from __future__ import annotations

from pathlib import Path

import pytest

from carerisk48h.artifacts import deep_resume_fingerprint, stable_hash
from carerisk48h.config import canonical_config_payload, load_config


def _write_config(path: Path, *, split_seed: int = 2026, model_seeds: str = "17, 42, 2026") -> None:
    path.write_text(
        "\n".join(
            [
                "mode: full",
                "model: auto",
                "data_dir: data/raw",
                "output_dir: artifacts",
                f"split_seed: {split_seed}",
                f"model_seeds: [{model_seeds}]",
                "bootstrap_samples: 2000",
                "cpu_threads: 2",
                "max_patients: null",
                "epochs: 50",
                "batch_size: 64",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("split_seed", "model_seeds", "message"),
    [
        (42, "17, 42, 2026", "split_seed"),
        (2026, "17, 42", "model_seeds"),
        (2026, "2026, 42, 17", "model_seeds"),
    ],
)
def test_load_config_rejects_protocol_seed_changes(
    tmp_path: Path, split_seed: int, model_seeds: str, message: str
) -> None:
    config_path = tmp_path / "full.yaml"
    _write_config(config_path, split_seed=split_seed, model_seeds=model_seeds)
    with pytest.raises(ValueError, match=message):
        load_config(config_path, repo_root=tmp_path)


def test_canonical_config_hash_is_independent_of_checkout_location(tmp_path: Path) -> None:
    roots = [tmp_path / "local", tmp_path / "colab"]
    payloads = []
    for root in roots:
        root.mkdir()
        config_path = root / "full.yaml"
        _write_config(config_path)
        config = load_config(config_path, repo_root=root)
        payloads.append(canonical_config_payload(config, repo_root=root))

    assert payloads[0]["data_dir"] == "data/raw"
    assert payloads[0]["output_dir"] == "artifacts"
    assert stable_hash(payloads[0]) == stable_hash(payloads[1])


def test_deep_resume_fingerprint_binds_all_training_inputs() -> None:
    identity = {
        "config_hash": "config-a",
        "data_manifest_hash": "data-a",
        "split_hash": "split-a",
        "source_git_sha": "commit-a",
        "family": "grud",
        "seed": 17,
    }
    baseline = deep_resume_fingerprint(**identity)
    replacements = {
        "config_hash": "config-b",
        "data_manifest_hash": "data-b",
        "split_hash": "split-b",
        "source_git_sha": "commit-b",
        "family": "tcn",
        "seed": 42,
    }
    for field, value in replacements.items():
        changed = {**identity, field: value}
        assert deep_resume_fingerprint(**changed) != baseline
