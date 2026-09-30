"""Снимок из DICOM для открытой зоны. Кривую в картинку не рисует."""

from __future__ import annotations

import io

import numpy as np
from PIL import Image

class DicomOpenError(ValueError):
    """Файл не стал снимком для разбора картинки."""


def open_dicom_image(payload: bytes) -> bytes:
    if len(payload) < 132 or payload[128:132] != b"DICM":
        raise DicomOpenError("Это не DICOM.")
    try:
        import pydicom
    except ImportError as exc:
        raise DicomOpenError("Чтение DICOM на этой сборке не установлено.") from exc
    try:
        dataset = pydicom.dcmread(io.BytesIO(payload), force=False)
    except Exception as exc:
        raise DicomOpenError("DICOM не открылся.") from exc
    if getattr(dataset, "PixelData", None) is None:
        if getattr(dataset, "WaveformSequence", None):
            raise DicomOpenError("В DICOM кривая, не снимок. В открытую зону она пока не рисуется.")
        raise DicomOpenError("В DICOM нет снимка.")
    try:
        frame = _first_frame(np.asarray(dataset.pixel_array))
    except Exception as exc:
        raise DicomOpenError("Снимок DICOM не прочитался.") from exc
    if str(getattr(dataset, "PhotometricInterpretation", "")).upper() == "MONOCHROME1":
        frame = np.max(frame) - frame
    return _png(_to_uint8(frame))


def _first_frame(array: np.ndarray) -> np.ndarray:
    if array.ndim == 2:
        return array
    if array.ndim == 3 and array.shape[-1] in (3, 4):
        return array
    if array.ndim >= 3:
        return array[0]
    raise DicomOpenError("Снимок DICOM этой формы страница не показывает.")


def _to_uint8(frame: np.ndarray) -> np.ndarray:
    if frame.dtype == np.uint8:
        return frame
    values = frame.astype(np.float32)
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return np.zeros(frame.shape, dtype=np.uint8)
    low = float(finite.min())
    high = float(finite.max())
    if high <= low:
        return np.zeros(frame.shape, dtype=np.uint8)
    scaled = (values - low) * (255.0 / (high - low))
    return np.clip(scaled, 0, 255).astype(np.uint8)


def _png(frame: np.ndarray) -> bytes:
    if frame.ndim == 2:
        image = Image.fromarray(frame, mode="L")
    elif frame.ndim == 3 and frame.shape[-1] == 3:
        image = Image.fromarray(frame, mode="RGB")
    elif frame.ndim == 3 and frame.shape[-1] == 4:
        image = Image.fromarray(frame, mode="RGBA")
    else:
        raise DicomOpenError("Снимок DICOM этой формы страница не показывает.")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
