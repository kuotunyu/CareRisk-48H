"""Train-fitted numpy preprocessing shared by GRU-D and TCN."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from carerisk48h.constants import STATIC_VARIABLES, TIME_SERIES_VARIABLES
from carerisk48h.data.parser import ParsedStay, stack_hourly


@dataclass(frozen=True)
class DeepPreprocessor:
    """Serializable statistics fit only on an explicitly supplied cohort."""

    value_mean: np.ndarray
    value_std: np.ndarray
    static_median: np.ndarray
    static_mean: np.ndarray
    static_std: np.ndarray
    fit_record_ids: np.ndarray

    @classmethod
    def fit(cls, stays: list[ParsedStay]) -> DeepPreprocessor:
        if not stays:
            raise ValueError("at least one train stay is required")
        values, mask, _ = stack_hourly(stays)
        value_mean = np.zeros(len(TIME_SERIES_VARIABLES), dtype=np.float32)
        value_std = np.ones(len(TIME_SERIES_VARIABLES), dtype=np.float32)
        for column in range(values.shape[2]):
            observed = values[:, :, column][mask[:, :, column]]
            if observed.size:
                value_mean[column] = float(np.mean(observed))
                standard_deviation = float(np.std(observed))
                value_std[column] = standard_deviation if standard_deviation > 1e-6 else 1.0
        static = np.asarray(
            [[stay.static[name] for name in STATIC_VARIABLES] for stay in stays],
            dtype=np.float32,
        )
        static_median = np.nanmedian(static, axis=0).astype(np.float32)
        static_median = np.nan_to_num(static_median, nan=0.0)
        imputed = np.where(np.isnan(static), static_median, static)
        static_mean = imputed.mean(axis=0).astype(np.float32)
        static_std = imputed.std(axis=0).astype(np.float32)
        static_std[static_std <= 1e-6] = 1.0
        return cls(
            value_mean,
            value_std,
            static_median,
            static_mean,
            static_std,
            np.asarray([stay.record_id for stay in stays], dtype=np.int64),
        )

    def transform(self, stays: list[ParsedStay]) -> dict[str, np.ndarray]:
        values, mask, delta = stack_hourly(stays)
        normalized = (values - self.value_mean[None, None, :]) / self.value_std[None, None, :]
        normalized = np.where(mask, normalized, 0.0).astype(np.float32)
        static = np.asarray(
            [[stay.static[name] for name in STATIC_VARIABLES] for stay in stays],
            dtype=np.float32,
        )
        static = np.where(np.isnan(static), self.static_median, static)
        static = ((static - self.static_mean) / self.static_std).astype(np.float32)
        return {
            "values": normalized,
            "mask": mask.astype(np.float32),
            "delta": delta.astype(np.float32),
            "static": static,
            "record_ids": np.asarray([stay.record_id for stay in stays], dtype=np.int64),
        }

    def save(self, path: str | Path) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".partial")
        with temporary.open("wb") as handle:
            np.savez_compressed(
                handle,
                value_mean=self.value_mean,
                value_std=self.value_std,
                static_median=self.static_median,
                static_mean=self.static_mean,
                static_std=self.static_std,
                fit_record_ids=self.fit_record_ids,
            )
        temporary.replace(destination)

    @classmethod
    def load(cls, path: str | Path) -> DeepPreprocessor:
        with np.load(path) as data:
            return cls(
                value_mean=data["value_mean"],
                value_std=data["value_std"],
                static_median=data["static_median"],
                static_mean=data["static_mean"],
                static_std=data["static_std"],
                fit_record_ids=data["fit_record_ids"],
            )
