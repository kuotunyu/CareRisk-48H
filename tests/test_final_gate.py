from __future__ import annotations

import json

import pytest

from carerisk48h.final_gate import load_set_b_outcomes_once


def _write_outcomes(path) -> None:
    path.write_text("RecordID,In-hospital_death\n1,0\n2,1\n", encoding="utf-8")


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
    freeze = tmp_path / "freeze.json"
    freeze.write_text(
        json.dumps({"status": "frozen", "artifact_hashes": {"model": "abc"}}),
        encoding="utf-8",
    )
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
