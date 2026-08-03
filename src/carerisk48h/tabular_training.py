"""Three-seed logistic and constrained LightGBM comparison on one fixed split."""

from __future__ import annotations

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
from carerisk48h.config import RunConfig, canonical_config_payload
from carerisk48h.data.downloader import sha256_file
from carerisk48h.data.parser import ParsedStay
from carerisk48h.data.split import validate_split_manifest
from carerisk48h.explanations import generate_tree_shap_artifacts
from carerisk48h.features.tabular import build_feature_frame
from carerisk48h.metrics import compute_binary_metrics
from carerisk48h.models.lightgbm_model import LIGHTGBM_GRID, fit_lightgbm
from carerisk48h.models.logistic import fit_logistic

_AGGREGATE_METRICS = ("auprc", "auroc", "brier", "ece", "sensitivity", "specificity")


def _aggregate(seed_metrics: list[dict[str, Any]]) -> dict[str, dict[str, float | None]]:
    result: dict[str, dict[str, float | None]] = {}
    for name in _AGGREGATE_METRICS:
        values = [float(item[name]) for item in seed_metrics if item[name] is not None]
        result[name] = {
            "mean": float(np.mean(values)) if values else None,
            "std": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0 if values else None,
        }
    return result


def _mean_metric(aggregate: dict[str, dict[str, float | None]], name: str) -> float:
    value = aggregate[name]["mean"]
    if value is None:
        raise ValueError(f"aggregate metric is undefined: {name}")
    return value


def _join_features(
    frame: pd.DataFrame, outcomes: pd.DataFrame, split: pd.DataFrame
) -> pd.DataFrame:
    cohort = frame.merge(outcomes, on="RecordID", validate="one_to_one")
    cohort = cohort.merge(split, on="RecordID", validate="one_to_one")
    if len(cohort) != len(frame):
        raise ValueError("features, outcomes, and split are not perfectly aligned")
    return cohort


