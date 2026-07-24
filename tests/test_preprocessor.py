from __future__ import annotations

import pandas as pd

from carerisk48h.models.logistic import fit_logistic


def test_preprocessor_statistics_are_fit_only_on_passed_training_rows() -> None:
    training = pd.DataFrame(
        {
            "static_Age": [20.0, 30.0, None, 40.0],
            "static_ICUType": [1.0, 2.0, 1.0, 2.0],
            "HR__mean": [60.0, 70.0, 80.0, 90.0],
        }
    )
    labels = pd.Series([0, 0, 1, 1])
    pipeline = fit_logistic(training, labels, seed=17)
    numeric_pipeline = pipeline.named_steps["preprocessor"].named_transformers_["numeric"]
    statistics = numeric_pipeline.named_steps["imputer"].statistics_
    assert statistics[0] == 30.0
    assert statistics[1] == 75.0
