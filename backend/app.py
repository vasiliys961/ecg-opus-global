"""HTTP-сервис ECG engine. Не импортирует production Doctor Opus."""

from __future__ import annotations

import csv
import io
import socket
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel

from backend.bridge import MAX_FILE_BYTES, BridgeError, bridge
from backend.dicom_image import DicomOpenError, open_dicom_image
from backend.vision import (
    EmptyCase,
    UnsupportedImage,
    VisionUnavailable,
    analyze_case,
    analyze_ecg_image,
    form_protocol,
    form_signal_conclusion,
)
from ecg_engine.delineation import measure_tracing
from ecg_engine.intake import IntakeError, Sheet, Waveform, open_upload
from ecg_engine.ecgfounder import SignalError, WeightsMissing, arrange, predict_signal
from ecg_engine.feature_compatibility import FeatureCompatibilityEngine, json_ready
from ecg_engine.preprocessing import PreprocessingError
from ecg_engine.raw_extractor import RawECGExtractor

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "index.html"
PHONE = ROOT / "frontend" / "phone.html"
EXAMPLE_CSV = ROOT / "examples2" / "00001_норма.csv"

app = FastAPI(title="Doctor Opus ECG Engine", version="0.2.0")


class ProtocolBody(BaseModel):
    interpretation: str
    extraction: dict | None = None
    locale: str = "en"


class SignalConclusionBody(BaseModel):
    measurements: dict
    scores: list
    locale: str = "en"


class ExampleBody(BaseModel):
    sampling_rate: float = 500


class SignalBody(BaseModel):
    signal: list
    sampling_rate: float
    lead_names: list[str]


class RawFeaturesBody(BaseModel):
    signal: list
    sampling_rate: float
    lead_names: list[str]


def _signal_error(exc: Exception) -> HTTPException:
    if isinstance(exc, SignalError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, WeightsMissing):
        return HTTPException(status_code=503, detail=str(exc))
    raise exc


def _trace_preview(arranged: object, buckets: int = 500) -> list[dict[str, object]]:
    import numpy as np

    from ecg_engine.ecgfounder import LEADS

    matrix = np.asarray(arranged, dtype=float)
    width = int(matrix.shape[1])
    edges = np.linspace(0, width, buckets + 1, dtype=int)
    rows: list[dict[str, object]] = []
    for index, name in enumerate(LEADS):
        lead = matrix[index]
        samples: list[float] = []
        for start, stop in zip(edges[:-1], edges[1:]):
            chunk = lead[int(start) : int(stop)]
            if chunk.size == 0:
                continue
            samples.append(round(float(chunk.min()), 4))
            samples.append(round(float(chunk.max()), 4))
        rows.append({"lead": name, "samples": samples})
    return rows


def _digital_report(signal: object, lead_names: list[str], sampling_rate: float) -> dict[str, object]:
    arranged = arrange(signal, lead_names)
    result = predict_signal(signal, lead_names, sampling_rate)
    result["measurements"] = measure_tracing(arranged, sampling_rate)
    result["trace"] = _trace_preview(arranged)
    return result


@app.post("/api/ecg/signal")
def score_signal(body: SignalBody):
    try:
        return _digital_report(body.signal, body.lead_names, body.sampling_rate)
    except (SignalError, WeightsMissing) as exc:
        raise _signal_error(exc) from exc


def _columns_from_csv(text: str) -> tuple[list[str], list[list[float]]]:
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 2:
        raise HTTPException(status_code=400, detail="В CSV нет строки отсчётов.")
    lead_names = [cell.strip() for cell in rows[0]]
    columns: list[list[float]] = [[] for _ in lead_names]
    try:
        for row in rows[1:]:
            if not any(cell.strip() for cell in row):
                continue
            if len(row) != len(lead_names):
                raise HTTPException(status_code=400, detail="В строке CSV другое число колонок, чем в заголовке.")
            for index, cell in enumerate(row):
                columns[index].append(float(cell))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="В CSV есть нечисловой отсчёт.") from exc
    return lead_names, columns


