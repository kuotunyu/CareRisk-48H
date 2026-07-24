from __future__ import annotations

import pandas as pd
import pytest

from carerisk48h.features.tabular import assert_no_forbidden_features


@pytest.mark.parametrize(
    "column", ["SAPS-I", "SOFA", "Length_of_stay", "Survival", "In-hospital_death", "label"]
)
def test_outcome_related_columns_are_blocked(column: str) -> None:
    with pytest.raises(ValueError, match="forbidden"):
        assert_no_forbidden_features(pd.DataFrame({column: [1.0]}))


def test_safe_feature_columns_are_allowed() -> None:
    assert_no_forbidden_features(pd.DataFrame({"HR__mean": [80.0], "static_Age": [65.0]}))
