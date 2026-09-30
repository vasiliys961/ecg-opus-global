"""Assemble the step-12 audit for record 00513. Does not run ECGDeli."""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from ecg_engine.feature_columns import FEATURE_COLUMNS
from experiments.raw_to_531.reconstruct_from_fiducials import PUBLISHED, split_name

HERE = Path(__file__).resolve().parent
WINNER_QT = "framingham_per_beat_then_aggregate__lead_rr_padded__same_index"
WINNER_AMP = "P0_mV__csv_name__matlab1"
AMPLITUDE = {"P_Amp", "Q_Amp", "R_Amp", "S_Amp", "T_Amp"}


def load_csv(name: str) -> list[dict[str, str]]:
    with (HERE / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    published = pd.read_csv(PUBLISHED)
    published = published.loc[published["ecg_id"] == 513].iloc[0]
    compared = {row["feature"]: row for row in load_csv("comparison_fiducials_00513_v2.csv")}
    qt = {
        row["feature"]: row
        for row in load_csv("qt_correction_candidates_00513.csv")
        if row["candidate_formula"] == WINNER_QT
    }
    amp = {
        row["feature"]: row
        for row in load_csv("amplitude_preprocessing_grid_00513.csv")
        if row["preprocessing_id"] == WINNER_AMP
    }
    rows = []
    morph_rows = []
    for feature in FEATURE_COLUMNS:
        family, _lead, _stat = split_name(feature)
        published_value = float(published[feature])
        if family in AMPLITUDE:
            item = amp[feature]
            reconstructed = item["reconstructed"]
            error = item["abs_error"]
            numerical = "EXACT" if item["exact_1e6"] == "True" else "CALCULABLE_BUT_DIFFERENT"
            record = {
                "feature": feature,
                "family": family,
                "public_function": "ExtractAmplitudeFeaturesFromFPT",
                "input_required": "signal sample at the peak fiducial",
                "algorithm": "sample at fiducial; best tested input is raw mV, not an identified author filter",
                "reconstruction_status": "REQUIRES_PROCESSED_SIGNAL",
                "numerical_status": numerical,
                "published_value": published_value,
                "reconstructed_value": reconstructed,
                "abs_error": error,
            }
        elif family == "P_Morph":
            record = {
                "feature": feature,
                "family": family,
                "public_function": "Get_P_Morphology",
                "input_required": "signal, samplerate, FPT cell",
                "algorithm": "public v1.1 function; not executed, MATLAB and Octave are absent",
                "reconstruction_status": "PUBLIC_FUNCTION_NOT_EXECUTED",
                "numerical_status": "NOT_EXECUTED",
                "published_value": published_value,
                "reconstructed_value": "",
                "abs_error": "",
            }
            morph_rows.append(
                {
                    "feature": feature,
                    "published": published_value,
                    "reconstructed": "",
                    "abs_error": "",
                    "exact_1e6": False,
                    "status": "NOT_EXECUTED",
                }
            )
        elif family == "QT_IntCorr":
            item = qt[feature]
            numerical = "EXACT" if item["exact_match"] == "True" else "CALCULABLE_BUT_DIFFERENT"
            record = {
                "feature": feature,
                "family": family,
                "public_function": "none for the per-lead column; Framingham expression is the sync column",
                "input_required": "lead QT and padded lead RR",
                "algorithm": WINNER_QT,
                "reconstruction_status": numerical,
                "numerical_status": numerical,
                "published_value": published_value,
                "reconstructed_value": item["reconstructed_value"],
                "abs_error": item["absolute_error"],
            }
        elif family in {"ST_Elev", "HA"}:
            record = {
                "feature": feature,
                "family": family,
                "public_function": "none in ECGDeli 1.1",
                "input_required": "unknown",
                "algorithm": "unknown",
                "reconstruction_status": "AUTHOR_ALGORITHM_UNKNOWN",
                "numerical_status": "NOT_IN_ECGDELI",
                "published_value": published_value,
                "reconstructed_value": "",
                "abs_error": "",
            }
        else:
            item = compared[feature]
            record = {
                "feature": feature,
                "family": family,
                "public_function": "ExtractIntervalFeaturesFromFPT",
                "input_required": "published fiducial sample indices",
                "algorithm": "interval formulas and, for global QTc, Framingham on unpadded global RR",
                "reconstruction_status": item["status"] if item["status"] != "DIFFERENT" else "CALCULABLE_BUT_DIFFERENT",
                "numerical_status": item["status"] if item["status"] != "DIFFERENT" else "CALCULABLE_BUT_DIFFERENT",
                "published_value": published_value,
                "reconstructed_value": item["reconstructed"],
                "abs_error": item["abs_error"],
            }
        rows.append(record)

    fields = [
        "feature",
        "family",
        "public_function",
        "input_required",
        "algorithm",
        "reconstruction_status",
        "numerical_status",
        "published_value",
        "reconstructed_value",
        "abs_error",
    ]
    with (HERE / "step12_feature_status.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with (HERE / "pmorph_00513_final.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["feature", "published", "reconstructed", "abs_error", "exact_1e6", "status"],
        )
        writer.writeheader()
        writer.writerows(morph_rows)
    from collections import Counter
    print("rows", len(rows), "morph", len(morph_rows))
    print("reconstruction", Counter(row["reconstruction_status"] for row in rows))
    print("numerical", Counter(row["numerical_status"] for row in rows))


if __name__ == "__main__":
    main()
