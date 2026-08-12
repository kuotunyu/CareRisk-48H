"""Gradio dashboard with fail-closed risk display."""

from __future__ import annotations

import argparse
import html
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from carerisk48h.constants import VARIABLE_INDEX
from carerisk48h.data.quality import stay_quality_features
from carerisk48h.demo import build_synthetic_demo_bundle, synthetic_payload
from carerisk48h.inference import predict_stay
from carerisk48h.schema import validate_inference_payload

_TREND_VARIABLES = ("HR", "RespRate", "Temp", "NIMAP", "SaO2")

_APP_CSS = """
:root {
    --cr-canvas: #F4F7FA;
    --cr-surface: #FFFFFF;
    --cr-ink: #102A43;
    --cr-navy: #082B4C;
    --cr-teal: #087F8C;
    --cr-amber: #A16207;
    --cr-border: #CAD5E0;
    --cr-muted: #52677A;
    --cr-invalid: #B42318;
    --cr-body: 16px;
    --cr-label: 14px;
    --cr-code: 13px;
}

html,
body {
    background: var(--cr-canvas);
    color: var(--cr-ink);
    overflow-x: hidden;
}

.gradio-container {
    background: var(--cr-canvas) !important;
    color: var(--cr-ink) !important;
    font-family: "Segoe UI Variable", "Segoe UI", system-ui, sans-serif !important;
    font-size: var(--cr-body) !important;
    line-height: 1.5;
    margin: 0 auto !important;
    max-width: 1280px !important;
    padding: 20px 24px 28px !important;
    overflow-x: hidden;
}

#cr-header {
    background: var(--cr-navy);
    border-radius: 12px 12px 0 0;
    color: #FFFFFF;
    margin: 0 !important;
    padding: 20px 24px;
}

.cr-header {
    align-items: end;
    display: flex;
    gap: 24px;
    justify-content: space-between;
}

.cr-eyebrow,
.cr-step {
    color: var(--cr-teal);
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.08em;
    margin: 0 0 6px;
    text-transform: uppercase;
}

.cr-header .cr-eyebrow {
    color: #8FDBE0;
}

.cr-header h1 {
    color: #FFFFFF;
    font-size: clamp(30px, 3vw, 36px);
    letter-spacing: -0.025em;
    line-height: 1.12;
    margin: 0;
}

.cr-value-line {
    color: #D9E5EE;
    font-size: 16px;
    margin: 7px 0 0;
    max-width: 52rem;
}

.cr-notice {
    align-items: center;
    display: flex;
    flex: 0 1 34rem;
    font-size: 15px;
    gap: 10px;
    justify-content: flex-end;
    text-align: right;
}

.cr-notice__icon {
    align-items: center;
    border: 2px solid #8FDBE0;
    border-radius: 50%;
    color: #8FDBE0;
    display: inline-flex;
    flex: 0 0 24px;
    font-size: 14px;
    font-weight: 800;
    height: 24px;
    justify-content: center;
}

#cr-console {
    background: var(--cr-surface);
    border: 1px solid var(--cr-border);
    border-radius: 0 0 12px 12px;
    display: grid !important;
    gap: 0 !important;
    grid-template-columns: minmax(0, 38fr) minmax(0, 62fr);
    margin: 0 0 20px !important;
    overflow: hidden;
}

#cr-scenario,
#cr-result {
    min-width: 0 !important;
    padding: 20px 24px;
}

#cr-result {
    border-left: 1px solid var(--cr-border);
}

.cr-scenario-summary h2,
.cr-state h2,
.cr-contributors h2 {
    color: var(--cr-ink);
    font-size: clamp(21px, 2vw, 24px);
    line-height: 1.25;
    margin: 0 0 12px;
}

.cr-evidence-list,
.cr-guard-summary {
    border-bottom: 1px solid var(--cr-border);
    border-top: 1px solid var(--cr-border);
}

.cr-evidence-row {
    align-items: baseline;
    border-bottom: 1px solid #E4EAF0;
    display: flex;
    font-size: 15px;
    gap: 16px;
    justify-content: space-between;
    min-height: 42px;
    padding: 9px 2px;
}

.cr-evidence-row:last-child {
    border-bottom: 0;
}

.cr-evidence-row span {
    color: var(--cr-muted);
}

.cr-evidence-row strong {
    color: var(--cr-ink);
    font-weight: 650;
    text-align: right;
}

#cr-run {
    background: var(--cr-navy) !important;
    border: 2px solid var(--cr-navy) !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    margin-top: 16px !important;
    min-height: 44px;
}

#cr-run:hover {
    background: #0D416E !important;
}

#cr-run:focus-visible {
    box-shadow: 0 0 0 4px rgb(8 127 140 / 28%) !important;
    outline: 2px solid var(--cr-teal) !important;
    outline-offset: 2px;
}

.label-wrap,
.block-info,
label span {
    font-size: 14px !important;
}

#cr-payload .cm-editor,
#cr-payload pre,
#cr-payload code {
    font-size: var(--cr-code) !important;
    line-height: 1.5 !important;
}

#cr-payload .cm-editor,
#cr-payload pre {
    max-height: 24rem;
    overflow: auto;
}

.cr-state {
    min-height: 100%;
}

.cr-state > p {
    font-size: 16px;
}

.cr-status-line {
    align-items: center;
    border: 1px solid var(--cr-teal);
    border-radius: 8px;
    color: #075D66;
    display: flex;
    font-size: 16px;
    font-weight: 700;
    gap: 10px;
    margin-bottom: 16px;
    padding: 10px 12px;
}

.cr-status-line span {
    align-items: center;
    border: 2px solid currentColor;
    border-radius: 50%;
    display: inline-flex;
    height: 24px;
    justify-content: center;
    width: 24px;
}

.cr-state--review {
    border-left: 4px solid var(--cr-amber);
    padding-left: 16px;
}

.cr-state--invalid {
    border-left: 4px solid var(--cr-invalid);
    padding-left: 16px;
}

.cr-score {
    color: var(--cr-teal);
    font-size: clamp(42px, 6vw, 64px) !important;
    font-variant-numeric: tabular-nums;
    font-weight: 750;
    letter-spacing: -0.04em;
    line-height: 1;
    margin: 0 0 8px;
}

.cr-score-note,
.cr-section-note,
.cr-boundary {
    color: var(--cr-muted);
}

.cr-step--output {
    margin-top: 20px;
}

.cr-operating-point {
    margin: 16px 0;
}

.cr-operating-point__label {
    font-size: 15px;
    margin-bottom: 8px;
}

.cr-operating-point__track {
    background: #D9E3EA;
    height: 4px;
    position: relative;
}

.cr-operating-point__track span {
    background: var(--cr-teal);
    border: 3px solid var(--cr-surface);
    border-radius: 50%;
    box-shadow: 0 0 0 1px var(--cr-teal);
    height: 16px;
    position: absolute;
    top: 50%;
    transform: translate(-50%, -50%);
    width: 16px;
}

.cr-reasons {
    color: var(--cr-ink);
    font-size: 15px;
    margin: 12px 0;
    padding-left: 22px;
}

#cr-analysis {
    display: grid !important;
    gap: 20px !important;
    grid-template-columns: minmax(0, 3fr) minmax(20rem, 2fr);
    margin-bottom: 20px !important;
}

#cr-trend,
#cr-contributors {
    background: var(--cr-surface);
    border: 1px solid var(--cr-border);
    border-radius: 10px;
    min-width: 0 !important;
    padding: 16px;
}

.cr-contributors table {
    border-collapse: collapse;
    font-size: 14px;
    width: 100%;
}

.cr-contributors th,
.cr-contributors td {
    border-bottom: 1px solid #E4EAF0;
    padding: 9px 6px;
    text-align: left;
}

.cr-contributors th {
    color: var(--cr-muted);
    font-size: 14px;
    font-weight: 700;
}

.cr-contributors code {
    background: transparent;
    color: var(--cr-ink);
    font-size: 13px;
    overflow-wrap: anywhere;
}

.cr-rank,
.cr-number {
    font-variant-numeric: tabular-nums;
}

.cr-number {
    text-align: right !important;
}

#cr-advanced {
    background: var(--cr-surface);
    border: 1px solid var(--cr-border) !important;
    border-radius: 10px !important;
}

#cr-advanced > button,
#cr-scenario .wrap > button {
    font-size: 16px !important;
    min-height: 44px;
}

@media (max-width: 719px) {
    .gradio-container {
        padding: 12px !important;
    }

    .cr-header {
        align-items: flex-start;
        flex-direction: column;
        gap: 12px;
    }

    .cr-notice {
        flex: 1 1 auto;
        justify-content: flex-start;
        text-align: left;
    }

    #cr-console,
    #cr-analysis {
        grid-template-columns: minmax(0, 1fr);
    }

    #cr-result {
        border-left: 0;
        border-top: 1px solid var(--cr-border);
    }

    #cr-scenario,
    #cr-result {
        padding: 18px 16px;
    }

    .cr-evidence-row {
        align-items: flex-start;
        flex-direction: column;
        gap: 2px;
    }

    .cr-evidence-row strong {
        text-align: left;
    }

    .cr-score {
        font-size: 44px !important;
    }
}
"""

