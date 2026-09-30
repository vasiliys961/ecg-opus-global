"""Один файл сам выбирает поток.

Кривая становится таблицей 12 отведений и уходит в ECGFounder и NeuroKit.
Лист уходит в разбор снимка. Имя пациента из заголовка файла в ответ не входит.
"""

from __future__ import annotations

import csv
import io
import struct
import zipfile
from dataclasses import dataclass

import numpy as np

from ecg_engine.ecgfounder import LEADS

_LIMB = ("III", "aVR", "aVL", "aVF")
_SCP_LEADS = {
    1: "I",
    2: "II",
    3: "V1",
    4: "V2",
    5: "V3",
    6: "V4",
    7: "V5",
    8: "V6",
    61: "III",
    62: "aVR",
    63: "aVL",
    64: "aVF",
}
_ALIASES = {
    "I": "I",
    "ECG I": "I",
    "LEADI": "I",
    "MLI": "I",
    "MDC_ECG_LEAD_I": "I",
    "II": "II",
    "ECG II": "II",
    "LEADII": "II",
    "MLII": "II",
    "MDC_ECG_LEAD_II": "II",
    "III": "III",
    "ECG III": "III",
    "LEADIII": "III",
    "MLIII": "III",
    "MDC_ECG_LEAD_III": "III",
    "AVR": "aVR",
    "ECGAVR": "aVR",
    "MDC_ECG_LEAD_AVR": "aVR",
    "AVL": "aVL",
    "ECGAVL": "aVL",
    "MDC_ECG_LEAD_AVL": "aVL",
    "AVF": "aVF",
    "ECGAVF": "aVF",
    "MDC_ECG_LEAD_AVF": "aVF",
    "V1": "V1",
    "ECGV1": "V1",
    "MDC_ECG_LEAD_V1": "V1",
    "V2": "V2",
    "ECGV2": "V2",
    "MDC_ECG_LEAD_V2": "V2",
    "V3": "V3",
    "ECGV3": "V3",
    "MDC_ECG_LEAD_V3": "V3",
    "V4": "V4",
    "ECGV4": "V4",
    "MDC_ECG_LEAD_V4": "V4",
    "V5": "V5",
    "ECGV5": "V5",
    "MDC_ECG_LEAD_V5": "V5",
    "V6": "V6",
    "ECGV6": "V6",
    "MDC_ECG_LEAD_V6": "V6",
}


class IntakeError(ValueError):
    """Файл распознан или отклонён до расчёта."""


@dataclass(frozen=True)
class Waveform:
    lead_names: list[str]
    columns: list[list[float]]
    sampling_rate: float
    format_name: str
    stream: str = "signal"


@dataclass(frozen=True)
class Sheet:
    payload: bytes
    filename: str
    mime: str
    format_name: str
    text: str = ""
    stream: str = "document"


def open_upload(payload: bytes, filename: str, sampling_rate_hint: float | None = None) -> Waveform | Sheet:
    name = (filename or "").lower().rsplit("/", 1)[-1]
    if not payload:
        raise IntakeError("Пустой файл.")
    if name.endswith(".zqecg"):
        raise IntakeError("ZQECG распознан, это поток кривой. Открытой раскладки нет, файл не распакован.")
    if name.endswith(".pdf") or payload.startswith(b"%PDF"):
        if not payload.startswith(b"%PDF"):
            raise IntakeError("Файл не похож на PDF.")
        return Sheet(payload, filename or "sheet.pdf", "application/pdf", "PDF")
    image = _image_mime(payload)
    if image and not name.endswith((".edf", ".scp", ".mat", ".hea", ".dat", ".xml", ".csv")):
        return Sheet(payload, filename or "ecg", image, "снимок")
    if len(payload) > 132 and payload[128:132] == b"DICM":
        return _from_dicom(payload)
    if payload.startswith(b"PK\x03\x04"):
        return _from_zip(payload, sampling_rate_hint)
    if payload.startswith(b"MATLAB"):
        return _from_mat(payload, sampling_rate_hint)
    if name.endswith(".edf") or payload[:8] == b"0       ":
        return _from_edf(payload)
    if name.endswith(".xml") or _looks_xml(payload):
        return _from_xml(payload)
    if name.endswith(".hea"):
        raise IntakeError("WFDB — это пара .hea и .dat. Положите обе в один zip.")
    if name.endswith(".dat"):
        raise IntakeError("Рядом с .dat нужен заголовок .hea. Положите оба файла в один zip.")
    if name.endswith(".scp"):
        return _from_scp(payload)
    if name.endswith(".mat"):
        return _from_mat(payload, sampling_rate_hint)
    if name.endswith(".csv") or _looks_csv(payload):
        return _from_csv(payload, sampling_rate_hint)
    raise IntakeError("Формат не распознан. Нужны CSV, EDF, WFDB в zip, MAT, XML, SCP-ECG, PDF, снимок или DICOM.")


