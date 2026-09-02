from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from scripts.export_hf_space import (
    APP_SOURCE_MAP,
    MANIFEST_SOURCE_MAP,
    PUBLIC_PATHS,
    TAG_SOURCE_MAP,
    ExportError,
    export_space,
)
from space.tests.test_export_contract import (
    REVIEWER_BROWSER_BYTE_SIGNATURES,
    assert_exact_webkit_metadata_only,
    assert_no_reviewer_or_browser_bytes,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TASK7_SOURCE_SHA = "78faab4d274ea14a6cfc945428600a6fafc24eed"
TAG_OBJECT_SHA = "2f1ddb0e2276fa894e124b856de488e31e21e88c"
TAG_COMMIT_SHA = "f4c820cce953f401c1ec525bd8df3a3c1678bbf3"
RECEIPT_BLOB_SHA = "b13ec7655bbdb8db1079c3b4793a0bf5590ef69c"
RECEIPT_SHA256 = "d32d833af25e4ebb2f5bd06b64343eb36d7cd180c8e9777f539f6401b78064b3"
RECEIPT_SIZE = 3_363

EXPECTED_PUBLIC_PATHS = (
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
EXPECTED_APP_SOURCE_MAP = {
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
EXPECTED_TAG_SOURCE_MAP = {
    "evidence/final-result-receipt.json": "docs/final-result-receipt.json",
    "evidence/release-v0.2.0.json": "docs/release-v0.2.0.json",
    "LICENSE": "LICENSE",
    "NOTICE": "NOTICE",
    "CITATION.cff": "CITATION.cff",
}
EXPECTED_MANIFEST_SOURCE_MAP = {"deployment-manifest.json": "space/deployment-manifest.json"}

SBOM_WEBKIT_RECORD = {
    "SPDXID": "SPDXRef-Package-webkit-26.5",
    "checksums": [
        {
            "algorithm": "SHA256",
            "checksumValue": "c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c",
        }
    ],
    "copyrightText": "NOASSERTION",
    "downloadLocation": "https://github.com/microsoft/playwright/tree/v1.62.0",
    "filesAnalyzed": False,
    "licenseConcluded": "NOASSERTION",
    "licenseDeclared": "NOASSERTION",
    "name": "webkit",
    "versionInfo": "26.5",
}
THIRD_PARTY_WEBKIT_RECORD = {
    "artifact_sha256": [
        "c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c"
    ],
    "base_branch": "main",
    "base_revision": "343e13bf22dca9d0ec227801419aab0f9001a32f",
    "browsers_json_url": (
        "https://github.com/microsoft/playwright/blob/v1.62.0/packages/playwright-core/"
        "browsers.json"
    ),
    "cdn_artifact_url": (
        "https://cdn.playwright.dev/dbazure/download/playwright/builds/webkit/2336/"
        "webkit-ubuntu-24.04.zip"
    ),
    "commit_pinned_raw_url": (
        "https://raw.githubusercontent.com/microsoft/playwright/"
        "e3950d9c140d007bd52853b45813c6274b24e36f/browser_patches/webkit/UPSTREAM_CONFIG.sh"
    ),
    "complete_digest_bound_notice": False,
    "image_tree_source_relative_path_absence_proof": {
        "canonical_tree_algorithm": "sha256-canonical-tree-v1",
        "canonical_tree_file_count": 38,
        "canonical_tree_sha256": (
            "c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c"
        ),
        "canonical_tree_total_bytes": 306_401_261,
        "present": False,
        "repository_relative_path": "browser_patches/webkit/UPSTREAM_CONFIG.sh",
    },
    "licenseConcluded": "NOASSERTION",
    "licenseDeclared": "NOASSERTION",
    "official_webkit_licensing_references": [
        "https://webkit.org/licensing-webkit/",
        (
            "https://github.com/WebKit/WebKit/blob/"
            "343e13bf22dca9d0ec227801419aab0f9001a32f/Source/WebCore/LICENSE-APPLE"
        ),
        (
            "https://github.com/WebKit/WebKit/blob/"
            "343e13bf22dca9d0ec227801419aab0f9001a32f/Source/WebCore/LICENSE-LGPL-2"
        ),
    ],
    "package": "webkit",
    "playwright_tag": "v1.62.0",
    "playwright_tag_commit": "e3950d9c140d007bd52853b45813c6274b24e36f",
    "playwright_tag_url": "https://github.com/microsoft/playwright/tree/v1.62.0",
    "playwright_version": "1.62.0",
    "raw_byte_length": 126,
    "raw_sha256": "3554c5b666ed87032fb22e78956f8a2fffe1faede63ae8dcae60a26961f6419c",
    "registry_source_url": (
        "https://github.com/microsoft/playwright/blob/v1.62.0/packages/playwright-core/"
        "src/server/registry/index.ts"
    ),
    "remote_url": "https://github.com/WebKit/WebKit.git",
    "repository_relative_path": "browser_patches/webkit/UPSTREAM_CONFIG.sh",
    "review_disposition": "reviewer_test_only_not_redistributed",
    "reviewer_image_tag": "mcr.microsoft.com/playwright/python:v1.62.0-noble",
    "reviewer_index_digest": (
        "sha256:aa81288e738725378becba5b3e06cb0f3a7f012a610e87e8d767a090ea3f740d"
    ),
    "reviewer_linux_amd64_digest": (
        "sha256:51d31fdfacb0cff99a1a724152e34ae408d2bd4e7da310ff157450f49261cc59"
    ),
    "version": "26.5",
    "webkit_revision": "2336",
    "webkit_tree_algorithm": "sha256-canonical-tree-v1",
    "webkit_tree_file_count": 38,
    "webkit_tree_sha256": (
        "c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c"
    ),
    "webkit_tree_total_bytes": 306_401_261,
    "webkit_version": "26.5",
}

CAPABILITIES = {
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


def _git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["git", "-C", os.fspath(repo), *args],
        input=input_bytes,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr.decode(errors="replace"))
    return result.stdout


def _write(repo: Path, source_path: str, raw: bytes) -> None:
    path = repo.joinpath(*source_path.split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def _canonical_json(value: object) -> bytes:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (text + "\n").encode()


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


def _default_app_files() -> dict[str, bytes]:
    files = {
        source_path: f"synthetic committed bytes for {source_path}\n".encode()
        for source_path in EXPECTED_APP_SOURCE_MAP.values()
    }
    sbom = json.loads(
        _git(PROJECT_ROOT, "show", f"{TASK7_SOURCE_SHA}:space/SBOM.spdx.json")
    )
    third_party = json.loads(
        _git(
            PROJECT_ROOT,
            "show",
            f"{TASK7_SOURCE_SHA}:space/THIRD_PARTY_LICENSES.json",
        )
    )
    browser_identities = {"chromium", "firefox", "ffmpeg", "webkit"}
    files["space/SBOM.spdx.json"] = _canonical_json(
        {
            "packages": [
                record for record in sbom["packages"] if record.get("name") in browser_identities
            ],
            "spdxVersion": "SPDX-2.3",
        }
    )
    files["space/THIRD_PARTY_LICENSES.json"] = _canonical_json(
        {
            "components": [
                record
                for record in third_party["components"]
                if record.get("package") in browser_identities
            ],
            "document_version": 1,
        }
    )
    return files


def _metadata_document(destination: str) -> tuple[dict[str, object], str, str]:
    raw = _default_app_files()[EXPECTED_APP_SOURCE_MAP[destination]]
    document = json.loads(raw)
    if destination == "SBOM.spdx.json":
        return document, "packages", "name"
    return document, "components", "package"


def _mutated_metadata(
    destination: str,
    identity: str,
    mutation: Callable[[dict[str, object], list[object], dict[str, object]], None],
) -> bytes:
    document, collection_key, identity_key = _metadata_document(destination)
    records = document[collection_key]
    assert isinstance(records, list)
    record = next(
        item
        for item in records
        if isinstance(item, dict) and item.get(identity_key) == identity
    )
    mutation(document, records, record)
    return _canonical_json(document)


def _manifest(
    *,
    app_sha: str,
    app_files: dict[str, bytes],
    tag_files: dict[str, bytes],
) -> dict[str, object]:
    by_destination = {
        destination: app_files[source] for destination, source in EXPECTED_APP_SOURCE_MAP.items()
    }
    by_destination.update(
        {destination: tag_files[source] for destination, source in EXPECTED_TAG_SOURCE_MAP.items()}
    )
    files = []
    for destination in sorted(EXPECTED_PUBLIC_PATHS):
        is_manifest = destination == "deployment-manifest.json"
        is_tag = destination in EXPECTED_TAG_SOURCE_MAP
        source_path = (
            EXPECTED_MANIFEST_SOURCE_MAP[destination]
            if is_manifest
            else EXPECTED_TAG_SOURCE_MAP[destination]
            if is_tag
            else EXPECTED_APP_SOURCE_MAP[destination]
        )
        raw = None if is_manifest else by_destination[destination]
        files.append(
            {
                "source_ref": (
                    "export-manifest-commit"
                    if is_manifest
                    else TAG_COMMIT_SHA
                    if is_tag
                    else app_sha
                ),
                "source_path": source_path,
                "destination_path": destination,
                "sha256": None if raw is None else hashlib.sha256(raw).hexdigest(),
                "byte_size": None if raw is None else len(raw),
                "media_type": _media_type(destination),
                "capability": CAPABILITIES[destination],
            }
        )
    return {
        "schema_version": 1,
        "space_app_source_git_sha": app_sha,
        "evidence_tag": "v0.2.0",
        "evidence_tag_object": TAG_OBJECT_SHA,
        "evidence_tag_commit": TAG_COMMIT_SHA,
        "destination_repository": "steven0226/carerisk-48h",
        "base_images": {
            "runtime": {
                "repository": "docker.io/library/python",
                "tag": "3.11.14-slim-bookworm",
                "index_digest": "sha256:" + "1" * 64,
                "linux_amd64_digest": "sha256:" + "2" * 64,
            },
            "reviewer": {
                "repository": "mcr.microsoft.com/playwright/python",
                "tag": "v1.62.0-noble",
                "index_digest": (
                    "sha256:aa81288e738725378becba5b3e06cb0f3a7f012a610e87e8d767a090ea3f740d"
                ),
                "linux_amd64_digest": (
                    "sha256:51d31fdfacb0cff99a1a724152e34ae408d2bd4e7da310ff157450f49261cc59"
                ),
            },
        },
        "supply_chain": {
            "runtime_lock_sha256": hashlib.sha256(by_destination["requirements.lock"]).hexdigest(),
            "development_lock_sha256": hashlib.sha256(
                by_destination["requirements-dev.lock"]
            ).hexdigest(),
            "sbom_sha256": hashlib.sha256(by_destination["SBOM.spdx.json"]).hexdigest(),
            "third_party_licenses_sha256": hashlib.sha256(
                by_destination["THIRD_PARTY_LICENSES.json"]
            ).hexdigest(),
        },
        "files": files,
    }


@dataclass(frozen=True)
class SyntheticRepo:
    root: Path
    app_sha: str
    manifest_sha: str
    destination: Path


ManifestMutation = Callable[[dict[str, object]], None]


@dataclass
class ExporterCase:
    tmp_path: Path
    sequence: int = 0

    def build(
        self,
        *,
        app_override: tuple[str, bytes] | None = None,
        manifest_mutation: ManifestMutation | None = None,
        symlink_source: bool = False,
    ) -> SyntheticRepo:
        self.sequence += 1
        repo = self.tmp_path / f"repo-{self.sequence}"
        repo.mkdir()
        _git(repo, "init", "--initial-branch=main")
        _git(repo, "config", "user.name", "Task 8 Synthetic")
        _git(repo, "config", "user.email", "task8@example.invalid")
        _git(repo, "config", "core.autocrlf", "false")
        _git(repo, "config", "core.symlinks", "false")
        _git(
            repo,
            "fetch",
            os.fspath(PROJECT_ROOT),
            "refs/tags/v0.2.0:refs/tags/v0.2.0",
        )
        app_files = _default_app_files()
        if app_override is not None:
            app_files[EXPECTED_APP_SOURCE_MAP[app_override[0]]] = app_override[1]
        for source_path, raw in app_files.items():
            if symlink_source and source_path == "space/app.py":
                continue
            _write(repo, source_path, raw)
        explicit_sources = sorted(app_files)
        if symlink_source:
            explicit_sources.remove("space/app.py")
        _git(repo, "add", "--", *explicit_sources)
        if symlink_source:
            target = b"carerisk_space/ui.py"
            blob = _git(repo, "hash-object", "-w", "--stdin", input_bytes=target).decode().strip()
            _git(repo, "update-index", "--add", "--cacheinfo", f"120000,{blob},space/app.py")
            app_files["space/app.py"] = target
        _git(repo, "commit", "-m", "synthetic app source")
        app_sha = _git(repo, "rev-parse", "HEAD").decode().strip()
        if symlink_source:
            _git(repo, "checkout", "HEAD", "--", "space/app.py")
        tag_files = {
            source: _git(repo, "show", f"{TAG_COMMIT_SHA}:{source}")
            for source in EXPECTED_TAG_SOURCE_MAP.values()
        }
        manifest = _manifest(app_sha=app_sha, app_files=app_files, tag_files=tag_files)
        if manifest_mutation is not None:
            manifest_mutation(manifest)
        _write(repo, "space/deployment-manifest.json", _canonical_json(manifest))
        _git(repo, "add", "--", "space/deployment-manifest.json")
        _git(repo, "commit", "-m", "synthetic export manifest")
        manifest_sha = _git(repo, "rev-parse", "HEAD").decode().strip()
        assert not _git(repo, "status", "--porcelain=v1", "--untracked-files=all")
        return SyntheticRepo(
            root=repo,
            app_sha=app_sha,
            manifest_sha=manifest_sha,
            destination=self.tmp_path / f"candidate-{self.sequence}",
        )

    def run(self, case: str) -> object:
        mutation: ManifestMutation | None = None
        override: tuple[str, bytes] | None = None
        symlink = False
        if case == "large_file":
            override = ("README.md", b"x" * 1_048_577)
        elif case == "secret_signature":
            override = ("app.py", b"api_key=synthetic-forbidden-value\n")
        elif case == "binary_signature":
            override = ("app.py", b"\x7fELFsynthetic")
        elif case == "symlink":
            symlink = True
        elif case == "extra_path":
            def add_extra(manifest: dict[str, object]) -> None:
                files = manifest["files"]
                assert isinstance(files, list)
                files.append(
                    {
                        "source_ref": "export-manifest-commit",
                        "source_path": "unexpected.txt",
                        "destination_path": "unexpected.txt",
                        "sha256": None,
                        "byte_size": None,
                        "media_type": "text/plain",
                        "capability": "metadata",
                    }
                )

            mutation = add_extra
        elif case == "path_traversal":
            def traverse(manifest: dict[str, object]) -> None:
                files = manifest["files"]
                assert isinstance(files, list)
                item = next(value for value in files if value["destination_path"] == "app.py")
                item["source_path"] = "../space/app.py"

            mutation = traverse
        repo = self.build(
            app_override=override,
            manifest_mutation=mutation,
            symlink_source=symlink,
        )
        if case == "dirty_source":
            (repo.root / "space/app.py").write_bytes(b"dirty checkout bytes\n")
        elif case == "nonempty_destination":
            repo.destination.mkdir()
            (repo.destination / "sentinel.txt").write_text("preserve", encoding="utf-8")
        elif case == "wrong_tag_commit":
            _git(repo.root, "tag", "--force", "v0.2.0", repo.app_sha)
        return export_space(
            repo_root=repo.root,
            app_source_sha=repo.app_sha,
            manifest_source_sha=repo.manifest_sha,
            destination=repo.destination,
        )

    def run_with_added_bytes(self, capability: str, token: bytes) -> object:
        destination = next(
            path
            for path in EXPECTED_PUBLIC_PATHS
            if CAPABILITIES[path] == capability and path in EXPECTED_APP_SOURCE_MAP
        )
        repo = self.build(app_override=(destination, b"synthetic-prefix\n" + token + b"\n"))
        return export_space(
            repo_root=repo.root,
            app_source_sha=repo.app_sha,
            manifest_source_sha=repo.manifest_sha,
            destination=repo.destination,
        )


@pytest.fixture
def exporter_case(tmp_path: Path) -> ExporterCase:
    return ExporterCase(tmp_path)


@pytest.fixture
def git_repo(exporter_case: ExporterCase) -> SyntheticRepo:
    return exporter_case.build()


def test_source_maps_partition_the_exact_public_allowlist() -> None:
    assert APP_SOURCE_MAP == EXPECTED_APP_SOURCE_MAP
    assert TAG_SOURCE_MAP == EXPECTED_TAG_SOURCE_MAP
    assert MANIFEST_SOURCE_MAP == EXPECTED_MANIFEST_SOURCE_MAP
    assert PUBLIC_PATHS == EXPECTED_PUBLIC_PATHS
    source_sets = tuple(map(set, (APP_SOURCE_MAP, TAG_SOURCE_MAP, MANIFEST_SOURCE_MAP)))
    assert tuple(map(len, source_sets)) == (18, 5, 1)
    assert not (
        source_sets[0] & source_sets[1]
        or source_sets[0] & source_sets[2]
        or source_sets[1] & source_sets[2]
    )
    assert set().union(*source_sets) == set(PUBLIC_PATHS)
    assert "scripts/verify_hf_space_candidate.py" not in set().union(*source_sets)


def test_export_reads_committed_blobs_and_matches_exact_allowlist(git_repo: SyntheticRepo) -> None:
    checkout_path = git_repo.root / "space/app.py"
    committed = _git(git_repo.root, "cat-file", "blob", f"{git_repo.app_sha}:space/app.py")
    _git(git_repo.root, "update-index", "--skip-worktree", "space/app.py")
    checkout_path.write_bytes(b"ignored checkout-only bytes\n")
    assert not _git(git_repo.root, "status", "--porcelain=v1", "--untracked-files=all")

    receipt = export_space(
        repo_root=git_repo.root,
        app_source_sha=git_repo.app_sha,
        manifest_source_sha=git_repo.manifest_sha,
        destination=git_repo.destination,
    )

    assert tuple(item.path for item in receipt.files) == EXPECTED_PUBLIC_PATHS
    assert (receipt.destination / "app.py").read_bytes() == committed
    assert not (receipt.destination / ".git").exists()
    for item in receipt.files:
        raw = receipt.destination.joinpath(*item.path.split("/")).read_bytes()
        assert item.sha256 == hashlib.sha256(raw).hexdigest()
        assert item.byte_size == len(raw)
    listing = b"".join(
        item.path.encode()
        + b"\0"
        + item.sha256.encode()
        + b"\0"
        + str(item.byte_size).encode()
        + b"\n"
        for item in sorted(receipt.files, key=lambda value: value.path)
    )
    assert receipt.tree_sha256 == hashlib.sha256(listing).hexdigest()
    receipt_raw = (receipt.destination / "evidence/final-result-receipt.json").read_bytes()
    assert len(receipt_raw) == RECEIPT_SIZE
    assert hashlib.sha256(receipt_raw).hexdigest() == RECEIPT_SHA256
    receipt_blob = _git(
        git_repo.root, "hash-object", "--stdin", input_bytes=receipt_raw
    ).decode().strip()
    assert receipt_blob == RECEIPT_BLOB_SHA


@pytest.mark.parametrize(
    "case",
    [
        "dirty_source",
        "nonempty_destination",
        "symlink",
        "extra_path",
        "large_file",
        "secret_signature",
        "binary_signature",
        "path_traversal",
        "wrong_tag_commit",
    ],
)
def test_export_rejects_unsafe_source_or_destination(
    case: str, exporter_case: ExporterCase
) -> None:
    with pytest.raises(ExportError, match=case):
        exporter_case.run(case)


def test_manifest_is_two_commit_non_self_referential_contract(git_repo: SyntheticRepo) -> None:
    raw = _git(
        git_repo.root,
        "cat-file",
        "blob",
        f"{git_repo.manifest_sha}:space/deployment-manifest.json",
    )
    manifest = json.loads(raw)
    assert manifest["space_app_source_git_sha"] == git_repo.app_sha
    assert git_repo.manifest_sha != git_repo.app_sha
    assert not subprocess.run(
        [
            "git",
            "-C",
            os.fspath(git_repo.root),
            "merge-base",
            "--is-ancestor",
            git_repo.app_sha,
            git_repo.manifest_sha,
        ],
        check=False,
    ).returncode
    assert "destination_commit" not in manifest
    manifest_item = next(
        item for item in manifest["files"] if item["destination_path"] == "deployment-manifest.json"
    )
    assert manifest_item["sha256"] is None
    assert manifest_item["byte_size"] is None


def test_export_contains_webkit_policy_metadata_but_no_reviewer_or_browser_bytes(
    git_repo: SyntheticRepo,
) -> None:
    receipt = export_space(
        repo_root=git_repo.root,
        app_source_sha=git_repo.app_sha,
        manifest_source_sha=git_repo.manifest_sha,
        destination=git_repo.destination,
    )
    assert_exact_webkit_metadata_only(receipt.destination)
    assert_no_reviewer_or_browser_bytes(receipt.destination)


@pytest.mark.parametrize("identity", ["chromium", "firefox", "ffmpeg"])
@pytest.mark.parametrize("destination", ["SBOM.spdx.json", "THIRD_PARTY_LICENSES.json"])
def test_export_requires_each_approved_ordinary_browser_metadata_record(
    identity: str,
    destination: str,
    exporter_case: ExporterCase,
) -> None:
    def remove_record(
        _document: dict[str, object], records: list[object], record: dict[str, object]
    ) -> None:
        records.remove(record)

    raw = _mutated_metadata(destination, identity, remove_record)
    repo = exporter_case.build(app_override=(destination, raw))
    with pytest.raises(ExportError, match="approved_browser_metadata_invalid"):
        export_space(
            repo_root=repo.root,
            app_source_sha=repo.app_sha,
            manifest_source_sha=repo.manifest_sha,
            destination=repo.destination,
        )


@pytest.mark.parametrize("identity", ["chromium", "firefox", "ffmpeg"])
@pytest.mark.parametrize(
    "record_source,destination",
    [
        ("SBOM.spdx.json", "SBOM.spdx.json"),
        ("SBOM.spdx.json", "THIRD_PARTY_LICENSES.json"),
        ("THIRD_PARTY_LICENSES.json", "SBOM.spdx.json"),
        ("THIRD_PARTY_LICENSES.json", "THIRD_PARTY_LICENSES.json"),
    ],
)
def test_export_rejects_duplicate_or_wrong_schema_non_webkit_record(
    identity: str,
    record_source: str,
    destination: str,
    exporter_case: ExporterCase,
) -> None:
    source_document, source_collection, source_identity = _metadata_document(record_source)
    source_records = source_document[source_collection]
    assert isinstance(source_records, list)
    inserted = next(
        dict(item)
        for item in source_records
        if isinstance(item, dict) and item.get(source_identity) == identity
    )

    def insert_record(
        _document: dict[str, object], records: list[object], _record: dict[str, object]
    ) -> None:
        records.append(inserted)

    raw = _mutated_metadata(destination, identity, insert_record)
    repo = exporter_case.build(app_override=(destination, raw))
    with pytest.raises(ExportError):
        export_space(
            repo_root=repo.root,
            app_source_sha=repo.app_sha,
            manifest_source_sha=repo.manifest_sha,
            destination=repo.destination,
        )


@pytest.mark.parametrize("identity", ["chromium", "firefox", "ffmpeg"])
@pytest.mark.parametrize("destination", ["SBOM.spdx.json", "THIRD_PARTY_LICENSES.json"])
def test_export_rejects_unrecognized_browser_record(
    identity: str,
    destination: str,
    exporter_case: ExporterCase,
) -> None:
    _document, _collection, identity_key = _metadata_document(destination)

    def add_unrecognized(
        _document: dict[str, object], records: list[object], record: dict[str, object]
    ) -> None:
        added = dict(record)
        added[identity_key] = f"{identity}-nightly"
        records.append(added)

    raw = _mutated_metadata(destination, identity, add_unrecognized)
    repo = exporter_case.build(app_override=(destination, raw))
    with pytest.raises(ExportError):
        export_space(
            repo_root=repo.root,
            app_source_sha=repo.app_sha,
            manifest_source_sha=repo.manifest_sha,
            destination=repo.destination,
        )


@pytest.mark.parametrize(
    "destination,identity,updates",
    [
        ("SBOM.spdx.json", "chromium", {"licenseConcluded": "MIT"}),
        ("SBOM.spdx.json", "ffmpeg", {"licenseDeclared": "NOASSERTION"}),
        (
            "THIRD_PARTY_LICENSES.json",
            "firefox",
            {"review_disposition": "approved"},
        ),
        (
            "THIRD_PARTY_LICENSES.json",
            "ffmpeg",
            {
                "licenseDeclared": "NOASSERTION",
                "licenseConcluded": "NOASSERTION",
                "review_disposition": "reviewer_test_only_not_redistributed",
            },
        ),
        ("SBOM.spdx.json", "webkit", {"licenseConcluded": "LGPL-2.1-only"}),
        (
            "THIRD_PARTY_LICENSES.json",
            "webkit",
            {"review_disposition": "approved"},
        ),
    ],
)
def test_export_rejects_browser_license_or_disposition_drift(
    destination: str,
    identity: str,
    updates: dict[str, object],
    exporter_case: ExporterCase,
) -> None:
    def drift_record(
        _document: dict[str, object], _records: list[object], record: dict[str, object]
    ) -> None:
        record.update(updates)

    raw = _mutated_metadata(destination, identity, drift_record)
    repo = exporter_case.build(app_override=(destination, raw))
    with pytest.raises(ExportError):
        export_space(
            repo_root=repo.root,
            app_source_sha=repo.app_sha,
            manifest_source_sha=repo.manifest_sha,
            destination=repo.destination,
        )


@pytest.mark.parametrize("token", REVIEWER_BROWSER_BYTE_SIGNATURES)
@pytest.mark.parametrize("destination", ["SBOM.spdx.json", "THIRD_PARTY_LICENSES.json"])
def test_export_rejects_residual_browser_signature_in_metadata(
    token: bytes,
    destination: str,
    exporter_case: ExporterCase,
) -> None:
    document, _collection, _identity_key = _metadata_document(destination)
    document["unexpected_browser_payload"] = token.decode()
    repo = exporter_case.build(app_override=(destination, _canonical_json(document)))
    with pytest.raises(ExportError, match="reviewer bytes reached public export"):
        export_space(
            repo_root=repo.root,
            app_source_sha=repo.app_sha,
            manifest_source_sha=repo.manifest_sha,
            destination=repo.destination,
        )


@pytest.mark.parametrize("token", REVIEWER_BROWSER_BYTE_SIGNATURES)
@pytest.mark.parametrize("capability", ["runtime_code", "test", "supply_chain", "metadata"])
def test_export_rejects_reviewer_or_browser_byte_signatures(
    token: bytes, capability: str, exporter_case: ExporterCase
) -> None:
    with pytest.raises(ExportError, match="reviewer bytes reached public export"):
        exporter_case.run_with_added_bytes(capability, token)


@pytest.mark.parametrize(
    "mutation_name,mutation",
    [
        (
            "unsorted_paths",
            lambda manifest: manifest["files"].reverse(),
        ),
        (
            "duplicate_paths",
            lambda manifest: manifest["files"].append(dict(manifest["files"][0])),
        ),
        (
            "hash_mismatch",
            lambda manifest: manifest["files"][0].update(sha256="0" * 64),
        ),
        (
            "size_mismatch",
            lambda manifest: manifest["files"][0].update(
                byte_size=manifest["files"][0]["byte_size"] + 1
            ),
        ),
        (
            "manifest_self_reference",
            lambda manifest: manifest.update(destination_commit="0" * 40),
        ),
    ],
)
def test_manifest_rejects_order_duplicates_integrity_and_self_reference(
    mutation_name: str,
    mutation: ManifestMutation,
    exporter_case: ExporterCase,
) -> None:
    repo = exporter_case.build(manifest_mutation=mutation)
    with pytest.raises(ExportError, match=mutation_name):
        export_space(
            repo_root=repo.root,
            app_source_sha=repo.app_sha,
            manifest_source_sha=repo.manifest_sha,
            destination=repo.destination,
        )
    assert not repo.destination.exists()


def test_export_failure_cleans_only_the_fresh_verified_destination(
    exporter_case: ExporterCase,
) -> None:
    repo = exporter_case.build(app_override=("README.md", b"x" * 1_048_577))
    sibling = repo.destination.with_name("candidate-sibling")
    sibling.mkdir()
    (sibling / "sentinel.txt").write_text("preserve", encoding="utf-8")
    with pytest.raises(ExportError, match="large_file"):
        export_space(
            repo_root=repo.root,
            app_source_sha=repo.app_sha,
            manifest_source_sha=repo.manifest_sha,
            destination=repo.destination,
        )
    assert not repo.destination.exists()
    assert (sibling / "sentinel.txt").read_text(encoding="utf-8") == "preserve"


def test_nonempty_destination_is_rejected_without_cleanup(exporter_case: ExporterCase) -> None:
    repo = exporter_case.build()
    repo.destination.mkdir()
    sentinel = repo.destination / "sentinel.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    with pytest.raises(ExportError, match="nonempty_destination"):
        export_space(
            repo_root=repo.root,
            app_source_sha=repo.app_sha,
            manifest_source_sha=repo.manifest_sha,
            destination=repo.destination,
        )
    assert sentinel.read_text(encoding="utf-8") == "preserve"


@pytest.mark.parametrize("sha_kind", ["missing_app", "tree_manifest", "non_ancestor"])
def test_export_rejects_missing_noncommit_or_nonancestor_sha(
    sha_kind: str, exporter_case: ExporterCase
) -> None:
    repo = exporter_case.build()
    app_sha = repo.app_sha
    manifest_sha = repo.manifest_sha
    if sha_kind == "missing_app":
        app_sha = "0" * 40
    elif sha_kind == "tree_manifest":
        manifest_sha = _git(
            repo.root, "rev-parse", f"{repo.manifest_sha}^{{tree}}"
        ).decode().strip()
    else:
        tree = _git(repo.root, "rev-parse", f"{repo.app_sha}^{{tree}}").decode().strip()
        manifest_sha = _git(
            repo.root,
            "commit-tree",
            tree,
            input_bytes=b"unrelated manifest\n",
        ).decode().strip()
    with pytest.raises(ExportError, match=sha_kind):
        export_space(
            repo_root=repo.root,
            app_source_sha=app_sha,
            manifest_source_sha=manifest_sha,
            destination=repo.destination,
        )


def test_export_rejects_noncanonical_manifest_bytes(exporter_case: ExporterCase) -> None:
    repo = exporter_case.build()
    manifest = json.loads((repo.root / "space/deployment-manifest.json").read_bytes())
    (repo.root / "space/deployment-manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8", newline="\n"
    )
    _git(repo.root, "add", "--", "space/deployment-manifest.json")
    _git(repo.root, "commit", "-m", "noncanonical manifest")
    noncanonical_sha = _git(repo.root, "rev-parse", "HEAD").decode().strip()
    with pytest.raises(ExportError, match="noncanonical_manifest"):
        export_space(
            repo_root=repo.root,
            app_source_sha=repo.app_sha,
            manifest_source_sha=noncanonical_sha,
            destination=repo.destination,
        )


def test_git_object_modes_reject_non_regular_entries(exporter_case: ExporterCase) -> None:
    repo = exporter_case.build(symlink_source=True)
    mode = _git(repo.root, "ls-tree", repo.app_sha, "--", "space/app.py").split()[0]
    assert stat.S_IFMT(int(mode, 8)) == stat.S_IFLNK
    with pytest.raises(ExportError, match="symlink"):
        export_space(
            repo_root=repo.root,
            app_source_sha=repo.app_sha,
            manifest_source_sha=repo.manifest_sha,
            destination=repo.destination,
        )
