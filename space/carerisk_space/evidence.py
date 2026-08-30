"""Fail-closed validation of the public v0.2.0 evidence objects."""
# The fixed schema key sets intentionally mirror the committed JSON objects.
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import math
import re
import stat
from pathlib import Path
from types import MappingProxyType
from typing import Literal, NoReturn, cast

from .contracts import (
    PUBLIC_PATHS,
    ContractViolation,
    DeploymentManifest,
    EvidenceFailure,
    EvidenceLoadResult,
    EvidenceViewModel,
    ManifestCapability,
    ManifestFile,
    MetricInterval,
    ReceiptEvidence,
    ReceiptHashMismatch,
    ReleaseRelationship,
)

# SHA-256 of the immutable receipt blob at v0.2.0 (verified with git cat-file).
RECEIPT_SHA256 = "d32d833af25e4ebb2f5bd06b64343eb36d7cd180c8e9777f539f6401b78064b3"
RECEIPT_GIT_BLOB_SHA = "b13ec7655bbdb8db1079c3b4793a0bf5590ef69c"
FORMAL_METRICS_SHA256 = "808525afad2ec550e8059c4ba37c2f5aaf8af748873a5a590dff7f1aeaaf47af"
RELEASE_RECEIPT_BLOB_SHA = RECEIPT_GIT_BLOB_SHA

_RECEIPT_KEYS = {
    "confidence_intervals",
    "dataset",
    "evaluation",
    "evaluation_status",
    "metrics",
    "model",
    "privacy",
    "provenance",
    "schema_version",
    "title",
    "use_limitation",
}
_INTERVAL_KEYS = {"estimate", "lower", "upper"}
_DATASET_KEYS = {"events", "n", "name", "prevalence", "role"}
_EVALUATION_KEYS = {
    "bootstrap",
    "created_at_utc",
    "final_lock_status",
    "run_id",
    "set_b_final_evaluation_successes",
}
_BOOTSTRAP_KEYS = {"method", "samples", "seed"}
_PRIVACY_KEYS = {"aggregate_only", "excluded"}
_PROVENANCE_KEYS = {
    "candidate_source_git_sha",
    "config_hash",
    "data_manifest_hash",
    "evaluation_source_git_dirty",
    "evaluation_source_git_sha",
    "formal_metrics_sha256",
    "freeze_manifest_sha256",
    "set_b_input_manifest_sha256",
    "split_hash",
}
_RELEASE_KEYS = {
    "baseline_main_commit",
    "limitations",
    "release",
    "release_date",
    "release_kind",
    "schema_version",
    "scientific_evidence",
    "scope",
    "zenodo",
}
_SCIENTIFIC_KEYS = {
    "final_result_receipt",
    "final_result_receipt_git_blob_sha",
    "scientific_result_changed",
    "set_b_rerun",
    "set_c_used",
    "frozen_model_changed",
    "threshold_changed",
}
_LIMITATIONS = (
    "no external validation",
    "no temporal or site-held-out validation",
    "no prospective validation",
    "no clinical utility study",
    "historical same-source ICU cohort",
)
_EXCLUSIONS = (
    "record_identifiers",
    "raw_outcomes",
    "individual_predictions",
    "model_artifacts",
    "subgroup_rows",
    "environment_details",
    "access_ledger_contents",
)
_DISPLAYED_METRICS = ("auprc", "auroc", "brier", "ece")
_MODEL_KEYS = {"calibrator", "family", "seeds", "threshold"}

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
_BASE_IMAGE_KEYS = {"runtime", "reviewer"}
_BASE_IMAGE_RECORD_KEYS = {
    "repository",
    "tag",
    "index_digest",
    "linux_amd64_digest",
}
_SUPPLY_CHAIN_KEYS = {
    "runtime_lock_sha256",
    "development_lock_sha256",
    "sbom_sha256",
    "third_party_licenses_sha256",
}
_CAPABILITIES = {
    "runtime_code",
    "evidence",
    "legal",
    "metadata",
    "supply_chain",
    "test",
}
_LITERAL_EVIDENCE_PATHS = {
    "evidence/final-result-receipt.json",
    "evidence/release-v0.2.0.json",
    "deployment-manifest.json",
}
_SOURCE_PATHS = {
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
    "evidence/final-result-receipt.json": "docs/final-result-receipt.json",
    "evidence/release-v0.2.0.json": "docs/release-v0.2.0.json",
    "deployment-manifest.json": "space/deployment-manifest.json",
    "LICENSE": "LICENSE",
    "NOTICE": "NOTICE",
    "CITATION.cff": "CITATION.cff",
    "SBOM.spdx.json": "space/SBOM.spdx.json",
    "THIRD_PARTY_LICENSES.json": "space/THIRD_PARTY_LICENSES.json",
    "tests/test_claim_contract.py": "space/tests/test_claim_contract.py",
    "tests/test_evidence_contract.py": "space/tests/test_evidence_contract.py",
    "tests/test_scenario_contract.py": "space/tests/test_scenario_contract.py",
    "tests/test_gradio_contract.py": "space/tests/test_gradio_contract.py",
    "tests/test_export_contract.py": "space/tests/test_export_contract.py",
    "tests/test_container_contract.py": "space/tests/test_container_contract.py",
}
_EXPECTED_CAPABILITIES: dict[str, ManifestCapability] = {
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
_TAG_SOURCE_PATHS = {
    "evidence/final-result-receipt.json",
    "evidence/release-v0.2.0.json",
    "LICENSE",
    "NOTICE",
    "CITATION.cff",
}
_SUPPLY_CHAIN_FILE_RELATIONSHIPS = {
    "runtime_lock_sha256": "requirements.lock",
    "development_lock_sha256": "requirements-dev.lock",
    "sbom_sha256": "SBOM.spdx.json",
    "third_party_licenses_sha256": "THIRD_PARTY_LICENSES.json",
}
_HEX_SHA40 = re.compile(r"[0-9a-f]{40}")
_HEX_SHA64 = re.compile(r"[0-9a-f]{64}")
_IMAGE_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
_RUNTIME_TAG = re.compile(r"3\.11\.\d+-slim-bookworm")
_REVIEWER_TAG = re.compile(r"v\d+\.\d+\.\d+-(?:jammy|noble)")

AllowedEvidencePath = Literal[
    "evidence/final-result-receipt.json",
    "evidence/release-v0.2.0.json",
    "deployment-manifest.json",
]


def loads_strict_object(raw: bytes) -> dict[str, object]:
    def unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ContractViolation("receipt_schema_invalid")
            result[key] = value
        return result

    def reject_constant(_: str) -> NoReturn:
        raise ContractViolation("receipt_schema_invalid")

    try:
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=unique_pairs, parse_constant=reject_constant
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractViolation("receipt_schema_invalid") from exc
    if not isinstance(value, dict):
        raise ContractViolation("receipt_schema_invalid")
    return value


def git_blob_sha1(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw, usedforsecurity=False).hexdigest()


def _object(value: object, keys: set[str], code: str = "receipt_schema_invalid") -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ContractViolation(code)
    return value


def _number(value: object) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
    ):
        raise ContractViolation("receipt_schema_invalid")
    return float(value)


