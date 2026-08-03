from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")

from carerisk48h.constants import MODEL_SEEDS


def _ids_hash(record_ids: list[int]) -> str:
    encoded = json.dumps(record_ids, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_final_refit_uses_only_refit_and_calibration_scopes(tmp_path: Path) -> None:
    try:
        from carerisk48h.final_refit import refit_lightgbm_candidate
    except ModuleNotFoundError as exc:
        pytest.fail(f"final refit implementation is missing: {exc}")
    record_ids = list(range(1, 46))
    splits = ["train"] * 21 + ["validation"] * 12 + ["calibration"] * 12
    labels = [index % 2 for index in range(45)]
    cohort = pd.DataFrame(
        {
            "RecordID": record_ids,
            "static_ICUType": [(index % 4) + 1 for index in range(45)],
            "HR__mean": [60.0 + index + 8.0 * labels[index] for index in range(45)],
            "HR__slope": [0.1 * (index % 5) + 0.3 * labels[index] for index in range(45)],
            "label": labels,
            "split": splits,
        }
    )
    output = tmp_path / "frozen-candidate"
    dry_run = output / "set_a_dry_run" / "evaluation.json"
    dry_run.parent.mkdir(parents=True)
    dry_run.write_text(
        json.dumps(
            {
                "evaluation_status": "set_a_reused_development_dry_run",
                "set_b_accessed": False,
            }
        ),
        encoding="utf-8",
    )

    metadata_path, metadata = refit_lightgbm_candidate(
        cohort,
        feature_columns=["static_ICUType", "HR__mean", "HR__slope"],
        parameters={"n_estimators": 5, "num_leaves": 3, "min_child_samples": 2},
        model_seeds=MODEL_SEEDS,
        n_jobs=1,
        output_dir=output,
        source_git_sha="a" * 40,
        source_git_dirty=False,
        selection_sha256="b" * 64,
        data_manifest_hash="c" * 64,
        split_hash="d" * 64,
        environment={"lightgbm": "4.6.0", "python": "test"},
        dry_run_evaluation_path=dry_run,
        target_specificity=0.90,
    )

    refit_ids = list(range(1, 34))
    calibration_ids = list(range(34, 46))
    assert metadata_path == output / "candidate_metadata.json"
    assert metadata["model_family"] == "lightgbm"
    assert metadata["model_seeds"] == [17, 42, 2026]
    assert metadata["training_scope"] == "Set A train+validation"
    assert metadata["preprocessor_fit_scope"] == "Set A train+validation"
    assert metadata["calibration_fit_scope"] == "Set A calibration"
    assert metadata["threshold_fit_scope"] == "Set A calibration"
    assert metadata["fit_record_ids_sha256"] == _ids_hash(refit_ids)
    assert metadata["calibration_record_ids_sha256"] == _ids_hash(calibration_ids)
    assert metadata["fit_counts"] == {"calibration": 12, "train": 21, "validation": 12}
    assert metadata["calibrator"] == {"method": "platt"}
    assert metadata["target_specificity"] == 0.90
    assert metadata["calibration_operating_point"]["specificity"] >= 0.90
    assert 0.0 <= metadata["threshold"] <= 1.0
    assert metadata["set_a_dry_run"]["status"] == "passed"
    assert metadata["set_a_dry_run"]["set_b_accessed"] is False
    assert metadata["set_b_accessed"] is False

    bundle = joblib.load(output / "final_candidate.joblib")
    with np.load(output / "calibration_predictions.npz") as saved:
        calibration = cohort[cohort["split"] == "calibration"]
        matrix = calibration[bundle["feature_columns"]]
        raw = np.mean(
            np.stack([model.predict_proba(matrix)[:, 1] for model in bundle["models"]]), axis=0
        )
        calibrated = bundle["calibrator"].predict(raw)
        np.testing.assert_allclose(raw, saved["raw_probabilities"])
        np.testing.assert_allclose(calibrated, saved["probabilities"])
        np.testing.assert_array_equal(saved["record_ids"], calibration_ids)

    assert sorted(path.name for path in (output / "models").glob("*.joblib")) == [
        "lightgbm_seed_17.joblib",
        "lightgbm_seed_2026.joblib",
        "lightgbm_seed_42.joblib",
    ]
    assert (output / "calibrator.joblib").is_file()
    assert (output / "environment-lock.json").is_file()


def test_final_refit_rejects_dry_run_that_accessed_set_b(tmp_path: Path) -> None:
    try:
        from carerisk48h.final_refit import refit_lightgbm_candidate
    except ModuleNotFoundError as exc:
        pytest.fail(f"final refit implementation is missing: {exc}")
    output = tmp_path / "output"
    dry_run = output / "set_a_dry_run" / "evaluation.json"
    dry_run.parent.mkdir(parents=True)
    dry_run.write_text(json.dumps({"set_b_accessed": True}), encoding="utf-8")
    cohort = pd.DataFrame(
        {
            "RecordID": [1, 2, 3, 4],
            "static_ICUType": [1, 1, 2, 2],
            "feature": [0.0, 1.0, 2.0, 3.0],
            "label": [0, 1, 0, 1],
            "split": ["train", "validation", "calibration", "calibration"],
        }
    )

    with pytest.raises(ValueError, match="Set B"):
        refit_lightgbm_candidate(
            cohort,
            feature_columns=["static_ICUType", "feature"],
            parameters={"n_estimators": 2},
            model_seeds=MODEL_SEEDS,
            n_jobs=1,
            output_dir=output,
            source_git_sha="a" * 40,
            source_git_dirty=False,
            selection_sha256="b" * 64,
            data_manifest_hash="c" * 64,
            split_hash="d" * 64,
            environment={"python": "test"},
            dry_run_evaluation_path=dry_run,
        )
