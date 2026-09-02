from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_INPUT = ROOT / "tools" / "space" / "requirements-runtime.in"
DEVELOPMENT_INPUT = ROOT / "tools" / "space" / "requirements-dev.in"
RUNTIME_LOCK = ROOT / "space" / "requirements.lock"
DEVELOPMENT_LOCK = ROOT / "space" / "requirements-dev.lock"
BASE_IMAGE = ROOT / "tools" / "space" / "base-image.json"
LICENSE_POLICY = ROOT / "tools" / "space" / "license-policy.json"
LICENSE_TRUST_ROOT = ROOT / "tools" / "space" / "license-trust-root.json"
SBOM = ROOT / "space" / "SBOM.spdx.json"
LICENSES = ROOT / "space" / "THIRD_PARTY_LICENSES.json"
GENERATOR = ROOT / "scripts" / "build_hf_space_supply_chain.py"
CHILD_NETWORK_BOMB_PROBE_CODE = """\
import socket
import urllib.request

for operation in (
    lambda: socket.create_connection(("127.0.0.1", 1), timeout=0.01),
    lambda: urllib.request.urlopen("http://127.0.0.1:1", timeout=0.01),
):
    try:
        operation()
    except RuntimeError as error:
        if str(error) != "TASK7_NETWORK_BOMB":
            raise
    else:
        raise SystemExit(91)
"""


@dataclass(frozen=True)
class LockedRequirement:
    package: str
    version: str
    version_operator: str
    sha256_hashes: tuple[str, ...]
    editable: bool
    url_without_hash: bool


def _canonical_package_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_hash_lock(text: str) -> tuple[LockedRequirement, ...]:
    entries: list[LockedRequirement] = []
    lines = iter(text.splitlines())
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("--"):
            continue
        parts = [line]
        while parts[-1].rstrip().endswith("\\"):
            try:
                parts.append(next(lines).strip())
            except StopIteration as error:
                raise AssertionError("unterminated hash-lock continuation") from error
        requirement = " ".join(part.rstrip("\\").strip() for part in parts)
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)(==)([^\s;]+)(.*)", requirement)
        assert match is not None, f"not an exact requirement: {requirement}"
        package, operator, version, suffix = match.groups()
        hashes = tuple(sorted(re.findall(r"--hash=sha256:([0-9a-f]{64})", suffix)))
        entries.append(
            LockedRequirement(
                package=_canonical_package_name(package),
                version=version,
                version_operator=operator,
                sha256_hashes=hashes,
                editable=(
                    re.search(r"(?:^|\s)-e(?:\s|$)", requirement) is not None
                    or "--editable" in requirement
                ),
                url_without_hash=" @ " in requirement or "://" in requirement,
            )
        )
    return tuple(entries)


def normalized_package_versions(path: Path) -> set[tuple[str, str]]:
    entries = parse_hash_lock(path.read_text(encoding="utf-8"))
    versions = {(entry.package, entry.version) for entry in entries}
    assert len(versions) == len(entries), f"duplicate lock entry in {path}"
    return versions


