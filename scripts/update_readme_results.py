"""Update README only from a complete frozen one-time Set B final evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from carerisk48h.formal_results import validate_final_metrics

START = "<!-- RESULTS_START -->"
END = "<!-- RESULTS_END -->"


def _format_interval(item: dict[str, Any]) -> str:
    estimate = item.get("estimate")
    lower = item.get("lower")
    upper = item.get("upper")
    if estimate is None or lower is None or upper is None:
        return "待填"
    return f"{float(estimate):.3f} ({float(lower):.3f}–{float(upper):.3f})"


def update_readme(readme: Path, payload: dict[str, Any]) -> None:
    validate_final_metrics(payload)
    text = readme.read_text(encoding="utf-8")
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError("README result markers must occur exactly once")
    metrics = payload["metrics"]
    intervals = payload["confidence_intervals"]
    sensitivity = metrics["sensitivity"]
    specificity = metrics["specificity"]
    operating = (
        "待填"
        if sensitivity is None or specificity is None
        else f"{float(sensitivity):.3f} @ {float(specificity):.3f} specificity"
    )
    table = "\n".join(
        [
            START,
            (
                "| Frozen model | Split | AUPRC (95% CI) | AUROC (95% CI) | "
                "Brier (95% CI) | ECE (95% CI) | Sensitivity @ ≥90% specificity | "
                "Threshold |"
            ),
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            (
                f"| {payload['model_family']} | 最終測試資料（Set B） | "
                f"{_format_interval(intervals['auprc'])} | "
                f"{_format_interval(intervals['auroc'])} | "
                f"{_format_interval(intervals['brier'])} | "
                f"{_format_interval(intervals['ece'])} | {operating} | "
                f"{float(metrics['threshold']):.3f} |"
            ),
            END,
        ]
    )
    before, remainder = text.split(START)
    _, after = remainder.split(END)
    readme.write_text(before + table + after, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    args = parser.parse_args()
    payload = json.loads(args.metrics.read_text(encoding="utf-8"))
    update_readme(args.readme, payload)
    print(f"Updated {args.readme.resolve()}")


if __name__ == "__main__":
    main()
