"""Write the record-00513 comparison after ECGDeli failed to start.

Reads the published PTB-XL+ row and the canonical 531 names. Writes no
reconstructed ECG numbers. Does not call the ensemble.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from ecg_engine.feature_columns import FEATURE_COLUMNS
from reconstruct_aggregation import aggregate_beats

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PUBLISHED = (
    ROOT
    / "research/ecgdeli_reproduction/data/ptbxl_plus/ecgdeli_features_prefix.csv"
)

LEADS = (
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

DIRECT_LEAD_FAMILIES = frozenset(
    {
        "PQ_Int",
        "PR_Int",
        "QRS_Dur",
        "QT_Int",
        "P_DurFull",
        "T_DurFull",
        "P_Amp",
        "Q_Amp",
        "R_Amp",
        "S_Amp",
        "T_Amp",
        "P_Morph",
    }
)


def split_name(name: str) -> tuple[str, str, str]:
    if name.startswith("HA__"):
        stat = "value"
        rest = name
        for suffix, label in (("_iqr", "iqr"), ("_count", "count")):
            if name.endswith(suffix):
                stat = label
                rest = name[: -len(suffix)]
                break
        if rest != "HA__Global":
            raise ValueError(name)
        return "HA", "Global", stat
    stat = "value"
    base = name
    for suffix, label in (("_iqr", "iqr"), ("_count", "count")):
        if name.endswith(suffix):
            stat = label
            base = name[: -len(suffix)]
            break
    for lead in LEADS:
        token = f"_{lead}"
        if base.endswith(token):
            return base[: -len(token)], lead, stat
    raise ValueError(name)


def classify(family: str, lead: str) -> tuple[str, str, str]:
    """Return source, status, note. No reconstructed number."""
    if family == "HA":
        return (
            "NOT_REPRODUCIBLE",
            "NOT_REPRODUCIBLE",
            "ECGDeli v1.1 has no elHA function. Axis class was not invented.",
        )
    if family == "ST_Elev":
        return (
            "NOT_REPRODUCIBLE",
            "NOT_REPRODUCIBLE",
            "Dictionary name STc describes Gaussian ST fits. ECGDeli v1.1 does not export that amplitude. The L point is only a sample index.",
        )
    if family == "QT_IntCorr":
        return (
            "NOT_REPRODUCIBLE",
            "NOT_REPRODUCIBLE",
            "Dictionary calls this per-lead Framingham. ExtractIntervalFeaturesFromFPT computes Framingham only on the synchronised QT and RR, not per lead.",
        )
    if family == "QT_IntFramingham":
        return (
            "DERIVED_FROM_ECGDELI",
            "NOT_REPRODUCIBLE",
            "Per-beat sync Framingham is defined. Beat table is absent, so neither correction-then-median nor median-then-correction was computed. Dictionary name QTci_max was not treated as max().",
        )
    if lead == "Global":
        return (
            "UNKNOWN",
            "NOT_REPRODUCIBLE",
            "Dictionary wording says max across leads. ECGDeli sync features use the 2nd-latest minus 2nd-earliest boundary. Neither statistic was selected.",
        )
    if family in DIRECT_LEAD_FAMILIES:
        return (
            "AGGREGATED",
            "MISSING",
            "Beat-level series is defined by ECGDeli v1.1. Median, IQR and count were not computed because ECGDeli did not start.",
        )
    return ("UNKNOWN", "NOT_REPRODUCIBLE", "No public ECGDeli series was identified for this column.")


def arithmetic_check() -> dict[str, object]:
    sample = aggregate_beats(np.array([1.0, 2.0, 3.0, 4.0]))
    return {
        "applied_to_ecg": False,
        "input": [1.0, 2.0, 3.0, 4.0],
        "result": sample.as_dict(),
        "purpose": "Checks median, percentile difference and count on four ordinary numbers. Not an ECG feature.",
    }


def main() -> None:
    frame = pd.read_csv(PUBLISHED)
    row = frame.loc[frame["ecg_id"] == 513]
    if len(row) != 1:
        raise SystemExit(f"expected one published row for ecg_id 513, found {len(row)}")
    published = row.iloc[0]
    missing_cols = [name for name in FEATURE_COLUMNS if name not in published.index]
    if missing_cols:
        raise SystemExit(f"published row is missing columns: {missing_cols[:5]}")

    features: list[dict[str, object]] = []
    counts = {
        "EXACT": 0,
        "CLOSE": 0,
        "DIFFERENT": 0,
        "MISSING": 0,
        "NOT_REPRODUCIBLE": 0,
    }
    family_counts: dict[str, dict[str, int]] = {}
    for index, name in enumerate(FEATURE_COLUMNS):
        family, lead, stat = split_name(name)
        source, status, note = classify(family, lead)
        raw = published[name]
        published_value: float | None
        if raw is None or (isinstance(raw, float) and math.isnan(raw)) or pd.isna(raw):
            published_value = None
        else:
            published_value = float(raw)
        counts[status] += 1
        bucket = family_counts.setdefault(
            family, {"MISSING": 0, "NOT_REPRODUCIBLE": 0, "columns": 0}
        )
        bucket[status] += 1
        bucket["columns"] += 1
        features.append(
            {
                "index": index,
                "feature": name,
                "family": family,
                "lead": lead,
                "statistic": stat,
                "published_value": published_value,
                "reconstructed_value": None,
                "absolute_difference": None,
                "relative_difference": None,
                "status": status,
                "source": source,
                "notes": note,
            }
        )

    if sum(counts.values()) != 531:
        raise SystemExit(f"column count {sum(counts.values())} is not 531")

    OUT.joinpath("comparison_00513.csv").write_text("", encoding="utf-8")
    with OUT.joinpath("comparison_00513.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "feature",
                "family",
                "published_value",
                "reconstructed_value",
                "absolute_difference",
                "relative_difference",
                "status",
                "source",
                "notes",
            ],
        )
        writer.writeheader()
        for item in features:
            writer.writerow({key: "" if item[key] is None else item[key] for key in writer.fieldnames})

    summary_path = OUT / "comparison_summary.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "record",
                "pipeline",
                "coverage",
                "exact_percent",
                "close_percent",
                "mae",
                "median_ae",
                "max_ae",
                "note",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "record": "00513",
                "pipeline": "not_started",
                "coverage": 0,
                "exact_percent": 0,
                "close_percent": 0,
                "mae": "",
                "median_ae": "",
                "max_ae": "",
                "note": "ECGDeli did not start. No paired absolute errors.",
            }
        )
        for record in ("00514", "00515", "00516", "00517"):
            writer.writerow(
                {
                    "record": record,
                    "pipeline": "NOT_RUN",
                    "coverage": "",
                    "exact_percent": "",
                    "close_percent": "",
                    "mae": "",
                    "median_ae": "",
                    "max_ae": "",
                    "note": "Not started. Record 00513 did not produce a beat table.",
                }
            )

    reproduced = counts["EXACT"] + counts["CLOSE"] + counts["DIFFERENT"]
    result = {
        "record": "00513",
        "status": "EXPERIMENTAL",
        "reproduction_status": "EXACT_REPRODUCTION_NOT_ESTABLISHED",
        "raw_to_531_status": "NOT_PROVEN",
        "raw_variants": [
            {
                "id": "A",
                "path": "records500/00000/00513_hr",
                "sampling_frequency_hz": 500,
                "samples": 5000,
                "leads": 12,
                "duration_s": 10,
                "executed": False,
            },
            {
                "id": "B",
                "path": "records100/00000/00513_lr",
                "sampling_frequency_hz": 100,
                "samples": 1000,
                "leads": 12,
                "duration_s": 10,
                "executed": False,
            },
        ],
        "ecgdeli_version": "1.1",
        "ecgdeli_commit": "3c13b1b2ff55152360f3cee992c1d1d66099aa14",
        "ecgdeli_started": False,
        "blocker": "matlab, octave and MATLAB Runtime were not found",
        "published_feature_count": 531,
        "reconstructed_feature_count": reproduced,
        "metrics": {
            "N_total": 531,
            "N_exact": counts["EXACT"],
            "N_close": counts["CLOSE"],
            "N_different": counts["DIFFERENT"],
            "N_missing": counts["MISSING"],
            "N_not_reproducible": counts["NOT_REPRODUCIBLE"],
            "exact_match_percent": 0.0,
            "close_match_percent": 0.0,
            "coverage_percent": 0.0,
            "mean_absolute_error": None,
            "median_absolute_error": None,
            "max_absolute_error": None,
            "tolerances": {"exact": 1e-6, "close": 1e-4},
            "error_note": "Absolute errors are null because no reconstructed number exists. They are not zero.",
        },
        "family_counts": family_counts,
        "qt_experiments": {
            "formula": "QTc_ms = QT_ms + 154 * (1 - RR_ms / 1000)",
            "variant_1_correction_then_aggregate": "NOT_RUN",
            "variant_2_aggregate_then_correction": "NOT_RUN",
            "winner_selected": False,
        },
        "network_sensitivity": {
            "executed": False,
            "reason": "Reconstructed vector does not contain 531 features.",
        },
        "aggregator_arithmetic_check": arithmetic_check(),
        "features": features,
        "unknowns": [
            "author preprocessing",
            "sampling frequency used by the authors",
            "lead order expected by the PTB-XL+ ECGDeli run",
            "quantile algorithm",
            "global max versus sync second-order statistic",
            "per-lead QT correction",
            "ST_Elev Gaussian procedure",
            "heart-axis procedure",
        ],
        "conclusion": (
            "ECGDeli 1.1 did not start, so no beat-level table exists and "
            "no published feature was reconstructed. "
            "EXACT_REPRODUCTION_NOT_ESTABLISHED. RAW_TO_531_STATUS remains NOT_PROVEN."
        ),
    }
    OUT.joinpath("results_00513.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"missing={counts['MISSING']} not_reproducible={counts['NOT_REPRODUCIBLE']} "
        f"reproduced={reproduced}"
    )


if __name__ == "__main__":
    main()
