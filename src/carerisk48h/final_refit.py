"""Final train+validation tabular refit with calibration-only locking."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import joblib
import numpy as np
import pandas as pd

from carerisk48h.artifacts import stable_hash, write_json_atomic
from carerisk48h.calibration import ProbabilityCalibrator, fit_calibration_bundle
from carerisk48h.constants import MODEL_SEEDS
from carerisk48h.data.downloader import sha256_file
from carerisk48h.models.lightgbm_model import fit_lightgbm


def _require_hash(value: str, *, field: str, length: int = 64) -> str:
    if len(value) != length or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field} must be a lowercase {length * 4}-bit hash")
    return value


def _validate_dry_run(path: Path, *, output_dir: Path) -> dict[str, Any]:
    resolved = path.resolve()
    root = output_dir.resolve()
    if not resolved.is_file() or root not in resolved.parents:
        raise ValueError("Set A dry-run evidence must be inside the final candidate directory")
    payload = json_load(resolved)
    if payload.get("set_b_accessed") is not False:
        raise ValueError("Set A dry-run must prove that Set B was not accessed")
    if payload.get("evaluation_status") != "set_a_reused_development_dry_run":
        raise ValueError("Set A dry-run evaluation status is invalid")
    return payload


def json_load(path: Path) -> dict[str, Any]:
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return payload


def refit_lightgbm_candidate(
    cohort: pd.DataFrame,
    *,
    feature_columns: list[str],
    parameters: dict[str, Any],
    model_seeds: tuple[int, ...],
    n_jobs: int,
    output_dir: str | Path,
    source_git_sha: str,
    source_git_dirty: bool,
    selection_sha256: str,
    data_manifest_hash: str,
    split_hash: str,
    environment: dict[str, str],
    dry_run_evaluation_path: str | Path,
    target_specificity: float = 0.90,
) -> tuple[Path, dict[str, Any]]:
    """Refit the frozen LightGBM specification and lock calibration artifacts."""
    if tuple(model_seeds) != MODEL_SEEDS:
        raise ValueError(f"model seeds must equal {MODEL_SEEDS}")
    _require_hash(source_git_sha, field="source_git_sha", length=40)
    if source_git_dirty:
        raise ValueError("source must be clean before final refit")
    _require_hash(selection_sha256, field="selection_sha256")
    _require_hash(data_manifest_hash, field="data_manifest_hash")
    _require_hash(split_hash, field="split_hash")
    if not environment:
        raise ValueError("environment metadata is required")
    if target_specificity < 0.90:
        raise ValueError("target specificity must be at least 0.90")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    dry_run_path = Path(dry_run_evaluation_path)
    dry_run = _validate_dry_run(dry_run_path, output_dir=output)

    required = {"RecordID", "label", "split", *feature_columns}
    missing = required - set(cohort.columns)
    if missing:
        raise ValueError(f"final refit cohort is missing columns: {sorted(missing)}")
    if cohort["RecordID"].duplicated().any():
        raise ValueError("final refit cohort RecordID values must be unique")
    if set(cohort["split"]) != {"train", "validation", "calibration"}:
        raise ValueError("final refit requires train, validation, and calibration splits")

    train_rows = cohort["split"] == "train"
    validation_rows = cohort["split"] == "validation"
    refit_rows = train_rows | validation_rows
    calibration_rows = cohort["split"] == "calibration"
    if set(cohort.loc[refit_rows, "label"].astype(int)) != {0, 1}:
        raise ValueError("train+validation refit requires both outcome classes")
    if set(cohort.loc[calibration_rows, "label"].astype(int)) != {0, 1}:
        raise ValueError("calibration requires both outcome classes")

    fit_ids = sorted(cohort.loc[refit_rows, "RecordID"].astype(int).tolist())
    calibration_ids = sorted(cohort.loc[calibration_rows, "RecordID"].astype(int).tolist())
    models_dir = output / "models"
    models_dir.mkdir(parents=True, exist_ok=False)
    models: list[Any] = []
    model_paths: list[Path] = []
    for seed in model_seeds:
        model = fit_lightgbm(
            cohort.loc[refit_rows, feature_columns],
            cohort.loc[refit_rows, "label"],
            seed=seed,
            n_jobs=n_jobs,
            parameters=parameters,
        )
        path = models_dir / f"lightgbm_seed_{seed}.joblib"
        joblib.dump(
            {
                "model_family": "lightgbm",
                "model": model,
                "feature_columns": feature_columns,
                "parameters": parameters,
                "seed": seed,
                "training_scope": "Set A train+validation",
            },
            path,
        )
        models.append(model)
        model_paths.append(path)

    calibration_matrix = cohort.loc[calibration_rows, feature_columns]
    calibration_labels = cohort.loc[calibration_rows, "label"].to_numpy(dtype=np.int8)
    calibration_raw = np.mean(
        np.stack([model.predict_proba(calibration_matrix)[:, 1] for model in models]), axis=0
    )
    calibration_bundle = fit_calibration_bundle(
        calibration_labels,
        calibration_raw,
        method="platt",
        target_specificity=target_specificity,
    )
    calibrator = cast(ProbabilityCalibrator, calibration_bundle["calibrator"])
    calibrated = calibrator.predict(calibration_raw)
    threshold = float(cast(float, calibration_bundle["threshold"]))

    calibrator_path = output / "calibrator.joblib"
    joblib.dump(calibration_bundle, calibrator_path)
    calibration_json = output / "calibration.json"
    write_json_atomic(
        calibration_json,
        {key: value for key, value in calibration_bundle.items() if key != "calibrator"},
    )
    predictions_path = output / "calibration_predictions.npz"
    np.savez_compressed(
        predictions_path,
        record_ids=np.asarray(calibration_ids, dtype=np.int64),
        labels=calibration_labels,
        raw_probabilities=calibration_raw,
        probabilities=calibrated,
    )

    final_bundle_path = output / "final_candidate.joblib"
    joblib.dump(
        {
            "schema_version": 1,
            "model_family": "lightgbm",
            "models": models,
            "model_seeds": list(model_seeds),
            "feature_columns": feature_columns,
            "parameters": parameters,
            "calibrator": calibrator,
            "calibration_method": "platt",
            "threshold": threshold,
            "target_specificity": target_specificity,
            "training_scope": "Set A train+validation",
            "calibration_fit_scope": "Set A calibration",
        },
        final_bundle_path,
    )

    environment_path = output / "environment-lock.json"
    write_json_atomic(environment_path, {"environment": environment})
    config = {
        "model_family": "lightgbm",
        "model_seeds": list(model_seeds),
        "parameters": parameters,
        "training_scope": "Set A train+validation",
        "preprocessor_fit_scope": "Set A train+validation",
        "calibration_fit_scope": "Set A calibration",
        "threshold_fit_scope": "Set A calibration",
        "calibration_method": "platt",
        "target_specificity": target_specificity,
    }
    artifact_paths = [
        *model_paths,
        calibrator_path,
        calibration_json,
        predictions_path,
        final_bundle_path,
        environment_path,
        dry_run_path,
    ]
    artifact_hashes = {
        path.resolve().relative_to(output.resolve()).as_posix(): sha256_file(path)
        for path in artifact_paths
    }
    operating_point = calibration_bundle["operating_point"]
    metadata: dict[str, Any] = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_status": "frozen_candidate_pending_manifest",
        "model_family": "lightgbm",
        "model_seeds": list(model_seeds),
        "parameters": parameters,
        "source_git_sha": source_git_sha,
        "source_git_dirty": False,
        "selection_sha256": selection_sha256,
        "config": config,
        "config_hash": stable_hash(config),
        "data_manifest_hash": data_manifest_hash,
        "split_hash": split_hash,
        "training_scope": "Set A train+validation",
        "preprocessor_fit_scope": "Set A train+validation",
        "calibration_fit_scope": "Set A calibration",
        "threshold_fit_scope": "Set A calibration",
        "fit_counts": {
            "train": int(train_rows.sum()),
            "validation": int(validation_rows.sum()),
            "calibration": int(calibration_rows.sum()),
        },
        "fit_record_ids_sha256": stable_hash(fit_ids),
        "calibration_record_ids_sha256": stable_hash(calibration_ids),
        "calibrator": {"method": "platt"},
        "threshold": threshold,
        "target_specificity": target_specificity,
        "calibration_metrics": calibration_bundle["calibration_metrics"],
        "calibration_operating_point": operating_point,
        "environment": environment,
        "environment_lock_sha256": sha256_file(environment_path),
        "set_a_dry_run": {
            "status": "passed",
            "evaluation_status": dry_run["evaluation_status"],
            "artifact": dry_run_path.resolve().relative_to(output.resolve()).as_posix(),
            "artifact_sha256": sha256_file(dry_run_path),
            "set_b_accessed": False,
        },
        "artifact_hashes": artifact_hashes,
        "set_b_accessed": False,
    }
    metadata_path = output / "candidate_metadata.json"
    write_json_atomic(metadata_path, metadata)
    return metadata_path, metadata
