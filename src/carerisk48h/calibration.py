"""Validation/calibration-only probability calibration and threshold locking."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import joblib
import numpy as np
from scipy.optimize import minimize_scalar
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from carerisk48h.artifacts import write_json_atomic
from carerisk48h.metrics import (
    compute_binary_metrics,
    select_threshold_at_specificity,
)


def _logit(probabilities: np.ndarray) -> np.ndarray:
    clipped = np.clip(np.asarray(probabilities, dtype=np.float64), 1e-7, 1 - 1e-7)
    return np.log(clipped / (1.0 - clipped))


def _sigmoid(logits: np.ndarray) -> np.ndarray:
    clipped = np.clip(np.asarray(logits, dtype=np.float64), -50, 50)
    return 1.0 / (1.0 + np.exp(-clipped))


class ProbabilityCalibrator(Protocol):
    def fit(self, scores: np.ndarray, labels: np.ndarray) -> ProbabilityCalibrator: ...

    def predict(self, scores: np.ndarray) -> np.ndarray: ...


@dataclass
class PlattCalibrator:
    """Logistic calibration over candidate logits."""

    model: LogisticRegression | None = None

    def fit(self, scores: np.ndarray, labels: np.ndarray) -> PlattCalibrator:
        truth = np.asarray(labels, dtype=np.int8)
        if set(np.unique(truth)) != {0, 1}:
            raise ValueError("calibration requires both outcome classes")
        self.model = LogisticRegression(C=1e6, solver="lbfgs", random_state=2026)
        self.model.fit(_logit(scores).reshape(-1, 1), truth)
        return self

    def predict(self, scores: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("calibrator is not fitted")
        return self.model.predict_proba(_logit(scores).reshape(-1, 1))[:, 1]


@dataclass
class IsotonicCalibrator:
    """Monotone non-parametric calibrator for explicitly selected use cases."""

    model: IsotonicRegression | None = None

    def fit(self, scores: np.ndarray, labels: np.ndarray) -> IsotonicCalibrator:
        truth = np.asarray(labels, dtype=np.int8)
        if set(np.unique(truth)) != {0, 1}:
            raise ValueError("calibration requires both outcome classes")
        self.model = IsotonicRegression(out_of_bounds="clip")
        self.model.fit(np.asarray(scores, dtype=np.float64), truth)
        return self

    def predict(self, scores: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("calibrator is not fitted")
        return np.asarray(self.model.predict(scores), dtype=np.float64)


@dataclass
class TemperatureCalibrator:
    """Single temperature fitted to ensemble logits with bounded optimization."""

    temperature: float | None = None

    def fit(self, scores: np.ndarray, labels: np.ndarray) -> TemperatureCalibrator:
        logits = np.asarray(scores, dtype=np.float64)
        truth = np.asarray(labels, dtype=np.float64)
        if set(np.unique(truth)) != {0.0, 1.0}:
            raise ValueError("calibration requires both outcome classes")

        def negative_log_likelihood(log_temperature: float) -> float:
            probabilities = _sigmoid(logits / math_exp(log_temperature))
            probabilities = np.clip(probabilities, 1e-12, 1 - 1e-12)
            return float(
                -np.mean(
                    truth * np.log(probabilities) + (1.0 - truth) * np.log(1.0 - probabilities)
                )
            )

        result = minimize_scalar(negative_log_likelihood, bounds=(-4.0, 4.0), method="bounded")
        if not result.success:
            raise RuntimeError("temperature optimization failed")
        self.temperature = math_exp(float(result.x))
        return self

    def predict(self, scores: np.ndarray) -> np.ndarray:
        if self.temperature is None:
            raise RuntimeError("calibrator is not fitted")
        return _sigmoid(np.asarray(scores, dtype=np.float64) / self.temperature)


def math_exp(value: float) -> float:
    """Tiny indirection keeps scipy callback scalar handling explicit."""
    return float(np.exp(value))


def fit_calibration_bundle(
    labels: np.ndarray,
    scores: np.ndarray,
    *,
    method: str,
    target_specificity: float = 0.90,
) -> dict[str, object]:
    """Fit a calibrator and lock an operating threshold on the same calibration split."""
    calibrator: ProbabilityCalibrator
    if method == "platt":
        calibrator = PlattCalibrator()
    elif method == "isotonic":
        calibrator = IsotonicCalibrator()
    elif method == "temperature":
        calibrator = TemperatureCalibrator()
    else:
        raise ValueError("method must be platt, isotonic, or temperature")
    calibrator.fit(scores, labels)
    calibrated = calibrator.predict(scores)
    threshold, sensitivity, specificity = select_threshold_at_specificity(
        labels, calibrated, target_specificity=target_specificity
    )
    return {
        "schema_version": 1,
        "method": method,
        "calibrator": calibrator,
        "threshold": threshold,
        "target_specificity": target_specificity,
        "calibration_metrics": compute_binary_metrics(labels, calibrated, threshold=threshold),
        "operating_point": {
            "sensitivity": sensitivity,
            "specificity": specificity,
        },
    }


def calibration_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--method", choices=["platt", "isotonic", "temperature"], required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    with np.load(args.predictions) as data:
        labels = data["labels"]
        score_key = "logits" if args.method == "temperature" else "probabilities"
        scores = data[score_key]
    bundle = fit_calibration_bundle(labels, scores, method=args.method)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, args.output_dir / "calibrator.joblib")
    serializable = {key: value for key, value in bundle.items() if key != "calibrator"}
    write_json_atomic(args.output_dir / "calibration.json", serializable)
    print(json.dumps(serializable, indent=2))
