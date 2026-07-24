from __future__ import annotations

import joblib

from carerisk48h.demo import build_synthetic_demo_bundle, synthetic_payload
from carerisk48h.inference import predict_stay
from carerisk48h.schema import validate_inference_payload


def test_synthetic_demo_bundle_is_guarded_and_nonclinical(tmp_path) -> None:
    path = build_synthetic_demo_bundle(tmp_path / "demo.joblib")
    bundle = joblib.load(path)
    assert bundle["evaluation_status"] == "smoke_test"
    assert "synthetic" in bundle["data_source"]
    stay = validate_inference_payload(synthetic_payload(index=0))
    result = predict_stay(bundle, stay)
    assert result.disclaimer
    assert result.allow_probability or result.requires_human_review