def _lead_key(raw: str) -> str:
    return "".join(ch for ch in raw.upper() if ch.isalnum())


_LEAD_KEYS = {_lead_key(key): value for key, value in _ALIASES.items()}


def canonical_lead(raw: str) -> str | None:
    return _LEAD_KEYS.get(_lead_key(raw))


def complete_twelve(named: dict[str, np.ndarray]) -> tuple[list[str], list[list[float]]]:
    cleaned: dict[str, np.ndarray] = {}
    width: int | None = None
    for raw_name, values in named.items():
        lead = raw_name if raw_name in LEADS else canonical_lead(raw_name)
        if lead is None:
            raise IntakeError(f"Неизвестное отведение {raw_name}.")
        if lead in cleaned:
            raise IntakeError(f"Отведение {lead} повторяется.")
        column = np.asarray(values, dtype=np.float64).reshape(-1)
        if not np.isfinite(column).all():
            raise IntakeError("В отсчётах есть NaN или Inf.")
        if width is None:
            width = int(column.size)
            if width == 0:
                raise IntakeError("В записи нет отсчётов.")
        elif int(column.size) != width:
            raise IntakeError("В каждом отведении должно быть одно и то же число отсчётов.")
        cleaned[lead] = column
    if width is None:
        raise IntakeError("В записи нет отведений.")
    if "I" in cleaned and "II" in cleaned:
        first = cleaned["I"]
        second = cleaned["II"]
        derived = {
            "III": second - first,
            "aVR": -(first + second) / 2.0,
            "aVL": first - second / 2.0,
            "aVF": second - first / 2.0,
        }
        for lead in _LIMB:
            if lead not in cleaned:
                cleaned[lead] = derived[lead]
    missing = [lead for lead in LEADS if lead not in cleaned]
    if missing:
        raise IntakeError(f"Не хватает отведений: {', '.join(missing)}.")
    columns = [cleaned[lead].tolist() for lead in LEADS]
    return list(LEADS), columns


def _waveform(columns: list[list[float]], sampling_rate: float, format_name: str) -> Waveform:
    if not np.isfinite(sampling_rate) or sampling_rate <= 0:
        raise IntakeError("В файле нет частоты дискретизации.")
    return Waveform(list(LEADS), columns, float(sampling_rate), format_name)


def _image_mime(payload: bytes) -> str | None:
    if payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if payload.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if payload.startswith(b"GIF87a") or payload.startswith(b"GIF89a"):
        return "image/gif"
    if payload.startswith(b"RIFF") and payload[8:12] == b"WEBP":
        return "image/webp"
    return None


def _looks_xml(payload: bytes) -> bool:
    start = payload.lstrip(b"\xef\xbb\xbf \t\r\n")
    return start.startswith(b"<")


def _looks_csv(payload: bytes) -> bool:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        return False
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 2:
        return False
    known = [name for name in rows[0] if canonical_lead(name)]
    return len(known) >= 2


def _hint(sampling_rate_hint: float | None) -> float:
    if sampling_rate_hint is None or not np.isfinite(sampling_rate_hint) or sampling_rate_hint <= 0:
        raise IntakeError("В файле нет частоты. Укажите её рядом с файлом.")
    return float(sampling_rate_hint)


def _from_csv(payload: bytes, sampling_rate_hint: float | None) -> Waveform:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise IntakeError("CSV не в кодировке UTF-8.") from exc
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 2:
        raise IntakeError("В CSV нет строки отсчётов.")
    names = [cell.strip() for cell in rows[0]]
    buckets: dict[str, list[float]] = {name: [] for name in names}
    try:
        for row in rows[1:]:
            if not any(cell.strip() for cell in row):
                continue
            if len(row) != len(names):
                raise IntakeError("В строке CSV другое число колонок, чем в заголовке.")
            for index, cell in enumerate(row):
                buckets[names[index]].append(float(cell))
    except ValueError as exc:
        raise IntakeError("В CSV есть нечисловой отсчёт.") from exc
    lead_names, columns = complete_twelve(buckets)
    return _waveform(columns, _hint(sampling_rate_hint), "CSV")


def _edf_text(payload: bytes, start: int, length: int) -> str:
    return payload[start : start + length].decode("latin1", errors="replace").strip()


