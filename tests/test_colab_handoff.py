from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from carerisk48h.artifacts import deep_resume_fingerprint, stable_hash
from carerisk48h.colab_handoff import create_source_bundle, package_deep_results
from carerisk48h.data.downloader import sha256_file

SEEDS = (17, 42, 2026)


def test_source_bundle_is_cloneable_and_receipted(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    (repo / "tracked.txt").write_text("source\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "fixture",
        ],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    bundle, receipt_path = create_source_bundle(repo, tmp_path / "handoff")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["bundle_sha256"] == sha256_file(bundle)
    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", "--branch", receipt["source_branch"], str(bundle), str(clone)],
        check=True,
        capture_output=True,
    )
    cloned_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=clone, check=True, capture_output=True, text=True
    ).stdout.strip()
    assert cloned_sha == receipt["source_git_sha"]


def test_source_bundle_rejects_forbidden_paths_deleted_from_head(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    forbidden = repo / "artifacts" / "generated.bin"
    forbidden.parent.mkdir(parents=True)
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    forbidden.write_bytes(b"generated")
    subprocess.run(["git", "add", "artifacts/generated.bin"], cwd=repo, check=True)
    commit = [
        "git",
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-m",
    ]
    subprocess.run([*commit, "add generated file"], cwd=repo, check=True, capture_output=True)
    forbidden.unlink()
    subprocess.run(["git", "add", "-u"], cwd=repo, check=True)
    subprocess.run([*commit, "remove generated file"], cwd=repo, check=True, capture_output=True)

    with pytest.raises(ValueError, match="forbidden"):
        create_source_bundle(repo, tmp_path / "handoff")


def _write_run(root: Path, family: str, *, source_sha: str) -> Path:
    run = root / f"20260803T000000Z-{family}-full"
    (run / "models").mkdir(parents=True)
    (run / "plots").mkdir()
    files = [
        run / "best_model.json",
        run / "preprocessor.npz",
        run / "training_log.json",
        run / "validation_predictions.npz",
        run / "plots" / "training_history.png",
        run / "plots" / "validation_curves.png",
    ]
    model_files = [run / "models" / f"{family}_seed_{seed}.pt" for seed in SEEDS]
    for path in [*files, *model_files]:
        path.write_bytes(f"fixture:{path.name}".encode())
    config = {
        "mode": "full",
        "model": "auto",
        "data_dir": "data/raw",
        "output_dir": "artifacts",
        "split_seed": 2026,
        "model_seeds": list(SEEDS),
        "bootstrap_samples": 2000,
        "cpu_threads": 2,
        "max_patients": None,
        "epochs": 50,
        "batch_size": 64,
    }
    config_hash = stable_hash(config)
    split_hash = "a" * 64
    data_hash = "b" * 64
    checkpoint_hashes = {
        f"{family}_seed_{seed}.pt": "" for seed in SEEDS
    }
    resume = [
        {
            "seed": seed,
            "resume_requested": True,
            "checkpoint_found": False,
            "resumed": False,
            "start_epoch": 0,
            "epochs_executed": 10,
            "completed_epochs": 10,
            "early_stopping_reached": True,
            "checkpoint_file": f"{family}_seed_{seed}.pt",
            "resume_fingerprint": deep_resume_fingerprint(
                config_hash=config_hash,
                data_manifest_hash=data_hash,
                split_hash=split_hash,
                source_git_sha=source_sha,
                family=family,
                seed=seed,
            ),
        }
        for seed in SEEDS
    ]
    payload = {
        "run_id": run.name,
        "evaluation_status": "development",
        "selection_scope": "Set A train to validation only; calibration untouched",
        "model_family": family,
        "seed_metrics": [{"seed": seed, "auprc": 0.4} for seed in SEEDS],
        "ensemble_metrics": {"auprc": 0.4, "brier": 0.1, "ece": 0.03},
        "seeds": {"split": 2026, "models": list(SEEDS)},
        "config": config,
        "config_hash": config_hash,
        "data_manifest_hash": data_hash,
        "split_hash": split_hash,
        "git": {"commit": source_sha, "dirty": False},
        "environment": {"torch": "2.10.0"},
        "artifact_hashes": {
            path.relative_to(run).as_posix(): sha256_file(path)
            for path in [*model_files, run / "preprocessor.npz"]
        },
        "checkpoint_hashes": checkpoint_hashes,
        "resume": resume,
        "timing": {"total_seconds": 12.5, "per_seed": []},
    }
    (run / "metrics.json").write_text(json.dumps(payload), encoding="utf-8")
    (run / "results.json").write_text(json.dumps(payload), encoding="utf-8")
    return run


def test_result_package_verifies_runs_checkpoints_and_environment(tmp_path: Path) -> None:
    source_sha = "c" * 40
    runs = [_write_run(tmp_path, family, source_sha=source_sha) for family in ("grud", "tcn")]
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    for run in runs:
        payload = json.loads((run / "metrics.json").read_text(encoding="utf-8"))
        for filename in payload["checkpoint_hashes"]:
            checkpoint = checkpoints / filename
            checkpoint.write_bytes(f"checkpoint:{filename}".encode())
            payload["checkpoint_hashes"][filename] = sha256_file(checkpoint)
        (run / "metrics.json").write_text(json.dumps(payload), encoding="utf-8")
        (run / "results.json").write_text(json.dumps(payload), encoding="utf-8")
    lock = tmp_path / "environment-full.lock.txt"
    lock.write_text("torch==2.10.0\n", encoding="utf-8")

    package, checksum = package_deep_results(
        runs,
        checkpoint_dir=checkpoints,
        environment_lock=lock,
        output_dir=tmp_path / "packages",
        mode="full",
        expected_git_sha=source_sha,
    )
    assert checksum.read_text(encoding="utf-8").split()[0] == sha256_file(package)
    with zipfile.ZipFile(package) as archive:
        manifest = json.loads(archive.read("package_manifest.json"))
    assert manifest["families"] == ["grud", "tcn"]
    assert manifest["source_git_sha"] == source_sha
    assert manifest["set_b_accessed"] is False

    model = runs[0] / "models" / "grud_seed_17.pt"
    model.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="artifact hash mismatch"):
        package_deep_results(
            runs,
            checkpoint_dir=checkpoints,
            environment_lock=lock,
            output_dir=tmp_path / "tampered-package",
            mode="full",
            expected_git_sha=source_sha,
        )
