"""Console entry points for CareRisk 48H."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from carerisk48h.config import load_config
from carerisk48h.data.downloader import sha256_file
from carerisk48h.data.parser import load_outcomes, parse_directory
from carerisk48h.data.split import make_split_manifest
from carerisk48h.synthetic import generate_synthetic_cohort
from carerisk48h.training import train_logistic


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def train_main() -> None:
    parser = argparse.ArgumentParser(description="Train a CareRisk 48H candidate model.")
    parser.add_argument("--config", type=Path, default=Path("configs/quick.yaml"))
    parser.add_argument("--model", choices=["logistic", "tabular", "grud", "tcn"])
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--split", type=Path, default=Path("data/processed/set_a_split.csv"))
    parser.add_argument("--checkpoint-dir", type=Path, default=Path("checkpoints"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Use a deterministic non-clinical smoke cohort instead of PhysioNet data.",
    )
    args = parser.parse_args()
    root = _repo_root()
    config = load_config(args.config, repo_root=root)
    requested_model = args.model or ("tabular" if config.model == "auto" else config.model)
    if args.synthetic:
        size = 400 if config.max_patients is None else max(120, min(config.max_patients, 500))
        stays, outcomes = generate_synthetic_cohort(size, seed=config.split_seed)
        manifest_hash = None
        metadata = pd.DataFrame(
            {
                "RecordID": [stay.record_id for stay in stays],
                "label": outcomes.set_index("RecordID")
                .loc[[stay.record_id for stay in stays], "label"]
                .to_numpy(),
                "ICUType": [stay.static["ICUType"] for stay in stays],
            }
        )
        split = make_split_manifest(metadata, seed=config.split_seed)
    else:
        set_a = config.data_dir / "set-a"
        outcomes_path = config.data_dir / "Outcomes-a.txt"
        if not set_a.exists() or not outcomes_path.exists():
            raise FileNotFoundError(
                "Set A is unavailable. Run scripts/download_physionet.py or pass --synthetic."
            )
        stays = parse_directory(set_a)
        outcomes = load_outcomes(outcomes_path)
        if requested_model == "logistic" and config.max_patients is not None:
            metadata = pd.DataFrame(
                {
                    "RecordID": [stay.record_id for stay in stays],
                    "ICUType": [stay.static["ICUType"] for stay in stays],
                }
            ).merge(outcomes, on="RecordID", validate="one_to_one")
            strata = metadata["label"].astype(str) + "_" + metadata["ICUType"].astype(str)
            selected, _ = train_test_split(
                metadata["RecordID"],
                train_size=config.max_patients,
                random_state=config.split_seed,
                stratify=strata,
            )
            selected_ids = set(selected.astype(int))
            stays = [stay for stay in stays if stay.record_id in selected_ids]
            outcomes = outcomes[outcomes["RecordID"].isin(selected_ids)].reset_index(drop=True)
        split = pd.read_csv(args.split)
        manifest = config.data_dir / "manifest-set-a.json"
        manifest_hash = sha256_file(manifest) if manifest.exists() else None
    if requested_model == "logistic":
        run_dir, payload = train_logistic(
            stays,
            outcomes,
            config,
            repo_root=root,
            data_manifest_hash=manifest_hash,
        )
        primary = payload["metrics"]["auprc"]
    elif requested_model == "tabular":
        from carerisk48h.tabular_training import train_tabular_comparison

        run_dir, payload = train_tabular_comparison(
            stays,
            outcomes,
            split,
            config,
            repo_root=root,
            data_manifest_hash=manifest_hash,
        )
        family = payload["selected_tabular_family"]
        primary = payload["families"][family]["aggregate"]["auprc"]["mean"]
    elif requested_model in {"grud", "tcn"}:
        from carerisk48h.deep_training import train_deep_family

        run_dir, payload = train_deep_family(
            stays,
            outcomes,
            split,
            config,
            family=requested_model,
            repo_root=root,
            device_name=args.device,
            checkpoint_dir=args.checkpoint_dir,
            resume=args.resume,
            data_manifest_hash=manifest_hash,
        )
        primary = payload["ensemble_metrics"]["auprc"]
    else:
        raise ValueError(f"unsupported configured model: {requested_model}")
    print(f"Run directory: {run_dir}")
    print(f"Evaluation status: {payload['evaluation_status']}")
    print(f"Validation AUPRC: {primary}")


def evaluate_main() -> None:
    from carerisk48h.evaluation import evaluation_cli

    evaluation_cli()


def calibrate_main() -> None:
    from carerisk48h.calibration import calibration_cli

    calibration_cli()


def predict_main() -> None:
    from carerisk48h.inference import prediction_cli

    prediction_cli()


def benchmark_main() -> None:
    from carerisk48h.benchmarking import benchmark_cli

    benchmark_cli()