def _edf_number(payload: bytes, start: int, length: int) -> float:
    raw = _edf_text(payload, start, length)
    if not raw:
        raise IntakeError("В заголовке EDF пустое число.")
    return float(raw)


def _from_edf(payload: bytes) -> Waveform:
    if len(payload) < 256 or payload[:8] != b"0       ":
        raise IntakeError("Файл не похож на EDF.")
    header_bytes = int(_edf_number(payload, 184, 8))
    records = int(_edf_number(payload, 236, 8))
    record_seconds = _edf_number(payload, 244, 8)
    signals = int(_edf_number(payload, 252, 4))
    if signals <= 0 or records <= 0 or record_seconds <= 0 or header_bytes < 256:
        raise IntakeError("Заголовок EDF не содержит запись.")
    cursor = 256

    def take(width: int) -> list[str]:
        nonlocal cursor
        cells = [_edf_text(payload, cursor + index * width, width) for index in range(signals)]
        cursor += signals * width
        return cells

    labels = take(16)
    take(80)
    take(8)
    physical_min = [float(value) for value in take(8)]
    physical_max = [float(value) for value in take(8)]
    digital_min = [float(value) for value in take(8)]
    digital_max = [float(value) for value in take(8)]
    take(80)
    per_record = [int(float(value)) for value in take(8)]
    if cursor > header_bytes or len(payload) < header_bytes:
        raise IntakeError("Заголовок EDF оборван.")
    named: dict[str, np.ndarray] = {}
    rates: list[float] = []
    offset = header_bytes
    record_width = sum(per_record)
    expected = header_bytes + records * record_width * 2
    if len(payload) < expected:
        raise IntakeError("В EDF меньше отсчётов, чем обещает заголовок.")
    collected: dict[str, list[np.ndarray]] = {label: [] for label in labels}
    for _ in range(records):
        for index, label in enumerate(labels):
            count = per_record[index]
            chunk = payload[offset : offset + count * 2]
            offset += count * 2
            if "annotation" in label.lower():
                continue
            digital = np.frombuffer(chunk, dtype="<i2").astype(np.float64)
            span = digital_max[index] - digital_min[index]
            if span == 0:
                raise IntakeError(f"У канала {label} нулевой цифровой диапазон.")
            physical = (digital - digital_min[index]) / span * (physical_max[index] - physical_min[index]) + physical_min[index]
            collected[label].append(physical)
    for label, parts in collected.items():
        if not parts:
            continue
        column = np.concatenate(parts)
        lead = canonical_lead(label)
        if lead is None:
            continue
        named[lead] = column
        rates.append(per_record[labels.index(label)] / record_seconds)
    if not named:
        raise IntakeError("В EDF нет отведений ЭКГ.")
    rate = rates[0]
    if any(abs(item - rate) > 1e-6 for item in rates):
        raise IntakeError("У отведений EDF разная частота.")
    lead_names, columns = complete_twelve(named)
    return _waveform(columns, rate, "EDF")


def _gain_baseline(token: str) -> tuple[float, float]:
    gain_text, _, _units = token.partition("/")
    baseline = 0.0
    if "(" in gain_text and gain_text.endswith(")"):
        gain_text, baseline_text = gain_text[:-1].split("(", 1)
        baseline = float(baseline_text or "0")
    gain = float(gain_text)
    if gain == 0:
        raise IntakeError("В WFDB нулевое усиление.")
    return gain, baseline


def read_wfdb(header: str, dat: bytes) -> Waveform:
    lines = [line.strip() for line in header.splitlines() if line.strip() and not line.startswith("#")]
    if len(lines) < 2:
        raise IntakeError("В заголовке WFDB нет отведений.")
    first = lines[0].split()
    if len(first) < 3:
        raise IntakeError("Первая строка WFDB не содержит частоту.")
    try:
        count = int(first[1])
        sampling_rate = float(first[2])
    except ValueError as exc:
        raise IntakeError("Заголовок WFDB не разобран.") from exc
    specs = []
    for line in lines[1 : 1 + count]:
        parts = line.split()
        if len(parts) < 3:
            raise IntakeError("Строка отведения WFDB короче трёх полей.")
        fmt = int(parts[1])
        if fmt != 16:
            raise IntakeError(f"WFDB формата {fmt} не читается. Нужен формат 16.")
        gain, baseline = _gain_baseline(parts[2])
        lead = parts[-1]
        specs.append((parts[0], gain, baseline, lead))
    if len(specs) != count:
        raise IntakeError("В WFDB меньше строк отведений, чем заявлено.")
    if any(spec[0] != specs[0][0] for spec in specs):
        raise IntakeError("Отведения WFDB в разных файлах .dat пока не собираются.")
    frame = count * 2
    if len(dat) < frame or len(dat) % frame:
        raise IntakeError("Длина .dat не совпадает с числом отведений.")
    digital = np.frombuffer(dat, dtype="<i2").astype(np.float64).reshape(-1, count)
    named = {}
    for index, (_filename, gain, baseline, lead) in enumerate(specs):
        named[lead] = (digital[:, index] - baseline) / gain
    lead_names, columns = complete_twelve(named)
    return _waveform(columns, sampling_rate, "WFDB")


