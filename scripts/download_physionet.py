"""Download PhysioNet Challenge 2012 data without committing raw files."""

from __future__ import annotations

import argparse
from pathlib import Path

from carerisk48h.data.downloader import download_physionet, verify_manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--set", dest="dataset_set", choices=["a", "b"], default="a")
    parser.add_argument(
        "--without-outcomes",
        action="store_true",
        help="Download only input records (recommended for Set B before final evaluation).",
    )
    parser.add_argument(
        "--confirm-final",
        action="store_true",
        help="Permit Outcomes-b only after the separate freeze/evaluation gate is satisfied.",
    )
    parser.add_argument("--verify-only", type=Path, help="Verify an existing manifest and exit.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.verify_only is not None:
        verify_manifest(args.raw_dir, args.verify_only)
        print(f"Verified manifest: {args.verify_only}")
        return
    manifest = download_physionet(
        args.raw_dir,
        dataset_set=args.dataset_set,
        include_outcomes=not args.without_outcomes,
        confirm_final=args.confirm_final,
    )
    print(f"Downloaded and verified: {manifest}")


if __name__ == "__main__":
    main()
