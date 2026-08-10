"""Set A-only apparent calibration and threshold-stability diagnostics."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression

from carerisk48h.metrics import select_threshold_at_specificity


def _validated_binary_inputs(
    labels: np.ndarray, probabilities: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    raw_truth = np.asarray(labels)
    probs = np.asarray(probabilities, dtype=np.float64)
    if raw_truth.ndim != 1 or probs.ndim != 1:
        raise ValueError("labels and probabilities must be one-dimensional")
    if raw_truth.size == 0 or raw_truth.size != probs.size:
        raise ValueError("labels and probabilities must be non-empty and equally sized")
    try:
        numeric_truth = raw_truth.astype(np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError("labels must contain binary numeric values") from exc
    if not np.all(np.isfinite(numeric_truth)) or not np.all(np.isin(numeric_truth, [0.0, 1.0])):
        raise ValueError("labels must contain only 0 and 1")
    truth = numeric_truth.astype(np.int8)
    if set(np.unique(truth)) != {0, 1}:
        raise ValueError("calibration diagnostics require both outcome classes")
    if np.any(~np.isfinite(probs)) or np.any((probs <= 0.0) | (probs >= 1.0)):
        raise ValueError("probabilities must be finite and strictly between 0 and 1")
    return truth, probs


def calibration_intercept_slope(labels: np.ndarray, probabilities: np.ndarray) -> dict[str, float]:
    """Estimate apparent calibration intercept and slope on supplied predictions.

    This is an internal descriptive diagnostic. It is not an external calibration estimate.
    """
    truth, probs = _validated_binary_inputs(labels, probabilities)
    logits = np.log(probs / (1.0 - probs)).reshape(-1, 1)
    model = LogisticRegression(C=1e6, solver="lbfgs", random_state=2026)
    model.fit(logits, truth)
    return {
        "intercept": float(model.intercept_[0]),
        "slope": float(model.coef_[0, 0]),
    }


def _percentile_summary(estimate: float, values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    return {
        "estimate": float(estimate),
        "median": float(np.percentile(array, 50.0)),
        "lower": float(np.percentile(array, 2.5)),
        "upper": float(np.percentile(array, 97.5)),
    }


def bootstrap_calibration_diagnostics(
    labels: np.ndarray,
    probabilities: np.ndarray,
    *,
    target_specificity: float = 0.90,
    samples: int = 2_000,
    seed: int = 2026,
) -> dict[str, Any]:
    """Bootstrap apparent calibration and threshold selection on one calibration split."""
    truth, probs = _validated_binary_inputs(labels, probabilities)
    if samples < 1:
        raise ValueError("bootstrap samples must be positive")
    if not 0.0 < target_specificity <= 1.0:
        raise ValueError("target_specificity must be in (0, 1]")

    point_calibration = calibration_intercept_slope(truth, probs)
    point_threshold, point_sensitivity, point_specificity = select_threshold_at_specificity(
        truth,
        probs,
        target_specificity=target_specificity,
    )
    positive = np.flatnonzero(truth == 1)
    negative = np.flatnonzero(truth == 0)
    generator = np.random.default_rng(seed)
    distributions: dict[str, list[float]] = {
        "calibration_intercept": [],
        "calibration_slope": [],
        "threshold": [],
        "sensitivity": [],
        "specificity": [],
    }
    for _ in range(samples):
        indices = np.concatenate(
            [
                generator.choice(negative, size=len(negative), replace=True),
                generator.choice(positive, size=len(positive), replace=True),
            ]
        )
        replicate_calibration = calibration_intercept_slope(truth[indices], probs[indices])
        threshold, sensitivity, specificity = select_threshold_at_specificity(
            truth[indices],
            probs[indices],
            target_specificity=target_specificity,
        )
        distributions["calibration_intercept"].append(replicate_calibration["intercept"])
        distributions["calibration_slope"].append(replicate_calibration["slope"])
        distributions["threshold"].append(threshold)
        distributions["sensitivity"].append(sensitivity)
        distributions["specificity"].append(specificity)

    return {
        "schema_version": 1,
        "scope": "apparent_internal_set_a_calibration",
        "target_specificity": float(target_specificity),
        "calibration_intercept": _percentile_summary(
            point_calibration["intercept"], distributions["calibration_intercept"]
        ),
        "calibration_slope": _percentile_summary(
            point_calibration["slope"], distributions["calibration_slope"]
        ),
        "threshold": _percentile_summary(point_threshold, distributions["threshold"]),
        "sensitivity": _percentile_summary(point_sensitivity, distributions["sensitivity"]),
        "specificity": _percentile_summary(point_specificity, distributions["specificity"]),
        "bootstrap": {
            "method": "outcome_stratified_percentile",
            "samples": int(samples),
            "seed": int(seed),
        },
        "interpretation": (
            "Apparent internal Set A calibration-split stability only; not external or "
            "prospective calibration evidence."
        ),
    }
