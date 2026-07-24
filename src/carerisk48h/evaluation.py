"""Calibrated evaluation, bootstrap intervals, plots, errors, and subgroups."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import precision_recall_curve, roc_curve

from carerisk48h.artifacts import write_json_atomic
from carerisk48h.metrics import compute_binary_metrics

_CI_METRICS = (
    "auprc",
    "auroc",
    "brier",
    "ece",
    "sensitivity",
    "specificity",
    "ppv",
    "npv",
)


def stratified_bootstrap_ci(
    labels: np.ndarray,
    probabilities: np.ndarray,
    *,
    threshold: float,
    samples: int = 2_000,
    seed: int = 2026,
) -> dict[str, dict[str, float | None]]:
    """Percentile 95% CIs with outcome-stratified resampling."""
    truth = np.asarray(labels, dtype=np.int8)
    scores = np.asarray(probabilities, dtype=np.float64)
    if samples < 1:
        raise ValueError("bootstrap samples must be positive")
    positive = np.flatnonzero(truth == 1)
    negative = np.flatnonzero(truth == 0)
    if not len(positive) or not len(negative):
        metrics = compute_binary_metrics(truth, scores, threshold=threshold)
        return {
            name: {"estimate": metrics[name], "lower": None, "upper": None} for name in _CI_METRICS
        }
    generator = np.random.default_rng(seed)
    distributions: dict[str, list[float]] = {name: [] for name in _CI_METRICS}
    for _ in range(samples):
        indices = np.concatenate(
            [
                generator.choice(negative, size=len(negative), replace=True),
                generator.choice(positive, size=len(positive), replace=True),
            ]
        )
        replicate = compute_binary_metrics(truth[indices], scores[indices], threshold=threshold)
        for name in _CI_METRICS:
            if replicate[name] is not None:
                distributions[name].append(float(replicate[name]))
    estimate = compute_binary_metrics(truth, scores, threshold=threshold)
    return {
        name: {
            "estimate": estimate[name],
            "lower": (
                float(np.percentile(distributions[name], 2.5)) if distributions[name] else None
            ),
            "upper": (
                float(np.percentile(distributions[name], 97.5)) if distributions[name] else None
            ),
        }
        for name in _CI_METRICS
    }


def _age_band(value: float) -> str:
    if np.isnan(value):
        return "missing"
    if value < 45:
        return "<45"
    if value < 65:
        return "45-64"
    if value < 80:
        return "65-79"
    return ">=80"


def subgroup_analysis(
    labels: np.ndarray,
    probabilities: np.ndarray,
    metadata: pd.DataFrame,
    *,
    threshold: float,
    bootstrap_samples: int,
    seed: int,
) -> list[dict[str, Any]]:
    """Evaluate prespecified groups with instability warnings, not fairness claims."""
    required = {"Gender", "ICUType", "Age"}
    if not required.issubset(metadata):
        raise ValueError(f"subgroup metadata missing {sorted(required - set(metadata))}")
    if len(metadata) != len(labels):
        raise ValueError("metadata and predictions must have equal length")
    working = metadata.reset_index(drop=True).copy()
    working["label"] = np.asarray(labels, dtype=np.int8)
    working["probability"] = np.asarray(probabilities, dtype=np.float64)
    working["age_band"] = working["Age"].astype(float).map(_age_band)
    working["Gender"] = working["Gender"].astype(object).where(working["Gender"].notna(), "missing")
    working["ICUType"] = (
        working["ICUType"].astype(object).where(working["ICUType"].notna(), "missing")
    )
    reports: list[dict[str, Any]] = []
    for field, output_name in (
        ("Gender", "gender"),
        ("ICUType", "ICUType"),
        ("age_band", "age_band"),
    ):
        for level, group in working.groupby(field, dropna=False, sort=True):
            group_labels = group["label"].to_numpy()
            group_probabilities = group["probability"].to_numpy()
            deaths = int(group_labels.sum())
            survivors = int(len(group) - deaths)
            metrics = compute_binary_metrics(group_labels, group_probabilities, threshold=threshold)
            ci = stratified_bootstrap_ci(
                group_labels,
                group_probabilities,
                threshold=threshold,
                samples=bootstrap_samples,
                seed=seed,
            )
            reports.append(
                {
                    "subgroup": output_name,
                    "level": str(level),
                    "n": len(group),
                    "deaths": deaths,
                    "non_deaths": survivors,
                    "unstable": deaths < 20 or survivors < 20,
                    "metrics": metrics,
                    "confidence_intervals": ci,
                    "interpretation": (
                        "Descriptive error analysis only; do not infer fairness or causality."
                    ),
                }
            )
    return reports


def _decision_curve(
    labels: np.ndarray, probabilities: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    thresholds = np.linspace(0.01, 0.50, 50)
    sample_size = len(labels)
    prevalence = float(np.mean(labels))
    model_benefit: list[float] = []
    all_benefit: list[float] = []
    for threshold in thresholds:
        predicted = probabilities >= threshold
        true_positive = np.sum(predicted & (labels == 1))
        false_positive = np.sum(predicted & (labels == 0))
        weight = threshold / (1.0 - threshold)
        model_benefit.append(true_positive / sample_size - false_positive / sample_size * weight)
        all_benefit.append(prevalence - (1.0 - prevalence) * weight)
    return thresholds, np.asarray(model_benefit), np.asarray(all_benefit)


def write_evaluation_plots(
    labels: np.ndarray, probabilities: np.ndarray, *, output_dir: str | Path
) -> None:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    precision, recall, _ = precision_recall_curve(labels, probabilities)
    false_positive, true_positive, _ = roc_curve(labels, probabilities)
    observed, predicted = calibration_curve(labels, probabilities, n_bins=10, strategy="uniform")
    thresholds, net_benefit, all_benefit = _decision_curve(labels, probabilities)
    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    axes[0, 0].plot(recall, precision)
    axes[0, 0].axhline(float(np.mean(labels)), linestyle="--", color="grey")
    axes[0, 0].set(xlabel="Recall", ylabel="Precision", title="Precision-recall")
    axes[0, 1].plot(false_positive, true_positive)
    axes[0, 1].plot([0, 1], [0, 1], linestyle="--", color="grey")
    axes[0, 1].set(xlabel="False-positive rate", ylabel="True-positive rate", title="ROC")
    axes[1, 0].plot(predicted, observed, marker="o")
    axes[1, 0].plot([0, 1], [0, 1], linestyle="--", color="grey")
    axes[1, 0].set(xlabel="Mean predicted probability", ylabel="Observed rate", title="Reliability")
    axes[1, 1].plot(thresholds, net_benefit, label="model")
    axes[1, 1].plot(thresholds, all_benefit, label="treat all")
    axes[1, 1].axhline(0, color="grey", linestyle="--", label="treat none")
    axes[1, 1].set(xlabel="Threshold", ylabel="Net benefit", title="Decision curve")
    axes[1, 1].legend()
    fig.tight_layout()
    fig.savefig(destination / "evaluation_plots.png", dpi=160)
    plt.close(fig)


def error_case_table(
    labels: np.ndarray,
    probabilities: np.ndarray,
    record_ids: np.ndarray,
    *,
    threshold: float,
) -> pd.DataFrame:
    truth = np.asarray(labels, dtype=np.int8)
    scores = np.asarray(probabilities, dtype=np.float64)
    predicted = scores >= threshold
    errors = predicted != truth.astype(bool)
    frame = pd.DataFrame(
        {
            "RecordID": record_ids[errors],
            "label": truth[errors],
            "probability": scores[errors],
            "error_type": np.where(predicted[errors], "false_positive", "false_negative"),
        }
    )
    frame["distance_from_threshold"] = np.abs(frame["probability"] - threshold)
    return frame.sort_values("distance_from_threshold", ascending=False).reset_index(drop=True)


def evaluation_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--threshold", type=float, required=True)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=2_000)
    args = parser.parse_args()
    with np.load(args.predictions) as data:
        labels = data["labels"]
        probabilities = data["probabilities"]
        record_ids = data["record_ids"]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics = compute_binary_metrics(labels, probabilities, threshold=args.threshold)
    intervals = stratified_bootstrap_ci(
        labels,
        probabilities,
        threshold=args.threshold,
        samples=args.bootstrap_samples,
        seed=2026,
    )
    payload: dict[str, Any] = {
        "metrics": metrics,
        "confidence_intervals": intervals,
        "bootstrap": {
            "method": "stratified percentile",
            "samples": args.bootstrap_samples,
            "seed": 2026,
        },
    }
    if args.metadata:
        metadata = pd.read_csv(args.metadata)
        payload["subgroups"] = subgroup_analysis(
            labels,
            probabilities,
            metadata,
            threshold=args.threshold,
            bootstrap_samples=args.bootstrap_samples,
            seed=2026,
        )
    write_evaluation_plots(labels, probabilities, output_dir=args.output_dir / "plots")
    error_case_table(labels, probabilities, record_ids, threshold=args.threshold).to_csv(
        args.output_dir / "error_cases.csv", index=False
    )
    write_json_atomic(args.output_dir / "evaluation.json", payload)
    print(f"Evaluation written to {args.output_dir.resolve()}")
