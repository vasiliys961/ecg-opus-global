"""Write the 531-row reconstruction matrix and the forensic map.

Reads the v2 comparison. Does not recompute features and does not call the network.
"""

from __future__ import annotations

import csv
from pathlib import Path

from ecg_engine.feature_columns import FEATURE_COLUMNS
from experiments.raw_to_531.reconstruct_from_fiducials import split_name

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
COMPARISON = HERE / "comparison_fiducials_00513_v2.csv"

INTERVAL = {
    "PQ_Int": (
        "P onset, QRS onset",
        "ExtractIntervalFeaturesFromFPT",
        "2*(QRS onset - P onset); global uses the 2nd-order sync rule",
    ),
    "PR_Int": (
        "P onset, R peak",
        "ExtractIntervalFeaturesFromFPT",
        "2*(R peak - P onset); global uses the 2nd-order sync rule",
    ),
    "QRS_Dur": (
        "QRS onset, QRS offset",
        "ExtractIntervalFeaturesFromFPT",
        "2*(QRS offset - QRS onset); global uses the 2nd-order sync rule",
    ),
    "QT_Int": (
        "QRS onset, T offset",
        "ExtractIntervalFeaturesFromFPT",
        "2*(T offset - QRS onset); global uses the 2nd-order sync rule",
    ),
    "P_DurFull": (
        "P onset, P offset",
        "ExtractIntervalFeaturesFromFPT",
        "2*(P offset - P onset)",
    ),
    "T_DurFull": (
        "T onset, T offset",
        "ExtractIntervalFeaturesFromFPT",
        "2*(T offset - T onset)",
    ),
    "P_Dur": (
        "P onset, P offset across 12 leads",
        "ExtractIntervalFeaturesFromFPT",
        "sync: 2*(2nd latest P offset - 2nd earliest P onset)",
    ),
    "T_Dur": (
        "T onset, T offset across 12 leads",
        "ExtractIntervalFeaturesFromFPT",
        "sync: 2*(2nd latest T offset - 2nd earliest T onset)",
    ),
    "RR_Mean": (
        "successive global R peaks",
        "ExtractIntervalFeaturesFromFPT",
        "RR_i = 2*(R_{i+1}-R_i); published count is N-1, the function also copies the last gap",
    ),
    "QT_IntFramingham": (
        "sync QT of beat i and the RR gap that starts at that R",
        "ExtractIntervalFeaturesFromFPT",
        "1000*(QT/1000 + 0.154*(1 - 0.001*RR)) on each of the N-1 gaps, then median and IQR",
    ),
}

AMPLITUDE = {
    "P_Amp": "P peak",
    "Q_Amp": "Q peak",
    "R_Amp": "R peak",
    "S_Amp": "S peak",
    "T_Amp": "T peak",
}


