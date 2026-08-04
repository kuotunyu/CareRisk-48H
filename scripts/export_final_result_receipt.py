"""Export a privacy-safe aggregate receipt from qualified final metrics."""

from __future__ import annotations

import argparse
import hashlib
import json
from math import isfinite
from pathlib import Path
from typing import Any

from carerisk48h.formal_results import validate_final_metrics

AGGREGATE_METRICS = (
    "auprc",
    "auroc",
    "brier",
    "ece",
    "sensitivity",
    "specificity",
    "ppv",
    "npv",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require_hash(value: str, *, field: str) -> str:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _validate_public_aggregates(payload: dict[str, Any]) -> None:
    metrics = payload["metrics"]
    if metrics.get("events") != 568 or metrics.get("prevalence") != 568 / 4000:
        raise ValueError("formal Set B cohort aggregates are inconsistent")
    confusion = metrics.get("confusion")
    if not isinstance(confusion, dict) or set(confusion) != {"tn", "fp", "fn", "tp"}:
        raise ValueError("formal Set B confusion aggregates are incomplete")
    if any(not isinstance(confusion[name], int) or confusion[name] < 0 for name in confusion):
        raise ValueError("formal Set B confusion aggregates are invalid")
    if sum(confusion.values()) != 4000 or confusion["tp"] + confusion["fn"] != 568:
        raise ValueError("formal Set B confusion aggregates are inconsistent")

    intervals = payload["confidence_intervals"]
    for name in AGGREGATE_METRICS:
        value = metrics.get(name)
        interval = intervals.get(name)
        if (
            isinstance(value, bool)
            or not isinstance(value, int | float)
            or not isfinite(float(value))
            or not 0.0 <= float(value) <= 1.0
            or not isinstance(interval, dict)
            or set(interval) != {"estimate", "lower", "upper"}
        ):
            raise ValueError(f"formal aggregate metric {name} is incomplete")
        estimate = float(interval["estimate"])
        lower = float(interval["lower"])
        upper = float(interval["upper"])
        bounds = (lower, estimate, upper)
        bounds_are_valid = all(isfinite(number) and 0.0 <= number <= 1.0 for number in bounds)
        if (
            not bounds_are_valid
            or not lower <= estimate <= upper
            or abs(estimate - float(value)) > 1e-12
        ):
            raise ValueError(f"formal aggregate metric {name} is inconsistent")


def build_public_receipt(payload: dict[str, Any], *, metrics_sha256: str) -> dict[str, Any]:
    """Return a strict aggregate-only receipt without copying private payload fields."""

    validate_final_metrics(payload)
    _validate_public_aggregates(payload)
    metrics = payload["metrics"]
    intervals = payload["confidence_intervals"]
    return {
        "schema_version": 1,
        "title": "CareRisk 48H 正式結果收據",
        "evaluation_status": "final",
        "use_limitation": "僅供研究與教育，不是臨床診斷、治療或照護決策工具。",
        "dataset": {
            "name": payload["dataset"],
            "role": "final_test",
            "n": metrics["n"],
            "events": metrics["events"],
            "prevalence": metrics["prevalence"],
        },
        "model": {
            "family": payload["model_family"],
            "seeds": list(payload["model_seeds"]),
            "calibrator": payload["calibrator"]["method"],
            "threshold": payload["threshold"],
        },
        "evaluation": {
            "run_id": payload["run_id"],
            "created_at_utc": payload["created_at_utc"],
            "bootstrap": {
                "method": payload["bootstrap"]["method"],
                "samples": payload["bootstrap"]["samples"],
                "seed": payload["bootstrap"]["seed"],
            },
            "set_b_final_evaluation_successes": payload["set_b_final_evaluation_successes"],
            "final_lock_status": "locked_after_one_success",
        },
        "metrics": {
            **{name: metrics[name] for name in AGGREGATE_METRICS},
            "confusion": {name: metrics["confusion"][name] for name in ("tn", "fp", "fn", "tp")},
        },
        "confidence_intervals": {
            name: {
                "estimate": intervals[name]["estimate"],
                "lower": intervals[name]["lower"],
                "upper": intervals[name]["upper"],
            }
            for name in AGGREGATE_METRICS
        },
        "provenance": {
            "candidate_source_git_sha": payload["candidate_source_git_sha"],
            "evaluation_source_git_sha": payload["evaluation_source_git_sha"],
            "evaluation_source_git_dirty": payload["evaluation_source_git_dirty"],
            "freeze_manifest_sha256": payload["freeze_manifest_sha256"],
            "config_hash": payload["config_hash"],
            "data_manifest_hash": payload["data_manifest_hash"],
            "split_hash": payload["split_hash"],
            "set_b_input_manifest_sha256": payload["set_b_input_manifest_sha256"],
            "formal_metrics_sha256": _require_hash(metrics_sha256, field="formal_metrics_sha256"),
        },
        "privacy": {
            "aggregate_only": True,
            "excluded": [
                "record_identifiers",
                "raw_outcomes",
                "individual_predictions",
                "model_artifacts",
                "subgroup_rows",
                "environment_details",
                "access_ledger_contents",
            ],
        },
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    source = args.metrics.read_bytes()
    payload = json.loads(source.decode("utf-8"))
    receipt = build_public_receipt(payload, metrics_sha256=_sha256(source))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Exported aggregate receipt to {args.output.resolve()}")


if __name__ == "__main__":
    main()
