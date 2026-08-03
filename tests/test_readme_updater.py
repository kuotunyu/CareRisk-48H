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


def _valid_payload() -> dict:
    intervals = {
        name: {"estimate": 0.5, "lower": 0.4, "upper": 0.6}
        for name in ("auprc", "auroc", "brier", "ece")
    }
    return {
        "run_id": "20260804T000000Z-lightgbm-set-b-final",
        "created_at_utc": "2026-08-04T00:00:00+00:00",
        "evaluation_status": "final",
        "dataset": "PhysioNet Challenge 2012 Set B",
        "freeze_status": "frozen",
        "set_b_final_evaluation_successes": 1,
        "bootstrap": {
            "samples": 2000,
            "method": "stratified percentile",
            "seed": 2026,
        },
        "model_family": "lightgbm",
        "model_seeds": [17, 42, 2026],
        "calibrator": {"method": "platt"},
        "candidate_source_git_sha": "a" * 40,
        "evaluation_source_git_sha": "b" * 40,
        "evaluation_source_git_dirty": False,
        "freeze_manifest_sha256": "c" * 64,
        "config_hash": "d" * 64,
        "data_manifest_hash": "e" * 64,
        "split_hash": "f" * 64,
        "set_b_input_manifest_sha256": "0" * 64,
        "set_b_record_ids_sha256": "1" * 64,
        "outcomes_sha256": "2" * 64,
        "environment": {"python": "3.12"},
        "artifact_hashes": {
            "set_b_access_ledger.json": "3" * 64,
            "set_b_access_ledger.final-lock.json": "4" * 64,
        },
        "subgroups": [{"subgroup": "gender", "level": "0"}],
        "metrics": {
            "n": 4000,
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
    payload = _valid_payload()
    updater.update_readme(readme, payload)
    assert "lightgbm" in readme.read_text(encoding="utf-8")


def test_updater_rejects_nonofficial_set_b_cohort_size(tmp_path) -> None:
    updater = _module()
    readme = tmp_path / "README.md"
    readme.write_text("x\n<!-- RESULTS_START -->old<!-- RESULTS_END -->\ny", encoding="utf-8")
    payload = _valid_payload()
    payload["metrics"]["n"] = 80
    with pytest.raises(ValueError, match="4,000"):
        updater.update_readme(readme, payload)


@pytest.mark.parametrize(
    "field",
    [
        "run_id",
        "created_at_utc",
        "model_seeds",
        "candidate_source_git_sha",
        "evaluation_source_git_sha",
        "freeze_manifest_sha256",
        "config_hash",
        "data_manifest_hash",
        "split_hash",
        "set_b_input_manifest_sha256",
        "set_b_record_ids_sha256",
        "outcomes_sha256",
        "environment",
        "artifact_hashes",
        "subgroups",
    ],
)
def test_updater_rejects_missing_final_provenance(tmp_path, field) -> None:
    updater = _module()
    readme = tmp_path / "README.md"
    readme.write_text("x\n<!-- RESULTS_START -->old<!-- RESULTS_END -->\ny", encoding="utf-8")
    payload = _valid_payload()
    payload.pop(field)
    with pytest.raises(ValueError, match="provenance"):
        updater.update_readme(readme, payload)
