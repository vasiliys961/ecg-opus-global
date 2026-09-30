"""Experimental beat-level aggregation for a future ECGDeli 1.1 run.

The PTB-XL+ paper states that each published feature is the median across
beats, that the published variability is the (0.25, 0.75) interquartile
range, and that the third number is the count of beats considered.

This module implements only those three reductions. It does not delineate
a signal, filter it, reorder leads, or apply a medical formula.

The NumPy percentile method is an experimental parameter. The authors'
quantile algorithm is unknown. Do not treat a later numerical match as
proof that this method is theirs.

Callers must pass beat values that came from an actual ECGDeli 1.1 run.
This module does not read the published CSV and does not invent beats.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass

import numpy as np

EXPERIMENTAL_PERCENTILE_METHOD = "linear"
PAPER_STATEMENT = (
    "median across beats; (0.25, 0.75) interquartile range; "
    "count of beats considered for that feature"
)


@dataclass(frozen=True)
class AggregatedFeature:
    value: float | None
    iqr: float | None
    count: int
    percentile_method: str

    def as_dict(self) -> dict[str, float | int | str | None]:
        return {
            "value": self.value,
            "iqr": self.iqr,
            "count": self.count,
            "percentile_method": self.percentile_method,
        }


def _finite(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64).reshape(-1)
    return array[np.isfinite(array)]


def aggregate_beats(values: np.ndarray) -> AggregatedFeature:
    """Reduce one beat-level series.

    value = median of finite numbers
    iqr = percentile 75 minus percentile 25
    count = number of finite numbers
    """
    finite = _finite(values)
    count = int(finite.size)
    if count == 0:
        return AggregatedFeature(None, None, 0, EXPERIMENTAL_PERCENTILE_METHOD)
    median = float(np.median(finite))
    q75 = float(np.percentile(finite, 75, method=EXPERIMENTAL_PERCENTILE_METHOD))
    q25 = float(np.percentile(finite, 25, method=EXPERIMENTAL_PERCENTILE_METHOD))
    iqr = q75 - q25
    if not math.isfinite(median) or not math.isfinite(iqr):
        raise ValueError("aggregation produced a non-finite number")
    return AggregatedFeature(median, iqr, count, EXPERIMENTAL_PERCENTILE_METHOD)


def framingham_qtc_ms(qt_ms: float, rr_ms: float) -> float:
    """Per-beat Framingham formula copied from ECGDeli's sync feature.

    QTc_ms = QT_ms + 154 * (1 - RR_ms / 1000)

    ECGDeli applies this inside ExtractIntervalFeaturesFromFPT to each
    beat, before any cross-beat median. This helper does not decide
    whether the published column is the median of those beats.
    """
    qtc = qt_ms + 154.0 * (1.0 - rr_ms / 1000.0)
    if not math.isfinite(qtc):
        raise ValueError("Framingham input is not finite")
    return qtc


def main() -> int:
    print(
        "ECGDeli 1.1 did not run. Beat-level measurements for record 00513 "
        "were not produced. Aggregation was not applied to an ECG.",
        file=sys.stderr,
    )
    print(
        "Refusing to read the published CSV or to synthesise beats.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