def _from_zip(payload: bytes, sampling_rate_hint: float | None) -> Waveform | Sheet:
    if len(payload) > 40_000_000:
        raise IntakeError("Архив больше 40 МБ.")
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload))
    except zipfile.BadZipFile as exc:
        raise IntakeError("Архив не открылся.") from exc
    names = [item for item in archive.namelist() if item and not item.endswith("/")]
    if len(names) > 12:
        raise IntakeError("В архиве слишком много файлов.")
    lowered = {item.lower(): item for item in names}
    headers = [item for item in names if item.lower().endswith(".hea")]
    data_files = [item for item in names if item.lower().endswith(".dat")]
    if headers and data_files:
        header_name = headers[0]
        header = archive.read(header_name).decode("latin1")
        body = [line.strip() for line in header.splitlines() if line.strip() and not line.startswith("#")]
        wanted = body[1].split()[0] if len(body) > 1 else ""
        match = next((item for item in data_files if item.split("/")[-1].lower() == wanted.lower()), data_files[0])
        return read_wfdb(header, archive.read(match))
    if len(names) == 1:
        inner = archive.read(names[0])
        if inner.startswith(b"PK"):
            raise IntakeError("Вложенный архив не распаковывается.")
        return open_upload(inner, names[0].rsplit("/", 1)[-1], sampling_rate_hint)
    raise IntakeError("В архиве нет пары WFDB и нет одного файла записи.")


def _from_mat(payload: bytes, sampling_rate_hint: float | None) -> Waveform:
    from scipy.io import loadmat

    try:
        raw = loadmat(io.BytesIO(payload), squeeze_me=True, struct_as_record=False)
    except Exception as exc:
        raise IntakeError("MAT не открылся. Нужен файл MATLAB 5, не v7.3.") from exc
    sampling_rate = None
    arrays: list[np.ndarray] = []
    for key, value in raw.items():
        if key.startswith("__"):
            continue
        if isinstance(value, (int, float, np.number)) and key.lower() in {"fs", "freq", "frequency", "samplingrate", "samplerate"}:
            sampling_rate = float(value)
            continue
        array = np.asarray(value)
        if array.ndim == 2 and array.dtype.kind in "iuf" and 12 in array.shape:
            arrays.append(array.astype(np.float64))
    if len(arrays) != 1:
        raise IntakeError("В MAT нет одной матрицы из 12 отведений.")
    matrix = arrays[0]
    if matrix.shape[0] != 12:
        matrix = matrix.T
    if matrix.shape[0] != 12:
        raise IntakeError("В MAT нет 12 отведений.")
    named = {LEADS[index]: matrix[index] for index in range(12)}
    lead_names, columns = complete_twelve(named)
    rate = sampling_rate if sampling_rate and sampling_rate > 0 else _hint(sampling_rate_hint)
    return _waveform(columns, rate, "MAT")


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _lzw_bytes(payload: bytes, bits: int = 10) -> list[int]:
    max_code = (1 << bits) - 2
    strings = {code: bytes([code]) for code in range(256)}
    next_code = 256
    previous = b""
    offset = 0
    bit_count = 0
    bit_buffer = 0
    output: list[int] = []

    def read_code() -> int:
        nonlocal offset, bit_count, bit_buffer
        while bit_count <= 24:
            if offset < len(payload):
                bit_buffer = (bit_buffer | ((payload[offset] & 0xFF) << (24 - bit_count))) & 0xFFFFFFFF
                offset += 1
                bit_count += 8
            elif bit_count < bits:
                return -1
            else:
                break
        code = (bit_buffer >> (32 - bits)) & 0xFFFF
        bit_buffer = (bit_buffer << bits) & 0xFFFFFFFF
        bit_count -= bits
        return code

    while True:
        code = read_code()
        if code < 0 or code > max_code:
            break
        if code not in strings:
            data = previous + previous[:1]
            strings[code] = data
        else:
            data = strings[code]
        if previous and next_code <= max_code:
            strings[next_code] = previous + data[:1]
            next_code += 1
        previous = data
        output.extend(data)
    return output


