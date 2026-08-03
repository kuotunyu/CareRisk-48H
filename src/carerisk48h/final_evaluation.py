"""One-time frozen Set B evaluation orchestrator."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from carerisk48h.artifacts import (
    environment_versions,
    git_state,
    stable_hash,
    utc_run_id,
    write_json_atomic,
)
from carerisk48h.data.downloader import sha256_file, verify_manifest
from carerisk48h.data.parser import parse_directory
from carerisk48h.evaluation import (
    error_case_table,
    stratified_bootstrap_ci,
    subgroup_analysis,
    write_evaluation_plots,
)
from carerisk48h.features.tabular import build_feature_frame
from carerisk48h.final_gate import load_set_b_outcomes_once
from carerisk48h.freezing import validate_freeze_manifest
from carerisk48h.metrics import compute_binary_metrics


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _validate_input_only_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = _read_json_object(path)
    files = payload.get("files")
    filenames = (
        [str(item.get("filename", "")) for item in files if isinstance(item, dict)]
        if isinstance(files, list)
        else []
    )
    if payload.get("set") != "b" or filenames != ["set-b.tar.gz"]:
        raise ValueError("Set B preflight requires an input-only manifest without outcomes")
    verify_manifest(path.parent, path)
    return payload


def _validate_bundle(bundle: dict[str, Any], freeze: dict[str, Any]) -> None:
    if bundle.get("schema_version") != 1:
        raise ValueError("final candidate bundle schema is unsupported")
    if bundle.get("model_family") != freeze.get("model_family"):
        raise ValueError("final candidate family does not match freeze")
    if bundle.get("model_seeds") != freeze.get("model_seeds"):
        raise ValueError("final candidate seeds do not match freeze")
    if bundle.get("training_scope") != "Set A train+validation":
        raise ValueError("final candidate training scope is invalid")
    if bundle.get("calibration_fit_scope") != "Set A calibration":
        raise ValueError("final candidate calibration scope is invalid")
    if float(bundle.get("threshold", -1.0)) != float(freeze.get("threshold", -2.0)):
        raise ValueError("final candidate threshold does not match freeze")
    models = bundle.get("models")
    if not isinstance(models, list) or len(models) != 3:
        raise ValueError("final candidate must contain the frozen three-model ensemble")
    feature_columns = bundle.get("feature_columns")
    if not isinstance(feature_columns, list) or not feature_columns:
        raise ValueError("final candidate feature contract is missing")
    if bundle.get("calibrator") is None:
        raise ValueError("final candidate calibrator is missing")


def _success_attempt(ledger: dict[str, Any]) -> dict[str, Any]:
    attempts = ledger.get("attempts")
    successes = (
        [item for item in attempts if isinstance(item, dict) and item.get("status") == "success"]
        if isinstance(attempts, list)
        else []
    )
    if len(successes) != 1:
        raise RuntimeError("final ledger must contain exactly one successful Set B access")
    return successes[0]


def run_set_b_final_evaluation(
    *,
    candidate_dir: str | Path,
    records_dir: str | Path,
    outcomes_path: str | Path,
    input_manifest_path: str | Path,
    repo_root: str | Path,
    confirm_final: bool,
    bootstrap_samples: int = 2_000,
    expected_records: int = 4_000,
) -> tuple[Path, dict[str, Any]]:
    """Preflight everything, then consume Set B outcomes exactly once."""
    candidate = Path(candidate_dir).resolve()
    freeze_path = candidate / "freeze_manifest.json"
    bundle_path = candidate / "final_candidate.joblib"
    output = candidate / "set_b_final"
    ledger_path = candidate / "set_b_access_ledger.json"
    final_lock_path = candidate / "set_b_access_ledger.final-lock.json"
    outcome_file = Path(outcomes_path)

    if not confirm_final:
        load_set_b_outcomes_once(
            outcome_file,
            freeze_manifest_path=freeze_path,
            ledger_path=ledger_path,
            confirm_final=False,
        )
        raise AssertionError("unreachable after missing final confirmation")
    if output.exists():
        raise FileExistsError(f"final output already exists: {output}")
    if bootstrap_samples < 1:
        raise ValueError("bootstrap samples must be positive")
    if expected_records < 1:
        raise ValueError("expected record count must be positive")

    source = git_state(repo_root)
    evaluation_sha = source.get("commit")
    if not isinstance(evaluation_sha, str) or len(evaluation_sha) != 40:
        raise ValueError("final evaluation requires a committed Git source")
    if source.get("dirty") is not False:
        raise ValueError("final evaluation requires a clean Git worktree")

    freeze = _read_json_object(freeze_path)
    validate_freeze_manifest(freeze, manifest_path=freeze_path, verify_artifacts=True)
    if freeze.get("set_b_final_evaluation_successes") != 0:
        raise ValueError("freeze must record zero Set B successes before final evaluation")
    if not bundle_path.is_file():
        raise FileNotFoundError(bundle_path)
    loaded_bundle = joblib.load(bundle_path)
    if not isinstance(loaded_bundle, dict):
        raise ValueError("final candidate bundle must be a mapping")
    bundle: dict[str, Any] = loaded_bundle
    _validate_bundle(bundle, freeze)

    input_manifest = Path(input_manifest_path)
    input_payload = _validate_input_only_manifest(input_manifest)
    preflight_started = time.perf_counter()
    stays = parse_directory(records_dir)
    if len(stays) != expected_records:
        raise ValueError(
            f"Set B input count changed: expected {expected_records}, observed {len(stays)}"
        )
    features = build_feature_frame(stays, include_slope=bundle["model_family"] == "lightgbm")
    feature_columns = [str(column) for column in bundle["feature_columns"]]
    missing = set(feature_columns) - set(features.columns)
    if missing:
        raise ValueError(f"Set B features are missing frozen columns: {sorted(missing)}")
    matrix = features.loc[:, feature_columns]
    models = list(bundle["models"])
    raw_probabilities = np.mean(
        np.stack([model.predict_proba(matrix)[:, 1] for model in models]), axis=0
    )
    probabilities = np.asarray(bundle["calibrator"].predict(raw_probabilities), dtype=np.float64)
    if probabilities.shape != (expected_records,) or np.any(
        ~np.isfinite(probabilities) | (probabilities < 0.0) | (probabilities > 1.0)
    ):
        raise ValueError("frozen candidate produced invalid Set B probabilities")
    record_ids = features["RecordID"].to_numpy(dtype=np.int64)
    metadata = pd.DataFrame(
        {
            "RecordID": [stay.record_id for stay in stays],
            "Gender": [stay.static["Gender"] for stay in stays],
            "ICUType": [stay.static["ICUType"] for stay in stays],
            "Age": [stay.static["Age"] for stay in stays],
        }
    ).sort_values("RecordID", ignore_index=True)
    if not np.array_equal(metadata["RecordID"].to_numpy(dtype=np.int64), record_ids):
        raise ValueError("Set B feature and subgroup metadata IDs do not align")
    preflight_seconds = time.perf_counter() - preflight_started

    output.mkdir(parents=False, exist_ok=False)
    preflight_path = output / "preflight.json"
    write_json_atomic(
        preflight_path,
        {
            "schema_version": 1,
            "status": "passed_before_outcome_access",
            "evaluation_source_git_sha": evaluation_sha,
            "freeze_manifest_sha256": sha256_file(freeze_path),
            "final_candidate_sha256": sha256_file(bundle_path),
            "set_b_input_manifest_sha256": sha256_file(input_manifest),
            "set_b_record_count": expected_records,
            "set_b_record_ids_sha256": stable_hash(record_ids.tolist()),
            "set_b_accessed": False,
        },
    )

    access_started = time.perf_counter()
    outcomes = load_set_b_outcomes_once(
        outcome_file,
        freeze_manifest_path=freeze_path,
        ledger_path=ledger_path,
        confirm_final=True,
        download_if_missing=True,
    )
    access_seconds = time.perf_counter() - access_started
    ledger = _read_json_object(ledger_path)
    success = _success_attempt(ledger)
    if not final_lock_path.is_file():
        raise RuntimeError("successful Set B access did not create the persistent final lock")

    aligned = pd.DataFrame({"RecordID": record_ids}).merge(
        outcomes, on="RecordID", how="left", validate="one_to_one"
    )
    if len(aligned) != expected_records or aligned["label"].isna().any():
        raise ValueError("Set B outcomes do not exactly match the preflighted input RecordIDs")
    if set(outcomes["RecordID"].astype(int)) != set(record_ids.tolist()):
        raise ValueError("Set B outcomes contain IDs outside the preflighted input cohort")
    labels = aligned["label"].to_numpy(dtype=np.int8)
    threshold = float(bundle["threshold"])

    evaluation_started = time.perf_counter()
    metrics = compute_binary_metrics(labels, probabilities, threshold=threshold)
    intervals = stratified_bootstrap_ci(
        labels,
        probabilities,
        threshold=threshold,
        samples=bootstrap_samples,
        seed=2026,
    )
    subgroups = subgroup_analysis(
        labels,
        probabilities,
        metadata.loc[:, ["Gender", "ICUType", "Age"]],
        threshold=threshold,
        bootstrap_samples=bootstrap_samples,
        seed=2026,
    )
    predictions_path = output / "predictions.npz"
    np.savez_compressed(
        predictions_path,
        record_ids=record_ids,
        labels=labels,
        raw_probabilities=raw_probabilities,
        probabilities=probabilities,
    )
    errors_path = output / "error_cases.csv"
    error_case_table(labels, probabilities, record_ids, threshold=threshold).to_csv(
        errors_path, index=False
    )
    subgroups_path = output / "subgroups.json"
    write_json_atomic(subgroups_path, {"subgroups": subgroups})
    write_evaluation_plots(labels, probabilities, output_dir=output / "plots")
    plot_path = output / "plots" / "evaluation_plots.png"
    evaluation_seconds = time.perf_counter() - evaluation_started

    frozen_candidate = freeze["candidate"]
    artifacts = [
        preflight_path,
        predictions_path,
        errors_path,
        subgroups_path,
        plot_path,
        ledger_path,
        final_lock_path,
    ]
    artifact_hashes = {
        path.resolve().relative_to(candidate).as_posix(): sha256_file(path) for path in artifacts
    }
    payload: dict[str, Any] = {
        "schema_version": 1,
        "run_id": utc_run_id(str(bundle["model_family"]), "set-b-final"),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_status": "final",
        "dataset": "PhysioNet Challenge 2012 Set B",
        "freeze_status": "frozen",
        "freeze_manifest_sha256": sha256_file(freeze_path),
        "set_b_final_evaluation_successes": 1,
        "model_family": bundle["model_family"],
        "model_seeds": bundle["model_seeds"],
        "calibrator": frozen_candidate["calibrator"],
        "threshold": threshold,
        "candidate_source_git_sha": freeze["source_git_sha"],
        "evaluation_source_git_sha": evaluation_sha,
        "evaluation_source_git_dirty": False,
        "config_hash": freeze["config_hash"],
        "data_manifest_hash": frozen_candidate["data_manifest_hash"],
        "split_hash": frozen_candidate["split_hash"],
        "set_b_input_manifest_sha256": sha256_file(input_manifest),
        "set_b_input_archive_sha256": input_payload["files"][0]["sha256"],
        "set_b_record_ids_sha256": stable_hash(record_ids.tolist()),
        "outcomes_sha256": success["outcomes_sha256"],
        "environment": {
            "python": sys.version,
            **environment_versions(("lightgbm", "shap")),
        },
        "timing_seconds": {
            "preflight": preflight_seconds,
            "outcome_access": access_seconds,
            "evaluation_and_reports": evaluation_seconds,
        },
        "bootstrap": {
            "method": "stratified percentile",
            "samples": bootstrap_samples,
            "seed": 2026,
        },
        "metrics": metrics,
        "confidence_intervals": intervals,
        "subgroups": subgroups,
        "artifact_hashes": artifact_hashes,
        "notes": [
            "Descriptive research evaluation only; not clinical guidance.",
            "Subgroup results are descriptive and do not establish fairness or causality.",
            "The frozen candidate, calibrator, and threshold were not changed after Set B access.",
        ],
    }
    metrics_path = output / "metrics.json"
    write_json_atomic(metrics_path, payload)
    return metrics_path, payload


def final_evaluation_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--records-dir", type=Path, default=Path("data/raw/set-b"))
    parser.add_argument("--outcomes", type=Path, default=Path("data/raw/Outcomes-b.txt"))
    parser.add_argument("--input-manifest", type=Path, default=Path("data/raw/manifest-set-b.json"))
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--confirm-final", action="store_true")
    args = parser.parse_args()
    metrics_path, payload = run_set_b_final_evaluation(
        candidate_dir=args.candidate_dir,
        records_dir=args.records_dir,
        outcomes_path=args.outcomes,
        input_manifest_path=args.input_manifest,
        repo_root=args.repo_root,
        confirm_final=args.confirm_final,
    )
    print(f"Final metrics: {metrics_path.resolve()}")
    print(f"Set B successful accesses: {payload['set_b_final_evaluation_successes']}")
