"""Generate Set A data-quality artifacts and the fixed development split."""

from __future__ import annotations

import argparse
from pathlib import Path

from carerisk48h.data.parser import load_outcomes, parse_directory
from carerisk48h.data.quality import generate_quality_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports/generated/data_quality"))
    parser.add_argument("--split-seed", type=int, default=2026)
    args = parser.parse_args()
    stays = parse_directory(args.raw_dir / "set-a")
    outcomes = load_outcomes(args.raw_dir / "Outcomes-a.txt")
    summary = generate_quality_report(
        stays,
        outcomes,
        report_dir=args.report_dir,
        processed_dir=args.processed_dir,
        split_seed=args.split_seed,
    )
    print(f"Generated data-quality report for {summary['n_stays']} Set A stays.")
    print(f"Report directory: {args.report_dir.resolve()}")


if __name__ == "__main__":
    main()
