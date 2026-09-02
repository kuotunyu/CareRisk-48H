from __future__ import annotations

import re
from dataclasses import FrozenInstanceError, fields

import pytest

from carerisk_mvp.content import EVIDENCE_STATES, STATE_IDS, EvidenceState


EXPECTED_STATE_IDS = (
    "evidence_available",
    "evidence_withheld",
    "schema_withheld",
    "provenance_withheld",
)


def _all_text() -> str:
    return " ".join(
        str(getattr(state, field.name))
        for state in EVIDENCE_STATES
        for field in fields(EvidenceState)
    )


def test_registry_exposes_exactly_four_ordered_immutable_states() -> None:
    assert STATE_IDS == EXPECTED_STATE_IDS
    assert isinstance(EVIDENCE_STATES, tuple)
    assert tuple(state.state_id for state in EVIDENCE_STATES) == EXPECTED_STATE_IDS
    assert all(isinstance(state, EvidenceState) for state in EVIDENCE_STATES)

    with pytest.raises(FrozenInstanceError):
        EVIDENCE_STATES[0].label_zh = "changed"  # type: ignore[misc]


def test_registry_is_complete_deterministic_authored_text() -> None:
    snapshot = tuple(
        tuple(getattr(state, field.name) for field in fields(EvidenceState))
        for state in EVIDENCE_STATES
    )
    assert snapshot == tuple(
        tuple(getattr(state, field.name) for field in fields(EvidenceState))
        for state in EVIDENCE_STATES
    )
    assert all(value.strip() == value and value for row in snapshot for value in row)


def test_registry_contains_no_real_record_shapes_or_markup() -> None:
    text = _all_text()
    assert not re.search(r"https?://|www\.|<[^>]+>|\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b", text)
    assert not re.search(r"\b(?:id|mrn|dob)\s*[:=#]", text, re.IGNORECASE)
    assert not re.search(r"\b(?:bpm|mmhg|mg/dl|spo2|celsius)\b", text, re.IGNORECASE)


@pytest.mark.parametrize(
    "forbidden",
    (
        "patient",
        "risk",
        "score",
        "probability",
        "threshold",
        "metric",
        "model",
        "diagnosis",
        "treatment",
        "prognosis",
        "recommendation",
        "clinical validation",
        "病人",
        "患者",
        "風險",
        "分數",
        "機率",
        "閾值",
        "指標",
        "模型",
        "診斷",
        "治療",
        "預後",
        "建議",
        "臨床驗證",
    ),
)
def test_registry_does_not_cross_claim_ceiling(forbidden: str) -> None:
    assert forbidden.casefold() not in _all_text().casefold()
