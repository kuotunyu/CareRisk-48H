import json
import re
from dataclasses import FrozenInstanceError, asdict, fields

import pytest
from carerisk_space.contracts import ScenarioViewModel
from carerisk_space.scenarios import (
    SCENARIO_IDS,
    SCENARIOS,
    UNKNOWN_SCENARIO,
    render_bounded_scenario_html,
    render_scenario,
    select_scenario,
)

EXPECTED_IDS = (
    "synthetic_evidence_available",
    "synthetic_schema_withheld",
    "synthetic_coverage_withheld",
    "synthetic_value_pattern_withheld",
)

EXPECTED_SCENARIOS = (
    (
        "synthetic_evidence_available",
        "Synthetic A｜所有示意 evidence gates 通過",
        "evidence available",
        "所有示意 evidence gates 均通過；此狀態不產生分數。",
        True,
        True,
        True,
    ),
    (
        "synthetic_schema_withheld",
        "Synthetic B｜schema contract 不完整",
        "evidence withheld",
        "示意 schema contract 未通過，因此研究 evidence 不顯示。",
        False,
        True,
        True,
    ),
    (
        "synthetic_coverage_withheld",
        "Synthetic C｜measurement coverage 不足",
        "evidence withheld",
        "示意 measurement coverage 不足，因此研究 evidence 不顯示。",
        True,
        False,
        True,
    ),
    (
        "synthetic_value_pattern_withheld",
        "Synthetic D｜value pattern 超出 synthetic reference",
        "evidence withheld",
        "示意 value pattern 超出 synthetic reference，因此研究 evidence 不顯示。",
        True,
        True,
        False,
    ),
)


def _scenario_values(scenario: ScenarioViewModel) -> tuple[object, ...]:
    return tuple(getattr(scenario, field.name) for field in fields(scenario))


def test_registry_contains_only_four_exact_abstract_scenarios() -> None:
    assert isinstance(SCENARIOS, tuple)
    assert SCENARIO_IDS == EXPECTED_IDS
    assert tuple(item.id for item in SCENARIOS) == SCENARIO_IDS
    assert tuple(_scenario_values(item) for item in SCENARIOS) == EXPECTED_SCENARIOS
    assert UNKNOWN_SCENARIO not in SCENARIOS

    serialized = json.dumps([asdict(item) for item in SCENARIOS], ensure_ascii=False)
    for prohibited in (
        "probability",
        "score",
        "threshold",
        "risk class",
        "recommendation",
        "patient",
        "case feature",
        "age",
        "gender",
        "record",
        "outcome",
    ):
        assert re.search(rf"\b{re.escape(prohibited)}\b", serialized.lower()) is None


def test_scenario_view_models_are_frozen_and_have_only_approved_fields() -> None:
    assert tuple(field.name for field in fields(ScenarioViewModel)) == (
        "id",
        "label_zh_tw",
        "state",
        "reason_zh_tw",
        "schema_contract",
        "measurement_coverage",
        "value_pattern",
    )
    with pytest.raises(FrozenInstanceError):
        SCENARIOS[0].state = "evidence withheld"  # type: ignore[misc]


def test_available_state_has_all_gates_and_explicitly_produces_no_number() -> None:
    available = select_scenario(EXPECTED_IDS[0])
    assert available.state == "evidence available"
    assert (
        available.schema_contract,
        available.measurement_coverage,
        available.value_pattern,
    ) == (True, True, True)
    assert available.reason_zh_tw == "所有示意 evidence gates 均通過；此狀態不產生分數。"


@pytest.mark.parametrize(
    ("scenario_id", "expected_gates", "expected_reason"),
    [
        (
            EXPECTED_IDS[1],
            (False, True, True),
            "示意 schema contract 未通過，因此研究 evidence 不顯示。",
        ),
        (
            EXPECTED_IDS[2],
            (True, False, True),
            "示意 measurement coverage 不足，因此研究 evidence 不顯示。",
        ),
        (
            EXPECTED_IDS[3],
            (True, True, False),
            "示意 value pattern 超出 synthetic reference，因此研究 evidence 不顯示。",
        ),
    ],
)
def test_each_withheld_state_changes_exactly_one_gate_and_uses_bounded_reason(
    scenario_id: str,
    expected_gates: tuple[bool, bool, bool],
    expected_reason: str,
) -> None:
    scenario = select_scenario(scenario_id)
    assert scenario.state == "evidence withheld"
    assert (
        scenario.schema_contract,
        scenario.measurement_coverage,
        scenario.value_pattern,
    ) == expected_gates
    assert scenario.reason_zh_tw == expected_reason


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "unknown",
        "synthetic_evidence_available ",
        "SYNTHETIC_EVIDENCE_AVAILABLE",
        "<img src=x onerror=alert(1)>",
        pytest.param("x" * 1_048_576, id="one-mebibyte-string"),
        [],
        {},
        {"id": EXPECTED_IDS[0]},
        1,
        True,
    ],
)
def test_adversarial_callback_fails_closed_without_coercion_or_echo(value: object) -> None:
    selected = select_scenario(value)
    html = render_scenario(value)
    assert selected is UNKNOWN_SCENARIO
    assert html == render_scenario(None)
    assert "unknown_synthetic_scenario" in html
    assert "evidence withheld" in html
    if str(value) and str(value) != "unknown":
        assert str(value) not in html


def test_bounded_renderer_escapes_every_text_field() -> None:
    hostile = ScenarioViewModel(
        id='<script id="hostile">',
        label_zh_tw="<b>label</b>",
        state="evidence withheld",
        reason_zh_tw='<img src="x" onerror="alert(1)">',
        schema_contract=False,
        measurement_coverage=True,
        value_pattern=False,
    )
    html = render_bounded_scenario_html(hostile)
    assert "<script" not in html
    assert "<b>label</b>" not in html
    assert "<img" not in html
    assert "&lt;script id=&quot;hostile&quot;&gt;" in html
    assert "&lt;b&gt;label&lt;/b&gt;" in html
    assert "&lt;img src=&quot;x&quot; onerror=&quot;alert(1)&quot;&gt;" in html
    assert len(html) < 2_048


def test_registry_rendering_is_fixed_bounded_and_contains_only_gate_statuses() -> None:
    for scenario_id in EXPECTED_IDS:
        html = render_scenario(scenario_id)
        assert len(html) < 2_048
        assert html.count("<li>") == 3
        assert all(
            gate in html
            for gate in ("schema_contract", "measurement_coverage", "value_pattern")
        )
        assert "pass" in html
        assert scenario_id in html
