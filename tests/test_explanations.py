from __future__ import annotations

from carerisk48h.explanations import variable_occlusion_sensitivity
from carerisk48h.synthetic import generate_synthetic_cohort


def test_occlusion_sensitivity_is_noncausal_variable_ranking() -> None:
    stays, _ = generate_synthetic_cohort(120, seed=2026)

    def predictor(stay) -> float:
        return float(stay.mask.sum()) / (48 * 37)

    result = variable_occlusion_sensitivity(predictor, stays[0], limit=5)
    assert len(result) == 5
    assert all(item["absolute_change"] >= 0 for item in result)
