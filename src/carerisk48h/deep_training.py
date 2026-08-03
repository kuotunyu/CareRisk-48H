"""Reproducible three-seed training for compact GRU-D and TCN candidates."""

from __future__ import annotations

import copy
import math
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import precision_recall_curve, roc_curve
from torch import Tensor, nn
from torch.utils.data import DataLoader, TensorDataset

from carerisk48h.artifacts import (
    deep_resume_fingerprint,
    environment_versions,
    git_state,
    stable_hash,
    utc_run_id,
    write_json_atomic,
)
from carerisk48h.config import RunConfig, canonical_config_payload
from carerisk48h.data.downloader import sha256_file
from carerisk48h.data.parser import ParsedStay
from carerisk48h.data.split import validate_split_manifest
from carerisk48h.deep_preprocessing import DeepPreprocessor
from carerisk48h.metrics import compute_binary_metrics
from carerisk48h.models.deep import build_deep_model


def _set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def resolve_device(requested: str) -> torch.device:
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    if requested not in {"cpu", "cuda"}:
        raise ValueError("device must be 'cpu' or 'cuda'")
    return torch.device(requested)


def _dataset(arrays: dict[str, np.ndarray], labels: np.ndarray) -> TensorDataset:
    return TensorDataset(
        torch.from_numpy(arrays["values"]),
        torch.from_numpy(arrays["mask"]),
        torch.from_numpy(arrays["delta"]),
        torch.from_numpy(arrays["static"]),
        torch.from_numpy(labels.astype(np.float32)),
    )


def _predict_logits(
    model: nn.Module, loader: DataLoader[tuple[Tensor, ...]], device: torch.device
) -> np.ndarray:
    model.eval()
    outputs: list[np.ndarray] = []
    with torch.inference_mode():
        for values, mask, delta, static, _ in loader:
            logits = model(values.to(device), mask.to(device), delta.to(device), static.to(device))
            outputs.append(logits.detach().cpu().numpy())
    return np.concatenate(outputs)


def _save_torch_atomic(payload: dict[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".partial")
    torch.save(payload, partial)
    os.replace(partial, destination)


def _plot_deep_run(
    logs: list[dict[str, Any]],
    truth: np.ndarray,
    probabilities: np.ndarray,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 5))
    for seed in sorted({int(item["seed"]) for item in logs}):
        selected = [item for item in logs if int(item["seed"]) == seed]
        plt.plot(
            [item["epoch"] for item in selected],
            [item["train_loss"] for item in selected],
            label=f"seed {seed}",
        )
    plt.xlabel("Epoch")
    plt.ylabel("Weighted BCE")
    plt.title("Training history")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "training_history.png", dpi=160)
    plt.close()

    precision, recall, _ = precision_recall_curve(truth, probabilities)
    false_positive, true_positive, _ = roc_curve(truth, probabilities)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(recall, precision)
    axes[0].axhline(float(truth.mean()), linestyle="--", color="grey")
    axes[0].set(xlabel="Recall", ylabel="Precision", title="Validation PR curve")
    axes[1].plot(false_positive, true_positive)
    axes[1].plot([0, 1], [0, 1], linestyle="--", color="grey")
    axes[1].set(xlabel="False-positive rate", ylabel="True-positive rate", title="Validation ROC")
    fig.tight_layout()
    fig.savefig(output_dir / "validation_curves.png", dpi=160)
    plt.close(fig)


