from __future__ import annotations

from io import StringIO

import numpy as np
import pytest

from carerisk48h.constants import VARIABLE_INDEX
from carerisk48h.data.parser import parse_record, timestamp_to_bin


@pytest.mark.parametrize(
    ("timestamp", "expected_bin", "elapsed"),
    [
        ("00:00", 0, 0.0),
        ("00:59", 0, 59 / 60),
        ("01:00", 1, 1.0),
        ("47:59", 47, 47 + 59 / 60),
        ("48:00", 47, 48.0),
    ],
)
def test_timestamp_boundaries(timestamp: str, expected_bin: int, elapsed: float) -> None:
    actual_bin, actual_elapsed = timestamp_to_bin(timestamp)
    assert actual_bin == expected_bin
    assert actual_elapsed == pytest.approx(elapsed)


@pytest.mark.parametrize("timestamp", ["48:01", "49:00", "01:60", "1:00", "bad"])
def test_timestamp_rejects_out_of_contract_values(timestamp: str) -> None:
    with pytest.raises(ValueError):
        timestamp_to_bin(timestamp)


def test_parser_aggregation_missingness_and_delta() -> None:
    record = StringIO(
        "Time,Parameter,Value\n"
        "00:00,RecordID,123\n"
        "00:00,Age,70\n"
        "00:00,Gender,1\n"
        "00:00,Height,-1\n"
        "00:00,ICUType,3\n"
        "00:00,Weight,80\n"
        "00:40,Weight,82\n"
        "01:10,HR,80\n"
        "01:50,HR,100\n"
        "02:00,Urine,20\n"
        "02:30,Urine,30\n"
        "03:00,MechVent,0\n"
        "03:15,MechVent,1\n"
        "04:00,Temp,-1\n"
        "48:00,HR,70\n"
    )
    stay = parse_record(record)
    assert stay.record_id == 123
    assert np.isnan(stay.static["Height"])
    assert stay.static["Weight"] == 80
    assert stay.values.dtype == np.float32
    assert stay.mask.dtype == np.bool_
    assert stay.delta.dtype == np.float32
    assert stay.values[0, VARIABLE_INDEX["Weight"]] == pytest.approx(82)
    assert stay.values[1, VARIABLE_INDEX["HR"]] == pytest.approx(90)
    assert stay.values[2, VARIABLE_INDEX["Urine"]] == pytest.approx(50)
    assert stay.values[3, VARIABLE_INDEX["MechVent"]] == pytest.approx(1)
    assert not stay.mask[4, VARIABLE_INDEX["Temp"]]
    assert stay.values[47, VARIABLE_INDEX["HR"]] == pytest.approx(70)
    assert stay.delta[0, VARIABLE_INDEX["HR"]] == 1
    assert stay.delta[1, VARIABLE_INDEX["HR"]] == 0
    assert stay.delta[2, VARIABLE_INDEX["HR"]] == 1
    assert stay.delta[47, VARIABLE_INDEX["HR"]] == 0


def test_parser_rejects_outcome_descriptor() -> None:
    record = StringIO("Time,Parameter,Value\n00:00,RecordID,123\n00:00,In-hospital_death,1\n")
    with pytest.raises(ValueError, match="outcome-related"):
        parse_record(record)


def test_parser_normalizes_official_troponin_names() -> None:
    record = StringIO(
        "Time,Parameter,Value\n00:00,RecordID,123\n01:00,TroponinI,0.4\n02:00,TroponinT,0.2\n"
    )
    stay = parse_record(record)
    assert stay.values[1, VARIABLE_INDEX["TropI"]] == pytest.approx(0.4)
    assert stay.values[2, VARIABLE_INDEX["TropT"]] == pytest.approx(0.2)
    assert stay.observations["TropI"] == ((1.0, 0.4),)
    assert stay.observations["TropT"] == ((2.0, 0.2),)


def test_parser_preserves_non_sentinel_negative_outlier() -> None:
    record = StringIO("Time,Parameter,Value\n00:00,RecordID,123\n01:00,Temp,-17.8\n")
    stay = parse_record(record)
    assert stay.mask[1, VARIABLE_INDEX["Temp"]]
    assert stay.values[1, VARIABLE_INDEX["Temp"]] == pytest.approx(-17.8)