def direct_pin(path: Path, package: str) -> str:
    canonical = _canonical_package_name(package)
    matches = [
        version
        for raw_line in path.read_text(encoding="utf-8").splitlines()
        if (match := re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s#]+)", raw_line.strip()))
        and _canonical_package_name(match.group(1)) == canonical
        for version in [match.group(2)]
    ]
    assert matches == [matches[0]] if matches else False, f"missing or duplicate pin for {package}"
    return matches[0]


def normalized_locked_packages(*paths: Path) -> set[tuple[str, str]]:
    packages: set[tuple[str, str]] = set()
    for path in paths:
        packages.update(normalized_package_versions(path))
    return packages


def sbom_package_keys(path: Path) -> set[tuple[str, str]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    packages = document["packages"]
    return {(_canonical_package_name(item["name"]), item["versionInfo"]) for item in packages}


def load_licenses(path: Path) -> list[dict[str, object]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    components = document["components"]
    assert isinstance(components, list)
    assert all(isinstance(component, dict) for component in components)
    return components


def license_inventory_keys(path: Path) -> set[tuple[str, str]]:
    return {
        (_canonical_package_name(str(item["package"])), str(item["version"]))
        for item in load_licenses(path)
    }


def _supply_chain_module() -> Any:
    spec = importlib.util.spec_from_file_location("build_hf_space_supply_chain", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def exact_webkit_policy_dict() -> dict[str, object]:
    return {
        "package": "webkit",
        "version": "26.5",
        "artifact_sha256": ["c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c"],
        "reviewer_image_tag": "mcr.microsoft.com/playwright/python:v1.62.0-noble",
        "reviewer_index_digest": (
            "sha256:aa81288e738725378becba5b3e06cb0f3a7f012a610e87e8d767a090ea3f740d"
        ),
        "reviewer_linux_amd64_digest": (
            "sha256:51d31fdfacb0cff99a1a724152e34ae408d2bd4e7da310ff157450f49261cc59"
        ),
        "playwright_version": "1.62.0",
        "playwright_tag": "v1.62.0",
        "playwright_tag_url": "https://github.com/microsoft/playwright/tree/v1.62.0",
        "browsers_json_url": (
            "https://github.com/microsoft/playwright/blob/v1.62.0/"
            "packages/playwright-core/browsers.json"
        ),
        "registry_source_url": (
            "https://github.com/microsoft/playwright/blob/v1.62.0/"
            "packages/playwright-core/src/server/registry/index.ts"
        ),
        "cdn_artifact_url": (
            "https://cdn.playwright.dev/dbazure/download/playwright/builds/"
            "webkit/2336/webkit-ubuntu-24.04.zip"
        ),
        "playwright_tag_commit": "e3950d9c140d007bd52853b45813c6274b24e36f",
        "repository_relative_path": "browser_patches/webkit/UPSTREAM_CONFIG.sh",
        "commit_pinned_raw_url": (
            "https://raw.githubusercontent.com/microsoft/playwright/"
            "e3950d9c140d007bd52853b45813c6274b24e36f/"
            "browser_patches/webkit/UPSTREAM_CONFIG.sh"
        ),
        "raw_byte_length": 126,
        "raw_sha256": ("3554c5b666ed87032fb22e78956f8a2fffe1faede63ae8dcae60a26961f6419c"),
        "remote_url": "https://github.com/WebKit/WebKit.git",
        "base_branch": "main",
        "base_revision": "343e13bf22dca9d0ec227801419aab0f9001a32f",
        "webkit_revision": "2336",
        "webkit_version": "26.5",
        "webkit_tree_file_count": 38,
        "webkit_tree_total_bytes": 306401261,
        "webkit_tree_algorithm": "sha256-canonical-tree-v1",
        "webkit_tree_sha256": ("c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c"),
        "image_tree_source_relative_path_absence_proof": {
            "repository_relative_path": "browser_patches/webkit/UPSTREAM_CONFIG.sh",
            "canonical_tree_algorithm": "sha256-canonical-tree-v1",
            "canonical_tree_file_count": 38,
            "canonical_tree_total_bytes": 306401261,
            "canonical_tree_sha256": (
                "c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c"
            ),
            "present": False,
        },
        "official_webkit_licensing_references": [
            "https://webkit.org/licensing-webkit/",
            (
                "https://github.com/WebKit/WebKit/blob/"
                "343e13bf22dca9d0ec227801419aab0f9001a32f/"
                "Source/WebCore/LICENSE-APPLE"
            ),
            (
                "https://github.com/WebKit/WebKit/blob/"
                "343e13bf22dca9d0ec227801419aab0f9001a32f/"
                "Source/WebCore/LICENSE-LGPL-2"
            ),
        ],
        "licenseDeclared": "NOASSERTION",
        "licenseConcluded": "NOASSERTION",
        "review_disposition": "reviewer_test_only_not_redistributed",
        "complete_digest_bound_notice": False,
    }


SOURCE_REFERENCE_FIELDS = {
    "schema_version": 1,
    "phase": "controller_controlled_acquisition_complete",
    "network_permission": "exact_commit_pinned_https_get_once",
    "https_get_count": 1,
    "raw_body_retained": False,
    "playwright_tag": "v1.62.0",
    "playwright_tag_commit": "e3950d9c140d007bd52853b45813c6274b24e36f",
    "repository_relative_path": "browser_patches/webkit/UPSTREAM_CONFIG.sh",
    "commit_pinned_raw_url": (
        "https://raw.githubusercontent.com/microsoft/playwright/"
        "e3950d9c140d007bd52853b45813c6274b24e36f/"
        "browser_patches/webkit/UPSTREAM_CONFIG.sh"
    ),
    "raw_byte_length": 126,
    "raw_sha256": "3554c5b666ed87032fb22e78956f8a2fffe1faede63ae8dcae60a26961f6419c",
    "remote_url": "https://github.com/WebKit/WebKit.git",
    "base_branch": "main",
    "base_revision": "343e13bf22dca9d0ec227801419aab0f9001a32f",
}


def _source_reference_file(*, mutation: tuple[str, object] | None = None) -> tuple[Path, str]:
    run_guid = uuid.uuid4().hex
    root = Path(tempfile.gettempdir()).resolve() / f"carerisk-task7-{run_guid}"
    root.mkdir(mode=0o700)
    document = {"run_guid": run_guid, **SOURCE_REFERENCE_FIELDS}
    if mutation is not None:
        key, value = mutation
        if value is _MISSING:
            document.pop(key)
        else:
            document[key] = value
    path = root / "webkit-source-reference.json"
    path.write_text(
        json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path, run_guid


def _remove_source_reference(path: Path) -> None:
    path.unlink()
    path.parent.rmdir()


_MISSING = object()


def _ordinary_policy_record(package: str) -> dict[str, object]:
    return {
        "package": package,
        "version": "1.0",
        "artifact_sha256": ["a" * 64],
        "licenseDeclared": "MIT",
        "licenseConcluded": "MIT",
        "review_disposition": "approved",
        "complete_digest_bound_notice": True,
        "distribution_scope": "runtime_or_review_tooling",
        "license_evidence": ["https://pypi.org/project/example/1.0/"],
    }


def _policy_document(*records: dict[str, object]) -> dict[str, object]:
    return {"schema_version": 1, "components": [*records]}


WEBKIT_MUTATION_FIELDS = tuple(exact_webkit_policy_dict())[2:]
ORDINARY_COMPONENTS = (
    "ffmpeg",
    "gradio",
    "debian:libc6",
    "anyio",
)
AGGREGATE_CLAIM_CEILING = "aggregate_identity_and_notice_evidence_only_no_single_spdx_conclusion"
UNCERTAIN_AGGREGATE_COMPONENTS = {
    ("python-runtime-base", "3.11"): "runtime_distribution_not_license_approved",
    ("playwright-reviewer-base", "1.62.0"): "reviewer_test_only_not_redistributed",
    ("chromium", "pinned"): "reviewer_test_only_not_redistributed",
    ("firefox", "pinned"): "reviewer_test_only_not_redistributed",
}
REVIEWER_BYTE_SIGNATURES = (
    "sha256:51d31fdfacb0cff99a1a724152e34ae408d2bd4e7da310ff157450f49261cc59",
    "/ms-playwright",
    "c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c",
    "65e91099ff94fb6aa3dc2b5a5216975c38749e5e25ce4f28587a97acf50ce6f7",
    "b9ac23dff6e2cb4421f56d20279618ce615a6bc3de774f0fcbfa7f117da5234f",
    "ffmpeg-1011",
)


@pytest.mark.parametrize("field", WEBKIT_MUTATION_FIELDS)
def test_exact_webkit_reviewer_exception_rejects_every_single_field_drift(
    field: str,
) -> None:
    module = _supply_chain_module()
    exact = exact_webkit_policy_dict()
    mutated = json.loads(json.dumps(exact))
    value = mutated[field]
    if isinstance(value, bool):
        mutated[field] = not value
    elif isinstance(value, list):
        mutated[field] = [*value, "https://example.invalid/not-exact"]
    else:
        mutated[field] = f"{value}-drift"

    with pytest.raises(ValueError, match="exact reviewer-only WebKit"):
        module.validate_license_policy(_policy_document(mutated))


@pytest.mark.parametrize(
    "mutation",
    (
        "missing_key",
        "extra_key",
        "alternate_reference_order",
        "alternate_case",
        "integer_revision",
        "truthy_notice",
        "guessed_declared_license",
        "guessed_concluded_license",
        "approved_disposition",
        "notice_true",
    ),
)
def test_exact_webkit_reviewer_exception_rejects_structural_drift(
    mutation: str,
) -> None:
    module = _supply_chain_module()
    record = exact_webkit_policy_dict()
    if mutation == "missing_key":
        record.pop("playwright_tag_url")
    elif mutation == "extra_key":
        record["unreviewed_claim"] = "present"
    elif mutation == "alternate_reference_order":
        references = record["official_webkit_licensing_references"]
        assert isinstance(references, list)
        record["official_webkit_licensing_references"] = list(reversed(references))
    elif mutation == "alternate_case":
        record["package"] = "WebKit"
    elif mutation == "integer_revision":
        record["webkit_revision"] = 2336
    elif mutation == "truthy_notice":
        record["complete_digest_bound_notice"] = "false"
    elif mutation == "guessed_declared_license":
        record["licenseDeclared"] = "BSD-2-Clause AND LGPL-2.1-only"
    elif mutation == "guessed_concluded_license":
        record["licenseConcluded"] = "BSD-2-Clause AND LGPL-2.1-only"
    elif mutation == "approved_disposition":
        record["review_disposition"] = "approved"
    elif mutation == "notice_true":
        record["complete_digest_bound_notice"] = True
    else:  # pragma: no cover - protects the mutation registry itself
        raise AssertionError(f"unknown test mutation: {mutation}")

    with pytest.raises(ValueError, match="exact reviewer-only WebKit"):
        module.validate_license_policy(_policy_document(record))


@pytest.mark.parametrize(
    "field",
    (
        "repository_relative_path",
        "canonical_tree_algorithm",
        "canonical_tree_file_count",
        "canonical_tree_total_bytes",
        "canonical_tree_sha256",
        "present",
    ),
)
def test_exact_webkit_reviewer_exception_rejects_each_absence_proof_drift(
    field: str,
) -> None:
    module = _supply_chain_module()
    record = exact_webkit_policy_dict()
    proof = record["image_tree_source_relative_path_absence_proof"]
    assert isinstance(proof, dict)
    value = proof[field]
    proof[field] = not value if isinstance(value, bool) else f"{value}-drift"

    with pytest.raises(ValueError, match="exact reviewer-only WebKit"):
        module.validate_license_policy(_policy_document(record))


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("playwright_tag_commit", "0" * 40),
        ("repository_relative_path", "UPSTREAM_CONFIG.sh"),
        ("commit_pinned_raw_url", "https://example.invalid/source"),
        ("raw_byte_length", 125),
        ("raw_sha256", "0" * 64),
        ("remote_url", "https://example.invalid/WebKit.git"),
        ("base_branch", "trunk"),
        ("base_revision", "0" * 40),
        ("phase", "offline_verify"),
        ("network_permission", "unbounded"),
        ("https_get_count", 2),
        ("raw_body_retained", True),
        ("playwright_tag", "v1.61.0"),
        ("schema_version", 2),
        ("playwright_tag_commit", _MISSING),
    ),
)
def test_source_reference_phase_contract_rejects_every_metadata_drift(
    field: str, value: object
) -> None:
    module = _supply_chain_module()
    path, run_guid = _source_reference_file(mutation=(field, value))
    try:
        with pytest.raises(ValueError, match="source reference phase contract"):
            module.load_webkit_source_reference(
                path,
                run_guid=run_guid,
                phase="offline_verify",
                offline=True,
                network_bomb=True,
            )
    finally:
        _remove_source_reference(path)


@pytest.mark.parametrize(
    "mutation",
    ("wrong_guid", "wrong_name", "alternate_path", "offline_false", "network_bomb_false"),
)
def test_source_reference_phase_contract_rejects_every_control_mutation(
    mutation: str,
) -> None:
    module = _supply_chain_module()
    path, run_guid = _source_reference_file()
    alternate: Path | None = None
    try:
        candidate = path
        supplied_guid = run_guid
        offline = True
        network_bomb = True
        if mutation == "wrong_guid":
            supplied_guid = "0" * 32
        elif mutation == "wrong_name":
            candidate = path.with_name("alternate.json")
            path.rename(candidate)
            path = candidate
        elif mutation == "alternate_path":
            alternate = path.parent / "webkit-source-reference-copy.json"
            alternate.write_bytes(path.read_bytes())
            candidate = alternate
        elif mutation == "offline_false":
            offline = False
        elif mutation == "network_bomb_false":
            network_bomb = False
        else:  # pragma: no cover
            raise AssertionError(mutation)
        with pytest.raises(ValueError, match="source reference phase contract"):
            module.load_webkit_source_reference(
                candidate,
                run_guid=supplied_guid,
                phase="offline_verify",
                offline=offline,
                network_bomb=network_bomb,
            )
    finally:
        if alternate is not None and alternate.exists():
            alternate.unlink()
        _remove_source_reference(path)


def test_webkit_source_relative_file_is_absent_from_immutable_image_tree() -> None:
    module = _supply_chain_module()
    path, run_guid = _source_reference_file()
    try:
        source_reference = module.load_webkit_source_reference(
            path,
            run_guid=run_guid,
            phase="offline_verify",
            offline=True,
            network_bomb=True,
        )
        module.verify_image_record(
            BASE_IMAGE,
            source_reference=source_reference,
            offline=True,
            network_bomb=True,
        )
    finally:
        _remove_source_reference(path)


def test_offline_test_installs_network_bomb_before_argv() -> None:
    module = _supply_chain_module()
    path, run_guid = _source_reference_file()
    events: list[str] = []
    try:
        result = module.run_network_bombed_child(
            source_reference=path,
            run_guid=run_guid,
            phase="offline_verify",
            offline=True,
            network_bomb=True,
            argv=(sys.executable, "-c", CHILD_NETWORK_BOMB_PROBE_CODE),
            event_sink=events.append,
        )
        assert result == 0
        assert events == ["load_reference", "install_network_bomb", "spawn_child"]
    finally:
        _remove_source_reference(path)


def test_offline_test_child_enforces_socket_and_urllib_network_bomb() -> None:
    module = _supply_chain_module()
    path, run_guid = _source_reference_file()
    try:
        result = module.run_network_bombed_child(
            source_reference=path,
            run_guid=run_guid,
            phase="offline_verify",
            offline=True,
            network_bomb=True,
            argv=(sys.executable, "-c", CHILD_NETWORK_BOMB_PROBE_CODE),
            event_sink=lambda _event: None,
        )
        assert result == 0
    finally:
        _remove_source_reference(path)


@pytest.mark.parametrize(
    "argv",
    (
        ("definitely-not-python", "-c", "raise SystemExit(0)"),
        (sys.executable, "-Iu", "-c", "raise SystemExit(0)"),
        (sys.executable, "-Es", "-c", "raise SystemExit(0)"),
        (sys.executable, "-Ss", "-c", "raise SystemExit(0)"),
        (sys.executable, "-Is", "-c", "raise SystemExit(0)"),
        (sys.executable, "-E", "-c", "raise SystemExit(0)"),
        (sys.executable, "-s", "-c", "raise SystemExit(0)"),
        (sys.executable, "-S", "-c", "raise SystemExit(0)"),
        (sys.executable, "-I", "-c", "raise SystemExit(0)"),
    ),
)
def test_offline_child_argv_is_deny_by_default(argv: tuple[str, ...]) -> None:
    module = _supply_chain_module()
    path, run_guid = _source_reference_file()
    try:
        with pytest.raises(ValueError, match="offline child argv not allowlisted"):
            module.run_network_bombed_child(
                source_reference=path,
                run_guid=run_guid,
                phase="offline_verify",
                offline=True,
                network_bomb=True,
                argv=argv,
                event_sink=lambda _event: None,
            )
    finally:
        _remove_source_reference(path)


def test_acquisition_commands_are_not_available_in_offline_cli() -> None:
    module = _supply_chain_module()
    parser = module.build_parser()
    for command in ("lock", "resolve-images", "acquire-wheels"):
        with pytest.raises(SystemExit):
            parser.parse_args([command])


@pytest.mark.parametrize("package", ORDINARY_COMPONENTS)
def test_noassertion_fails_for_public_or_any_other_component(package: str) -> None:
    module = _supply_chain_module()
    record = _ordinary_policy_record(package)
    record["licenseDeclared"] = "NOASSERTION"
    record["licenseConcluded"] = "NOASSERTION"

    with pytest.raises(ValueError, match="NOASSERTION outside exact reviewer-only WebKit"):
        module.validate_license_policy(_policy_document(record))


def _closed_distribution_surfaces(module: Any) -> list[Any]:
    return [
        module.DistributionSurface(
            name=name,
            paths=(f"approved/{name}.txt",),
            layer_digests=(),
            content_sha256=(),
            command_tokens=(),
        )
        for name in module.DISTRIBUTION_SURFACE_NAMES
    ]


@pytest.mark.parametrize(
    "surface_name",
    (
        "public_export",
        "candidate",
        "runtime_stage",
        "final_image",
        "deployment_artifact",
        "saved_archive",
        "pushed_image",
        "uploaded_artifact",
        "published_image",
        "build_output",
        "other_distributed_output",
    ),
)
@pytest.mark.parametrize("signature", REVIEWER_BYTE_SIGNATURES)
def test_reviewer_or_browser_bytes_fail_every_distribution_surface(
    surface_name: str,
    signature: str,
) -> None:
    module = _supply_chain_module()
    surfaces = _closed_distribution_surfaces(module)
    index = module.DISTRIBUTION_SURFACE_NAMES.index(surface_name)
    surfaces[index] = module.DistributionSurface(
        name=surface_name,
        paths=(signature,),
        layer_digests=(),
        content_sha256=(),
        command_tokens=(),
    )

    with pytest.raises(ValueError, match="reviewer/browser bytes"):
        module.validate_distribution_exclusion(surfaces)


@pytest.mark.parametrize(
    "mutation",
    ("omitted", "duplicate", "unknown", "empty", "unclassified"),
)
def test_distribution_surface_registry_is_closed_and_complete(mutation: str) -> None:
    module = _supply_chain_module()
    surfaces = _closed_distribution_surfaces(module)
    if mutation == "omitted":
        surfaces.pop()
    elif mutation == "duplicate":
        surfaces.append(surfaces[-1])
    elif mutation == "unknown":
        surfaces[-1] = module.DistributionSurface(
            name="future_unclassified_output",
            paths=("approved/unknown.txt",),
            layer_digests=(),
            content_sha256=(),
            command_tokens=(),
        )
    elif mutation == "empty":
        surfaces.clear()
    elif mutation == "unclassified":
        surfaces[-1] = module.DistributionSurface(
            name=module.DISTRIBUTION_SURFACE_NAMES[-1],
            paths=(),
            layer_digests=(),
            content_sha256=(),
            command_tokens=(),
        )
    else:  # pragma: no cover - protects the mutation registry itself
        raise AssertionError(f"unknown test mutation: {mutation}")

    with pytest.raises(ValueError, match="distribution surface registry"):
        module.validate_distribution_exclusion(surfaces)


def test_locks_are_complete_exact_and_hashed() -> None:
    for path in (RUNTIME_LOCK, DEVELOPMENT_LOCK):
        entries = parse_hash_lock(path.read_text(encoding="utf-8"))
        assert entries
        assert all(entry.version_operator == "==" for entry in entries)
        assert all(entry.sha256_hashes for entry in entries)
        assert not any(entry.editable or entry.url_without_hash for entry in entries)

    runtime = normalized_package_versions(RUNTIME_LOCK)
    development = normalized_package_versions(DEVELOPMENT_LOCK)
    assert runtime <= development
    assert direct_pin(RUNTIME_INPUT, "gradio") == "6.26.0"
    assert direct_pin(DEVELOPMENT_INPUT, "gradio") == "6.26.0"
    assert ("gradio", "6.26.0") in runtime
    assert ("gradio", "6.26.0") in development


def test_both_base_images_are_patch_tagged_digest_pinned_and_compatible() -> None:
    bases = json.loads(BASE_IMAGE.read_text(encoding="utf-8"))["images"]
    runtime, reviewer = bases["runtime"], bases["reviewer"]

    assert re.fullmatch(r"python:3\.11\.\d+-slim-bookworm", runtime["tag"])
    assert re.fullmatch(
        r"mcr\.microsoft\.com/playwright/python:v\d+\.\d+\.\d+-(jammy|noble)",
        reviewer["tag"],
    )
    assert reviewer["playwright_python_version"] == direct_pin(DEVELOPMENT_INPUT, "playwright")
    assert set(reviewer["embedded_browsers"]) == {"chromium", "firefox", "webkit"}
    for base in (runtime, reviewer):
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", base["index_digest"])
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", base["linux_amd64_digest"])
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", base["system_inventory_sha256"])


def test_reviewer_base_component_uses_exact_playwright_version() -> None:
    records = {
        (_canonical_package_name(str(item["package"])), str(item["version"])): item
        for item in load_licenses(LICENSES)
    }
    assert ("playwright-reviewer-base", "1.62.0") in records
    assert ("playwright-reviewer-base", "6.26.0") not in records


def test_ffmpeg_has_no_fabricated_content_checksum() -> None:
    records = {
        (_canonical_package_name(str(item["package"])), str(item["version"])): item
        for item in load_licenses(LICENSES)
    }
    ffmpeg = records[("ffmpeg", "pinned")]
    exact_tree_sha256 = "1514c84470c5a5706b48eea2ce282c290ccdb508a46196c24c82b6b91ffc287a"
    assert ffmpeg["artifact_sha256"] == [exact_tree_sha256]
    assert ffmpeg["license_evidence"] == {
        "content_identity": {
            "algorithm": "sha256-canonical-tree-v1",
            "byte_count": 5127582,
            "file_count": 4,
            "sha256": exact_tree_sha256,
        },
        "embedded_support": ["ffmpeg-1011"],
        "notice_files": [
            {
                "path": "/ms-playwright/ffmpeg-1011/COPYING.LGPLv2.1",
                "sha256": "b634ab5640e258563c536e658cad87080553df6f34f62269a21d554844e58bfe",
                "size": 26526,
            }
        ],
        "revision": "1011",
        "review_basis": "exact_reviewer_image_subtree_and_notice",
    }
    sbom = json.loads(SBOM.read_text(encoding="utf-8"))
    [package] = [item for item in sbom["packages"] if item["name"] == "ffmpeg"]
    assert package["checksums"] == [{"algorithm": "SHA256", "checksumValue": exact_tree_sha256}]


def test_policy_uses_extracted_wheel_and_image_evidence_not_placeholders() -> None:
    policy = json.loads(LICENSE_POLICY.read_text(encoding="utf-8"))
    records = {
        (_canonical_package_name(str(item["package"])), str(item["version"])): item
        for item in policy["components"]
    }
    locked = normalized_locked_packages(RUNTIME_LOCK, DEVELOPMENT_LOCK)
    for key in locked:
        record = records[key]
        assert record["licenseDeclared"] == record["licenseConcluded"]
        assert not str(record["licenseDeclared"]).startswith("LicenseRef-Hash-Locked")
        assert not str(record["licenseDeclared"]).startswith("LicenseRef-Wheel-")
        evidence = record["license_evidence"]
        assert isinstance(evidence, dict)
        assert evidence["review_basis"] == "exact_locked_wheel_metadata_and_notices"
        assert set(evidence) == {
            "license_classifiers",
            "license_files",
            "metadata_license",
            "metadata_license_expression",
            "review_basis",
        }
        lock_hashes = {
            digest
            for lock in (RUNTIME_LOCK, DEVELOPMENT_LOCK)
            for entry in parse_hash_lock(lock.read_text(encoding="utf-8"))
            if (entry.package, entry.version) == key
            for digest in entry.sha256_hashes
        }
        assert set(record["artifact_sha256"]) == lock_hashes

    for key in (
        ("python-runtime-base", "3.11"),
        ("playwright-reviewer-base", "1.62.0"),
        ("chromium", "pinned"),
        ("firefox", "pinned"),
    ):
        evidence = records[key]["license_evidence"]
        assert isinstance(evidence, dict)
        assert evidence["review_basis"].startswith("exact_")
        assert evidence["claim_ceiling"] == AGGREGATE_CLAIM_CEILING


def test_uncertain_aggregate_components_are_not_reported_as_license_approved() -> None:
    policy_records = {
        (_canonical_package_name(str(item["package"])), str(item["version"])): item
        for item in json.loads(LICENSE_POLICY.read_text(encoding="utf-8"))["components"]
    }
    inventory_records = {
        (_canonical_package_name(str(item["package"])), str(item["version"])): item
        for item in load_licenses(LICENSES)
    }
    sbom_records = {
        (_canonical_package_name(str(item["name"])), str(item["versionInfo"])): item
        for item in json.loads(SBOM.read_text(encoding="utf-8"))["packages"]
    }
    for key, disposition in UNCERTAIN_AGGREGATE_COMPONENTS.items():
        for records in (policy_records, inventory_records):
            record = records[key]
            assert record["licenseDeclared"] == "NOASSERTION"
            assert record["licenseConcluded"] == "NOASSERTION"
            assert record["review_disposition"] == disposition
            evidence = record["license_evidence"]
            assert isinstance(evidence, dict)
            assert evidence["claim_ceiling"] == AGGREGATE_CLAIM_CEILING
        assert sbom_records[key]["licenseDeclared"] == "NOASSERTION"
        assert sbom_records[key]["licenseConcluded"] == "NOASSERTION"


def test_static_license_trust_root_is_exact_artifact_indexed() -> None:
    root = json.loads(LICENSE_TRUST_ROOT.read_text(encoding="utf-8"))
    assert root["schema_version"] == 1
    entries = root["components"]
    identities = [
        (
            _canonical_package_name(str(item["package"])),
            str(item["version"]),
            tuple(item["artifact_sha256"]),
        )
        for item in entries
    ]
    assert identities == sorted(identities)
    assert len(identities) == len(set(identities))
    assert all(
        all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in hashes)
        for _name, _version, hashes in identities
    )
    expected = license_inventory_keys(LICENSES) | {("carerisk-space", "0.2.0")}
    assert {(name, version) for name, version, _hashes in identities} == expected


def test_webkit_absence_proof_is_recomputed_from_ordered_tree_inventory() -> None:
    module = _supply_chain_module()
    base = json.loads(BASE_IMAGE.read_text(encoding="utf-8"))
    webkit = base["images"]["reviewer"]["embedded_browsers"]["webkit"]
    inventory = webkit["ordered_tree_inventory"]
    assert isinstance(inventory, list) and inventory
    assert [entry["path"] for entry in inventory] == sorted(entry["path"] for entry in inventory)
    assert sum(entry["size"] for entry in inventory if entry["type"] == "F") == 306401261
    assert sum(entry["type"] == "F" for entry in inventory) == 38
    proof = module.derive_webkit_absence_proof(
        webkit,
        source_relative_path="browser_patches/webkit/UPSTREAM_CONFIG.sh",
    )
    assert proof == webkit["image_tree_source_relative_path_absence_proof"]
    mutated = json.loads(json.dumps(webkit))
    mutated["ordered_tree_inventory"].append(
        {
            "mode": "0644",
            "path": "browser_patches/webkit/UPSTREAM_CONFIG.sh",
            "payload_sha256": "0" * 64,
            "size": 0,
            "type": "F",
        }
    )
    mutated["ordered_tree_inventory"].sort(key=lambda item: item["path"])
    assert (
        module.derive_webkit_absence_proof(
            mutated,
            source_relative_path="browser_patches/webkit/UPSTREAM_CONFIG.sh",
        )["present"]
        is True
    )


def test_sbom_and_license_inventory_cover_every_lock_package_once() -> None:
    locked = normalized_locked_packages(RUNTIME_LOCK, DEVELOPMENT_LOCK)
    image_components = {
        ("carerisk-space", "0.2.0"),
        ("python-runtime-base", "3.11"),
        ("playwright-reviewer-base", "1.62.0"),
        ("chromium", "pinned"),
        ("firefox", "pinned"),
        ("webkit", "26.5"),
        ("ffmpeg", "pinned"),
    }

    assert sbom_package_keys(SBOM) == locked | image_components
    assert license_inventory_keys(LICENSES) == locked | (
        image_components - {("carerisk-space", "0.2.0")}
    )
    records = {
        (_canonical_package_name(str(item["package"])), str(item["version"])): item
        for item in load_licenses(LICENSES)
    }
    assert records[("webkit", "26.5")] == exact_webkit_policy_dict()
    assert records[("webkit", "26.5")]["licenseDeclared"] == "NOASSERTION"
    assert records[("webkit", "26.5")]["licenseConcluded"] == "NOASSERTION"
    assert (
        records[("webkit", "26.5")]["review_disposition"] == "reviewer_test_only_not_redistributed"
    )
    assert records[("webkit", "26.5")]["complete_digest_bound_notice"] is False
    assert all(
        item["review_disposition"] == "approved"
        and item["licenseDeclared"] != "NOASSERTION"
        and item["licenseConcluded"] != "NOASSERTION"
        for key, item in records.items()
        if key != ("webkit", "26.5") and key not in UNCERTAIN_AGGREGATE_COMPONENTS
    )


def _copy_supply_chain_tree(destination_root: Path) -> None:
    for relative in (
        "tools/space/requirements-runtime.in",
        "tools/space/requirements-dev.in",
        "tools/space/lock-tooling.txt",
        "tools/space/base-image.json",
        "tools/space/license-policy.json",
        "tools/space/license-trust-root.json",
        "space/requirements.lock",
        "space/requirements-dev.lock",
        "space/SBOM.spdx.json",
        "space/THIRD_PARTY_LICENSES.json",
    ):
        destination = destination_root / relative
        if not (ROOT / relative).exists() and relative == "tools/space/license-trust-root.json":
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)


def _write_canonical_json(path: Path, document: object) -> None:
    path.write_text(
        json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _tamper_gradio_license(path: Path, surface: str) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    records = document["packages"] if surface == "sbom" else document["components"]
    name_key = "name" if surface == "sbom" else "package"
    [record] = [item for item in records if item[name_key] == "gradio"]
    record["licenseDeclared"] = "MIT"
    record["licenseConcluded"] = "MIT"
    if surface == "sbom":
        package_bytes = (
            json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode()
        document["documentNamespace"] = (
            "https://github.com/kuotunyu/CareRisk-48H/spdx/"
            + hashlib.sha256(package_bytes).hexdigest()
        )
    _write_canonical_json(path, document)


@pytest.mark.parametrize("surface", ("policy", "inventory", "sbom"))
def test_each_license_output_is_validated_independently_against_trust_root(
    tmp_path: Path, surface: str
) -> None:
    module = _supply_chain_module()
    _copy_supply_chain_tree(tmp_path)
    paths = {
        "policy": tmp_path / "tools/space/license-policy.json",
        "inventory": tmp_path / "space/THIRD_PARTY_LICENSES.json",
        "sbom": tmp_path / "space/SBOM.spdx.json",
    }
    _tamper_gradio_license(paths[surface], surface)
    path, run_guid = _source_reference_file()
    try:
        source_reference = module.load_webkit_source_reference(
            path,
            run_guid=run_guid,
            phase="offline_verify",
            offline=True,
            network_bomb=True,
        )
        with pytest.raises(ValueError, match="license trust root"):
            module.verify_all(
                tmp_path,
                source_reference=source_reference,
                offline=True,
                network_bomb=True,
            )
    finally:
        _remove_source_reference(path)


def test_coherent_tampering_of_all_three_license_outputs_fails(
    tmp_path: Path,
) -> None:
    module = _supply_chain_module()
    _copy_supply_chain_tree(tmp_path)
    for surface, relative in (
        ("policy", "tools/space/license-policy.json"),
        ("inventory", "space/THIRD_PARTY_LICENSES.json"),
        ("sbom", "space/SBOM.spdx.json"),
    ):
        _tamper_gradio_license(tmp_path / relative, surface)
    path, run_guid = _source_reference_file()
    try:
        source_reference = module.load_webkit_source_reference(
            path,
            run_guid=run_guid,
            phase="offline_verify",
            offline=True,
            network_bomb=True,
        )
        with pytest.raises(ValueError, match="license trust root"):
            module.verify_all(
                tmp_path,
                source_reference=source_reference,
                offline=True,
                network_bomb=True,
            )
    finally:
        _remove_source_reference(path)


def test_verify_all_accepts_the_committed_supply_chain_outputs() -> None:
    module = _supply_chain_module()
    path, run_guid = _source_reference_file()
    try:
        source_reference = module.load_webkit_source_reference(
            path,
            run_guid=run_guid,
            phase="offline_verify",
            offline=True,
            network_bomb=True,
        )
        module.verify_all(
            ROOT,
            source_reference=source_reference,
            offline=True,
            network_bomb=True,
        )
        assert LICENSE_POLICY.is_file()
    finally:
        _remove_source_reference(path)


@pytest.mark.parametrize(
    "mutation",
    ("spdx_id", "license", "download", "checksum", "relationships"),
)
def test_verify_all_rejects_each_ordinary_spdx_projection_drift(
    tmp_path: Path, mutation: str
) -> None:
    module = _supply_chain_module()
    for relative in (
        "tools/space/requirements-runtime.in",
        "tools/space/requirements-dev.in",
        "tools/space/lock-tooling.txt",
        "tools/space/base-image.json",
        "tools/space/license-policy.json",
        "tools/space/license-trust-root.json",
        "space/requirements.lock",
        "space/requirements-dev.lock",
        "space/SBOM.spdx.json",
        "space/THIRD_PARTY_LICENSES.json",
    ):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)

    sbom_path = tmp_path / "space/SBOM.spdx.json"
    sbom = json.loads(sbom_path.read_text(encoding="utf-8"))
    [ordinary] = [item for item in sbom["packages"] if item["name"] == "gradio"]
    if mutation == "spdx_id":
        ordinary["SPDXID"] += "-drift"
    elif mutation == "license":
        ordinary["licenseConcluded"] = "LicenseRef-Deliberate-Test-Drift"
    elif mutation == "download":
        ordinary["downloadLocation"] = "https://example.invalid/drift"
    elif mutation == "checksum":
        ordinary["checksums"][0]["checksumValue"] = "0" * 64
    elif mutation == "relationships":
        sbom["relationships"].pop()
    else:  # pragma: no cover
        raise AssertionError(mutation)
    sbom_path.write_text(
        json.dumps(sbom, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    path, run_guid = _source_reference_file()
    try:
        source_reference = module.load_webkit_source_reference(
            path,
            run_guid=run_guid,
            phase="offline_verify",
            offline=True,
            network_bomb=True,
        )
        with pytest.raises(ValueError, match="SPDX .* drift"):
            module.verify_all(
                tmp_path,
                source_reference=source_reference,
                offline=True,
                network_bomb=True,
            )
    finally:
        _remove_source_reference(path)