def train_deep_family(
    stays: list[ParsedStay],
    outcomes: pd.DataFrame,
    split_manifest: pd.DataFrame,
    config: RunConfig,
    *,
    family: str,
    repo_root: str | Path,
    device_name: str,
    checkpoint_dir: str | Path,
    resume: bool,
    data_manifest_hash: str | None,
) -> tuple[Path, dict[str, Any]]:
    """Train a three-seed deep ensemble without accessing calibration or Set B."""
    expected_ids = {stay.record_id for stay in stays}
    validate_split_manifest(split_manifest, expected_ids=expected_ids)
    run_started = time.perf_counter()
    split_hash = stable_hash(split_manifest.to_dict(orient="records"))
    source_git = git_state(repo_root)
    split_lookup = split_manifest.set_index("RecordID")["split"].to_dict()
    outcome_lookup = outcomes.set_index("RecordID")["label"].to_dict()
    if set(outcome_lookup) != expected_ids:
        raise ValueError("patient records and outcomes are not perfectly aligned")
    train_stays = [stay for stay in stays if split_lookup[stay.record_id] == "train"]
    validation_stays = [stay for stay in stays if split_lookup[stay.record_id] == "validation"]
    processor = DeepPreprocessor.fit(train_stays)
    train_arrays = processor.transform(train_stays)
    validation_arrays = processor.transform(validation_stays)
    train_labels = np.asarray(
        [outcome_lookup[stay.record_id] for stay in train_stays], dtype=np.float32
    )
    validation_labels = np.asarray(
        [outcome_lookup[stay.record_id] for stay in validation_stays], dtype=np.int8
    )
    device = resolve_device(device_name)
    config_payload = canonical_config_payload(config, repo_root=repo_root)
    config_hash = stable_hash(config_payload)
    checkpoint_path = Path(checkpoint_dir)
    run_dir = config.output_dir / utc_run_id(family, config.mode)
    model_dir = run_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=False)
    processor.save(run_dir / "preprocessor.npz")

    train_loader = DataLoader(
        _dataset(train_arrays, train_labels),
        batch_size=config.batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=device.type == "cuda",
    )
    validation_loader = DataLoader(
        _dataset(validation_arrays, validation_labels),
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=device.type == "cuda",
    )
    positive = float(train_labels.sum())
    if positive == 0 or positive == len(train_labels):
        raise ValueError("deep training requires both outcome classes")
    positive_weight = torch.tensor(
        [(len(train_labels) - positive) / positive], dtype=torch.float32, device=device
    )
    loss_function = nn.BCEWithLogitsLoss(pos_weight=positive_weight)
    patience = 2 if config.mode == "quick" else 8
    all_logs: list[dict[str, Any]] = []
    seed_logits: list[np.ndarray] = []
    seed_metrics: list[dict[str, Any]] = []
    model_paths: list[Path] = []
    checkpoint_hashes: dict[str, str] = {}
    resume_evidence: list[dict[str, Any]] = []
    seed_timings: list[dict[str, Any]] = []
    parameter_count: int | None = None

    for seed in config.model_seeds:
        seed_started = time.perf_counter()
        _set_seed(seed)
        model = build_deep_model(family).to(device)
        parameter_count = sum(parameter.numel() for parameter in model.parameters())
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
        checkpoint = checkpoint_path / f"{family}_seed_{seed}.pt"
        start_epoch = 0
        best_auprc = -math.inf
        best_state: dict[str, Tensor] | None = None
        stale_epochs = 0
        epochs_executed = 0
        checkpoint_found = bool(resume and checkpoint.exists())
        fingerprint = deep_resume_fingerprint(
            config_hash=config_hash,
            data_manifest_hash=data_manifest_hash,
            split_hash=split_hash,
            source_git_sha=source_git["commit"],
            family=family,
            seed=seed,
        )
        if checkpoint_found:
            saved = torch.load(checkpoint, map_location=device, weights_only=False)
            if saved.get("resume_fingerprint") != fingerprint:
                raise ValueError(f"checkpoint provenance mismatch: {checkpoint}")
            model.load_state_dict(saved["model_state"])
            optimizer.load_state_dict(saved["optimizer_state"])
            start_epoch = int(saved["epoch"]) + 1
            best_auprc = float(saved["best_auprc"])
            best_state = saved["best_model_state"]
            stale_epochs = int(saved["stale_epochs"])

        for epoch in range(start_epoch, config.epochs):
            if stale_epochs >= patience:
                break
            epochs_executed += 1
            model.train()
            total_loss = 0.0
            total_items = 0
            for values, mask, delta, static, labels in train_loader:
                optimizer.zero_grad(set_to_none=True)
                labels = labels.to(device)
                logits = model(
                    values.to(device), mask.to(device), delta.to(device), static.to(device)
                )
                loss = loss_function(logits, labels)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
                optimizer.step()
                total_loss += float(loss.detach().cpu()) * len(labels)
                total_items += len(labels)
            validation_logits = _predict_logits(model, validation_loader, device)
            validation_probabilities = 1.0 / (1.0 + np.exp(-validation_logits))
            validation_metrics = compute_binary_metrics(validation_labels, validation_probabilities)
            current_auprc = float(validation_metrics["auprc"])
            improved = current_auprc > best_auprc + 1e-6
            if improved:
                best_auprc = current_auprc
                best_state = copy.deepcopy(
                    {name: value.detach().cpu() for name, value in model.state_dict().items()}
                )
                stale_epochs = 0
            else:
                stale_epochs += 1
            log = {
                "seed": seed,
                "epoch": epoch,
                "train_loss": total_loss / total_items,
                "validation_auprc": current_auprc,
                "validation_brier": validation_metrics["brier"],
                "validation_ece": validation_metrics["ece"],
            }
            all_logs.append(log)
            _save_torch_atomic(
                {
                    "family": family,
                    "seed": seed,
                    "epoch": epoch,
                    "model_state": model.state_dict(),
                    "optimizer_state": optimizer.state_dict(),
                    "best_model_state": best_state,
                    "best_auprc": best_auprc,
                    "stale_epochs": stale_epochs,
                    "config_hash": config_hash,
                    "resume_fingerprint": fingerprint,
                    "data_manifest_hash": data_manifest_hash,
                    "split_hash": split_hash,
                    "source_git_sha": source_git["commit"],
                },
                checkpoint,
            )
            write_json_atomic(run_dir / "training_log.json", {"epochs": all_logs})
            if stale_epochs >= patience:
                break
        if best_state is None:
            raise RuntimeError("training produced no checkpointed model")
        model.load_state_dict(best_state)
        logits = _predict_logits(model, validation_loader, device)
        probabilities = 1.0 / (1.0 + np.exp(-logits))
        seed_logits.append(logits)
        seed_metrics.append(
            {"seed": seed, **compute_binary_metrics(validation_labels, probabilities)}
        )
        destination = model_dir / f"{family}_seed_{seed}.pt"
        _save_torch_atomic(
            {
                "family": family,
                "seed": seed,
                "model_state": best_state,
                "parameter_count": parameter_count,
                "schema_version": 1,
            },
            destination,
        )
        model_paths.append(destination)
        checkpoint_hashes[checkpoint.name] = sha256_file(checkpoint)
        resume_evidence.append(
            {
                "seed": seed,
                "resume_requested": resume,
                "checkpoint_found": checkpoint_found,
                "resumed": checkpoint_found,
                "start_epoch": start_epoch,
                "epochs_executed": epochs_executed,
                "completed_epochs": start_epoch + epochs_executed,
                "early_stopping_reached": stale_epochs >= patience,
                "checkpoint_file": checkpoint.name,
                "resume_fingerprint": fingerprint,
            }
        )
        seed_timings.append(
            {"seed": seed, "elapsed_seconds": time.perf_counter() - seed_started}
        )

    ensemble_logits = np.mean(np.stack(seed_logits), axis=0)
    ensemble_probabilities = 1.0 / (1.0 + np.exp(-ensemble_logits))
    ensemble_metrics = compute_binary_metrics(validation_labels, ensemble_probabilities)
    _plot_deep_run(all_logs, validation_labels, ensemble_probabilities, run_dir / "plots")
    np.savez_compressed(
        run_dir / "validation_predictions.npz",
        record_ids=validation_arrays["record_ids"],
        labels=validation_labels,
        logits=ensemble_logits,
        probabilities=ensemble_probabilities,
    )
    model_manifest = {
        "schema_version": 1,
        "family": family,
        "ensemble": "mean logits across seeds",
        "seeds": list(config.model_seeds),
        "model_files": [path.relative_to(run_dir).as_posix() for path in model_paths],
        "preprocessor": "preprocessor.npz",
        "parameter_count_per_model": parameter_count,
        "calibrator": None,
        "threshold": 0.5,
    }
    write_json_atomic(run_dir / "best_model.json", model_manifest)
    artifact_hashes = {
        path.relative_to(run_dir).as_posix(): sha256_file(path)
        for path in [*model_paths, run_dir / "preprocessor.npz"]
    }
    payload: dict[str, Any] = {
        "run_id": run_dir.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_status": "smoke_test" if config.mode == "quick" else "development",
        "selection_scope": "Set A train to validation only; calibration untouched",
        "model_family": family,
        "device": str(device),
        "parameter_count_per_model": parameter_count,
        "seed_metrics": seed_metrics,
        "ensemble_metrics": ensemble_metrics,
        "seeds": {"split": config.split_seed, "models": list(config.model_seeds)},
        "config": config_payload,
        "config_hash": config_hash,
        "data_manifest_hash": data_manifest_hash,
        "split_hash": split_hash,
        "preprocessor_fit_ids_hash": stable_hash(sorted(processor.fit_record_ids.tolist())),
        "git": source_git,
        "environment": environment_versions(("torch",)),
        "artifact_hashes": artifact_hashes,
        "checkpoint_hashes": checkpoint_hashes,
        "resume": resume_evidence,
        "timing": {
            "total_seconds": time.perf_counter() - run_started,
            "per_seed": seed_timings,
        },
        "notes": [
            "Validation metrics are uncalibrated development evidence.",
            "Full training is intended for Colab CPU/T4, not the local RTX 4090.",
        ],
    }
    write_json_atomic(run_dir / "metrics.json", payload)
    write_json_atomic(run_dir / "results.json", payload)
    return run_dir, payload
