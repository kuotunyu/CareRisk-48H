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
from carerisk48h.inference import DISCLAIMER, predict_stay
from carerisk48h.schema import validate_inference_payload

_TREND_VARIABLES = ("HR", "RespRate", "Temp", "NIMAP", "SaO2")


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


def _legacy_outputs(view: DashboardEvaluation) -> tuple[Any, ...]:
    machine = view.machine_output
    if not bool(machine.get("allow_probability", False)):
        raw = calibrated = threshold = "未顯示"
    else:
        raw = f"{float(machine['raw_probability']):.3f}"
        calibrated = f"{float(machine['calibrated_probability']):.3f}"
        threshold = (
            f"{float(machine['threshold']):.3f}；above threshold={bool(machine['above_threshold'])}"
        )
    contributors = machine.get("contributors")
    return (
        view.figure,
        view.result_html,
        raw,
        calibrated,
        threshold,
        contributors if isinstance(contributors, list) else [],
        view.guard_json,
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
    fixture = json.dumps(synthetic_payload(index=0), indent=2, ensure_ascii=False)
    with gr.Blocks(title="CareRisk 48H") as application:
        gr.Markdown(
            "# CareRisk 48H\n"
            f"**{DISCLAIMER}。** 本頁預設使用完全合成的 smoke fixture；機率不可視為臨床結果。"
        )
        payload = gr.Code(label="48H JSON payload", value=fixture, language="json")
        run = gr.Button("執行安全檢查與研究推論", variant="primary")
        status = gr.Markdown()
        with gr.Row():
            raw = gr.Textbox(label="Raw risk", interactive=False)
            calibrated = gr.Textbox(label="Calibrated probability", interactive=False)
            threshold = gr.Textbox(label="Decision threshold", interactive=False)
        trend = gr.Plot(label="48-hour trend and missingness")
        with gr.Row():
            contributors = gr.JSON(label="主要 contributing features（非因果）")
            guard = gr.JSON(label="Missingness / OOD guard")
        run.click(
            fn=lambda text: _legacy_outputs(_evaluate(text, bundle)),
            inputs=payload,
            outputs=[trend, status, raw, calibrated, threshold, contributors, guard],
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
