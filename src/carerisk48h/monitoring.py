"""Aggregate, outcome-free monitoring for input quality and abstention drift."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from numbers import Integral
from typing import Any

import numpy as np

_REASON_CODES = {
    "dynamic variable coverage below train 1st percentile": "low_dynamic_variable_coverage",
    "measurement count below train 1st percentile": "low_measurement_count",
    "fewer than three core vital groups": "insufficient_core_vital_groups",
    "input pattern below train 1st-percentile OOD score": "missingness_pattern_shift",
    "value pattern exceeds train-derived range": "value_pattern_shift",
}


def _finite_vector(values: Sequence[float] | np.ndarray, *, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or array.size == 0:
        raise ValueError(f"{name} must be a non-empty one-dimensional array")
    if np.any(~np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    return array


def population_stability_index(
    reference: Sequence[float] | np.ndarray,
    current: Sequence[float] | np.ndarray,
    *,
    bins: int = 10,
) -> float:
    """Compute PSI using reference-derived quantile bins.

    PSI is a distribution-shift signal. It does not measure model performance.
    """
    reference_array = _finite_vector(reference, name="reference")
    current_array = _finite_vector(current, name="current")
    if bins < 2:
        raise ValueError("bins must be at least 2")

    if float(np.ptp(reference_array)) == 0.0:
        center = float(reference_array[0])
        tolerance = max(abs(center) * 1e-6, 1e-6)
        edges = np.asarray([float("-inf"), center - tolerance, center + tolerance, float("inf")])
    else:
        quantiles = np.linspace(0.0, 1.0, bins + 1)[1:-1]
        internal = np.unique(np.quantile(reference_array, quantiles))
        edges = np.concatenate(([float("-inf")], internal, [float("inf")]))

    reference_counts, _ = np.histogram(reference_array, bins=edges)
    current_counts, _ = np.histogram(current_array, bins=edges)
    epsilon = 1e-6
    reference_fraction = np.clip(reference_counts / reference_array.size, epsilon, None)
    current_fraction = np.clip(current_counts / current_array.size, epsilon, None)
    psi = np.sum(
        (current_fraction - reference_fraction) * np.log(current_fraction / reference_fraction)
    )
    return float(psi)


def _numeric(value: Any, *, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not np.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _assessment_signals(
    assessments: Sequence[Mapping[str, Any]],
) -> dict[str, list[float]]:
    signals: dict[str, list[float]] = {
        "dynamic_variable_coverage": [],
        "log1p_measurement_count": [],
        "core_vital_groups": [],
        "ood_score": [],
        "value_shift_score": [],
    }
    for index, assessment in enumerate(assessments):
        quality = assessment.get("quality")
        if not isinstance(quality, Mapping):
            raise ValueError(f"assessment {index} must contain a quality mapping")
        coverage = _numeric(
            quality.get("dynamic_variable_coverage"),
            name=f"assessment {index} dynamic_variable_coverage",
        )
        measurement_count = _numeric(
            quality.get("measurement_count"),
            name=f"assessment {index} measurement_count",
        )
        if measurement_count < 0:
            raise ValueError("measurement_count must be non-negative")
        signals["dynamic_variable_coverage"].append(coverage)
        signals["log1p_measurement_count"].append(float(np.log1p(measurement_count)))
        signals["core_vital_groups"].append(
            _numeric(
                quality.get("core_vital_groups"),
                name=f"assessment {index} core_vital_groups",
            )
        )
        signals["ood_score"].append(
            _numeric(assessment.get("ood_score"), name=f"assessment {index} ood_score")
        )
        value_shift_score = assessment.get("value_shift_score")
        if value_shift_score is not None:
            signals["value_shift_score"].append(
                _numeric(
                    value_shift_score,
                    name=f"assessment {index} value_shift_score",
                )
            )
    return signals


def _probability_signal(
    probabilities: Sequence[float | None] | np.ndarray | None,
    *,
    expected_length: int,
    name: str,
) -> list[float] | None:
    if probabilities is None:
        return None
    if len(probabilities) != expected_length:
        raise ValueError(f"{name} probabilities must match assessment count")
    values: list[float] = []
    for index, value in enumerate(probabilities):
        if value is None:
            continue
        numeric = _numeric(value, name=f"{name} probability {index}")
        if not 0.0 <= numeric <= 1.0:
            raise ValueError(f"{name} probabilities must be in [0, 1]")
        values.append(numeric)
    return values


def _distribution_summary(values: Sequence[float]) -> dict[str, float | int]:
    array = np.asarray(values, dtype=np.float64)
    return {
        "n": int(array.size),
        "mean": float(np.mean(array)),
        "p05": float(np.percentile(array, 5.0)),
        "median": float(np.percentile(array, 50.0)),
        "p95": float(np.percentile(array, 95.0)),
    }


def _cohort_summary(
    assessments: Sequence[Mapping[str, Any]], schema_rejections: int
) -> dict[str, Any]:
    if isinstance(schema_rejections, bool) or not isinstance(schema_rejections, Integral):
        raise ValueError("schema rejection counts must be integers")
    schema_rejection_count = int(schema_rejections)
    if schema_rejection_count < 0:
        raise ValueError("schema rejection counts must be non-negative")
    abstentions = 0
    reasons: Counter[str] = Counter()
    for index, assessment in enumerate(assessments):
        allow_probability = assessment.get("allow_probability")
        if not isinstance(allow_probability, bool):
            raise ValueError(f"assessment {index} allow_probability must be boolean")
        if not allow_probability:
            abstentions += 1
        raw_reasons = assessment.get("reasons", [])
        if not isinstance(raw_reasons, list) or not all(
            isinstance(reason, str) for reason in raw_reasons
        ):
            raise ValueError(f"assessment {index} reasons must be a list of strings")
        reason_codes = {_REASON_CODES.get(reason, "other") for reason in raw_reasons}
        reasons.update(reason_codes)
    assessed = len(assessments)
    total_inputs = assessed + schema_rejection_count
    return {
        "assessed": assessed,
        "schema_rejections": schema_rejection_count,
        "total_inputs": total_inputs,
        "schema_rejection_rate": float(schema_rejection_count / total_inputs),
        "abstentions": abstentions,
        "abstention_rate": float(abstentions / assessed),
        "reason_rates": {
            reason: float(count / assessed) for reason, count in sorted(reasons.items())
        },
    }


def build_monitoring_report(
    reference_assessments: Sequence[Mapping[str, Any]],
    current_assessments: Sequence[Mapping[str, Any]],
    *,
    reference_probabilities: Sequence[float | None] | np.ndarray | None = None,
    current_probabilities: Sequence[float | None] | np.ndarray | None = None,
    reference_schema_rejections: int = 0,
    current_schema_rejections: int = 0,
    psi_alert_threshold: float = 0.20,
    abstention_delta_threshold: float = 0.10,
) -> dict[str, Any]:
    """Build an aggregate-only drift and abstention report without outcomes."""
    if not reference_assessments or not current_assessments:
        raise ValueError("reference and current assessments must be non-empty")
    if psi_alert_threshold <= 0.0 or abstention_delta_threshold <= 0.0:
        raise ValueError("monitoring alert thresholds must be positive")
    if (reference_probabilities is None) != (current_probabilities is None):
        raise ValueError("reference and current probabilities must be supplied together")

    reference = _cohort_summary(reference_assessments, reference_schema_rejections)
    current = _cohort_summary(current_assessments, current_schema_rejections)
    reference_signals = _assessment_signals(reference_assessments)
    current_signals = _assessment_signals(current_assessments)
    reference_probability_signal = _probability_signal(
        reference_probabilities,
        expected_length=len(reference_assessments),
        name="reference",
    )
    current_probability_signal = _probability_signal(
        current_probabilities,
        expected_length=len(current_assessments),
        name="current",
    )
    if reference_probabilities is not None and current_probabilities is not None:
        assert reference_probability_signal is not None
        assert current_probability_signal is not None
        reference_signals["probability"] = reference_probability_signal
        current_signals["probability"] = current_probability_signal

    alerts: list[str] = []
    signal_report: dict[str, Any] = {}
    for name in sorted(reference_signals):
        reference_values = reference_signals[name]
        current_values = current_signals[name]
        reference_availability_rate = len(reference_values) / len(reference_assessments)
        current_availability_rate = len(current_values) / len(current_assessments)
        availability_rate_delta = current_availability_rate - reference_availability_rate
        availability_alert = abs(availability_rate_delta) >= abstention_delta_threshold
        psi: float | None = None
        psi_alert = False
        if reference_values and current_values:
            status = "comparable"
            psi = population_stability_index(reference_values, current_values)
            psi_alert = psi >= psi_alert_threshold
        elif reference_values or current_values:
            status = "not_comparable"
        else:
            status = "unavailable_both"
        signal_alert = psi_alert or availability_alert
        signal_report[name] = {
            "psi": psi,
            "status": status,
            "alert": signal_alert,
            "reference_available": len(reference_values),
            "current_available": len(current_values),
            "reference_availability_rate": float(reference_availability_rate),
            "current_availability_rate": float(current_availability_rate),
            "availability_rate_delta": float(availability_rate_delta),
            "reference": (_distribution_summary(reference_values) if reference_values else None),
            "current": _distribution_summary(current_values) if current_values else None,
        }
        if psi_alert:
            alerts.append(f"psi:{name}")
        if availability_alert:
            alerts.append(f"availability:{name}")

    abstention_rate_delta = float(current["abstention_rate"] - reference["abstention_rate"])
    schema_rejection_rate_delta = float(
        current["schema_rejection_rate"] - reference["schema_rejection_rate"]
    )
    if abs(abstention_rate_delta) >= abstention_delta_threshold:
        alerts.append("abstention_rate_delta")
    if abs(schema_rejection_rate_delta) >= abstention_delta_threshold:
        alerts.append("schema_rejection_rate_delta")

    return {
        "schema_version": 1,
        "monitoring_scope": "outcome_free_input_and_abstention_drift",
        "reference": reference,
        "current": current,
        "abstention_rate_delta": abstention_rate_delta,
        "schema_rejection_rate_delta": schema_rejection_rate_delta,
        "signals": signal_report,
        "thresholds": {
            "psi_alert": float(psi_alert_threshold),
            "absolute_rate_delta_alert": float(abstention_delta_threshold),
        },
        "alert": bool(alerts),
        "alerts": alerts,
        "limitations": [
            "PSI and rate shifts do not measure discrimination, calibration, or clinical harm.",
            (
                "Delayed outcomes and an approved evaluation protocol are required for "
                "performance monitoring."
            ),
            (
                "Alerts require investigation; they must not trigger automatic retraining "
                "or threshold changes."
            ),
        ],
    }
