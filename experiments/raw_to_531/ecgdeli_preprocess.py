"""Python transcription of the ECGDeli 1.1 filters used by the example.

This is an experiment for record 00513. It is not a copy of the MATLAB
sources and it is not a bit-exact MATLAB run: Butterworth sections go
through SciPy, and the histogram mode follows equal-width bin centers.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.signal import butter, filtfilt, sos2tf

FS = 500


def isoline_correction(signal: np.ndarray) -> np.ndarray:
    """Mode removal. Default bin count is min(1024, N), as in Isoline_Correction."""
    columns = np.asarray(signal, dtype=float)
    if columns.ndim == 1:
        columns = columns[:, None]
    out = np.empty_like(columns)
    n_bins = min(1024, columns.shape[0])
    for index in range(columns.shape[1]):
        column = columns[:, index]
        if np.allclose(column, column[0]):
            offset = float(column[0])
        else:
            counts, edges = np.histogram(column, bins=n_bins)
            centers = edges[:-1] + np.diff(edges) / 2.0
            offset = float(centers[int(np.argmax(counts))])
        out[:, index] = column - offset
    return out


def _pad_edge(column: np.ndarray, left: int, right: int) -> np.ndarray:
    return np.pad(column, (left, right), mode="edge")


def _butter_filtfilt(column: np.ndarray, cutoff: float, kind: str) -> np.ndarray:
    sos = butter(3, 2.0 * cutoff / FS, btype=kind, output="sos")
    filtered = column
    for section in sos:
        b, a = sos2tf(section[None, :])
        filtered = filtfilt(b, a, filtered)
    return filtered


def high_low_filter(signal: np.ndarray, high_hz: float, low_hz: float) -> np.ndarray:
    """Default Butterworth path of ECG_High_Low_Filter at 500 Hz.

    Each stage pads ten seconds on both sides by repeating the edge sample,
    filters, crops, then removes the histogram mode.
    """
    columns = np.asarray(signal, dtype=float)
    pad = round(FS * 10)
    out = np.empty_like(columns)
    for index in range(columns.shape[1]):
        extended = _pad_edge(columns[:, index], pad, pad)
        if high_hz < FS / 2:
            extended = _butter_filtfilt(extended, high_hz, "high")
        cropped = extended[pad:-pad]
        cropped = isoline_correction(cropped)[:, 0]
        extended = _pad_edge(cropped, pad, pad)
        if low_hz < FS / 2:
            extended = _butter_filtfilt(extended, low_hz, "low")
        cropped = extended[pad:-pad]
        out[:, index] = isoline_correction(cropped)[:, 0]
    return out


def notch_filter(signal: np.ndarray, f0: float = 50.0, width: float = 1.0) -> np.ndarray:
    """Frequency-domain notch from Notch_Filter. f0 and width are the example values."""
    columns = np.asarray(signal, dtype=float)
    harmonics = math.floor(FS / 2 / f0)
    extension = round(0.5 * math.ceil(FS / width))
    extended = np.pad(columns, ((extension, extension), (0, 0)), mode="edge")
    length = extended.shape[0]
    frequencies = np.arange(length) / length * FS
    sigma = math.ceil(length * width / FS)
    kernel_length = 2 * round(4 * sigma) + 1
    half = (kernel_length - 1) / 2
    axis = np.arange(kernel_length) - (kernel_length - 1) / 2.0
    kernel = np.exp(-(axis**2) / (2.0 * sigma**2))
    kernel = kernel / kernel.sum()
    span = kernel.max() - kernel.min()
    kernel = (kernel.max() - kernel) / span
    response = np.ones(length)
    for harmonic in range(1, harmonics + 1):
        center = int(np.argmin(np.abs(frequencies - harmonic * f0)))
        half_i = int(half)
        start = center - half_i
        stop = center + half_i + 1
        mirror = (length - center) % length
        mirror_start = mirror - half_i
        mirror_stop = mirror + half_i + 1
        if min(start, mirror_start) < 0 or max(stop, mirror_stop) > length:
            raise ValueError(f"notch kernel does not fit: harmonic {harmonic}")
        response[start:stop] = kernel
        response[mirror_start:mirror_stop] = kernel
    spectrum = np.fft.fft(extended, axis=0) * response[:, None]
    restored = np.fft.ifft(spectrum, axis=0).real
    return restored[extension:-extension]


def baseline_removal(signal: np.ndarray, window_seconds: float, overlap: float) -> np.ndarray:
    """Median-window baseline from ECG_Baseline_Removal, then its own isoline step."""
    columns = np.asarray(signal, dtype=float)
    length, channels = columns.shape
    window = round(window_seconds * FS)
    window = window + 1 - (window % 2)
    half = (window - 1) // 2
    if overlap == 1:
        centers = np.arange(1, length + 1)
    else:
        count = math.floor((length - window * overlap) / (window * (1 - overlap)))
        centers = np.round(window * (1 - overlap) * np.arange(count)) + half + 1
        centers = centers.astype(int)
    out = np.empty_like(columns)
    grid = np.arange(1, length + 1)
    for index in range(channels):
        points = []
        for center in centers:
            left = max(int(center) - half, 1)
            right = min(int(center) + half, length)
            points.append(float(np.median(columns[left - 1 : right, index])))
        baseline = PchipInterpolator(centers.astype(float), np.array(points), extrapolate=True)(grid)
        corrected = isoline_correction(columns[:, index] - baseline)
        out[:, index] = corrected[:, 0]
    return out


def example_forward(signal: np.ndarray) -> np.ndarray:
    """Example forward path at this record's 500 Hz: 1–40 Hz, notch 50/1, isoline.

    The example also computes a baseline and does not pass it forward.
    """
    filtered = high_low_filter(signal, 1.0, 40.0)
    filtered = notch_filter(filtered, 50.0, 1.0)
    return isoline_correction(filtered)
