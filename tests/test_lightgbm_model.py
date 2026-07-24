from __future__ import annotations

import pandas as pd
import pytest

pytest.importorskip("lightgbm")

from carerisk48h.models.lightgbm_model import fit_lightgbm


def test_lightgbm_pipeline_handles_missing_and_unseen_icu() -> None:
    frame = pd.DataFrame(
        {
            "static_ICUType": [1, 1, 2, 2, 3, 3, 1, 2],
            "HR__mean": [70.0, 80.0, None, 90.0, 65.0, 100.0, 77.0, 95.0],
            "HR__slope": [0.1, 0.2, None, -0.1, 0.0, 0.4, 0.1, -0.2],
        }
    )
    labels = pd.Series([0, 0, 1, 1, 0, 1, 0, 1])
    model = fit_lightgbm(
        frame,
        labels,
        seed=17,
        n_jobs=1,
        parameters={"n_estimators": 5, "num_leaves": 3, "min_child_samples": 2},
    )
    probability = model.predict_proba(
        pd.DataFrame({"static_ICUType": [4], "HR__mean": [85.0], "HR__slope": [None]})
    )[0, 1]
    assert 0 <= probability <= 1
