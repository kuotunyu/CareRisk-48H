from __future__ import annotations

import numpy as np
import pytest
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from carerisk48h.metrics import (
    compute_binary_metrics,
    expected_calibration_error,
    select_threshold_at_specificity,
)


def test_metrics_match_sklearn() -> None:
    truth = np.array([0, 0, 1, 1])
    probabilities = np.array([0.1, 0.4, 0.35, 0.8])
    metrics = compute_binary_metrics(truth, probabilities, threshold=0.5)
    assert metrics["auprc"] == pytest.approx(average_precision_score(truth, probabilities))
    assert metrics["auroc"] == pytest.approx(roc_auc_score(truth, probabilities))
    assert metrics["brier"] == pytest.approx(brier_score_loss(truth, probabilities))
    assert metrics["confusion"] == {"tn": 2, "fp": 0, "fn": 1, "tp": 1}


def test_ece_hand_computed() -> None:
    truth = np.array([0, 1])
    probabilities = np.array([0.1, 0.9])
    assert expected_calibration_error(truth, probabilities, n_bins=2) == pytest.approx(0.1)


def test_single_class_has_explicit_undefined_discrimination() -> None:
    metrics = compute_binary_metrics(np.array([0, 0]), np.array([0.1, 0.2]))
    assert metrics["auprc"] is None
    assert metrics["auroc"] is None
    assert metrics["sensitivity"] is None


def test_threshold_meets_specificity_target() -> None:
    truth = np.array([0] * 10 + [1] * 4)
    probabilities = np.array(
        [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.8, 0.5, 0.6, 0.7, 0.9]
    )
    threshold, sensitivity, specificity = select_threshold_at_specificity(truth, probabilities)
    assert threshold == pytest.approx(0.5)
    assert sensitivity == 1.0
    assert specificity == 0.9
