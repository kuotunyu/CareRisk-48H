"""Leakage-safe tabular summary features from parsed stays."""

from __future__ import annotations

import numpy as np
import pandas as pd

from carerisk48h.constants import FORBIDDEN_FEATURE_COLUMNS, N_HOURS, TIME_SERIES_VARIABLES
from carerisk48h.data.parser import ParsedStay


def _slope(samples: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    if len(samples) < 2:
        return float("nan"), 0.0
    hours = np.asarray([hour for hour, _ in samples], dtype=np.float64)
    values = np.asarray([value for _, value in samples], dtype=np.float64)
    if np.allclose(hours, hours[0]):
        return float("nan"), 0.0
    return float(np.polyfit(hours, values, 1)[0]), 1.0


def build_feature_frame(stays: list[ParsedStay], *, include_slope: bool) -> pd.DataFrame:
    """Build deterministic static and per-variable summary features."""
    rows: list[dict[str, float | int]] = []
    for stay in stays:
        row: dict[str, float | int] = {"RecordID": stay.record_id}
        for name, value in stay.static.items():
            row[f"static_{name}"] = value
        for column, variable in enumerate(TIME_SERIES_VARIABLES):
            observed = stay.values[:, column][stay.mask[:, column]]
            prefix = f"{variable}__"
            row[prefix + "last"] = float(observed[-1]) if observed.size else float("nan")
            row[prefix + "mean"] = float(np.mean(observed)) if observed.size else float("nan")
            row[prefix + "min"] = float(np.min(observed)) if observed.size else float("nan")
            row[prefix + "max"] = float(np.max(observed)) if observed.size else float("nan")
            row[prefix + "count"] = float(len(stay.observations[variable]))
            row[prefix + "missing_fraction"] = float(1.0 - stay.mask[:, column].sum() / N_HOURS)
            if include_slope:
                slope, present = _slope(stay.observations[variable])
                row[prefix + "slope"] = slope
                row[prefix + "slope_present"] = present
        rows.append(row)
    frame = pd.DataFrame(rows).sort_values("RecordID").reset_index(drop=True)
    assert_no_forbidden_features(frame.drop(columns=["RecordID"]))
    return frame


def assert_no_forbidden_features(frame: pd.DataFrame) -> None:
    """Reject identity, label, and outcome-related columns at the feature boundary."""
    forbidden = set(frame.columns) & FORBIDDEN_FEATURE_COLUMNS
    if forbidden:
        raise ValueError(f"forbidden feature columns: {sorted(forbidden)}")
