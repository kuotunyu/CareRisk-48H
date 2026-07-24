"""Train three-seed logistic and LightGBM development candidates."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from carerisk48h.config import load_config
from carerisk48h.data.downloader import sha256_file
from carerisk48h.data.parser import load_outcomes, parse_directory
from carerisk48h.tabular_training import train_tabular_comparison


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/full.yaml"))
    parser.add_argument("--split", type=Path, default=Path("data/processed/set_a_split.csv"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = load_config(args.config, repo_root=root)
    stays = parse_directory(config.data_dir / "set-a")
    outcomes = load_outcomes(config.data_dir / "Outcomes-a.txt")
    split = pd.read_csv(args.split)
    manifest_path = config.data_dir / "manifest-set-a.json"
    run_dir, payload = train_tabular_comparison(
        stays,
        outcomes,
        split,
        config,
        repo_root=root,
        data_manifest_hash=sha256_file(manifest_path) if manifest_path.exists() else None,
    )
    print(f"Run directory: {run_dir}")
    print(f"Selected development tabular family: {payload['selected_tabular_family']}")


if __name__ == "__main__":
    main()
