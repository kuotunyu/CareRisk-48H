"""Config-driven baseline training orchestration."""

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
from carerisk48h.data.parser import ParsedStay
from carerisk48h.data.split import make_split_manifest
from carerisk48h.features.tabular import build_feature_frame
from carerisk48h.metrics import compute_binary_metrics
from carerisk48h.models.logistic import fit_logistic


def train_logistic(
    stays: list[ParsedStay],
    outcomes: pd.DataFrame,
    config: RunConfig,
    *,
    repo_root: str | Path,
    data_manifest_hash: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Train the vertical-slice logistic model and serialize a smoke/full run."""
    config_payload = canonical_config_payload(config, repo_root=repo_root)
    feature_frame = build_feature_frame(stays, include_slope=False)
    cohort = feature_frame.merge(outcomes, on="RecordID", how="inner", validate="one_to_one")
    if len(cohort) != len(feature_frame):
        raise ValueError("patient records and outcomes are not perfectly aligned")
    metadata = cohort.loc[:, ["RecordID", "label", "static_ICUType"]].rename(
        columns={"static_ICUType": "ICUType"}
    )
    split_manifest = make_split_manifest(metadata, seed=config.split_seed)
    cohort = cohort.merge(split_manifest, on="RecordID", validate="one_to_one")
    feature_columns = [column for column in feature_frame.columns if column != "RecordID"]
    train_rows = cohort["split"] == "train"
    validation_rows = cohort["split"] == "validation"
    model = fit_logistic(
        cohort.loc[train_rows, feature_columns],
        cohort.loc[train_rows, "label"],
        seed=config.model_seeds[0],
    )
    validation_probabilities = model.predict_proba(cohort.loc[validation_rows, feature_columns])[
        :, 1
    ]
    metrics = compute_binary_metrics(
        cohort.loc[validation_rows, "label"].to_numpy(),
        np.asarray(validation_probabilities),
        threshold=0.5,
    )

    run_id = utc_run_id("logistic", config.mode)
    run_dir = config.output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    bundle = {
        "schema_version": 1,
        "model_family": "logistic",
        "model": model,
        "feature_columns": feature_columns,
        "calibrator": None,
        "threshold": 0.5,
        "evaluation_status": "smoke_test" if config.mode == "quick" else "development",
    }
    joblib.dump(bundle, run_dir / "best_model.joblib")
    split_manifest.to_csv(run_dir / "split_manifest.csv", index=False)

    payload: dict[str, Any] = {
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_status": bundle["evaluation_status"],
        "model_family": "logistic",
        "split": "validation",
        "metrics": metrics,
        "seeds": {
            "split": config.split_seed,
            "models": list(config.model_seeds),
        },
        "config": config_payload,
        "config_hash": stable_hash(config_payload),
        "data_manifest_hash": data_manifest_hash,
        "split_hash": stable_hash(split_manifest.to_dict(orient="records")),
        "git": git_state(repo_root),
        "environment": environment_versions(),
        "notes": [
            "Threshold 0.5 is provisional; the locked 90% specificity threshold is fit only in M5.",
            "Quick/synthetic runs must not update README formal results.",
        ],
    }
    write_json_atomic(run_dir / "metrics.json", payload)
    write_json_atomic(run_dir / "results.json", payload)
    return run_dir, payload
