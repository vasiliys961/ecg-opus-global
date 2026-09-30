"""Amplitude grid for record 00513. P_Morph is not ported."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from ecg_engine.feature_columns import FEATURE_COLUMNS
from experiments.raw_to_531.ecgdeli_preprocess import (
    baseline_removal,
    example_forward,
    high_low_filter,
    isoline_correction,
)
from experiments.raw_to_531.reconstruct_aggregation import aggregate_beats
from experiments.raw_to_531.reconstruct_from_fiducials import (
    FID,
    LEAD_FILES,
    PUBLISHED,
    beats_from_rows,
    parse_atr,
    split_name,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DAT = ROOT / "research/ecgdeli_reproduction/data/ptbxl/records500/00000/00513_hr.dat"
HEA = ROOT / "research/ecgdeli_reproduction/data/ptbxl/records500/00000/00513_hr.hea"
EXACT = 1e-6
HEADER_LEADS = ("I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6")
PEAKS = {
    "P_Amp": "p-wave peak",
    "Q_Amp": "Q peak",
    "R_Amp": "R peak",
    "S_Amp": "S peak",
    "T_Amp": "t-wave peak",
}
FILE_LEAD = {
    "00513_points_lead_I.atr": "I",
    "00513_points_lead_II.atr": "II",
    "00513_points_lead_III.atr": "III",
    "00513_points_lead_aVR.atr": "aVR",
    "00513_points_lead_aVL.atr": "aVL",
    "00513_points_lead_aVF.atr": "aVF",
    "00513_points_lead_V1.atr": "V1",
    "00513_points_lead_V2.atr": "V2",
    "00513_points_lead_V3.atr": "V3",
    "00513_points_lead_V4.atr": "V4",
    "00513_points_lead_V5.atr": "V5",
    "00513_points_lead_V6.atr": "V6",
}


def load_mv() -> np.ndarray:
    raw = np.fromfile(DAT, dtype=np.int16)
    if raw.size != 5000 * 12:
        raise SystemExit(f"unexpected sample count {raw.size}")
    return raw.reshape(5000, 12).astype(float) / 1000.0


def load_adc() -> np.ndarray:
    raw = np.fromfile(DAT, dtype=np.int16)
    return raw.reshape(5000, 12).astype(float)


def sample_at(signal: np.ndarray, channel: int, stored: float, base: str) -> float:
    """MATLAB clamps the 1-based index into 1..N. `base` says what the atr integer is."""
    if not math.isfinite(stored):
        return math.nan
    matlab_index = int(stored) + 1 if base == "wfdb0" else int(stored)
    length = signal.shape[0]
    if matlab_index <= 0:
        matlab_index = 1
    if matlab_index > length:
        matlab_index = length
    return float(signal[matlab_index - 1, channel])


def pipelines(mv: np.ndarray, adc: np.ndarray) -> dict[str, np.ndarray]:
    return {
        "P0_mV": mv,
        "P0_ADC": adc,
        "P2_isoline": isoline_correction(mv),
        "P2_baseline_example_1s_0.5": baseline_removal(mv, 1.0, 0.5),
        "P2_baseline_morph_0.3_0.3": baseline_removal(mv, 0.3, 0.3),
        "P3_highlow_1_40": high_low_filter(mv, 1.0, 40.0),
        "P3_qrs_0.5_30": high_low_filter(mv, 0.5, 30.0),
        "P3_t_0.3_20": high_low_filter(mv, 0.3, 20.0),
        "P1_example_forward": example_forward(mv),
        "P4_baseline_then_example_forward": example_forward(baseline_removal(mv, 1.0, 0.5)),
    }


def points() -> dict[str, list[dict[str, float]]]:
    return {lead: beats_from_rows(parse_atr(FID / name)) for lead, name in LEAD_FILES.items()}


def channel_for(csv_lead: str, pairing: str) -> int:
    if pairing == "csv_name":
        anatomical = csv_lead
    elif pairing == "file_name":
        anatomical = FILE_LEAD[LEAD_FILES[csv_lead]]
    else:
        raise KeyError(pairing)
    return HEADER_LEADS.index(anatomical)


def evaluate(signal: np.ndarray, published: pd.Series, beats: dict, pairing: str, base: str, pipeline: str):
    rows = []
    errors = []
    exact = 0
    for feature in FEATURE_COLUMNS:
        family, lead, stat = split_name(feature)
        if family not in PEAKS:
            continue
        channel = channel_for(lead, pairing)
        series = np.array(
            [sample_at(signal, channel, beat[PEAKS[family]], base) for beat in beats[lead]],
            dtype=float,
        )
        reduced = aggregate_beats(series)
        reconstructed = {"value": reduced.value, "iqr": reduced.iqr, "count": reduced.count}[stat]
        published_value = float(published[feature])
        if stat == "count":
            error = abs(published_value - float(reconstructed))
            is_exact = error == 0
        else:
            error = abs(published_value - float(reconstructed))
            is_exact = error <= EXACT
        if is_exact:
            exact += 1
        errors.append(error)
        rows.append(
            {
                "preprocessing_id": f"{pipeline}__{pairing}__{base}",
                "feature": feature,
                "published": published_value,
                "reconstructed": reconstructed,
                "abs_error": error,
                "exact_1e6": is_exact,
            }
        )
    summary = {
        "pipeline": f"{pipeline}__{pairing}__{base}",
        "exact": exact,
        "mae": float(np.mean(errors)),
        "median_absolute_error": float(np.median(errors)),
        "max_absolute_error": float(np.max(errors)),
        "columns": len(errors),
    }
    return rows, summary


def pmorph_rows(published: pd.Series) -> list[dict[str, object]]:
    rows = []
    for feature in FEATURE_COLUMNS:
        family, _lead, _stat = split_name(feature)
        if family != "P_Morph":
            continue
        rows.append(
            {
                "preprocessing_id": "NOT_EXECUTED",
                "feature": feature,
                "published": float(published[feature]),
                "reconstructed": "",
                "abs_error": "",
                "exact_1e6": False,
            }
        )
    return rows


def main() -> None:
    published_frame = pd.read_csv(PUBLISHED)
    published = published_frame.loc[published_frame["ecg_id"] == 513].iloc[0]
    mv = load_mv()
    adc = load_adc()
    beats = points()
    prepared = pipelines(mv, adc)
    all_rows = []
    summaries = []
    for name, signal in prepared.items():
        for pairing in ("csv_name", "file_name"):
            for base in ("wfdb0", "matlab1"):
                rows, summary = evaluate(signal, published, beats, pairing, base, name)
                all_rows.extend(rows)
                summaries.append(summary)
                print(summary)
    with (HERE / "amplitude_preprocessing_grid_00513.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["preprocessing_id", "feature", "published", "reconstructed", "abs_error", "exact_1e6"],
        )
        writer.writeheader()
        writer.writerows(all_rows)
    morph = pmorph_rows(published)
    with (HERE / "pmorph_preprocessing_grid_00513.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["preprocessing_id", "feature", "published", "reconstructed", "abs_error", "exact_1e6"],
        )
        writer.writeheader()
        writer.writerows(morph)
    best = max(summaries, key=lambda item: (item["exact"], -item["mae"]))
    payload = {
        "record": "00513",
        "sampling_frequency_hz": 500,
        "n_samples": 5000,
        "header": HEA.read_text(encoding="utf-8"),
        "matlab": "absent",
        "octave": "absent",
        "pmorph": "NOT_EXECUTED",
        "summaries": summaries,
        "best_numerical_candidate": best,
        "network_called": False,
    }
    (HERE / "amplitude_grid_summary_00513.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
