from __future__ import annotations

import numpy as np
import pandas as pd

from carerisk48h.data.quality import generate_quality_report, robust_outlier_table
from carerisk48h.synthetic import generate_synthetic_cohort


def test_quality_report_writes_split_and_train_only_thresholds(tmp_path) -> None:
    stays, outcomes = generate_synthetic_cohort(160, seed=2026)
    summary = generate_quality_report(
        stays,
        outcomes,
        report_dir=tmp_path / "reports",
        processed_dir=tmp_path / "processed",
        split_seed=2026,
    )
    split = pd.read_csv(tmp_path / "processed" / "set_a_split.csv")
    assert summary["n_stays"] == 160
    assert split["RecordID"].is_unique
    assert set(split["split"]) == {"train", "validation", "calibration"}
    assert (tmp_path / "reports" / "missingness_heatmap.png").is_file()
    assert (tmp_path / "processed" / "quality_thresholds.json").is_file()


def test_robust_outlier_report_does_not_mutate_stays() -> None:
    stays, _ = generate_synthetic_cohort(120, seed=2026)
    original = stays[0].values.copy()
    table = robust_outlier_table(stays)
    assert len(table) == 37
    assert table["variable"].is_unique
    np.testing.assert_equal(stays[0].values, original)
