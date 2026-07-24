"""Synthetic-only demo fixture and reproducible smoke bundle builder."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from carerisk48h.calibration import fit_calibration_bundle
from carerisk48h.data.parser import ParsedStay
from carerisk48h.data.split import make_split_manifest
from carerisk48h.features.tabular import build_feature_frame
from carerisk48h.guard import QualityOODGuard
from carerisk48h.models.logistic import fit_logistic
from carerisk48h.synthetic import generate_synthetic_cohort


def synthetic_payload(*, index: int = 0, seed: int = 2026) -> dict[str, Any]:
    """Return one deterministic, non-clinical JSON-compatible patient fixture."""
    stays, _ = generate_synthetic_cohort(120, seed=seed)
    stay = stays[index % len(stays)]
    measurements = [
        {
            "time": f"{int(hour):02d}:{int(round((hour % 1) * 60)):02d}",
            "parameter": name,
            "value": value,
        }
        for name, samples in stay.observations.items()
        for hour, value in samples
    ]
    measurements.sort(key=lambda item: (str(item["time"]), str(item["parameter"])))
    return {"static": stay.static, "measurements": measurements}


def _metadata(stays: list[ParsedStay], outcomes: pd.DataFrame) -> pd.DataFrame:
    labels = outcomes.set_index("RecordID")["label"]
    return pd.DataFrame(
        {
            "RecordID": [stay.record_id for stay in stays],
            "label": [labels.loc[stay.record_id] for stay in stays],
            "ICUType": [stay.static["ICUType"] for stay in stays],
        }
    )


def build_synthetic_demo_bundle(path: str | Path, *, seed: int = 2026) -> Path:
    """Train a small synthetic-only bundle; never represents project performance."""
    destination = Path(path)
    stays, outcomes = generate_synthetic_cohort(240, seed=seed)
    split = make_split_manifest(_metadata(stays, outcomes), seed=seed)
    features = build_feature_frame(stays, include_slope=False)
    cohort = features.merge(outcomes, on="RecordID").merge(split, on="RecordID")
    columns = [column for column in features if column != "RecordID"]
    train = cohort["split"] == "train"
    calibration = cohort["split"] == "calibration"
    model = fit_logistic(cohort.loc[train, columns], cohort.loc[train, "label"], seed=seed)
    raw_calibration = model.predict_proba(cohort.loc[calibration, columns])[:, 1]
    calibration_bundle = fit_calibration_bundle(
        cohort.loc[calibration, "label"].to_numpy(), raw_calibration, method="platt"
    )
    train_ids = set(cohort.loc[train, "RecordID"].astype(int))
    guard = QualityOODGuard.fit(
        [stay for stay in stays if stay.record_id in train_ids], seed=seed, n_jobs=1
    )
    bundle = {
        "schema_version": 1,
        "model_family": "logistic",
        "models": [model],
        "feature_columns": columns,
        "guard": guard,
        "calibrator": calibration_bundle["calibrator"],
        "threshold": calibration_bundle["threshold"],
        "evaluation_status": "smoke_test",
        "data_source": "deterministic synthetic fixture only",
        "warning": "Synthetic demo scores are not CareRisk 48H study results.",
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, destination)
    return destination
