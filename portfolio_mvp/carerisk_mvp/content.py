"""Fixed, synthetic teaching states for the portfolio explorer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvidenceState:
    """One authored state in the static evidence-gate illustration."""

    state_id: str
    label_zh: str
    label_en: str
    heading_zh: str
    body_zh: str
    process_note_zh: str


EVIDENCE_STATES: tuple[EvidenceState, ...] = (
    EvidenceState(
        state_id="evidence_available",
        label_zh="證據可用",
        label_en="Evidence available",
        heading_zh="合成封包完整",
        body_zh="固定範例包含預期的結構與來源說明。",
        process_note_zh="必要證據齊備，本頁顯示研究流程示意。",
    ),
    EvidenceState(
        state_id="evidence_withheld",
        label_zh="證據保留",
        label_en="Evidence withheld",
        heading_zh="合成封包不完整",
        body_zh="固定範例刻意省略一項必要說明。",
        process_note_zh="必要證據不齊，本頁保留研究流程示意。",
    ),
    EvidenceState(
        state_id="schema_withheld",
        label_zh="結構檢查保留",
        label_en="Schema withheld",
        heading_zh="合成結構未通過",
        body_zh="固定範例刻意使用不完整的欄位結構。",
        process_note_zh="結構檢查未通過，本頁保留研究流程示意。",
    ),
    EvidenceState(
        state_id="provenance_withheld",
        label_zh="來源檢查保留",
        label_en="Provenance withheld",
        heading_zh="合成來源未確認",
        body_zh="固定範例刻意省略來源說明。",
        process_note_zh="來源檢查未通過，本頁保留研究流程示意。",
    ),
)

STATE_IDS: tuple[str, ...] = tuple(state.state_id for state in EVIDENCE_STATES)