def _xli_deltas(buffer: list[int], first: int) -> np.ndarray:
    half = len(buffer) // 2
    deltas = np.empty(half, dtype=np.int32)
    for index in range(half):
        value = ((buffer[index] << 8) | buffer[half + index]) & 0xFFFF
        if value >= 0x8000:
            value -= 0x10000
        deltas[index] = value
    if half < 2:
        return deltas
    previous = int(deltas[0])
    current = int(deltas[1])
    last = int(first)
    for index in range(2, half):
        restored = current + current - previous - last
        last = int(deltas[index]) - 64
        deltas[index] = restored
        previous = current
        current = restored
    return deltas


def _xli_leads(payload: bytes, count: int) -> list[np.ndarray]:
    offset = 0
    leads: list[np.ndarray] = []
    while offset + 8 <= len(payload) and len(leads) < count:
        size = int.from_bytes(payload[offset : offset + 4], "little", signed=True)
        origin = int.from_bytes(payload[offset + 6 : offset + 8], "little", signed=True)
        offset += 8
        if size < 0 or offset + size > len(payload):
            raise IntakeError("Сжатие Philips XLI оборвано.")
        raw = _lzw_bytes(payload[offset : offset + size], 10)
        offset += size
        if len(raw) % 2:
            raw.append(0)
        leads.append(_xli_deltas(raw, origin))
    if len(leads) < count:
        raise IntakeError("В Philips XML меньше отведений, чем заявлено.")
    return leads


def _philips_waveform(root: object) -> Waveform | None:
    import base64

    for element in root.iter():
        if _local(element.tag).lower() != "parsedwaveforms":
            continue
        compression = (element.attrib.get("compression") or "").lower()
        if compression != "xli":
            raise IntakeError("Кривая Philips сжата не методом XLI. В таблицу она не собрана.")
        encoded = "".join((element.text or "").split())
        if not encoded:
            raise IntakeError("В Philips XML нет отсчётов.")
        try:
            payload = base64.b64decode(encoded, validate=False)
        except Exception as exc:
            raise IntakeError("Отсчёты Philips XML не читаются как base64.") from exc
        count = int(element.attrib.get("numberofleads") or "0")
        rate = float(element.attrib.get("samplespersecond") or "0")
        resolution = float(element.attrib.get("resolution") or "1")
        labels = (element.attrib.get("leadlabels") or "").split()
        if count <= 0 or rate <= 0 or len(labels) < count:
            raise IntakeError("В Philips XML нет частоты или списка отведений.")
        columns = _xli_leads(payload, count)
        named = {
            labels[index]: columns[index].astype(np.float64) * resolution / 1000.0
            for index in range(count)
        }
        _lead_names, table = complete_twelve(named)
        return _waveform(table, rate, "XML")
    return None


def _from_xml(payload: bytes) -> Waveform | Sheet:
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise IntakeError("XML не разобран.") from exc
    increment = None
    declared = None
    for element in root.iter():
        name = _local(element.tag)
        if name.lower() in {"increment"} and element.attrib.get("value"):
            unit = (element.attrib.get("unit") or "s").lower()
            value = float(element.attrib["value"])
            increment = value / 1000.0 if unit == "ms" else value
        if element.attrib.get("samplingRate") or element.attrib.get("sampleRate") or element.attrib.get("frequency"):
            declared = float(element.attrib.get("samplingRate") or element.attrib.get("sampleRate") or element.attrib.get("frequency"))
    sequences: list[tuple[str, np.ndarray]] = []
    for element in root.iter():
        if _local(element.tag).lower() not in {"sequence", "lead", "channel"}:
            continue
        lead = element.attrib.get("name") or element.attrib.get("code") or element.attrib.get("lead")
        digits = None
        scale = 1.0
        unit = "uv"
        for child in element.iter():
            child_name = _local(child.tag).lower()
            if child_name == "code" and child.attrib.get("code"):
                lead = child.attrib["code"]
            if child_name in {"digits", "samples"} and child.text and child.text.strip():
                digits = child.text
            if child_name == "scale" and child.attrib.get("value"):
                scale = float(child.attrib["value"])
                unit = (child.attrib.get("unit") or unit).lower()
        if lead is None and element.text and element.text.strip():
            lead = element.attrib.get("name")
        text = digits if digits is not None else (element.text.strip() if element.text and element.text.strip() else None)
        if lead and text:
            values = np.asarray([float(piece) for piece in text.replace(",", " ").split()], dtype=np.float64)
            if unit in {"uv", "µv", "μv"}:
                values = values * scale / 1000.0
            elif unit == "mv":
                values = values * scale
            sequences.append((lead, values))
    if sequences:
        named: dict[str, np.ndarray] = {}
        for lead, values in sequences:
            current = named.get(lead)
            if current is None or values.size > current.size:
                named[lead] = values
        lead_names, columns = complete_twelve(named)
        if declared and declared > 0:
            rate = declared
        elif increment and increment > 0:
            rate = 1.0 / increment
        else:
            raise IntakeError("В XML есть отсчёты, но нет частоты.")
        return _waveform(columns, rate, "XML")
    philips = _philips_waveform(root)
    if philips is not None:
        return philips
    text = " ".join(piece.strip() for piece in root.itertext() if piece and piece.strip())
    if len(text) < 20:
        raise IntakeError("В XML нет ни отсчётов, ни текста заключения.")
    return Sheet(payload, "note.txt", "text/plain", "XML", text=text[:8000])


