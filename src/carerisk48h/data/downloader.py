"""Resumable, checksummed downloader for PhysioNet Challenge 2012."""

from __future__ import annotations

import hashlib
import json
import os
import tarfile
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, BinaryIO

from carerisk48h.constants import (
    DATA_LICENSE,
    DATA_LICENSE_URL,
    PHYSIONET_BASE_URL,
    PHYSIONET_VERSION,
)


@dataclass(frozen=True)
class DownloadRecord:
    filename: str
    url: str
    bytes: int
    sha256: str


def sha256_file(path: str | Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_response(response: BinaryIO, output: IO[bytes], *, chunk_size: int = 1024 * 1024) -> None:
    while chunk := response.read(chunk_size):
        output.write(chunk)


def download_file(
    url: str,
    target: str | Path,
    *,
    timeout: int = 60,
    user_agent: str = "CareRisk48H/0.1 (+research; PhysioNet ODC-By attribution)",
) -> DownloadRecord:
    """Download to a partial file, resume when supported, and atomically rename."""
    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    partial = target_path.with_name(target_path.name + ".partial")
    if target_path.exists():
        return DownloadRecord(
            target_path.name,
            url,
            target_path.stat().st_size,
            sha256_file(target_path),
        )

    resume_at = partial.stat().st_size if partial.exists() else 0
    headers = {"User-Agent": user_agent}
    if resume_at:
        headers["Range"] = f"bytes={resume_at}-"
    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            status = getattr(response, "status", response.getcode())
            append = resume_at > 0 and status == 206
            mode = "ab" if append else "wb"
            with partial.open(mode) as output:
                _copy_response(response, output)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"download failed for {url}: {exc}") from exc

    if not partial.exists() or partial.stat().st_size == 0:
        raise RuntimeError(f"download produced an empty file: {url}")
    os.replace(partial, target_path)
    return DownloadRecord(
        target_path.name,
        url,
        target_path.stat().st_size,
        sha256_file(target_path),
    )


def safe_extract_tar(archive: str | Path, destination: str | Path) -> list[Path]:
    """Extract a tar archive after rejecting traversal and link entries."""
    archive_path = Path(archive)
    destination_path = Path(destination).resolve()
    destination_path.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    with tarfile.open(archive_path, mode="r:*") as bundle:
        for member in bundle.getmembers():
            if member.issym() or member.islnk():
                raise ValueError(f"archive links are not allowed: {member.name}")
            candidate = (destination_path / member.name).resolve()
            if destination_path != candidate and destination_path not in candidate.parents:
                raise ValueError(f"unsafe archive member: {member.name}")
            extracted.append(candidate)
        bundle.extractall(destination_path)  # noqa: S202 - validated above
    return extracted


def _manifest_payload(records: list[DownloadRecord], *, dataset_set: str) -> dict[str, object]:
    return {
        "dataset": "PhysioNet/Computing in Cardiology Challenge 2012",
        "version": PHYSIONET_VERSION,
        "set": dataset_set,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "license": DATA_LICENSE,
        "license_url": DATA_LICENSE_URL,
        "files": [asdict(record) for record in records],
    }


def write_manifest(path: str | Path, payload: dict[str, object]) -> None:
    """Atomically write a UTF-8 JSON manifest."""
    manifest = Path(path)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    partial = manifest.with_name(manifest.name + ".partial")
    partial.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, manifest)


def verify_manifest(raw_dir: str | Path, manifest_path: str | Path | None = None) -> None:
    """Verify every file recorded in a local manifest."""
    root = Path(raw_dir)
    path = Path(manifest_path) if manifest_path is not None else root / "manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    for item in payload.get("files", []):
        file_path = root / str(item["filename"])
        if not file_path.exists():
            raise FileNotFoundError(file_path)
        actual_size = file_path.stat().st_size
        actual_sha = sha256_file(file_path)
        if actual_size != int(item["bytes"]) or actual_sha != str(item["sha256"]):
            raise ValueError(f"checksum mismatch for {file_path.name}")


def download_physionet(
    raw_dir: str | Path,
    *,
    dataset_set: str = "a",
    include_outcomes: bool = True,
    confirm_final: bool = False,
) -> Path:
    """Download one challenge set and create a checksum manifest.

    Set A is the development default. Accessing Outcomes-b requires an explicit
    final-evaluation confirmation and is intentionally unavailable through normal calls.
    """
    normalized = dataset_set.lower()
    if normalized not in {"a", "b"}:
        raise ValueError("dataset_set must be 'a' or 'b'; Set C is excluded by protocol")
    if normalized == "b" and include_outcomes and not confirm_final:
        raise PermissionError(
            "Outcomes-b is gated until model freeze; pass confirm_final only via final evaluation"
        )

    root = Path(raw_dir)
    root.mkdir(parents=True, exist_ok=True)
    archive_name = f"set-{normalized}.tar.gz"
    filenames = [archive_name]
    if include_outcomes:
        filenames.append(f"Outcomes-{normalized}.txt")

    records = [
        download_file(f"{PHYSIONET_BASE_URL}/{filename}", root / filename) for filename in filenames
    ]
    safe_extract_tar(root / archive_name, root)
    manifest_path = root / f"manifest-set-{normalized}.json"
    write_manifest(manifest_path, _manifest_payload(records, dataset_set=normalized))
    verify_manifest(root, manifest_path)
    return manifest_path
