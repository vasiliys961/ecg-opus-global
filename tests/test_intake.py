"""Маршрут файла: кривая в таблицу, лист в разбор."""

from __future__ import annotations

import io
import struct
import zipfile

import numpy as np
import pytest
from fastapi.testclient import TestClient
from scipy.io import savemat

from backend.app import app
from ecg_engine.intake import IntakeError, Sheet, Waveform, open_upload


def _edf(values: dict[str, list[float]], sampling_rate: float = 500.0) -> bytes:
    labels = list(values)
    count = len(values[labels[0]])
    header_bytes = 256 + len(labels) * 256

    def field(text: object, width: int) -> bytes:
        raw = str(text).encode("ascii")
        return raw[:width].ljust(width, b" ")

    duration = f"{count / sampling_rate:.3f}"
    head = b"".join(
        [
            field(0, 8),
            field("", 80),
            field("", 80),
            field("01.01.26", 8),
            field("00.00.00", 8),
            field(header_bytes, 8),
            field("", 44),
            field(1, 8),
            field(duration, 8),
            field(len(labels), 4),
        ]
    )
    assert len(head) == 256
    signal = b"".join(
        [
            b"".join(field(label, 16) for label in labels),
            b"".join(field("", 80) for _ in labels),
            b"".join(field("mV", 8) for _ in labels),
            b"".join(field(-100, 8) for _ in labels),
            b"".join(field(100, 8) for _ in labels),
            b"".join(field(-100, 8) for _ in labels),
            b"".join(field(100, 8) for _ in labels),
            b"".join(field("", 80) for _ in labels),
            b"".join(field(count, 8) for _ in labels),
            b"".join(field("", 32) for _ in labels),
        ]
    )
    data = bytearray()
    for label in labels:
        for sample in values[label]:
            data.extend(struct.pack("<h", int(sample)))
    return head + signal + bytes(data)


def _wfdb_zip() -> bytes:
    count = 4
    leads = ["I", "II", "V1", "V2", "V3", "V4", "V5", "V6"]
    header = f"rec {len(leads)} 500 {count}\n" + "".join(
        f"rec.dat 16 1000(0)/mV 16 0 0 0 {lead}\n" for lead in leads
    )
    data = bytearray()
    for time in range(count):
        for index, _lead in enumerate(leads):
            data.extend(struct.pack("<h", (time + 1) * 10 + index))
    blob = io.BytesIO()
    with zipfile.ZipFile(blob, "w") as archive:
        archive.writestr("rec.hea", header)
        archive.writestr("rec.dat", bytes(data))
    return blob.getvalue()


def _scp(samples: list[list[int]], *, huffman: bool = False) -> bytes:
    lead_ids = [1, 2, 3, 4, 5, 6, 7, 8]
    lead_body = struct.pack("<BB", len(lead_ids), 0)
    for lead_id in lead_ids:
        lead_body += struct.pack("<IIB", 1, len(samples[0]), lead_id)
    rhythm = struct.pack("<HHBB", 1000, 2000, 0, 0)
    for column in samples:
        rhythm += struct.pack("<H", len(column) * 2)
    for column in samples:
        rhythm += struct.pack("<" + "h" * len(column), *column)

    def section(section_id: int, body: bytes) -> bytes:
        length = 16 + len(body)
        return struct.pack("<HHIBB", 0, section_id, length, 20, 20) + b"\x00" * 6 + body

    section3 = section(3, lead_body)
    section6 = section(6, rhythm)
    pointers = b""
    # filled after we know offsets; placeholder built in two steps
    prefix = 6
    section0_length = 16 + 12 * 10
    section3_at = prefix + section0_length
    section6_at = section3_at + len(section3)
    locations = {0: (section0_length, prefix + 1), 3: (len(section3), section3_at + 1), 6: (len(section6), section6_at + 1)}
    if huffman:
        locations[2] = (16, section6_at + len(section6) + 1)
    for section_id in range(12):
        length, index = locations.get(section_id, (0, 0))
        pointers += struct.pack("<HII", section_id, length, index)
    section0 = section(0, pointers)
    body = section0 + section3 + section6
    return struct.pack("<HI", 0, 6 + len(body)) + body


def test_csv_and_eight_leads_derive_the_limb_leads():
    text = "I,II,V1,V2,V3,V4,V5,V6\n1,3,0,0,0,0,0,0\n"
    opened = open_upload(text.encode(), "trace.csv", 500)
    assert isinstance(opened, Waveform)
    assert opened.stream == "signal"
    assert opened.format_name == "CSV"
    assert opened.columns[2] == [2.0]
    assert opened.columns[3] == [-2.0]
    assert opened.columns[4] == [-0.5]
    assert opened.columns[5] == [2.5]


