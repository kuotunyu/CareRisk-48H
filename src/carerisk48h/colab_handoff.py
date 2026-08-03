"""Immutable Colab source handoff and self-verifying deep-result packages."""

from __future__ import annotations

import json
import os
import subprocess
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from carerisk48h.artifacts import deep_resume_fingerprint, stable_hash, write_json_atomic
from carerisk48h.constants import MODEL_SEEDS, SPLIT_SEED
from carerisk48h.data.downloader import sha256_file

_FAMILIES = ("grud", "tcn")


def deep_checkpoint_directory(root: str | Path, *, mode: str, source_git_sha: str) -> Path:
    """Keep resumable checkpoints isolated by mode and immutable source revision."""
    if mode not in {"quick", "full"}:
        raise ValueError("mode must be quick or full")
    if len(source_git_sha) != 40 or any(
        character not in "0123456789abcdef" for character in source_git_sha
    ):
        raise ValueError("source_git_sha must be a lowercase 40-character Git SHA")
    return Path(root) / mode / source_git_sha[:12]


def _git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()


def _contains_sensitive_tracked_path(paths: list[str]) -> bool:
    for raw in paths:
        path = raw.replace("\\", "/")
        name = Path(path).name.lower()
        if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
            return True
        if path.startswith(("data/raw/", "data/processed/", "artifacts/", "checkpoints/")):
            return True
    return False


