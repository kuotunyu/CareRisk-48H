from __future__ import annotations

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
