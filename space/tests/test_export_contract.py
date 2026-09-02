"""Pure path/content gates for the later clean-export implementation."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import stat
from pathlib import Path, PurePosixPath

SPACE_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_SOURCE = SPACE_ROOT / "carerisk_space" / "contracts.py"
EVIDENCE_SOURCE = SPACE_ROOT / "carerisk_space" / "evidence.py"
MAX_PUBLIC_FILE_BYTES = 1_048_576

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
EXPECTED_PUBLIC_SOURCE_PATHS = (
    "space/README.md",
    "space/Dockerfile",
    "space/requirements.lock",
    "space/requirements-dev.lock",
    "space/app.py",
    "space/carerisk_space/__init__.py",
    "space/carerisk_space/contracts.py",
    "space/carerisk_space/evidence.py",
    "space/carerisk_space/scenarios.py",
    "space/carerisk_space/ui.py",
    "docs/final-result-receipt.json",
    "docs/release-v0.2.0.json",
    "space/deployment-manifest.json",
    "LICENSE",
    "NOTICE",
    "CITATION.cff",
    "space/SBOM.spdx.json",
    "space/THIRD_PARTY_LICENSES.json",
    "space/tests/test_claim_contract.py",
    "space/tests/test_evidence_contract.py",
    "space/tests/test_scenario_contract.py",
    "space/tests/test_gradio_contract.py",
    "space/tests/test_export_contract.py",
    "space/tests/test_container_contract.py",
)

DENY_COMPONENTS = frozenset(
    {
        ".agents",
        ".git",
        ".github",
        "artifacts",
        "bundles",
        "caches",
        "checkpoints",
        "coverage",
        "data",
        "models",
        "patches",
        "reports",
        "results",
        "worktrees",
    }
)
DENY_SUFFIXES = frozenset(
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
DENY_PATH_PATTERNS = (
    re.compile(r"(^|/)\.env(?:\.[^/]+)?$", re.IGNORECASE),
    re.compile(r"(^|/)(?:credential|token|key|cookie|auth|secret|variable)[^/]*", re.IGNORECASE),
    re.compile(r"(^|/)(?:notebooks?|temp(?:orary)?|build|reflogs?|history)(?:/|$)", re.IGNORECASE),
    re.compile(r"(^|/)(?:raw|processed).*physionet", re.IGNORECASE),
    re.compile(
        r"(^|/)(?:outcome|row|record|prediction|subgroup|error|access-ledger|final-lock|artifact-map|env-capture)",
        re.IGNORECASE,
    ),
    re.compile(r"(^|/)(?:plot|plots|screenshot|screenshots)(?:/|$)", re.IGNORECASE),
    re.compile(r"(^|/)docs/assets/final-evaluation-overview\.png$", re.IGNORECASE),
    re.compile(r"(^|/)(?:app/dashboard\.py|src/carerisk48h)(?:/|$)", re.IGNORECASE),
    re.compile(r"(^|/)configs/inference_schema\.json$", re.IGNORECASE),
    re.compile(
        r"(^|/)(?:training|downloader|evaluation|synthetic.*scoring.*bundle)(?:/|$)", re.IGNORECASE
    ),
    re.compile(r"(^|/)(?:AGENTS\.md|PROJECT_PLAN\.md|interview\.md)(?:/|$)", re.IGNORECASE),
)
FORBIDDEN_CONTENT = (
    re.compile(rb"-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----"),
    re.compile(rb"\b(?:api[_-]?key|password|secret|token)\s*[:=]", re.IGNORECASE),
    re.compile(rb"\b(?:ghp|github_pat|hf)_[A-Za-z0-9_\-]{12,}"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
)
EXECUTABLE_BINARY_SIGNATURES = (b"\x7fELF", b"MZ", b"\xca\xfe\xba\xbe", b"\xfe\xed\xfa")
REVIEWER_BROWSER_BYTE_SIGNATURES = (
    b"/ms-" b"playwright/chromium-",
    b"/ms-" b"playwright/chromium_headless_shell-",
    b"/ms-" b"playwright/firefox-",
    b"/ms-" b"playwright/webkit-",
    b"/ms-" b"playwright/ffmpeg-",
    b"chrome-linux64/" b"chrome",
    b"firefox/" b"firefox",
    b"minibrowser-gtk/" b"bin/MiniBrowser",
    b"minibrowser-wpe/" b"bin/MiniBrowser",
)
WEBKIT_EXCEPTION_MARKER = b"reviewer_test_only_" b"not_redistributed"
WEBKIT_METADATA_PATHS = frozenset({"SBOM.spdx.json", "THIRD_PARTY_LICENSES.json"})
EXPECTED_SBOM_WEBKIT_RECORD_SHA256 = (
    "63f2a7be2b20d7adaae63361e12ea95e0f3894fc69c6202a227be6f797a707b8"
)
EXPECTED_THIRD_PARTY_WEBKIT_RECORD_SHA256 = (
    "20831fd7b773fe13bf5a7508181b301b49bb9d0e0d89ccc4d1b25ac8baca7046"
)
EXPECTED_THIRD_PARTY_BROWSER_RECORD_SHA256 = {
    "chromium": "116821ea11186ffc5eab80b7740f38dc162b0f61b1f1aac30eb6bde5bf8b7705",
    "firefox": "f438e37eee9b74996b1afdca3244ad4ce2aaf9f5bb3bf05995b03795e38431bf",
    "webkit": EXPECTED_THIRD_PARTY_WEBKIT_RECORD_SHA256,
    "ffmpeg": "1c9e9d22be5dd9d05d8b76af7d5510517eb45c457c0d88ffafdd711a32a11264",
}


def _public_paths_from_ast() -> tuple[str, ...]:
    tree = ast.parse(CONTRACTS_SOURCE.read_text(encoding="utf-8"), filename=str(CONTRACTS_SOURCE))
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "PUBLIC_PATHS"
    )
    assert assignment.value is not None
    return ast.literal_eval(assignment.value)


def _source_paths_from_ast() -> dict[str, str]:
    tree = ast.parse(EVIDENCE_SOURCE.read_text(encoding="utf-8"), filename=str(EVIDENCE_SOURCE))
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "_SOURCE_PATHS" for target in node.targets
        )
    )
    return ast.literal_eval(assignment.value)


PUBLIC_PATHS = _public_paths_from_ast()
PUBLIC_SOURCE_PATHS = tuple(_source_paths_from_ast()[path] for path in PUBLIC_PATHS)


def _canonical(path: str) -> str | None:
    if not isinstance(path, str) or not path or "\\" in path:
        return None
    value = PurePosixPath(path)
    if value.is_absolute() or any(part in {"", ".", ".."} for part in value.parts):
        return None
    return value.as_posix()


def is_public_path(path: str) -> bool:
    canonical = _canonical(path)
    if canonical is None:
        return False
    lower = canonical.casefold()
    if any(component.casefold() in DENY_COMPONENTS for component in canonical.split("/")):
        return False
    if any(lower.endswith(suffix) for suffix in DENY_SUFFIXES):
        return False
    if any(pattern.search(canonical) for pattern in DENY_PATH_PATTERNS):
        return False
    return canonical in PUBLIC_PATHS


def accepts_public_file(path: str, raw: bytes, mode: int) -> bool:
    """Accept only a bounded regular public file represented by synthetic bytes."""

    if not is_public_path(path) or len(raw) > MAX_PUBLIC_FILE_BYTES or not stat.S_ISREG(mode):
        return False
    if stat.S_ISLNK(mode) or stat.S_ISFIFO(mode) or stat.S_ISCHR(mode) or stat.S_ISBLK(mode):
        return False
    if any(raw.startswith(signature) for signature in EXECUTABLE_BINARY_SIGNATURES):
        return False
    return not any(pattern.search(raw) for pattern in FORBIDDEN_CONTENT)


def _canonical_record_sha256(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def assert_exact_webkit_metadata_only(bundle_root: Path) -> None:
    """Assert the reviewer-only WebKit exception is exactly the Task 7 metadata pair."""

    sbom = json.loads((bundle_root / "SBOM.spdx.json").read_bytes())
    third_party = json.loads((bundle_root / "THIRD_PARTY_LICENSES.json").read_bytes())
    sbom_records = [item for item in sbom["packages"] if item.get("name") == "webkit"]
    third_party_records = [
        item for item in third_party["components"] if item.get("package") == "webkit"
    ]
    assert len(sbom_records) == len(third_party_records) == 1
    assert _canonical_record_sha256(sbom_records[0]) == EXPECTED_SBOM_WEBKIT_RECORD_SHA256
    assert (
        _canonical_record_sha256(third_party_records[0])
        == EXPECTED_THIRD_PARTY_WEBKIT_RECORD_SHA256
    )
    for path in PUBLIC_PATHS:
        candidate = bundle_root.joinpath(*path.split("/"))
        if path not in WEBKIT_METADATA_PATHS and candidate.exists():
            assert WEBKIT_EXCEPTION_MARKER not in candidate.read_bytes()


def assert_no_reviewer_or_browser_bytes(bundle_root: Path) -> None:
    for path in PUBLIC_PATHS:
        candidate = bundle_root.joinpath(*path.split("/"))
        if candidate.exists():
            raw = candidate.read_bytes()
            if path == "THIRD_PARTY_LICENSES.json":
                value = json.loads(raw)
                for record in value["components"]:
                    package = record.get("package")
                    if package in EXPECTED_THIRD_PARTY_BROWSER_RECORD_SHA256:
                        assert (
                            _canonical_record_sha256(record)
                            == EXPECTED_THIRD_PARTY_BROWSER_RECORD_SHA256[package]
                        )
                        encoded = json.dumps(
                            record,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode()
                        assert raw.count(encoded) == 1
                        raw = raw.replace(encoded, b"", 1)
            assert all(token not in raw for token in REVIEWER_BROWSER_BYTE_SIGNATURES)


def test_public_paths_are_exact_and_independently_repeated() -> None:
    assert PUBLIC_PATHS == EXPECTED_PUBLIC_PATHS
    assert len(PUBLIC_PATHS) == len(set(PUBLIC_PATHS)) == 24


def test_existing_application_and_private_paths_are_absent_from_source_or_destination_tuples() -> (
    None
):
    source_only_excluded = ("app/dashboard.py", "app.py", "src/carerisk48h")
    destination_excluded = (
        "app/dashboard.py",
        "src/carerisk48h",
        "docs/assets/final-evaluation-overview.png",
    )
    for path in source_only_excluded:
        assert path not in PUBLIC_SOURCE_PATHS
    for path in destination_excluded:
        assert path not in PUBLIC_PATHS
        assert path not in PUBLIC_SOURCE_PATHS
        assert not is_public_path(path)
    assert "app.py" in PUBLIC_PATHS
    assert "space/app.py" in PUBLIC_SOURCE_PATHS
    assert is_public_path("app.py") is True


def test_public_source_paths_are_exact_and_align_one_to_one_with_destinations() -> None:
    assert PUBLIC_SOURCE_PATHS == EXPECTED_PUBLIC_SOURCE_PATHS
    assert len(PUBLIC_SOURCE_PATHS) == len(PUBLIC_PATHS) == 24


def test_design_denylist_patterns_reject_every_private_or_legacy_path_family() -> None:
    rejected = (
        ".env.production",
        "tokens/hf_token.txt",
        ".git/config",
        ".github/workflows/space-ci.yml",
        "worktrees/export/README.md",
        "data/raw/physionet.csv",
        "artifacts/model.joblib",
        "reports/plot.png",
        "records/row-1.json",
        "docs/assets/final-evaluation-overview.png",
        "app/dashboard.py",
        "src/carerisk48h/demo.py",
        "configs/inference_schema.json",
        "scripts/training.py",
        "AGENTS.md",
        "PROJECT_PLAN.md",
        ".agents/handoff.md",
        "unexpected.txt",
    )
    assert all(not is_public_path(path) for path in rejected)


def test_public_candidate_rejects_oversize_special_executable_and_credential_bytes() -> None:
    regular = stat.S_IFREG | 0o644
    assert accepts_public_file("README.md", b"public synthetic text", regular)
    assert not accepts_public_file("README.md", b"x" * (MAX_PUBLIC_FILE_BYTES + 1), regular)
    assert not accepts_public_file("README.md", b"text", stat.S_IFIFO | 0o644)
    assert not accepts_public_file("README.md", b"text", stat.S_IFCHR | 0o644)
    assert not accepts_public_file("README.md", b"\x7fELFsynthetic", regular | stat.S_IXUSR)
    assert not accepts_public_file("README.md", b"token=synthetic-secret", regular)
    assert not accepts_public_file("README.md", b"-----BEGIN PRIVATE KEY-----", regular)


def test_task7_webkit_exception_is_exact_metadata_not_reviewer_payload() -> None:
    assert_exact_webkit_metadata_only(SPACE_ROOT)
    assert_no_reviewer_or_browser_bytes(SPACE_ROOT)
