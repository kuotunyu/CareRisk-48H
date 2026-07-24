from __future__ import annotations

from carerisk48h.model_selection import select_candidate


def _tabular() -> dict:
    metrics = {
        "auprc": {"mean": 0.40},
        "brier": {"mean": 0.12},
        "ece": {"mean": 0.04},
    }
    return {"selected_tabular_family": "lightgbm", "families": {"lightgbm": {"aggregate": metrics}}}


def test_deep_must_pass_all_simplicity_gate_checks() -> None:
    deep = {
        "model_family": "grud",
        "ensemble_metrics": {"auprc": 0.42, "brier": 0.13, "ece": 0.03},
    }
    decision = select_candidate(_tabular(), [deep])
    assert decision["selected"]["family"] == "lightgbm"
    assert not decision["deep_audit"][0]["checks"]["brier_not_worse"]


def test_deep_can_upgrade_when_all_checks_pass() -> None:
    deep = {
        "model_family": "tcn",
        "ensemble_metrics": {"auprc": 0.42, "brier": 0.11, "ece": 0.03},
    }
    assert select_candidate(_tabular(), [deep])["selected"]["family"] == "tcn"
