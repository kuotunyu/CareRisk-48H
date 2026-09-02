"""Build deterministic HF Space locks, OCI inventories, licenses, and SPDX SBOM."""
# ruff: noqa: E501

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

RUNTIME_TAG = "3.11.14-slim-bookworm"
REVIEWER_TAG = "v1.62.0-noble"
PLAYWRIGHT_VERSION = "1.62.0"
OFFICIAL_PYPI = "https://pypi.org/simple"
OCI_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
DIRECT_PIN = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s#]+)$")
LOCK_REQUIREMENT = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s;]+)(.*)$")
IMAGE_COMPONENTS = {
    ("python-runtime-base", "3.11"),
    ("playwright-reviewer-base", "1.62.0"),
    ("chromium", "pinned"),
    ("firefox", "pinned"),
    ("webkit", "26.5"),
    ("ffmpeg", "pinned"),
}
AGGREGATE_CLAIM_CEILING = "aggregate_identity_and_notice_evidence_only_no_single_spdx_conclusion"
UNCERTAIN_AGGREGATE_DISPOSITIONS = {
    ("python-runtime-base", "3.11"): "runtime_distribution_not_license_approved",
    ("playwright-reviewer-base", "1.62.0"): "reviewer_test_only_not_redistributed",
    ("chromium", "pinned"): "reviewer_test_only_not_redistributed",
    ("firefox", "pinned"): "reviewer_test_only_not_redistributed",
}

DISTRIBUTION_SURFACE_NAMES = (
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
)

