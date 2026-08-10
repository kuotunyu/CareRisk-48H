from __future__ import annotations

from dataclasses import replace

import numpy as np

from carerisk48h.constants import VARIABLE_INDEX
from carerisk48h.guard import QualityOODGuard
from carerisk48h.synthetic import generate_synthetic_cohort


def test_guard_fit_scope_serialization_and_fail_closed(tmp_path) -> None:
    stays, _ = generate_synthetic_cohort(140, seed=2026)
    train = stays[:100]
    guard = QualityOODGuard.fit(train, seed=2026, n_jobs=1)
    assert set(guard.fit_record_ids) == {stay.record_id for stay in train}
    path = tmp_path / "guard.joblib"
    guard.save(path)
    loaded = QualityOODGuard.load(path)
    first = loaded.assess(stays[110])
    assert "allow_probability" in first
    loaded.ood_score_min = float("inf")
    denied = loaded.assess(stays[110])
    assert not denied["allow_probability"]
    assert denied["requires_human_review"]


def test_guard_abstains_on_train_derived_value_scale_shift() -> None:
    stays, _ = generate_synthetic_cohort(140, seed=2026)
    guard = QualityOODGuard.fit(stays[:100], seed=2026, n_jobs=1)
    source = stays[110]
    observations = dict(source.observations)
    observations["HR"] = tuple((hour, value * 1000.0) for hour, value in observations["HR"])
    values = source.values.copy()
    hr_column = VARIABLE_INDEX["HR"]
    values[source.mask[:, hr_column], hr_column] *= np.float32(1000.0)
    shifted = replace(source, observations=observations, values=values)

    result = guard.assess(shifted)

    assert result["value_pattern_guard_available"] is True
    assert result["value_shift_score"] > result["thresholds"]["value_shift_score_max"]
    assert "value pattern exceeds train-derived range" in result["reasons"]
    assert result["allow_probability"] is False


def test_guard_loads_legacy_pickle_without_value_reference(tmp_path) -> None:
    stays, _ = generate_synthetic_cohort(140, seed=2026)
    guard = QualityOODGuard.fit(stays[:100], seed=2026, n_jobs=1)
    for attribute in ("value_center", "value_scale", "value_shift_score_max"):
        delattr(guard, attribute)
    path = tmp_path / "legacy-guard.joblib"
    guard.save(path)

    loaded = QualityOODGuard.load(path)
    result = loaded.assess(stays[110])

    assert result["value_pattern_guard_available"] is False
    assert result["value_shift_score"] is None
    assert result["thresholds"]["value_shift_score_max"] is None
