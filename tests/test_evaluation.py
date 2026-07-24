from __future__ import annotations

import numpy as np
import pandas as pd

from carerisk48h.evaluation import stratified_bootstrap_ci, subgroup_analysis


def test_bootstrap_is_deterministic_and_contains_estimate() -> None:
    labels = np.asarray([0] * 80 + [1] * 20)
    probabilities = np.linspace(0.01, 0.99, 100)
    first = stratified_bootstrap_ci(labels, probabilities, threshold=0.7, samples=50, seed=7)
    second = stratified_bootstrap_ci(labels, probabilities, threshold=0.7, samples=50, seed=7)
    assert first == second
    assert first["auprc"]["lower"] <= first["auprc"]["estimate"] <= first["auprc"]["upper"]


def test_subgroup_marks_small_class_counts_unstable() -> None:
    labels = np.asarray([0] * 80 + [1] * 20)
    probabilities = np.linspace(0.01, 0.99, 100)
    metadata = pd.DataFrame(
        {
            "Gender": [0] * 50 + [1] * 50,
            "ICUType": [1, 2, 3, 4] * 25,
            "Age": [40, 55, 70, 85] * 25,
        }
    )
    report = subgroup_analysis(
        labels,
        probabilities,
        metadata,
        threshold=0.7,
        bootstrap_samples=10,
        seed=2026,
    )
    assert report
    assert all("interpretation" in item for item in report)
    assert any(item["unstable"] for item in report)