_ZH_TW_HEAD = f"""
<style>
{_APP_CSS}
</style>
<script>
document.documentElement.lang = "zh-TW";
</script>
"""


def _header_html() -> str:
    return (
        '<header class="cr-header">'
        '<div class="cr-header__identity">'
        '<p class="cr-eyebrow">SYNTHETIC RESEARCH DEMO</p>'
        "<h1>CareRisk 48H</h1>"
        '<p class="cr-value-line">展示 schema validation、evidence gates、calibration 與 '
        "abstention 的可稽核研究流程。</p>"
        "</div>"
        '<div class="cr-notice" role="note">'
        '<span class="cr-notice__icon" aria-hidden="true">i</span>'
        "<span>僅使用 synthetic data｜僅供研究與教育｜不得用於臨床決策</span>"
        "</div>"
        "</header>"
    )


def _ready_html() -> str:
    return (
        '<section class="cr-state cr-state--ready" role="status">'
        '<p class="cr-step">02 · evidence gates</p>'
        "<h2>等待執行 synthetic case</h2>"
        "<p>執行後會先檢查輸入與 evidence gates，再決定是否顯示研究輸出。</p>"
        '<p class="cr-boundary">僅供研究與教育，不得用於臨床決策。</p>'
        "</section>"
    )


def _scenario_html(stay: Any) -> str:
    quality = stay_quality_features(stay)
    measurement_count = int(quality["measurement_count"])
    coverage = 100.0 * float(quality["dynamic_variable_coverage"])
    vital_groups = int(quality["core_vital_groups"])
    rows = (
        ("觀察窗", "48 小時"),
        ("measurement 數量", f"{measurement_count:,}"),
        ("coverage", f"{coverage:.1f}%"),
        ("core vital groups", f"{vital_groups} / 5"),
        ("fixture 類型", "synthetic fixture"),
    )
    rendered_rows = "".join(
        '<div class="cr-evidence-row">'
        f"<span>{html.escape(label)}</span>"
        f"<strong>{html.escape(value)}</strong>"
        "</div>"
        for label, value in rows
    )
    return (
        '<section class="cr-scenario-summary">'
        '<p class="cr-step">01 · synthetic fixture</p>'
        "<h2>合成 48 小時案例</h2>"
        f'<div class="cr-evidence-list">{rendered_rows}</div>'
        "</section>"
    )