@app.post("/api/ecg/intake")
async def intake_file(
    file: UploadFile = File(...),
    sampling_rate: float = Form(500),
    notes: str = Form(""),
    clinical_context: str = Form(""),
    locale: str = Form("en"),
):
    payload = await file.read()
    try:
        opened = open_upload(payload, file.filename or "", sampling_rate)
    except IntakeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if isinstance(opened, Waveform):
        try:
            report = _digital_report(opened.columns, opened.lead_names, opened.sampling_rate)
        except (SignalError, WeightsMissing) as exc:
            raise _signal_error(exc) from exc
        report["stream"] = opened.stream
        report["format"] = opened.format_name
        return report
    if not isinstance(opened, Sheet):
        raise HTTPException(status_code=400, detail="Файл не попал ни в один поток.")
    try:
        if opened.text:
            result = analyze_case(notes=opened.text, clinical_context=clinical_context, locale=locale)
        else:
            result = analyze_case(
                image=opened.payload,
                filename=opened.filename,
                mime_type=opened.mime,
                notes=notes,
                clinical_context=clinical_context,
                locale=locale,
            )
    except EmptyCase as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except UnsupportedImage as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except VisionUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    result["stream"] = opened.stream
    result["format"] = opened.format_name
    return result


@app.post("/api/ecg/signal/csv")
async def score_signal_csv(
    file: UploadFile = File(...),
    sampling_rate: float = Form(...),
):
    text = (await file.read()).decode("utf-8-sig")
    lead_names, columns = _columns_from_csv(text)
    try:
        return _digital_report(columns, lead_names, sampling_rate)
    except (SignalError, WeightsMissing) as exc:
        raise _signal_error(exc) from exc


@app.post("/api/ecg/signal/example")
def score_example(body: ExampleBody):
    if not EXAMPLE_CSV.is_file():
        raise HTTPException(status_code=404, detail="Пример записи не найден.")
    lead_names, columns = _columns_from_csv(EXAMPLE_CSV.read_text(encoding="utf-8-sig"))
    try:
        report = _digital_report(columns, lead_names, body.sampling_rate)
    except (SignalError, WeightsMissing) as exc:
        raise _signal_error(exc) from exc
    report["example"] = "PTB-XL 00001, открытая 10-секундная запись. Это не подключённый аппарат."
    return report


@app.post("/api/ecg/signal/conclusion")
def signal_conclusion(body: SignalConclusionBody):
    try:
        return form_signal_conclusion(body.measurements, body.scores, body.locale)
    except EmptyCase as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except VisionUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/")
def index():
    return FileResponse(FRONTEND, headers={"Cache-Control": "no-store"})


@app.get("/phone")
def phone_page():
    return FileResponse(PHONE, headers={"Cache-Control": "no-store"})


@app.get("/i18n.js")
def i18n_script():
    return FileResponse(ROOT / "frontend" / "i18n.js", media_type="text/javascript", headers={"Cache-Control": "no-store"})


def _lan_host() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("192.0.2.1", 9))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def _phone_url(request: Request, token: str) -> str:
    hostname = request.url.hostname or "127.0.0.1"
    if hostname in {"127.0.0.1", "localhost", "::1"}:
        hostname = _lan_host()
    port = request.url.port
    scheme = request.url.scheme or "http"
    origin = f"{scheme}://{hostname}" if port in {None, 80, 443} else f"{scheme}://{hostname}:{port}"
    return f"{origin}/phone?token={quote(token)}"


def _qr_png(text: str) -> bytes:
    import qrcode

    image = qrcode.make(text, border=1)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _bridge_http(exc: BridgeError) -> HTTPException:
    missing = "не найдена" in str(exc)
    return HTTPException(status_code=404 if missing else 400, detail=str(exc))


@app.post("/api/bridge/session")
def bridge_session(request: Request):
    token = bridge.create()
    return {"token": token, "phone_url": _phone_url(request, token)}


