from __future__ import annotations

import pytest

from carerisk48h.freezing import create_freeze_manifest


def _metadata() -> dict[str, object]:
    return {
        "training_scope": "Set A train+validation",
        "calibration_fit_scope": "Set A calibration",
        "target_specificity": 0.90,
    }


def test_freeze_requires_final_refit_scope_and_confirmation(tmp_path) -> None:
    model = tmp_path / "model.bin"
    split = tmp_path / "split.csv"
    data = tmp_path / "manifest.json"
    for path in (model, split, data):
        path.write_text("fixture", encoding="utf-8")
    with pytest.raises(PermissionError, match="confirmation"):
        create_freeze_manifest(
            candidate_metadata=_metadata(),
            artifact_paths=[model],
            split_manifest_path=split,
            data_manifest_path=data,
            output_path=tmp_path / "freeze.json",
            confirm_freeze=False,
        )
    invalid = _metadata()
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
        candidate_metadata=_metadata(),
        artifact_paths=[model],
        split_manifest_path=split,
        data_manifest_path=data,
        output_path=tmp_path / "freeze.json",
        confirm_freeze=True,
    )
    assert manifest["status"] == "frozen"
    assert manifest["set_b_final_evaluation_successes"] == 0
