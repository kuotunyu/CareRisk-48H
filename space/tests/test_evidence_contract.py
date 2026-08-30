# ruff: noqa: E501
import hashlib
import json
import subprocess
from dataclasses import fields, replace
from pathlib import Path
from typing import get_args

import carerisk_space.contracts as contracts_module
import carerisk_space.evidence as evidence_module
import pytest
from carerisk_space.contracts import ContractViolation, ReceiptHashMismatch
from carerisk_space.evidence import (
    FORMAL_METRICS_SHA256,
    RECEIPT_GIT_BLOB_SHA,
    RECEIPT_SHA256,
    git_blob_sha1,
    loads_strict_object,
    validate_receipt,
    validate_release,
)

SPACE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = SPACE_ROOT.parent


def source_or_bundled_evidence(name: str) -> Path:
    bundled = SPACE_ROOT / "evidence" / name
    if bundled.is_file():
        return bundled
    source = SOURCE_ROOT / "docs" / name
    if not source.is_file():
        raise AssertionError(f"missing public evidence fixture: {name}")
    return source


def receipt_raw() -> bytes:
    bundled = SPACE_ROOT / "evidence" / "final-result-receipt.json"
    if bundled.is_file():
        return bundled.read_bytes()
    return subprocess.check_output(
        ["git", "cat-file", "blob", RECEIPT_GIT_BLOB_SHA], cwd=SOURCE_ROOT
    )


def release_raw() -> bytes:
    bundled = SPACE_ROOT / "evidence" / "release-v0.2.0.json"
    if bundled.is_file():
        return bundled.read_bytes()
    release_blob = (
        subprocess.check_output(
            ["git", "rev-parse", "v0.2.0:docs/release-v0.2.0.json"], cwd=SOURCE_ROOT
        )
        .strip()
        .decode()
    )
    return subprocess.check_output(["git", "cat-file", "blob", release_blob], cwd=SOURCE_ROOT)


def test_receipt_rejects_duplicate_json_keys() -> None:
    with pytest.raises(ContractViolation, match="receipt_schema_invalid"):
        loads_strict_object(b'{"schema_version":1,"schema_version":1}')


@pytest.mark.parametrize("token", [b"NaN", b"Infinity", b"-Infinity"])
def test_receipt_rejects_nonfinite_json_constants(token: bytes) -> None:
    raw = b'{"schema_version":' + token + b"}"
    with pytest.raises(ContractViolation, match="receipt_schema_invalid"):
        loads_strict_object(raw)


def test_strict_parser_rejects_nested_duplicate_and_trailing_bytes() -> None:
    with pytest.raises(ContractViolation, match="receipt_schema_invalid"):
        loads_strict_object(b'{"nested":{"x":1,"x":2}}')
    with pytest.raises(ContractViolation, match="receipt_schema_invalid"):
        loads_strict_object(b'{"schema_version":1} trailing')


def test_exact_committed_receipt_hash_and_git_blob() -> None:
    raw = receipt_raw()
    assert hashlib.sha256(raw).hexdigest() == RECEIPT_SHA256
    assert git_blob_sha1(raw) == RECEIPT_GIT_BLOB_SHA


def test_receipt_schema_is_exact() -> None:
    evidence = validate_receipt(receipt_raw())
    assert evidence.dataset_name == "PhysioNet Challenge 2012 Set B"
    assert evidence.dataset_role == "final_test"
    assert evidence.formal_metrics_sha256 == FORMAL_METRICS_SHA256


