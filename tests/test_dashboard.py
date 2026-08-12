from __future__ import annotations

import json

from app.dashboard import (
    _APP_CSS,
    _ZH_TW_HEAD,
    _contributors_html,
    _evaluate,
    _header_html,
    _ready_html,
    _result_html,
    _scenario_html,
    _trend_figure,
    create_app,
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


def test_header_avoids_redundant_eyebrow_and_uses_authored_icon() -> None:
    html = _header_html()
    assert "SYNTHETIC RESEARCH DEMO" not in html
    assert "<svg" in html
    assert "僅使用 synthetic data" in html


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
    assert "✓" not in html
    assert "<svg" in html


def test_allowed_state_groups_guards_before_output_without_changing_abstention() -> None:
    allowed_html = _result_html(_prediction(allowed=True))
    review_html = _result_html(_prediction(allowed=False))

    assert 'class="cr-allowed-layout"' in allowed_html
    assert 'class="cr-allowed-guards"' in allowed_html
    assert 'class="cr-allowed-output"' in allowed_html
    assert allowed_html.index('class="cr-allowed-guards"') < allowed_html.index(
        'class="cr-allowed-output"'
    )
    assert 'class="cr-allowed-layout"' not in review_html


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


def test_create_app_uses_zh_tw_progressive_disclosure(tmp_path, monkeypatch) -> None:
    bundle_path = tmp_path / "synthetic.joblib"
    bundle_path.touch()
    monkeypatch.setattr("app.dashboard.joblib.load", lambda _: {"synthetic": True})

    application = create_app(bundle_path)
    config = json.dumps(application.get_config_file(), ensure_ascii=False)

    assert "執行 synthetic case" in config
    assert "檢視或編輯 synthetic JSON" in config
    assert "進階稽核資訊" in config
    assert "僅使用 synthetic data" in config
    assert "zh-TW" in _ZH_TW_HEAD


def test_css_enforces_readable_compact_responsive_layout() -> None:
    assert "--cr-body: 17px" in _APP_CSS
    assert "--cr-label: 15px" in _APP_CSS
    assert "--cr-code: 14px" in _APP_CSS
    assert "color-scheme: light" in _APP_CSS
    assert "--body-text-color: var(--cr-ink)" in _APP_CSS
    assert "--block-background-fill: var(--cr-surface)" in _APP_CSS
    assert "font-size: 14px" in _APP_CSS
    assert "min-height: 44px" in _APP_CSS
    assert "max-height: 24rem" in _APP_CSS
    assert "grid-template-columns: minmax(0, 38fr) minmax(0, 62fr)" in _APP_CSS
    assert "grid-template-columns: minmax(0, 56fr) minmax(0, 44fr)" in _APP_CSS
    assert "@media (min-width: 1000px)" in _APP_CSS
    assert "@media (max-width: 719px)" in _APP_CSS
    assert "overflow-x: hidden" in _APP_CSS
    assert "#cr-analysis:empty" in _APP_CSS
    assert "border-left: 4px" not in _APP_CSS


def test_trend_figure_uses_readable_label_sizes() -> None:
    stay = validate_inference_payload(synthetic_payload(index=0))
    figure = _trend_figure(stay)
    try:
        assert all(axis.yaxis.label.get_size() >= 11 for axis in figure.axes)
        assert figure.axes[-1].xaxis.label.get_size() >= 11
        assert figure._suptitle is not None
        assert figure._suptitle.get_size() >= 14
    finally:
        figure.clear()