@dataclass(frozen=True)
class DashboardEvaluation:
    figure: Any | None
    result_html: str
    contributors_html: str
    guard_json: dict[str, Any]
    machine_output: dict[str, Any]
    show_trend: bool
    show_contributors: bool


def _guard_summary_html(guard: dict[str, Any]) -> str:
    quality = guard.get("quality")
    quality_map = quality if isinstance(quality, dict) else {}
    reasons = guard.get("reasons")
    reason_list = reasons if isinstance(reasons, list) else []
    allowed = bool(guard.get("allow_probability", False))
    coverage = quality_map.get("dynamic_variable_coverage")
    measurement_count = quality_map.get("measurement_count")
    vital_groups = quality_map.get("core_vital_groups")
    guard_available = bool(guard.get("value_pattern_guard_available", False))
    rows = (
        ("schema validation", "通過"),
        (
            "coverage",
            f"{100.0 * float(coverage):.1f}%" if coverage is not None else "未提供",
        ),
        (
            "measurement 數量",
            f"{int(measurement_count):,}" if measurement_count is not None else "未提供",
        ),
        (
            "core vital groups",
            f"{int(vital_groups)} / 5" if vital_groups is not None else "未提供",
        ),
        ("value-pattern guard", "可用" if guard_available else "不可用"),
        ("review required", "否" if allowed else "是"),
    )
    rendered_rows = "".join(
        '<div class="cr-evidence-row">'
        f"<span>{html.escape(label)}</span>"
        f"<strong>{html.escape(value)}</strong>"
        "</div>"
        for label, value in rows
    )
    rendered_reasons = "".join(f"<li>{html.escape(str(reason))}</li>" for reason in reason_list)
    reasons_html = f'<ul class="cr-reasons">{rendered_reasons}</ul>' if rendered_reasons else ""
    return f'<div class="cr-guard-summary">{rendered_rows}{reasons_html}</div>'


