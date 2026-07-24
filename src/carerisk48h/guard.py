"""Train-only missingness and out-of-distribution safety guard."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from carerisk48h.constants import TIME_SERIES_VARIABLES
from carerisk48h.data.parser import ParsedStay
from carerisk48h.data.quality import stay_quality_features


def _guard_vector(stay: ParsedStay) -> np.ndarray:
    quality = stay_quality_features(stay)
    per_variable_coverage = stay.mask.mean(axis=0).astype(np.float64)
    base = np.asarray(
        [
            quality["dynamic_variable_coverage"],
            np.log1p(float(quality["measurement_count"])),
            quality["core_vital_groups"] / 5.0,
        ],
        dtype=np.float64,
    )
    return np.concatenate([base, per_variable_coverage])


@dataclass
class QualityOODGuard:
    """Serializable fail-closed gate fit only on development training rows."""

    model: IsolationForest
    dynamic_variable_coverage_min: float
    measurement_count_min: float
    core_vital_groups_min: int
    ood_score_min: float
    fit_record_ids: np.ndarray
    feature_names: tuple[str, ...]

    @classmethod
    def fit(
        cls,
        stays: list[ParsedStay],
        *,
        seed: int = 2026,
        n_jobs: int = 1,
    ) -> QualityOODGuard:
        if len(stays) < 100:
            raise ValueError("guard fitting requires at least 100 train stays")
        matrix = np.stack([_guard_vector(stay) for stay in stays])
        qualities = [stay_quality_features(stay) for stay in stays]
        model = IsolationForest(
            n_estimators=200,
            contamination="auto",
            random_state=seed,
            n_jobs=n_jobs,
        ).fit(matrix)
        scores = model.score_samples(matrix)
        names = (
            "dynamic_variable_coverage",
            "log1p_measurement_count",
            "core_vital_groups_fraction",
            *(f"{variable}_hourly_coverage" for variable in TIME_SERIES_VARIABLES),
        )
        return cls(
            model=model,
            dynamic_variable_coverage_min=float(
                np.percentile([float(item["dynamic_variable_coverage"]) for item in qualities], 1)
            ),
            measurement_count_min=float(
                np.percentile([float(item["measurement_count"]) for item in qualities], 1)
            ),
            core_vital_groups_min=3,
            ood_score_min=float(np.percentile(scores, 1)),
            fit_record_ids=np.asarray([stay.record_id for stay in stays], dtype=np.int64),
            feature_names=names,
        )

    def assess(self, stay: ParsedStay) -> dict[str, Any]:
        quality = stay_quality_features(stay)
        score = float(self.model.score_samples(_guard_vector(stay).reshape(1, -1))[0])
        reasons: list[str] = []
        if float(quality["dynamic_variable_coverage"]) < self.dynamic_variable_coverage_min:
            reasons.append("dynamic variable coverage below train 1st percentile")
        if float(quality["measurement_count"]) < self.measurement_count_min:
            reasons.append("measurement count below train 1st percentile")
        if int(quality["core_vital_groups"]) < self.core_vital_groups_min:
            reasons.append("fewer than three core vital groups")
        if score < self.ood_score_min:
            reasons.append("input pattern below train 1st-percentile OOD score")
        return {
            "allow_probability": not reasons,
            "requires_human_review": bool(reasons),
            "reasons": reasons,
            "quality": quality,
            "ood_score": score,
            "thresholds": {
                "dynamic_variable_coverage_min": self.dynamic_variable_coverage_min,
                "measurement_count_min": self.measurement_count_min,
                "core_vital_groups_min": self.core_vital_groups_min,
                "ood_score_min": self.ood_score_min,
            },
        }

    def save(self, path: str | Path) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, destination)

    @classmethod
    def load(cls, path: str | Path) -> QualityOODGuard:
        loaded = joblib.load(path)
        if not isinstance(loaded, cls):
            raise TypeError("serialized object is not a QualityOODGuard")
        return loaded
