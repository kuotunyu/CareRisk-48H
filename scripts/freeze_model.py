"""Create a frozen artifact manifest; does not access Set B."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from carerisk48h.freezing import create_freeze_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-metadata", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, action="append", required=True)
    parser.add_argument("--split-manifest", type=Path, required=True)
    parser.add_argument("--data-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--confirm-freeze", action="store_true")
    args = parser.parse_args()
    metadata = json.loads(args.candidate_metadata.read_text(encoding="utf-8"))
    manifest = create_freeze_manifest(
        candidate_metadata=metadata,
        artifact_paths=args.artifact,
        split_manifest_path=args.split_manifest,
        data_manifest_path=args.data_manifest,
        output_path=args.output,
        confirm_freeze=args.confirm_freeze,
    )
    print(f"Frozen {len(manifest['artifact_hashes'])} artifacts at {args.output.resolve()}")


if __name__ == "__main__":
    main()
