from pathlib import Path

from carerisk_space.contracts import (
    PRIMARY_CLAIM_ZH_TW,
    SAFETY_SUBTITLE_EN,
)

SPACE_ROOT = Path(__file__).parents[1]
EXPECTED_ZH_TW = (
    "僅供研究與教育；不是臨床診斷、治療、分流、資源配置或照護決策工具。"
    "本 Space 僅使用內建 synthetic gate-state scenarios，不接受、儲存或處理任何"
    "使用者提供的病人資料；"
    "不輸出 live probability、risk class、case recommendation 或 threshold-based case decision。"
)
EXPECTED_EN = (
    "Research and education only. Non-clinical and synthetic-only. "
    "No patient data entry or upload, no live predictions, and no care decisions."
)


def test_claim_copy_is_exact_and_card_places_it_first() -> None:
    assert PRIMARY_CLAIM_ZH_TW == EXPECTED_ZH_TW
    assert SAFETY_SUBTITLE_EN == EXPECTED_EN
    card = (SPACE_ROOT / "README.md").read_text(encoding="utf-8")
    body = card.split("---", 2)[2]
    assert body.index(EXPECTED_ZH_TW) < body.index("## Evidence")
    assert "sdk: docker" in card
    assert "app_port: 7860" in card
    assert "license: apache-2.0" in card
