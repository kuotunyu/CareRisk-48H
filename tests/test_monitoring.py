from __future__ import annotations

import json

import numpy as np
import pytest

from carerisk48h.monitoring import build_monitoring_report, population_stability_index


def _assessment(index: int, *, shifted: bool = False) -> dict[str, object]:
    abstain = shifted and index < 60
    return {
        "allow_probability": not abstain,
        "requires_human_review": abstain,
        "reasons": ["value pattern exceeds train-derived range"] if abstain else [],
        "quality": {
            "RecordID": 900_000 + index,
            "dynamic_variable_coverage": 0.12 + index * 0.0001 if shifted else 0.78,
            "measurement_count": 4 + index % 2 if shifted else 220 + index % 5,
            "core_vital_groups": 1 if shifted else 5,
        },
        "ood_score": -0.8 - index * 0.0001 if shifted else 0.15,
        "value_pattern_guard_available": True,
        "value_shift_score": 80.0 + index * 0.01 if shifted else 1.0,
    }


def test_population_stability_index_is_zero_for_identical_values() -> None:
    values = np.linspace(0.05, 0.95, 100)

    assert population_stability_index(values, values) == pytest.approx(0.0, abs=1e-12)


def test_monitoring_does_not_alert_on_identical_cohorts() -> None:
    reference = [_assessment(index) for index in range(100)]
    probabilities = np.linspace(0.05, 0.45, 100)

    report = build_monitoring_report(
        reference,
        reference,
        reference_probabilities=probabilities,
        current_probabilities=probabilities,
    )

    assert report["alert"] is False
    assert report["alerts"] == []
    assert report["abstention_rate_delta"] == pytest.approx(0.0)
    assert all(signal["psi"] == pytest.approx(0.0) for signal in report["signals"].values())


def test_monitoring_alerts_on_missingness_value_and_abstention_shift() -> None:
    reference = [_assessment(index) for index in range(100)]
    current = [_assessment(index, shifted=True) for index in range(100)]

    report = build_monitoring_report(
        reference,
        current,
        reference_probabilities=np.linspace(0.05, 0.45, 100),
        current_probabilities=np.linspace(0.75, 0.95, 100),
        current_schema_rejections=20,
    )

    assert report["alert"] is True
    assert report["abstention_rate_delta"] == pytest.approx(0.60)
    assert "abstention_rate_delta" in report["alerts"]
    assert "schema_rejection_rate_delta" in report["alerts"]
    assert report["signals"]["dynamic_variable_coverage"]["alert"] is True
    assert report["signals"]["value_shift_score"]["alert"] is True
    assert report["signals"]["probability"]["alert"] is True

    serialized = json.dumps(report, sort_keys=True)
    assert "RecordID" not in serialized
    assert "record_id" not in serialized.lower()
    assert "monitoring_values" not in serialized


def test_monitoring_rejects_empty_or_misaligned_inputs() -> None:
    assessment = _assessment(0)
    with pytest.raises(ValueError, match="non-empty"):
        build_monitoring_report([], [assessment])
    with pytest.raises(ValueError, match="probabilities"):
        build_monitoring_report(
            [assessment],
            [assessment],
            reference_probabilities=[0.2, 0.3],
            current_probabilities=[0.2],
        )


def test_monitoring_buckets_unknown_reasons_and_deduplicates_per_assessment() -> None:
    reference = [_assessment(index) for index in range(2)]
    current = [_assessment(index) for index in range(2)]
    current[0]["allow_probability"] = False
    current[0]["reasons"] = [
        "value pattern exceeds train-derived range",
        "value pattern exceeds train-derived range",
        "RecordID 900000 free-text incident",
    ]

    report = build_monitoring_report(reference, current)
    reason_rates = report["current"]["reason_rates"]

    assert reason_rates == {"other": 0.5, "value_pattern_shift": 0.5}
    assert all(rate <= 1.0 for rate in reason_rates.values())
    assert "900000" not in json.dumps(report, sort_keys=True)


def test_monitoring_alerts_when_probability_availability_becomes_not_comparable() -> None:
    reference = [_assessment(index) for index in range(20)]
    current = [_assessment(index) for index in range(20)]

    report = build_monitoring_report(
        reference,
        current,
        reference_probabilities=[0.2] * 20,
        current_probabilities=[None] * 20,
    )
    probability = report["signals"]["probability"]

    assert probability["status"] == "not_comparable"
    assert probability["psi"] is None
    assert probability["reference_availability_rate"] == 1.0
    assert probability["current_availability_rate"] == 0.0
    assert probability["alert"] is True
    assert "availability:probability" in report["alerts"]


@pytest.mark.parametrize("rejections", [True, 1.5, "2"])
def test_monitoring_rejects_non_integer_schema_rejection_counts(rejections: object) -> None:
    assessment = _assessment(0)

    with pytest.raises(ValueError, match="integer"):
        build_monitoring_report(
            [assessment],
            [assessment],
            current_schema_rejections=rejections,
        )
