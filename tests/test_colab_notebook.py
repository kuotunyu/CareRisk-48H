from __future__ import annotations

import json
from pathlib import Path


def test_colab_notebook_has_safety_and_resume_contract() -> None:
    notebook = json.loads(Path("notebooks/01_train_colab.ipynb").read_text(encoding="utf-8"))
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    assert notebook["nbformat"] == 4
    assert "DOWNLOAD_SET_A" in source
    assert "Switch Colab to a CPU runtime" in source
    assert "--resume" in source
    assert "--synthetic" in source
    assert "Set B" in source