def test_edf_wfdb_mat_and_xml_become_the_same_table():
    leads = ["I", "II", "V1", "V2", "V3", "V4", "V5", "V6"]
    values = {lead: [1.0, 3.0] for lead in leads}
    edf = open_upload(_edf(values), "night.edf")
    assert isinstance(edf, Waveform)
    assert edf.format_name == "EDF"
    assert edf.sampling_rate == pytest.approx(500)
    assert edf.columns[0] == pytest.approx([1, 3])
    assert edf.columns[2] == pytest.approx([0, 0])

    wfdb = open_upload(_wfdb_zip(), "rec.zip")
    assert isinstance(wfdb, Waveform)
    assert wfdb.format_name == "WFDB"
    assert wfdb.columns[0][0] == pytest.approx(0.01)

    matrix = np.arange(24, dtype=np.float64).reshape(12, 2)
    blob = io.BytesIO()
    savemat(blob, {"val": matrix, "fs": 250.0})
    mat = open_upload(blob.getvalue(), "beat.mat")
    assert isinstance(mat, Waveform)
    assert mat.sampling_rate == 250
    assert mat.columns[0] == [0.0, 1.0]

    digits = " ".join(str(item) for item in (1000, 3000))
    sequences = "".join(
        f'<sequence><code code="MDC_ECG_LEAD_{lead}"/><digits>{digits}</digits><scale value="1" unit="uV"/></sequence>'
        for lead in leads
    )
    short = " ".join(str(item) for item in (100, 100))
    rhythm = " ".join(str(item) for item in (1000, 3000, 5000))
    sequences = (
        f'<sequence><code code="MDC_ECG_LEAD_I"/><digits>{short}</digits><scale value="1" unit="uV"/></sequence>'
        + f'<sequence><code code="MDC_ECG_LEAD_I"/><digits>{rhythm}</digits><scale value="1" unit="uV"/></sequence>'
        + "".join(
            f'<sequence><code code="MDC_ECG_LEAD_{lead}"/><digits>{rhythm}</digits><scale value="1" unit="uV"/></sequence>'
            for lead in leads
            if lead != "I"
        )
    )
    xml = f'<ecg><increment value="0.002" unit="s"/>{sequences}</ecg>'.encode()
    opened = open_upload(xml, "device.xml")
    assert isinstance(opened, Waveform)
    assert opened.format_name == "XML"
    assert opened.sampling_rate == pytest.approx(500)
    assert opened.columns[0] == pytest.approx([1, 3, 5])


def test_xml_without_samples_is_a_document():
    opened = open_upload("<report><text>Синусовый ритм, ЧСС 70, QRS 90 мс.</text></report>".encode(), "note.xml")
    assert isinstance(opened, Sheet)
    assert opened.stream == "document"
    assert "Синусовый ритм" in opened.text


def test_scp_rhythm_is_read_and_compressed_scp_stops():
    column = [2000, 4000]
    opened = open_upload(_scp([column for _ in range(8)]), "rest.scp")
    assert isinstance(opened, Waveform)
    assert opened.format_name == "SCP-ECG"
    assert opened.sampling_rate == pytest.approx(500)
    assert opened.columns[0] == pytest.approx([2, 4])
    with pytest.raises(IntakeError, match="Хаффмана"):
        open_upload(_scp([column for _ in range(8)], huffman=True), "packed.scp")


def test_pdf_is_a_document_and_unknown_files_stop():
    pdf = open_upload(b"%PDF-1.4\n", "sheet.pdf")
    assert isinstance(pdf, Sheet)
    assert pdf.mime == "application/pdf"
    picture = open_upload(b"\x89PNG\r\n\x1a\nfake", "trace.png")
    assert picture.format_name == "снимок"
    with pytest.raises(IntakeError, match="ZQECG"):
        open_upload(b"\x00\x00", "holter.zqecg")
    with pytest.raises(IntakeError, match="не распознан"):
        open_upload(b"\x01\x02not-a-format", "mystery.bin")
    with pytest.raises(IntakeError, match="zip"):
        open_upload(b"record 12 500 10\n", "00513.hea")


def test_intake_route_sends_a_curve_to_the_signal_stream(monkeypatch):
    def report(signal, lead_names, sampling_rate):
        return {"scores": [{"label": "SINUS RHYTHM", "score": 0.9}], "measurements": {"available": True}, "trace": []}

    monkeypatch.setattr("backend.app._digital_report", report)
    text = "I,II,III,aVR,aVL,aVF,V1,V2,V3,V4,V5,V6\n" + "0,0,0,0,0,0,0,0,0,0,0,0\n"
    with TestClient(app) as client:
        response = client.post(
            "/api/ecg/intake",
            data={"sampling_rate": "500"},
            files={"file": ("trace.csv", text.encode(), "text/csv")},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["stream"] == "signal"
    assert body["format"] == "CSV"
    assert body["scores"][0]["label"] == "SINUS RHYTHM"


def test_intake_route_sends_a_pdf_to_the_document_stream(monkeypatch):
    def analyze_case(**kwargs):
        assert kwargs["mime_type"] == "application/pdf"
        return {"interpretation": "Запись\nлист", "extraction": None}

    monkeypatch.setattr("backend.app.analyze_case", analyze_case)
    with TestClient(app) as client:
        response = client.post("/api/ecg/intake", files={"file": ("sheet.pdf", b"%PDF-1.4\n", "application/pdf")})
    assert response.status_code == 200
    assert response.json()["stream"] == "document"
    assert response.json()["format"] == "PDF"
