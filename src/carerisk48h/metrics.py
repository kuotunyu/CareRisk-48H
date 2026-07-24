"""Imbalance-aware discrimination, calibration, and operating-point metrics."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    roc_auc_score,
)


def expected_calibration_error(
    y_true: np.ndarray, probabilities: np.ndarray, *, n_bins: int = 10
) -> float:
    """Compute fixed-width ECE with empty bins omitted."""
    truth = np.asarray(y_true, dtype=np.int8)
    probs = np.asarray(probabilities, dtype=np.float64)
    if truth.size == 0 or truth.size != probs.size:
        raise ValueError("y_true and probabilities must be non-empty and equally sized")
    if np.any((probs < 0) | (probs > 1) | ~np.isfinite(probs)):
        raise ValueError("probabilities must be finite values in [0, 1]")
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    indices = np.minimum(np.digitize(probs, edges[1:-1], right=False), n_bins - 1)
    ece = 0.0
    for bin_index in range(n_bins):
        selected = indices == bin_index
        if not np.any(selected):
            continue
        ece += float(selected.mean()) * abs(float(probs[selected].mean() - truth[selected].mean()))
    return float(ece)


def select_threshold_at_specificity(
    y_true: np.ndarray, probabilities: np.ndarray, *, target_specificity: float = 0.90
) -> tuple[float, float, float]:
    """Maximize sensitivity among thresholds meeting the specificity target."""
    truth = np.asarray(y_true, dtype=np.int8)
    probs = np.asarray(probabilities, dtype=np.float64)
    if not 0 < target_specificity <= 1:
        raise ValueError("target_specificity must be in (0, 1]")
    if set(np.unique(truth)) != {0, 1}:
        raise ValueError("threshold selection requires both outcome classes")
    candidates = np.unique(np.append(probs, np.nextafter(float(np.max(probs)), float("inf"))))
    eligible: list[tuple[float, float, float]] = []
    for threshold in candidates:
        prediction = probs >= threshold
        tn, fp, fn, tp = confusion_matrix(truth, prediction, labels=[0, 1]).ravel()
        specificity = tn / (tn + fp)
        sensitivity = tp / (tp + fn)
        if specificity + 1e-12 >= target_specificity:
            eligible.append((float(sensitivity), float(threshold), float(specificity)))
    sensitivity, threshold, specificity = max(eligible, key=lambda item: (item[0], item[1]))
    return threshold, sensitivity, specificity


def compute_binary_metrics(
    y_true: np.ndarray, probabilities: np.ndarray, *, threshold: float = 0.5
) -> dict[str, Any]:
    """Compute required mortality-risk metrics with explicit undefined values."""
    truth = np.asarray(y_true, dtype=np.int8)
    probs = np.asarray(probabilities, dtype=np.float64)
    if truth.size == 0 or truth.size != probs.size:
        raise ValueError("y_true and probabilities must be non-empty and equally sized")
    prediction = probs >= threshold
    tn, fp, fn, tp = confusion_matrix(truth, prediction, labels=[0, 1]).ravel()
    sensitivity = tp / (tp + fn) if tp + fn else None
    specificity = tn / (tn + fp) if tn + fp else None
    ppv = tp / (tp + fp) if tp + fp else None
    npv = tn / (tn + fn) if tn + fn else None
    both_classes = len(np.unique(truth)) == 2
    return {
        "n": int(truth.size),
        "events": int(truth.sum()),
        "prevalence": float(truth.mean()),
        "auprc": float(average_precision_score(truth, probs)) if both_classes else None,
        "auroc": float(roc_auc_score(truth, probs)) if both_classes else None,
        "brier": float(brier_score_loss(truth, probs)),
        "ece": expected_calibration_error(truth, probs),
        "threshold": float(threshold),
        "sensitivity": None if sensitivity is None else float(sensitivity),
        "specificity": None if specificity is None else float(specificity),
        "ppv": None if ppv is None else float(ppv),
        "npv": None if npv is None else float(npv),
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }
