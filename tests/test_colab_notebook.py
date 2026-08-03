from __future__ import annotations

import json
import subprocess
from pathlib import Path

from packaging.specifiers import SpecifierSet
from packaging.version import Version

NOTEBOOK_PATH = Path("notebooks/CareRisk48H_Deep_Experiments_Colab.ipynb")


def test_colab_notebook_has_safety_and_resume_contract() -> None:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    assert notebook["nbformat"] == 4
    assert notebook["metadata"]["colab"]["name"] == NOTEBOOK_PATH.name
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


def test_colab_requirements_match_cpu_and_l4_runtime_contracts() -> None:
    pins = {
        name.casefold(): version
        for line in Path("requirements-colab.txt").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
        for name, version in [line.split("==", maxsplit=1)]
    }

    assert pins["jedi"] == "0.19.2"
    assert pins["pandas"] == "2.2.2"
    numba = Version(pins["numba"])
    assert numba in SpecifierSet(">=0.58,<=0.65.1")  # CPU pytensor 2.38.3
    assert numba in SpecifierSet(">=0.60,<0.62")  # L4 cudf/cuml 26.2
    assert numba in SpecifierSet(">=0.61.2,<0.62")  # NumPy 2.2 support


def test_colab_installs_an_importable_package_in_the_current_kernel() -> None:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    code_cells = [
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    ]
    install_cell = next(cell for cell in code_cells if "requirements-colab.txt" in cell)

    assert "%pip install -q . --no-deps" in install_cell
    assert "%pip install -q -e . --no-deps" not in install_cell
    assert "from carerisk48h.artifacts import stable_hash" in install_cell
    assert "assert callable(stable_hash)" in install_cell


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
