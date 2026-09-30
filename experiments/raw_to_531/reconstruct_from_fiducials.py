"""Reconstruct PTB-XL+ interval columns from published fiducial points.

The beat formulas are the ones in ECGDeli 1.1 ExtractIntervalFeaturesFromFPT.
Sample differences are multiplied by 2, as that function does. The published
annotation itself says "time resolution: 500".

Amplitudes, P morphology, ST elevation and the heart-axis class are not
derived here. Their definitions are not fixed by these fiducials.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ecg_engine.feature_columns import FEATURE_COLUMNS
try:
    from reconstruct_aggregation import aggregate_beats
except ImportError:
    from experiments.raw_to_531.reconstruct_aggregation import aggregate_beats

HERE = Path(__file__).resolve().parent
FID = HERE / "fiducials" / "00513"
PUBLISHED = (
    ROOT
    / "research/ecgdeli_reproduction/data/ptbxl_plus/ecgdeli_features_prefix.csv"
)

# CSV column -> annotation file.
# Ten names match. For record 00513 the series in the file named aVF equals
# the published aVL columns, and the file named aVL equals the published aVF
# columns. The published table is not edited. See
# docs/LEAD_ORDER_FORENSIC_00513.md.
LEAD_FILES = {
    "I": "00513_points_lead_I.atr",
    "II": "00513_points_lead_II.atr",
    "III": "00513_points_lead_III.atr",
    "aVR": "00513_points_lead_aVR.atr",
    "aVL": "00513_points_lead_aVF.atr",
    "aVF": "00513_points_lead_aVL.atr",
    "V1": "00513_points_lead_V1.atr",
    "V2": "00513_points_lead_V2.atr",
    "V3": "00513_points_lead_V3.atr",
    "V4": "00513_points_lead_V4.atr",
    "V5": "00513_points_lead_V5.atr",
    "V6": "00513_points_lead_V6.atr",
}

# Aux strings written in the PTB-XL+ files, in ECGDeli FPT column order.
FIELDS = (
    "p-wave onset",
    "p-wave peak",
    "p-wave offset",
    "QRS onset",
    "Q peak",
    "R peak",
    "S peak",
    "QRS offset",
    "L point (for STEMI)",
    "t-wave onset",
    "t-wave peak",
    "t-wave offset",
)

# Lead-wise column index in ExtractIntervalFeaturesFromFPT, 0-based.
LEAD_FORMULAS = {
    "P_DurFull": ("p-wave offset", "p-wave onset"),
    "T_DurFull": ("t-wave offset", "t-wave onset"),
    "PQ_Int": ("QRS onset", "p-wave onset"),
    "PR_Int": ("R peak", "p-wave onset"),
    "QRS_Dur": ("QRS offset", "QRS onset"),
    "QT_Int": ("t-wave offset", "QRS onset"),
}

SYNC_FORMULAS = {
    "P_Dur": ("p-wave offset", "p-wave onset"),
    "T_Dur": ("t-wave offset", "t-wave onset"),
    "PQ_Int": ("QRS onset", "p-wave onset"),
    "PR_Int": ("R peak", "p-wave onset"),
    "QRS_Dur": ("QRS offset", "QRS onset"),
    "QT_Int": ("t-wave offset", "QRS onset"),
}

EXACT = 1e-6
CLOSE = 1e-4


def parse_atr(path: Path) -> list[dict[str, object]]:
    raw = np.frombuffer(path.read_bytes(), dtype=np.uint8)
    if raw.size % 2:
        raw = raw[:-1]
    fb = raw.reshape(-1, 2)
    rows: list[dict[str, object]] = []
    total = 0
    bpi = 0
    while bpi < fb.shape[0] - 1:
        sample_diff = 0
        while int(fb[bpi, 1]) >> 2 == 59:
            skip = (
                (int(fb[bpi + 1, 0]) << 16)
                + (int(fb[bpi + 1, 1]) << 24)
                + int(fb[bpi + 2, 0])
                + (int(fb[bpi + 2, 1]) << 8)
            )
            if skip > 2147483647:
                skip -= 4294967296
            sample_diff += skip
            bpi += 3
        label = int(fb[bpi, 1]) >> 2
        sample_diff += int(fb[bpi, 0]) + 256 * (int(fb[bpi, 1]) & 3)
        bpi += 1
        total += int(sample_diff)
        aux = None
        if bpi >= fb.shape[0]:
            rows.append({"sample": total, "label_store": label, "aux": aux})
            break
        nxt = int(fb[bpi, 1]) >> 2
        while nxt > 59 and bpi < fb.shape[0]:
            if nxt == 63:
                length = int(fb[bpi, 0])
                span = int(math.ceil(length / 2))
                blob = fb[bpi + 1 : bpi + 1 + span].flatten()
                if length & 1:
                    blob = blob[:-1]
                aux = "".join(chr(int(char)) for char in blob)
                bpi += 1 + span
            elif nxt in (60, 61, 62):
                bpi += 1
            else:
                raise ValueError(f"unsupported annotation extension {nxt} in {path.name}")
            if bpi >= fb.shape[0]:
                break
            nxt = int(fb[bpi, 1]) >> 2
        rows.append({"sample": total, "label_store": label, "aux": aux})
    return rows


def beats_from_rows(rows: list[dict[str, object]]) -> list[dict[str, int]]:
    resolution = [row for row in rows if row["aux"] == "## time resolution: 500"]
    if len(resolution) != 1:
        raise ValueError("the annotation does not state time resolution 500 exactly once")
    grouped: dict[str, list[int]] = {field: [] for field in FIELDS}
    for row in rows:
        aux = row["aux"]
        if aux in grouped:
            grouped[aux].append(int(row["sample"]))
    counts = {field: len(samples) for field, samples in grouped.items()}
    if len(set(counts.values())) != 1:
        raise ValueError(f"uneven fiducial counts: {counts}")
    n_beats = next(iter(counts.values()))
    return [
        {field: grouped[field][beat] for field in FIELDS}
        for beat in range(n_beats)
    ]


def samples_to_ms(later: float, earlier: float) -> float:
    if not math.isfinite(later) or not math.isfinite(earlier):
        return math.nan
    return 2.0 * (later - earlier)


def second_order_ms(later: np.ndarray, earlier: np.ndarray) -> float:
    """ECGDeli sync rule: 2nd latest end minus 2nd earliest start.

    Samples below 5 are removed first, matching FPT_mat(FPT_mat<5)=NaN
    before maxk/mink. NaNs are omitted because the function comment defines
    the statistic on detectable boundaries.
    """
    later = later.astype(float).copy()
    earlier = earlier.astype(float).copy()
    later[later < 5] = math.nan
    earlier[earlier < 5] = math.nan
    later = later[np.isfinite(later)]
    earlier = earlier[np.isfinite(earlier)]
    if later.size < 2 or earlier.size < 2:
        return math.nan
    second_latest = float(np.sort(later)[-2])
    second_earliest = float(np.sort(earlier)[1])
    return samples_to_ms(second_latest, second_earliest)


def successive_rr_ms(r_peaks: np.ndarray) -> np.ndarray:
    """RR_i = 2 * (R_{i+1} - R_i). One value per gap, so the length is N-1.

    ExtractIntervalFeaturesFromFPT copies the last gap onto an extra row so
    the matrix has one RR per beat. The published count for record 513 is
    the number of gaps, not that padded length.
    """
    return 2.0 * np.diff(np.asarray(r_peaks, dtype=float))


def framingham(qt_ms: float, rr_ms_value: float) -> float:
    return 1000.0 * (qt_ms / 1000.0 + 0.154 * (1.0 - 0.001 * rr_ms_value))


def load_published() -> pd.Series:
    frame = pd.read_csv(PUBLISHED)
    row = frame.loc[frame["ecg_id"] == 513]
    if len(row) != 1:
        raise SystemExit(f"expected one row for ecg_id 513, found {len(row)}")
    return row.iloc[0]


def split_name(name: str) -> tuple[str, str, str]:
    leads = (
        "III",
        "II",
        "aVF",
        "aVL",
        "aVR",
        "V1",
        "V2",
        "V3",
        "V4",
        "V5",
        "V6",
        "Global",
        "I",
    )
    if name.startswith("HA__"):
        stat = "value"
        rest = name
        for suffix, label in (("_iqr", "iqr"), ("_count", "count")):
            if name.endswith(suffix):
                stat = label
                rest = name[: -len(suffix)]
                break
        return "HA", "Global", stat
    stat = "value"
    base = name
    for suffix, label in (("_iqr", "iqr"), ("_count", "count")):
        if name.endswith(suffix):
            stat = label
            base = name[: -len(suffix)]
            break
    for lead in leads:
        token = f"_{lead}"
        if base.endswith(token):
            return base[: -len(token)], lead, stat
    raise ValueError(name)


def status_for(published: float | None, reconstructed: float | None, statistic: str) -> str:
    if reconstructed is None or (isinstance(reconstructed, float) and math.isnan(reconstructed)):
        return "MISSING"
    if published is None or (isinstance(published, float) and math.isnan(published)):
        return "DIFFERENT"
    diff = abs(published - reconstructed)
    if statistic == "count":
        return "EXACT" if diff == 0 else "DIFFERENT"
    if diff <= EXACT:
        return "EXACT"
    if diff <= CLOSE:
        return "CLOSE"
    return "DIFFERENT"


def main() -> None:
    lead_beats = {lead: beats_from_rows(parse_atr(FID / filename)) for lead, filename in LEAD_FILES.items()}
    global_beats = beats_from_rows(parse_atr(FID / "00513_points_global.atr"))
    n_beats = len(next(iter(lead_beats.values())))
    if any(len(beats) != n_beats for beats in lead_beats.values()):
        raise SystemExit("leads do not share one beat count")

    (HERE / "lead_mapping_v2.json").write_text(
        json.dumps(
            {
                "record": "00513",
                "csv_column_to_file": LEAD_FILES,
                "note": "aVL and aVF filenames are exchanged relative to the CSV columns. Other names match. The published CSV was not edited.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    beat_rows: list[dict[str, object]] = []
    series: dict[str, np.ndarray] = {}

    for family, (later, earlier) in LEAD_FORMULAS.items():
        for lead, beats in lead_beats.items():
            values = np.array(
                [samples_to_ms(beat[later], beat[earlier]) for beat in beats],
                dtype=float,
            )
            series[f"{family}_{lead}"] = values
            for beat_index, value in enumerate(values):
                beat_rows.append(
                    {
                        "lead": lead,
                        "beat": beat_index,
                        "feature": family,
                        "later": later,
                        "earlier": earlier,
                        "value_ms": value,
                        "rule": "leadwise sample difference times 2",
                    }
                )

    for family, (later, earlier) in SYNC_FORMULAS.items():
        values = []
        for beat_index in range(n_beats):
            later_samples = np.array([lead_beats[lead][beat_index][later] for lead in LEAD_FILES])
            earlier_samples = np.array([lead_beats[lead][beat_index][earlier] for lead in LEAD_FILES])
            value = second_order_ms(later_samples, earlier_samples)
            values.append(value)
            beat_rows.append(
                {
                    "lead": "Global",
                    "beat": beat_index,
                    "feature": family,
                    "later": later,
                    "earlier": earlier,
                    "value_ms": value,
                    "rule": "2nd latest minus 2nd earliest, then times 2",
                }
            )
        series[f"{family}_Global"] = np.array(values, dtype=float)

    rr = successive_rr_ms(np.array([beat["R peak"] for beat in global_beats], dtype=float))
    series["RR_Mean_Global"] = rr
    for beat_index, value in enumerate(rr):
        beat_rows.append(
            {
                "lead": "Global",
                "beat": beat_index,
                "feature": "RR_Mean",
                "later": "next R peak",
                "earlier": "R peak",
                "value_ms": value,
                "rule": "2 times the gap between successive global R peaks; the trailing copy used inside ECGDeli is not included",
            }
        )

    qt_sync = series["QT_Int_Global"]
    qt_for_qtc = qt_sync[: rr.size]
    qtc_beats = np.array(
        [framingham(float(qt), float(rr_value)) for qt, rr_value in zip(qt_for_qtc, rr)],
        dtype=float,
    )
    series["QT_IntFramingham_Global"] = qtc_beats
    for beat_index, value in enumerate(qtc_beats):
        beat_rows.append(
            {
                "lead": "Global",
                "beat": beat_index,
                "feature": "QT_IntFramingham",
                "later": "sync QT",
                "earlier": "sync RR",
                "value_ms": value,
                "rule": "Framingham of sync QT at beat i and the RR gap that starts at that R; the last beat has no following R and is omitted",
            }
        )
    qtc_after = framingham(float(np.median(qt_for_qtc)), float(np.median(rr)))

    with (HERE / "beat_features_00513_v2.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["lead", "beat", "feature", "later", "earlier", "value_ms", "rule"],
        )
        writer.writeheader()
        writer.writerows(beat_rows)

    aggregated_rows = []
    aggregated: dict[str, dict[str, float | int | None]] = {}
    for key, values in series.items():
        reduced = aggregate_beats(values)
        aggregated[key] = reduced.as_dict()
        aggregated_rows.append({"series": key, **reduced.as_dict()})
    with (HERE / "aggregated_features_00513_v2.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["series", "value", "iqr", "count", "percentile_method"])
        writer.writeheader()
        writer.writerows(aggregated_rows)

    published = load_published()
    comparison = []
    counts = {"EXACT": 0, "CLOSE": 0, "DIFFERENT": 0, "MISSING": 0, "NOT_REPRODUCIBLE": 0}
    families: dict[str, dict[str, int]] = {}
    errors: list[float] = []
    for name in FEATURE_COLUMNS:
        family, lead, stat = split_name(name)
        raw = published[name]
        published_value = None if pd.isna(raw) else float(raw)
        bucket = families.setdefault(
            family,
            {"total_features": 0, "EXACT": 0, "CLOSE": 0, "DIFFERENT": 0, "MISSING": 0, "NOT_REPRODUCIBLE": 0},
        )
        bucket["total_features"] += 1
        key = f"{family}_{lead}"
        if key not in aggregated:
            status = "NOT_REPRODUCIBLE"
            reconstructed = None
            note = non_reproducible_note(family)
            source = "NOT_REPRODUCIBLE"
        else:
            reduced = aggregated[key]
            reconstructed = reduced[stat]
            if reconstructed is None:
                status = "MISSING"
            else:
                reconstructed = float(reconstructed)
                status = status_for(published_value, reconstructed, stat)
            source = "AGGREGATED"
            note = "median, linear percentile IQR, finite count; beat values from the ECGDeli interval formulas"
        if status in ("EXACT", "CLOSE", "DIFFERENT") and published_value is not None and reconstructed is not None:
            errors.append(abs(published_value - reconstructed))
        counts[status] += 1
        bucket[status] += 1
        diff = None
        if published_value is not None and reconstructed is not None:
            diff = abs(published_value - reconstructed)
        comparison.append(
            {
                "feature": name,
                "family": family,
                "published": "" if published_value is None else published_value,
                "reconstructed": "" if reconstructed is None else reconstructed,
                "abs_error": "" if diff is None else diff,
                "status": status,
                "source": source,
                "notes": note,
            }
        )

    with (HERE / "comparison_fiducials_00513_v2.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["feature", "family", "published", "reconstructed", "abs_error", "status", "source", "notes"],
        )
        writer.writeheader()
        writer.writerows(comparison)

    with (HERE / "feature_family_results_00513_v2.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["family", "total_features", "exact", "close", "different", "missing", "not_reproducible", "coverage", "notes"],
        )
        writer.writeheader()
        for family, bucket in families.items():
            covered = bucket["EXACT"] + bucket["CLOSE"] + bucket["DIFFERENT"]
            writer.writerow(
                {
                    "family": family,
                    "total_features": bucket["total_features"],
                    "exact": bucket["EXACT"],
                    "close": bucket["CLOSE"],
                    "different": bucket["DIFFERENT"],
                    "missing": bucket["MISSING"],
                    "not_reproducible": bucket["NOT_REPRODUCIBLE"],
                    "coverage": covered / bucket["total_features"],
                    "notes": non_reproducible_note(family) if bucket["NOT_REPRODUCIBLE"] == bucket["total_features"] else "interval formulas from ExtractIntervalFeaturesFromFPT",
                }
            )

    covered = counts["EXACT"] + counts["CLOSE"] + counts["DIFFERENT"]
    summary = {
        "record": "00513",
        "total": 531,
        "exact": counts["EXACT"],
        "close": counts["CLOSE"],
        "different": counts["DIFFERENT"],
        "missing": counts["MISSING"],
        "not_reproducible": counts["NOT_REPRODUCIBLE"],
        "coverage": covered / 531,
        "mae": None if not errors else float(np.mean(errors)),
        "median_absolute_error": None if not errors else float(np.median(errors)),
        "max_absolute_error": None if not errors else float(np.max(errors)),
        "paired_features": len(errors),
        "qt_variant_1_correction_then_median": aggregated["QT_IntFramingham_Global"],
        "qt_variant_2_median_then_correction": qtc_after,
        "winner_selected": False,
        "percentile_method": "linear",
        "network_called": False,
    }
    (HERE / "fiducial_reconstruction_summary_00513_v2.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


def non_reproducible_note(family: str) -> str:
    notes = {
        "P_Amp": "Amplitude reads the signal matrix at a fiducial. The matrix filter and baseline used by PTB-XL+ are unknown, so the raw sample was not substituted.",
        "Q_Amp": "Amplitude reads the signal matrix at a fiducial. The matrix filter and baseline used by PTB-XL+ are unknown, so the raw sample was not substituted.",
        "R_Amp": "Amplitude reads the signal matrix at a fiducial. The matrix filter and baseline used by PTB-XL+ are unknown, so the raw sample was not substituted.",
        "S_Amp": "Amplitude reads the signal matrix at a fiducial. The matrix filter and baseline used by PTB-XL+ are unknown, so the raw sample was not substituted.",
        "T_Amp": "Amplitude reads the signal matrix at a fiducial. The matrix filter and baseline used by PTB-XL+ are unknown, so the raw sample was not substituted.",
        "P_Morph": "The fiducial files contain wave boundaries, not morphology codes -3..3. Get_P_Morphology was not reimplemented.",
        "QT_IntCorr": "ECGDeli computes Framingham on the synchronised QT and RR only. A per-lead correction was not added.",
        "ST_Elev": "The files contain an L point marked for STEMI. They do not contain Gaussian parameters, and ECGDeli does not export an ST amplitude from that point.",
        "HA": "No elHA input is present in the fiducial files, and ECGDeli v1.1 has no heart-axis function.",
    }
    return notes.get(family, "No beat series was defined for this column from the published fiducials.")


if __name__ == "__main__":
    main()
