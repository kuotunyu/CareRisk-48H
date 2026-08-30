# ruff: noqa: E501
import hashlib
import json
import subprocess
from dataclasses import replace
from pathlib import Path

import carerisk_space.evidence as evidence_module
import pytest
from carerisk_space.contracts import ContractViolation
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


@pytest.mark.parametrize(
    "path",
    [
        ("schema_version",),
        ("dataset", "n"),
        ("dataset", "events"),
        ("dataset", "prevalence"),
        ("evaluation", "set_b_final_evaluation_successes"),
        ("evaluation", "bootstrap", "samples"),
        ("evaluation", "bootstrap", "seed"),
        ("model", "threshold"),
        ("metrics", "auroc"),
        ("confidence_intervals", "auroc", "estimate"),
    ],
)
def test_receipt_rejects_exponent_overflow_for_every_numeric_field(
    path: tuple[str, ...], monkeypatch: pytest.MonkeyPatch
) -> None:
    source = json.loads(receipt_raw())
    target = source
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = 1e9999
    raw = json.dumps(source).encode()
    monkeypatch.setattr(evidence_module, "RECEIPT_SHA256", hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(evidence_module, "RECEIPT_GIT_BLOB_SHA", git_blob_sha1(raw))
    with pytest.raises(ContractViolation, match="receipt_schema_invalid"):
        validate_receipt(raw)


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


@pytest.mark.parametrize("gate", range(1, 13))
def test_receipt_numbered_gate_mutations_are_rejected(
    gate: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = json.loads(receipt_raw())
    mutations = {
        1: lambda d: d.update({"_path": "not-a-runtime-object"}),
        2: lambda d: d["provenance"].update({"formal_metrics_sha256": "0" * 64}),
        3: lambda d: d["provenance"].update({"formal_metrics_sha256": "0" * 64}),
        4: lambda d: d.update({"title": "broken"}),
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
    raw = json.dumps(source, allow_nan=False).encode()
    if gate == 4:
        raw += b" trailing"
    monkeypatch.setattr(evidence_module, "RECEIPT_SHA256", hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(evidence_module, "RECEIPT_GIT_BLOB_SHA", git_blob_sha1(raw))
    with pytest.raises(ContractViolation, match="receipt_schema_invalid"):
        validate_receipt(raw)


@pytest.mark.parametrize("gate", range(1, 7))
def test_release_numbered_gate_mutations_are_rejected(gate: int) -> None:
    source = json.loads(release_raw())
    mutations = {
        1: lambda d: d.update({"release": "broken"}),
        2: lambda d: d.update({"schema_version": 2}),
        3: lambda d: d["scientific_evidence"].update({"final_result_receipt": "wrong"}),
        4: lambda d: d["scientific_evidence"].update(
            {"final_result_receipt_git_blob_sha": "0" * 40}
        ),
        5: lambda d: d["scientific_evidence"].update({"set_c_used": True}),
        6: lambda d: d.update({"limitations": []}),
    }
    mutations[gate](source)
    with pytest.raises(ContractViolation):
        validate_release(json.dumps(source).encode(), validate_receipt(receipt_raw()))
