from __future__ import annotations

import pytest

from carerisk48h.constants import VARIABLE_INDEX
from carerisk48h.schema import validate_inference_payload


def _payload() -> dict[str, object]:
    return {
        "static": {"Age": 70, "Gender": 1, "Height": 175, "ICUType": 2, "Weight": 80},
        "measurements": [
            {"time": "00:30", "parameter": "HR", "value": 88},
            {"time": "01:00", "parameter": "TroponinI", "value": 0.2},
        ],
    }


def test_valid_inference_payload_uses_parser_contract() -> None:
    stay = validate_inference_payload(_payload())
    assert stay.values[0, VARIABLE_INDEX["HR"]] == pytest.approx(88)
    assert stay.values[1, VARIABLE_INDEX["TropI"]] == pytest.approx(0.2)


def test_inference_payload_rejects_outcome_fields() -> None:
    payload = _payload()
    payload["measurements"] = [{"time": "00:30", "parameter": "In-hospital_death", "value": 1}]
    with pytest.raises(ValueError, match="outcome-related"):
        validate_inference_payload(payload)


def test_inference_payload_rejects_invalid_timestamp() -> None:
    payload = _payload()
    payload["measurements"] = [{"time": "48:01", "parameter": "HR", "value": 88}]
    with pytest.raises(ValueError, match="outside first 48 hours"):
        validate_inference_payload(payload)


def test_inference_payload_rejects_non_numeric_and_csv_injection() -> None:
    payload = _payload()
    payload["measurements"] = [{"time": "00:30", "parameter": "HR", "value": "88"}]
    with pytest.raises(ValueError, match="finite number"):
        validate_inference_payload(payload)
    payload = _payload()
    payload["measurements"] = [{"time": "00:30", "parameter": "HR\nIn-hospital_death", "value": 1}]
    with pytest.raises(ValueError, match="plain string"):
        validate_inference_payload(payload)