def _text(value: object) -> str:
    if not isinstance(value, str):
        raise ContractViolation("receipt_schema_invalid")
    return value


def validate_receipt(raw: bytes) -> ReceiptEvidence:
    if (
        hashlib.sha256(raw).hexdigest() != RECEIPT_SHA256
        or git_blob_sha1(raw) != RECEIPT_GIT_BLOB_SHA
    ):
        raise ReceiptHashMismatch("receipt_hash_mismatch")
    try:
        root = loads_strict_object(raw)
        if (
            set(root) != _RECEIPT_KEYS
            or root["schema_version"] != 1
            or root["evaluation_status"] != "final"
        ):
            raise ContractViolation("receipt_schema_invalid")
        dataset = _object(root["dataset"], _DATASET_KEYS)
        evaluation = _object(root["evaluation"], _EVALUATION_KEYS)
        bootstrap = _object(evaluation["bootstrap"], _BOOTSTRAP_KEYS)
        model = _object(root["model"], _MODEL_KEYS)
        privacy = _object(root["privacy"], _PRIVACY_KEYS)
        provenance = _object(root["provenance"], _PROVENANCE_KEYS)
        metrics_raw = _object(
            root["metrics"],
            set(_DISPLAYED_METRICS) | {"confusion", "npv", "ppv", "sensitivity", "specificity"},
        )
        intervals = _object(
            root["confidence_intervals"],
            {"auprc", "auroc", "brier", "ece", "npv", "ppv", "sensitivity", "specificity"},
        )
        if (
            privacy["aggregate_only"] is not True
            or evaluation["set_b_final_evaluation_successes"] != 1
        ):
            raise ContractViolation("receipt_schema_invalid")
        if evaluation["final_lock_status"] != "locked_after_one_success":
            raise ContractViolation("receipt_schema_invalid")
        if dataset["role"] != "final_test" or dataset["n"] != 4000 or dataset["events"] != 568:
            raise ContractViolation("receipt_schema_invalid")
        if _number(dataset["prevalence"]) != 568 / 4000:
            raise ContractViolation("receipt_schema_invalid")
        if (
            bootstrap["method"] != "stratified percentile"
            or bootstrap["samples"] != 2000
            or bootstrap["seed"] != 2026
        ):
            raise ContractViolation("receipt_schema_invalid")
        if provenance["formal_metrics_sha256"] != FORMAL_METRICS_SHA256 or privacy[
            "excluded"
        ] != list(_EXCLUSIONS):
            raise ContractViolation("receipt_schema_invalid")
        if not isinstance(dataset["name"], str) or not isinstance(dataset["role"], str):
            raise ContractViolation("receipt_schema_invalid")
        if not isinstance(root["title"], str) or not isinstance(root["use_limitation"], str):
            raise ContractViolation("receipt_schema_invalid")
        if not isinstance(model["family"], str) or not isinstance(model["calibrator"], str):
            raise ContractViolation("receipt_schema_invalid")
        if (
            not isinstance(model["seeds"], list)
            or len(model["seeds"]) != 3
            or any(isinstance(seed, bool) or not isinstance(seed, int) for seed in model["seeds"])
            or not isinstance(model["threshold"], (int, float))
            or isinstance(model["threshold"], bool)
            or not math.isfinite(float(model["threshold"]))
        ):
            raise ContractViolation("receipt_schema_invalid")
        result: dict[str, MetricInterval] = {}
        for name in _DISPLAYED_METRICS:
            metric = _number(metrics_raw[name])
            interval = _object(intervals[name], _INTERVAL_KEYS)
            estimate, lower, upper = (_number(interval[k]) for k in ("estimate", "lower", "upper"))
            if (
                not all(0 <= x <= 1 for x in (metric, estimate, lower, upper))
                or not lower <= estimate <= upper
                or estimate != metric
            ):
                raise ContractViolation("receipt_schema_invalid")
            result[name] = MetricInterval(estimate, lower, upper)
        return ReceiptEvidence(
            dataset_name=_text(dataset["name"]),
            dataset_role=_text(dataset["role"]),
            n=int(dataset["n"]),
            events=int(dataset["events"]),
            prevalence=_number(dataset["prevalence"]),
            metrics=MappingProxyType(result),
            bootstrap_method=_text(bootstrap["method"]),
            bootstrap_samples=int(bootstrap["samples"]),
            bootstrap_seed=int(bootstrap["seed"]),
            evaluation_status="final",
            success_count=int(evaluation["set_b_final_evaluation_successes"]),
            final_lock_status=_text(evaluation["final_lock_status"]),
            use_limitation=_text(root["use_limitation"]),
            formal_metrics_sha256=_text(provenance["formal_metrics_sha256"]),
        )
    except ContractViolation:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractViolation("receipt_schema_invalid") from exc


