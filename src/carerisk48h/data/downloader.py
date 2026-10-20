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


def _copy_response(response: BinaryIO, output: IO[bytes], *, chunk_size: int = 1024 * 1024) -> int:
    written = 0
    while chunk := response.read(chunk_size):
        output.write(chunk)
        written += len(chunk)
    return written


@dataclass(frozen=True)
class _ContentRange:
    start: int
    end: int
    total: int | None


def _header(response: object, name: str) -> str | None:
    getter = getattr(response, "getheader", None)
    if getter is not None:
        return getter(name)
    headers = getattr(response, "headers", None)
    return headers.get(name) if headers is not None else None


def _int_header(response: object, name: str) -> int | None:
    raw = _header(response, name)
    if raw is None:
        return None
    try:
        return int(raw.strip())
    except ValueError:
        return None


def _parse_content_range(value: str | None) -> _ContentRange | None:
    """Parse ``bytes start-end/total``; return None when absent or unusable."""
    if not value:
        return None
    units, _, spec = value.strip().partition(" ")
    if units.lower() != "bytes":
        return None
    span, _, total_text = spec.strip().partition("/")
    start_text, separator, end_text = span.partition("-")
    if not separator:
        return None
    try:
        start = int(start_text)
        end = int(end_text)
        total = None if total_text.strip() == "*" else int(total_text)
    except ValueError:
        return None
    if start < 0 or end < start or (total is not None and end >= total):
        return None
    return _ContentRange(start, end, total)


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
            advertised = _int_header(response, "Content-Length")
            expected_body: int | None
            expected_size: int | None
            if status == 206:
                # Validate the served range before any byte touches the partial file,
                # so a wrong range can never poison a resumable prefix.
                served = _parse_content_range(_header(response, "Content-Range"))
                if served is None:
                    raise RuntimeError(f"resumed response has an unusable Content-Range: {url}")
                if served.total is None:
                    raise RuntimeError(
                        f"resumed response has an unknown Content-Range total, so completion "
                        f"cannot be established: {url}"
                    )
                if served.start != resume_at:
                    raise RuntimeError(
                        f"resumed response Content-Range starts at {served.start}, "
                        f"expected {resume_at}: {url}"
                    )
                expected_body = served.end - served.start + 1
                if advertised is not None and advertised != expected_body:
                    raise RuntimeError(
                        f"resumed response Content-Length disagrees with Content-Range: {url}"
                    )
                append = resume_at > 0
                expected_size = served.total
            else:
                append = False
                expected_body = advertised
                expected_size = advertised
            mode = "ab" if append else "wb"
            with partial.open(mode) as output:
                written = _copy_response(response, output)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"download failed for {url}: {exc}") from exc

    if not partial.exists() or partial.stat().st_size == 0:
        raise RuntimeError(f"download produced an empty file: {url}")
    if expected_body is not None and written != expected_body:
        raise RuntimeError(
            f"download delivered {written} of {expected_body} advertised bytes: {url}"
        )
    size = partial.stat().st_size
    if expected_size is not None and size != expected_size:
        raise RuntimeError(f"download is incomplete: {size} of {expected_size} bytes: {url}")
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

    Set A is the development default. ``confirm_final`` is retained for API
    compatibility but never authorizes Outcomes-b here; only the audited final
    evaluation gate may download or read that file.
    """
    normalized = dataset_set.lower()
    if normalized not in {"a", "b"}:
        raise ValueError("dataset_set must be 'a' or 'b'; Set C is excluded by protocol")
    if normalized == "b" and include_outcomes:
        raise PermissionError(
            "Outcomes-b is gated behind the audited final evaluation and cannot be "
            "downloaded through the general downloader"
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