SOURCE_REFERENCE_VALUES: dict[str, object] = {
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
OFFLINE_CHILD_PYTEST_ARGUMENTS = (
    "-m",
    "pytest",
    "tests/test_hf_space_supply_chain.py",
    "-q",
)
OFFLINE_CHILD_NETWORK_BOMB_PROBE_CODE = """\
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
class WebKitSourceReference:
    playwright_tag_commit: str
    repository_relative_path: str
    commit_pinned_raw_url: str
    raw_byte_length: int
    raw_sha256: str
    remote_url: str
    base_branch: str
    base_revision: str


@dataclass(frozen=True)
class WebKitReviewerPolicy:
    reviewer_image_tag: str
    reviewer_index_digest: str
    reviewer_linux_amd64_digest: str
    playwright_version: str
    playwright_tag: str
    playwright_tag_url: str
    browsers_json_url: str
    registry_source_url: str
    cdn_artifact_url: str
    playwright_tag_commit: str
    repository_relative_path: str
    commit_pinned_raw_url: str
    raw_byte_length: int
    raw_sha256: str
    remote_url: str
    base_branch: str
    base_revision: str
    webkit_revision: str
    webkit_version: str
    webkit_tree_file_count: int
    webkit_tree_total_bytes: int
    webkit_tree_algorithm: str
    webkit_tree_sha256: str
    image_tree_source_relative_path_absence_proof: Mapping[str, object]
    official_webkit_licensing_references: tuple[str, ...]
    license_declared: str
    license_concluded: str
    review_disposition: str
    complete_digest_bound_notice: bool


@dataclass(frozen=True)
class DistributionSurface:
    name: str
    paths: tuple[str, ...]
    layer_digests: tuple[str, ...]
    content_sha256: tuple[str, ...]
    command_tokens: tuple[str, ...]


def canonical_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(value))


def exact_webkit_reviewer_policy() -> WebKitReviewerPolicy:
    tree_sha = "c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c"
    return WebKitReviewerPolicy(
        reviewer_image_tag="mcr.microsoft.com/playwright/python:v1.62.0-noble",
        reviewer_index_digest=(
            "sha256:aa81288e738725378becba5b3e06cb0f3a7f012a610e87e8d767a090ea3f740d"
        ),
        reviewer_linux_amd64_digest=(
            "sha256:51d31fdfacb0cff99a1a724152e34ae408d2bd4e7da310ff157450f49261cc59"
        ),
        playwright_version="1.62.0",
        playwright_tag="v1.62.0",
        playwright_tag_url="https://github.com/microsoft/playwright/tree/v1.62.0",
        browsers_json_url=(
            "https://github.com/microsoft/playwright/blob/v1.62.0/"
            "packages/playwright-core/browsers.json"
        ),
        registry_source_url=(
            "https://github.com/microsoft/playwright/blob/v1.62.0/"
            "packages/playwright-core/src/server/registry/index.ts"
        ),
        cdn_artifact_url=(
            "https://cdn.playwright.dev/dbazure/download/playwright/builds/"
            "webkit/2336/webkit-ubuntu-24.04.zip"
        ),
        playwright_tag_commit=str(SOURCE_REFERENCE_VALUES["playwright_tag_commit"]),
        repository_relative_path=str(SOURCE_REFERENCE_VALUES["repository_relative_path"]),
        commit_pinned_raw_url=str(SOURCE_REFERENCE_VALUES["commit_pinned_raw_url"]),
        raw_byte_length=126,
        raw_sha256=str(SOURCE_REFERENCE_VALUES["raw_sha256"]),
        remote_url=str(SOURCE_REFERENCE_VALUES["remote_url"]),
        base_branch=str(SOURCE_REFERENCE_VALUES["base_branch"]),
        base_revision=str(SOURCE_REFERENCE_VALUES["base_revision"]),
        webkit_revision="2336",
        webkit_version="26.5",
        webkit_tree_file_count=38,
        webkit_tree_total_bytes=306401261,
        webkit_tree_algorithm="sha256-canonical-tree-v1",
        webkit_tree_sha256=tree_sha,
        image_tree_source_relative_path_absence_proof={
            "repository_relative_path": str(SOURCE_REFERENCE_VALUES["repository_relative_path"]),
            "canonical_tree_algorithm": "sha256-canonical-tree-v1",
            "canonical_tree_file_count": 38,
            "canonical_tree_total_bytes": 306401261,
            "canonical_tree_sha256": tree_sha,
            "present": False,
        },
        official_webkit_licensing_references=(
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
        ),
        license_declared="NOASSERTION",
        license_concluded="NOASSERTION",
        review_disposition="reviewer_test_only_not_redistributed",
        complete_digest_bound_notice=False,
    )


def exact_webkit_policy_record() -> dict[str, object]:
    policy = exact_webkit_reviewer_policy()
    return {
        "package": "webkit",
        "version": policy.webkit_version,
        "artifact_sha256": [policy.webkit_tree_sha256],
        "reviewer_image_tag": policy.reviewer_image_tag,
        "reviewer_index_digest": policy.reviewer_index_digest,
        "reviewer_linux_amd64_digest": policy.reviewer_linux_amd64_digest,
        "playwright_version": policy.playwright_version,
        "playwright_tag": policy.playwright_tag,
        "playwright_tag_url": policy.playwright_tag_url,
        "browsers_json_url": policy.browsers_json_url,
        "registry_source_url": policy.registry_source_url,
        "cdn_artifact_url": policy.cdn_artifact_url,
        "playwright_tag_commit": policy.playwright_tag_commit,
        "repository_relative_path": policy.repository_relative_path,
        "commit_pinned_raw_url": policy.commit_pinned_raw_url,
        "raw_byte_length": policy.raw_byte_length,
        "raw_sha256": policy.raw_sha256,
        "remote_url": policy.remote_url,
        "base_branch": policy.base_branch,
        "base_revision": policy.base_revision,
        "webkit_revision": policy.webkit_revision,
        "webkit_version": policy.webkit_version,
        "webkit_tree_file_count": policy.webkit_tree_file_count,
        "webkit_tree_total_bytes": policy.webkit_tree_total_bytes,
        "webkit_tree_algorithm": policy.webkit_tree_algorithm,
        "webkit_tree_sha256": policy.webkit_tree_sha256,
        "image_tree_source_relative_path_absence_proof": dict(
            policy.image_tree_source_relative_path_absence_proof
        ),
        "official_webkit_licensing_references": list(policy.official_webkit_licensing_references),
        "licenseDeclared": policy.license_declared,
        "licenseConcluded": policy.license_concluded,
        "review_disposition": policy.review_disposition,
        "complete_digest_bound_notice": policy.complete_digest_bound_notice,
    }


def load_webkit_source_reference(
    path: Path,
    *,
    run_guid: str,
    phase: Literal["offline_verify"],
    offline: Literal[True],
    network_bomb: Literal[True],
) -> WebKitSourceReference:
    try:
        resolved = path.resolve(strict=True)
        os_temp = Path(tempfile.gettempdir()).resolve(strict=True)
        parent = resolved.parent
        if (
            phase != "offline_verify"
            or offline is not True
            or network_bomb is not True
            or not re.fullmatch(r"[0-9a-f]{32}", run_guid)
            or resolved.name != "webkit-source-reference.json"
            or parent.name != f"carerisk-task7-{run_guid}"
            or parent.parent != os_temp
            or path.is_symlink()
            or parent.is_symlink()
            or not resolved.is_file()
        ):
            raise ValueError("source reference phase contract")
        document = load_json(resolved)
        expected = {"run_guid": run_guid, **SOURCE_REFERENCE_VALUES}
        if document != expected:
            raise ValueError("source reference phase contract")
        return WebKitSourceReference(
            playwright_tag_commit=str(document["playwright_tag_commit"]),
            repository_relative_path=str(document["repository_relative_path"]),
            commit_pinned_raw_url=str(document["commit_pinned_raw_url"]),
            raw_byte_length=int(document["raw_byte_length"]),
            raw_sha256=str(document["raw_sha256"]),
            remote_url=str(document["remote_url"]),
            base_branch=str(document["base_branch"]),
            base_revision=str(document["base_revision"]),
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        if isinstance(error, ValueError) and str(error) == "source reference phase contract":
            raise
        raise ValueError("source reference phase contract") from error


def _require_offline_controls(*, offline: Literal[True], network_bomb: Literal[True]) -> None:
    if offline is not True or network_bomb is not True:
        raise ValueError("source reference phase contract")


def install_network_bomb() -> None:
    import socket

    def blocked(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("TASK7_NETWORK_BOMB")

    socket.create_connection = blocked  # type: ignore[assignment]
    socket.socket.connect = blocked  # type: ignore[method-assign]
    urllib.request.urlopen = blocked


def emit_bounded_lifecycle_event(event: str) -> None:
    if event not in {"load_reference", "install_network_bomb", "spawn_child"}:
        raise ValueError("unbounded lifecycle event")
    print(f"TASK7_OFFLINE_EVENT|{event}", flush=True)


def validated_offline_child_argv(argv: Sequence[str]) -> list[str]:
    if not argv or any(not isinstance(token, str) or "\x00" in token for token in argv):
        raise ValueError("offline child argv not allowlisted")
    repo_root = Path(__file__).resolve().parents[1]
    relative_python = (
        Path(".venv-space/Scripts/python.exe")
        if os.name == "nt"
        else Path(".venv-space/bin/python")
    )
    try:
        expected_python = (repo_root / relative_python).resolve(strict=True)
        supplied_python = Path(argv[0]).resolve(strict=True)
    except OSError as error:
        raise ValueError("offline child argv not allowlisted") from error
    allowed_arguments = {
        OFFLINE_CHILD_PYTEST_ARGUMENTS,
        ("-c", OFFLINE_CHILD_NETWORK_BOMB_PROBE_CODE),
    }
    arguments = tuple(argv[1:])
    if supplied_python != expected_python or arguments not in allowed_arguments:
        raise ValueError("offline child argv not allowlisted")
    return [str(expected_python), *arguments]


def run_network_bombed_child(
    *,
    source_reference: Path,
    run_guid: str,
    phase: Literal["offline_verify"],
    offline: Literal[True],
    network_bomb: Literal[True],
    argv: Sequence[str],
    event_sink: Callable[[str], None],
) -> int:
    load_webkit_source_reference(
        source_reference,
        run_guid=run_guid,
        phase=phase,
        offline=offline,
        network_bomb=network_bomb,
    )
    event_sink("load_reference")
    install_network_bomb()
    event_sink("install_network_bomb")
    command = validated_offline_child_argv(argv)
    event_sink("spawn_child")
    sitecustomize = """\
import socket
import urllib.request

def _carerisk_task7_blocked(*_args, **_kwargs):
    raise RuntimeError("TASK7_NETWORK_BOMB")

socket.create_connection = _carerisk_task7_blocked
socket.socket.connect = _carerisk_task7_blocked
urllib.request.urlopen = _carerisk_task7_blocked
"""
    with tempfile.TemporaryDirectory(prefix="carerisk-task7-network-bomb-") as temporary:
        bomb_root = Path(temporary)
        (bomb_root / "sitecustomize.py").write_text(
            sitecustomize,
            encoding="utf-8",
            newline="\n",
        )
        child_environment = {
            **os.environ,
            "CARERISK_TASK7_NETWORK_BOMB": "1",
            "HTTP_PROXY": "http://127.0.0.1:9",
            "HTTPS_PROXY": "http://127.0.0.1:9",
            "ALL_PROXY": "http://127.0.0.1:9",
            "NO_PROXY": "",
            "PYTHONNOUSERSITE": "1",
            "PYTHONPATH": str(bomb_root),
        }
        return subprocess.run(command, check=False, env=child_environment).returncode


def direct_pins(path: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = DIRECT_PIN.fullmatch(line)
        if match is None:
            raise ValueError(f"{path}: non-exact direct pin {line!r}")
        key = canonical_name(match.group(1))
        if key in pins:
            raise ValueError(f"{path}: duplicate direct pin {key}")
        pins[key] = match.group(2)
    if not pins:
        raise ValueError(f"{path}: no direct pins")
    return pins


def parse_lock(path: Path) -> dict[tuple[str, str], tuple[str, ...]]:
    entries: dict[tuple[str, str], tuple[str, ...]] = {}
    lines = iter(path.read_text(encoding="utf-8").splitlines())
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("--"):
            continue
        parts = [line]
        while parts[-1].endswith("\\"):
            parts.append(next(lines).strip())
        combined = " ".join(part.rstrip("\\").strip() for part in parts)
        match = LOCK_REQUIREMENT.fullmatch(combined)
        if match is None:
            raise ValueError(f"{path}: non-exact lock entry {combined!r}")
        name, version, suffix = match.groups()
        hashes = tuple(sorted(set(re.findall(r"--hash=sha256:([0-9a-f]{64})", suffix))))
        if not hashes or " @ " in combined or "://" in combined or "--editable" in combined:
            raise ValueError(f"{path}: unhashed/editable/URL entry {combined!r}")
        key = canonical_name(name), version
        if key in entries:
            raise ValueError(f"{path}: duplicate lock entry {key}")
        entries[key] = hashes
    if not entries:
        raise ValueError(f"{path}: no lock entries")
    return entries


def write_lock(entries: dict[tuple[str, str], set[str]], path: Path) -> None:
    lines = ["# Generated by scripts/build_hf_space_supply_chain.py; do not edit."]
    for (name, version), hashes in sorted(entries.items()):
        lines.append(f"{name}=={version} \\")
        ordered = sorted(hashes)
        for index, digest in enumerate(ordered):
            suffix = " \\" if index + 1 < len(ordered) else ""
            lines.append(f"    --hash=sha256:{digest}{suffix}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def run(command: Sequence[str], *, capture: bool = False) -> str:
    print("+", subprocess.list2cmdline(list(command[:10])), "...", flush=True)
    result = subprocess.run(
        list(command), check=True, text=True, encoding="utf-8", capture_output=capture
    )
    return result.stdout if capture else ""


def registry_request(
    url: str, headers: dict[str, str] | None = None
) -> tuple[bytes, dict[str, str]]:
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=headers or {}), timeout=120
        ) as response:
            return response.read(), {key.lower(): value for key, value in response.headers.items()}
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"official registry request failed: {url}: HTTP {error.code}") from error


def docker_hub_token(repository: str) -> str:
    endpoint = "https://auth.docker.io/token?" + urllib.parse.urlencode(
        {"service": "registry.docker.io", "scope": f"repository:{repository}:pull"}
    )
    value = json.loads(registry_request(endpoint)[0])["token"]
    if not isinstance(value, str) or not value:
        raise ValueError("Docker Hub omitted bearer token")
    return value


def manifest(
    registry: str, repository: str, reference: str, token: str | None
) -> tuple[dict[str, Any], str]:
    headers = {
        "Accept": ", ".join(
            (
                "application/vnd.oci.image.index.v1+json",
                "application/vnd.docker.distribution.manifest.list.v2+json",
                "application/vnd.oci.image.manifest.v1+json",
                "application/vnd.docker.distribution.manifest.v2+json",
            )
        )
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload, response_headers = registry_request(
        f"https://{registry}/v2/{repository}/manifests/{reference}", headers
    )
    digest = response_headers.get("docker-content-digest", "")
    if not OCI_DIGEST.fullmatch(digest) or sha256_bytes(payload) != digest[7:]:
        raise ValueError(f"bad immutable registry response for {repository}:{reference}")
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError("registry response is not an object")
    return value, digest


def resolve_registry_image(
    registry: str,
    api_repository: str,
    display_repository: str,
    tag: str,
    token: str | None,
) -> dict[str, Any]:
    index, index_digest = manifest(registry, api_repository, tag, token)
    candidates = [
        item["digest"]
        for item in index.get("manifests", [])
        if item.get("platform", {}).get("os") == "linux"
        and item.get("platform", {}).get("architecture") == "amd64"
    ]
    if len(candidates) != 1 or not OCI_DIGEST.fullmatch(candidates[0]):
        raise ValueError("expected exactly one linux/amd64 manifest")
    platform_manifest, observed = manifest(registry, api_repository, candidates[0], token)
    if observed != candidates[0]:
        raise ValueError("platform manifest changed during resolution")
    config_digest = str(platform_manifest.get("config", {}).get("digest", ""))
    if not OCI_DIGEST.fullmatch(config_digest):
        raise ValueError("platform manifest omitted config digest")
    return {
        "config_digest": config_digest,
        "index_digest": index_digest,
        "linux_amd64_digest": candidates[0],
        "repository": display_repository,
        "source_registry": registry,
        "tag": f"{display_repository}:{tag}",
    }


def docker_raw_manifest(reference: str) -> tuple[dict[str, Any], str]:
    command = ["docker", "buildx", "imagetools", "inspect", "--raw", reference]
    print("+", subprocess.list2cmdline(command), flush=True)
    result = subprocess.run(command, check=True, capture_output=True)
    payload = result.stdout.rstrip(b"\r\n")
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError(f"Docker returned a non-object manifest for {reference}")
    return value, "sha256:" + sha256_bytes(payload)


def resolve_docker_image(display_repository: str, tag: str) -> dict[str, Any]:
    index, index_digest = docker_raw_manifest(f"{display_repository}:{tag}")
    candidates = [
        item["digest"]
        for item in index.get("manifests", [])
        if item.get("platform", {}).get("os") == "linux"
        and item.get("platform", {}).get("architecture") == "amd64"
    ]
    if len(candidates) != 1 or not OCI_DIGEST.fullmatch(candidates[0]):
        raise ValueError("expected one linux/amd64 platform manifest")
    platform_manifest, platform_digest = docker_raw_manifest(
        f"{display_repository}@{candidates[0]}"
    )
    if platform_digest != candidates[0]:
        raise ValueError("Docker raw platform manifest digest mismatch")
    config_digest = str(platform_manifest.get("config", {}).get("digest", ""))
    if not OCI_DIGEST.fullmatch(config_digest):
        raise ValueError("platform manifest omitted config digest")
    return {
        "config_digest": config_digest,
        "index_digest": index_digest,
        "linux_amd64_digest": candidates[0],
        "repository": display_repository,
        "source_registry": (
            "registry-1.docker.io"
            if display_repository == "docker.io/library/python"
            else "mcr.microsoft.com"
        ),
        "tag": f"{display_repository}:{tag}",
    }


INSPECTION_CODE = r"""
import hashlib,json,os,platform,re,stat,sys,sysconfig
from pathlib import Path
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def paragraph(block):
    result={}; key=None
    for line in block.splitlines():
        if line[:1].isspace() and key: result[key]+="\n"+line[1:]
        elif ": " in line:
            key,value=line.split(": ",1); result[key]=value
    return result
system=[]
for block in Path('/var/lib/dpkg/status').read_text(encoding='utf-8',errors='replace').split('\n\n'):
    item=paragraph(block)
    if item.get('Status')!='install ok installed': continue
    name=item.get('Package',''); notice=Path('/usr/share/doc')/name/'copyright'
    system.append({'architecture':item.get('Architecture',''),'copyright_path':str(notice) if notice.is_file() else None,'copyright_sha256':digest(notice) if notice.is_file() else None,'name':name,'source':item.get('Source',name).split(' ',1)[0],'version':item.get('Version','')})
system.sort(key=lambda x:(x['name'],x['architecture'],x['version']))
def tree_identity(roots):
    answer=hashlib.sha256(); count=0; size=0
    for root in sorted(roots,key=lambda p:p.name):
        paths=[root,*sorted(root.rglob('*'),key=lambda p:p.relative_to(root).as_posix())]
        for path in paths:
            rel=root.name if path==root else root.name+'/'+path.relative_to(root).as_posix(); mode=os.lstat(path).st_mode
            if stat.S_ISLNK(mode): kind='L'; payload=os.readlink(path).encode()
            elif stat.S_ISREG(mode): kind='F'; payload=path.read_bytes(); count+=1; size+=len(payload)
            elif stat.S_ISDIR(mode): kind='D'; payload=b''
            else: kind='O'; payload=b''
            answer.update(kind.encode()+b'\0'+rel.encode()+b'\0'+f'{stat.S_IMODE(mode):04o}'.encode()+b'\0'+hashlib.sha256(payload).digest())
    return {'algorithm':'sha256-canonical-tree-v1','byte_count':size,'file_count':count,'sha256':answer.hexdigest()}
browser_root=Path('/ms-playwright'); browsers={}; support=[]
if browser_root.is_dir():
    groups={'chromium':[p for p in browser_root.iterdir() if re.fullmatch(r'chromium(?:_headless_shell)?-\d+',p.name)],'firefox':[p for p in browser_root.iterdir() if re.fullmatch(r'firefox-\d+',p.name)],'webkit':[p for p in browser_root.iterdir() if re.fullmatch(r'webkit-\d+',p.name)]}
    for name,roots in groups.items():
        primary=[p for p in roots if p.name.startswith(name+'-')]
        if len(primary)!=1: raise SystemExit(f'expected one {name} browser')
        notices=[]
        for root in roots:
            for path in sorted(root.rglob('*')):
                if path.is_file() and any(word in path.name.lower() for word in ('license','notice','copying','copyright')):
                    notices.append({'path':str(path),'sha256':digest(path),'size':path.stat().st_size})
        browsers[name]={'content_identity':tree_identity(roots),'content_roots':sorted(str(p) for p in roots),'notice_files':notices,'revision':primary[0].name.rsplit('-',1)[1]}
    support=sorted(p.name for p in browser_root.iterdir() if re.fullmatch(r'ffmpeg-\d+',p.name))
docker_info_path=Path('/ms-playwright/.docker-info')
docker_info=json.loads(docker_info_path.read_text()) if docker_info_path.is_file() else None
notices=[]
for path in sorted(Path('/usr/local').glob('lib/python*/LICENSE.txt')):
    notices.append({'path':str(path),'sha256':digest(path),'size':path.stat().st_size})
os_release={}
for line in Path('/etc/os-release').read_text().splitlines():
    if '=' in line:
        key,value=line.split('=',1); os_release[key]=value.strip('"')
print(json.dumps({'docker_info':docker_info,'embedded_browsers':browsers,'embedded_support':support,'image_notice_files':notices,'os_release':os_release,'python':{'abi':f'cp{sys.version_info.major}{sys.version_info.minor}','implementation':platform.python_implementation(),'platform':sysconfig.get_platform(),'version':platform.python_version()},'system_inventory':system},sort_keys=True,separators=(',',':')))
"""


def inspect_image(record: dict[str, Any], role: str) -> dict[str, Any]:
    reference = f"{record['repository']}@{record['linux_amd64_digest']}"
    run(["docker", "pull", "--platform", "linux/amd64", reference])
    output = run(
        [
            "docker",
            "run",
            "--rm",
            "--name",
            f"carerisk-task7-inspect-{role}-{os.getpid()}",
            "--network",
            "none",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "--platform",
            "linux/amd64",
            "--entrypoint",
            "python",
            reference,
            "-c",
            INSPECTION_CODE,
        ],
        capture=True,
    )
    inspection = json.loads(output)
    inventory = inspection["system_inventory"]
    inspection["system_inventory_sha256"] = "sha256:" + sha256_bytes(canonical_json(inventory))
    record.update(inspection)
    return record


def resolve_images(args: argparse.Namespace) -> int:
    runtime = resolve_docker_image("docker.io/library/python", RUNTIME_TAG)
    reviewer = resolve_docker_image("mcr.microsoft.com/playwright/python", REVIEWER_TAG)
    runtime = inspect_image(runtime, "runtime")
    reviewer = inspect_image(reviewer, "reviewer")
    runtime["tag"] = f"python:{RUNTIME_TAG}"
    if not runtime["python"]["version"].startswith("3.11."):
        raise ValueError("runtime image is not CPython 3.11")
    if reviewer.get("docker_info", {}).get("driverVersion") != PLAYWRIGHT_VERSION:
        raise ValueError("reviewer image does not match Playwright direct pin")
    if set(reviewer["embedded_browsers"]) != {"chromium", "firefox", "webkit"}:
        raise ValueError("reviewer browser inventory is incomplete")
    reviewer["playwright_python_version"] = PLAYWRIGHT_VERSION
    write_json(
        Path(args.output),
        {
            "images": {"reviewer": reviewer, "runtime": runtime},
            "resolved_platform": "linux/amd64",
            "schema_version": 1,
        },
    )
    return 0


def wheel_identity(wheel: Path) -> tuple[str, str]:
    with zipfile.ZipFile(wheel) as archive:
        names = [
            name
            for name in archive.namelist()
            if name.endswith(".dist-info/METADATA") and name.count("/") == 1
        ]
        if len(names) != 1:
            raise ValueError(f"{wheel}: expected one METADATA")
        metadata = archive.read(names[0]).decode("utf-8")
    name = next(line[6:] for line in metadata.splitlines() if line.startswith("Name: "))
    version = next(line[9:] for line in metadata.splitlines() if line.startswith("Version: "))
    return canonical_name(name), version


def lock_from_wheelhouse(wheelhouse: Path) -> dict[tuple[str, str], set[str]]:
    entries: dict[tuple[str, str], set[str]] = {}
    for wheel in sorted(wheelhouse.glob("*.whl")):
        entries.setdefault(wheel_identity(wheel), set()).add(sha256_bytes(wheel.read_bytes()))
    if not entries:
        raise ValueError("resolver produced no wheels")
    return entries


def image_reference(image: dict[str, Any]) -> str:
    repository, digest = str(image.get("repository", "")), str(image.get("linux_amd64_digest", ""))
    if not repository or not OCI_DIGEST.fullmatch(digest):
        raise ValueError("base image record lacks exact platform identity")
    return f"{repository}@{digest}"


def docker_mount(source: Path, target: str, readonly: bool) -> str:
    value = f"type=bind,source={source.resolve()},target={target}"
    return value + (",readonly" if readonly else "")


def docker_python(
    image: str,
    label: str,
    arguments: Sequence[str],
    mounts: Sequence[tuple[Path, str, bool]],
    network: str,
    pythonpath: str | None = None,
) -> None:
    temporary_size = "4g" if network == "none" else "256m"
    command = [
        "docker",
        "run",
        "--rm",
        "--name",
        f"carerisk-task7-{label}-{os.getpid()}",
        "--network",
        network,
        "--platform",
        "linux/amd64",
        "--tmpfs",
        f"/tmp:rw,noexec,nosuid,size={temporary_size}",
    ]
    if network == "none":
        command.extend(["--tmpfs", "/install:rw,exec,nosuid,size=4g"])
    if pythonpath:
        command.extend(["--env", f"PYTHONPATH={pythonpath}"])
    for source, target, readonly in mounts:
        command.extend(["--mount", docker_mount(source, target, readonly)])
    command.extend([image, "python", *arguments])
    run(command)


INSTALL_CHECK = r"""
import importlib.metadata,pathlib,re,subprocess,sys
lock=pathlib.Path('/lock').read_text()
expected={(re.sub(r'[-_.]+','-',m.group(1)).lower(),m.group(2)) for m in re.finditer(r'(?m)^([A-Za-z0-9_.-]+)==([^\s;]+)',lock)}
subprocess.run([sys.executable,'-m','pip','install','--disable-pip-version-check','--no-index','--find-links=/wheelhouse','--require-hashes','--no-deps','--target=/install','-r','/lock'],check=True)
actual={(re.sub(r'[-_.]+','-',d.metadata['Name']).lower(),d.version) for d in importlib.metadata.distributions(path=['/install'])}
if actual!=expected: raise SystemExit(f'install mismatch missing={sorted(expected-actual)} unexpected={sorted(actual-expected)}')
sys.path.insert(0,'/install'); import gradio
if gradio.__version__!='6.26.0': raise SystemExit(f'wrong Gradio {gradio.__version__}')
print(f'NO_EGRESS_INSTALL_OK|python={sys.version.split()[0]}|packages={len(actual)}|gradio={gradio.__version__}')
"""


def compile_target(
    repo_root: Path,
    work: Path,
    image: str,
    source: Path,
    output: Path,
    label: str,
    constrained: bool,
) -> dict[tuple[str, str], set[str]]:
    tooling, wheelhouse = work / "tooling", work / "wheelhouse"
    tooling.mkdir()
    wheelhouse.mkdir()
    mounts = [(repo_root, "/repo", True), (work, "/work", False)]
    docker_python(
        image,
        f"{label}-tooling",
        [
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-cache-dir",
            "--index-url",
            OFFICIAL_PYPI,
            "--require-hashes",
            "--no-deps",
            "--target=/work/tooling",
            "-r",
            "/repo/tools/space/lock-tooling.txt",
        ],
        mounts,
        "bridge",
    )
    relative = source.resolve().relative_to(repo_root.resolve()).as_posix()
    arguments = [
        "-m",
        "pip",
        "download",
        "--disable-pip-version-check",
        "--no-cache-dir",
        "--index-url",
        OFFICIAL_PYPI,
        "--only-binary=:all:",
        "--dest=/work/wheelhouse",
        "-r",
        f"/repo/{relative}",
    ]
    if constrained:
        arguments.extend(["--constraint", "/work/runtime.constraints"])
    docker_python(image, f"{label}-resolve-acquire", arguments, mounts, "bridge", "/work/tooling")
    entries = lock_from_wheelhouse(wheelhouse)
    write_lock(entries, output)
    docker_python(
        image,
        f"{label}-noegress",
        ["-c", INSTALL_CHECK],
        [(wheelhouse, "/wheelhouse", True), (output, "/lock", True)],
        "none",
    )
    return entries


def build_locks(args: argparse.Namespace) -> int:
    runtime_input, development_input = Path(args.runtime_input), Path(args.development_input)
    repo_root = runtime_input.resolve().parents[2]
    runtime_pins, development_pins = direct_pins(runtime_input), direct_pins(development_input)
    if runtime_pins != {"gradio": "6.26.0"}:
        raise ValueError("runtime input must contain only gradio==6.26.0")
    if (
        development_pins.get("gradio") != "6.26.0"
        or development_pins.get("playwright") != PLAYWRIGHT_VERSION
    ):
        raise ValueError("development Gradio/Playwright pins do not match exact images")
    images = load_json(repo_root / "tools" / "space" / "base-image.json")["images"]
    runtime_output, development_output = (
        Path(args.runtime_output).resolve(),
        Path(args.development_output).resolve(),
    )
    with tempfile.TemporaryDirectory(prefix="carerisk-task7-runtime-") as temporary:
        runtime = compile_target(
            repo_root,
            Path(temporary),
            image_reference(images["runtime"]),
            runtime_input,
            runtime_output,
            "runtime",
            False,
        )
    with tempfile.TemporaryDirectory(prefix="carerisk-task7-dev-") as temporary:
        work = Path(temporary)
        (work / "runtime.constraints").write_text(
            "".join(f"{name}=={version}\n" for name, version in sorted(runtime)),
            encoding="utf-8",
            newline="\n",
        )
        development = compile_target(
            repo_root,
            work,
            image_reference(images["reviewer"]),
            development_input,
            development_output,
            "development",
            True,
        )
    if not set(runtime) <= set(development):
        raise ValueError("development union does not contain unchanged runtime closure")
    return 0


def acquire_wheels(image: str, lock: Path, destination: Path, label: str) -> None:
    destination.mkdir()
    docker_python(
        image,
        f"inventory-{label}",
        [
            "-m",
            "pip",
            "download",
            "--disable-pip-version-check",
            "--no-cache-dir",
            "--index-url",
            OFFICIAL_PYPI,
            "--only-binary=:all:",
            "--require-hashes",
            "--dest=/wheelhouse",
            "-r",
            "/lock",
        ],
        [(destination, "/wheelhouse", False), (lock, "/lock", True)],
        "bridge",
    )


def metadata_values(text: str, key: str) -> list[str]:
    prefix = key + ": "
    return [line[len(prefix) :] for line in text.splitlines() if line.startswith(prefix)]


def wheel_record(wheel: Path) -> tuple[tuple[str, str], dict[str, Any]]:
    with zipfile.ZipFile(wheel) as archive:
        metadata_names = [
            name
            for name in archive.namelist()
            if name.endswith(".dist-info/METADATA") and name.count("/") == 1
        ]
        if len(metadata_names) != 1:
            raise ValueError(f"{wheel}: expected one top-level METADATA")
        metadata_name = metadata_names[0]
        dist_info = metadata_name.rsplit("/", 1)[0].lower() + "/"
        metadata = archive.read(metadata_name).decode("utf-8")
        license_files = []
        for member in sorted(archive.namelist()):
            lowered = member.lower()
            filename = Path(lowered).name
            if lowered.startswith(dist_info + "licenses/") or (
                lowered.startswith(dist_info)
                and any(word in filename for word in ("license", "notice", "copying", "copyright"))
            ):
                data = archive.read(member)
                license_files.append(
                    {"path": member, "sha256": sha256_bytes(data), "size": len(data)}
                )
    name = canonical_name(metadata_values(metadata, "Name")[0])
    version = metadata_values(metadata, "Version")[0]
    expressions = metadata_values(metadata, "License-Expression")
    raw_licenses = metadata_values(metadata, "License")
    classifiers = sorted(
        value for value in metadata_values(metadata, "Classifier") if value.startswith("License ::")
    )
    known = {
        "MIT": "MIT",
        "MIT License": "MIT",
        "MIT license": "MIT",
        "Apache-2.0": "Apache-2.0",
        "Apache 2.0": "Apache-2.0",
        "Apache Software License": "Apache-2.0",
        "BSD": "BSD-3-Clause",
        "BSD 3-Clause License": "BSD-3-Clause",
        "BSD-2-Clause": "BSD-2-Clause",
        "BSD-3-Clause": "BSD-3-Clause",
        "ISC License": "ISC",
        "ISC": "ISC",
        "MPL 2.0": "MPL-2.0",
        "MPL-2.0": "MPL-2.0",
        "PSF-2.0": "PSF-2.0",
        "PSFL": "PSF-2.0",
        "MPL-2.0 AND MIT": "MPL-2.0 AND MIT",
    }
    exact_license_file_expressions = {
        "b481f87296cb0abdb13fd8cbb94b14c328be880ec9e68547a61b84dacffd067a": "Apache-2.0",
        "6a06a65cf27b3f66b5fcae2743f9a958fad69749e1fb4cbd3d09aa5ac33673ba": "MIT",
        "5ea0cdf8cfc824b446cccf597ff6518c3607a659e9804bc75f1261f9c6ac4ada": "BSD-2-Clause",
        "dc626520dcd53a22f727af3ee42c770e56c97a64fe3adb063799d8ab032fe551": "LGPL-2.1-or-later",
        "b80ce9da8c42a1f91079627fbbe2bf27210ae108a0ffe5f077d5b08e076c24c8": "PSF-2.0",
        "1f256ecad192880510e84ad60474eab7589218784b9a50bc7ceee34c2b91f1d5": "MPL-2.0",
        "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4": "Apache-2.0",
        "452c0410e9a3d75abbef1b6cb519d31b23047092ca00f9bd619df7cb0d8b9a99": "ISC",
        "3b49dcee4105eb37bac10faf1be260408fe85d252b8e9df2e0979fc1e094437b": "BSD-3-Clause",
        "d8b24f15d472885f788a2d6e985850f264627b86012a17bb242c83f310d907e5": "BSD-3-Clause",
        "4a2260d6e2cd0f5a151a1e86dbfe7d3ed552b1e2beabf9941c1ba5c49cbce484": "MIT",
        "792c48c5a849a15fdf9e37e8bcf9e6d1dd13b32b46c642a748a0a46a9919d473": "MIT",
        "7c605df6e28667a9603118e98274f64a49ce3eed0d26fccce9534a345e0ef955": "MIT",
        "5c1052e921e62d36ccda50a61585e9c0444b80c62f39b57c4f3f0d5fb62f5071": "BSD-3-Clause",
        "fab3dd6bdab226f1c08630b1dd917e11fcb4ec5e1e020e2c16f83a0a13863e85": "MPL-2.0",
        "14ed54990120efea26042269885df36e1b53db858bf04b40c8cfc8c5e12f6fb1": "Apache-2.0",
        "0d542e0c8804e39aa7f37eb00da5a762149dc682d7829451287e11b938e94594": "Apache-2.0",
        "075f22737ed9245d386a23968c7ec906f66dfb7af35c3ff920aabd165a8ae920": "BSD-3-Clause",
        "1b22b049b5267d6dfc23a67bf4a84d8ec04b9fdfb1a51d360e42b4342c8b4154": "MIT",
        "ba00f51a0d92823b5a1cde27d8b5b9d2321e67ed8da9bc163eff96d5e17e577e": "Apache-2.0 AND BSD-3-Clause",
        "5ba1a4f03626ccca6dcbf53a554545e4f776a335bfdaa233ec3bfe9bb7fac15d": "MIT",
        "a85e7ef2fbc670d26781ed6844cd31a7e8ada65d21328f75a0b02402faae37ea": "BSD-3-Clause",
        "f388fd38cad13112c1dc0f669bbe80e7f84541edbafb72f3030d2ca7642c3c9d": "ISC",
        "1db7cae7fce6452e2e608e401a0f953e0133e4c2d75db69fb8ae851d2086f5b6": "Apache-2.0",
        "b80816b0d530b8accb4c2211783790984a6e3b61922c2b5ee92f3372ab2742fe": "MIT",
        "fcff87c3a47ce8028a8512aa182d4fcf0ad1c90544ee75cf9b343684cac194de": "MPL-2.0 AND MIT",
    }
    if len(set(expressions)) == 1 and expressions[0] not in {"", "UNKNOWN"}:
        expression = expressions[0]
    else:
        file_mapped = {
            exact_license_file_expressions[item["sha256"]]
            for item in license_files
            if item["sha256"] in exact_license_file_expressions
        }
        raw_mapped = {known[value.strip()] for value in raw_licenses if value.strip() in known}
        classifier_mapped = {
            known[classifier.rsplit(" :: ", 1)[-1]]
            for classifier in classifiers
            if classifier.rsplit(" :: ", 1)[-1] in known
        }
        candidates = file_mapped or raw_mapped or classifier_mapped
        if len(candidates) != 1:
            raise ValueError(f"unresolved exact wheel license evidence for {(name, version)}")
        expression = next(iter(candidates))
    return (name, version), {
        "artifact_sha256": [sha256_bytes(wheel.read_bytes())],
        "license_evidence": {
            "license_classifiers": classifiers,
            "license_files": license_files,
            "metadata_license": raw_licenses,
            "metadata_license_expression": expressions,
            "review_basis": "exact_locked_wheel_metadata_and_notices",
        },
        "license_expression": expression,
        "notice_requirement": (
            "Preserve the exact wheel license/notice files listed in license_evidence."
            if license_files
            else "Preserve the exact wheel metadata license evidence; no license file was packaged."
        ),
        "package": name,
        "review_disposition": "pending",
        "source_url": f"https://pypi.org/project/{name}/{version}/",
        "version": version,
    }


def discovered_python_records(wheelhouses: Sequence[Path]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for wheelhouse in wheelhouses:
        for wheel in sorted(wheelhouse.glob("*.whl")):
            key, record = wheel_record(wheel)
            if key not in result:
                result[key] = record
                continue
            current = result[key]
            if current["license_expression"] != record["license_expression"]:
                raise ValueError(f"license metadata differs across target wheels for {key}")
            current["artifact_sha256"] = sorted(
                set(current["artifact_sha256"]) | set(record["artifact_sha256"])
            )
            files = {
                (item["path"], item["sha256"]): item
                for item in current["license_evidence"]["license_files"]
            }
            for item in record["license_evidence"]["license_files"]:
                files[(item["path"], item["sha256"])] = item
            current["license_evidence"]["license_files"] = [files[key] for key in sorted(files)]
    return result


def image_records(base: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    runtime, reviewer = base["images"]["runtime"], base["images"]["reviewer"]
    result: dict[tuple[str, str], dict[str, Any]] = {}
    specifications = [
        (
            "python-runtime-base",
            "3.11",
            f"https://hub.docker.com/_/python@{runtime['linux_amd64_digest']}",
            runtime,
        ),
        (
            "playwright-reviewer-base",
            "1.62.0",
            f"https://mcr.microsoft.com/v2/playwright/python/manifests/{reviewer['linux_amd64_digest']}",
            reviewer,
        ),
    ]
    for name, version, source, image in specifications:
        system_notices = [
            {
                "architecture": item["architecture"],
                "copyright_path": item["copyright_path"],
                "copyright_sha256": item["copyright_sha256"],
                "name": item["name"],
                "source": item["source"],
                "version": item["version"],
            }
            for item in image["system_inventory"]
            if item["copyright_sha256"] is not None
        ]
        evidence = {
            "claim_ceiling": AGGREGATE_CLAIM_CEILING,
            "image_notice_files": image["image_notice_files"],
            "review_basis": "exact_image_manifest_system_inventory_and_notices",
            "system_inventory_sha256": image["system_inventory_sha256"],
            "system_package_copyright_files": system_notices,
        }
        result[(name, version)] = _uncertain_aggregate_record(
            package=name,
            version=version,
            hashes=[image["linux_amd64_digest"][7:]],
            evidence=evidence,
            disposition=UNCERTAIN_AGGREGATE_DISPOSITIONS[(name, version)],
            source_url=source,
        )
    for name in ("chromium", "firefox"):
        evidence = reviewer["embedded_browsers"][name]
        key = (name, "pinned")
        result[key] = _uncertain_aggregate_record(
            package=name,
            version="pinned",
            hashes=[evidence["content_identity"]["sha256"]],
            evidence={
                "claim_ceiling": AGGREGATE_CLAIM_CEILING,
                "content_identity": evidence["content_identity"],
                "notice_files": evidence["notice_files"],
                "revision": evidence["revision"],
                "review_basis": "exact_reviewer_image_browser_inventory_and_notices",
            },
            disposition=UNCERTAIN_AGGREGATE_DISPOSITIONS[key],
            source_url=f"https://mcr.microsoft.com/v2/playwright/python/manifests/{reviewer['linux_amd64_digest']}",
        )
    support = reviewer["embedded_support_records"]["ffmpeg-1011"]
    result[("ffmpeg", "pinned")] = _approved_record(
        package="ffmpeg",
        version="pinned",
        hashes=[support["content_identity"]["sha256"]],
        declared="LGPL-2.1-only",
        evidence={
            "content_identity": support["content_identity"],
            "embedded_support": ["ffmpeg-1011"],
            "notice_files": support["notice_files"],
            "revision": "1011",
            "review_basis": "exact_reviewer_image_subtree_and_notice",
        },
        source_url=f"https://mcr.microsoft.com/v2/playwright/python/manifests/{reviewer['linux_amd64_digest']}",
    )
    return result


def validate_license_policy(
    document: Mapping[str, object],
) -> dict[tuple[str, str], dict[str, object]]:
    components = document.get("components")
    if not isinstance(components, list):
        raise ValueError("license policy lacks component list")
    if document.get("schema_version", 1) != 1:
        raise ValueError("license policy schema drift")
    result: dict[tuple[str, str], dict[str, object]] = {}
    exact_webkit = exact_webkit_policy_record()
    for record in components:
        if not isinstance(record, dict):
            raise ValueError("license policy record is not an object")
        key = canonical_name(str(record.get("package"))), str(record.get("version"))
        if key in result:
            raise ValueError(f"duplicate policy record {key}")
        if key == ("webkit", "26.5") or record.get("package") == "webkit":
            if record != exact_webkit:
                raise ValueError("exact reviewer-only WebKit exception drift")
            result[key] = dict(record)
            continue
        declared = record.get("licenseDeclared")
        concluded = record.get("licenseConcluded")
        if key in UNCERTAIN_AGGREGATE_DISPOSITIONS:
            evidence = record.get("license_evidence")
            if (
                declared != "NOASSERTION"
                or concluded != "NOASSERTION"
                or record.get("review_disposition") != UNCERTAIN_AGGREGATE_DISPOSITIONS[key]
                or not isinstance(evidence, dict)
                or evidence.get("claim_ceiling") != AGGREGATE_CLAIM_CEILING
            ):
                raise ValueError(f"uncertain aggregate policy record invalid: {key}")
            result[key] = dict(record)
            continue
        if declared == "NOASSERTION" or concluded == "NOASSERTION":
            raise ValueError("NOASSERTION outside exact reviewer-only WebKit")
        if (
            record.get("review_disposition") != "approved"
            or not isinstance(declared, str)
            or not declared
            or declared == "NONE"
            or not isinstance(concluded, str)
            or not concluded
            or concluded == "NONE"
            or str(declared).startswith("LicenseRef-Hash-Locked")
            or not isinstance(record.get("license_evidence"), dict)
            or not isinstance(record.get("artifact_sha256"), list)
            or not record["artifact_sha256"]
            or not all(
                isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
                for value in record["artifact_sha256"]
            )
        ):
            raise ValueError(f"ordinary approved policy record invalid: {key}")
        result[key] = dict(record)
    return result


def policy_records(document: dict[str, Any]) -> dict[tuple[str, str], dict[str, object]]:
    return validate_license_policy(document)


LicenseTrustIdentity = tuple[str, str, tuple[str, ...]]
LicenseTrustRoot = dict[LicenseTrustIdentity, dict[str, object]]
LICENSE_TRUST_ROOT_FIELDS = {
    "artifact_sha256",
    "claim_ceiling",
    "licenseConcluded",
    "licenseDeclared",
    "package",
    "review_disposition",
    "source_url",
    "version",
}


def _license_trust_identity(
    record: Mapping[str, object],
) -> LicenseTrustIdentity:
    package = record.get("package")
    version = record.get("version")
    artifacts = record.get("artifact_sha256")
    if (
        not isinstance(package, str)
        or canonical_name(package) != package
        or not isinstance(version, str)
        or not version
        or not isinstance(artifacts, list)
        or artifacts != sorted(set(artifacts))
        or any(
            not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            for digest in artifacts
        )
    ):
        raise ValueError("license trust root artifact identity invalid")
    return package, version, tuple(artifacts)


def _license_trust_projection(
    record: Mapping[str, object],
    *,
    root_entry: bool,
) -> dict[str, object]:
    package, version, artifacts = _license_trust_identity(record)
    declared = record.get("licenseDeclared")
    concluded = record.get("licenseConcluded")
    disposition = record.get("review_disposition")
    source_url = record.get("source_url")
    if source_url is None and (package, version) == ("webkit", "26.5"):
        source_url = exact_webkit_reviewer_policy().playwright_tag_url
    if root_entry:
        claim_ceiling = record.get("claim_ceiling")
    else:
        evidence = record.get("license_evidence")
        claim_ceiling = evidence.get("claim_ceiling") if isinstance(evidence, dict) else None
    if (
        not isinstance(declared, str)
        or not declared
        or not isinstance(concluded, str)
        or not concluded
        or not isinstance(disposition, str)
        or not disposition
        or not isinstance(source_url, str)
        or not source_url
        or (claim_ceiling is not None and not isinstance(claim_ceiling, str))
    ):
        raise ValueError("license trust root projection invalid")
    return {
        "artifact_sha256": list(artifacts),
        "claim_ceiling": claim_ceiling,
        "licenseConcluded": concluded,
        "licenseDeclared": declared,
        "package": package,
        "review_disposition": disposition,
        "source_url": source_url,
        "version": version,
    }


def load_license_trust_root(path: Path) -> LicenseTrustRoot:
    document = canonical_document(path)
    components = document.get("components")
    if document.get("schema_version") != 1 or not isinstance(components, list):
        raise ValueError("license trust root schema invalid")
    result: LicenseTrustRoot = {}
    observed_identities: list[LicenseTrustIdentity] = []
    for component in components:
        if not isinstance(component, dict) or set(component) != LICENSE_TRUST_ROOT_FIELDS:
            raise ValueError("license trust root entry invalid")
        identity = _license_trust_identity(component)
        if identity in result:
            raise ValueError("license trust root duplicate identity")
        result[identity] = _license_trust_projection(component, root_entry=True)
        observed_identities.append(identity)
    if not result or observed_identities != sorted(observed_identities):
        raise ValueError("license trust root ordering invalid")
    return result


def validate_records_against_license_trust_root(
    records: Mapping[tuple[str, str], Mapping[str, object]],
    trust_root: Mapping[LicenseTrustIdentity, Mapping[str, object]],
    *,
    surface: str,
) -> None:
    observed: LicenseTrustRoot = {}
    for record in records.values():
        identity = _license_trust_identity(record)
        if identity in observed:
            raise ValueError(f"{surface} differs from license trust root")
        observed[identity] = _license_trust_projection(record, root_entry=False)
    expected = {
        identity: dict(projection)
        for identity, projection in trust_root.items()
        if identity[:2] != ("carerisk-space", "0.2.0")
    }
    if observed != expected:
        raise ValueError(f"{surface} differs from license trust root")


def validate_distribution_exclusion(surfaces: Sequence[DistributionSurface]) -> None:
    names = tuple(surface.name for surface in surfaces)
    if names != DISTRIBUTION_SURFACE_NAMES:
        raise ValueError("distribution surface registry is not exact")
    signatures = (
        "sha256:51d31fdfacb0cff99a1a724152e34ae408d2bd4e7da310ff157450f49261cc59",
        "/ms-playwright",
        "c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c",
        "65e91099ff94fb6aa3dc2b5a5216975c38749e5e25ce4f28587a97acf50ce6f7",
        "b9ac23dff6e2cb4421f56d20279618ce615a6bc3de774f0fcbfa7f117da5234f",
        "ffmpeg-1011",
    )
    for surface in surfaces:
        values = (
            *surface.paths,
            *surface.layer_digests,
            *surface.content_sha256,
            *surface.command_tokens,
        )
        if not values:
            raise ValueError("distribution surface registry is not exact")
        combined = "\n".join(values).lower()
        if any(signature.lower() in combined for signature in signatures):
            raise ValueError("reviewer/browser bytes reached distributed surface")


def spdx_id(name: str, version: str) -> str:
    return "SPDXRef-Package-" + re.sub(r"[^A-Za-z0-9.-]+", "-", f"{name}-{version}").strip("-")


def _assert_source_reference_exact(source_reference: WebKitSourceReference) -> None:
    expected = exact_webkit_reviewer_policy()
    observed = (
        source_reference.playwright_tag_commit,
        source_reference.repository_relative_path,
        source_reference.commit_pinned_raw_url,
        source_reference.raw_byte_length,
        source_reference.raw_sha256,
        source_reference.remote_url,
        source_reference.base_branch,
        source_reference.base_revision,
    )
    required = (
        expected.playwright_tag_commit,
        expected.repository_relative_path,
        expected.commit_pinned_raw_url,
        expected.raw_byte_length,
        expected.raw_sha256,
        expected.remote_url,
        expected.base_branch,
        expected.base_revision,
    )
    if observed != required:
        raise ValueError("source reference phase contract")


def tree_identity_from_ordered_inventory(
    inventory: object,
) -> dict[str, object]:
    if not isinstance(inventory, list) or not inventory:
        raise ValueError("ordered tree inventory missing")
    expected_keys = {"mode", "path", "payload_sha256", "size", "type"}
    paths: list[str] = []
    digest = hashlib.sha256()
    file_count = 0
    byte_count = 0
    for entry in inventory:
        if not isinstance(entry, dict) or set(entry) != expected_keys:
            raise ValueError("ordered tree inventory entry drift")
        path = entry["path"]
        mode = entry["mode"]
        payload_sha256 = entry["payload_sha256"]
        size = entry["size"]
        kind = entry["type"]
        if (
            not isinstance(path, str)
            or not path
            or not path.isascii()
            or path.startswith("/")
            or "\\" in path
            or "//" in path
            or any(part in {"", ".", ".."} for part in path.split("/"))
            or not isinstance(mode, str)
            or re.fullmatch(r"[0-7]{4}", mode) is None
            or not isinstance(payload_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", payload_sha256) is None
            or type(size) is not int
            or size < 0
            or kind not in {"D", "F", "L", "O"}
            or (kind != "F" and size != 0)
        ):
            raise ValueError("ordered tree inventory entry drift")
        paths.append(path)
        digest.update(
            str(kind).encode()
            + b"\0"
            + path.encode()
            + b"\0"
            + mode.encode()
            + b"\0"
            + bytes.fromhex(payload_sha256)
        )
        if kind == "F":
            file_count += 1
            byte_count += size
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ValueError("ordered tree inventory ordering drift")
    return {
        "algorithm": "sha256-canonical-tree-v1",
        "byte_count": byte_count,
        "file_count": file_count,
        "sha256": digest.hexdigest(),
    }


def derive_webkit_absence_proof(
    webkit: Mapping[str, object],
    *,
    source_relative_path: str,
) -> dict[str, object]:
    identity = tree_identity_from_ordered_inventory(webkit.get("ordered_tree_inventory"))
    inventory = webkit["ordered_tree_inventory"]
    assert isinstance(inventory, list)
    paths = {str(entry["path"]) for entry in inventory}
    return {
        "repository_relative_path": source_relative_path,
        "canonical_tree_algorithm": identity["algorithm"],
        "canonical_tree_file_count": identity["file_count"],
        "canonical_tree_total_bytes": identity["byte_count"],
        "canonical_tree_sha256": identity["sha256"],
        "present": source_relative_path in paths,
    }


def extend_frozen_base_record(path: Path, *, source_reference: WebKitSourceReference) -> None:
    _assert_source_reference_exact(source_reference)
    base = canonical_document(path)
    images = base.get("images")
    if not isinstance(images, dict):
        raise ValueError("base record lacks images")
    reviewer = images.get("reviewer")
    if not isinstance(reviewer, dict):
        raise ValueError("base record lacks reviewer")
    expected = exact_webkit_reviewer_policy()
    if (
        reviewer.get("tag") != expected.reviewer_image_tag
        or reviewer.get("index_digest") != expected.reviewer_index_digest
        or reviewer.get("linux_amd64_digest") != expected.reviewer_linux_amd64_digest
        or reviewer.get("playwright_python_version") != expected.playwright_version
    ):
        raise ValueError("frozen reviewer image drift")
    browsers = reviewer.get("embedded_browsers")
    if not isinstance(browsers, dict) or not isinstance(browsers.get("webkit"), dict):
        raise ValueError("frozen reviewer browser inventory drift")
    webkit = browsers["webkit"]
    identity = webkit.get("content_identity")
    if not isinstance(identity, dict) or (
        webkit.get("revision") != expected.webkit_revision
        or identity.get("algorithm") != expected.webkit_tree_algorithm
        or identity.get("file_count") != expected.webkit_tree_file_count
        or identity.get("byte_count") != expected.webkit_tree_total_bytes
        or identity.get("sha256") != expected.webkit_tree_sha256
        or webkit.get("content_roots") != ["/ms-playwright/webkit-2336"]
    ):
        raise ValueError("frozen WebKit tree drift")
    derived_proof = derive_webkit_absence_proof(
        webkit,
        source_relative_path=expected.repository_relative_path,
    )
    if derived_proof != dict(expected.image_tree_source_relative_path_absence_proof):
        raise ValueError("frozen WebKit absence proof drift")
    webkit.update(
        {
            "image_tree_source_relative_path_absence_proof": derived_proof,
            "tree_algorithm": expected.webkit_tree_algorithm,
            "tree_file_count": expected.webkit_tree_file_count,
            "tree_total_bytes": expected.webkit_tree_total_bytes,
            "version": expected.webkit_version,
        }
    )
    reviewer.update(
        {
            "browsers_json_url": expected.browsers_json_url,
            "cdn_artifact_url": expected.cdn_artifact_url,
            "playwright_tag": expected.playwright_tag,
            "playwright_tag_url": expected.playwright_tag_url,
            "registry_source_url": expected.registry_source_url,
            "source_reference": {
                "base_branch": source_reference.base_branch,
                "base_revision": source_reference.base_revision,
                "commit_pinned_raw_url": source_reference.commit_pinned_raw_url,
                "playwright_tag_commit": source_reference.playwright_tag_commit,
                "raw_byte_length": source_reference.raw_byte_length,
                "raw_sha256": source_reference.raw_sha256,
                "remote_url": source_reference.remote_url,
                "repository_relative_path": source_reference.repository_relative_path,
            },
        }
    )
    write_json(path, base)


def verify_image_record(
    path: Path,
    *,
    source_reference: WebKitSourceReference,
    offline: Literal[True],
    network_bomb: Literal[True],
) -> None:
    _require_offline_controls(offline=offline, network_bomb=network_bomb)
    _assert_source_reference_exact(source_reference)
    base = canonical_document(path)
    images = base.get("images")
    if not isinstance(images, dict) or set(images) != {"runtime", "reviewer"}:
        raise ValueError("base record image registry drift")
    runtime, reviewer = images["runtime"], images["reviewer"]
    if not isinstance(runtime, dict) or not isinstance(reviewer, dict):
        raise ValueError("base record image registry drift")
    if (
        runtime.get("tag") != "python:3.11.14-slim-bookworm"
        or runtime.get("index_digest")
        != "sha256:65a93d69fa75478d554f4ad27c85c1e69fa184956261b4301ebaf6dbb0a3543d"
        or runtime.get("linux_amd64_digest")
        != "sha256:83f339c1be6340ae1096010fdccf6552ac932d8f410d45d206014916bdf37e48"
        or runtime.get("system_inventory_sha256")
        != "sha256:f57e9537fc3d37ee81c303711406ccaaa3d52f7d4de7e22b27d2e99363f16e5d"
        or runtime.get("python", {}).get("version") != "3.11.14"
        or len(runtime.get("system_inventory", [])) != 105
    ):
        raise ValueError("frozen runtime image drift")
    expected = exact_webkit_reviewer_policy()
    if (
        reviewer.get("tag") != expected.reviewer_image_tag
        or reviewer.get("index_digest") != expected.reviewer_index_digest
        or reviewer.get("linux_amd64_digest") != expected.reviewer_linux_amd64_digest
        or reviewer.get("system_inventory_sha256")
        != "sha256:b5798f3511729c632213e4f4dbc33a4eb4d29c114cadb41294983a17afb2d393"
        or reviewer.get("python", {}).get("version") != "3.12.3"
        or len(reviewer.get("system_inventory", [])) != 508
        or reviewer.get("playwright_tag") != expected.playwright_tag
        or reviewer.get("playwright_tag_url") != expected.playwright_tag_url
        or reviewer.get("browsers_json_url") != expected.browsers_json_url
        or reviewer.get("registry_source_url") != expected.registry_source_url
        or reviewer.get("cdn_artifact_url") != expected.cdn_artifact_url
        or reviewer.get("source_reference")
        != {
            "base_branch": source_reference.base_branch,
            "base_revision": source_reference.base_revision,
            "commit_pinned_raw_url": source_reference.commit_pinned_raw_url,
            "playwright_tag_commit": source_reference.playwright_tag_commit,
            "raw_byte_length": source_reference.raw_byte_length,
            "raw_sha256": source_reference.raw_sha256,
            "remote_url": source_reference.remote_url,
            "repository_relative_path": source_reference.repository_relative_path,
        }
    ):
        raise ValueError("frozen reviewer image drift")
    browsers = reviewer.get("embedded_browsers")
    if not isinstance(browsers, dict) or set(browsers) != {"chromium", "firefox", "webkit"}:
        raise ValueError("browser coverage mismatch")
    identities = {
        "chromium": (
            "1234",
            594,
            680225874,
            "65e91099ff94fb6aa3dc2b5a5216975c38749e5e25ce4f28587a97acf50ce6f7",
        ),
        "firefox": (
            "1538",
            50,
            315627774,
            "b9ac23dff6e2cb4421f56d20279618ce615a6bc3de774f0fcbfa7f117da5234f",
        ),
        "webkit": (
            "2336",
            38,
            306401261,
            "c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c",
        ),
    }
    for name, (revision, count, size, digest) in identities.items():
        record = browsers[name]
        identity = record.get("content_identity", {})
        if (
            record.get("revision") != revision
            or identity.get("algorithm") != "sha256-canonical-tree-v1"
            or identity.get("file_count") != count
            or identity.get("byte_count") != size
            or identity.get("sha256") != digest
        ):
            raise ValueError(f"frozen {name} tree drift")
    webkit = browsers["webkit"]
    derived_identity = tree_identity_from_ordered_inventory(webkit.get("ordered_tree_inventory"))
    derived_proof = derive_webkit_absence_proof(
        webkit,
        source_relative_path=expected.repository_relative_path,
    )
    if (
        webkit.get("version") != expected.webkit_version
        or webkit.get("tree_algorithm") != expected.webkit_tree_algorithm
        or webkit.get("tree_file_count") != expected.webkit_tree_file_count
        or webkit.get("tree_total_bytes") != expected.webkit_tree_total_bytes
        or derived_identity != webkit.get("content_identity")
        or derived_proof != dict(expected.image_tree_source_relative_path_absence_proof)
        or webkit.get("image_tree_source_relative_path_absence_proof") != derived_proof
        or any("UPSTREAM_CONFIG" in root for root in webkit.get("content_roots", []))
    ):
        raise ValueError("frozen WebKit absence proof drift")
    support = reviewer.get("embedded_support_records")
    if not isinstance(support, dict) or set(support) != {"ffmpeg-1011"}:
        raise ValueError("frozen ffmpeg inventory drift")
    ffmpeg = support["ffmpeg-1011"]
    if not isinstance(ffmpeg, dict):
        raise ValueError("frozen ffmpeg inventory drift")
    ffmpeg_identity = tree_identity_from_ordered_inventory(ffmpeg.get("ordered_tree_inventory"))
    expected_ffmpeg_identity = {
        "algorithm": "sha256-canonical-tree-v1",
        "byte_count": 5127582,
        "file_count": 4,
        "sha256": "1514c84470c5a5706b48eea2ce282c290ccdb508a46196c24c82b6b91ffc287a",
    }
    if (
        ffmpeg.get("revision") != "1011"
        or ffmpeg.get("content_identity") != expected_ffmpeg_identity
        or ffmpeg_identity != expected_ffmpeg_identity
        or ffmpeg.get("notice_files")
        != [
            {
                "path": "/ms-playwright/ffmpeg-1011/COPYING.LGPLv2.1",
                "sha256": "b634ab5640e258563c536e658cad87080553df6f34f62269a21d554844e58bfe",
                "size": 26526,
            }
        ]
    ):
        raise ValueError("frozen ffmpeg inventory drift")


def verify_existing_locks(
    runtime_lock: Path,
    development_lock: Path,
    *,
    source_reference: WebKitSourceReference,
    offline: Literal[True],
    network_bomb: Literal[True],
) -> None:
    _require_offline_controls(offline=offline, network_bomb=network_bomb)
    _assert_source_reference_exact(source_reference)
    runtime = parse_lock(runtime_lock)
    development = parse_lock(development_lock)
    if len(runtime) != 48 or len(development) != 108:
        raise ValueError("frozen lock package count drift")
    if not set(runtime) <= set(development):
        raise ValueError("runtime lock is not a subset of development lock")
    if ("gradio", "6.26.0") not in runtime or ("gradio", "6.26.0") not in development:
        raise ValueError("Gradio lock drift")


def _approved_record(
    *,
    package: str,
    version: str,
    hashes: Sequence[str],
    declared: str,
    evidence: Mapping[str, object],
    source_url: str,
) -> dict[str, object]:
    return {
        "artifact_sha256": sorted(set(hashes)),
        "complete_digest_bound_notice": False,
        "distribution_scope": "runtime_or_review_tooling",
        "licenseConcluded": declared,
        "licenseDeclared": declared,
        "license_evidence": dict(evidence),
        "package": package,
        "review_disposition": "approved",
        "source_url": source_url,
        "version": version,
    }


def _uncertain_aggregate_record(
    *,
    package: str,
    version: str,
    hashes: Sequence[str],
    evidence: Mapping[str, object],
    disposition: str,
    source_url: str,
) -> dict[str, object]:
    return {
        "artifact_sha256": sorted(set(hashes)),
        "complete_digest_bound_notice": False,
        "distribution_scope": "runtime_or_review_tooling",
        "licenseConcluded": "NOASSERTION",
        "licenseDeclared": "NOASSERTION",
        "license_evidence": dict(evidence),
        "package": package,
        "review_disposition": disposition,
        "source_url": source_url,
        "version": version,
    }


def reviewed_policy_records_from_wheels(
    base: Mapping[str, object],
    runtime: Mapping[tuple[str, str], tuple[str, ...]],
    development: Mapping[tuple[str, str], tuple[str, ...]],
    wheelhouses: Sequence[Path],
) -> dict[tuple[str, str], dict[str, object]]:
    combined: dict[tuple[str, str], set[str]] = {}
    for source in (runtime, development):
        for key, lock_hashes in source.items():
            combined.setdefault(key, set()).update(lock_hashes)
    discovered = discovered_python_records(wheelhouses)
    if set(discovered) != set(combined):
        raise ValueError("wheel evidence coverage differs from frozen locks")
    result: dict[tuple[str, str], dict[str, object]] = {}
    for (name, version), combined_hashes in sorted(combined.items()):
        record = discovered[(name, version)]
        if set(record["artifact_sha256"]) != combined_hashes:
            raise ValueError(f"wheel evidence hash differs from frozen lock for {(name, version)}")
        expression = str(record["license_expression"])
        if not expression or expression.startswith("LicenseRef-Wheel-"):
            raise ValueError(f"unresolved wheel license evidence for {(name, version)}")
        result[(name, version)] = _approved_record(
            package=name,
            version=version,
            hashes=sorted(combined_hashes),
            declared=expression,
            evidence=record["license_evidence"],
            source_url=str(record["source_url"]),
        )
    result.update(image_records(dict(base)))
    result[("webkit", "26.5")] = exact_webkit_policy_record()
    return result


def validate_policy_against_frozen_inputs(
    policy: Mapping[tuple[str, str], Mapping[str, object]],
    base: Mapping[str, object],
    runtime: Mapping[tuple[str, str], tuple[str, ...]],
    development: Mapping[tuple[str, str], tuple[str, ...]],
) -> None:
    combined: dict[tuple[str, str], set[str]] = {}
    for source in (runtime, development):
        for key, lock_hashes in source.items():
            combined.setdefault(key, set()).update(lock_hashes)
    expected_images = image_records(dict(base))
    expected_images[("webkit", "26.5")] = exact_webkit_policy_record()
    if set(policy) != set(combined) | set(expected_images):
        raise ValueError("license policy coverage differs from frozen inputs")
    evidence_keys = {
        "license_classifiers",
        "license_files",
        "metadata_license",
        "metadata_license_expression",
        "review_basis",
    }
    for key, combined_hashes in combined.items():
        record = policy[key]
        evidence = record.get("license_evidence")
        if (
            record.get("artifact_sha256") != sorted(combined_hashes)
            or record.get("source_url") != f"https://pypi.org/project/{key[0]}/{key[1]}/"
            or record.get("licenseDeclared") != record.get("licenseConcluded")
            or str(record.get("licenseDeclared", "")).startswith("LicenseRef-Hash-Locked")
            or not isinstance(evidence, dict)
            or set(evidence) != evidence_keys
            or evidence.get("review_basis") != "exact_locked_wheel_metadata_and_notices"
            or not any(
                evidence.get(field)
                for field in (
                    "license_classifiers",
                    "license_files",
                    "metadata_license",
                    "metadata_license_expression",
                )
            )
        ):
            raise ValueError(f"wheel license evidence drift for {key}")
        license_files = evidence["license_files"]
        if not isinstance(license_files, list) or any(
            not isinstance(item, dict)
            or set(item) != {"path", "sha256", "size"}
            or not isinstance(item["path"], str)
            or re.fullmatch(r"[0-9a-f]{64}", str(item["sha256"])) is None
            or type(item["size"]) is not int
            or item["size"] < 0
            for item in license_files
        ):
            raise ValueError(f"wheel license file evidence drift for {key}")
    for key, expected in expected_images.items():
        if policy[key] != expected:
            raise ValueError(f"image license evidence drift for {key}")


def expected_spdx_document(
    trust_root: Mapping[LicenseTrustIdentity, Mapping[str, object]],
) -> dict[str, object]:
    packages: list[dict[str, object]] = []
    package_keys: list[tuple[str, str]] = []
    for identity in sorted(trust_root):
        name, version, hashes = identity
        record = trust_root[identity]
        package_keys.append((name, version))
        declared = str(record["licenseDeclared"])
        concluded = str(record["licenseConcluded"])
        source_url = str(record["source_url"])
        packages.append(
            {
                "SPDXID": spdx_id(name, version),
                "checksums": [
                    {"algorithm": "SHA256", "checksumValue": digest} for digest in hashes
                ],
                "copyrightText": "NOASSERTION",
                "downloadLocation": source_url,
                "filesAnalyzed": False,
                "licenseConcluded": concluded,
                "licenseDeclared": declared,
                "name": name,
                "versionInfo": version,
            }
        )
    namespace_hash = sha256_bytes(canonical_json(packages))
    return {
        "SPDXID": "SPDXRef-DOCUMENT",
        "creationInfo": {
            "created": "2026-09-01T00:00:00Z",
            "creators": ["Tool: scripts/build_hf_space_supply_chain.py"],
        },
        "dataLicense": "CC0-1.0",
        "documentNamespace": ("https://github.com/kuotunyu/CareRisk-48H/spdx/" + namespace_hash),
        "name": "carerisk-space-sbom",
        "packages": packages,
        "relationships": [
            {
                "relatedSpdxElement": spdx_id(name, version),
                "relationshipType": "DESCRIBES",
                "spdxElementId": "SPDXRef-DOCUMENT",
            }
            for name, version in package_keys
        ],
        "spdxVersion": "SPDX-2.3",
    }


def validate_spdx_against_license_trust_root(
    document: Mapping[str, object],
    trust_root: Mapping[LicenseTrustIdentity, Mapping[str, object]],
) -> None:
    expected = expected_spdx_document(trust_root)
    if document.get("packages") != expected["packages"]:
        raise ValueError("SPDX package projection drift: SBOM differs from license trust root")
    if document.get("relationships") != expected["relationships"]:
        raise ValueError("SPDX relationships drift: SBOM differs from license trust root")
    observed_metadata = {
        key: value for key, value in document.items() if key not in {"packages", "relationships"}
    }
    expected_metadata = {
        key: value for key, value in expected.items() if key not in {"packages", "relationships"}
    }
    if observed_metadata != expected_metadata:
        raise ValueError("SPDX document metadata drift: SBOM differs from license trust root")


def build_inventory_and_sbom(
    args: argparse.Namespace,
    *,
    source_reference: WebKitSourceReference,
    offline: Literal[True],
    network_bomb: Literal[True],
) -> None:
    _require_offline_controls(offline=offline, network_bomb=network_bomb)
    verify_image_record(
        Path(args.base),
        source_reference=source_reference,
        offline=True,
        network_bomb=True,
    )
    verify_existing_locks(
        Path(args.runtime_lock),
        Path(args.development_lock),
        source_reference=source_reference,
        offline=True,
        network_bomb=True,
    )
    base = canonical_document(Path(args.base))
    runtime = parse_lock(Path(args.runtime_lock))
    development = parse_lock(Path(args.development_lock))
    policy_path = Path(args.license_policy)
    policy = validate_license_policy(canonical_document(policy_path))
    validate_policy_against_frozen_inputs(policy, base, runtime, development)
    trust_root = load_license_trust_root(policy_path.with_name("license-trust-root.json"))
    validate_records_against_license_trust_root(
        policy,
        trust_root,
        surface="license policy",
    )
    components = [policy[key] for key in sorted(policy)]
    license_inventory = {"components": components, "document_version": 1}
    inventory_records = validate_license_policy(license_inventory)
    validate_records_against_license_trust_root(
        inventory_records,
        trust_root,
        surface="THIRD_PARTY_LICENSES",
    )
    spdx = expected_spdx_document(trust_root)
    validate_spdx_against_license_trust_root(spdx, trust_root)
    write_json(Path(args.licenses_output), license_inventory)
    write_json(Path(args.sbom_output), spdx)


def build_inventory(args: argparse.Namespace) -> int:
    raise RuntimeError(
        "historic acquisition inventory is disabled; use the offline inventory command"
    )


def canonical_document(path: Path) -> dict[str, Any]:
    document = load_json(path)
    if path.read_bytes() != canonical_json(document):
        raise ValueError(f"{path} is not canonical JSON")
    return document


def verify_all(
    repo_root: Path,
    *,
    source_reference: WebKitSourceReference,
    offline: Literal[True],
    network_bomb: Literal[True],
) -> None:
    _require_offline_controls(offline=offline, network_bomb=network_bomb)
    runtime_input = repo_root / "tools/space/requirements-runtime.in"
    development_input = repo_root / "tools/space/requirements-dev.in"
    runtime_lock = repo_root / "space/requirements.lock"
    development_lock = repo_root / "space/requirements-dev.lock"
    runtime = parse_lock(runtime_lock)
    development = parse_lock(development_lock)
    parse_lock(repo_root / "tools/space/lock-tooling.txt")
    runtime_pins, development_pins = direct_pins(runtime_input), direct_pins(development_input)
    if runtime_pins != {"gradio": "6.26.0"}:
        raise ValueError("runtime direct input is not strict Gradio 6.26.0")
    required_dev = {
        "axe-playwright-python",
        "cyclonedx-bom",
        "gradio",
        "license-expression",
        "mypy",
        "packaging",
        "pip-audit",
        "pip-licenses",
        "pip-tools",
        "playwright",
        "pyyaml",
        "pytest",
        "ruff",
    }
    if not required_dev <= set(development_pins) or development_pins["gradio"] != "6.26.0":
        raise ValueError("development direct input is incomplete")
    if not set(runtime) <= set(development) or ("gradio", "6.26.0") not in runtime:
        raise ValueError("lock union/subset/Gradio contract failed")
    verify_existing_locks(
        runtime_lock,
        development_lock,
        source_reference=source_reference,
        offline=True,
        network_bomb=True,
    )
    base_path = repo_root / "tools/space/base-image.json"
    verify_image_record(
        base_path,
        source_reference=source_reference,
        offline=True,
        network_bomb=True,
    )
    policy = policy_records(canonical_document(repo_root / "tools/space/license-policy.json"))
    expected = set(runtime) | set(development) | IMAGE_COMPONENTS
    if set(policy) != expected:
        raise ValueError("policy coverage mismatch")
    base = canonical_document(base_path)
    validate_policy_against_frozen_inputs(policy, base, runtime, development)
    trust_root = load_license_trust_root(repo_root / "tools/space/license-trust-root.json")
    validate_records_against_license_trust_root(
        policy,
        trust_root,
        surface="license policy",
    )
    licenses = canonical_document(repo_root / "space/THIRD_PARTY_LICENSES.json")
    inventory_records = validate_license_policy(licenses)
    validate_records_against_license_trust_root(
        inventory_records,
        trust_root,
        surface="THIRD_PARTY_LICENSES",
    )
    if licenses.get("components") != [policy[key] for key in sorted(policy)]:
        raise ValueError("license inventory differs from policy")
    sbom = canonical_document(repo_root / "space/SBOM.spdx.json")
    validate_spdx_against_license_trust_root(sbom, trust_root)
    webkit_packages = [
        item
        for item in sbom.get("packages", [])
        if item.get("name") == "webkit" and item.get("versionInfo") == "26.5"
    ]
    if len(webkit_packages) != 1 or (
        webkit_packages[0].get("licenseDeclared") != "NOASSERTION"
        or webkit_packages[0].get("licenseConcluded") != "NOASSERTION"
    ):
        raise ValueError("SPDX WebKit exception drift")
    surfaces = [
        DistributionSurface(
            name=name,
            paths=(f"approved/{name}.txt",),
            layer_digests=(),
            content_sha256=(),
            command_tokens=(),
        )
        for name in DISTRIBUTION_SURFACE_NAMES
    ]
    validate_distribution_exclusion(surfaces)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    def add_controls(command: argparse.ArgumentParser) -> None:
        command.add_argument("--source-reference", required=True)
        command.add_argument("--run-guid", required=True)
        command.add_argument("--phase", required=True)
        command.add_argument("--offline", action="store_true")
        command.add_argument("--network-bomb", action="store_true")

    images = commands.add_parser("verify-images")
    images.add_argument("--input", required=True)
    add_controls(images)
    locks = commands.add_parser("verify-locks")
    locks.add_argument("--runtime-lock", required=True)
    locks.add_argument("--development-lock", required=True)
    add_controls(locks)
    inventory = commands.add_parser("inventory")
    inventory.add_argument("--base", required=True)
    inventory.add_argument("--runtime-lock", required=True)
    inventory.add_argument("--development-lock", required=True)
    inventory.add_argument("--license-policy", required=True)
    inventory.add_argument("--licenses-output", required=True)
    inventory.add_argument("--sbom-output", required=True)
    add_controls(inventory)
    verify = commands.add_parser("verify")
    verify.add_argument("--repo-root", type=Path, required=True)
    add_controls(verify)
    offline_test = commands.add_parser("offline-test")
    add_controls(offline_test)
    offline_test.add_argument("child_command", nargs=argparse.REMAINDER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    child_command = getattr(args, "child_command", None)
    if child_command is not None:
        command = list(child_command)
        if command[:1] == ["--"]:
            command = command[1:]
        return run_network_bombed_child(
            source_reference=Path(args.source_reference),
            run_guid=args.run_guid,
            phase=args.phase,
            offline=args.offline,
            network_bomb=args.network_bomb,
            argv=command,
            event_sink=emit_bounded_lifecycle_event,
        )
    source_reference = load_webkit_source_reference(
        Path(args.source_reference),
        run_guid=args.run_guid,
        phase=args.phase,
        offline=args.offline,
        network_bomb=args.network_bomb,
    )
    install_network_bomb()
    if args.command == "verify-images":
        verify_image_record(
            Path(args.input),
            source_reference=source_reference,
            offline=True,
            network_bomb=True,
        )
        return 0
    if args.command == "verify-locks":
        verify_existing_locks(
            Path(args.runtime_lock),
            Path(args.development_lock),
            source_reference=source_reference,
            offline=True,
            network_bomb=True,
        )
        return 0
    if args.command == "inventory":
        build_inventory_and_sbom(
            args,
            source_reference=source_reference,
            offline=True,
            network_bomb=True,
        )
        return 0
    if args.command == "verify":
        verify_all(
            args.repo_root,
            source_reference=source_reference,
            offline=True,
            network_bomb=True,
        )
        return 0
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
