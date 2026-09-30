"""Forensic candidates for the PTB-XL+ columns that ECGDeli 1.1 does not emit.

Record 00513 only. Published values are read and not edited.
This is not a raw-to-531 extractor and it does not call the network.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from ecg_engine.feature_columns import FEATURE_COLUMNS
from experiments.raw_to_531.reconstruct_aggregation import aggregate_beats
from experiments.raw_to_531.reconstruct_from_fiducials import (
    FID,
    LEAD_FILES,
    PUBLISHED,
    beats_from_rows,
    parse_atr,
    samples_to_ms,
    split_name,
    successive_rr_ms,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SIGNAL = (
    ROOT
    / "research/ecgdeli_reproduction/data/ptbxl/records500/00000/00513_hr.dat"
)
HEADER_LEADS = ("I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6")
EXACT = 1e-6

# CSV anatomical name -> WFDB channel. The header order is not the CSV order.
WFDB_INDEX = {name: index for index, name in enumerate(HEADER_LEADS)}


def framingham(qt_ms: np.ndarray, rr_ms: np.ndarray) -> np.ndarray:
    return 1000.0 * (qt_ms / 1000.0 + 0.154 * (1.0 - 0.001 * rr_ms))


def bazett(qt_ms: np.ndarray, rr_ms: np.ndarray) -> np.ndarray:
    return qt_ms / np.sqrt(rr_ms / 1000.0)


def fridericia(qt_ms: np.ndarray, rr_ms: np.ndarray) -> np.ndarray:
    return qt_ms / np.power(rr_ms / 1000.0, 1.0 / 3.0)


def hodges(qt_ms: np.ndarray, rr_ms: np.ndarray) -> np.ndarray:
    heart_rate = 60000.0 / rr_ms
    return qt_ms + 1.75 * (heart_rate - 60.0)


FORMULAS = {
    "framingham": framingham,
    "bazett": bazett,
    "fridericia": fridericia,
    "hodges": hodges,
}


def load_published() -> pd.Series:
    frame = pd.read_csv(PUBLISHED)
    row = frame.loc[frame["ecg_id"] == 513]
    if len(row) != 1:
        raise SystemExit(f"expected one published row, found {len(row)}")
    return row.iloc[0]


def lead_series() -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], np.ndarray]:
    """Lead QT and lead RR from the fiducial file that matched that CSV column."""
    qt: dict[str, np.ndarray] = {}
    rr: dict[str, np.ndarray] = {}
    for lead, filename in LEAD_FILES.items():
        beats = beats_from_rows(parse_atr(FID / filename))
        qt[lead] = np.array(
            [
                samples_to_ms(beat["t-wave offset"], beat["QRS onset"])
                for beat in beats
            ],
            dtype=float,
        )
        rr[lead] = successive_rr_ms(np.array([beat["R peak"] for beat in beats], dtype=float))
    global_beats = beats_from_rows(parse_atr(FID / "00513_points_global.atr"))
    global_rr = successive_rr_ms(
        np.array([beat["R peak"] for beat in global_beats], dtype=float)
    )
    return qt, rr, global_rr


def pad_last(values: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return values
    return np.concatenate([values, values[-1:]])


def pair(qt: np.ndarray, rr: np.ndarray, alignment: str) -> tuple[np.ndarray, np.ndarray]:
    if alignment == "same_index":
        n = min(qt.size, rr.size)
        return qt[:n], rr[:n]
    if alignment == "qt_next":
        n = min(qt.size - 1, rr.size)
        return qt[1 : 1 + n], rr[:n]
    raise KeyError(alignment)


def write_rows(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def qt_candidates(published: pd.Series) -> list[dict[str, object]]:
    qt, lead_rr, global_rr = lead_series()
    rows: list[dict[str, object]] = []
    rr_sources = {
        "global_rr_n_minus_1": global_rr,
        "global_rr_padded": pad_last(global_rr),
    }
    for lead in LEAD_FILES:
        rr_sources_lead = {
            **rr_sources,
            "lead_rr_n_minus_1": lead_rr[lead],
            "lead_rr_padded": pad_last(lead_rr[lead]),
        }
        for formula_name, formula in FORMULAS.items():
            for rr_name, rr in rr_sources_lead.items():
                for alignment in ("same_index", "qt_next"):
                    qt_used, rr_used = pair(qt[lead], rr, alignment)
                    corrected = formula(qt_used, rr_used)
                    reduced = aggregate_beats(corrected)
                    name = f"{formula_name}_per_beat_then_aggregate__{rr_name}__{alignment}"
                    rows.extend(stat_rows(published, f"QT_IntCorr_{lead}", name, reduced))
                value = float(formula(float(np.median(qt[lead])), float(np.median(rr))))
                after_name = f"{formula_name}_median_then_correct__{rr_name}"
                rows.extend(
                    stat_rows(
                        published,
                        f"QT_IntCorr_{lead}",
                        after_name,
                        SimpleNamespace(value=value, iqr=None, count=1),
                        count_override=int(np.isfinite(qt[lead]).sum()),
                    )
                )
    return rows


def stat_rows(published, stem, formula, reduced, count_override=None):
    count = reduced.count if count_override is None else count_override
    specs = (
        ("", reduced.value),
        ("_iqr", reduced.iqr),
        ("_count", float(count)),
    )
    rows = []
    for suffix, reconstructed in specs:
        feature = f"{stem}{suffix}"
        published_value = float(published[feature])
        if reconstructed is None or (isinstance(reconstructed, float) and math.isnan(reconstructed)):
            error = ""
            exact = False
            reconstructed_out = ""
        else:
            error = abs(published_value - float(reconstructed))
            exact = error <= EXACT if suffix != "_count" else error == 0
            reconstructed_out = float(reconstructed)
        rows.append(
            {
                "feature": feature,
                "candidate_formula": formula,
                "reconstructed_value": reconstructed_out,
                "published_value": published_value,
                "absolute_error": error,
                "exact_match": exact,
            }
        )
    return rows


def signal_mv() -> np.ndarray:
    raw = np.fromfile(SIGNAL, dtype=np.int16)
    if raw.size != 5000 * 12:
        raise SystemExit(f"unexpected 500 Hz length {raw.size}")
    return raw.reshape(5000, 12).astype(float) / 1000.0


def sample(mv: np.ndarray, channel: int, index: float, base: str) -> float:
    if not math.isfinite(index):
        return math.nan
    position = int(index) if base == "zero" else int(index) - 1
    if position < 0 or position >= mv.shape[0]:
        return math.nan
    return float(mv[position, channel])


def st_candidates(published: pd.Series) -> list[dict[str, object]]:
    mv = signal_mv()
    rows: list[dict[str, object]] = []
    definitions = (
        "raw500_L_minus_QRS_onset",
        "raw500_L_minus_P_offset",
        "raw500_L_minus_median_Poffset_to_QRSonset",
    )
    for lead, filename in LEAD_FILES.items():
        beats = beats_from_rows(parse_atr(FID / filename))
        channel = WFDB_INDEX[lead]
        for base in ("zero", "one"):
            for definition in definitions:
                values = []
                for beat in beats:
                    l_point = sample(mv, channel, beat["L point (for STEMI)"], base)
                    if definition.endswith("QRS_onset"):
                        reference = sample(mv, channel, beat["QRS onset"], base)
                    elif definition.endswith("P_offset"):
                        reference = sample(mv, channel, beat["p-wave offset"], base)
                    else:
                        start = int(beat["p-wave offset"]) if base == "zero" else int(beat["p-wave offset"]) - 1
                        stop = int(beat["QRS onset"]) if base == "zero" else int(beat["QRS onset"]) - 1
                        if stop <= start or start < 0 or stop > mv.shape[0]:
                            reference = math.nan
                        else:
                            reference = float(np.median(mv[start:stop, channel]))
                    values.append(l_point - reference)
                reduced = aggregate_beats(np.array(values, dtype=float))
                rows.extend(
                    stat_rows(
                        published,
                        f"ST_Elev_{lead}",
                        f"{definition}__index_{base}__v2_points_on_same_name_channel",
                        reduced,
                    )
                )
    for feature in FEATURE_COLUMNS:
        family, _lead, _stat = split_name(feature)
        if family != "ST_Elev":
            continue
        rows.append(
            {
                "feature": feature,
                "candidate_formula": "ecgfeat_two_gaussian_T_peakness_not_applied",
                "reconstructed_value": "",
                "published_value": float(published[feature]),
                "absolute_error": "",
                "exact_match": False,
            }
        )
    return rows


def ha_candidates(published: pd.Series, metadata_axis: str) -> list[dict[str, object]]:
    mv = signal_mv()
    rows = []
    for base in ("zero", "one"):
        nets = {}
        for lead in ("I", "II", "III", "aVR", "aVL", "aVF"):
            beats = beats_from_rows(parse_atr(FID / LEAD_FILES[lead]))
            channel = WFDB_INDEX[lead]
            beat_net = []
            for beat in beats:
                r_value = sample(mv, channel, beat["R peak"], base)
                s_value = sample(mv, channel, beat["S peak"], base)
                beat_net.append(r_value + s_value)
            nets[lead] = float(np.median(np.array(beat_net, dtype=float)))
        angle = math.degrees(math.atan2(nets["aVF"], nets["I"]))
        rows.append(
            {
                "feature": "HA__Global",
                "candidate_formula": f"atan2_median_RplusS_aVF_I__raw500_index_{base}",
                "reconstructed_value": angle,
                "published_value": float(published["HA__Global"]),
                "absolute_error": abs(angle - float(published["HA__Global"])),
                "exact_match": False,
            }
        )
    rows.append(
        {
            "feature": "HA__Global",
            "candidate_formula": "ptbxl_metadata_heart_axis_string",
            "reconstructed_value": metadata_axis,
            "published_value": float(published["HA__Global"]),
            "absolute_error": "",
            "exact_match": False,
        }
    )
    for suffix in ("", "_iqr", "_count"):
        feature = f"HA__Global{suffix}"
        rows.append(
            {
                "feature": feature,
                "candidate_formula": "single_label_not_12_beat_aggregate",
                "reconstructed_value": "",
                "published_value": float(published[feature]),
                "absolute_error": "",
                "exact_match": False,
            }
        )
    return rows


def write_status(published: pd.Series) -> None:
    comparison = {
        row["feature"]: row["status"]
        for row in csv.DictReader((HERE / "comparison_fiducials_00513_v2.csv").open(encoding="utf-8"))
    }
    amplitude = {"P_Amp", "Q_Amp", "R_Amp", "S_Amp", "T_Amp"}
    rows = []
    for feature in FEATURE_COLUMNS:
        family, _lead, _stat = split_name(feature)
        compared = comparison[feature]
        if family in amplitude or family == "P_Morph":
            status = "REQUIRES_PROCESSED_SIGNAL"
            identified = "yes"
            numerical = "not tested; the published fiducial archive has no signal matrix"
            source = (
                "ExtractAmplitudeFeaturesFromFPT"
                if family in amplitude
                else "Get_P_Morphology"
            )
        elif family == "QT_IntCorr":
            winner = "framingham_per_beat_then_aggregate__lead_rr_padded__same_index"
            match = next(
                row
                for row in csv.DictReader((HERE / "qt_correction_candidates_00513.csv").open(encoding="utf-8"))
                if row["feature"] == feature and row["candidate_formula"] == winner
            )
            status = "EXACT" if match["exact_match"] == "True" else "CALCULABLE_BUT_DIFFERENT"
            identified = "yes, numerically, not as a separate source function"
            numerical = (
                f"Framingham per beat, lead QT, padded lead RR; "
                f"abs error {match['absolute_error']}"
            )
            source = "lead-wise columns of ExtractIntervalFeaturesFromFPT plus the sync Framingham expression"
        elif family == "ST_Elev":
            status = "ALGORITHM_UNKNOWN"
            identified = "no"
            numerical = "raw 500 Hz L-point differences do not match; no Gaussian implementation found"
            source = "not in ECGDeli 1.1; dictionary text STc_X"
        elif family == "HA":
            status = "ALGORITHM_UNKNOWN"
            identified = "no"
            numerical = "PTB-XL heart_axis for ecg_id 513 is empty; raw I/aVF angle is not the integer 2"
            source = "not in ECGDeli 1.1; dictionary text elHA"
        elif compared == "EXACT":
            status = "EXACT"
            identified = "yes"
            numerical = "exact at 1e-6 on record 00513"
            source = "published fiducials and ExtractIntervalFeaturesFromFPT"
        elif compared == "DIFFERENT":
            status = "CALCULABLE_BUT_DIFFERENT"
            identified = "yes"
            numerical = "same Framingham expression; residual about 0.002 ms, above 1e-6"
            source = "sync QT and unpadded global RR"
        else:
            status = "ALGORITHM_UNKNOWN"
            identified = "no"
            numerical = compared
            source = "unclassified"
        rows.append(
            {
                "feature": feature,
                "family": family,
                "source": source,
                "algorithm_identified": identified,
                "numerical_reconstruction": numerical,
                "status": status,
            }
        )
    write_rows(
        HERE / "step10_feature_status.csv",
        rows,
        [
            "feature",
            "family",
            "source",
            "algorithm_identified",
            "numerical_reconstruction",
            "status",
        ],
    )
    from collections import Counter
    print(Counter(row["status"] for row in rows))


def main() -> None:
    published = load_published()
    qt_rows = qt_candidates(published)
    write_rows(
        HERE / "qt_correction_candidates_00513.csv",
        qt_rows,
        [
            "feature",
            "candidate_formula",
            "reconstructed_value",
            "published_value",
            "absolute_error",
            "exact_match",
        ],
    )
    st_rows = st_candidates(published)
    write_rows(
        HERE / "st_elevation_candidates_00513.csv",
        st_rows,
        [
            "feature",
            "candidate_formula",
            "reconstructed_value",
            "published_value",
            "absolute_error",
            "exact_match",
        ],
    )
    metadata = ""
    database = Path("/tmp/ptbxl_database.csv")
    if database.exists() and database.stat().st_size > 1000:
        frame = pd.read_csv(database)
        hit = frame.loc[frame["ecg_id"] == 513]
        if len(hit) == 1 and "heart_axis" in frame.columns:
            cell = hit.iloc[0]["heart_axis"]
            metadata = "EMPTY" if pd.isna(cell) or str(cell).strip() == "" else str(cell)
    ha_rows = ha_candidates(published, metadata)
    write_rows(
        HERE / "heart_axis_candidates_00513.csv",
        ha_rows,
        [
            "feature",
            "candidate_formula",
            "reconstructed_value",
            "published_value",
            "absolute_error",
            "exact_match",
        ],
    )
    qt_exact = [row for row in qt_rows if row["exact_match"] is True]
    st_exact = [row for row in st_rows if row["exact_match"] is True]
    print("qt rows", len(qt_rows), "exact", len(qt_exact))
    print("st rows", len(st_rows), "exact", len(st_exact))
    print("metadata", metadata or "ABSENT")
    write_status(published)
    if qt_exact:
        print("QT EXACT SAMPLE", qt_exact[:12])


if __name__ == "__main__":
    main()
