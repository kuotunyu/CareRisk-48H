from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import types
from pathlib import Path

import pytest
from packaging.specifiers import SpecifierSet
from packaging.version import Version

NOTEBOOK_PATH = Path("notebooks/CareRisk48H_Deep_Experiments_Colab.ipynb")


def _source_setup_cell() -> str:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    return next(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
        and "carerisk48h-source-receipt.json" in "".join(cell.get("source", []))
    )


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
    assert "deep_checkpoint_directory" in source
    assert "checkpoint_dir=checkpoint_dir" in source
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


def test_source_setup_can_run_twice_in_the_same_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    origin = tmp_path / "origin"
    origin.mkdir()
    subprocess.run(
        ["git", "init", "--initial-branch=main"],
        cwd=origin,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "CareRisk test"],
        cwd=origin,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "carerisk-test@example.invalid"],
        cwd=origin,
        check=True,
    )
    (origin / ".gitignore").write_text("/data\n/artifacts\n/checkpoints\n", encoding="utf-8")
    (origin / "tracked.txt").write_text("immutable source\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=origin, check=True)
    subprocess.run(
        ["git", "commit", "-m", "fixture"],
        cwd=origin,
        check=True,
        capture_output=True,
    )
    source_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=origin,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    handoff = tmp_path / "handoff"
    handoff.mkdir()
    bundle = handoff / "source.bundle"
    subprocess.run(
        ["git", "bundle", "create", str(bundle), "main"],
        cwd=origin,
        check=True,
        capture_output=True,
    )
    receipt = {
        "bundle_filename": bundle.name,
        "bundle_sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
        "source_branch": "main",
        "source_git_sha": source_sha,
    }
    (handoff / "carerisk48h-source-receipt.json").write_text(json.dumps(receipt), encoding="utf-8")

    project = tmp_path / "CareRisk48H-source"
    persistent = tmp_path / "runtime"
    source = _source_setup_cell().replace(
        "Path('/content/CareRisk48H-source')", f"Path({str(project)!r})"
    )
    drive = types.ModuleType("google.colab.drive")
    drive.mount = lambda *_args, **_kwargs: None  # type: ignore[attr-defined]
    colab = types.ModuleType("google.colab")
    colab.drive = drive  # type: ignore[attr-defined]
    google = types.ModuleType("google")
    google.colab = colab  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.colab", colab)
    monkeypatch.setitem(sys.modules, "google.colab.drive", drive)
    monkeypatch.setattr(
        type(project),
        "symlink_to",
        lambda self, _target, target_is_directory=False: self.mkdir(),
    )
    real_rmtree = shutil.rmtree

    def remove_checkout(path: str | Path) -> None:
        checkout = Path(path).resolve()
        current = Path.cwd().resolve()
        if current == checkout or checkout in current.parents:
            raise OSError("cannot delete the active source working directory")

        def remove_readonly(function: object, target: str, _error: object) -> None:
            os.chmod(target, stat.S_IWRITE)
            function(target)  # type: ignore[operator]

        real_rmtree(path, onerror=remove_readonly)

    monkeypatch.setattr(shutil, "rmtree", remove_checkout)

    namespace = {
        "HANDOFF_DIR": str(handoff),
        "PERSISTENT_DIR": str(persistent),
    }
    original_cwd = Path.cwd()
    try:
        exec(compile(source, str(NOTEBOOK_PATH), "exec"), namespace)
        exec(compile(source, str(NOTEBOOK_PATH), "exec"), namespace)
    except (OSError, subprocess.CalledProcessError) as exc:
        pytest.fail(f"source setup was not rerunnable: {exc}")
    finally:
        os.chdir(original_cwd)

    assert (project / "tracked.txt").read_text(encoding="utf-8") == "immutable source\n"


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
