"""Small YAML configuration loader with repository-relative paths."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from carerisk48h.constants import MODEL_SEEDS, SPLIT_SEED


@dataclass(frozen=True)
class RunConfig:
    mode: str
    model: str
    data_dir: Path
    output_dir: Path
    split_seed: int
    model_seeds: tuple[int, ...]
    bootstrap_samples: int
    cpu_threads: int
    max_patients: int | None
    epochs: int
    batch_size: int


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (root / path).resolve()


def canonical_config_payload(config: RunConfig, *, repo_root: str | Path) -> dict[str, Any]:
    """Return machine-independent config metadata with repository-relative paths."""
    root = Path(repo_root).resolve()
    payload = asdict(config)
    for field in ("data_dir", "output_dir"):
        path = Path(payload[field]).resolve()
        try:
            payload[field] = path.relative_to(root).as_posix()
        except ValueError:
            payload[field] = f"<external>/{path.name}"
    payload["model_seeds"] = list(config.model_seeds)
    return payload


def load_config(path: str | Path, *, repo_root: str | Path | None = None) -> RunConfig:
    """Load a validated YAML run config without machine-specific path assumptions."""
    config_path = Path(path).resolve()
    root = Path(repo_root).resolve() if repo_root is not None else config_path.parent.parent
    with config_path.open("r", encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle) or {}

    mode = str(raw.get("mode", "quick"))
    if mode not in {"quick", "full"}:
        raise ValueError("mode must be 'quick' or 'full'")
    split_seed = int(raw.get("split_seed", SPLIT_SEED))
    if split_seed != SPLIT_SEED:
        raise ValueError(f"split_seed is frozen at {SPLIT_SEED}")
    seeds = tuple(int(seed) for seed in raw.get("model_seeds", MODEL_SEEDS))
    if seeds != MODEL_SEEDS:
        raise ValueError(f"model_seeds are frozen at {list(MODEL_SEEDS)} in that order")
    cpu_threads = int(raw.get("cpu_threads", 2))
    if cpu_threads < 1:
        raise ValueError("cpu_threads must be positive")

    return RunConfig(
        mode=mode,
        model=str(raw.get("model", "logistic")),
        data_dir=_resolve(root, str(raw.get("data_dir", "data/raw"))),
        output_dir=_resolve(root, str(raw.get("output_dir", "artifacts"))),
        split_seed=split_seed,
        model_seeds=seeds,
        bootstrap_samples=int(raw.get("bootstrap_samples", 200 if mode == "quick" else 2000)),
        cpu_threads=cpu_threads,
        max_patients=(None if raw.get("max_patients") is None else int(raw["max_patients"])),
        epochs=int(raw.get("epochs", 3 if mode == "quick" else 50)),
        batch_size=int(raw.get("batch_size", 64)),
    )
