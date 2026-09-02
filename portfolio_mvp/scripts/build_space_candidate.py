"""Build the exact public Hugging Face Space candidate."""

from __future__ import annotations

import argparse
import re
import shutil
import uuid
from collections.abc import Sequence
from pathlib import Path

SPACE_PATHS: tuple[str, ...] = (
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

_FORBIDDEN_SUFFIXES = {
    ".7z",
    ".bin",
    ".ckpt",
    ".joblib",
    ".npy",
    ".npz",
    ".onnx",
    ".pkl",
    ".pt",
    ".pth",
    ".tar",
    ".zip",
}
_FORBIDDEN_PATH = re.compile(
    r"(^|/)(?:\.git|\.env|id_rsa|data|models?|artifacts?|reports?|__pycache__)"
    r"(?:/|$)|\.(?:pem|key|p12)$",
    re.IGNORECASE,
)
_SECRET_CONTENT = re.compile(
    r"(?:hf_[A-Za-z0-9]{24,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)
_LEGACY_CONTENT = (
    "scripts/export_hf_space.py",
    "tools/space/",
    "final-result-receipt",
    "sbom.spdx",
    "third_party_licenses",
    "reviewer_image",
)


class CandidateError(RuntimeError):
    """Raised when the candidate cannot satisfy its narrow public boundary."""


def _read_public_text(path: Path, relative: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise CandidateError(f"source_member_invalid:{relative}")
    if path.suffix.casefold() in _FORBIDDEN_SUFFIXES:
        raise CandidateError(f"source_member_forbidden:{relative}")
    raw = path.read_bytes()
    if b"\x00" in raw:
        raise CandidateError(f"binary_content_forbidden:{relative}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CandidateError(f"non_utf8_content_forbidden:{relative}") from exc
    if _SECRET_CONTENT.search(text):
        raise CandidateError(f"secret_content_forbidden:{relative}")
    lowered = text.casefold()
    if any(token in lowered for token in _LEGACY_CONTENT):
        raise CandidateError(f"legacy_content_forbidden:{relative}")
    return raw


def audit_candidate(destination: Path) -> tuple[Path, ...]:
    """Validate exact membership and public-safe text for a built candidate."""

    root = destination.resolve(strict=True)
    if not root.is_dir() or root.is_symlink():
        raise CandidateError("candidate_root_invalid")

    members = tuple(
        sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() or path.is_symlink()
        )
    )
    if members != tuple(sorted(SPACE_PATHS)):
        raise CandidateError("candidate_membership_invalid")

    audited: list[Path] = []
    for relative in SPACE_PATHS:
        if _FORBIDDEN_PATH.search(relative):
            raise CandidateError(f"candidate_path_forbidden:{relative}")
        path = root / relative
        _read_public_text(path, relative)
        audited.append(path)
    return tuple(audited)


def build_candidate(source_root: Path, destination: Path) -> tuple[Path, ...]:
    """Copy only literal allowlisted files into a new destination."""

    source = source_root.resolve(strict=True)
    target = destination.resolve(strict=False)
    if not source.is_dir() or source.is_symlink():
        raise CandidateError("source_root_invalid")
    if destination.exists() or destination.is_symlink():
        raise CandidateError("destination_exists")
    if target == source or target == source.parent:
        raise CandidateError("destination_scope_invalid")

    run_id = uuid.uuid4().hex
    marker = target / ".carerisk-mvp-build"
    target.mkdir(parents=False)
    marker.write_text(run_id, encoding="ascii")
    try:
        for relative in SPACE_PATHS:
            source_path = source / relative
            raw = _read_public_text(source_path, relative)
            destination_path = target / relative
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            destination_path.write_bytes(raw)
        marker.unlink()
        return audit_candidate(target)
    except Exception:
        if marker.is_file() and marker.read_text(encoding="ascii") == run_id:
            shutil.rmtree(target)
        raise


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args(argv)
    for path in build_candidate(args.source_root, args.destination):
        print(path.relative_to(args.destination.resolve()).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
