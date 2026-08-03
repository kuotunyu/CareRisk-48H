"""Refit the pre-registered LightGBM winner and lock calibration on Set A only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from carerisk48h.artifacts import environment_versions, git_state, stable_hash
from carerisk48h.data.downloader import sha256_file
from carerisk48h.data.parser import load_outcomes, parse_directory
from carerisk48h.features.tabular import build_feature_frame
from carerisk48h.final_refit import refit_lightgbm_candidate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--development-run", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--split", type=Path, default=Path("data/processed/set_a_split.csv"))
    parser.add_argument("--data-manifest", type=Path, default=Path("data/raw/manifest-set-a.json"))
    parser.add_argument("--n-jobs", type=int, default=2)
    args = parser.parse_args()

    selection = json.loads(args.selection.read_text(encoding="utf-8"))
    if selection.get("set_b_accessed") is not False:
        raise ValueError("model selection must prove that Set B was not accessed")
    selected = selection.get("decision", {}).get("selected", {})
    if selected.get("family") != "lightgbm":
        raise ValueError("this final refit entry point requires the selected LightGBM family")

    development = json.loads((args.development_run / "metrics.json").read_text(encoding="utf-8"))
    if development.get("selected_tabular_family") != "lightgbm":
        raise ValueError("development run did not select LightGBM")
    parameters = development["families"]["lightgbm"]["selected_parameters"]
    model_seeds = tuple(int(seed) for seed in development["seeds"]["models"])

    stays = parse_directory(args.raw_dir / "set-a")
    outcomes = load_outcomes(args.raw_dir / "Outcomes-a.txt")
    split = pd.read_csv(args.split)
    counts = split["split"].value_counts().to_dict()
    if counts != {"train": 2800, "validation": 600, "calibration": 600}:
        raise ValueError(f"frozen Set A split counts changed: {counts}")
    split_hash = stable_hash(split.to_dict(orient="records"))
    if split_hash != development["split_hash"] or split_hash != selection["tabular_split_hash"]:
        raise ValueError("Set A split hash does not match development selection")
    data_manifest_hash = sha256_file(args.data_manifest)
    if data_manifest_hash != development["data_manifest_hash"]:
        raise ValueError("Set A data manifest hash does not match development selection")

    features = build_feature_frame(stays, include_slope=True)
    cohort = features.merge(outcomes, on="RecordID", validate="one_to_one").merge(
        split, on="RecordID", validate="one_to_one"
    )
    if len(cohort) != 4000:
        raise ValueError("final refit requires all 4,000 Set A stays")
    feature_columns = [column for column in features.columns if column != "RecordID"]

    repo_root = Path(__file__).resolve().parents[1]
    source = git_state(repo_root)
    source_sha = source.get("commit")
    if not isinstance(source_sha, str) or source.get("dirty") is not False:
        raise ValueError("final refit requires a clean Git source")
    environment = {
        "python": sys.version,
        **environment_versions(("lightgbm", "shap")),
    }
    metadata_path, metadata = refit_lightgbm_candidate(
        cohort,
        feature_columns=feature_columns,
        parameters=parameters,
        model_seeds=model_seeds,
        n_jobs=args.n_jobs,
        output_dir=args.output_dir,
        source_git_sha=source_sha,
        source_git_dirty=False,
        selection_sha256=sha256_file(args.selection),
        data_manifest_hash=data_manifest_hash,
        split_hash=split_hash,
        environment=environment,
        dry_run_evaluation_path=args.output_dir / "set_a_dry_run" / "evaluation.json",
        target_specificity=0.90,
    )
    print(f"Final candidate metadata: {metadata_path.resolve()}")
    print(f"Family: {metadata['model_family']}")
    print(f"Threshold: {metadata['threshold']}")
    print("Set B accessed: False")


if __name__ == "__main__":
    main()