def _section_header(payload: bytes, offset: int) -> tuple[dict[str, int], int]:
    if offset + 16 > len(payload):
        raise IntakeError("Секция SCP-ECG оборвана.")
    crc, section_id, length, version, protocol = struct.unpack_from("<HHIBB", payload, offset)
    if length < 16 or offset + length > len(payload):
        raise IntakeError("Длина секции SCP-ECG не сходится с файлом.")
    return {"crc": crc, "id": section_id, "length": length, "version": version, "protocol": protocol}, offset + 16


def _from_scp(payload: bytes) -> Waveform:
    if len(payload) < 32:
        raise IntakeError("SCP-ECG слишком короткий.")
    _crc, size = struct.unpack_from("<HI", payload, 0)
    if size and size != len(payload):
        return _from_healforce(payload)
    header, cursor = _section_header(payload, 6)
    if header["id"] != 0:
        raise IntakeError("SCP-ECG распознан, но секция указателей не на месте.")
    end = 6 + header["length"]
    pointers: dict[int, tuple[int, int]] = {}
    while cursor + 10 <= end:
        section_id, length, index = struct.unpack_from("<HII", payload, cursor)
        pointers[section_id] = (length, index)
        cursor += 10
    huffman = False
    if 2 in pointers and pointers[2][0] > 0:
        if pointers[2][0] <= 16:
            raise IntakeError("SCP-ECG сжат таблицей Хаффмана. Такой ритм не распаковывается.")
        table_id = struct.unpack_from("<H", payload, pointers[2][1] - 1 + 16)[0]
        if table_id != 19999:
            raise IntakeError("В SCP-ECG своя таблица Хаффмана. Такой ритм не распаковывается.")
        huffman = True
    if 3 not in pointers or pointers[3][0] <= 0 or 6 not in pointers or pointers[6][0] <= 0:
        raise IntakeError("В SCP-ECG нет секции отведений или ритма.")
    leads, counts = _scp_leads(payload, pointers[3][1] - 1)
    samples, sampling_rate = _scp_rhythm(payload, pointers[6][1] - 1, len(leads), huffman, counts)
    named = {lead: column for lead, column in zip(leads, samples, strict=True)}
    lead_names, columns = complete_twelve(named)
    return _waveform(columns, sampling_rate, "SCP-ECG")


_SCP_HUFFMAN = {
    (1, 0b0): 0,
    (3, 0b100): 1,
    (3, 0b101): -1,
    (4, 0b1100): 2,
    (4, 0b1101): -2,
    (5, 0b11100): 3,
    (5, 0b11101): -3,
    (6, 0b111100): 4,
    (6, 0b111101): -4,
    (7, 0b1111100): 5,
    (7, 0b1111101): -5,
    (8, 0b11111100): 6,
    (8, 0b11111101): -6,
    (9, 0b111111100): 7,
    (9, 0b111111101): -7,
    (10, 0b1111111100): 8,
    (10, 0b1111111101): -8,
    (10, 0b1111111110): 511,
    (10, 0b1111111111): 1023,
}


def _scp_huffman(data: bytes) -> list[int]:
    prefix = 0
    size = 0
    pending = 0
    bits = ""
    values: list[int] = []
    for byte in data:
        for mask in (128, 64, 32, 16, 8, 4, 2, 1):
            bit = 1 if byte & mask else 0
            if pending:
                bits += "1" if bit else "0"
                pending -= 1
                if pending == 0:
                    number = int(bits, 2)
                    if len(bits) == 8 and number >= 128:
                        number -= 256
                    elif len(bits) == 16 and number >= 32768:
                        number -= 65536
                    values.append(number)
                    bits = ""
                    prefix = 0
                    size = 0
                continue
            prefix = (prefix << 1) | bit
            size += 1
            symbol = _SCP_HUFFMAN.get((size, prefix))
            if symbol is None:
                continue
            if symbol == 511:
                pending = 8
            elif symbol == 1023:
                pending = 16
            else:
                values.append(symbol)
                prefix = 0
                size = 0
    return values


