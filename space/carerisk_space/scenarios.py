"""Fixed synthetic evidence-gate states for the public explorer."""

from html import escape

from .contracts import ScenarioViewModel

SCENARIOS: tuple[ScenarioViewModel, ...] = (
    ScenarioViewModel(
        id="synthetic_evidence_available",
        label_zh_tw="Synthetic A｜所有示意 evidence gates 通過",
        state="evidence available",
        reason_zh_tw="所有示意 evidence gates 均通過；此狀態不產生分數。",
        schema_contract=True,
        measurement_coverage=True,
        value_pattern=True,
    ),
    ScenarioViewModel(
        id="synthetic_schema_withheld",
        label_zh_tw="Synthetic B｜schema contract 不完整",
        state="evidence withheld",
        reason_zh_tw="示意 schema contract 未通過，因此研究 evidence 不顯示。",
        schema_contract=False,
        measurement_coverage=True,
        value_pattern=True,
    ),
    ScenarioViewModel(
        id="synthetic_coverage_withheld",
        label_zh_tw="Synthetic C｜measurement coverage 不足",
        state="evidence withheld",
        reason_zh_tw="示意 measurement coverage 不足，因此研究 evidence 不顯示。",
        schema_contract=True,
        measurement_coverage=False,
        value_pattern=True,
    ),
    ScenarioViewModel(
        id="synthetic_value_pattern_withheld",
        label_zh_tw="Synthetic D｜value pattern 超出 synthetic reference",
        state="evidence withheld",
        reason_zh_tw="示意 value pattern 超出 synthetic reference，因此研究 evidence 不顯示。",
        schema_contract=True,
        measurement_coverage=True,
        value_pattern=False,
    ),
)

SCENARIO_IDS: tuple[str, ...] = tuple(item.id for item in SCENARIOS)

UNKNOWN_SCENARIO = ScenarioViewModel(
    id="unknown_synthetic_scenario",
    label_zh_tw="Unknown synthetic scenario",
    state="evidence withheld",
    reason_zh_tw="unknown_synthetic_scenario",
    schema_contract=False,
    measurement_coverage=False,
    value_pattern=False,
)


def select_scenario(value: object) -> ScenarioViewModel:
    """Return an exact fixed scenario, or the bounded fail-closed state."""

    if type(value) is not str:
        return UNKNOWN_SCENARIO
    for scenario in SCENARIOS:
        if value == scenario.id:
            return scenario
    return UNKNOWN_SCENARIO


def _bounded_escape(value: str, limit: int) -> str:
    return escape(value[:limit], quote=True)


def render_bounded_scenario_html(scenario: ScenarioViewModel) -> str:
    """Render only bounded, escaped scenario fields and fixed gate statuses."""

    scenario_id = _bounded_escape(scenario.id, 128)
    label = _bounded_escape(scenario.label_zh_tw, 256)
    state = _bounded_escape(scenario.state, 64)
    reason = _bounded_escape(scenario.reason_zh_tw, 512)
    gate_values = (
        ("schema_contract", scenario.schema_contract),
        ("measurement_coverage", scenario.measurement_coverage),
        ("value_pattern", scenario.value_pattern),
    )
    gates = "".join(
        f"<li>{name}: {'pass' if enabled else 'withheld'}</li>"
        for name, enabled in gate_values
    )
    return (
        f'<article class="scenario-state" data-scenario-id="{scenario_id}">'
        f"<h3>{state}</h3>"
        f'<p class="scenario-label">{label}</p>'
        f"<p>{reason}</p>"
        f'<ul aria-label="synthetic evidence gates">{gates}</ul>'
        "</article>"
    )


def render_scenario(value: object) -> str:
    """Render one exact scenario ID without coercing or echoing other input."""

    return render_bounded_scenario_html(select_scenario(value))
