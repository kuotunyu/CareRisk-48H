from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pytest

from carerisk48h.data.downloader import sha256_file
from carerisk48h.freezing import create_freeze_manifest


class StaticAgeModel:
    def predict_proba(self, frame):
        age = frame["static_Age"].to_numpy(dtype=float)
        probability = np.where(age >= 65.0, 0.8, 0.2)
        return np.column_stack([1.0 - probability, probability])


class IdentityCalibrator:
    def predict(self, scores):
        return np.asarray(scores, dtype=np.float64)


def _write_record(path: Path, *, record_id: int, age: int, gender: int, icu_type: int) -> None:
    path.write_text(
        "\n".join(
            [
                "Time,Parameter,Value",
                f"00:00,RecordID,{record_id}",
                f"00:00,Age,{age}",
                f"00:00,Gender,{gender}",
                "00:00,Height,170",
                f"00:00,ICUType,{icu_type}",
                "00:00,Weight,70",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_candidate(candidate: Path) -> None:
    candidate.mkdir(parents=True)
    bundle = candidate / "final_candidate.joblib"
    joblib.dump(
        {
            "schema_version": 1,
            "model_family": "lightgbm",
            "models": [StaticAgeModel(), StaticAgeModel(), StaticAgeModel()],
            "model_seeds": [17, 42, 2026],
            "feature_columns": ["static_Age"],
            "calibrator": IdentityCalibrator(),
            "calibration_method": "platt",
            "threshold": 0.5,
            "target_specificity": 0.9,
            "training_scope": "Set A train+validation",
            "calibration_fit_scope": "Set A calibration",
        },
        bundle,
    )
    environment = candidate / "environment-lock.json"
    environment.write_text('{"python":"fixture"}\n', encoding="utf-8")
    dry_run = candidate / "set_a_dry_run.json"
    dry_run.write_text(
        json.dumps(
            {
                "evaluation_status": "set_a_reused_development_dry_run",
                "set_b_accessed": False,
            }
        ),
        encoding="utf-8",
    )
    split = candidate / "set_a_split.csv"
    split.write_text("RecordID,split\n1,train\n", encoding="utf-8")
    data = candidate / "manifest-set-a.json"
    data.write_text('{"set":"a"}\n', encoding="utf-8")
    metadata = {
        "source_git_sha": "a" * 40,
        "source_git_dirty": False,
        "config_hash": "b" * 64,
        "data_manifest_hash": "c" * 64,
        "split_hash": "d" * 64,
        "model_family": "lightgbm",
        "model_seeds": [17, 42, 2026],
        "training_scope": "Set A train+validation",
        "calibration_fit_scope": "Set A calibration",
        "calibrator": {"method": "platt"},
        "threshold": 0.5,
        "target_specificity": 0.90,
        "environment": {"python": "fixture"},
        "environment_lock_sha256": sha256_file(environment),
        "set_a_dry_run": {
            "status": "passed",
            "set_b_accessed": False,
            "artifact_sha256": sha256_file(dry_run),
        },
    }
    create_freeze_manifest(
        candidate_metadata=metadata,
        artifact_paths=[bundle, environment, dry_run],
        split_manifest_path=split,
        data_manifest_path=data,
        output_path=candidate / "freeze_manifest.json",
        confirm_freeze=True,
    )


def _write_set_b_inputs(raw: Path, *, records: int = 40) -> tuple[Path, Path, Path]:
    records_dir = raw / "set-b"
    records_dir.mkdir(parents=True)
    labels: list[str] = ["RecordID,In-hospital_death"]
    ages = (40, 55, 70, 85)
    for index in range(records):
        record_id = 1000 + index
        age = ages[index % len(ages)]
        _write_record(
            records_dir / f"{record_id}.txt",
            record_id=record_id,
            age=age,
            gender=index % 2,
            icu_type=index % 4 + 1,
        )
        labels.append(f"{record_id},{int(age >= 65)}")
    outcomes = raw / "Outcomes-b.txt"
    outcomes.write_text("\n".join(labels) + "\n", encoding="utf-8")
    archive = raw / "set-b.tar.gz"
    archive.write_bytes(b"input-only fixture archive")
    manifest = raw / "manifest-set-b.json"
    manifest.write_text(
        json.dumps(
            {
                "dataset": "PhysioNet/Computing in Cardiology Challenge 2012",
                "version": "1.0.0",
                "set": "b",
                "files": [
                    {
                        "filename": archive.name,
                        "url": "https://example.test/set-b.tar.gz",
                        "bytes": archive.stat().st_size,
                        "sha256": sha256_file(archive),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return records_dir, outcomes, manifest


def _clean_repo(path: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    (path / ".gitignore").write_text("candidate/\nraw/\n", encoding="utf-8")
    (path / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore", "README.md"], cwd=path, check=True)
    environment = {
        "GIT_AUTHOR_NAME": "Fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.test",
        "GIT_COMMITTER_NAME": "Fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.test",
    }
    subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=path, check=True, env=environment)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_final_evaluation_produces_locked_formal_package(tmp_path) -> None:
    from carerisk48h.final_evaluation import run_set_b_final_evaluation

    expected_evaluation_sha = _clean_repo(tmp_path)
    candidate = tmp_path / "candidate"
    _write_candidate(candidate)
    records, outcomes, manifest = _write_set_b_inputs(tmp_path / "raw")

    metrics_path, payload = run_set_b_final_evaluation(
        candidate_dir=candidate,
        records_dir=records,
        outcomes_path=outcomes,
        input_manifest_path=manifest,
        repo_root=tmp_path,
        confirm_final=True,
        bootstrap_samples=10,
        expected_records=40,
    )

    assert metrics_path == candidate / "set_b_final" / "metrics.json"
    assert payload["evaluation_status"] == "final"
    assert payload["run_id"].endswith("-lightgbm-set-b-final")
    assert datetime.fromisoformat(payload["created_at_utc"]).tzinfo is not None
    assert payload["dataset"] == "PhysioNet Challenge 2012 Set B"
    assert payload["freeze_status"] == "frozen"
    assert payload["set_b_final_evaluation_successes"] == 1
    assert payload["bootstrap"] == {
        "method": "stratified percentile",
        "samples": 10,
        "seed": 2026,
    }
    assert payload["model_family"] == "lightgbm"
    assert payload["model_seeds"] == [17, 42, 2026]
    assert payload["metrics"]["n"] == 40
    assert payload["metrics"]["threshold"] == 0.5
    assert payload["evaluation_source_git_sha"] == expected_evaluation_sha
    assert payload["evaluation_source_git_dirty"] is False
    assert payload["subgroups"]
    assert json.loads(metrics_path.read_text(encoding="utf-8")) == payload
    for relative, expected_hash in payload["artifact_hashes"].items():
        assert sha256_file(candidate / relative) == expected_hash
    ledger = candidate / "set_b_access_ledger.json"
    ledger_payload = json.loads(ledger.read_text(encoding="utf-8"))
    assert [item["status"] for item in ledger_payload["attempts"]] == ["success"]
    assert candidate.joinpath("set_b_access_ledger.final-lock.json").is_file()


def test_final_evaluation_refuses_existing_output_before_outcome_access(tmp_path) -> None:
    from carerisk48h.final_evaluation import run_set_b_final_evaluation

    _clean_repo(tmp_path)
    candidate = tmp_path / "candidate"
    _write_candidate(candidate)
    records, outcomes, manifest = _write_set_b_inputs(tmp_path / "raw")
    (candidate / "set_b_final").mkdir()

    with pytest.raises(FileExistsError, match="output"):
        run_set_b_final_evaluation(
            candidate_dir=candidate,
            records_dir=records,
            outcomes_path=outcomes,
            input_manifest_path=manifest,
            repo_root=tmp_path,
            confirm_final=True,
            bootstrap_samples=10,
            expected_records=40,
        )
    assert not candidate.joinpath("set_b_access_ledger.json").exists()


def test_final_evaluation_rejects_manifest_containing_outcomes_before_access(tmp_path) -> None:
    from carerisk48h.final_evaluation import run_set_b_final_evaluation

    _clean_repo(tmp_path)
    candidate = tmp_path / "candidate"
    _write_candidate(candidate)
    records, outcomes, manifest = _write_set_b_inputs(tmp_path / "raw")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["files"].append(
        {
            "filename": "Outcomes-b.txt",
            "url": "https://example.test/Outcomes-b.txt",
            "bytes": outcomes.stat().st_size,
            "sha256": sha256_file(outcomes),
        }
    )
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="input-only"):
        run_set_b_final_evaluation(
            candidate_dir=candidate,
            records_dir=records,
            outcomes_path=outcomes,
            input_manifest_path=manifest,
            repo_root=tmp_path,
            confirm_final=True,
            bootstrap_samples=10,
            expected_records=40,
        )
    assert not candidate.joinpath("set_b_access_ledger.json").exists()