def _scp_second(codes: list[int]) -> list[int]:
    previous = None
    first_difference = None
    restored: list[int] = []
    for code in codes:
        if previous is None:
            previous = code
            restored.append(code)
            continue
        if first_difference is None:
            first_difference = code - previous
            previous = code
            restored.append(code)
            continue
        first_difference += code
        previous += first_difference
        restored.append(previous)
    return restored


def _scp_first(codes: list[int]) -> list[int]:
    if not codes:
        return []
    restored = [codes[0]]
    for code in codes[1:]:
        restored.append(restored[-1] + code)
    return restored


def _from_healforce(payload: bytes) -> Waveform:
    header, cursor = _section_header(payload, 6)
    if header["id"] != 0:
        raise IntakeError("Длина SCP-ECG в заголовке не равна файлу.")
    end = 6 + header["length"]
    pointers: dict[int, tuple[int, int]] = {}
    while cursor + 10 <= end:
        section_id, length, index = struct.unpack_from("<HII", payload, cursor)
        pointers[section_id] = (length, index)
        cursor += 10
    if 3 not in pointers or 6 not in pointers:
        raise IntakeError("Длина SCP-ECG в заголовке не равна файлу.")
    lead_header, lead_cursor = _section_header(payload, pointers[3][1])
    if lead_header["id"] != 3:
        raise IntakeError("Секция отведений Healforce не на месте.")
    lead_count = payload[lead_cursor]
    rhythm_header, rhythm_cursor = _section_header(payload, pointers[6][1])
    if rhythm_header["id"] != 6:
        raise IntakeError("Секция ритма Healforce не на месте.")
    _avm, interval, _encoding, _bimodal = struct.unpack_from("<HHBB", payload, rhythm_cursor)
    rhythm_cursor += 6
    if interval <= 0 or lead_count <= 0:
        raise IntakeError("В файле Healforce нет шага времени или отведений.")
    stream_count = 1
    widths = list(struct.unpack_from("<" + "H" * stream_count, payload, rhythm_cursor))
    rhythm_cursor += 2 * stream_count
    packed = payload[rhythm_cursor : rhythm_cursor + widths[0]]
    words = np.frombuffer(packed[: len(packed) - (len(packed) % 6)], dtype="<i2").reshape(-1, 3)
    fourth = ((words[:, 0] & 0x3C00) >> 2) + ((words[:, 1] & 0x3C00) >> 6) + ((words[:, 2] & 0x3C00) >> 10)
    samples = np.concatenate([words, fourth.reshape(-1, 1)], axis=1).reshape(-1)
    sign = (((samples & 0x0300) >> 8) + 0xFE) & 0xFF
    samples = (sign.astype(np.int16) << 8) + (samples & 0xFF).astype(np.int16)
    usable = samples.size - (samples.size % lead_count)
    matrix = samples[:usable].reshape(-1, lead_count).T.astype(np.float64) / 100.0
    rate = 1_000_000.0 / interval
    duration = matrix.shape[1] / rate
    if lead_count < 8 or not (8 <= duration <= 12):
        raise IntakeError(
            f"Healforce открыт: {lead_count} отведений, {duration:.2f} с при {rate:.0f} Гц. "
            "Для расчёта нужно около 10 с и 12 отведений."
        )
    names = ["I", "II", "V1", "V2", "V3", "V4", "V5", "V6"][:lead_count]
    named = {names[index]: matrix[index] for index in range(lead_count)}
    _lead_names, columns = complete_twelve(named)
    return _waveform(columns, rate, "SCP-ECG")


def _scp_leads(payload: bytes, offset: int) -> tuple[list[str], list[int]]:
    header, cursor = _section_header(payload, offset)
    if header["id"] != 3:
        raise IntakeError("Секция отведений SCP-ECG не на указанном месте.")
    count = payload[cursor]
    flags = payload[cursor + 1]
    if flags & 0x02:
        raise IntakeError("В SCP-ECG ритм хранится как остаток после вычитания опорного комплекса.")
    cursor += 2
    leads = []
    counts = []
    for _ in range(count):
        start, end, lead_id = struct.unpack_from("<IIB", payload, cursor)
        cursor += 9
        name = _SCP_LEADS.get(lead_id)
        if name is None:
            raise IntakeError(f"Код отведения SCP-ECG {lead_id} не из двенадцати стандартных.")
        leads.append(name)
        counts.append(end - start + 1 if end >= start else 0)
    return leads, counts


