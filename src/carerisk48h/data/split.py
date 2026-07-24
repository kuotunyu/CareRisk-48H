"""Deterministic Set A train/validation/calibration splitting."""

from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split


def make_split_manifest(metadata: pd.DataFrame, *, seed: int = 2026) -> pd.DataFrame:
    """Return a 70/15/15 mortality×ICUType-stratified split manifest."""
    required = {"RecordID", "label", "ICUType"}
    if not required.issubset(metadata.columns):
        raise ValueError(f"metadata is missing {sorted(required - set(metadata.columns))}")
    if metadata["RecordID"].duplicated().any():
        raise ValueError("RecordID must be unique before splitting")
    strata = metadata["label"].astype(str) + "_" + metadata["ICUType"].astype(str)
    try:
        train_ids, holdout_ids = train_test_split(
            metadata["RecordID"],
            test_size=0.30,
            random_state=seed,
            stratify=strata,
        )
        holdout = metadata[metadata["RecordID"].isin(holdout_ids)]
        holdout_strata = holdout["label"].astype(str) + "_" + holdout["ICUType"].astype(str)
        validation_ids, calibration_ids = train_test_split(
            holdout["RecordID"],
            test_size=0.50,
            random_state=seed,
            stratify=holdout_strata,
        )
    except ValueError as exc:
        raise ValueError(
            "mortality×ICUType strata are too small for a reproducible 70/15/15 split"
        ) from exc

    assignments = {
        **{int(record_id): "train" for record_id in train_ids},
        **{int(record_id): "validation" for record_id in validation_ids},
        **{int(record_id): "calibration" for record_id in calibration_ids},
    }
    manifest = metadata.loc[:, ["RecordID"]].copy()
    manifest["split"] = manifest["RecordID"].map(assignments)
    validate_split_manifest(manifest, expected_ids=set(metadata["RecordID"].astype(int)))
    return manifest.sort_values("RecordID").reset_index(drop=True)


def validate_split_manifest(
    manifest: pd.DataFrame, *, expected_ids: set[int] | None = None
) -> None:
    """Fail on duplicate, missing, unknown, or overlapping split assignments."""
    if set(manifest.columns) != {"RecordID", "split"}:
        raise ValueError("split manifest must contain only RecordID and split")
    if manifest["RecordID"].duplicated().any():
        raise ValueError("split manifest contains duplicate RecordID")
    allowed = {"train", "validation", "calibration"}
    if not set(manifest["split"]).issubset(allowed):
        raise ValueError("split manifest contains an unknown split")
    if set(manifest["split"]) != allowed:
        raise ValueError("split manifest must contain train, validation, and calibration")
    if expected_ids is not None and set(manifest["RecordID"].astype(int)) != expected_ids:
        raise ValueError("split manifest IDs do not match the expected cohort")
