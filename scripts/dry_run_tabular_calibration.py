"""Exercise calibration/evaluation on Set A only; never a formal estimate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from carerisk48h.artifacts import write_json_atomic
from carerisk48h.calibration import fit_calibration_bundle
from carerisk48h.data.parser import load_outcomes, parse_directory
from carerisk48h.evaluation import (
    error_case_table,
    stratified_bootstrap_ci,
    subgroup_analysis,
    write_evaluation_plots,
)
from carerisk48h.features.tabular import build_feature_frame
from carerisk48h.metrics import compute_binary_metrics


def _latest_tabular_run(artifacts: Path) -> Path:
    candidates = sorted(artifacts.glob("*-tabular-full"))
    if not candidates:
        raise FileNotFoundError("no full tabular development run found")
    return candidates[-1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--split", type=Path, default=Path("data/processed/set_a_split.csv"))
    parser.add_argument("--bootstrap-samples", type=int, default=200)
    args = parser.parse_args()
    run_dir = args.run_dir or _latest_tabular_run(Path("artifacts"))
    development = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    family = str(development["selected_tabular_family"])
    model_paths = sorted((run_dir / "models").glob(f"{family}_seed_*.joblib"))
    if len(model_paths) != 3:
        raise ValueError("dry run requires exactly three seed models")
    saved_models = [joblib.load(path) for path in model_paths]
    feature_columns = list(saved_models[0]["feature_columns"])
    models = [item["model"] for item in saved_models]

    stays = parse_directory(args.raw_dir / "set-a")
    outcomes = load_outcomes(args.raw_dir / "Outcomes-a.txt")
    split = pd.read_csv(args.split)
    features = build_feature_frame(stays, include_slope=family == "lightgbm")
    cohort = features.merge(outcomes, on="RecordID", validate="one_to_one").merge(
        split, on="RecordID", validate="one_to_one"
    )
    calibration = cohort["split"] == "calibration"
    validation = cohort["split"] == "validation"

    def ensemble_probability(rows: pd.Series) -> np.ndarray:
        matrix = cohort.loc[rows, feature_columns]
        return np.mean(np.stack([model.predict_proba(matrix)[:, 1] for model in models]), axis=0)

    calibration_raw = ensemble_probability(calibration)
    calibration_labels = cohort.loc[calibration, "label"].to_numpy()
    calibration_bundle = fit_calibration_bundle(
        calibration_labels, calibration_raw, method="platt", target_specificity=0.90
    )
    threshold = float(calibration_bundle["threshold"])
    validation_raw = ensemble_probability(validation)
    calibrator = calibration_bundle["calibrator"]
    validation_probability = calibrator.predict(validation_raw)
    validation_labels = cohort.loc[validation, "label"].to_numpy()
    validation_ids = cohort.loc[validation, "RecordID"].to_numpy()
    metadata_lookup = {
        stay.record_id: {
            "Gender": stay.static["Gender"],
            "ICUType": stay.static["ICUType"],
            "Age": stay.static["Age"],
        }
        for stay in stays
    }
    metadata = pd.DataFrame([metadata_lookup[int(item)] for item in validation_ids])

    output = run_dir / "set_a_dry_run"
    output.mkdir(parents=True, exist_ok=True)
    joblib.dump(calibration_bundle, output / "calibrator.joblib")
    np.savez_compressed(
        output / "validation_predictions.npz",
        record_ids=validation_ids,
        labels=validation_labels,
        raw_probabilities=validation_raw,
        probabilities=validation_probability,
    )
    metrics = compute_binary_metrics(validation_labels, validation_probability, threshold=threshold)
    intervals = stratified_bootstrap_ci(
        validation_labels,
        validation_probability,
        threshold=threshold,
        samples=args.bootstrap_samples,
        seed=2026,
    )
    subgroups = subgroup_analysis(
        validation_labels,
        validation_probability,
        metadata,
        threshold=threshold,
        bootstrap_samples=args.bootstrap_samples,
        seed=2026,
    )
    write_evaluation_plots(validation_labels, validation_probability, output_dir=output / "plots")
    error_case_table(
        validation_labels, validation_probability, validation_ids, threshold=threshold
    ).to_csv(output / "error_cases.csv", index=False)
    payload = {
        "evaluation_status": "set_a_reused_development_dry_run",
        "dataset": "PhysioNet Challenge 2012 Set A validation",
        "model_family": family,
        "calibration_fit_scope": "Set A calibration",
        "threshold_fit_scope": "Set A calibration",
        "target_specificity": 0.90,
        "threshold": threshold,
        "metrics": metrics,
        "confidence_intervals": intervals,
        "subgroups": subgroups,
        "bootstrap": {
            "samples": args.bootstrap_samples,
            "method": "stratified percentile",
            "seed": 2026,
        },
        "warning": (
            "Validation was previously used for model selection. This only tests pipeline wiring "
            "and must never be reported as final performance."
        ),
        "set_b_accessed": False,
    }
    write_json_atomic(output / "evaluation.json", payload)
    print(f"Set A-only dry run: {output.resolve()}")
    print(f"Locked dry-run threshold: {threshold}")


if __name__ == "__main__":
    main()
