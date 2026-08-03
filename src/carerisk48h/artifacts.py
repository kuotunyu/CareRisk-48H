"""Reproducibility metadata and atomic artifact helpers."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import subprocess
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_run_id(model: str, mode: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{model}-{mode}"


def stable_hash(value: Any) -> str:
    if is_dataclass(value):
        value = asdict(value)  # type: ignore[arg-type]
    encoded = json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def deep_resume_fingerprint(
    *,
    config_hash: str,
    data_manifest_hash: str | None,
    split_hash: str,
    source_git_sha: str | None,
    family: str,
    seed: int,
) -> str:
    """Bind a deep checkpoint to every frozen training input and its source revision."""
    return stable_hash(
        {
            "config_hash": config_hash,
            "data_manifest_hash": data_manifest_hash,
            "split_hash": split_hash,
            "source_git_sha": source_git_sha,
            "family": family,
            "seed": seed,
        }
    )


def git_state(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root)
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        commit = None
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    ).stdout
    return {"commit": commit, "dirty": bool(status.strip())}


def environment_versions(packages: tuple[str, ...] = ()) -> dict[str, str]:
    defaults = ("numpy", "pandas", "scikit-learn", "scipy", "joblib")
    versions: dict[str, str] = {}
    for package in defaults + packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not-installed"
    return versions


def write_json_atomic(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".partial")
    partial.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, target)
