"""Fail-closed inference for tabular research bundles."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from carerisk48h.data.parser import ParsedStay
from carerisk48h.features.tabular import build_feature_frame
from carerisk48h.guard import QualityOODGuard
from carerisk48h.schema import validate_inference_payload

DISCLAIMER = "研究與教育用途，非臨床診斷或照護決策工具"


@dataclass(frozen=True)
class SafePrediction:
    allow_probability: bool
    requires_human_review: bool
    message: str
    raw_probability: float | None
    calibrated_probability: float | None
    threshold: float | None
    above_threshold: bool | None
    contributors: list[dict[str, float | str]]
    guard: dict[str, Any]
    disclaimer: str = DISCLAIMER


def _models(bundle: dict[str, Any]) -> list[Any]:
    if "models" in bundle:
        return list(bundle["models"])
    if "model" in bundle:
        return [bundle["model"]]
    raise ValueError("bundle does not contain a model or ensemble")


def _logistic_contributors(
    model: Any, frame: Any, *, limit: int = 8
) -> list[dict[str, float | str]]:
    preprocessor = model.named_steps["preprocessor"]
    classifier = model.named_steps["classifier"]
    matrix = np.asarray(preprocessor.transform(frame), dtype=np.float64)[0]
    names = preprocessor.get_feature_names_out()
    contribution = matrix * np.asarray(classifier.coef_)[0]
    order = np.argsort(np.abs(contribution))[::-1][:limit]
    return [
        {"feature": str(names[index]), "contribution": float(contribution[index])}
        for index in order
    ]


def _lightgbm_contributors(
    model: Any, frame: Any, *, limit: int = 8
) -> list[dict[str, float | str]]:
    try:
        import shap
    except ImportError:
        return [{"feature": "TreeSHAP unavailable", "contribution": 0.0}]
    preprocessor = model.named_steps["preprocessor"]
    classifier = model.named_steps["classifier"]
    matrix = np.asarray(preprocessor.transform(frame), dtype=np.float64)
    values = shap.TreeExplainer(classifier).shap_values(matrix)
    if isinstance(values, list):
        shap_row = np.asarray(values[-1])[0]
    else:
        array = np.asarray(values)
        shap_row = array[0, :, -1] if array.ndim == 3 else array[0]
    names = preprocessor.get_feature_names_out()
    order = np.argsort(np.abs(shap_row))[::-1][:limit]
    return [
        {"feature": str(names[index]), "contribution": float(shap_row[index])} for index in order
    ]


def predict_stay(bundle: dict[str, Any], stay: ParsedStay) -> SafePrediction:
    guard = bundle.get("guard")
    if not isinstance(guard, QualityOODGuard):
        assessment = {
            "allow_probability": False,
            "requires_human_review": True,
            "reasons": ["validated quality/OOD guard is unavailable"],
        }
    else:
        assessment = guard.assess(stay)
    if not assessment["allow_probability"]:
        return SafePrediction(
            allow_probability=False,
            requires_human_review=True,
            message="資料品質不足，需要人工複核",
            raw_probability=None,
            calibrated_probability=None,
            threshold=None,
            above_threshold=None,
            contributors=[],
            guard=assessment,
        )
    family = str(bundle.get("model_family", "logistic"))
    include_slope = family == "lightgbm"
    feature_frame = build_feature_frame([stay], include_slope=include_slope).drop(
        columns="RecordID"
    )
    feature_columns = list(bundle["feature_columns"])
    feature_frame = feature_frame.loc[:, feature_columns]
    models = _models(bundle)
    probabilities = [float(model.predict_proba(feature_frame)[0, 1]) for model in models]
    raw_probability = float(np.mean(probabilities))
    calibrator = bundle.get("calibrator")
    calibrated = (
        float(calibrator.predict(np.asarray([raw_probability]))[0])
        if calibrator is not None
        else raw_probability
    )
    threshold = float(bundle.get("threshold", 0.5))
    contributors = (
        _lightgbm_contributors(models[0], feature_frame)
        if family == "lightgbm"
        else _logistic_contributors(models[0], feature_frame)
    )
    return SafePrediction(
        allow_probability=True,
        requires_human_review=False,
        message="通過輸入品質檢查；機率仍僅供研究與教育。",
        raw_probability=raw_probability,
        calibrated_probability=calibrated,
        threshold=threshold,
        above_threshold=calibrated >= threshold,
        contributors=contributors,
        guard=assessment,
    )


def prediction_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    stay = validate_inference_payload(payload)
    bundle = joblib.load(args.bundle)
    print(json.dumps(asdict(predict_stay(bundle, stay)), indent=2, ensure_ascii=False))
