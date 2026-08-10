# CareRisk 48H Data Card

## 資料來源與允許用途

本專案使用 [PhysioNet/Computing in Cardiology Challenge 2012 v1.0.0](https://physionet.org/content/challenge-2012/1.0.0/) 的去識別化 ICU research data。Set A 用於開發；模型、preprocessing、calibrator、threshold、config 與 split 全部凍結後，以 Set B 執行恰一次 self-audited held-out evaluation；Set C 完全排除。資料只支援研究與教育，不代表現代 ICU、一般病房、長照、居家或其他照護場域。

原始資料依 Open Data Commons Attribution License v1.0 提供，未包含於本 repository。使用者須從官方來源取得並遵守 [ODC-By 1.0](https://physionet.org/content/challenge-2012/view-license/1.0.0/)；本專案 Apache-2.0 授權不涵蓋資料或受原授權約束的衍生 artifacts。

## Cohort definition 與 48-hour landmark

Challenge cohort 共 12,000 ICU stays。官方 cohort 定義為：

- 年齡至少 16 歲；
- 每位病人的首次可用 ICU stay；
- initial ICU stay 至少 48 小時；
- 使用 ICU 入院最初 48 小時的 observations；
- DNR/CMO 個案未排除，官方沒有列出其他 exclusion criteria。

這是 conditional 48-hour landmark cohort。早於 48 小時死亡、離 ICU 或不滿足 stay duration 的人不在 cohort，因此結果不得解讀成 ICU admission 時點對所有病人的 prediction performance。

資料來自單一機構 Beth Israel Deaconess Medical Center 的 MIMIC-II（2001–2007），涵蓋 medical、surgical、coronary 與 cardiac surgery recovery 四種 adult ICU type；不是四所醫院。Challenge cohort 隨機分成 Set A／B／C，各 4,000 stays。這些分組不是 chronological、site-held-out 或 external validation；本研究也沒有可用於跨院驗證的多機構 site variation。

## Patient leakage 與 split

- 官方來源只保留每位病人的首次可用 ICU stay，降低同一病人跨 stay 出現在不同官方 sets 的風險。
- Repository 以 `RecordID` 驗證 Set A train／validation／calibration 互斥，並驗證 outcome alignment。
- 公開 records 沒有可供研究者獨立重建 patient-level linkage 的跨 stay patient identifier；因此 patient uniqueness 依賴官方 cohort construction，不能把 `RecordID` disjoint 誇大為完整 patient identity audit。
- Set A 依 `In-hospital_death × ICUType` 分層為 train／validation／calibration = 70%／15%／15%，split seed `2026`。
- Set B 有 4,000 stays、568 deaths（14.2%）；在模型凍結後完成一次留出評估並建立 persistent final lock。`Outcomes-b.txt` 現已公開，但 2012 challenge 期間 test outcomes 曾隱藏。

## 欄位、label 與時間邊界

General descriptors 為 Age、Gender、Height、ICUType、initial Weight。37 個 dynamic variables 轉成 48 個 hourly bins，保留 `value`、measurement `mask` 與 `time-since-last-measurement`。精確 `48:00` 納入最後一個 bin；超過 48 小時的 measurement 被拒絕。

唯一 outcome 是 `In-hospital_death`。`SAPS-I`、`SOFA`、`Length_of_stay`、`Survival`、任何 outcome descriptor 與 `RecordID` 不得進入 feature pipeline。官方 `-1` sentinel 轉為 missing；其他 outlier 原樣保留並 report-first，不在 parser 靜默刪除。

## Missingness、value 與 unit 風險

- Missingness 同時反映病況、量測政策、臨床工作流程與資源，不能解讀為因果生理訊號。
- 資料欄位以 Challenge schema 的 canonical unit 為前提；inference payload 沒有獨立 unit metadata，無法做完整 unit reconciliation。
- Train-derived value-pattern screen 可攔截明顯 scale shift，但不是 physiological plausibility validator，也不能保證每個數值的臨床合理性。
- 極端值可能是重症、單位／設備問題或資料錯誤；輸入 guard 採 abstention，不自動更正數值。
- 性別欄位是資料集提供的有限編碼，不足以代表性別多樣性。

## Generalizability limits

- 2012 年資料的設備、治療、族群、missingness process 與 outcome definition 可能和目前流程不同。
- 沒有 temporal、site-held-out、external 或 prospective validation。
- 沒有足夠證據支持 ICU 到長照、居家或一般病房遷移。
- 若在其他場域研究，必須重新定義 cohort、確認 unit/schema、外部驗證、重新校準、設定 abstention policy，並先完成治理與前瞻性安全評估。

## 本機產物與隱私

`scripts/generate_data_quality.py` 會把 aggregate data-quality report 寫入 ignored `reports/generated/data_quality/`，並把固定 split 與 train-only guard thresholds 寫入 ignored `data/processed/`。正式 Set B predictions、error cases、subgroup outputs、plots、ledger 與 final lock 亦保持 ignored。原始資料、outcomes、個案 predictions、models、reports 與 locks 均不提交 repository。

## Citation

請同時引用 PhysioNet standard citation 與 Challenge 論文：

> Goldberger AL, Amaral LAN, Glass L, Hausdorff JM, Ivanov PC, Mark RG, Mietus JE, Moody GB, Peng CK, Stanley HE. PhysioBank, PhysioToolkit, and PhysioNet: Components of a New Research Resource for Complex Physiologic Signals. Circulation. 2000;101(23):e215–e220. RRID:SCR_007345.

> Silva I, Moody G, Scott DJ, Celi LA, Mark RG. Predicting in-hospital mortality of ICU patients: The PhysioNet/Computing in Cardiology Challenge 2012. Computing in Cardiology. 2012;39:245–248.
