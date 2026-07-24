"""Strict inference payload validation independent of model implementation."""

from __future__ import annotations

from io import StringIO
from math import isfinite
from numbers import Real
from typing import Any

from carerisk48h.constants import (
    OUTCOME_COLUMNS,
    PARAMETER_ALIASES,
    STATIC_VARIABLES,
    VARIABLE_INDEX,
)
from carerisk48h.data.parser import ParsedStay, parse_record, timestamp_to_bin


def _finite_number(value: Any, *, field: str, allow_null: bool = False) -> float | None:
    if value is None and allow_null:
        return None
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(float(value)):
        raise ValueError(f"{field} must be a finite number")
    return float(value)


def validate_inference_payload(payload: dict[str, Any]) -> ParsedStay:
    """Validate and convert one JSON-compatible payload to the parser contract."""
    if set(payload) != {"static", "measurements"}:
        raise ValueError("payload must contain exactly static and measurements")
    static = payload["static"]
    measurements = payload["measurements"]
    if not isinstance(static, dict) or not isinstance(measurements, list):
        raise ValueError("static must be an object and measurements must be a list")
    if set(static) != set(STATIC_VARIABLES):
        raise ValueError(f"static must contain exactly {list(STATIC_VARIABLES)}")
    for parameter in STATIC_VARIABLES:
        _finite_number(static[parameter], field=parameter, allow_null=parameter != "ICUType")
    icu_type = static["ICUType"]
    if icu_type not in {1, 2, 3, 4}:
        raise ValueError("ICUType must be one of 1, 2, 3, or 4")
    gender = static["Gender"]
    if gender not in {0, 1, -1, None}:
        raise ValueError("Gender must be 0, 1, -1, or null")

    rows = ["Time,Parameter,Value", "00:00,RecordID,1"]
    for parameter in STATIC_VARIABLES:
        value = static[parameter]
        rows.append(f"00:00,{parameter},{-1 if value is None else value}")
    for index, measurement in enumerate(measurements):
        if not isinstance(measurement, dict) or set(measurement) != {"time", "parameter", "value"}:
            raise ValueError(f"measurement {index} must contain time, parameter, and value")
        parameter = str(measurement["parameter"])
        if parameter != measurement["parameter"] or any(
            character in parameter for character in (",", "\r", "\n")
        ):
            raise ValueError(f"measurement {index} parameter must be a plain string")
        canonical = PARAMETER_ALIASES.get(parameter, parameter)
        if parameter in OUTCOME_COLUMNS or canonical in OUTCOME_COLUMNS:
            raise ValueError("outcome-related fields are forbidden at inference")
        if canonical not in VARIABLE_INDEX:
            raise ValueError(f"unknown dynamic parameter: {parameter}")
        timestamp = measurement["time"]
        if not isinstance(timestamp, str) or any(
            character in timestamp for character in (",", "\r", "\n")
        ):
            raise ValueError(f"measurement {index} time must be a plain timestamp string")
        timestamp_to_bin(timestamp)
        value = _finite_number(measurement["value"], field=f"measurement {index} value")
        rows.append(f"{timestamp},{parameter},{value}")
    return parse_record(StringIO("\n".join(rows) + "\n"))
