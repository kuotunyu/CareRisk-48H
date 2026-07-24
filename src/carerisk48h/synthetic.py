"""Deterministic synthetic cohort for tests, CI, and the public demo."""

from __future__ import annotations

import numpy as np
import pandas as pd

from carerisk48h.constants import N_HOURS, STATIC_VARIABLES, TIME_SERIES_VARIABLES, VARIABLE_INDEX
from carerisk48h.data.parser import ParsedStay


def _delta_from_mask(mask: np.ndarray) -> np.ndarray:
    delta = np.zeros_like(mask, dtype=np.float32)
    for column in range(mask.shape[1]):
        last: int | None = None
        for hour in range(mask.shape[0]):
            if mask[hour, column]:
                last = hour
            else:
                delta[hour, column] = float(hour + 1 if last is None else hour - last)
    return delta


def generate_synthetic_cohort(
    n_patients: int = 400, *, seed: int = 2026
) -> tuple[list[ParsedStay], pd.DataFrame]:
    """Create non-clinical synthetic stays with irregular observations.

    The generated labels are intentionally formulaic and outputs must only be used as smoke tests.
    """
    if n_patients < 120:
        raise ValueError("synthetic split smoke tests require at least 120 patients")
    rng = np.random.default_rng(seed)
    stays: list[ParsedStay] = []
    labels: list[dict[str, int]] = []
    for index in range(n_patients):
        record_id = 900_000 + index
        icu_type = index % 4 + 1
        # Keep every mortality×ICUType stratum large enough for quick 70/15/15 splits.
        label = int((index // 4) % 5 == 0)
        age = float(np.clip(42 + index % 48 + rng.normal(0, 3), 18, 95))
        static = {
            "Age": age,
            "Gender": float(index % 2),
            "Height": float(165 + (index % 11) + rng.normal(0, 2)),
            "ICUType": float(icu_type),
            "Weight": float(62 + (index % 27) + rng.normal(0, 3)),
        }
        assert set(static) == set(STATIC_VARIABLES)

        shape = (N_HOURS, len(TIME_SERIES_VARIABLES))
        values = np.full(shape, np.nan, dtype=np.float32)
        mask = np.zeros(shape, dtype=np.bool_)
        observations: dict[str, tuple[tuple[float, float], ...]] = {}
        core_values = {
            "HR": 76 + 18 * label,
            "RespRate": 17 + 5 * label,
            "Temp": 36.8 + 0.7 * label,
            "NIMAP": 78 - 10 * label,
            "SaO2": 97 - 4 * label,
            "Creatinine": 0.9 + 0.8 * label,
            "BUN": 17 + 12 * label,
            "Glucose": 115 + 35 * label,
            "WBC": 9 + 4 * label,
            "Urine": 75 - 35 * label,
            "Weight": static["Weight"],
        }
        for variable in TIME_SERIES_VARIABLES:
            samples: list[tuple[float, float]] = []
            if variable in core_values:
                interval = 3 + (index + VARIABLE_INDEX[variable]) % 4
                start = (index + VARIABLE_INDEX[variable]) % interval
                for hour in range(start, N_HOURS, interval):
                    if rng.random() < (0.08 + 0.10 * label):
                        continue
                    value = max(0.0, core_values[variable] + rng.normal(0, 2.0))
                    values[hour, VARIABLE_INDEX[variable]] = value
                    mask[hour, VARIABLE_INDEX[variable]] = True
                    samples.append((hour + 0.25, float(value)))
            observations[variable] = tuple(samples)
        delta = _delta_from_mask(mask)
        stays.append(ParsedStay(record_id, static, values, mask, delta, observations))
        labels.append({"RecordID": record_id, "label": label})
    return stays, pd.DataFrame(labels).astype({"RecordID": "int64", "label": "int8"})
