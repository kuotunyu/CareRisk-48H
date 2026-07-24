"""TreeSHAP artifacts for global and individual model sensitivity."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from carerisk48h.constants import TIME_SERIES_VARIABLES
from carerisk48h.data.parser import ParsedStay


def _positive_class_values(values: Any) -> np.ndarray:
    if isinstance(values, list):
        return np.asarray(values[-1])
    array = np.asarray(values)
    if array.ndim == 3:
        return array[:, :, -1]
    return array


def generate_tree_shap_artifacts(
    model: Pipeline,
    validation_frame: pd.DataFrame,
    *,
    output_dir: str | Path,
    seed: int,
    max_samples: int = 300,
) -> dict[str, str]:
    """Write bounded global, dependence, and individual TreeSHAP views."""
    try:
        import shap
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install CareRisk 48H with the 'tabular' extra") from exc
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    sample = validation_frame.sample(n=min(max_samples, len(validation_frame)), random_state=seed)
    preprocessor = model.named_steps["preprocessor"]
    classifier = model.named_steps["classifier"]
    matrix = np.asarray(preprocessor.transform(sample), dtype=np.float64)
    feature_names = [str(name) for name in preprocessor.get_feature_names_out()]
    explainer = shap.TreeExplainer(classifier)
    shap_values = _positive_class_values(explainer.shap_values(matrix))
    importance = np.mean(np.abs(shap_values), axis=0)
    order = np.argsort(importance)[::-1]
    pd.DataFrame(
        {"feature": np.asarray(feature_names)[order], "mean_abs_shap": importance[order]}
    ).to_csv(destination / "shap_global_importance.csv", index=False)

    shap.summary_plot(shap_values, matrix, feature_names=feature_names, show=False, max_display=20)
    plt.tight_layout()
    plt.savefig(destination / "shap_global_summary.png", dpi=160, bbox_inches="tight")
    plt.close()

    top_index = int(order[0])
    shap.dependence_plot(
        top_index,
        shap_values,
        matrix,
        feature_names=feature_names,
        interaction_index=None,
        show=False,
    )
    plt.tight_layout()
    plt.savefig(destination / "shap_dependence.png", dpi=160, bbox_inches="tight")
    plt.close()

    expected = explainer.expected_value
    if isinstance(expected, list | np.ndarray):
        expected_array = np.asarray(expected).reshape(-1)
        base_value = float(expected_array[-1])
    else:
        base_value = float(expected)
    explanation = shap.Explanation(
        values=shap_values[0],
        base_values=base_value,
        data=matrix[0],
        feature_names=feature_names,
    )
    shap.plots.waterfall(explanation, max_display=15, show=False)
    plt.tight_layout()
    plt.savefig(destination / "shap_individual_waterfall.png", dpi=160, bbox_inches="tight")
    plt.close()
    return {
        "global_importance": "shap_global_importance.csv",
        "global_summary": "shap_global_summary.png",
        "dependence": "shap_dependence.png",
        "individual_waterfall": "shap_individual_waterfall.png",
        "individual_row_index": str(int(sample.index[0])),
        "interpretation": "TreeSHAP attribution describes model output, not causal effect.",
    }


def variable_occlusion_sensitivity(
    predictor: Any, stay: ParsedStay, *, limit: int = 8
) -> list[dict[str, float | str]]:
    """Rank variables by probability change when their full sequence is hidden."""
    baseline = float(predictor(stay))
    sensitivities: list[dict[str, float | str]] = []
    for column, variable in enumerate(TIME_SERIES_VARIABLES):
        if not stay.mask[:, column].any():
            continue
        values = stay.values.copy()
        mask = stay.mask.copy()
        delta = stay.delta.copy()
        values[:, column] = np.nan
        mask[:, column] = False
        delta[:, column] = np.arange(1, len(delta) + 1, dtype=np.float32)
        observations = dict(stay.observations)
        observations[variable] = ()
        occluded = ParsedStay(
            stay.record_id,
            dict(stay.static),
            values,
            mask,
            delta,
            observations,
        )
        probability = float(predictor(occluded))
        sensitivities.append(
            {
                "variable": variable,
                "probability_change": baseline - probability,
                "absolute_change": abs(baseline - probability),
            }
        )
    sensitivities.sort(key=lambda item: float(item["absolute_change"]), reverse=True)
    return sensitivities[:limit]
