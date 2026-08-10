from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import joblib
import numpy as np
import pytest

from carerisk48h.calibration import fit_calibration_bundle
from carerisk48h.calibration_diagnostics import (
    bootstrap_calibration_diagnostics,
    calibration_intercept_slope,
)

ROOT = Path(__file__).resolve().parents[1]


def _diagnostic_cli_module():
    path = ROOT / "scripts" / "analyze_calibration_stability.py"
    spec = importlib.util.spec_from_file_location("analyze_calibration_stability", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _well_calibrated_fixture() -> tuple[np.ndarray, np.ndarray]:
    labels = np.asarray([0] * 90 + [1] * 10 + [0] * 20 + [1] * 80, dtype=np.int8)
    probabilities = np.asarray([0.1] * 100 + [0.8] * 100, dtype=np.float64)
    return labels, probabilities


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


def test_calibration_intercept_and_slope_match_hand_built_fixture() -> None:
    labels, probabilities = _well_calibrated_fixture()

    result = calibration_intercept_slope(labels, probabilities)

    assert result["intercept"] == pytest.approx(0.0, abs=0.02)
    assert result["slope"] == pytest.approx(1.0, abs=0.02)


@pytest.mark.parametrize(
    "probabilities",
    [
        np.asarray([0.0, 0.2, 0.8, 0.9]),
        np.asarray([0.1, 0.2, 0.8, 1.0]),
        np.asarray([0.1, 0.2, np.nan, 0.9]),
    ],
)
def test_calibration_diagnostics_reject_invalid_probabilities(
    probabilities: np.ndarray,
) -> None:
    with pytest.raises(ValueError, match="strictly between 0 and 1"):
        calibration_intercept_slope(np.asarray([0, 0, 1, 1]), probabilities)


def test_calibration_diagnostics_reject_single_class() -> None:
    with pytest.raises(ValueError, match="both outcome classes"):
        calibration_intercept_slope(np.zeros(10), np.linspace(0.1, 0.9, 10))


def test_calibration_bootstrap_is_deterministic_and_ordered() -> None:
    labels, probabilities = _well_calibrated_fixture()

    first = bootstrap_calibration_diagnostics(
        labels,
        probabilities,
        target_specificity=0.90,
        samples=40,
        seed=17,
    )
    second = bootstrap_calibration_diagnostics(
        labels,
        probabilities,
        target_specificity=0.90,
        samples=40,
        seed=17,
    )

    assert first == second
    assert first["bootstrap"] == {
        "method": "outcome_stratified_percentile",
        "samples": 40,
        "seed": 17,
    }
    for name in ("calibration_intercept", "calibration_slope", "threshold"):
        summary = first[name]
        assert summary["lower"] <= summary["median"] <= summary["upper"]


def test_calibration_diagnostic_cli_is_set_a_only_and_aggregate(tmp_path: Path) -> None:
    module = _diagnostic_cli_module()
    labels, probabilities = _well_calibrated_fixture()
    predictions = tmp_path / "predictions.npz"
    output = tmp_path / "diagnostics.json"
    np.savez(predictions, labels=labels, probabilities=probabilities)

    with pytest.raises(SystemExit):
        module.main(
            [
                "--predictions",
                str(predictions),
                "--dataset-role",
                "set_b",
                "--output",
                str(output),
            ]
        )

    module.main(
        [
            "--predictions",
            str(predictions),
            "--dataset-role",
            "set_a_calibration",
            "--output",
            str(output),
            "--bootstrap-samples",
            "20",
        ]
    )
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["evaluation_status"] == "set_a_calibration_diagnostic"
    assert payload["scope"] == "apparent_internal_set_a_calibration"
    assert payload["diagnostics"]["bootstrap"]["samples"] == 20
    assert "record" not in json.dumps(payload, sort_keys=True).lower()
