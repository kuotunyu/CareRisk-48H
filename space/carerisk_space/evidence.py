"""Fail-closed validation of the public v0.2.0 evidence objects."""
# The fixed schema key sets intentionally mirror the committed JSON objects.
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import math
from types import MappingProxyType
from typing import NoReturn, cast

from .contracts import (
    ContractViolation,
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
