from __future__ import annotations

import io
import tarfile
from pathlib import Path

import pytest

from carerisk48h.data.downloader import download_physionet, safe_extract_tar


def _tar_with_member(path: Path, member_name: str) -> None:
    payload = b"example"
    with tarfile.open(path, "w:gz") as bundle:
        info = tarfile.TarInfo(member_name)
        info.size = len(payload)
        bundle.addfile(info, io.BytesIO(payload))


def test_safe_extract_accepts_normal_member(tmp_path: Path) -> None:
    archive = tmp_path / "safe.tar.gz"
    _tar_with_member(archive, "set-a/123.txt")
    safe_extract_tar(archive, tmp_path / "raw")
    assert (tmp_path / "raw" / "set-a" / "123.txt").read_bytes() == b"example"


def test_safe_extract_rejects_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.tar.gz"
    _tar_with_member(archive, "../escape.txt")
    with pytest.raises(ValueError, match="unsafe"):
        safe_extract_tar(archive, tmp_path / "raw")


def test_outcomes_b_requires_final_confirmation(tmp_path: Path) -> None:
    with pytest.raises(PermissionError, match="gated"):
        download_physionet(tmp_path, dataset_set="b", include_outcomes=True)
