from __future__ import annotations

from app.dashboard import (
    _contributors_html,
    _evaluate,
    _legacy_outputs,
    _ready_html,
    _result_html,
    _scenario_html,
)
from carerisk48h.demo import synthetic_payload
from carerisk48h.inference import SafePrediction
from carerisk48h.schema import validate_inference_payload


def test_ready_state_is_zh_tw_and_explains_evidence_sequence() -> None:
    html = _ready_html()
    assert "等待執行 synthetic case" in html
    assert "evidence gates" in html
    assert "臨床" in html
    assert "1.000" not in html


def test_scenario_summary_is_derived_from_validated_fixture() -> None:
    stay = validate_inference_payload(synthetic_payload(index=0))
    html = _scenario_html(stay)
    assert "48 小時" in html
    assert "synthetic fixture" in html
    assert "measurement" in html
    assert "coverage" in html


def _prediction(*, allowed: bool) -> SafePrediction:
    return SafePrediction(
        allow_probability=allowed,
        requires_human_review=not allowed,
        message="synthetic test result",
        raw_probability=0.48 if allowed else None,
        calibrated_probability=0.62 if allowed else None,
        threshold=0.30 if allowed else None,
        above_threshold=True if allowed else None,
        contributors=[{"feature": "HR_mean", "contribution": 0.2}] if allowed else [],
        guard={
            "allow_probability": allowed,
            "requires_human_review": not allowed,
            "reasons": [] if allowed else ["value pattern exceeds train-derived range"],
            "quality": {
                "dynamic_variable_coverage": 0.75,
                "measurement_count": 120,
                "core_vital_groups": 4,
            },
            "ood_score": -0.1,
            "value_pattern_guard_available": True,
            "value_shift_score": 1.2,
        },
    )


def test_allowed_state_uses_research_language() -> None:
    html = _result_html(_prediction(allowed=True))
    assert "合成示範分數" in html
    assert "0.620" in html
    assert "research operating point" in html
    assert "不是臨床確定性" in html


def test_abstention_hides_precise_probability() -> None:
    html = _result_html(_prediction(allowed=False))
    assert "abstention" in html
    assert "需要人工複核" in html
    assert "0.620" not in html
    assert "research operating point" not in html


def test_contributor_names_are_escaped_and_labeled_noncausal() -> None:
    html = _contributors_html([{"feature": "<script>alert(1)</script>", "contribution": -0.25}])
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "描述性、非因果" in html
    assert "-0.250" in html


def test_invalid_input_clears_stale_evidence_and_escapes_error() -> None:
    view = _evaluate('{"static": "<script>alert(1)</script>"}', {})
    assert view.figure is None
    assert view.show_trend is False
    assert view.show_contributors is False
    assert "輸入格式無效" in view.result_html
    assert "<script>" not in view.result_html
    assert "schema_error" in view.guard_json


def test_legacy_adapter_keeps_current_callback_fail_closed() -> None:
    view = _evaluate("{}", {})
    outputs = _legacy_outputs(view)
    assert len(outputs) == 7
    assert outputs[0] is None
    assert outputs[2:5] == ("未顯示", "未顯示", "未顯示")
