"""Build the synthetic-only smoke bundle used when no frozen model is supplied."""

from __future__ import annotations

import argparse
from pathlib import Path

from carerisk48h.demo import build_synthetic_demo_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/demo/synthetic_demo_bundle.joblib")
    )
    args = parser.parse_args()
    print(build_synthetic_demo_bundle(args.output).resolve())


if __name__ == "__main__":
    main()
