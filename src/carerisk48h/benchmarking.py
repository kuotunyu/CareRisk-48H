"""CPU inference latency, memory, and bundle-size benchmark."""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import psutil
from threadpoolctl import threadpool_limits

from carerisk48h.artifacts import environment_versions, write_json_atomic
from carerisk48h.demo import build_synthetic_demo_bundle, synthetic_payload
from carerisk48h.inference import predict_stay
from carerisk48h.schema import validate_inference_payload


def benchmark_bundle(
    bundle_path: str | Path,
    payload: dict[str, Any],
    *,
    warmup: int = 10,
    iterations: int = 100,
) -> dict[str, Any]:
    """Benchmark the complete guarded single-stay CPU prediction path."""
    if warmup < 0 or iterations < 1:
        raise ValueError("warmup must be nonnegative and iterations must be positive")
    path = Path(bundle_path)
    bundle = joblib.load(path)
    stay = validate_inference_payload(payload)
    process = psutil.Process()
    latencies: list[float] = []
    peak_rss = process.memory_info().rss
    with threadpool_limits(limits=1):
        for _ in range(warmup):
            predict_stay(bundle, stay)
        for _ in range(iterations):
            start = time.perf_counter_ns()
            predict_stay(bundle, stay)
            latencies.append((time.perf_counter_ns() - start) / 1_000_000)
            peak_rss = max(peak_rss, process.memory_info().rss)
    return {
        "device": "cpu",
        "warmup_iterations": warmup,
        "measured_iterations": iterations,
        "latency_ms": {
            "p50": float(np.percentile(latencies, 50)),
            "p95": float(np.percentile(latencies, 95)),
            "mean": float(np.mean(latencies)),
        },
        "peak_rss_mb": peak_rss / (1024 * 1024),
        "bundle_size_mb": path.stat().st_size / (1024 * 1024),
        "hf_cpu_basic_soft_target_p95_ms": 1_000,
        "soft_target_met": float(np.percentile(latencies, 95)) < 1_000,
        "platform": platform.platform(),
        "environment": environment_versions(("psutil",)),
    }


def benchmark_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle", type=Path, default=Path("artifacts/demo/synthetic_demo_bundle.joblib")
    )
    parser.add_argument("--input", type=Path)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--output", type=Path, default=Path("reports/generated/cpu_benchmark.json"))
    args = parser.parse_args()
    if not args.bundle.exists():
        build_synthetic_demo_bundle(args.bundle)
    payload = (
        json.loads(args.input.read_text(encoding="utf-8"))
        if args.input
        else synthetic_payload(index=0)
    )
    result = benchmark_bundle(args.bundle, payload, warmup=args.warmup, iterations=args.iterations)
    write_json_atomic(args.output, result)
    print(json.dumps(result, indent=2))
