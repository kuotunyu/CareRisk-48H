"""Audited, one-success-only access gate for public Outcomes-b."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from carerisk48h.artifacts import write_json_atomic
from carerisk48h.data.downloader import sha256_file
from carerisk48h.data.parser import load_outcomes


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "attempts": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload.get("attempts"), list):
        raise ValueError("invalid Set B audit ledger")
    return payload


def load_set_b_outcomes_once(
    outcomes_path: str | Path,
    *,
    freeze_manifest_path: str | Path,
    ledger_path: str | Path,
    confirm_final: bool,
) -> pd.DataFrame:
    """Read Outcomes-b at most once successfully, with an append-only audit trail."""
    outcome_file = Path(outcomes_path)
    freeze_file = Path(freeze_manifest_path)
    ledger_file = Path(ledger_path)
    ledger_file.parent.mkdir(parents=True, exist_ok=True)
    lock_path = ledger_file.with_suffix(ledger_file.suffix + ".lock")
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(descriptor)
    except FileExistsError as exc:
        raise RuntimeError("another final-evaluation access is in progress") from exc
    try:
        ledger = _load_ledger(ledger_file)
        if any(item.get("status") == "success" for item in ledger["attempts"]):
            raise PermissionError("Set B outcomes have already been accessed successfully")
        attempt: dict[str, Any] = {
            "attempted_at_utc": _utc_now(),
            "status": "denied",
            "outcomes_filename": outcome_file.name,
            "freeze_manifest": str(freeze_file),
        }
        ledger["attempts"].append(attempt)
        if not confirm_final:
            attempt["reason"] = "explicit final confirmation missing"
            write_json_atomic(ledger_file, ledger)
            raise PermissionError("explicit final Set B confirmation is required")
        if outcome_file.name.lower() != "outcomes-b.txt":
            attempt["reason"] = "unexpected outcome filename"
            write_json_atomic(ledger_file, ledger)
            raise ValueError("final gate accepts only Outcomes-b.txt")
        if not freeze_file.is_file():
            attempt["reason"] = "freeze manifest missing"
            write_json_atomic(ledger_file, ledger)
            raise FileNotFoundError("freeze manifest is required before Set B access")
        freeze = json.loads(freeze_file.read_text(encoding="utf-8"))
        if freeze.get("status") != "frozen" or not freeze.get("artifact_hashes"):
            attempt["reason"] = "freeze manifest is incomplete"
            write_json_atomic(ledger_file, ledger)
            raise PermissionError("a complete frozen manifest is required")
        try:
            outcomes = load_outcomes(outcome_file)
        except Exception as exc:
            attempt["status"] = "failed"
            attempt["reason"] = f"outcome validation failed: {type(exc).__name__}"
            write_json_atomic(ledger_file, ledger)
            raise
        attempt.update(
            {
                "status": "success",
                "completed_at_utc": _utc_now(),
                "rows": len(outcomes),
                "outcomes_sha256": sha256_file(outcome_file),
                "freeze_manifest_sha256": sha256_file(freeze_file),
            }
        )
        write_json_atomic(ledger_file, ledger)
        return outcomes
    finally:
        lock_path.unlink(missing_ok=True)