def classify(family: str, comparison_status: str) -> dict[str, str]:
    if family in INTERVAL:
        required, function, formula = INTERVAL[family]
        return {
            "feature_type": "interval",
            "required_input": required,
            "available_input": "published fiducial sample indices for record 00513",
            "ecgdeli_function": function,
            "formula_known": "yes",
            "aggregation_known": "yes for this record: median, linear IQR, finite count",
            "reconstructability": "REPRODUCIBLE_FROM_FIDUCIALS",
            "status": "EXACT_FROM_FIDUCIALS",
            "publicly_available": "yes",
            "path": "fiducial sample indices and the public interval function",
            "notes": (
                ""
                if comparison_status == "EXACT"
                else "formula matches the published count; value and IQR differ by about 0.002 ms, above 1e-6"
            ),
        }
    if family in AMPLITUDE:
        peak = AMPLITUDE[family]
        return {
            "feature_type": "amplitude",
            "required_input": f"conditioned signal sample at {peak}",
            "available_input": f"{peak} sample index is public; the conditioned signal matrix is not",
            "ecgdeli_function": "ExtractAmplitudeFeaturesFromFPT",
            "formula_known": "yes: the sample at the fiducial, no unit conversion inside the function",
            "aggregation_known": "paper states median, IQR and count; not executed, because the sample value is absent",
            "reconstructability": "REPRODUCIBLE_FROM_RAW_SIGNAL",
            "status": "RECONSTRUCTABLE_FROM_RAW",
            "publicly_available": "fiducial index yes; amplitude no",
            "path": "public amplitude function on a signal whose filter and isoline are still UNKNOWN",
            "notes": "numerical match is not established; raw ADC was not substituted for the author matrix",
        }
    if family == "P_Morph":
        return {
            "feature_type": "morphology",
            "required_input": "signal, FPT, samplerate",
            "available_input": "FPT and raw signal are public; morphology codes are not in the atr files",
            "ecgdeli_function": "Get_P_Morphology",
            "formula_known": "the function is public and was not reimplemented",
            "aggregation_known": "unknown how integer codes were reduced; not executed",
            "reconstructability": "REQUIRES_ECGDELI_INTERMEDIATE_OUTPUT",
            "status": "REQUIRES_ECGDELI_OUTPUT",
            "publicly_available": "algorithm yes; this record's codes no",
            "path": "run the public morphology function; do not infer the code from amplitude",
            "notes": "FIR design inside the function hardcodes SampleRate 1000; record 00513 is 500 Hz",
        }
    if family == "QT_IntCorr":
        return {
            "feature_type": "corrected_interval",
            "required_input": "per-lead QT and a correction whose function is not in ECGDeli 1.1",
            "available_input": "per-lead QT can be computed; the per-lead correction cannot",
            "ecgdeli_function": "none in v1.1; Framingham there is only the sync column",
            "formula_known": "no",
            "aggregation_known": "no",
            "reconstructability": "REQUIRES_UNKNOWN_AUTHOR_ALGORITHM",
            "status": "REQUIRES_UNKNOWN_CODE",
            "publicly_available": "no",
            "path": "no public function writes a per-lead QTc",
            "notes": "dictionary name QTci_X is not an implementation",
        }
    if family == "ST_Elev":
        return {
            "feature_type": "st",
            "required_input": "ST elevation or depression from Gaussian fits, named STc in the dictionary",
            "available_input": "L-point sample index is in the fiducial file; elevation is not",
            "ecgdeli_function": "T_Detection writes the L point only; no STc function in v1.1",
            "formula_known": "no",
            "aggregation_known": "no",
            "reconstructability": "REQUIRES_UNKNOWN_AUTHOR_ALGORITHM",
            "status": "REQUIRES_UNKNOWN_CODE",
            "publicly_available": "no",
            "path": "L point is not an amplitude and was not turned into an approximation",
            "notes": "no Gaussian parameters are exported by v1.1",
        }
    if family == "HA":
        return {
            "feature_type": "axis",
            "required_input": "heart-axis class elHA",
            "available_input": "none of the class, its inputs, or its formula",
            "ecgdeli_function": "none; elHA is absent from v1.1",
            "formula_known": "no",
            "aggregation_known": "no",
            "reconstructability": "REQUIRES_UNKNOWN_AUTHOR_ALGORITHM",
            "status": "REQUIRES_UNKNOWN_CODE",
            "publicly_available": "no",
            "path": "blocker: no public implementation",
            "notes": "published row 513 is value 2, iqr 0, count 1; that row was not copied in",
        }
    raise KeyError(family)


def main() -> None:
    comparison = {row["feature"]: row for row in csv.DictReader(COMPARISON.open(encoding="utf-8"))}
    if list(comparison) != list(FEATURE_COLUMNS):
        raise SystemExit("comparison column order does not match the 531 schema")

    matrix_fields = [
        "feature",
        "family",
        "published_column",
        "feature_type",
        "required_input",
        "available_input",
        "ecgdeli_function",
        "formula_known",
        "aggregation_known",
        "reconstructability",
        "status",
        "comparison_status",
        "notes",
    ]
    rows = []
    for feature in FEATURE_COLUMNS:
        family, _lead, _stat = split_name(feature)
        info = classify(family, comparison[feature]["status"])
        rows.append(
            {
                "feature": feature,
                "family": family,
                "published_column": feature,
                "comparison_status": comparison[feature]["status"],
                **info,
            }
        )

    with (HERE / "feature_reconstruction_matrix.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=matrix_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Карта 531 признака после шага 8",
        "",
        "Запись `00513` / строка `ecg_id=513`. Опубликованные значения не изменялись.",
        "Current status — результат сравнения v2. Reconstruction path — откуда признак берётся.",
        "",
        "| # | Feature | Family | Current status | Required input | Publicly available? | Reconstruction path |",
        "| -: | --- | --- | --- | --- | --- | --- |",
    ]
    for index, row in enumerate(rows, start=1):
        lines.append(
            "| {n} | {feature} | {family} | {status} | {required} | {public} | {path} |".format(
                n=index,
                feature=row["feature"],
                family=row["family"],
                status=row["comparison_status"],
                required=row["required_input"].replace("|", "/"),
                public=row["publicly_available"].replace("|", "/"),
                path=row["path"].replace("|", "/"),
            )
        )
    lines.append("")
    (ROOT / "docs" / "FEATURE_531_FORENSIC_MAP.md").write_text("\n".join(lines), encoding="utf-8")
    print(len(rows))


if __name__ == "__main__":
    main()
