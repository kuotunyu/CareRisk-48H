"""Export the exact public Hugging Face Space tree from committed Git objects."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final

PUBLIC_PATHS: Final = (
    "README.md",
    "Dockerfile",
    "requirements.lock",
    "requirements-dev.lock",
    "app.py",
    "carerisk_space/__init__.py",
    "carerisk_space/contracts.py",
    "carerisk_space/evidence.py",
    "carerisk_space/scenarios.py",
    "carerisk_space/ui.py",
    "evidence/final-result-receipt.json",
    "evidence/release-v0.2.0.json",
    "deployment-manifest.json",
    "LICENSE",
    "NOTICE",
    "CITATION.cff",
    "SBOM.spdx.json",
    "THIRD_PARTY_LICENSES.json",
    "tests/test_claim_contract.py",
    "tests/test_evidence_contract.py",
    "tests/test_scenario_contract.py",
    "tests/test_gradio_contract.py",
    "tests/test_export_contract.py",
    "tests/test_container_contract.py",
)
APP_SOURCE_MAP: Final = {
    "README.md": "space/README.md",
    "Dockerfile": "space/Dockerfile",
    "requirements.lock": "space/requirements.lock",
    "requirements-dev.lock": "space/requirements-dev.lock",
    "app.py": "space/app.py",
    "carerisk_space/__init__.py": "space/carerisk_space/__init__.py",
    "carerisk_space/contracts.py": "space/carerisk_space/contracts.py",
    "carerisk_space/evidence.py": "space/carerisk_space/evidence.py",
    "carerisk_space/scenarios.py": "space/carerisk_space/scenarios.py",
    "carerisk_space/ui.py": "space/carerisk_space/ui.py",
    "SBOM.spdx.json": "space/SBOM.spdx.json",
    "THIRD_PARTY_LICENSES.json": "space/THIRD_PARTY_LICENSES.json",
    "tests/test_claim_contract.py": "space/tests/test_claim_contract.py",
    "tests/test_evidence_contract.py": "space/tests/test_evidence_contract.py",
    "tests/test_scenario_contract.py": "space/tests/test_scenario_contract.py",
    "tests/test_gradio_contract.py": "space/tests/test_gradio_contract.py",
    "tests/test_export_contract.py": "space/tests/test_export_contract.py",
    "tests/test_container_contract.py": "space/tests/test_container_contract.py",
}
TAG_SOURCE_MAP: Final = {
    "evidence/final-result-receipt.json": "docs/final-result-receipt.json",
    "evidence/release-v0.2.0.json": "docs/release-v0.2.0.json",
    "LICENSE": "LICENSE",
    "NOTICE": "NOTICE",
    "CITATION.cff": "CITATION.cff",
}
MANIFEST_SOURCE_MAP: Final = {"deployment-manifest.json": "space/deployment-manifest.json"}

MAX_PUBLIC_FILE_BYTES: Final = 1_048_576
TAG_OBJECT_SHA: Final = "2f1ddb0e2276fa894e124b856de488e31e21e88c"
TAG_COMMIT_SHA: Final = "f4c820cce953f401c1ec525bd8df3a3c1678bbf3"
RECEIPT_BLOB_SHA: Final = "b13ec7655bbdb8db1079c3b4793a0bf5590ef69c"
RECEIPT_SHA256: Final = "d32d833af25e4ebb2f5bd06b64343eb36d7cd180c8e9777f539f6401b78064b3"
RECEIPT_SIZE: Final = 3_363
SBOM_WEBKIT_RECORD_SHA256: Final = (
    "63f2a7be2b20d7adaae63361e12ea95e0f3894fc69c6202a227be6f797a707b8"
)
THIRD_PARTY_WEBKIT_RECORD_SHA256: Final = (
    "20831fd7b773fe13bf5a7508181b301b49bb9d0e0d89ccc4d1b25ac8baca7046"
)
_APPROVED_ORDINARY_BROWSER_RECORD_SHA256 = {
    "SBOM.spdx.json": {
        "chromium": "2b1061e9e52c75ce9b54a50f53053bb1eafde3b89e45f371a5e1d2dac0eae58b",
        "firefox": "16649a7fa3e21bfd9940ee290dbd2dfb87a9236e49a67e4b6814bcb9b3aa71ca",
        "ffmpeg": "325b0dde219da78a258c1e52aa1514fe50512bc40546db0aaa03652000448bbf",
    },
    "THIRD_PARTY_LICENSES.json": {
        "chromium": "116821ea11186ffc5eab80b7740f38dc162b0f61b1f1aac30eb6bde5bf8b7705",
        "firefox": "f438e37eee9b74996b1afdca3244ad4ce2aaf9f5bb3bf05995b03795e38431bf",
        "ffmpeg": "1c9e9d22be5dd9d05d8b76af7d5510517eb45c457c0d88ffafdd711a32a11264",
    },
}
_APPROVED_ORDINARY_BROWSER_COMPATIBILITY = {
    ("SBOM.spdx.json", "chromium"): ("NOASSERTION", "NOASSERTION", None),
    ("SBOM.spdx.json", "firefox"): ("NOASSERTION", "NOASSERTION", None),
    ("SBOM.spdx.json", "ffmpeg"): ("LGPL-2.1-only", "LGPL-2.1-only", None),
    ("THIRD_PARTY_LICENSES.json", "chromium"): (
        "NOASSERTION",
        "NOASSERTION",
        "reviewer_test_only_not_redistributed",
    ),
    ("THIRD_PARTY_LICENSES.json", "firefox"): (
        "NOASSERTION",
        "NOASSERTION",
        "reviewer_test_only_not_redistributed",
    ),
    ("THIRD_PARTY_LICENSES.json", "ffmpeg"): (
        "LGPL-2.1-only",
        "LGPL-2.1-only",
        "approved",
    ),
}
_WEBKIT_REVIEWER_EXCEPTION_RECORD_SHA256 = {
    "SBOM.spdx.json": SBOM_WEBKIT_RECORD_SHA256,
    "THIRD_PARTY_LICENSES.json": THIRD_PARTY_WEBKIT_RECORD_SHA256,
}

_SHA40 = re.compile(r"[0-9a-f]{40}")
_SHA64 = re.compile(r"[0-9a-f]{64}")
_IMAGE_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
_RUNTIME_TAG = re.compile(r"3\.11\.\d+-slim-bookworm")
_REVIEWER_TAG = re.compile(r"v\d+\.\d+\.\d+-(?:jammy|noble)")
_DENY_COMPONENTS = frozenset({".git", "data", "models", "artifacts", "worktrees"})
_DENY_SUFFIXES = frozenset(
    {
        ".arrow",
        ".ckpt",
        ".csv",
        ".feather",
        ".gz",
        ".joblib",
        ".npy",
        ".npz",
        ".onnx",
        ".parquet",
        ".pkl",
        ".pickle",
        ".pt",
        ".pth",
        ".tar",
        ".tsv",
        ".zip",
    }
)
_SECRET_SIGNATURES = (
    re.compile(rb"-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----"),
    re.compile(rb"\b(?:api[_-]?key|password|secret|token)\s*[:=]", re.IGNORECASE),
    re.compile(rb"\b(?:ghp|github_pat|hf)_[A-Za-z0-9_\-]{12,}"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
)
_BINARY_SIGNATURES = (
    b"\x7fELF",
    b"MZ",
    b"\xca\xfe\xba\xbe",
    b"\xfe\xed\xfa",
    b"PK\x03\x04",
    b"\x1f\x8b",
)
_REVIEWER_BROWSER_BYTE_SIGNATURES = (
    b"/ms-playwright/chromium-",
    b"/ms-playwright/chromium_headless_shell-",
    b"/ms-playwright/firefox-",
    b"/ms-playwright/webkit-",
    b"/ms-playwright/ffmpeg-",
    b"chrome-linux64/chrome",
    b"firefox/firefox",
    b"minibrowser-gtk/bin/MiniBrowser",
    b"minibrowser-wpe/bin/MiniBrowser",
)
_WEBKIT_EXCEPTION_MARKER = b"reviewer_test_only_not_redistributed"
_WEBKIT_METADATA_PATHS = frozenset({"SBOM.spdx.json", "THIRD_PARTY_LICENSES.json"})

_CAPABILITIES = {
    "README.md": "metadata",
    "Dockerfile": "runtime_code",
    "requirements.lock": "supply_chain",
    "requirements-dev.lock": "supply_chain",
    "app.py": "runtime_code",
    "carerisk_space/__init__.py": "runtime_code",
    "carerisk_space/contracts.py": "runtime_code",
    "carerisk_space/evidence.py": "runtime_code",
    "carerisk_space/scenarios.py": "runtime_code",
    "carerisk_space/ui.py": "runtime_code",
    "evidence/final-result-receipt.json": "evidence",
    "evidence/release-v0.2.0.json": "evidence",
    "deployment-manifest.json": "metadata",
    "LICENSE": "legal",
    "NOTICE": "legal",
    "CITATION.cff": "legal",
    "SBOM.spdx.json": "supply_chain",
    "THIRD_PARTY_LICENSES.json": "supply_chain",
    "tests/test_claim_contract.py": "test",
    "tests/test_evidence_contract.py": "test",
    "tests/test_scenario_contract.py": "test",
    "tests/test_gradio_contract.py": "test",
    "tests/test_export_contract.py": "test",
    "tests/test_container_contract.py": "test",
}
_MANIFEST_KEYS = {
    "schema_version",
    "space_app_source_git_sha",
    "evidence_tag",
    "evidence_tag_object",
    "evidence_tag_commit",
    "destination_repository",
    "base_images",
    "supply_chain",
    "files",
}
_MANIFEST_FILE_KEYS = {
    "source_ref",
    "source_path",
    "destination_path",
    "sha256",
    "byte_size",
    "media_type",
    "capability",
}


class ExportError(RuntimeError):
    """Raised when a public export boundary fails closed."""


@dataclass(frozen=True, slots=True)
class ExportFile:
    path: str
    sha256: str
    byte_size: int


@dataclass(frozen=True, slots=True)
class ExportReceipt:
    destination: Path
    app_source_sha: str
    manifest_source_sha: str
    files: tuple[ExportFile, ...]
    tree_sha256: str


@dataclass(frozen=True, slots=True)
class _Blob:
    raw: bytes
    object_sha: str


def _git(repo_root: Path, *args: str, allowed_codes: tuple[int, ...] = (0,)) -> bytes:
    process = subprocess.run(
        ["git", "-C", os.fspath(repo_root), "--literal-pathspecs", *args],
        capture_output=True,
        check=False,
    )
    if process.returncode not in allowed_codes:
        raise ExportError("git_object_read_failed")
    return process.stdout


def _canonical_path(path: object) -> str | None:
    if not isinstance(path, str) or not path or "\\" in path:
        return None
    value = PurePosixPath(path)
    if value.is_absolute() or any(part in {"", ".", ".."} for part in value.parts):
        return None
    return value.as_posix()


def _validate_source_maps() -> dict[str, str]:
    maps = (APP_SOURCE_MAP, TAG_SOURCE_MAP, MANIFEST_SOURCE_MAP)
    destination_sets = tuple(set(mapping) for mapping in maps)
    if tuple(map(len, destination_sets)) != (18, 5, 1):
        raise ExportError("source_map_collision")
    if any(
        destination_sets[left] & destination_sets[right]
        for left, right in ((0, 1), (0, 2), (1, 2))
    ):
        raise ExportError("source_map_collision")
    if set().union(*destination_sets) != set(PUBLIC_PATHS) or len(set(PUBLIC_PATHS)) != 24:
        raise ExportError("source_map_collision")
    merged: dict[str, str] = {}
    for mapping in maps:
        for destination, source in mapping.items():
            if _canonical_path(destination) != destination or _canonical_path(source) != source:
                raise ExportError("path_traversal")
            if any(part.casefold() in _DENY_COMPONENTS for part in destination.split("/")):
                raise ExportError("extra_path")
            if any(destination.casefold().endswith(suffix) for suffix in _DENY_SUFFIXES):
                raise ExportError("extra_path")
            merged[destination] = source
    return merged


def _repository_root(repo_root: Path) -> Path:
    try:
        root = Path(repo_root).resolve(strict=True)
        mode = root.lstat().st_mode
    except OSError as exc:
        raise ExportError("repository_invalid") from exc
    if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
        raise ExportError("repository_invalid")
    top = _git(root, "rev-parse", "--show-toplevel").decode().strip()
    try:
        if Path(top).resolve(strict=True) != root:
            raise ExportError("repository_invalid")
    except OSError as exc:
        raise ExportError("repository_invalid") from exc
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ExportError("dirty_source")
    return root


def _commit_sha(repo_root: Path, supplied: str, role: str) -> str:
    if _SHA40.fullmatch(supplied) is None:
        raise ExportError(f"missing_{role}")
    try:
        object_type = _git(repo_root, "cat-file", "-t", supplied).decode().strip()
    except ExportError as exc:
        raise ExportError(f"missing_{role}") from exc
    if object_type != "commit":
        if role == "manifest":
            raise ExportError("tree_manifest")
        raise ExportError(f"noncommit_{role}")
    resolved = _git(repo_root, "rev-parse", supplied).decode().strip()
    if resolved != supplied:
        raise ExportError(f"missing_{role}")
    return resolved


def _validate_topology(repo_root: Path, app_sha: str, manifest_sha: str) -> None:
    if app_sha == manifest_sha:
        raise ExportError("manifest_self_reference")
    result = subprocess.run(
        [
            "git",
            "-C",
            os.fspath(repo_root),
            "merge-base",
            "--is-ancestor",
            app_sha,
            manifest_sha,
        ],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ExportError("non_ancestor")


def _validate_tag(repo_root: Path) -> None:
    try:
        tag_object = _git(repo_root, "rev-parse", "refs/tags/v0.2.0").decode().strip()
        tag_type = _git(repo_root, "cat-file", "-t", tag_object).decode().strip()
        tag_commit = _git(repo_root, "rev-parse", "v0.2.0^{commit}").decode().strip()
    except ExportError as exc:
        raise ExportError("wrong_tag_commit") from exc
    if tag_object != TAG_OBJECT_SHA or tag_type != "tag" or tag_commit != TAG_COMMIT_SHA:
        raise ExportError("wrong_tag_commit")


def _prepare_destination(destination: Path) -> tuple[Path, Path]:
    supplied = Path(destination)
    if supplied.name in {"", ".", ".."} or os.path.lexists(supplied):
        raise ExportError("nonempty_destination")
    try:
        parent = supplied.parent.resolve(strict=True)
        parent_mode = parent.lstat().st_mode
    except OSError as exc:
        raise ExportError("destination_parent_invalid") from exc
    if stat.S_ISLNK(parent_mode) or not stat.S_ISDIR(parent_mode):
        raise ExportError("destination_parent_invalid")
    target = parent / supplied.name
    if target.parent != parent or os.path.lexists(target):
        raise ExportError("nonempty_destination")
    try:
        target.mkdir()
    except OSError as exc:
        raise ExportError("destination_create_failed") from exc
    return target, parent


def _cleanup_owned_destination(target: Path, verified_parent: Path) -> None:
    try:
        mode = target.lstat().st_mode
        parent = target.parent.resolve(strict=True)
    except OSError:
        return
    if parent == verified_parent and stat.S_ISDIR(mode) and not stat.S_ISLNK(mode):
        shutil.rmtree(target)


def _read_blob(repo_root: Path, commit_sha: str, source_path: str) -> _Blob:
    listing = _git(repo_root, "ls-tree", "-z", "--full-tree", commit_sha, "--", source_path)
    records = [record for record in listing.split(b"\0") if record]
    if len(records) != 1:
        raise ExportError("missing_source_path")
    try:
        metadata, listed_path = records[0].split(b"\t", 1)
        mode, object_type, object_sha = metadata.decode("ascii").split(" ")
        path = listed_path.decode("utf-8")
    except (UnicodeDecodeError, ValueError) as exc:
        raise ExportError("git_object_read_failed") from exc
    if path != source_path:
        raise ExportError("path_traversal")
    if mode == "120000":
        raise ExportError("symlink")
    if mode != "100644" or object_type != "blob" or _SHA40.fullmatch(object_sha) is None:
        raise ExportError("special_file")
    raw = _git(repo_root, "cat-file", "blob", object_sha)
    return _Blob(raw=raw, object_sha=object_sha)


def _validate_public_bytes(destination_path: str, raw: bytes) -> None:
    if len(raw) > MAX_PUBLIC_FILE_BYTES:
        raise ExportError("large_file")
    if any(raw.startswith(signature) for signature in _BINARY_SIGNATURES):
        raise ExportError("binary_signature")
    if any(pattern.search(raw) for pattern in _SECRET_SIGNATURES):
        raise ExportError("secret_signature")
    is_browser_metadata = destination_path in _WEBKIT_METADATA_PATHS
    if not is_browser_metadata and any(
        signature in raw for signature in _REVIEWER_BROWSER_BYTE_SIGNATURES
    ):
        raise ExportError("reviewer bytes reached public export")
    if not is_browser_metadata and _WEBKIT_EXCEPTION_MARKER in raw:
        raise ExportError("reviewer bytes reached public export")


def _strict_json(raw: bytes, error: str) -> dict[str, object]:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ExportError(error)
            result[key] = value
        return result

    try:
        value = json.loads(raw, object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExportError(error) from exc
    if not isinstance(value, dict):
        raise ExportError(error)
    return value


def _canonical_json_bytes(value: object) -> bytes:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (text + "\n").encode()


def _record_sha256(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _subtract_exact_metadata_record(
    residual: bytes,
    records: list[dict[str, object]],
    *,
    identity_key: str,
    identity: str,
    expected_sha256: str,
    error: str,
) -> tuple[dict[str, object], bytes]:
    matches = [record for record in records if record.get(identity_key) == identity]
    if len(matches) != 1 or _record_sha256(matches[0]) != expected_sha256:
        raise ExportError(error)
    record = matches[0]
    encoded = json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    if residual.count(encoded) != 1:
        raise ExportError(error)
    return record, residual.replace(encoded, b"", 1)


def _reject_cross_schema_or_unrecognized_browser_records(
    records: list[dict[str, object]], *, identity_key: str
) -> None:
    recognized = frozenset({"chromium", "firefox", "ffmpeg", "webkit"})
    for record in records:
        for candidate_key in ("name", "package"):
            identity = record.get(candidate_key)
            if not isinstance(identity, str):
                continue
            normalized = identity.casefold()
            if not any(name in normalized for name in recognized):
                continue
            if candidate_key != identity_key or normalized not in recognized:
                raise ExportError("browser_metadata_invalid")


def _validate_approved_ordinary_browser_metadata(
    destination: str,
    records: list[dict[str, object]],
    *,
    identity_key: str,
    residual: bytes,
) -> bytes:
    expected_records = _APPROVED_ORDINARY_BROWSER_RECORD_SHA256[destination]
    for identity, expected_sha256 in expected_records.items():
        record, residual = _subtract_exact_metadata_record(
            residual,
            records,
            identity_key=identity_key,
            identity=identity,
            expected_sha256=expected_sha256,
            error="approved_browser_metadata_invalid",
        )
        compatibility = (
            record.get("licenseDeclared"),
            record.get("licenseConcluded"),
            record.get("review_disposition"),
        )
        if compatibility != _APPROVED_ORDINARY_BROWSER_COMPATIBILITY[
            (destination, identity)
        ]:
            raise ExportError("approved_browser_metadata_invalid")
    return residual


def _validate_exact_webkit_reviewer_exception(
    destination: str,
    records: list[dict[str, object]],
    *,
    identity_key: str,
    residual: bytes,
) -> bytes:
    record, residual = _subtract_exact_metadata_record(
        residual,
        records,
        identity_key=identity_key,
        identity="webkit",
        expected_sha256=_WEBKIT_REVIEWER_EXCEPTION_RECORD_SHA256[destination],
        error="webkit_metadata_invalid",
    )
    expected_disposition = (
        None
        if destination == "SBOM.spdx.json"
        else "reviewer_test_only_not_redistributed"
    )
    if (
        record.get("licenseDeclared") != "NOASSERTION"
        or record.get("licenseConcluded") != "NOASSERTION"
        or record.get("review_disposition") != expected_disposition
    ):
        raise ExportError("webkit_metadata_invalid")
    return residual


def _validate_browser_metadata_policy(blobs: dict[str, _Blob]) -> None:
    sbom = _strict_json(blobs["SBOM.spdx.json"].raw, "webkit_metadata_invalid")
    third_party = _strict_json(
        blobs["THIRD_PARTY_LICENSES.json"].raw, "webkit_metadata_invalid"
    )
    packages = sbom.get("packages")
    components = third_party.get("components")
    if not isinstance(packages, list) or not isinstance(components, list):
        raise ExportError("webkit_metadata_invalid")
    if any(not isinstance(item, dict) for item in packages) or any(
        not isinstance(item, dict) for item in components
    ):
        raise ExportError("webkit_metadata_invalid")
    sbom_records = [item for item in packages if isinstance(item, dict)]
    third_party_records = [item for item in components if isinstance(item, dict)]
    for destination, records, identity_key in (
        ("SBOM.spdx.json", sbom_records, "name"),
        (
            "THIRD_PARTY_LICENSES.json",
            third_party_records,
            "package",
        ),
    ):
        residual = blobs[destination].raw
        _reject_cross_schema_or_unrecognized_browser_records(
            records, identity_key=identity_key
        )
        residual = _validate_approved_ordinary_browser_metadata(
            destination,
            records,
            identity_key=identity_key,
            residual=residual,
        )
        residual = _validate_exact_webkit_reviewer_exception(
            destination,
            records,
            identity_key=identity_key,
            residual=residual,
        )
        if any(token in residual for token in _REVIEWER_BROWSER_BYTE_SIGNATURES):
            raise ExportError("reviewer bytes reached public export")


def _media_type(path: str) -> str:
    if path.endswith(".json"):
        return "application/json"
    if path.endswith(".py"):
        return "text/x-python"
    if path.endswith(".md"):
        return "text/markdown"
    if path.endswith(".cff"):
        return "application/yaml"
    return "text/plain"


def _object_with_keys(value: object, keys: set[str], error: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ExportError(error)
    return value


def _text(value: object, error: str) -> str:
    if not isinstance(value, str) or not value:
        raise ExportError(error)
    return value


def _validate_base_images(value: object) -> None:
    images = _object_with_keys(value, {"runtime", "reviewer"}, "manifest_invalid")
    keys = {"repository", "tag", "index_digest", "linux_amd64_digest"}
    for role in ("runtime", "reviewer"):
        image = _object_with_keys(images[role], keys, "manifest_invalid")
        repository = _text(image["repository"], "manifest_invalid")
        tag = _text(image["tag"], "manifest_invalid")
        if role == "runtime":
            identity_ok = repository == "docker.io/library/python" and _RUNTIME_TAG.fullmatch(tag)
        else:
            identity_ok = (
                repository == "mcr.microsoft.com/playwright/python"
                and _REVIEWER_TAG.fullmatch(tag)
            )
        digests_ok = all(
            _IMAGE_DIGEST.fullmatch(_text(image[field], "manifest_invalid"))
            for field in ("index_digest", "linux_amd64_digest")
        )
        if not identity_ok or not digests_ok:
            raise ExportError("manifest_invalid")


def _validate_manifest(
    raw: bytes,
    *,
    app_sha: str,
    merged_sources: dict[str, str],
    blobs: dict[str, _Blob],
) -> None:
    manifest = _strict_json(raw, "manifest_invalid")
    if "destination_commit" in manifest:
        raise ExportError("manifest_self_reference")
    if set(manifest) != _MANIFEST_KEYS:
        raise ExportError("manifest_invalid")
    if _canonical_json_bytes(manifest) != raw:
        raise ExportError("noncanonical_manifest")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise ExportError("manifest_invalid")
    if (
        manifest["space_app_source_git_sha"] != app_sha
        or manifest["evidence_tag"] != "v0.2.0"
        or manifest["evidence_tag_object"] != TAG_OBJECT_SHA
        or manifest["evidence_tag_commit"] != TAG_COMMIT_SHA
        or manifest["destination_repository"] != "steven0226/carerisk-48h"
    ):
        raise ExportError("manifest_invalid")
    _validate_base_images(manifest["base_images"])
    raw_files = manifest["files"]
    if not isinstance(raw_files, list):
        raise ExportError("manifest_invalid")
    destinations = [
        item.get("destination_path") if isinstance(item, dict) else None for item in raw_files
    ]
    if len(destinations) != len(set(destinations)):
        raise ExportError("duplicate_paths")
    if set(destinations) != set(PUBLIC_PATHS):
        raise ExportError("extra_path")
    if destinations != sorted(PUBLIC_PATHS):
        raise ExportError("unsorted_paths")
    by_path: dict[str, dict[str, object]] = {}
    for value in raw_files:
        item = _object_with_keys(value, _MANIFEST_FILE_KEYS, "manifest_invalid")
        destination = _text(item["destination_path"], "manifest_invalid")
        source_path = _text(item["source_path"], "manifest_invalid")
        if (
            _canonical_path(destination) != destination
            or _canonical_path(source_path) != source_path
        ):
            raise ExportError("path_traversal")
        if source_path != merged_sources[destination]:
            raise ExportError("manifest_invalid")
        if item["media_type"] != _media_type(destination):
            raise ExportError("manifest_invalid")
        if item["capability"] != _CAPABILITIES[destination]:
            raise ExportError("manifest_invalid")
        if destination == "deployment-manifest.json":
            if (
                item["source_ref"] != "export-manifest-commit"
                or item["sha256"] is not None
                or item["byte_size"] is not None
            ):
                raise ExportError("manifest_self_reference")
        else:
            expected_ref = TAG_COMMIT_SHA if destination in TAG_SOURCE_MAP else app_sha
            if item["source_ref"] != expected_ref:
                raise ExportError("manifest_invalid")
            expected_sha = hashlib.sha256(blobs[destination].raw).hexdigest()
            if item["sha256"] != expected_sha:
                raise ExportError("hash_mismatch")
            byte_size = item["byte_size"]
            if type(byte_size) is not int or byte_size != len(blobs[destination].raw):
                raise ExportError("size_mismatch")
        by_path[destination] = item
    supply_chain = _object_with_keys(
        manifest["supply_chain"],
        {
            "runtime_lock_sha256",
            "development_lock_sha256",
            "sbom_sha256",
            "third_party_licenses_sha256",
        },
        "manifest_invalid",
    )
    relationships = {
        "runtime_lock_sha256": "requirements.lock",
        "development_lock_sha256": "requirements-dev.lock",
        "sbom_sha256": "SBOM.spdx.json",
        "third_party_licenses_sha256": "THIRD_PARTY_LICENSES.json",
    }
    for field, destination in relationships.items():
        expected = by_path[destination]["sha256"]
        if supply_chain[field] != expected or not isinstance(expected, str):
            raise ExportError("hash_mismatch")


def _collect_blobs(
    repo_root: Path,
    app_sha: str,
    manifest_sha: str,
    merged_sources: dict[str, str],
) -> dict[str, _Blob]:
    blobs: dict[str, _Blob] = {}
    for destination in PUBLIC_PATHS:
        if destination in APP_SOURCE_MAP:
            source_ref = app_sha
        elif destination in TAG_SOURCE_MAP:
            source_ref = TAG_COMMIT_SHA
        else:
            source_ref = manifest_sha
        blob = _read_blob(repo_root, source_ref, merged_sources[destination])
        _validate_public_bytes(destination, blob.raw)
        blobs[destination] = blob
    receipt = blobs["evidence/final-result-receipt.json"]
    if (
        receipt.object_sha != RECEIPT_BLOB_SHA
        or len(receipt.raw) != RECEIPT_SIZE
        or hashlib.sha256(receipt.raw).hexdigest() != RECEIPT_SHA256
    ):
        raise ExportError("wrong_tag_commit")
    _validate_browser_metadata_policy(blobs)
    _validate_manifest(
        blobs["deployment-manifest.json"].raw,
        app_sha=app_sha,
        merged_sources=merged_sources,
        blobs=blobs,
    )
    return blobs


def _write_export(target: Path, blobs: dict[str, _Blob]) -> tuple[ExportFile, ...]:
    files: list[ExportFile] = []
    for destination in PUBLIC_PATHS:
        output = target.joinpath(*destination.split("/"))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(blobs[destination].raw)
        files.append(
            ExportFile(
                path=destination,
                sha256=hashlib.sha256(blobs[destination].raw).hexdigest(),
                byte_size=len(blobs[destination].raw),
            )
        )
    actual_paths: list[str] = []
    for root, directories, names in os.walk(target, followlinks=False):
        directories.sort()
        names.sort()
        root_path = Path(root)
        for name in names:
            path = root_path / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
                raise ExportError("special_file")
            actual_paths.append(path.relative_to(target).as_posix())
    if set(actual_paths) != set(PUBLIC_PATHS) or len(actual_paths) != len(PUBLIC_PATHS):
        raise ExportError("extra_path")
    return tuple(files)


def _tree_sha256(files: tuple[ExportFile, ...]) -> str:
    digest = hashlib.sha256()
    for item in sorted(files, key=lambda value: value.path):
        digest.update(item.path.encode())
        digest.update(b"\0")
        digest.update(item.sha256.encode())
        digest.update(b"\0")
        digest.update(str(item.byte_size).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def export_space(
    *,
    repo_root: Path,
    app_source_sha: str,
    manifest_source_sha: str,
    destination: Path,
) -> ExportReceipt:
    """Export an exact, safe public tree from immutable committed objects."""

    merged_sources = _validate_source_maps()
    root = _repository_root(repo_root)
    app_sha = _commit_sha(root, app_source_sha, "app")
    manifest_sha = _commit_sha(root, manifest_source_sha, "manifest")
    _validate_topology(root, app_sha, manifest_sha)
    _validate_tag(root)
    target, verified_parent = _prepare_destination(destination)
    try:
        blobs = _collect_blobs(root, app_sha, manifest_sha, merged_sources)
        files = _write_export(target, blobs)
        return ExportReceipt(
            destination=target,
            app_source_sha=app_sha,
            manifest_source_sha=manifest_sha,
            files=files,
            tree_sha256=_tree_sha256(files),
        )
    except ExportError:
        _cleanup_owned_destination(target, verified_parent)
        raise
    except Exception as exc:
        _cleanup_owned_destination(target, verified_parent)
        raise ExportError("export_failed") from exc
