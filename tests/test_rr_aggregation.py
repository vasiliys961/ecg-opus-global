"""Published RR for record 513 is one value per gap between R peaks."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from experiments.raw_to_531.reconstruct_aggregation import aggregate_beats
from experiments.raw_to_531.reconstruct_from_fiducials import (
    FID,
    LEAD_FILES,
    PUBLISHED,
    beats_from_rows,
    framingham,
    parse_atr,
    second_order_ms,
    successive_rr_ms,
)


def _published_row() -> pd.Series:
    frame = pd.read_csv(PUBLISHED)
    row = frame.loc[frame["ecg_id"] == 513]
    assert len(row) == 1
    return row.iloc[0]


def _global_r_peaks() -> np.ndarray:
    beats = beats_from_rows(parse_atr(FID / "00513_points_global.atr"))
    return np.array([beat["R peak"] for beat in beats], dtype=float)


def _qtc_on_successive_gaps() -> np.ndarray:
    parsed = {lead: beats_from_rows(parse_atr(FID / name)) for lead, name in LEAD_FILES.items()}
    n_beats = len(next(iter(parsed.values())))
    qt = []
    for beat_index in range(n_beats):
        later = np.array([parsed[lead][beat_index]["t-wave offset"] for lead in LEAD_FILES])
        earlier = np.array([parsed[lead][beat_index]["QRS onset"] for lead in LEAD_FILES])
        qt.append(second_order_ms(later, earlier))
    rr = successive_rr_ms(_global_r_peaks())
    return np.array(
        [framingham(float(qt_value), float(rr_value)) for qt_value, rr_value in zip(qt, rr)],
        dtype=float,
    )


def test_successive_rr_count_is_one_less_than_r_peaks() -> None:
    peaks = _global_r_peaks()
    rr = successive_rr_ms(peaks)
    assert rr.size == peaks.size - 1
    assert np.allclose(rr, 2.0 * np.diff(peaks))


def test_record_513_rr_matches_published_row() -> None:
    published = _published_row()
    reduced = aggregate_beats(successive_rr_ms(_global_r_peaks()))
    assert reduced.count == int(published["RR_Mean_Global_count"])
    assert reduced.value == float(published["RR_Mean_Global"])
    assert reduced.iqr == float(published["RR_Mean_Global_iqr"])
    assert reduced.count == 11
    assert reduced.value == 862.0
    assert reduced.iqr == 37.0


def test_record_513_framingham_matches_published_within_rounding() -> None:
    published = _published_row()
    reduced = aggregate_beats(_qtc_on_successive_gaps())
    assert reduced.count == int(published["QT_IntFramingham_Global_count"])
    assert reduced.count == 11
    assert math.isclose(reduced.value, float(published["QT_IntFramingham_Global"]), abs_tol=0.01)
    assert math.isclose(reduced.iqr, float(published["QT_IntFramingham_Global_iqr"]), abs_tol=0.01)
    assert math.isclose(
        abs(reduced.value - float(published["QT_IntFramingham_Global"])), 0.002, abs_tol=1e-6
    )
    assert math.isclose(
        abs(reduced.iqr - float(published["QT_IntFramingham_Global_iqr"])), 0.003, abs_tol=1e-6
    )
    # The residual is above the experiment's exact threshold of 1e-6.
    assert abs(reduced.value - float(published["QT_IntFramingham_Global"])) > 1e-6
