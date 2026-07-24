"""Dataset constants and leakage boundaries."""

from __future__ import annotations

PHYSIONET_VERSION = "1.0.0"
PHYSIONET_BASE_URL = "https://physionet.org/files/challenge-2012/1.0.0"
DATA_LICENSE = "Open Data Commons Attribution License v1.0"
DATA_LICENSE_URL = "https://physionet.org/content/challenge-2012/view-license/1.0.0/"

N_HOURS = 48
STATIC_VARIABLES: tuple[str, ...] = ("Age", "Gender", "Height", "ICUType", "Weight")
TIME_SERIES_VARIABLES: tuple[str, ...] = (
    "Albumin",
    "ALP",
    "ALT",
    "AST",
    "Bilirubin",
    "BUN",
    "Cholesterol",
    "Creatinine",
    "DiasABP",
    "FiO2",
    "GCS",
    "Glucose",
    "HCO3",
    "HCT",
    "HR",
    "K",
    "Lactate",
    "Mg",
    "MAP",
    "MechVent",
    "Na",
    "NIDiasABP",
    "NIMAP",
    "NISysABP",
    "PaCO2",
    "PaO2",
    "pH",
    "Platelets",
    "RespRate",
    "SaO2",
    "SysABP",
    "Temp",
    "TropI",
    "TropT",
    "Urine",
    "WBC",
    "Weight",
)
VARIABLE_INDEX = {name: index for index, name in enumerate(TIME_SERIES_VARIABLES)}

# The published variable table uses the abbreviated names below, while the
# downloadable patient files spell out the two troponin parameters. Keep one
# canonical internal schema and normalize the documented file variants at the
# parser boundary.
PARAMETER_ALIASES: dict[str, str] = {
    "TroponinI": "TropI",
    "TroponinT": "TropT",
}

OUTCOME_COLUMNS: frozenset[str] = frozenset(
    {"SAPS-I", "SOFA", "Length_of_stay", "Survival", "In-hospital_death"}
)
FORBIDDEN_FEATURE_COLUMNS: frozenset[str] = OUTCOME_COLUMNS | frozenset(
    {"label", "RecordID", "record_id"}
)
CORE_VITAL_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"HR"}),
    frozenset({"RespRate"}),
    frozenset({"Temp"}),
    frozenset({"SaO2", "PaO2"}),
    frozenset({"MAP", "NIMAP", "SysABP", "NISysABP", "DiasABP", "NIDiasABP"}),
)

MODEL_SEEDS: tuple[int, ...] = (17, 42, 2026)
SPLIT_SEED = 2026
BOOTSTRAP_SEED = 2026