def _result_html(result: Any) -> str:
    guard_html = _guard_summary_html(dict(result.guard))
    if not result.allow_probability:
        return (
            '<section class="cr-state cr-state--review" role="status">'
            '<p class="cr-step">02 · evidence gates</p>'
            "<h2>需要人工複核</h2>"
            '<p class="cr-status-copy">已觸發 abstention，精確機率不會顯示。</p>'
            f"{guard_html}"
            '<p class="cr-boundary">這是 research safety state，不是臨床判斷。</p>'
            "</section>"
        )
    score = float(result.calibrated_probability)
    threshold = float(result.threshold)
    marker = max(0.0, min(100.0, 100.0 * threshold))
    comparison = "高於" if bool(result.above_threshold) else "低於"
    return (
        '<section class="cr-state cr-state--available" role="status">'
        '<p class="cr-step">02 · evidence gates</p>'
        '<div class="cr-status-line"><span aria-hidden="true">✓</span>'
        "evidence gates 已通過，研究輸出可顯示</div>"
        f"{guard_html}"
        '<p class="cr-step cr-step--output">03 · 研究輸出</p>'
        "<h2>合成示範分數</h2>"
        f'<p class="cr-score">{score:.3f}</p>'
        '<p class="cr-score-note">這是 demonstration value，不是臨床確定性。</p>'
        '<div class="cr-operating-point">'
        '<div class="cr-operating-point__label">'
        f"research operating point <strong>{threshold:.3f}</strong>；本次分數{comparison}該位置"
        "</div>"
        '<div class="cr-operating-point__track" aria-hidden="true">'
        f'<span style="left: {marker:.1f}%"></span>'
        "</div>"
        "</div>"
        '<p class="cr-boundary">僅供研究與教育，不得用於臨床決策。</p>'
        "</section>"
    )


def _contributors_html(contributors: list[dict[str, float | str]]) -> str:
    rows = []
    for rank, item in enumerate(contributors, start=1):
        feature = html.escape(str(item.get("feature", "未提供")))
        contribution = float(item.get("contribution", 0.0))
        rows.append(
            "<tr>"
            f'<td class="cr-rank">{rank}</td>'
            f"<td><code>{feature}</code></td>"
            f'<td class="cr-number">{contribution:+.3f}</td>'
            "</tr>"
        )
    rendered_rows = "".join(rows)
    return (
        '<section class="cr-contributors">'
        "<h2>model signals</h2>"
        '<p class="cr-section-note">描述性、非因果；數值不代表 care action。</p>'
        "<table><thead><tr><th>順位</th><th>feature</th><th>contribution</th></tr></thead>"
        f"<tbody>{rendered_rows}</tbody></table>"
        "</section>"
    )


def _trend_figure(stay: Any) -> Any:
    figure, axes = plt.subplots(len(_TREND_VARIABLES), 1, figsize=(10, 8), sharex=True)
    hours = np.arange(48)
    for axis, variable in zip(axes, _TREND_VARIABLES, strict=True):
        column = VARIABLE_INDEX[variable]
        observed = stay.mask[:, column]
        axis.plot(hours[observed], stay.values[observed, column], marker="o", linewidth=1)
        axis.set_ylabel(variable)
        axis.grid(alpha=0.2)
    axes[-1].set_xlabel("Hour bin")
    figure.suptitle("48-hour measurements (gaps are missing bins)")
    figure.tight_layout()
    return figure