@app.get("/api/bridge/qr.png")
def bridge_qr(request: Request, token: str):
    try:
        bridge.since(token, 0)
    except BridgeError as exc:
        raise _bridge_http(exc) from exc
    return Response(
        content=_qr_png(_phone_url(request, token)),
        media_type="image/png",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/bridge/events")
def bridge_events(token: str, since: int = 0):
    try:
        events = bridge.since(token, max(0, since))
    except BridgeError as exc:
        raise _bridge_http(exc) from exc
    return {"events": events}


@app.get("/api/bridge/file/{event_id}")
def bridge_file(event_id: int, token: str):
    try:
        payload, filename, mime = bridge.read_file(token, event_id)
    except BridgeError as exc:
        raise _bridge_http(exc) from exc
    return Response(
        content=payload,
        media_type=mime or "application/octet-stream",
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": f"inline; filename*=UTF-8''{quote(filename)}",
        },
    )


@app.post("/api/bridge/upload")
async def bridge_upload(
    token: str = Form(...),
    name: str = Form(""),
    year: str = Form(""),
    sex: str = Form(""),
    study_date: str = Form(""),
    file: UploadFile | None = File(None),
):
    try:
        patient_id = bridge.add_patient(token, name, year, sex, study_date)
        file_id = None
        if file is not None:
            payload = await _read_limited(file)
            if payload:
                file_id = bridge.add_file(token, file.filename or "ecg", file.content_type or "", payload)
        if patient_id is None and file_id is None:
            raise BridgeError("Заполните карточку или выберите файл.")
    except BridgeError as exc:
        raise _bridge_http(exc) from exc
    return {"ok": True}


async def _read_limited(file: UploadFile) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        block = await file.read(1024 * 1024)
        if not block:
            break
        total += len(block)
        if total > MAX_FILE_BYTES:
            raise BridgeError("Файл с телефона больше 20 МБ.")
        chunks.append(block)
    return b"".join(chunks)


@app.post("/api/ecg/dicom/image")
async def dicom_image(file: UploadFile = File(...)):
    payload = await file.read()
    try:
        png = open_dicom_image(payload)
    except DicomOpenError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    return Response(content=png, media_type="image/png")


async def _strip_frames(frames: list[UploadFile] | None) -> list[tuple[bytes, str, str]]:
    images: list[tuple[bytes, str, str]] = []
    for item in frames or []:
        payload = await item.read()
        if payload:
            images.append((payload, item.filename or "", item.content_type or ""))
    return images


@app.post("/api/ecg/analyze")
async def analyze(
    file: UploadFile | None = File(None),
    frames: list[UploadFile] | None = File(None),
    notes: str = Form(""),
    clinical_context: str = Form(""),
    locale: str = Form("en"),
):
    images = await _strip_frames(frames)
    payload = None
    if not images and file is not None:
        payload = await file.read() or None
    try:
        return analyze_case(
            image=payload,
            filename=file.filename if file is not None else "",
            mime_type=file.content_type if file is not None else "",
            images=images or None,
            notes=notes,
            clinical_context=clinical_context,
            locale=locale,
        )
    except EmptyCase as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except UnsupportedImage as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except VisionUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/ecg/protocol")
def protocol(body: ProtocolBody):
    try:
        return form_protocol(body.interpretation, body.extraction, body.locale)
    except EmptyCase as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except VisionUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/ecg/image")
async def analyze_image(
    file: UploadFile = File(...),
    clinical_context: str = Form(""),
):
    payload = await file.read()
    try:
        return analyze_ecg_image(payload, file.filename or "", file.content_type or "", clinical_context)
    except UnsupportedImage as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except VisionUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/ecg/raw")
def raw_ecg():
    return JSONResponse(status_code=501, content=RawECGExtractor().status())


@app.post("/api/ecg/raw/features")
def raw_features(body: RawFeaturesBody):
    try:
        payload = FeatureCompatibilityEngine().analyze(body.signal, body.sampling_rate, body.lead_names)
    except PreprocessingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    public = json_ready(payload)
    public.pop("analysis", None)
    public.pop("preprocessing", None)
    public["preprocessing_recorded"] = True
    if "prediction" in public:
        public["prediction"] = None
    return public
