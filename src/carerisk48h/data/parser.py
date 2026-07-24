"""Parse PhysioNet Challenge 2012 patient files into leakage-safe tensors."""

from __future__ import annotations

import csv
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

import numpy as np
import pandas as pd

from carerisk48h.constants import (
    N_HOURS,
    OUTCOME_COLUMNS,
    PARAMETER_ALIASES,
    STATIC_VARIABLES,
    TIME_SERIES_VARIABLES,
    VARIABLE_INDEX,
)

_TIMESTAMP = re.compile(r"^(\d{2}):(\d{2})$")


@dataclass(frozen=True)
class ParsedStay:
    """One ICU stay represented as hourly values, masks, deltas, and raw observations."""

    record_id: int
    static: dict[str, float]
    values: np.ndarray
    mask: np.ndarray
    delta: np.ndarray
    observations: dict[str, tuple[tuple[float, float], ...]]

    def __post_init__(self) -> None:
        expected = (N_HOURS, len(TIME_SERIES_VARIABLES))
        if (
            self.values.shape != expected
            or self.mask.shape != expected
            or self.delta.shape != expected
        ):
            raise ValueError(f"hourly arrays must have shape {expected}")


def timestamp_to_bin(timestamp: str) -> tuple[int, float]:
    """Convert HH:MM to a 0-based hourly bin and elapsed hours.

    Exact 48:00 belongs to the final bin; values after 48:00 are invalid.
    """
    match = _TIMESTAMP.fullmatch(timestamp.strip())
    if match is None:
        raise ValueError(f"invalid timestamp format: {timestamp!r}")
    hour, minute = (int(part) for part in match.groups())
    if minute > 59 or hour > 48 or (hour == 48 and minute != 0):
        raise ValueError(f"timestamp outside first 48 hours: {timestamp!r}")
    elapsed = hour + minute / 60.0
    return (N_HOURS - 1 if hour == 48 else hour), elapsed


def _parse_number(raw: str, *, parameter: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"non-numeric value for {parameter}: {raw!r}") from exc
    if not np.isfinite(value):
        raise ValueError(f"non-finite value for {parameter}: {raw!r}")
    return value


def _aggregate(parameter: str, samples: list[tuple[float, float]]) -> float:
    values = [value for _, value in samples]
    if parameter == "Urine":
        return float(np.sum(values))
    if parameter == "MechVent":
        return float(np.max(values))
    if parameter == "Weight":
        return float(max(samples, key=lambda sample: sample[0])[1])
    return float(np.mean(values))


def parse_record(source: str | Path | TextIO) -> ParsedStay:
    """Parse a patient record from a path or text stream."""
    close = False
    if isinstance(source, str | Path):
        handle: TextIO = Path(source).open(  # noqa: SIM115 - closed in finally
            "r", encoding="utf-8-sig", newline=""
        )
        close = True
    else:
        handle = source

    try:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["Time", "Parameter", "Value"]:
            raise ValueError("record must have Time,Parameter,Value header")

        record_id: int | None = None
        static = {name: float("nan") for name in STATIC_VARIABLES}
        hourly: dict[tuple[int, str], list[tuple[float, float]]] = {}
        raw_observations: dict[str, list[tuple[float, float]]] = {
            name: [] for name in TIME_SERIES_VARIABLES
        }

        for row_number, row in enumerate(reader, start=2):
            timestamp = row["Time"].strip()
            parameter = row["Parameter"].strip()
            parameter = PARAMETER_ALIASES.get(parameter, parameter)
            value = _parse_number(row["Value"].strip(), parameter=parameter)
            hour_bin, elapsed = timestamp_to_bin(timestamp)

            if parameter == "RecordID":
                if timestamp != "00:00" or not value.is_integer():
                    raise ValueError("RecordID must be an integer at 00:00")
                candidate = int(value)
                if record_id is not None and record_id != candidate:
                    raise ValueError("record contains conflicting RecordID values")
                record_id = candidate
                continue

            if (
                parameter in STATIC_VARIABLES
                and timestamp == "00:00"
                and np.isnan(static[parameter])
            ):
                static[parameter] = float("nan") if value == -1 else value

            if parameter in VARIABLE_INDEX:
                if value == -1:
                    continue
                sample = (elapsed, value)
                hourly.setdefault((hour_bin, parameter), []).append(sample)
                raw_observations[parameter].append(sample)
            elif parameter not in STATIC_VARIABLES:
                if parameter in OUTCOME_COLUMNS:
                    raise ValueError(
                        f"outcome-related descriptor found in input record: {parameter}"
                    )
                raise ValueError(f"unknown parameter {parameter!r} at row {row_number}")

        if record_id is None:
            raise ValueError("record is missing RecordID")

        shape = (N_HOURS, len(TIME_SERIES_VARIABLES))
        values = np.full(shape, np.nan, dtype=np.float32)
        mask = np.zeros(shape, dtype=np.bool_)
        for (hour_bin, parameter), samples in hourly.items():
            column = VARIABLE_INDEX[parameter]
            values[hour_bin, column] = _aggregate(parameter, samples)
            mask[hour_bin, column] = True

        delta = np.zeros(shape, dtype=np.float32)
        for column in range(shape[1]):
            last_observed: int | None = None
            for hour_bin in range(N_HOURS):
                if mask[hour_bin, column]:
                    delta[hour_bin, column] = 0.0
                    last_observed = hour_bin
                else:
                    delta[hour_bin, column] = float(
                        hour_bin + 1 if last_observed is None else hour_bin - last_observed
                    )

        frozen_observations = {
            name: tuple(sorted(samples)) for name, samples in raw_observations.items()
        }
        return ParsedStay(record_id, static, values, mask, delta, frozen_observations)
    finally:
        if close:
            handle.close()


def parse_directory(path: str | Path, *, max_patients: int | None = None) -> list[ParsedStay]:
    """Parse a directory of patient TXT records in deterministic RecordID order."""
    files = sorted(Path(path).glob("*.txt"), key=lambda item: item.stem)
    if max_patients is not None:
        files = files[:max_patients]
    if not files:
        raise FileNotFoundError(f"no patient TXT files found in {Path(path)}")
    stays = [parse_record(file) for file in files]
    ids = [stay.record_id for stay in stays]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate RecordID across patient files")
    return sorted(stays, key=lambda stay: stay.record_id)


def load_outcomes(path: str | Path) -> pd.DataFrame:
    """Load only RecordID and the permitted binary label from an outcomes file."""
    frame = pd.read_csv(path)
    required = {"RecordID", "In-hospital_death"}
    if not required.issubset(frame.columns):
        raise ValueError(f"outcomes file is missing {sorted(required - set(frame.columns))}")
    result = frame.loc[:, ["RecordID", "In-hospital_death"]].rename(
        columns={"In-hospital_death": "label"}
    )
    if result["RecordID"].duplicated().any():
        raise ValueError("outcomes contain duplicate RecordID")
    if not result["label"].isin([0, 1]).all():
        raise ValueError("In-hospital_death must contain only 0/1")
    return result.astype({"RecordID": "int64", "label": "int8"})


def stack_hourly(stays: Iterable[ParsedStay]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Stack value, mask, and delta arrays in input order."""
    materialized = list(stays)
    if not materialized:
        raise ValueError("at least one stay is required")
    return (
        np.stack([stay.values for stay in materialized]).astype(np.float32),
        np.stack([stay.mask for stay in materialized]).astype(np.bool_),
        np.stack([stay.delta for stay in materialized]).astype(np.float32),
    )
