from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from carerisk48h.config import load_config
from carerisk48h.synthetic import generate_synthetic_cohort
from carerisk48h.training import train_logistic


def test_synthetic_logistic_vertical_slice(tmp_path: Path) -> None:
    config = load_config("configs/quick.yaml", repo_root=Path.cwd())
    config = replace(config, output_dir=tmp_path / "artifacts", max_patients=160)
    stays, outcomes = generate_synthetic_cohort(160)
    run_dir, payload = train_logistic(stays, outcomes, config, repo_root=Path.cwd())
    assert payload["evaluation_status"] == "smoke_test"
    assert payload["metrics"]["auprc"] is not None
    assert (run_dir / "best_model.joblib").exists()
    assert (run_dir / "metrics.json").exists()
    assert (run_dir / "split_manifest.csv").exists()
