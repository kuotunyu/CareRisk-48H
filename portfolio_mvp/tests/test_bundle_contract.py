from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from scripts.build_space_candidate import (
    SPACE_PATHS,
    CandidateError,
    audit_candidate,
    build_candidate,
)


MVP_ROOT = Path(__file__).parents[1]
REPOSITORY_ROOT = MVP_ROOT.parent
EXPECTED_SPACE_PATHS = (
    "README.md",
    "LICENSE",
    "NOTICE",
    "Dockerfile",
    "requirements.txt",
    "app.py",
    "carerisk_mvp/__init__.py",
    "carerisk_mvp/content.py",
    "carerisk_mvp/ui.py",
)


def _write_valid_source(root: Path) -> None:
    for relative in EXPECTED_SPACE_PATHS:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"safe fixture for {relative}\n", encoding="utf-8")


def test_runtime_requirement_is_one_exact_pin() -> None:
    assert (MVP_ROOT / "requirements.txt").read_bytes() == b"gradio==6.26.0\n"


def test_dockerfile_is_a_small_non_root_exact_copy_runtime() -> None:
    dockerfile = (MVP_ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert dockerfile.startswith("FROM python:3.11.14-slim-bookworm\n")
    assert "EXPOSE 7860" in dockerfile
    assert 'CMD ["python", "app.py"]' in dockerfile
    assert re.search(r"^USER\s+carerisk$", dockerfile, re.MULTILINE)
    assert "COPY requirements.txt /app/requirements.txt" in dockerfile
    for relative in EXPECTED_SPACE_PATHS[5:]:
        assert f"COPY {relative} /app/{relative}" in dockerfile
    assert "COPY . " not in dockerfile
    assert "ADD " not in dockerfile
    assert "*" not in dockerfile
    assert "space/" not in dockerfile
    assert "browser" not in dockerfile.casefold()


def test_space_card_and_notice_disclose_the_narrow_boundary() -> None:
    readme = (MVP_ROOT / "README.md").read_text(encoding="utf-8")
    front_matter = readme.split("---", 2)[1]
    assert "sdk: docker" in front_matter
    assert "app_port: 7860" in front_matter
    assert "license: apache-2.0" in front_matter
    assert "本頁僅使用固定合成資料作研究展示；不提供個案風險、診斷、治療或照護決策。" in readme
    assert "Synthetic research demonstration only" in readme
    assert "air-gapped" not in readme.casefold()
    assert "attestation" not in readme.casefold()

    notice = (MVP_ROOT / "NOTICE").read_text(encoding="utf-8")
    for boundary in (
        "no PhysioNet data",
        "no patient data",
        "no trained weights",
        "no model artifacts",
        "no formal evaluation evidence",
    ):
        assert boundary in notice
    assert (MVP_ROOT / "LICENSE").read_text(encoding="utf-8") == (
        REPOSITORY_ROOT / "LICENSE"
    ).read_text(encoding="utf-8")


def test_builder_copies_only_the_literal_allowlist(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "candidate"
    _write_valid_source(source)
    (source / "ignored.txt").write_text("must not be copied", encoding="utf-8")

    copied = build_candidate(source, destination)

    assert SPACE_PATHS == EXPECTED_SPACE_PATHS
    assert tuple(path.relative_to(destination).as_posix() for path in copied) == (
        EXPECTED_SPACE_PATHS
    )
    assert audit_candidate(destination) == copied


@pytest.mark.parametrize(
    ("relative", "payload"),
    (
        (".git/config", "safe"),
        ("weights.bin", "safe"),
        ("extra.txt", "hf_abcdefghijklmnopqrstuvwxyz1234567890"),
        ("space/receipt.json", json.dumps({"safe": True})),
    ),
)
def test_candidate_audit_rejects_every_extra_member(
    tmp_path: Path, relative: str, payload: str
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "candidate"
    _write_valid_source(source)
    build_candidate(source, destination)
    extra = destination / relative
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text(payload, encoding="utf-8")

    with pytest.raises(CandidateError, match="candidate_membership_invalid"):
        audit_candidate(destination)


def test_builder_refuses_missing_file_and_preexisting_destination(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    _write_valid_source(source)
    (source / "NOTICE").unlink()

    with pytest.raises(CandidateError, match="source_member_invalid"):
        build_candidate(source, tmp_path / "candidate")

    destination = tmp_path / "already-there"
    destination.mkdir()
    with pytest.raises(CandidateError, match="destination_exists"):
        build_candidate(source, destination)
