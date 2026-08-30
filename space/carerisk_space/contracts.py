"""Immutable, public claim and safety contracts for the Space package."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

PRODUCT_NAME = "CareRisk 48H — Evidence & Abstention Explorer"
PRIMARY_CLAIM_ZH_TW = (
    "僅供研究與教育；不是臨床診斷、治療、分流、資源配置或照護決策工具。"
    "本 Space 僅使用內建 synthetic gate-state scenarios，不接受、儲存或處理任何"
    "使用者提供的病人資料；"
    "不輸出 live probability、risk class、case recommendation 或 threshold-based case decision。"
)
SAFETY_SUBTITLE_EN = (
    "Research and education only. Non-clinical and synthetic-only. "
    "No patient data entry or upload, no live predictions, and no care decisions."
)


@dataclass(frozen=True, slots=True)
class ClaimContract:
    """The immutable copy contract displayed by the public Space card."""

    product_name: str
    primary_claim_zh_tw: str
    safety_subtitle_en: str


PUBLIC_CLAIM_CONTRACT = ClaimContract(
    product_name=PRODUCT_NAME,
    primary_claim_zh_tw=PRIMARY_CLAIM_ZH_TW,
    safety_subtitle_en=SAFETY_SUBTITLE_EN,
)


EvidenceFailureCode = Literal[
    "receipt_missing",
    "receipt_hash_mismatch",
    "receipt_schema_invalid",
    "release_relationship_invalid",
    "deployment_manifest_invalid",
]


@dataclass(frozen=True, slots=True)
class MetricInterval:
    estimate: float
    lower: float
    upper: float


@dataclass(frozen=True, slots=True)
class ReceiptEvidence:
    dataset_name: str
    dataset_role: str
    n: int
    events: int
    prevalence: float
    metrics: Mapping[str, MetricInterval]
    bootstrap_method: str
    bootstrap_samples: int
    bootstrap_seed: int
    evaluation_status: str
    success_count: int
    final_lock_status: str
    use_limitation: str
    formal_metrics_sha256: str


@dataclass(frozen=True, slots=True)
class ReleaseRelationship:
    release: str
    limitations: tuple[str, ...]
    scientific_change_flags: Mapping[str, bool]


class ContractViolation(ValueError):
    """Raised when immutable public evidence fails a contract gate."""


class ReceiptHashMismatch(ContractViolation):
    """Raised when receipt bytes do not match the committed evidence anchor."""
