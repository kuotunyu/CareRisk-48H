from __future__ import annotations

from carerisk48h.features.tabular import build_feature_frame
from carerisk48h.guard import QualityOODGuard
from carerisk48h.inference import predict_stay
from carerisk48h.models.logistic import fit_logistic
from carerisk48h.synthetic import generate_synthetic_cohort


def test_inference_hides_probability_when_guard_denies() -> None:
    stays, outcomes = generate_synthetic_cohort(140, seed=2026)
    features = build_feature_frame(stays, include_slope=False)
    columns = [column for column in features if column != "RecordID"]
    labels = outcomes.set_index("RecordID").loc[features["RecordID"], "label"]
    model = fit_logistic(features[columns], labels, seed=17)
    guard = QualityOODGuard.fit(stays[:100], seed=2026, n_jobs=1)
    guard.ood_score_min = float("inf")
    result = predict_stay(
        {
            "model_family": "logistic",
            "model": model,
            "feature_columns": columns,
            "guard": guard,
            "threshold": 0.5,
        },
        stays[120],
    )
    assert result.requires_human_review
    assert result.raw_probability is None
    assert result.calibrated_probability is None
    assert result.threshold is None


def test_inference_round_trip_returns_research_probability_when_allowed() -> None:
    stays, outcomes = generate_synthetic_cohort(140, seed=2026)
    features = build_feature_frame(stays, include_slope=False)
    columns = [column for column in features if column != "RecordID"]
    labels = outcomes.set_index("RecordID").loc[features["RecordID"], "label"]
    model = fit_logistic(features[columns], labels, seed=17)
    guard = QualityOODGuard.fit(stays[:100], seed=2026, n_jobs=1)
    guard.dynamic_variable_coverage_min = 0
    guard.measurement_count_min = 0
    guard.core_vital_groups_min = 0
    guard.ood_score_min = float("-inf")
    result = predict_stay(
        {
            "model_family": "logistic",
            "model": model,
            "feature_columns": columns,
            "guard": guard,
            "threshold": 0.5,
        },
        stays[120],
    )
    assert result.allow_probability
    assert result.raw_probability is not None
    assert result.calibrated_probability is not None
    assert result.contributors
