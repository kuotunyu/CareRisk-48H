# ruff: noqa: E501
import hashlib
import json
import subprocess
from dataclasses import replace
from pathlib import Path

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
