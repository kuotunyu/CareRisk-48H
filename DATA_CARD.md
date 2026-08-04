# CareRisk 48H Data Card

## 資料來源與用途

本專案使用 [PhysioNet/Computing in Cardiology Challenge 2012 v1.0.0](https://physionet.org/content/challenge-2012/1.0.0/) 的 Set A 開發死亡風險研究原型，並在模型、preprocessing、calibrator 與 threshold 凍結後，以 Set B 做唯一一次 final evaluation。資料包含 ICU 入院最初 48 小時的不規則生理量測與住院死亡標籤。資料僅供研究與教育；不代表一般病房、長照、居家或當代照護流程。

原始資料依 Open Data Commons Attribution License v1.0 提供，並未包含於本 repository。使用者須從官方來源取得並遵守 [ODC-By 1.0](https://physionet.org/content/challenge-2012/view-license/1.0.0/) 的 attribution 要求。本專案 Apache-2.0 授權不涵蓋資料或由資料衍生且受原授權約束的 artifacts。

## Cohort 與切分

- Set A：4,000 stays，用於 train/validation/calibration（70%/15%/15%）。
- 分層：`In-hospital_death × ICUType`；固定 seed `2026`。
- Set B：4,000 stays，正式 final cohort 有 568 deaths（14.2%）；已在模型凍結後完成恰一次 final evaluation 並建立 persistent final lock。`Outcomes-b.txt` 現在公開，但 2012 challenge 期間 test outcomes 曾隱藏。
- Set C：完全排除。

## 欄位與轉換

General descriptors 為 Age、Gender、Height、ICUType、initial Weight。37 個 dynamic variables 轉成 48 個 hourly bins，保留 `value`、`measurement mask` 與 `time-since-last-measurement`。`-1` 是官方 missing sentinel。其他 outlier 原樣保留並報告，不在 parser 靜默刪除。

唯一 outcome 是 `In-hospital_death`。`SAPS-I`、`SOFA`、`Length_of_stay`、`Survival` 與任何 outcome 欄位不得進入 feature pipeline。

## 已知限制與品質風險

- Missingness 同時反映病況與量測/照護流程，不能解讀為因果生理訊號。
- 2012 ICU 資料的設備、臨床流程、族群與 outcome 定義可能和目前部署環境不同。
- 極端值可能是重症、單位/設備問題或資料錯誤；目前採 report-first 原則。
- 性別欄位是資料集提供的有限編碼，不足以代表性別多樣性。
- 沒有足夠證據支持 ICU→長照遷移；若跨場域使用必須重新驗證、重新校準並進行前瞻性安全評估。

## 產生的本機報告

執行 `scripts/generate_data_quality.py` 後，ignored 的 `reports/generated/data_quality/` 會包含 missingness heatmap、robust outlier table、label/ICUType distribution 與摘要；`data/processed/` 會包含固定 split 及 train-only quality guard thresholds。正式 Set B 的 predictions、error cases、11 個 subgroup reports、PR/ROC/reliability/decision curves、ledger 與 final lock 保存在 ignored 的 `artifacts/final-candidate-c993493/`。原始資料、outcomes 與這些衍生物均不提交 repository。

## Citation

請同時引用 PhysioNet 的標準引用：

> Goldberger AL, Amaral LAN, Glass L, Hausdorff JM, Ivanov PC, Mark RG, Mietus JE, Moody GB, Peng CK, Stanley HE. PhysioBank, PhysioToolkit, and PhysioNet: Components of a New Research Resource for Complex Physiologic Signals. Circulation. 2000;101(23):e215–e220. RRID:SCR_007345.

以及 Challenge 論文：

> Silva I, Moody G, Scott DJ, Celi LA, Mark RG. Predicting in-hospital mortality of ICU patients: The PhysioNet/Computing in Cardiology Challenge 2012. Computing in Cardiology. 2012;39:245–248.
