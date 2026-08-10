from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_container_is_non_root_and_ci_smoke_is_launch_free() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    user_directives = [
        line.split(maxsplit=1)[1]
        for line in dockerfile.splitlines()
        if line.strip().upper().startswith("USER ")
    ]
    workflow = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )

    assert user_directives[-1] == "carerisk"
    assert workflow["permissions"] == {"contents": "read"}
    container = workflow["jobs"]["container"]
    commands = "\n".join(step.get("run", "") for step in container["steps"])
    assert "docker build" in commands
    assert "--cpus=2" in commands
    assert "CUDA_VISIBLE_DEVICES=" in commands
    assert "os.geteuid() != 0" in commands
    assert "create_app()" in commands
    assert "launch(" not in commands
