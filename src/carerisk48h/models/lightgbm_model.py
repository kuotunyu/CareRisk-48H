"""Constrained LightGBM baseline with an explicit preprocessing boundary."""

from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from carerisk48h.features.tabular import assert_no_forbidden_features

LIGHTGBM_GRID: tuple[dict[str, Any], ...] = (
    {"learning_rate": 0.03, "n_estimators": 250, "num_leaves": 15, "min_child_samples": 30},
    {"learning_rate": 0.03, "n_estimators": 250, "num_leaves": 31, "min_child_samples": 50},
    {"learning_rate": 0.05, "n_estimators": 180, "num_leaves": 15, "min_child_samples": 50},
)


def build_lightgbm_pipeline(
    feature_columns: list[str],
    *,
    seed: int,
    n_jobs: int,
    parameters: dict[str, Any],
) -> Pipeline:
    """Build a deterministic, class-weighted LightGBM pipeline."""
    try:
        from lightgbm import LGBMClassifier
    except ImportError as exc:  # pragma: no cover - optional dependency message
        raise RuntimeError("Install CareRisk 48H with the 'tabular' extra") from exc
    if "static_ICUType" not in feature_columns:
        raise ValueError("static_ICUType is required")
    numeric = [column for column in feature_columns if column != "static_ICUType"]
    preprocessor = ColumnTransformer(
        [
            (
                "icu_type",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ["static_ICUType"],
            ),
            ("numeric", "passthrough", numeric),
        ],
        verbose_feature_names_out=True,
    )
    classifier = LGBMClassifier(
        objective="binary",
        class_weight="balanced",
        random_state=seed,
        bagging_seed=seed,
        feature_fraction_seed=seed,
        data_random_seed=seed,
        deterministic=True,
        force_col_wise=True,
        subsample=0.9,
        subsample_freq=1,
        colsample_bytree=0.9,
        n_jobs=n_jobs,
        verbosity=-1,
        reg_lambda=1.0,
        **parameters,
    )
    return Pipeline([("preprocessor", preprocessor), ("classifier", classifier)])


def fit_lightgbm(
    frame: pd.DataFrame,
    labels: pd.Series,
    *,
    seed: int,
    n_jobs: int,
    parameters: dict[str, Any],
) -> Pipeline:
    """Fit on exactly the caller-provided train rows."""
    assert_no_forbidden_features(frame)
    model = build_lightgbm_pipeline(
        list(frame.columns), seed=seed, n_jobs=n_jobs, parameters=parameters
    )
    model.fit(frame, labels)
    return model
