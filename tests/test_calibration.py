from __future__ import annotations

import joblib
import numpy as np
import pytest

from carerisk48h.calibration import fit_calibration_bundle


@pytest.mark.parametrize("method", ["platt", "isotonic", "temperature"])
def test_calibration_serialization_round_trip(tmp_path, method: str) -> None:
    labels = np.asarray([0] * 60 + [1] * 20, dtype=np.int8)
    probabilities = np.linspace(0.01, 0.99, len(labels))
    scores = (
        np.log(probabilities / (1 - probabilities)) if method == "temperature" else probabilities
    )
    bundle = fit_calibration_bundle(labels, scores, method=method)
    path = tmp_path / "calibrator.joblib"
    joblib.dump(bundle, path)
    loaded = joblib.load(path)
    np.testing.assert_allclose(
        bundle["calibrator"].predict(scores), loaded["calibrator"].predict(scores)
    )
    assert loaded["threshold"] == bundle["threshold"]
    assert loaded["operating_point"]["specificity"] >= 0.90


def test_calibration_rejects_single_class() -> None:
    with pytest.raises(ValueError, match="both outcome classes"):
        fit_calibration_bundle(np.zeros(10), np.linspace(0.1, 0.9, 10), method="platt")