def create_source_bundle(repo_root: str | Path, output_dir: str | Path) -> tuple[Path, Path]:
    """Create a clean, cloneable Git bundle plus a SHA-256 provenance receipt."""
    root = Path(repo_root).resolve()
    if _git(root, "status", "--porcelain"):
        raise ValueError("source bundle requires a clean Git worktree")
    branch = _git(root, "branch", "--show-current")
    if not branch:
        raise ValueError("source bundle requires a named branch")
    source_sha = _git(root, "rev-parse", "HEAD")
    history_objects = _git(root, "rev-list", "--objects", "HEAD").splitlines()
    history_paths = [line.split(" ", 1)[1] for line in history_objects if " " in line]
    if _contains_sensitive_tracked_path(history_paths):
        raise ValueError("source history contains a forbidden data or secret path")

    destination = Path(output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    bundle = destination / f"carerisk48h-source-{source_sha[:12]}.bundle"
    partial = bundle.with_suffix(bundle.suffix + ".partial")
    subprocess.run(
        ["git", "bundle", "create", str(partial), branch],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    subprocess.run(
        ["git", "bundle", "verify", str(partial)],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    os.replace(partial, bundle)
    receipt = destination / "carerisk48h-source-receipt.json"
    write_json_atomic(
        receipt,
        {
            "schema_version": 1,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_git_sha": source_sha,
            "source_branch": branch,
            "bundle_filename": bundle.name,
            "bundle_bytes": bundle.stat().st_size,
            "bundle_sha256": sha256_file(bundle),
        },
    )
    return bundle, receipt


def _require_sha256(value: Any, *, field: str, allow_none: bool = False) -> str | None:
    if allow_none and value is None:
        return None
    normalized = str(value)
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError(f"{field} must be a lowercase SHA-256")
    return normalized


def _validate_deep_run(
    run_dir: Path,
    *,
    checkpoint_dir: Path,
    mode: str,
    expected_git_sha: str,
) -> tuple[dict[str, Any], list[Path], list[Path]]:
    metrics_path = run_dir / "metrics.json"
    if not metrics_path.is_file():
        raise FileNotFoundError(metrics_path)
    payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    family = str(payload.get("model_family"))
    if family not in _FAMILIES or not run_dir.name.endswith(f"-{family}-{mode}"):
        raise ValueError(f"run directory and model family disagree: {run_dir}")
    expected_status = "smoke_test" if mode == "quick" else "development"
    if payload.get("evaluation_status") != expected_status:
        raise ValueError(f"{family} has invalid evaluation_status for {mode}")
    if payload.get("seeds") != {"split": SPLIT_SEED, "models": list(MODEL_SEEDS)}:
        raise ValueError(f"{family} does not use the frozen split/model seeds")
    config = payload.get("config")
    if not isinstance(config, dict) or config.get("mode") != mode:
        raise ValueError(f"{family} config mode mismatch")
    if stable_hash(config) != payload.get("config_hash"):
        raise ValueError(f"{family} config hash mismatch")
    _require_sha256(payload.get("config_hash"), field="config_hash")
    split_hash = _require_sha256(payload.get("split_hash"), field="split_hash")
    data_hash = _require_sha256(
        payload.get("data_manifest_hash"),
        field="data_manifest_hash",
        allow_none=mode == "quick",
    )
    if mode == "full" and data_hash is None:
        raise ValueError(f"{family} full run requires a data manifest hash")
    git = payload.get("git")
    if git != {"commit": expected_git_sha, "dirty": False}:
        raise ValueError(f"{family} source Git provenance mismatch or dirty run")
    if payload.get("environment", {}).get("torch") in {None, "not-installed"}:
        raise ValueError(f"{family} is missing its PyTorch environment version")
    if float(payload.get("timing", {}).get("total_seconds", 0.0)) <= 0:
        raise ValueError(f"{family} is missing positive runtime timing")

    resume = payload.get("resume")
    if not isinstance(resume, list) or [item.get("seed") for item in resume] != list(MODEL_SEEDS):
        raise ValueError(f"{family} resume evidence must cover the frozen seeds")
    for item in resume:
        seed = int(item["seed"])
        expected_fingerprint = deep_resume_fingerprint(
            config_hash=str(payload["config_hash"]),
            data_manifest_hash=data_hash,
            split_hash=str(split_hash),
            source_git_sha=expected_git_sha,
            family=family,
            seed=seed,
        )
        if item.get("resume_fingerprint") != expected_fingerprint:
            raise ValueError(f"{family} seed {seed} resume fingerprint mismatch")

    required = [
        run_dir / "best_model.json",
        run_dir / "preprocessor.npz",
        run_dir / "results.json",
        run_dir / "validation_predictions.npz",
        run_dir / "plots" / "training_history.png",
        run_dir / "plots" / "validation_curves.png",
        *[run_dir / "models" / f"{family}_seed_{seed}.pt" for seed in MODEL_SEEDS],
    ]
    if any(not path.is_file() for path in required):
        raise FileNotFoundError(f"{family} run is missing a required artifact")
    artifact_hashes = payload.get("artifact_hashes")
    if not isinstance(artifact_hashes, dict):
        raise ValueError(f"{family} artifact hashes are missing")
    for relative, expected_hash in artifact_hashes.items():
        path = run_dir / str(relative)
        if not path.is_file() or sha256_file(path) != expected_hash:
            raise ValueError(f"{family} artifact hash mismatch: {relative}")

    expected_checkpoint_names = {f"{family}_seed_{seed}.pt" for seed in MODEL_SEEDS}
    checkpoint_hashes = payload.get("checkpoint_hashes")
    if (
        not isinstance(checkpoint_hashes, dict)
        or set(checkpoint_hashes) != expected_checkpoint_names
    ):
        raise ValueError(f"{family} checkpoint hash set is incomplete")
    checkpoints = [checkpoint_dir / name for name in sorted(expected_checkpoint_names)]
    for checkpoint in checkpoints:
        if (
            not checkpoint.is_file()
            or sha256_file(checkpoint) != checkpoint_hashes[checkpoint.name]
        ):
            raise ValueError(f"{family} checkpoint hash mismatch: {checkpoint.name}")
    run_files = sorted(path for path in run_dir.rglob("*") if path.is_file())
    return payload, run_files, checkpoints


def package_deep_results(
    run_dirs: list[str | Path],
    *,
    checkpoint_dir: str | Path,
    environment_lock: str | Path,
    output_dir: str | Path,
    mode: str,
    expected_git_sha: str,
) -> tuple[Path, Path]:
    """Validate GRU-D/TCN provenance and write one self-contained ZIP plus checksum."""
    if mode not in {"quick", "full"}:
        raise ValueError("mode must be quick or full")
    if len(expected_git_sha) != 40:
        raise ValueError("expected_git_sha must be a full Git SHA")
    checkpoint_root = Path(checkpoint_dir).resolve()
    lock = Path(environment_lock).resolve()
    if not lock.is_file():
        raise FileNotFoundError(lock)
    validated = [
        _validate_deep_run(
            Path(run).resolve(),
            checkpoint_dir=checkpoint_root,
            mode=mode,
            expected_git_sha=expected_git_sha,
        )
        for run in run_dirs
    ]
    payloads = [item[0] for item in validated]
    families = sorted(str(payload["model_family"]) for payload in payloads)
    if families != sorted(_FAMILIES):
        raise ValueError("result package requires exactly one GRU-D and one TCN run")
    for field in ("config_hash", "data_manifest_hash", "split_hash"):
        if len({payload.get(field) for payload in payloads}) != 1:
            raise ValueError(f"GRU-D and TCN {field} values do not match")

    destination = Path(output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    package = destination / f"carerisk48h-colab-{mode}-{stamp}-{expected_git_sha[:12]}.zip"
    partial = package.with_suffix(package.suffix + ".partial")
    file_hashes: dict[str, str] = {}
    started = time.perf_counter()
    with zipfile.ZipFile(
        partial, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for payload, run_files, checkpoints in validated:
            run_name = str(payload["run_id"])
            run_root = next(
                Path(path).resolve() for path in run_dirs if Path(path).name == run_name
            )
            for path in run_files:
                member = f"runs/{run_name}/{path.relative_to(run_root).as_posix()}"
                archive.write(path, member)
                file_hashes[member] = sha256_file(path)
            for path in checkpoints:
                member = f"checkpoints/{path.name}"
                archive.write(path, member)
                file_hashes[member] = sha256_file(path)
        lock_member = f"environment/{lock.name}"
        archive.write(lock, lock_member)
        file_hashes[lock_member] = sha256_file(lock)
        manifest = {
            "schema_version": 1,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "families": families,
            "source_git_sha": expected_git_sha,
            "config_hash": payloads[0]["config_hash"],
            "data_manifest_hash": payloads[0]["data_manifest_hash"],
            "split_hash": payloads[0]["split_hash"],
            "environment_lock_sha256": sha256_file(lock),
            "file_hashes": dict(sorted(file_hashes.items())),
            "package_build_seconds": time.perf_counter() - started,
            "set_b_accessed": False,
        }
        archive.writestr(
            "package_manifest.json",
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        )
    os.replace(partial, package)
    checksum = package.with_suffix(package.suffix + ".sha256")
    checksum.write_text(f"{sha256_file(package)}  {package.name}\n", encoding="utf-8")
    return package, checksum
