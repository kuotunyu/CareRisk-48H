"""Gradio dashboard with fail-closed risk display."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from carerisk48h.constants import VARIABLE_INDEX
from carerisk48h.demo import build_synthetic_demo_bundle, synthetic_payload
from carerisk48h.inference import DISCLAIMER, predict_stay
from carerisk48h.schema import validate_inference_payload

_TREND_VARIABLES = ("HR", "RespRate", "Temp", "NIMAP", "SaO2")


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


def _evaluate(payload_text: str, bundle: dict[str, Any]) -> tuple[Any, ...]:
    try:
        payload = json.loads(payload_text)
        stay = validate_inference_payload(payload)
        result = predict_stay(bundle, stay)
    except Exception as exc:
        return (
            None,
            "輸入被拒絕",
            "已隱藏",
            "已隱藏",
            "不適用",
            [],
            {"schema_error": str(exc)},
        )
    serialized = asdict(result)
    if not result.allow_probability:
        raw = calibrated = "已隱藏（需要人工複核）"
        threshold = "不適用"
    else:
        raw = f"{result.raw_probability:.3f}"
        calibrated = f"{result.calibrated_probability:.3f}"
        threshold = f"{result.threshold:.3f}；above threshold={result.above_threshold}"
    return (
        _trend_figure(stay),
        result.message,
        raw,
        calibrated,
        threshold,
        result.contributors,
        serialized["guard"],
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
            fn=lambda text: _evaluate(text, bundle),
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