def _evaluate(payload_text: str, bundle: dict[str, Any]) -> DashboardEvaluation:
    try:
        payload = json.loads(payload_text)
        stay = validate_inference_payload(payload)
        result = predict_stay(bundle, stay)
    except Exception as exc:
        error = html.escape(str(exc))
        return DashboardEvaluation(
            figure=None,
            result_html=(
                '<section class="cr-state cr-state--invalid" role="alert">'
                '<p class="cr-step">02 · evidence gates</p>'
                "<h2>輸入格式無效</h2>"
                f"<p>{error}</p>"
                '<p class="cr-boundary">請修正 synthetic JSON 後再試一次；未產生研究輸出。</p>'
                "</section>"
            ),
            contributors_html="",
            guard_json={"schema_error": str(exc)},
            machine_output={"state": "invalid_input"},
            show_trend=False,
            show_contributors=False,
        )
    serialized = asdict(result)
    return DashboardEvaluation(
        figure=_trend_figure(stay),
        result_html=_result_html(result),
        contributors_html=_contributors_html(result.contributors),
        guard_json=dict(serialized["guard"]),
        machine_output=serialized,
        show_trend=True,
        show_contributors=bool(result.contributors),
    )


def create_app(bundle_path: str | Path | None = None) -> Any:
    try:
        import gradio as gr
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install CareRisk 48H with the 'app' extra") from exc
    path = Path(bundle_path) if bundle_path else Path("artifacts/demo/synthetic_demo_bundle.joblib")
    if not path.exists():
        build_synthetic_demo_bundle(path)
    bundle = joblib.load(path)
    fixture_payload = synthetic_payload(index=0)
    fixture = json.dumps(fixture_payload, indent=2, ensure_ascii=False)
    default_stay = validate_inference_payload(fixture_payload)

    def run_synthetic_case(text: str) -> tuple[Any, ...]:
        view = _evaluate(text, bundle)
        return (
            view.result_html,
            gr.update(value=view.figure, visible=view.show_trend),
            gr.update(value=view.contributors_html, visible=view.show_contributors),
            view.guard_json,
            view.machine_output,
        )

    with gr.Blocks(
        title="CareRisk 48H — Synthetic Research Demo",
        fill_width=True,
    ) as application:
        gr.HTML(_header_html(), elem_id="cr-header", head=_ZH_TW_HEAD)
        with gr.Row(elem_id="cr-console"):
            with gr.Column(scale=38, elem_id="cr-scenario"):
                gr.HTML(_scenario_html(default_stay))
                run = gr.Button("執行 synthetic case", variant="primary", elem_id="cr-run")
                with gr.Accordion("檢視或編輯 synthetic JSON", open=False):
                    payload = gr.Code(
                        label="48H synthetic JSON payload",
                        value=fixture,
                        language="json",
                        elem_id="cr-payload",
                    )
            with gr.Column(scale=62, elem_id="cr-result"):
                result = gr.HTML(_ready_html(), elem_id="cr-result-state")
        with gr.Row(elem_id="cr-analysis"):
            trend = gr.Plot(
                label="48 小時 trends（缺口代表 missing bins）",
                show_label=True,
                visible=False,
                elem_id="cr-trend",
            )
            contributors = gr.HTML(visible=False, elem_id="cr-contributors")
        with gr.Accordion("進階稽核資訊", open=False, elem_id="cr-advanced"), gr.Row():
            guard = gr.JSON(label="guard", elem_id="cr-guard-json")
            machine_output = gr.JSON(label="machine output", elem_id="cr-machine-output")
        run.click(
            fn=run_synthetic_case,
            inputs=payload,
            outputs=[result, trend, contributors, guard, machine_output],
        )
    return application


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--server-port", type=int, default=7860)
    args = parser.parse_args()
    create_app(args.bundle).launch(server_name="0.0.0.0", server_port=args.server_port)


if __name__ == "__main__":
    main()
