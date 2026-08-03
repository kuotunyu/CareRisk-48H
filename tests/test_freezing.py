from __future__ import annotations

import pytest

from carerisk48h.data.downloader import sha256_file
from carerisk48h.freezing import create_freeze_manifest


def _metadata(artifact) -> dict[str, object]:
    artifact_hash = sha256_file(artifact)
    return {
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


def test_freeze_requires_final_refit_scope_and_confirmation(tmp_path) -> None:
    model = tmp_path / "model.bin"
    split = tmp_path / "split.csv"
    data = tmp_path / "manifest.json"
    for path in (model, split, data):
        path.write_text("fixture", encoding="utf-8")
    with pytest.raises(PermissionError, match="confirmation"):
        create_freeze_manifest(
            candidate_metadata=_metadata(model),
            artifact_paths=[model],
            split_manifest_path=split,
            data_manifest_path=data,
            output_path=tmp_path / "freeze.json",
            confirm_freeze=False,
        )
    invalid = _metadata(model)
    invalid["training_scope"] = "Set A train"
    with pytest.raises(ValueError, match=r"train\+validation"):
        create_freeze_manifest(
            candidate_metadata=invalid,
            artifact_paths=[model],
            split_manifest_path=split,
            data_manifest_path=data,
            output_path=tmp_path / "freeze.json",
            confirm_freeze=True,
        )


def test_freeze_hashes_artifacts_without_set_b_access(tmp_path) -> None:
    model = tmp_path / "model.bin"
    split = tmp_path / "split.csv"
    data = tmp_path / "manifest.json"
    for path in (model, split, data):
        path.write_text("fixture", encoding="utf-8")
    manifest = create_freeze_manifest(
        candidate_metadata=_metadata(model),
        artifact_paths=[model],
        split_manifest_path=split,
        data_manifest_path=data,
        output_path=tmp_path / "freeze.json",
        confirm_freeze=True,
    )
    assert manifest["status"] == "frozen"
    assert manifest["set_b_final_evaluation_successes"] == 0


def test_freeze_rejects_incomplete_machine_readable_provenance(tmp_path) -> None:
    model = tmp_path / "model.bin"
    split = tmp_path / "split.csv"
    data = tmp_path / "manifest.json"
    for path in (model, split, data):
        path.write_text("fixture", encoding="utf-8")
    with pytest.raises(ValueError, match="source_git_sha"):
        create_freeze_manifest(
            candidate_metadata={
                "training_scope": "Set A train+validation",
                "calibration_fit_scope": "Set A calibration",
                "target_specificity": 0.90,
            },
            artifact_paths=[model],
            split_manifest_path=split,
            data_manifest_path=data,
            output_path=tmp_path / "freeze.json",
            confirm_freeze=True,
        )
