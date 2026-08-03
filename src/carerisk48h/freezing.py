"""Immutable manifest creation after final refit and calibration are complete."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from carerisk48h.artifacts import write_json_atomic
from carerisk48h.constants import MODEL_SEEDS
from carerisk48h.data.downloader import sha256_file

_MODEL_FAMILIES = {"logistic", "lightgbm", "grud", "tcn"}


def _require_hash(value: Any, *, field: str, length: int = 64) -> str:
    normalized = str(value)
    if len(normalized) != length or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError(f"{field} must be a lowercase {length * 4}-bit hash")
    return normalized


def _validate_candidate_metadata(
    candidate: dict[str, Any], *, artifact_hashes: dict[str, str]
) -> None:
    _require_hash(candidate.get("source_git_sha"), field="source_git_sha", length=40)
    if candidate.get("source_git_dirty") is not False:
        raise ValueError("source_git_dirty must be false before freezing")
    _require_hash(candidate.get("config_hash"), field="config_hash")
    family = str(candidate.get("model_family"))
    if family not in _MODEL_FAMILIES:
        raise ValueError("model_family is missing or unsupported")
    if candidate.get("model_seeds") != list(MODEL_SEEDS):
        raise ValueError(f"model_seeds must equal {list(MODEL_SEEDS)}")
    if candidate.get("training_scope") != "Set A train+validation":
        raise ValueError("candidate must be refit on Set A train+validation before freezing")
    if candidate.get("calibration_fit_scope") != "Set A calibration":
        raise ValueError("calibrator and threshold must be fit only on Set A calibration")
    threshold = float(candidate.get("threshold", -1.0))
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between zero and one")
    if float(candidate.get("target_specificity", 0.0)) < 0.90:
        raise ValueError("frozen operating point must target at least 90% specificity")
    calibrator = candidate.get("calibrator")
    method = calibrator.get("method") if isinstance(calibrator, dict) else None
    expected_method = "temperature" if family in {"grud", "tcn"} else "platt"
    if method != expected_method:
        raise ValueError(f"{family} requires the pre-registered {expected_method} calibrator")
    if not isinstance(candidate.get("environment"), dict) or not candidate["environment"]:
        raise ValueError("environment metadata is required")
    environment_hash = _require_hash(
        candidate.get("environment_lock_sha256"), field="environment_lock_sha256"
    )
    dry_run = candidate.get("set_a_dry_run")
    if not isinstance(dry_run, dict):
        raise ValueError("set_a_dry_run evidence is required")
    if dry_run.get("status") != "passed" or dry_run.get("set_b_accessed") is not False:
        raise ValueError("Set A simulated evaluation must pass without Set B access")
    dry_run_hash = _require_hash(dry_run.get("artifact_sha256"), field="set_a_dry_run hash")
    hash_values = set(artifact_hashes.values())
    if environment_hash not in hash_values or dry_run_hash not in hash_values:
        raise ValueError("environment lock and Set A dry-run evidence must be frozen artifacts")


def validate_freeze_manifest(
    manifest: dict[str, Any], *, manifest_path: str | Path, verify_artifacts: bool
) -> None:
    """Validate a schema-v2 freeze and optionally re-hash every frozen artifact."""
    if manifest.get("schema_version") != 2 or manifest.get("status") != "frozen":
        raise ValueError("freeze manifest is not a complete schema-v2 freeze")
    if manifest.get("set_b_final_evaluation_successes") != 0:
        raise ValueError("freeze manifest must record zero Set B successes")
    artifacts = manifest.get("artifact_hashes")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError("freeze manifest artifact hashes are missing")
    candidate = manifest.get("candidate")
    if not isinstance(candidate, dict):
        raise ValueError("freeze manifest candidate metadata is missing")
    _validate_candidate_metadata(candidate, artifact_hashes=artifacts)
    if not verify_artifacts:
        return
    root = Path(manifest_path).resolve().parent
    for relative, expected_hash in artifacts.items():
        relative_path = Path(str(relative))
        if relative_path.is_absolute():
            raise ValueError("frozen artifact paths must be manifest-relative")
        path = (root / relative_path).resolve()
        if root not in path.parents:
            raise ValueError("frozen artifact path escapes the manifest directory")
        if not path.is_file() or sha256_file(path) != expected_hash:
            raise ValueError(f"artifact hash mismatch: {relative}")


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
    paths = [Path(path) for path in artifact_paths]
    if not paths or any(not path.is_file() for path in paths):
        raise FileNotFoundError("all frozen artifacts must exist")
    split_path = Path(split_manifest_path)
    data_path = Path(data_manifest_path)
    if not split_path.is_file() or not data_path.is_file():
        raise FileNotFoundError("split and data manifests are required")
    output = Path(output_path).resolve()
    root = output.parent
    artifact_hashes: dict[str, str] = {}
    for path in paths:
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(root).as_posix()
        except ValueError as exc:
            raise ValueError("all frozen artifacts must be inside the manifest directory") from exc
        if relative in artifact_hashes:
            raise ValueError("frozen artifact paths must be unique")
        artifact_hashes[relative] = sha256_file(resolved)
    _validate_candidate_metadata(candidate_metadata, artifact_hashes=artifact_hashes)
    manifest: dict[str, Any] = {
        "schema_version": 2,
        "status": "frozen",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate": candidate_metadata,
        "source_git_sha": candidate_metadata["source_git_sha"],
        "config_hash": candidate_metadata["config_hash"],
        "model_family": candidate_metadata["model_family"],
        "model_seeds": candidate_metadata["model_seeds"],
        "calibrator": candidate_metadata["calibrator"],
        "threshold": candidate_metadata["threshold"],
        "environment": candidate_metadata["environment"],
        "set_a_dry_run": candidate_metadata["set_a_dry_run"],
        "artifact_hashes": artifact_hashes,
        "split_manifest_sha256": sha256_file(split_path),
        "data_manifest_sha256": sha256_file(data_path),
        "set_b_final_evaluation_successes": 0,
        "notes": [
            "Any artifact change invalidates this manifest.",
            "This freeze authorizes the gated final workflow but does not itself access Set B.",
        ],
    }
    write_json_atomic(output, manifest)
    return manifest
