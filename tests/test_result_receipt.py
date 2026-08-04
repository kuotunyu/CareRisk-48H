from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def _exporter_module():
    path = ROOT / "scripts" / "export_final_result_receipt.py"
    spec = importlib.util.spec_from_file_location("export_final_result_receipt", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load final-result receipt exporter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _valid_payload() -> dict:
    metrics = {
        "n": 4000,
        "events": 568,
        "prevalence": 0.142,
        "auprc": 0.5549611311053255,
        "auroc": 0.8696003233855347,
        "brier": 0.08662893958425562,
        "ece": 0.007835639822692777,
        "sensitivity": 0.5809859154929577,
        "specificity": 0.9087995337995338,
        "ppv": 0.5132192846034215,
        "npv": 0.9291033661006851,
        "threshold": 0.2974276505509685,
        "confusion": {"tn": 3119, "fp": 313, "fn": 238, "tp": 330},
    }
    intervals = {
        name: {"estimate": metrics[name], "lower": lower, "upper": upper}
        for name, lower, upper in (
            ("auprc", 0.5159391486187543, 0.5941855615749009),
            ("auroc", 0.8547766823845169, 0.8836828041383498),
            ("brier", 0.08294065055139704, 0.09036869670238311),
            ("ece", 0.006992943602957658, 0.019300500350357373),
            ("sensitivity", 0.5404929577464789, 0.6197183098591549),
            ("specificity", 0.8997668997668997, 0.9181235431235432),
            ("ppv", 0.48259379621981907, 0.5441176470588235),
            ("npv", 0.9228033896547718, 0.9350966412586362),
        )
    }
    return {
        "run_id": "20260804T025633Z-lightgbm-set-b-final",
        "created_at_utc": "2026-08-04T02:56:33.311607+00:00",
        "evaluation_status": "final",
        "dataset": "PhysioNet Challenge 2012 Set B",
        "freeze_status": "frozen",
        "set_b_final_evaluation_successes": 1,
        "bootstrap": {
            "samples": 2000,
            "method": "stratified percentile",
            "seed": 2026,
        },
        "model_family": "lightgbm",
        "model_seeds": [17, 42, 2026],
        "calibrator": {
            "method": "platt",
            "coefficients": ["DO_NOT_COPY_CALIBRATOR_COEFFICIENT"],
        },
        "threshold": metrics["threshold"],
        "candidate_source_git_sha": "a" * 40,
        "evaluation_source_git_sha": "b" * 40,
        "evaluation_source_git_dirty": False,
        "freeze_manifest_sha256": "c" * 64,
        "config_hash": "d" * 64,
        "data_manifest_hash": "e" * 64,
        "split_hash": "f" * 64,
        "set_b_input_manifest_sha256": "1" * 64,
        "set_b_record_ids_sha256": "2" * 64,
        "outcomes_sha256": "3" * 64,
        "environment": {"python": "DO_NOT_COPY_ENVIRONMENT"},
        "artifact_hashes": {
            "set_b_access_ledger.json": "4" * 64,
            "set_b_access_ledger.final-lock.json": "5" * 64,
        },
        "subgroups": [{"subgroup": "DO_NOT_COPY_SUBGROUP", "level": "x"}],
        "record_ids": ["DO_NOT_COPY_RECORD_ID"],
        "predictions": ["DO_NOT_COPY_PREDICTION"],
        "metrics": metrics,
        "confidence_intervals": intervals,
    }


def test_exporter_import_is_independent_of_repository_root(tmp_path: Path) -> None:
    exporter = ROOT / "scripts" / "export_final_result_receipt.py"
    code = """
import importlib.util
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("isolated_receipt_exporter", path)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print(module.build_public_receipt.__name__)
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")

    result = subprocess.run(
        [sys.executable, "-c", code, str(exporter)],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "build_public_receipt"


def test_public_receipt_whitelists_only_aggregate_results() -> None:
    exporter = _exporter_module()
    receipt = exporter.build_public_receipt(_valid_payload(), metrics_sha256="9" * 64)

    assert set(receipt) == {
        "schema_version",
        "title",
        "evaluation_status",
        "use_limitation",
        "dataset",
        "model",
        "evaluation",
        "metrics",
        "confidence_intervals",
        "provenance",
        "privacy",
    }
    assert receipt["dataset"] == {
        "name": "PhysioNet Challenge 2012 Set B",
        "role": "final_test",
        "n": 4000,
        "events": 568,
        "prevalence": 0.142,
    }
    assert receipt["model"] == {
        "family": "lightgbm",
        "seeds": [17, 42, 2026],
        "calibrator": "platt",
        "threshold": 0.2974276505509685,
    }
    assert set(receipt["provenance"]) == {
        "candidate_source_git_sha",
        "evaluation_source_git_sha",
        "evaluation_source_git_dirty",
        "freeze_manifest_sha256",
        "config_hash",
        "data_manifest_hash",
        "split_hash",
        "set_b_input_manifest_sha256",
        "formal_metrics_sha256",
    }
    serialized = json.dumps(receipt, sort_keys=True)
    for private_value in (
        "DO_NOT_COPY_CALIBRATOR_COEFFICIENT",
        "DO_NOT_COPY_ENVIRONMENT",
        "DO_NOT_COPY_SUBGROUP",
        "DO_NOT_COPY_RECORD_ID",
        "DO_NOT_COPY_PREDICTION",
    ):
        assert private_value not in serialized
    assert receipt["privacy"]["aggregate_only"] is True


def test_public_receipt_rejects_nonfinal_payload() -> None:
    exporter = _exporter_module()
    payload = _valid_payload()
    payload["evaluation_status"] = "development"

    with pytest.raises(ValueError, match="refuses"):
        exporter.build_public_receipt(payload, metrics_sha256="9" * 64)


def test_receipt_cli_is_deterministic(tmp_path: Path) -> None:
    exporter = _exporter_module()
    source = tmp_path / "metrics.json"
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    source.write_text(json.dumps(_valid_payload(), sort_keys=True), encoding="utf-8")

    exporter.main(["--metrics", str(source), "--output", str(first)])
    exporter.main(["--metrics", str(source), "--output", str(second)])

    assert first.read_bytes() == second.read_bytes()
    receipt = json.loads(first.read_text(encoding="utf-8"))
    assert (
        receipt["provenance"]["formal_metrics_sha256"]
        == hashlib.sha256(source.read_bytes()).hexdigest()
    )


def test_committed_receipt_matches_formal_public_values() -> None:
    receipt = json.loads((ROOT / "docs" / "final-result-receipt.json").read_text(encoding="utf-8"))

    assert receipt["evaluation_status"] == "final"
    assert receipt["evaluation"]["set_b_final_evaluation_successes"] == 1
    assert receipt["evaluation"]["final_lock_status"] == "locked_after_one_success"
    assert receipt["metrics"]["auprc"] == 0.5549611311053255
    assert receipt["confidence_intervals"]["auprc"] == {
        "estimate": 0.5549611311053255,
        "lower": 0.5159391486187543,
        "upper": 0.5941855615749009,
    }
    assert receipt["provenance"]["formal_metrics_sha256"] == (
        "808525afad2ec550e8059c4ba37c2f5aaf8af748873a5a590dff7f1aeaaf47af"
    )


def test_readme_links_to_machine_readable_receipt() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "[Machine-readable final-result receipt](docs/final-result-receipt.json)" in readme


def test_citation_identifies_the_sole_release_author() -> None:
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))

    assert citation["version"] == "0.1.0"
    assert str(citation["date-released"]) == "2026-08-04"
    assert citation["authors"] == [{"name": "kuotunyu"}]
    assert citation["repository-code"] == "https://github.com/kuotunyu/CareRisk-48H"
    assert "preferred-citation" not in citation
    assert {reference["title"] for reference in citation["references"]} == {
        "PhysioBank, PhysioToolkit, and PhysioNet: Components of a New Research "
        "Resource for Complex Physiologic Signals",
        "Predicting in-hospital mortality of ICU patients: The PhysioNet/Computing "
        "in Cardiology Challenge 2012",
    }


def test_ci_exercises_every_declared_python_minor() -> None:
    workflow = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )
    job = workflow["jobs"]["test"]

    assert workflow["permissions"] == {"contents": "read"}
    assert job["strategy"]["matrix"]["python-version"] == ["3.10", "3.11", "3.12"]
    assert any(step.get("uses") == "actions/checkout@v7" for step in job["steps"])
    setup = next(step for step in job["steps"] if step.get("uses") == "actions/setup-python@v7")
    assert setup["with"]["python-version"] == "${{ matrix.python-version }}"


def test_release_metadata_is_discoverable_and_modern() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    repository = "https://github.com/kuotunyu/CareRisk-48H"
    release = f"{repository}/releases/tag/v0.1.0"
    workflow = f"{repository}/actions/workflows/ci.yml"

    assert "setuptools>=77.0.3" in pyproject
    assert 'license = "Apache-2.0"' in pyproject
    assert 'license-files = ["LICENSE", "NOTICE"]' in pyproject
    assert f'Homepage = "{repository}"' in pyproject
    assert f'Repository = "{repository}"' in pyproject
    assert f'Release = "{release}"' in pyproject
    assert f"]({release})" in readme
    assert f"]({workflow})" in readme
    assert "[Inference JSON Schema](configs/inference_schema.json)" in readme


def test_local_only_synthetic_fixture_is_not_tracked() -> None:
    tracked = subprocess.run(
        ["git", "ls-files", "--", "app/fixtures/synthetic_patient.json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    assert tracked == ""
