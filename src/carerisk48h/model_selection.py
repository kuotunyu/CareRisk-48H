"""Pre-registered simplicity-aware candidate selection."""

from __future__ import annotations

from typing import Any


def select_candidate(
    tabular_payload: dict[str, Any], deep_payloads: list[dict[str, Any]]
) -> dict[str, Any]:
    """Apply the 0.01 AUPRC and non-inferior Brier/ECE deep-model gate."""
    family = str(tabular_payload["selected_tabular_family"])
    tabular = tabular_payload["families"][family]["aggregate"]
    reference_auprc = float(tabular["auprc"]["mean"])
    reference_brier = float(tabular["brier"]["mean"])
    reference_ece = float(tabular["ece"]["mean"])
    reference: dict[str, Any] = {
        "family": family,
        "auprc": reference_auprc,
        "brier": reference_brier,
        "ece": reference_ece,
    }
    eligible: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    for payload in deep_payloads:
        metrics = payload["ensemble_metrics"]
        candidate_auprc = float(metrics["auprc"])
        candidate_brier = float(metrics["brier"])
        candidate_ece = float(metrics["ece"])
        candidate: dict[str, Any] = {
            "family": str(payload["model_family"]),
            "auprc": candidate_auprc,
            "brier": candidate_brier,
            "ece": candidate_ece,
        }
        checks = {
            "auprc_gain_at_least_0_01": candidate_auprc >= reference_auprc + 0.01,
            "brier_not_worse": candidate_brier <= reference_brier,
            "ece_not_worse": candidate_ece <= reference_ece,
        }
        audits.append({**candidate, "checks": checks})
        if all(checks.values()):
            eligible.append(candidate)
    selected = max(eligible, key=lambda item: item["auprc"]) if eligible else reference
    return {
        "selected": selected,
        "tabular_reference": reference,
        "deep_audit": audits,
        "rule": "Deep requires >=0.01 absolute AUPRC gain and no Brier/ECE worsening.",
    }
