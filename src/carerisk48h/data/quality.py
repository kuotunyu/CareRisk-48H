"""Data-quality summaries that preserve rather than silently clean outliers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from carerisk48h.artifacts import stable_hash, write_json_atomic
from carerisk48h.constants import CORE_VITAL_GROUPS, N_HOURS, TIME_SERIES_VARIABLES
from carerisk48h.data.parser import ParsedStay
from carerisk48h.data.split import make_split_manifest


def stay_quality_features(stay: ParsedStay) -> dict[str, float | int]:
    """Compute non-outcome input-quality features for one stay."""
    observed_variables = np.asarray(stay.mask.any(axis=0), dtype=np.bool_)
    measured_names = {
        variable
        for variable, present in zip(
            TIME_SERIES_VARIABLES, observed_variables.tolist(), strict=True
        )
        if present
    }
    return {
        "RecordID": stay.record_id,
        "dynamic_variable_coverage": float(observed_variables.mean()),
        "measurement_count": int(sum(len(items) for items in stay.observations.values())),
        "core_vital_groups": int(sum(bool(group & measured_names) for group in CORE_VITAL_GROUPS)),
    }


def _aligned_cohort(stays: list[ParsedStay], outcomes: pd.DataFrame) -> pd.DataFrame:
    metadata = pd.DataFrame(
        {
            "RecordID": [stay.record_id for stay in stays],
            "Gender": [stay.static["Gender"] for stay in stays],
            "ICUType": [stay.static["ICUType"] for stay in stays],
            "Age": [stay.static["Age"] for stay in stays],
        }
    )
    cohort = metadata.merge(outcomes, on="RecordID", how="outer", indicator=True)
    if not (cohort["_merge"] == "both").all() or len(cohort) != len(stays):
        raise ValueError("patient records and outcomes are not perfectly aligned")
    return cohort.drop(columns="_merge").sort_values("RecordID").reset_index(drop=True)


def robust_outlier_table(stays: list[ParsedStay]) -> pd.DataFrame:
    """Report Tukey outer-fence outliers without altering observations."""
    rows: list[dict[str, Any]] = []
    for variable in TIME_SERIES_VARIABLES:
        observations = np.asarray(
            [value for stay in stays for _, value in stay.observations[variable]],
            dtype=np.float64,
        )
        if observations.size == 0:
            rows.append(
                {
                    "variable": variable,
                    "n_observations": 0,
                    "median": None,
                    "mad": None,
                    "q1": None,
                    "q3": None,
                    "lower_outer_fence": None,
                    "upper_outer_fence": None,
                    "outlier_count": 0,
                    "outlier_fraction": None,
                    "minimum": None,
                    "maximum": None,
                }
            )
            continue
        q1, median, q3 = np.quantile(observations, [0.25, 0.5, 0.75])
        mad = np.median(np.abs(observations - median))
        iqr = q3 - q1
        lower = q1 - 3.0 * iqr
        upper = q3 + 3.0 * iqr
        outlier = (observations < lower) | (observations > upper)
        rows.append(
            {
                "variable": variable,
                "n_observations": int(observations.size),
                "median": float(median),
                "mad": float(mad),
                "q1": float(q1),
                "q3": float(q3),
                "lower_outer_fence": float(lower),
                "upper_outer_fence": float(upper),
                "outlier_count": int(outlier.sum()),
                "outlier_fraction": float(outlier.mean()),
                "minimum": float(observations.min()),
                "maximum": float(observations.max()),
            }
        )
    return pd.DataFrame(rows)


def generate_quality_report(
    stays: list[ParsedStay],
    outcomes: pd.DataFrame,
    *,
    report_dir: str | Path,
    processed_dir: str | Path,
    split_seed: int,
) -> dict[str, Any]:
    """Generate auditable tables, plots, split manifest, and guard thresholds."""
    if not stays:
        raise ValueError("at least one stay is required")
    report_path = Path(report_dir)
    processed_path = Path(processed_dir)
    report_path.mkdir(parents=True, exist_ok=True)
    processed_path.mkdir(parents=True, exist_ok=True)

    cohort = _aligned_cohort(stays, outcomes)
    split_input = cohort.loc[:, ["RecordID", "label", "ICUType"]]
    split_manifest = make_split_manifest(split_input, seed=split_seed)
    split_manifest.to_csv(processed_path / "set_a_split.csv", index=False)

    mask = np.stack([stay.mask for stay in stays])
    missingness = 1.0 - mask.mean(axis=0)
    missingness_frame = pd.DataFrame(
        missingness,
        index=pd.Index(range(N_HOURS), name="hour"),
        columns=TIME_SERIES_VARIABLES,
    )
    missingness_frame.to_csv(report_path / "missingness_by_hour.csv")

    plt.figure(figsize=(15, 8))
    sns.heatmap(
        missingness_frame.T,
        vmin=0,
        vmax=1,
        cmap="mako_r",
        cbar_kws={"label": "Missing fraction"},
    )
    plt.xlabel("Hour bin")
    plt.ylabel("Variable")
    plt.title("Set A missingness by variable and hour")
    plt.tight_layout()
    plt.savefig(report_path / "missingness_heatmap.png", dpi=160)
    plt.close()

    outliers = robust_outlier_table(stays)
    outliers.to_csv(report_path / "robust_outliers.csv", index=False)

    label_counts = cohort["label"].value_counts().sort_index()
    icu_counts = cohort["ICUType"].value_counts(dropna=False).sort_index()
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].bar([str(item) for item in label_counts.index], label_counts.values)
    axes[0].set(title="In-hospital death", xlabel="Label", ylabel="Stays")
    axes[1].bar([str(item) for item in icu_counts.index], icu_counts.values)
    axes[1].set(title="ICUType distribution", xlabel="ICUType", ylabel="Stays")
    fig.tight_layout()
    fig.savefig(report_path / "cohort_distributions.png", dpi=160)
    plt.close(fig)

    quality = pd.DataFrame(stay_quality_features(stay) for stay in stays)
    quality = quality.merge(split_manifest, on="RecordID", validate="one_to_one")
    quality.to_csv(processed_path / "set_a_quality_features.csv", index=False)
    training_quality = quality.loc[quality["split"] == "train"]
    thresholds = {
        "fit_scope": "Set A train only",
        "percentile": 1.0,
        "dynamic_variable_coverage_min": float(
            np.percentile(training_quality["dynamic_variable_coverage"], 1)
        ),
        "measurement_count_min": float(np.percentile(training_quality["measurement_count"], 1)),
        "core_vital_groups_min": 3,
        "split_hash": stable_hash(split_manifest.to_dict(orient="records")),
    }
    write_json_atomic(processed_path / "quality_thresholds.json", thresholds)

    summary: dict[str, Any] = {
        "dataset": "PhysioNet Challenge 2012 Set A",
        "n_stays": len(stays),
        "n_deaths": int(cohort["label"].sum()),
        "death_prevalence": float(cohort["label"].mean()),
        "icu_type_counts": {str(key): int(value) for key, value in icu_counts.items()},
        "gender_counts": {
            str(key): int(value)
            for key, value in cohort["Gender"].value_counts(dropna=False).items()
        },
        "split_counts": {
            str(key): int(value) for key, value in split_manifest["split"].value_counts().items()
        },
        "split_seed": split_seed,
        "split_hash": thresholds["split_hash"],
        "outlier_policy": (
            "Reported with Tukey 3xIQR outer fences; observations are not silently removed."
        ),
        "quality_guard_thresholds": thresholds,
    }
    write_json_atomic(report_path / "quality_summary.json", summary)
    return summary
