"""Write aggregate Set A calibration and threshold-stability diagnostics."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from carerisk48h.artifacts import write_json_atomic
from carerisk48h.calibration_diagnostics import bootstrap_calibration_diagnostics


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument(
        "--dataset-role",
        choices=("set_a_calibration",),
        required=True,
        help="Fail-closed scope declaration; Set B and Set C are not accepted.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=2_000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--target-specificity", type=float, default=0.90)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    with np.load(args.predictions) as data:
        if "labels" not in data or "probabilities" not in data:
            raise ValueError("predictions NPZ must contain labels and probabilities")
        labels = np.asarray(data["labels"])
        probabilities = np.asarray(data["probabilities"])
    diagnostics = bootstrap_calibration_diagnostics(
        labels,
        probabilities,
        target_specificity=args.target_specificity,
        samples=args.bootstrap_samples,
        seed=args.seed,
    )
    payload: dict[str, Any] = {
        "schema_version": 1,
        "evaluation_status": "set_a_calibration_diagnostic",
        "dataset_role": args.dataset_role,
        "scope": "apparent_internal_set_a_calibration",
        "diagnostics": diagnostics,
        "use_limitation": (
            "Aggregate research diagnostic only; not a clinical threshold, external validation, "
            "or evidence that probabilities are reliable for individual care."
        ),
    }
    write_json_atomic(args.output, payload)
    print(f"Set A calibration diagnostic written to {args.output.resolve()}")


if __name__ == "__main__":
    main()
