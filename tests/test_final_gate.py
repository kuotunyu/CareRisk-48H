from __future__ import annotations

import json

import pytest

from carerisk48h.data.downloader import sha256_file
from carerisk48h.final_gate import load_set_b_outcomes_once
from carerisk48h.freezing import create_freeze_manifest


def _write_outcomes(path) -> None:
    path.write_text("RecordID,In-hospital_death\n1,0\n2,1\n", encoding="utf-8")


def _write_valid_freeze(tmp_path):
    model = tmp_path / "model.bin"
    split = tmp_path / "split.csv"
    data = tmp_path / "manifest.json"
    for path in (model, split, data):
        path.write_text("fixture", encoding="utf-8")
    artifact_hash = sha256_file(model)
    metadata = {
        "source_git_sha": "a" * 40,
        "source_git_dirty": False,
        "config_hash": "b" * 64,
        "model_family": "lightgbm",
        "model_seeds": [17, 42, 2026],
        "training_scope": "Set A train+validation",
        "calibration_fit_scope": "Set A calibration",
        "calibrator": {"method": "platt"},
        "threshold": 0.2,
        "target_specificity": 0.90,
        "environment": {"python": "3.12"},
        "environment_lock_sha256": artifact_hash,
        "set_a_dry_run": {
            "status": "passed",
            "set_b_accessed": False,
            "artifact_sha256": artifact_hash,
        },
    }
    freeze = tmp_path / "freeze.json"
    create_freeze_manifest(
        candidate_metadata=metadata,
        artifact_paths=[model],
        split_manifest_path=split,
        data_manifest_path=data,
        output_path=freeze,
        confirm_freeze=True,
    )
    return freeze, model


def test_final_gate_denies_without_confirmation_without_reading(tmp_path) -> None:
    outcome = tmp_path / "Outcomes-b.txt"
    outcome.write_text("not valid outcomes", encoding="utf-8")
    freeze = tmp_path / "freeze.json"
    ledger = tmp_path / "ledger.json"
    with pytest.raises(PermissionError, match="confirmation"):
        load_set_b_outcomes_once(
            outcome,
            freeze_manifest_path=freeze,
            ledger_path=ledger,
            confirm_final=False,
        )
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    assert payload["attempts"][0]["status"] == "denied"


def test_final_gate_allows_only_one_success(tmp_path) -> None:
    outcome = tmp_path / "Outcomes-b.txt"
    _write_outcomes(outcome)
    freeze, _ = _write_valid_freeze(tmp_path)
    ledger = tmp_path / "ledger.json"
    loaded = load_set_b_outcomes_once(
        outcome,
        freeze_manifest_path=freeze,
        ledger_path=ledger,
        confirm_final=True,
    )
    assert len(loaded) == 2
    with pytest.raises(PermissionError, match="already"):
        load_set_b_outcomes_once(
            outcome,
            freeze_manifest_path=freeze,
            ledger_path=ledger,
            confirm_final=True,
        )
    final_lock = ledger.with_suffix(".final-lock.json")
    lock_payload = json.loads(final_lock.read_text(encoding="utf-8"))
    assert lock_payload["status"] == "locked_after_one_success"


def test_final_gate_rejects_tampered_frozen_artifact_before_outcome_read(tmp_path) -> None:
    outcome = tmp_path / "Outcomes-b.txt"
    _write_outcomes(outcome)
    freeze, model = _write_valid_freeze(tmp_path)
    model.write_bytes(b"tampered")
    ledger = tmp_path / "ledger.json"
    with pytest.raises(ValueError, match="artifact hash mismatch"):
        load_set_b_outcomes_once(
            outcome,
            freeze_manifest_path=freeze,
            ledger_path=ledger,
            confirm_final=True,
        )
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    assert payload["attempts"][0]["status"] == "denied"
    assert sha256_file(outcome) not in ledger.read_text(encoding="utf-8")
