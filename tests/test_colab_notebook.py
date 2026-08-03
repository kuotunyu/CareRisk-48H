from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_colab_notebook_has_safety_and_resume_contract() -> None:
    notebook = json.loads(Path("notebooks/01_train_colab.ipynb").read_text(encoding="utf-8"))
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    assert notebook["nbformat"] == 4
    assert "STAGE = 'prepare'" in source
    assert "Switch Colab to a CPU runtime" in source
    assert "--resume" in source
    assert "--synthetic" in source
    assert "Set B" in source
    assert "git', 'clone'" in source
    assert "bundle_sha256" in source
    assert "--verify-only" in source
    assert "generate_data_quality.py" in source
    assert "package_deep_results" in source
    assert "EXPECTED_GPU = 'L4'" in source
    assert "requested L4-first policy" in source


def test_clean_git_source_contains_every_package_module() -> None:
    package_files = sorted(Path("src/carerisk48h").rglob("*.py"))
    tracked = set(
        subprocess.run(
            ["git", "ls-files", "--", "src/carerisk48h"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    )
    missing = [path.as_posix() for path in package_files if path.as_posix() not in tracked]
    assert missing == []
