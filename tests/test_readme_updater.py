from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _module():
    path = Path("scripts/update_readme_results.py")
    spec = importlib.util.spec_from_file_location("readme_updater", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_updater_rejects_smoke_results(tmp_path) -> None:
    updater = _module()
    readme = tmp_path / "README.md"
    readme.write_text("x\n<!-- RESULTS_START -->old<!-- RESULTS_END -->\ny", encoding="utf-8")
    with pytest.raises(ValueError, match="refuses"):
        updater.update_readme(readme, {"evaluation_status": "smoke_test"})


def test_updater_accepts_only_complete_final_payload(tmp_path) -> None:
    updater = _module()
    readme = tmp_path / "README.md"
    readme.write_text("x\n<!-- RESULTS_START -->old<!-- RESULTS_END -->\ny", encoding="utf-8")
    intervals = {
        name: {"estimate": 0.5, "lower": 0.4, "upper": 0.6}
        for name in ("auprc", "auroc", "brier", "ece")
    }
    payload = {
        "evaluation_status": "final",
        "dataset": "PhysioNet Challenge 2012 Set B",
        "freeze_status": "frozen",
        "set_b_final_evaluation_successes": 1,
        "bootstrap": {"samples": 2000, "method": "stratified percentile"},
        "model_family": "lightgbm",
        "metrics": {
            "auprc": 0.5,
            "auroc": 0.8,
            "brier": 0.1,
            "ece": 0.03,
            "sensitivity": 0.6,
            "specificity": 0.9,
            "threshold": 0.2,
        },
        "confidence_intervals": intervals,
    }
    updater.update_readme(readme, payload)
    assert "lightgbm" in readme.read_text(encoding="utf-8")