@pytest.mark.parametrize("field", ["name", "title", "use_limitation"])
def test_receipt_text_fields_require_strings(field: str, monkeypatch: pytest.MonkeyPatch) -> None:
    source = json.loads(receipt_raw())
    if field in source["dataset"]:
        source["dataset"][field] = 3
    else:
        source[field] = 3
    raw = json.dumps(source).encode()
    monkeypatch.setattr(evidence_module, "RECEIPT_SHA256", hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(evidence_module, "RECEIPT_GIT_BLOB_SHA", git_blob_sha1(raw))
    with pytest.raises(ContractViolation, match="receipt_schema_invalid"):
        validate_receipt(raw)


def test_receipt_model_schema_and_types_are_exact(monkeypatch: pytest.MonkeyPatch) -> None:
    source = json.loads(receipt_raw())
    source["model"]["family"] = 3
    raw = json.dumps(source).encode()
    monkeypatch.setattr(evidence_module, "RECEIPT_SHA256", hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(evidence_module, "RECEIPT_GIT_BLOB_SHA", git_blob_sha1(raw))
    with pytest.raises(ContractViolation, match="receipt_schema_invalid"):
        validate_receipt(raw)


_CONSUMED_NUMERIC_OVERFLOW_CASES = (
    ("schema_version", b'"schema_version": 1,', b"1"),
    ("dataset.events", b'"events": 568,', b"568"),
    ("dataset.n", b'"n": 4000,', b"4000"),
    ("dataset.prevalence", b'"prevalence": 0.142,', b"0.142"),
    (
        "evaluation.set_b_final_evaluation_successes",
        b'"set_b_final_evaluation_successes": 1',
        b"1",
    ),
    ("evaluation.bootstrap.samples", b'"samples": 2000,', b"2000"),
    ("evaluation.bootstrap.seed", b'"seed": 2026', b"2026"),
    ("model.seeds[0]", b"      17,", b"17"),
    ("model.seeds[1]", b"      42,", b"42"),
    ("model.seeds[2]", b"      2026\n", b"2026"),
    ("model.threshold", b'"threshold": 0.2974276505509685', b"0.2974276505509685"),
    ("metrics.auprc", b'"auprc": 0.5549611311053255,', b"0.5549611311053255"),
    ("metrics.auroc", b'"auroc": 0.8696003233855347,', b"0.8696003233855347"),
    ("metrics.brier", b'"brier": 0.08662893958425562,', b"0.08662893958425562"),
    ("metrics.ece", b'"ece": 0.007835639822692777,', b"0.007835639822692777"),
    (
        "confidence_intervals.auprc.estimate",
        b'"auprc": {\n      "estimate": 0.5549611311053255,',
        b"0.5549611311053255",
    ),
    (
        "confidence_intervals.auprc.lower",
        b'"lower": 0.5159391486187543,',
        b"0.5159391486187543",
    ),
    (
        "confidence_intervals.auprc.upper",
        b'"upper": 0.5941855615749009',
        b"0.5941855615749009",
    ),
    (
        "confidence_intervals.auroc.estimate",
        b'"auroc": {\n      "estimate": 0.8696003233855347,',
        b"0.8696003233855347",
    ),
    (
        "confidence_intervals.auroc.lower",
        b'"lower": 0.8547766823845169,',
        b"0.8547766823845169",
    ),
    (
        "confidence_intervals.auroc.upper",
        b'"upper": 0.8836828041383498',
        b"0.8836828041383498",
    ),
    (
        "confidence_intervals.brier.estimate",
        b'"brier": {\n      "estimate": 0.08662893958425562,',
        b"0.08662893958425562",
    ),
    (
        "confidence_intervals.brier.lower",
        b'"lower": 0.08294065055139704,',
        b"0.08294065055139704",
    ),
    (
        "confidence_intervals.brier.upper",
        b'"upper": 0.09036869670238311',
        b"0.09036869670238311",
    ),
    (
        "confidence_intervals.ece.estimate",
        b'"ece": {\n      "estimate": 0.007835639822692777,',
        b"0.007835639822692777",
    ),
    (
        "confidence_intervals.ece.lower",
        b'"lower": 0.006992943602957658,',
        b"0.006992943602957658",
    ),
    (
        "confidence_intervals.ece.upper",
        b'"upper": 0.019300500350357373',
        b"0.019300500350357373",
    ),
)


@pytest.mark.parametrize(
    ("field_path", "needle", "source_token"),
    _CONSUMED_NUMERIC_OVERFLOW_CASES,
    ids=[case[0] for case in _CONSUMED_NUMERIC_OVERFLOW_CASES],
)
def test_each_consumed_receipt_numeric_leaf_rejects_lexical_exponent_overflow(
    field_path: str,
    needle: bytes,
    source_token: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = receipt_raw()
    assert raw.count(needle) == 1
    assert needle.count(source_token) == 1
    raw = raw.replace(needle, needle.replace(source_token, b"1e9999", 1), 1)
    assert b"1e9999" in raw and b"Infinity" not in raw
    monkeypatch.setattr(evidence_module, "RECEIPT_SHA256", hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(evidence_module, "RECEIPT_GIT_BLOB_SHA", git_blob_sha1(raw))
    with pytest.raises(ContractViolation, match="receipt_schema_invalid") as exc_info:
        validate_receipt(raw)
    assert exc_info.value.args == ("receipt_schema_invalid",), field_path


@pytest.mark.parametrize(
    "raw",
    [b"{", b'{} trailing', b'{"x": 1, "x": 2}', b"\xff", b"[]"],
)
def test_release_parse_failures_use_release_relationship_code(raw: bytes) -> None:
    receipt = validate_receipt(receipt_raw())
    with pytest.raises(ContractViolation, match="release_relationship_invalid"):
        validate_release(raw, receipt)


def test_receipt_metrics_and_intervals_are_finite_and_ordered() -> None:
    evidence = validate_receipt(receipt_raw())
    assert set(evidence.metrics) == {"auprc", "auroc", "brier", "ece"}
    for metric in evidence.metrics.values():
        assert 0 <= metric.lower <= metric.estimate <= metric.upper <= 1


def test_receipt_privacy_exclusions_are_exact() -> None:
    source = json.loads(receipt_raw())
    assert source["privacy"]["excluded"] == [
        "record_identifiers",
        "raw_outcomes",
        "individual_predictions",
        "model_artifacts",
        "subgroup_rows",
        "environment_details",
        "access_ledger_contents",
    ]
    assert set(validate_receipt(receipt_raw()).metrics) == {"auprc", "auroc", "brier", "ece"}


def test_release_relationship_is_exact() -> None:
    receipt = validate_receipt(receipt_raw())
    relationship = validate_release(release_raw(), receipt)
    assert relationship.release == "v0.2.0"
    assert relationship.scientific_change_flags == {
        "scientific_result_changed": False,
        "set_b_rerun": False,
        "set_c_used": False,
        "frozen_model_changed": False,
        "threshold_changed": False,
    }
    assert relationship.limitations == (
        "no external validation",
        "no temporal or site-held-out validation",
        "no prospective validation",
        "no clinical utility study",
        "historical same-source ICU cohort",
    )


def test_release_requires_supplied_validated_receipt_relationship() -> None:
    receipt = validate_receipt(receipt_raw())
    mismatched = replace(receipt, dataset_name="other")
    with pytest.raises(ContractViolation, match="release_relationship_invalid"):
        validate_release(release_raw(), mismatched)


def test_release_nested_schema_uses_bounded_failure_code() -> None:
    source = json.loads(release_raw())
    source["scientific_evidence"] = {"broken": True}
    with pytest.raises(ContractViolation, match="release_relationship_invalid"):
        validate_release(json.dumps(source).encode(), validate_receipt(receipt_raw()))


def test_validated_mappings_are_deeply_immutable() -> None:
    receipt = validate_receipt(receipt_raw())
    with pytest.raises(TypeError):
        receipt.metrics["new"] = receipt.metrics["auroc"]  # type: ignore[index]
    release = validate_release(release_raw(), receipt)
    with pytest.raises(TypeError):
        release.scientific_change_flags["new"] = True  # type: ignore[index]


def _controlled_receipt(raw: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(evidence_module, "RECEIPT_SHA256", hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(evidence_module, "RECEIPT_GIT_BLOB_SHA", git_blob_sha1(raw))


def test_receipt_gate_2_keeps_both_canonical_anchors() -> None:
    raw = receipt_raw().replace(b'"title":', b'"titel":', 1)
    with pytest.raises(ReceiptHashMismatch, match="receipt_hash_mismatch"):
        validate_receipt(raw)


def test_receipt_gate_3_patches_only_sha(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = receipt_raw().replace(b'"title":', b'"titel":', 1)
    monkeypatch.setattr(evidence_module, "RECEIPT_SHA256", hashlib.sha256(raw).hexdigest())
    with pytest.raises(ReceiptHashMismatch, match="receipt_hash_mismatch"):
        validate_receipt(raw)


@pytest.mark.parametrize("gate", range(4, 13))
def test_receipt_downstream_gates_use_both_controlled_anchors(
    gate: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = json.loads(receipt_raw())
    mutations = {
        4: lambda d: None,
        5: lambda d: d.update({"extra": True}),
        6: lambda d: d.update({"schema_version": 2}),
        7: lambda d: d["evaluation"].update({"final_lock_status": "unlocked"}),
        8: lambda d: d["confidence_intervals"]["auroc"].update({"lower": 2}),
        9: lambda d: d["dataset"].update({"n": 1}),
        10: lambda d: d["evaluation"]["bootstrap"].update({"samples": 1}),
        11: lambda d: d["provenance"].update({"formal_metrics_sha256": "0" * 64}),
        12: lambda d: d["privacy"].update({"excluded": []}),
    }
    mutations[gate](source)
    raw = json.dumps(source).encode() + (b" trailing" if gate == 4 else b"")
    _controlled_receipt(raw, monkeypatch)
    with pytest.raises(ContractViolation, match="receipt_schema_invalid"):
        validate_receipt(raw)


_OWNED_RELEASE_GATE_MUTATIONS = (
    (2, "schema_version", 2),
    (2, "release", "broken"),
    (2, "release_kind", "broken"),
    (3, "scientific_evidence.final_result_receipt", "wrong"),
    (4, "scientific_evidence.final_result_receipt_git_blob_sha", "0" * 40),
    (5, "scientific_evidence.scientific_result_changed", True),
    (5, "scientific_evidence.set_b_rerun", True),
    (5, "scientific_evidence.set_c_used", True),
    (5, "scientific_evidence.frozen_model_changed", True),
    (5, "scientific_evidence.threshold_changed", True),
    (6, "limitations", []),
)


@pytest.mark.parametrize(
    ("gate", "field_path", "invalid_value"),
    _OWNED_RELEASE_GATE_MUTATIONS,
    ids=[f"gate-{case[0]}-{case[1]}" for case in _OWNED_RELEASE_GATE_MUTATIONS],
)
def test_release_owned_gates_2_through_6_reject_each_relationship_mutation(
    gate: int, field_path: str, invalid_value: object
) -> None:
    source = json.loads(release_raw())
    if field_path.startswith("scientific_evidence."):
        nested_field = field_path.removeprefix("scientific_evidence.")
        source["scientific_evidence"][nested_field] = invalid_value
    else:
        source[field_path] = invalid_value
    with pytest.raises(ContractViolation, match="release_relationship_invalid") as exc_info:
        validate_release(json.dumps(source).encode(), validate_receipt(receipt_raw()))
    assert exc_info.value.args == ("release_relationship_invalid",), gate


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

_APP_SOURCE_SHA = "a" * 40
_TAG_COMMIT = "f4c820cce953f401c1ec525bd8df3a3c1678bbf3"
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


def valid_manifest_bytes(receipt_bytes: bytes, release_bytes: bytes) -> bytes:
    hashes = {
        path: hashlib.sha256(("fixture:" + path).encode()).hexdigest()
        for path in EXPECTED_PUBLIC_PATHS
    }
    sizes = {path: len(("fixture:" + path).encode()) for path in EXPECTED_PUBLIC_PATHS}
    hashes["evidence/final-result-receipt.json"] = hashlib.sha256(receipt_bytes).hexdigest()
    sizes["evidence/final-result-receipt.json"] = len(receipt_bytes)
    hashes["evidence/release-v0.2.0.json"] = hashlib.sha256(release_bytes).hexdigest()
    sizes["evidence/release-v0.2.0.json"] = len(release_bytes)
    files = []
    for path in sorted(EXPECTED_PUBLIC_PATHS):
        is_manifest = path == "deployment-manifest.json"
        is_tag_file = path in {
            "evidence/final-result-receipt.json",
            "evidence/release-v0.2.0.json",
            "LICENSE",
            "NOTICE",
            "CITATION.cff",
        }
        files.append(
            {
                "source_ref": (
                    "export-manifest-commit"
                    if is_manifest
                    else _TAG_COMMIT
                    if is_tag_file
                    else _APP_SOURCE_SHA
                ),
                "source_path": _SOURCE_PATHS[path],
                "destination_path": path,
                "sha256": None if is_manifest else hashes[path],
                "byte_size": None if is_manifest else sizes[path],
                "media_type": _media_type(path),
                "capability": _CAPABILITIES[path],
            }
        )
    manifest = {
        "schema_version": 1,
        "space_app_source_git_sha": _APP_SOURCE_SHA,
        "evidence_tag": "v0.2.0",
        "evidence_tag_object": "2f1ddb0e2276fa894e124b856de488e31e21e88c",
        "evidence_tag_commit": _TAG_COMMIT,
        "destination_repository": "steven0226/carerisk-48h",
        "base_images": {
            "runtime": {
                "repository": "docker.io/library/python",
                "tag": "3.11.9-slim-bookworm",
                "index_digest": "sha256:" + "1" * 64,
                "linux_amd64_digest": "sha256:" + "2" * 64,
            },
            "reviewer": {
                "repository": "mcr.microsoft.com/playwright/python",
                "tag": "v1.55.0-noble",
                "index_digest": "sha256:" + "3" * 64,
                "linux_amd64_digest": "sha256:" + "4" * 64,
            },
        },
        "supply_chain": {
            "runtime_lock_sha256": hashes["requirements.lock"],
            "development_lock_sha256": hashes["requirements-dev.lock"],
            "sbom_sha256": hashes["SBOM.spdx.json"],
            "third_party_licenses_sha256": hashes["THIRD_PARTY_LICENSES.json"],
        },
        "files": files,
    }
    return (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()


@pytest.fixture
def candidate_bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / "candidate"
    evidence_dir = bundle / "evidence"
    evidence_dir.mkdir(parents=True)
    receipt_bytes = receipt_raw()
    release_bytes = release_raw()
    (evidence_dir / "final-result-receipt.json").write_bytes(receipt_bytes)
    (evidence_dir / "release-v0.2.0.json").write_bytes(release_bytes)
    (bundle / "deployment-manifest.json").write_bytes(
        valid_manifest_bytes(receipt_bytes, release_bytes)
    )
    return bundle


def _rewrite_manifest(bundle: Path, mutation: object) -> None:
    path = bundle / "deployment-manifest.json"
    manifest = json.loads(path.read_bytes())
    assert callable(mutation)
    mutation(manifest)
    path.write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _manifest_entry(manifest: dict[str, object], destination: str) -> dict[str, object]:
    files = manifest["files"]
    assert isinstance(files, list)
    return next(item for item in files if item["destination_path"] == destination)


def test_public_paths_are_one_exact_24_entry_application_constant() -> None:
    assert contracts_module.PUBLIC_PATHS == EXPECTED_PUBLIC_PATHS
    assert len(contracts_module.PUBLIC_PATHS) == len(set(contracts_module.PUBLIC_PATHS)) == 24


def test_normal_state_returns_receipt_backed_view(candidate_bundle: Path) -> None:
    result = evidence_module.load_evidence(candidate_bundle)
    assert isinstance(result, contracts_module.EvidenceViewModel)
    assert set(result.receipt.metrics) == {"auprc", "auroc", "brier", "ece"}
    assert result.manifest.destination_repository == "steven0226/carerisk-48h"


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("remove_receipt", "receipt_missing"),
        ("change_receipt_byte", "receipt_hash_mismatch"),
        ("duplicate_receipt_key", "receipt_schema_invalid"),
        ("change_release_flag", "release_relationship_invalid"),
        ("change_manifest_source_sha", "deployment_manifest_invalid"),
    ],
)
def test_evidence_failure_reason_is_bounded(
    candidate_bundle: Path,
    mutation: str,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_path = candidate_bundle / "evidence" / "final-result-receipt.json"
    release_path = candidate_bundle / "evidence" / "release-v0.2.0.json"
    if mutation == "remove_receipt":
        receipt_path.unlink()
    elif mutation == "change_receipt_byte":
        receipt_path.write_bytes(receipt_path.read_bytes().replace(b'"title":', b'"titel":', 1))
    elif mutation == "duplicate_receipt_key":
        raw = receipt_path.read_bytes().replace(
            b'"schema_version": 1,', b'"schema_version": 1,\n  "schema_version": 1,', 1
        )
        receipt_path.write_bytes(raw)
        monkeypatch.setattr(evidence_module, "RECEIPT_SHA256", hashlib.sha256(raw).hexdigest())
        monkeypatch.setattr(evidence_module, "RECEIPT_GIT_BLOB_SHA", git_blob_sha1(raw))
    elif mutation == "change_release_flag":
        release = json.loads(release_path.read_bytes())
        release["scientific_evidence"]["set_b_rerun"] = True
        release_path.write_text(json.dumps(release), encoding="utf-8")
    elif mutation == "change_manifest_source_sha":
        _rewrite_manifest(candidate_bundle, lambda value: value.update(space_app_source_git_sha="b" * 40))
    else:
        raise AssertionError(mutation)
    result = evidence_module.load_evidence(candidate_bundle)
    assert result == contracts_module.EvidenceFailure(expected)
    assert tuple(field.name for field in fields(result)) == ("code",)


def test_failure_code_type_has_exactly_five_bounded_values() -> None:
    assert get_args(contracts_module.EvidenceFailureCode) == (
        "receipt_missing",
        "receipt_hash_mismatch",
        "receipt_schema_invalid",
        "release_relationship_invalid",
        "deployment_manifest_invalid",
    )


@pytest.mark.parametrize(
    ("relative_path", "expected_code"),
    [
        ("evidence/final-result-receipt.json", "receipt_missing"),
        ("evidence/release-v0.2.0.json", "release_relationship_invalid"),
        ("deployment-manifest.json", "deployment_manifest_invalid"),
    ],
)
@pytest.mark.parametrize("kind", ["missing", "non_regular", "symlink"])
def test_each_literal_evidence_path_rejects_missing_nonregular_and_symlink(
    candidate_bundle: Path, relative_path: str, expected_code: str, kind: str
) -> None:
    target = candidate_bundle / relative_path
    original = target.read_bytes()
    target.unlink()
    if kind == "non_regular":
        target.mkdir()
    elif kind == "symlink":
        symlink_target = candidate_bundle / ("symlink-target-" + target.name)
        symlink_target.write_bytes(original)
        try:
            target.symlink_to(symlink_target)
        except OSError as exc:
            if getattr(exc, "winerror", None) == 1314:
                pytest.skip("Windows account lacks symlink creation privilege")
            raise
    result = evidence_module.load_evidence(candidate_bundle)
    assert result == contracts_module.EvidenceFailure(expected_code)


@pytest.mark.parametrize(
    ("destination", "field"),
    [
        ("evidence/final-result-receipt.json", "sha256"),
        ("evidence/final-result-receipt.json", "byte_size"),
        ("evidence/release-v0.2.0.json", "sha256"),
        ("evidence/release-v0.2.0.json", "byte_size"),
    ],
)
def test_manifest_receipt_and_release_hash_size_mutations_fail_closed(
    candidate_bundle: Path, destination: str, field: str
) -> None:
    def mutate(manifest: dict[str, object]) -> None:
        entry = _manifest_entry(manifest, destination)
        entry[field] = "0" * 64 if field == "sha256" else int(entry[field]) + 1

    _rewrite_manifest(candidate_bundle, mutate)
    assert evidence_module.load_evidence(candidate_bundle) == contracts_module.EvidenceFailure(
        "deployment_manifest_invalid"
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "extra_top_key",
        "wrong_tag",
        "wrong_tag_object",
        "wrong_tag_commit",
        "wrong_destination_repository",
        "wrong_source_ref",
        "wrong_source_path",
        "wrong_media_type",
        "wrong_capability",
        "wrong_runtime_repository",
        "mutable_runtime_tag",
        "wrong_reviewer_digest",
        "wrong_runtime_lock_hash",
        "wrong_development_lock_hash",
        "wrong_sbom_hash",
        "wrong_license_hash",
        "self_hashed_manifest",
    ],
)
def test_each_deployment_manifest_relationship_mutation_fails_closed(
    candidate_bundle: Path, mutation: str
) -> None:
    def mutate(manifest: dict[str, object]) -> None:
        if mutation == "extra_top_key":
            manifest["unexpected"] = True
        elif mutation == "wrong_tag":
            manifest["evidence_tag"] = "v0.2.1"
        elif mutation == "wrong_tag_object":
            manifest["evidence_tag_object"] = "0" * 40
        elif mutation == "wrong_tag_commit":
            manifest["evidence_tag_commit"] = "0" * 40
        elif mutation == "wrong_destination_repository":
            manifest["destination_repository"] = "other/repository"
        elif mutation == "wrong_source_ref":
            _manifest_entry(manifest, "README.md")["source_ref"] = "0" * 40
        elif mutation == "wrong_source_path":
            _manifest_entry(manifest, "README.md")["source_path"] = "README.md"
        elif mutation == "wrong_media_type":
            _manifest_entry(manifest, "README.md")["media_type"] = "text/plain"
        elif mutation == "wrong_capability":
            _manifest_entry(manifest, "README.md")["capability"] = "runtime_code"
        elif mutation == "wrong_runtime_repository":
            manifest["base_images"]["runtime"]["repository"] = "example.invalid/python"
        elif mutation == "mutable_runtime_tag":
            manifest["base_images"]["runtime"]["tag"] = "3.11-slim-bookworm"
        elif mutation == "wrong_reviewer_digest":
            manifest["base_images"]["reviewer"]["linux_amd64_digest"] = "sha256:latest"
        elif mutation.startswith("wrong_") and mutation.endswith("_hash"):
            fields_by_mutation = {
                "wrong_runtime_lock_hash": "runtime_lock_sha256",
                "wrong_development_lock_hash": "development_lock_sha256",
                "wrong_sbom_hash": "sbom_sha256",
                "wrong_license_hash": "third_party_licenses_sha256",
            }
            manifest["supply_chain"][fields_by_mutation[mutation]] = "0" * 64
        elif mutation == "self_hashed_manifest":
            entry = _manifest_entry(manifest, "deployment-manifest.json")
            entry["sha256"] = "0" * 64
            entry["byte_size"] = 1
        else:
            raise AssertionError(mutation)

    _rewrite_manifest(candidate_bundle, mutate)
    assert evidence_module.load_evidence(candidate_bundle) == contracts_module.EvidenceFailure(
        "deployment_manifest_invalid"
    )


@pytest.mark.parametrize("suffix", [b" trailing", b'\n{"schema_version":1}'])
def test_manifest_trailing_data_maps_to_bounded_failure(
    candidate_bundle: Path, suffix: bytes
) -> None:
    path = candidate_bundle / "deployment-manifest.json"
    path.write_bytes(path.read_bytes() + suffix)
    assert evidence_module.load_evidence(candidate_bundle) == contracts_module.EvidenceFailure(
        "deployment_manifest_invalid"
    )


def test_manifest_nested_duplicate_key_maps_to_bounded_failure(candidate_bundle: Path) -> None:
    path = candidate_bundle / "deployment-manifest.json"
    raw = path.read_bytes()
    needle = b'"runtime_lock_sha256":"'
    assert raw.count(needle) == 1
    raw = raw.replace(needle, b'"runtime_lock_sha256":"0","runtime_lock_sha256":"', 1)
    path.write_bytes(raw)
    assert evidence_module.load_evidence(candidate_bundle) == contracts_module.EvidenceFailure(
        "deployment_manifest_invalid"
    )


@pytest.mark.parametrize("value", ["../README.md", "README.md", "/tmp/evidence.json"])
def test_regular_file_reader_rejects_every_nonliteral_path(
    candidate_bundle: Path, value: str
) -> None:
    with pytest.raises(ContractViolation, match="deployment_manifest_invalid"):
        evidence_module.read_regular_file(candidate_bundle, value)  # type: ignore[arg-type]


def test_manifest_rejects_unsorted_duplicate_or_extra_paths(candidate_bundle: Path) -> None:
    mutations = (
        lambda manifest: manifest["files"].reverse(),
        lambda manifest: manifest["files"].append(manifest["files"][0]),
        lambda manifest: manifest["files"].append(
            {
                **manifest["files"][0],
                "destination_path": "extra.txt",
                "source_path": "space/extra.txt",
            }
        ),
    )
    for index, mutation in enumerate(mutations):
        bundle = candidate_bundle if index == 0 else candidate_bundle.parent / f"case-{index}"
        if index:
            evidence_dir = bundle / "evidence"
            evidence_dir.mkdir(parents=True)
            receipt_bytes = receipt_raw()
            release_bytes = release_raw()
            (evidence_dir / "final-result-receipt.json").write_bytes(receipt_bytes)
            (evidence_dir / "release-v0.2.0.json").write_bytes(release_bytes)
            (bundle / "deployment-manifest.json").write_bytes(
                valid_manifest_bytes(receipt_bytes, release_bytes)
            )
        _rewrite_manifest(bundle, mutation)
        assert evidence_module.load_evidence(bundle) == contracts_module.EvidenceFailure(
            "deployment_manifest_invalid"
        )


def test_failure_objects_never_expose_path_exception_or_submitted_value(
    candidate_bundle: Path,
) -> None:
    receipt_path = candidate_bundle / "evidence" / "final-result-receipt.json"
    receipt_path.unlink()
    result = evidence_module.load_evidence(candidate_bundle)
    rendered = repr(result)
    assert "final-result-receipt" not in rendered
    assert str(candidate_bundle) not in rendered
    assert "FileNotFoundError" not in rendered
