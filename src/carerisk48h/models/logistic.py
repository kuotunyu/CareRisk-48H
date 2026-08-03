"""Interpretable class-weighted logistic baseline."""

from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from carerisk48h.features.tabular import assert_no_forbidden_features


def build_logistic_pipeline(feature_columns: list[str], *, seed: int) -> Pipeline:
    """Create the fixed preprocessing and logistic regression pipeline."""
    if "static_ICUType" not in feature_columns:
        raise ValueError("static_ICUType is required")
    categorical = ["static_ICUType"]
    numeric = [column for column in feature_columns if column not in categorical]
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric,
            ),
            (
                "icu_type",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "onehot",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        ),
                    ]
                ),
                categorical,
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )
    return Pipeline(
        [
            ("preprocessor", preprocessor),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=2000,
                    penalty="l2",
                    random_state=seed,
                    solver="liblinear",
                ),
            ),
        ]
    )


def fit_logistic(frame: pd.DataFrame, labels: pd.Series, *, seed: int) -> Pipeline:
    """Fit on exactly the rows provided by the caller."""
    assert_no_forbidden_features(frame)
    pipeline = build_logistic_pipeline(list(frame.columns), seed=seed)
    pipeline.fit(frame, labels)
    return pipeline