def validate_release(raw: bytes, receipt: ReceiptEvidence) -> ReleaseRelationship:
    try:
        try:
            root = loads_strict_object(raw)
        except ContractViolation as exc:
            raise ContractViolation("release_relationship_invalid") from exc
        if (
            set(root) != _RELEASE_KEYS
            or root["schema_version"] != 1
            or root["release"] != "v0.2.0"
            or root["release_kind"] != "research-software-portfolio-closure"
        ):
            raise ContractViolation("release_relationship_invalid")
        if receipt.dataset_name != "PhysioNet Challenge 2012 Set B" or receipt.dataset_role != "final_test" or receipt.n != 4000 or receipt.events != 568 or receipt.formal_metrics_sha256 != FORMAL_METRICS_SHA256:
            raise ContractViolation("release_relationship_invalid")
        scientific = _object(root["scientific_evidence"], _SCIENTIFIC_KEYS, "release_relationship_invalid")
        if (
            scientific["final_result_receipt"] != "docs/final-result-receipt.json"
            or scientific["final_result_receipt_git_blob_sha"] != RECEIPT_GIT_BLOB_SHA
        ):
            raise ContractViolation("release_relationship_invalid")
        flags = {
            key: scientific[key]
            for key in (
                "scientific_result_changed",
                "set_b_rerun",
                "set_c_used",
                "frozen_model_changed",
                "threshold_changed",
            )
        }
        if any(value is not False for value in flags.values()) or root["limitations"] != list(
            _LIMITATIONS
        ):
            raise ContractViolation("release_relationship_invalid")
        return ReleaseRelationship(
            "v0.2.0", _LIMITATIONS, MappingProxyType(cast(dict[str, bool], flags))
        )
    except ContractViolation:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractViolation("release_relationship_invalid") from exc


