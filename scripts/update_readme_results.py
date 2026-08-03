"""Update README only from a complete frozen one-time Set B final evaluation."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

START = "<!-- RESULTS_START -->"
END = "<!-- RESULTS_END -->"


def _is_hash(value: Any, *, length: int = 64) -> bool:
    normalized = str(value)
    return len(normalized) == length and all(
        character in "0123456789abcdef" for character in normalized
    )


def _format_interval(item: dict[str, Any]) -> str:
    estimate = item.get("estimate")
    lower = item.get("lower")
    upper = item.get("upper")
    if estimate is None or lower is None or upper is None:
        return "待填"
    return f"{float(estimate):.3f} ({float(lower):.3f}–{float(upper):.3f})"


def validate_final_metrics(payload: dict[str, Any]) -> None:
    if payload.get("evaluation_status") != "final":
        raise ValueError("README updater refuses smoke_test/development metrics")
    if payload.get("dataset") != "PhysioNet Challenge 2012 Set B":
        raise ValueError("formal README results must come from Set B")
    if payload.get("freeze_status") != "frozen":
        raise ValueError("formal results require a frozen manifest")
    if payload.get("set_b_final_evaluation_successes") != 1:
        raise ValueError("formal results require exactly one successful Set B evaluation")
    bootstrap = payload.get("bootstrap", {})
    if (
        bootstrap.get("samples") != 2_000
        or bootstrap.get("method") != "stratified percentile"
        or bootstrap.get("seed") != 2026
    ):
        raise ValueError("formal results require 2,000 stratified percentile bootstrap samples")
    required = {
        "n",
        "auprc",
        "auroc",
        "brier",
        "ece",
        "sensitivity",
        "specificity",
        "threshold",
    }
    metrics = payload.get("metrics", {})
    if not required.issubset(metrics):
        raise ValueError("final metrics payload is incomplete")
    if metrics.get("n") != 4_000:
        raise ValueError("formal Set B results require exactly 4,000 records")
    if not {"auprc", "auroc", "brier", "ece"}.issubset(payload.get("confidence_intervals", {})):
        raise ValueError("final confidence intervals are incomplete")
    provenance_fields = {
        "run_id",
        "created_at_utc",
        "model_seeds",
        "candidate_source_git_sha",
        "evaluation_source_git_sha",
        "freeze_manifest_sha256",
        "config_hash",
        "data_manifest_hash",
        "split_hash",
        "set_b_input_manifest_sha256",
        "set_b_record_ids_sha256",
        "outcomes_sha256",
        "environment",
        "artifact_hashes",
        "subgroups",
    }
    if not provenance_fields.issubset(payload):
        raise ValueError("formal results provenance is incomplete or invalid")
    try:
        created_at = datetime.fromisoformat(str(payload["created_at_utc"]))
    except ValueError as exc:
        raise ValueError("formal results provenance is incomplete or invalid") from exc
    hashes = (
        "freeze_manifest_sha256",
        "config_hash",
        "data_manifest_hash",
        "split_hash",
        "set_b_input_manifest_sha256",
        "set_b_record_ids_sha256",
        "outcomes_sha256",
    )
    artifact_hashes = payload["artifact_hashes"]
    required_audit_artifacts = {
        "set_b_access_ledger.json",
        "set_b_access_ledger.final-lock.json",
    }
    if (
        not isinstance(payload["run_id"], str)
        or not payload["run_id"]
        or created_at.tzinfo is None
        or payload["model_seeds"] != [17, 42, 2026]
        or payload.get("evaluation_source_git_dirty") is not False
        or not _is_hash(payload["candidate_source_git_sha"], length=40)
        or not _is_hash(payload["evaluation_source_git_sha"], length=40)
        or any(not _is_hash(payload[field]) for field in hashes)
        or not isinstance(payload["environment"], dict)
        or not payload["environment"]
        or not isinstance(payload["subgroups"], list)
        or not payload["subgroups"]
        or not isinstance(artifact_hashes, dict)
        or not required_audit_artifacts.issubset(artifact_hashes)
        or any(not _is_hash(value) for value in artifact_hashes.values())
    ):
        raise ValueError("formal results provenance is incomplete or invalid")


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
                f"| {payload['model_family']} | Set B final | "
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
