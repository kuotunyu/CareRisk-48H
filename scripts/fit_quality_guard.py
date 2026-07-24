"""Fit and serialize the quality/OOD guard using only fixed Set A train IDs."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from carerisk48h.data.parser import parse_directory
from carerisk48h.guard import QualityOODGuard


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--split", type=Path, default=Path("data/processed/set_a_split.csv"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/quality_guard.joblib"))
    parser.add_argument("--n-jobs", type=int, default=2)
    args = parser.parse_args()
    stays = parse_directory(args.raw_dir / "set-a")
    split = pd.read_csv(args.split)
    train_ids = set(split.loc[split["split"] == "train", "RecordID"].astype(int))
    train_stays = [stay for stay in stays if stay.record_id in train_ids]
    if {stay.record_id for stay in train_stays} != train_ids:
        raise ValueError("split train IDs do not match Set A records")
    guard = QualityOODGuard.fit(train_stays, seed=2026, n_jobs=args.n_jobs)
    guard.save(args.output)
    print(f"Guard fit on {len(train_stays)} Set A train stays: {args.output.resolve()}")


if __name__ == "__main__":
    main()