def train_tabular_comparison(
    stays: list[ParsedStay],
    outcomes: pd.DataFrame,
    split_manifest: pd.DataFrame,
    config: RunConfig,
    *,
    repo_root: str | Path,
    data_manifest_hash: str | None,
) -> tuple[Path, dict[str, Any]]:
    """Train all tabular candidates and write auditable development artifacts."""
    expected_ids = {stay.record_id for stay in stays}
    validate_split_manifest(split_manifest, expected_ids=expected_ids)
    config_payload = canonical_config_payload(config, repo_root=repo_root)
    base_frame = build_feature_frame(stays, include_slope=False)
    slope_frame = build_feature_frame(stays, include_slope=True)
    base = _join_features(base_frame, outcomes, split_manifest)
    slope = _join_features(slope_frame, outcomes, split_manifest)
    base_columns = [column for column in base_frame if column != "RecordID"]
    slope_columns = [column for column in slope_frame if column != "RecordID"]
    train_rows = base["split"] == "train"
    validation_rows = base["split"] == "validation"

    run_dir = config.output_dir / utc_run_id("tabular", config.mode)
    model_dir = run_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=False)

    logistic_metrics: list[dict[str, Any]] = []
    logistic_models: list[Path] = []
    for seed in config.model_seeds:
        model = fit_logistic(
            base.loc[train_rows, base_columns], base.loc[train_rows, "label"], seed=seed
        )
        probabilities = model.predict_proba(base.loc[validation_rows, base_columns])[:, 1]
        logistic_metrics.append(
            {
                "seed": seed,
                **compute_binary_metrics(
                    base.loc[validation_rows, "label"].to_numpy(), probabilities
                ),
            }
        )
        path = model_dir / f"logistic_seed_{seed}.joblib"
        joblib.dump(
            {"model_family": "logistic", "model": model, "feature_columns": base_columns}, path
        )
        logistic_models.append(path)

    grid = LIGHTGBM_GRID if config.mode == "full" else LIGHTGBM_GRID[:1]
    grid_results: list[dict[str, Any]] = []
    grid_models: dict[tuple[int, int], Any] = {}
    for grid_index, parameters in enumerate(grid):
        seed_metrics: list[dict[str, Any]] = []
        for seed in config.model_seeds:
            model = fit_lightgbm(
                slope.loc[train_rows, slope_columns],
                slope.loc[train_rows, "label"],
                seed=seed,
                n_jobs=config.cpu_threads,
                parameters=parameters,
            )
            probabilities = model.predict_proba(slope.loc[validation_rows, slope_columns])[:, 1]
            metrics = {
                "seed": seed,
                **compute_binary_metrics(
                    slope.loc[validation_rows, "label"].to_numpy(), probabilities
                ),
            }
            seed_metrics.append(metrics)
            grid_models[(grid_index, seed)] = model
        grid_results.append(
            {
                "grid_index": grid_index,
                "parameters": parameters,
                "seeds": seed_metrics,
                "aggregate": _aggregate(seed_metrics),
            }
        )
    best_grid = max(
        grid_results,
        key=lambda item: (float(item["aggregate"]["auprc"]["mean"]), -int(item["grid_index"])),
    )
    best_grid_index = int(best_grid["grid_index"])
    lightgbm_models: list[Path] = []
    for seed in config.model_seeds:
        path = model_dir / f"lightgbm_seed_{seed}.joblib"
        joblib.dump(
            {
                "model_family": "lightgbm",
                "model": grid_models[(best_grid_index, seed)],
                "feature_columns": slope_columns,
                "parameters": best_grid["parameters"],
            },
            path,
        )
        lightgbm_models.append(path)

    logistic_aggregate = _aggregate(logistic_metrics)
    lightgbm_aggregate = best_grid["aggregate"]
    selected_family = (
        "lightgbm"
        if _mean_metric(lightgbm_aggregate, "auprc") > _mean_metric(logistic_aggregate, "auprc")
        else "logistic"
    )
    selected_paths = lightgbm_models if selected_family == "lightgbm" else logistic_models
    joblib.dump(joblib.load(selected_paths[0]), run_dir / "best_model.joblib")

    best_lgb_seed_metric = max(best_grid["seeds"], key=lambda item: float(item["auprc"]))
    best_lgb_seed = int(best_lgb_seed_metric["seed"])
    shap_artifacts = generate_tree_shap_artifacts(
        grid_models[(best_grid_index, best_lgb_seed)],
        slope.loc[validation_rows, slope_columns],
        output_dir=run_dir / "shap",
        seed=best_lgb_seed,
    )
    split_manifest.to_csv(run_dir / "split_manifest.csv", index=False)
    artifact_hashes = {
        path.relative_to(run_dir).as_posix(): sha256_file(path)
        for path in [*logistic_models, *lightgbm_models, run_dir / "best_model.joblib"]
    }
    payload: dict[str, Any] = {
        "run_id": run_dir.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_status": "smoke_test" if config.mode == "quick" else "development",
        "selection_scope": "Set A validation only; not frozen or calibrated",
        "selected_tabular_family": selected_family,
        "families": {
            "logistic": {"seeds": logistic_metrics, "aggregate": logistic_aggregate},
            "lightgbm": {
                "selected_grid_index": best_grid_index,
                "selected_parameters": best_grid["parameters"],
                "seeds": best_grid["seeds"],
                "aggregate": lightgbm_aggregate,
                "grid_results": grid_results,
            },
        },
        "feature_contract": {
            "logistic": "static + last/mean/min/max/count/missing_fraction",
            "lightgbm": (
                "same base summaries + actual-observation-time slope and presence indicator"
            ),
        },
        "shap": shap_artifacts,
        "seeds": {"split": config.split_seed, "models": list(config.model_seeds)},
        "config": config_payload,
        "config_hash": stable_hash(config_payload),
        "data_manifest_hash": data_manifest_hash,
        "split_hash": stable_hash(split_manifest.to_dict(orient="records")),
        "git": git_state(repo_root),
        "environment": environment_versions(),
        "artifact_hashes": artifact_hashes,
        "notes": [
            "All 0.5-threshold operating metrics are provisional before M5 calibration.",
            "SHAP attributions describe model behavior and are not causal explanations.",
            "Development results must not update README formal results.",
        ],
    }
    write_json_atomic(run_dir / "metrics.json", payload)
    write_json_atomic(run_dir / "results.json", payload)
    return run_dir, payload
