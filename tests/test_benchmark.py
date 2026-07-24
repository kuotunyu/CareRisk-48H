from __future__ import annotations

from carerisk48h.benchmarking import benchmark_bundle
from carerisk48h.demo import build_synthetic_demo_bundle, synthetic_payload


def test_cpu_benchmark_records_required_fields(tmp_path) -> None:
    bundle = build_synthetic_demo_bundle(tmp_path / "demo.joblib")
    result = benchmark_bundle(bundle, synthetic_payload(index=0), warmup=1, iterations=3)
    assert result["device"] == "cpu"
    assert result["latency_ms"]["p95"] >= 0
    assert result["peak_rss_mb"] > 0
    assert result["bundle_size_mb"] > 0
