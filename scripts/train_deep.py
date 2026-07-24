"""Train a compact GRU-D or TCN candidate with checkpoint/resume."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from carerisk48h.config import load_config
from carerisk48h.data.downloader import sha256_file
from carerisk48h.data.parser import load_outcomes, parse_directory
from carerisk48h.data.split import make_split_manifest
from carerisk48h.deep_training import train_deep_family
from carerisk48h.synthetic import generate_synthetic_cohort


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", choices=["grud", "tcn"], required=True)
    parser.add_argument("--config", type=Path, default=Path("configs/quick.yaml"))
    parser.add_argument("--split", type=Path, default=Path("data/processed/set_a_split.csv"))
    parser.add_argument("--checkpoint-dir", type=Path, default=Path("checkpoints"))
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--synthetic", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = load_config(args.config, repo_root=root)
    if args.synthetic:
        stays, outcomes = generate_synthetic_cohort(160, seed=config.split_seed)
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
        manifest_hash = None
    else:
        stays = parse_directory(config.data_dir / "set-a")
        outcomes = load_outcomes(config.data_dir / "Outcomes-a.txt")
        split = pd.read_csv(args.split)
        manifest = config.data_dir / "manifest-set-a.json"
        manifest_hash = sha256_file(manifest) if manifest.exists() else None
    run_dir, payload = train_deep_family(
        stays,
        outcomes,
        split,
        config,
        family=args.family,
        repo_root=root,
        device_name=args.device,
        checkpoint_dir=args.checkpoint_dir,
        resume=args.resume,
        data_manifest_hash=manifest_hash,
    )
    print(f"Run directory: {run_dir}")
    print(f"Evaluation status: {payload['evaluation_status']}")
    print(f"Validation ensemble AUPRC: {payload['ensemble_metrics']['auprc']}")


if __name__ == "__main__":
    main()
