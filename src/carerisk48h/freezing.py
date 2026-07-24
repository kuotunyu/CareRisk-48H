"""Immutable manifest creation after final refit and calibration are complete."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from carerisk48h.artifacts import write_json_atomic
from carerisk48h.data.downloader import sha256_file


def create_freeze_manifest(
    *,
    candidate_metadata: dict[str, Any],
    artifact_paths: list[str | Path],
    split_manifest_path: str | Path,
    data_manifest_path: str | Path,
    output_path: str | Path,
    confirm_freeze: bool,
) -> dict[str, Any]:
    """Hash a train+validation-refitted, calibration-locked artifact bundle."""
    if not confirm_freeze:
        raise PermissionError("explicit freeze confirmation is required")
    if candidate_metadata.get("training_scope") != "Set A train+validation":
        raise ValueError("candidate must be refit on Set A train+validation before freezing")
    if candidate_metadata.get("calibration_fit_scope") != "Set A calibration":
        raise ValueError("calibrator and threshold must be fit only on Set A calibration")
    if float(candidate_metadata.get("target_specificity", 0.0)) < 0.90:
        raise ValueError("frozen operating point must target at least 90% specificity")
    paths = [Path(path) for path in artifact_paths]
    if not paths or any(not path.is_file() for path in paths):
        raise FileNotFoundError("all frozen artifacts must exist")
    split_path = Path(split_manifest_path)
    data_path = Path(data_manifest_path)
    if not split_path.is_file() or not data_path.is_file():
        raise FileNotFoundError("split and data manifests are required")
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "status": "frozen",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate": candidate_metadata,
        "artifact_hashes": {str(path): sha256_file(path) for path in paths},
        "split_manifest_sha256": sha256_file(split_path),
        "data_manifest_sha256": sha256_file(data_path),
        "set_b_final_evaluation_successes": 0,
        "notes": [
            "Any artifact change invalidates this manifest.",
            "This freeze authorizes the gated final workflow but does not itself access Set B.",
        ],
    }
    write_json_atomic(output_path, manifest)
    return manifest