def _scp_rhythm(
    payload: bytes,
    offset: int,
    lead_count: int,
    huffman: bool = False,
    sample_counts: list[int] | None = None,
) -> tuple[list[np.ndarray], float]:
    header, cursor = _section_header(payload, offset)
    if header["id"] != 6:
        raise IntakeError("Секция ритма SCP-ECG не на указанном месте.")
    avm, interval, encoding, bimodal = struct.unpack_from("<HHBB", payload, cursor)
    cursor += 6
    if bimodal != 0:
        raise IntakeError("SCP-ECG со сдвоенным сжатием не распаковывается.")
    if not huffman and encoding != 0:
        raise IntakeError("SCP-ECG хранит разности отсчётов. Такой ритм не распаковывается.")
    if huffman and encoding not in (0, 1, 2):
        raise IntakeError("SCP-ECG хранит разности отсчётов. Такой ритм не распаковывается.")
    if avm <= 0 or interval <= 0:
        raise IntakeError("В SCP-ECG нет шага амплитуды или шага времени.")
    widths = list(struct.unpack_from("<" + "H" * lead_count, payload, cursor))
    cursor += 2 * lead_count
    columns = []
    for index, width in enumerate(widths):
        blob = payload[cursor : cursor + width]
        cursor += width
        if huffman:
            codes = _scp_huffman(blob)
            if encoding == 2:
                decoded = _scp_second(codes)
            elif encoding == 1:
                decoded = _scp_first(codes)
            else:
                decoded = codes
            needed = sample_counts[index] if sample_counts and sample_counts[index] > 0 else len(decoded)
            if len(decoded) < needed:
                raise IntakeError("После Хаффмана в отведении меньше отсчётов, чем в заголовке.")
            column = np.asarray(decoded[:needed], dtype=np.float64)
        else:
            if width % 2:
                raise IntakeError("Длина отведения SCP-ECG нечётная.")
            count = width // 2
            column = np.asarray(struct.unpack_from("<" + "h" * count, blob), dtype=np.float64)
        columns.append(column * (avm / 1_000_000.0))
    return columns, 1_000_000.0 / interval


def _from_dicom(payload: bytes) -> Waveform | Sheet:
    from backend.dicom_image import DicomOpenError, open_dicom_image

    try:
        png = open_dicom_image(payload)
    except DicomOpenError as exc:
        if "кривая" not in str(exc):
            raise IntakeError(str(exc)) from exc
        return _dicom_waveform(payload)
    return Sheet(png, "dicom.png", "image/png", "DICOM")


def _dicom_waveform(payload: bytes) -> Waveform:
    import pydicom

    dataset = pydicom.dcmread(io.BytesIO(payload), force=False)
    sequence = getattr(dataset, "WaveformSequence", None)
    if not sequence:
        raise IntakeError("В DICOM нет кривой.")
    item = sequence[0]
    sampling_rate = float(item.SamplingFrequency)
    channels = int(item.NumberOfWaveformChannels)
    samples = int(item.NumberOfWaveformSamples)
    if int(item.WaveformBitsAllocated) != 16:
        raise IntakeError("DICOM-кривая не в 16-битном отсчёте.")
    values = np.frombuffer(bytes(item.WaveformData), dtype="<i2").astype(np.float64)
    if values.size != channels * samples:
        raise IntakeError("Длина кривой DICOM не сходится с заголовком.")
    matrix = values.reshape(samples, channels).T
    definitions = list(item.ChannelDefinitionSequence)
    named = {}
    for index, channel in enumerate(definitions):
        label = str(getattr(channel, "ChannelLabel", "") or "")
        if not label and getattr(channel, "ChannelSource", None) is not None:
            label = str(getattr(channel.ChannelSource, "CodeMeaning", "") or "")
        sensitivity = float(getattr(channel, "ChannelSensitivity", 1.0) or 1.0)
        correction = float(getattr(channel, "ChannelSensitivityCorrectionFactor", 1.0) or 1.0)
        baseline = float(getattr(channel, "ChannelBaseline", 0.0) or 0.0)
        named[label or LEADS[index]] = (matrix[index] - baseline) * sensitivity * correction
    lead_names, columns = complete_twelve(named)
    return _waveform(columns, sampling_rate, "DICOM")