def read_regular_file(bundle_root: Path, relative_path: AllowedEvidencePath) -> bytes:
    """Read one literal evidence path without following symlinks or special files."""
    if relative_path not in _LITERAL_EVIDENCE_PATHS:
        raise ContractViolation("deployment_manifest_invalid")
    path = bundle_root.joinpath(*relative_path.split("/"))
    try:
        mode = path.lstat().st_mode
    except OSError:
        raise FileNotFoundError from None
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise FileNotFoundError
    try:
        return path.read_bytes()
    except OSError:
        raise FileNotFoundError from None


def _manifest_object(value: object, keys: set[str]) -> dict[str, object]:
    return _object(value, keys, "deployment_manifest_invalid")


def _manifest_text(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ContractViolation("deployment_manifest_invalid")
    return value


def _manifest_sha256(value: object) -> str:
    text = _manifest_text(value)
    if _HEX_SHA64.fullmatch(text) is None:
        raise ContractViolation("deployment_manifest_invalid")
    return text


def _expected_media_type(path: str) -> str:
    if path.endswith(".json"):
        return "application/json"
    if path.endswith(".py"):
        return "text/x-python"
    if path.endswith(".md"):
        return "text/markdown"
    if path.endswith(".cff"):
        return "application/yaml"
    return "text/plain"


def _validate_base_images(value: object) -> None:
    images = _manifest_object(value, _BASE_IMAGE_KEYS)
    for role in ("runtime", "reviewer"):
        image = _manifest_object(images[role], _BASE_IMAGE_RECORD_KEYS)
        repository = _manifest_text(image["repository"])
        tag = _manifest_text(image["tag"])
        if role == "runtime":
            valid_identity = (
                repository == "docker.io/library/python"
                and _RUNTIME_TAG.fullmatch(tag) is not None
            )
        else:
            valid_identity = (
                repository == "mcr.microsoft.com/playwright/python"
                and _REVIEWER_TAG.fullmatch(tag) is not None
            )
        if not valid_identity or any(
            _IMAGE_DIGEST.fullmatch(_manifest_text(image[key])) is None
            for key in ("index_digest", "linux_amd64_digest")
        ):
            raise ContractViolation("deployment_manifest_invalid")


def _validate_manifest_file(
    value: object,
    *,
    app_source_sha: str,
    evidence_tag_commit: str,
) -> ManifestFile:
    item = _manifest_object(value, _MANIFEST_FILE_KEYS)
    destination = _manifest_text(item["destination_path"])
    if destination not in PUBLIC_PATHS:
        raise ContractViolation("deployment_manifest_invalid")
    source_ref = _manifest_text(item["source_ref"])
    source_path = _manifest_text(item["source_path"])
    media_type = _manifest_text(item["media_type"])
    capability = _manifest_text(item["capability"])
    if (
        source_path != _SOURCE_PATHS[destination]
        or media_type != _expected_media_type(destination)
        or capability != _EXPECTED_CAPABILITIES[destination]
        or capability not in _CAPABILITIES
    ):
        raise ContractViolation("deployment_manifest_invalid")
    if destination == "deployment-manifest.json":
        if (
            source_ref != "export-manifest-commit"
            or item["sha256"] is not None
            or item["byte_size"] is not None
        ):
            raise ContractViolation("deployment_manifest_invalid")
        sha256 = None
        byte_size = None
    else:
        expected_ref = evidence_tag_commit if destination in _TAG_SOURCE_PATHS else app_source_sha
        if source_ref != expected_ref:
            raise ContractViolation("deployment_manifest_invalid")
        sha256 = _manifest_sha256(item["sha256"])
        raw_size = item["byte_size"]
        if isinstance(raw_size, bool) or not isinstance(raw_size, int) or raw_size < 0:
            raise ContractViolation("deployment_manifest_invalid")
        byte_size = raw_size
    return ManifestFile(
        source_ref=source_ref,
        source_path=source_path,
        destination_path=destination,
        sha256=sha256,
        byte_size=byte_size,
        media_type=media_type,
        capability=capability,
    )


def validate_deployment_manifest(
    raw: bytes,
    *,
    receipt_raw: bytes,
    release_raw: bytes,
    receipt: ReceiptEvidence,
    release: ReleaseRelationship,
) -> DeploymentManifest:
    try:
        root = loads_strict_object(raw)
        schema_version = root.get("schema_version")
        if (
            set(root) != _MANIFEST_KEYS
            or type(schema_version) is not int
            or schema_version != 1
        ):
            raise ContractViolation("deployment_manifest_invalid")
        app_source_sha = _manifest_text(root["space_app_source_git_sha"])
        evidence_tag = _manifest_text(root["evidence_tag"])
        evidence_tag_object = _manifest_text(root["evidence_tag_object"])
        evidence_tag_commit = _manifest_text(root["evidence_tag_commit"])
        destination_repository = _manifest_text(root["destination_repository"])
        if (
            _HEX_SHA40.fullmatch(app_source_sha) is None
            or evidence_tag != "v0.2.0"
            or evidence_tag_object != "2f1ddb0e2276fa894e124b856de488e31e21e88c"
            or evidence_tag_commit != "f4c820cce953f401c1ec525bd8df3a3c1678bbf3"
            or destination_repository != "steven0226/carerisk-48h"
            or receipt.formal_metrics_sha256 != FORMAL_METRICS_SHA256
            or release.release != "v0.2.0"
        ):
            raise ContractViolation("deployment_manifest_invalid")
        _validate_base_images(root["base_images"])
        raw_files = root["files"]
        if not isinstance(raw_files, list):
            raise ContractViolation("deployment_manifest_invalid")
        files = tuple(
            _validate_manifest_file(
                value,
                app_source_sha=app_source_sha,
                evidence_tag_commit=evidence_tag_commit,
            )
            for value in raw_files
        )
        paths = tuple(item.destination_path for item in files)
        if paths != tuple(sorted(PUBLIC_PATHS)) or len(paths) != len(set(paths)):
            raise ContractViolation("deployment_manifest_invalid")
        by_path = {item.destination_path: item for item in files}
        for destination, supplied_raw in (
            ("evidence/final-result-receipt.json", receipt_raw),
            ("evidence/release-v0.2.0.json", release_raw),
        ):
            item = by_path[destination]
            if (
                item.sha256 != hashlib.sha256(supplied_raw).hexdigest()
                or item.byte_size != len(supplied_raw)
            ):
                raise ContractViolation("deployment_manifest_invalid")
        supply_chain = _manifest_object(root["supply_chain"], _SUPPLY_CHAIN_KEYS)
        for field, destination in _SUPPLY_CHAIN_FILE_RELATIONSHIPS.items():
            if _manifest_sha256(supply_chain[field]) != by_path[destination].sha256:
                raise ContractViolation("deployment_manifest_invalid")
        return DeploymentManifest(
            space_app_source_git_sha=app_source_sha,
            evidence_tag=evidence_tag,
            evidence_tag_object=evidence_tag_object,
            evidence_tag_commit=evidence_tag_commit,
            destination_repository=destination_repository,
            files=files,
        )
    except ContractViolation as exc:
        raise ContractViolation("deployment_manifest_invalid") from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractViolation("deployment_manifest_invalid") from exc


def format_evidence(
    receipt: ReceiptEvidence,
    release: ReleaseRelationship,
    manifest: DeploymentManifest,
) -> EvidenceViewModel:
    return EvidenceViewModel(receipt=receipt, release=release, manifest=manifest)


def load_evidence(bundle_root: Path) -> EvidenceLoadResult:
    try:
        receipt_raw = read_regular_file(bundle_root, "evidence/final-result-receipt.json")
    except FileNotFoundError:
        return EvidenceFailure("receipt_missing")
    try:
        receipt = validate_receipt(receipt_raw)
    except ReceiptHashMismatch:
        return EvidenceFailure("receipt_hash_mismatch")
    except ContractViolation:
        return EvidenceFailure("receipt_schema_invalid")
    try:
        release_raw = read_regular_file(bundle_root, "evidence/release-v0.2.0.json")
        release = validate_release(release_raw, receipt)
    except (FileNotFoundError, ContractViolation):
        return EvidenceFailure("release_relationship_invalid")
    try:
        manifest_raw = read_regular_file(bundle_root, "deployment-manifest.json")
        manifest = validate_deployment_manifest(
            manifest_raw,
            receipt_raw=receipt_raw,
            release_raw=release_raw,
            receipt=receipt,
            release=release,
        )
    except (FileNotFoundError, ContractViolation):
        return EvidenceFailure("deployment_manifest_invalid")
    return format_evidence(receipt, release, manifest)
