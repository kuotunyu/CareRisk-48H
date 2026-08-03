# CareRisk 48H Model Card

## Model details

CareRisk 48H 是以 ICU 入院最初 48 小時的不規則、多缺失生理時序研究住院死亡風險的模型比較框架。候選包含 class-weighted logistic regression、LightGBM、compact GRU-D 與 small TCN。依預註冊規則已選定並凍結 3-seed LightGBM ensemble；正式 Set B 結果目前仍為「待填」。

程式碼採 Apache-2.0。PhysioNet 資料及其衍生 artifacts 另受 ODC-By 1.0 約束。

## Intended use

- 可信賴 clinical ML 的研究、教學、重現性與安全展示。
- 比較 discrimination、calibration、operating point、錯誤案例與 subgroup stability。
- 不適用於臨床診斷、治療、分流、資源配置或個別照護決策。
- 不可直接移植至長照、居家、一般病房、其他國家或其他年代資料。

## Inputs and outputs

輸入為 5 個 static descriptors 與 37 個 dynamic variables，轉成 48 hourly bins 的 value/mask/delta。凍結 candidate 是一次性 batch evaluation artifact，不是可部署的臨床推論 bundle。安全 demo 使用獨立的 synthetic-only guarded bundle；只有通過 schema、missingness 與 OOD guard 才顯示 raw/calibrated probability、固定 threshold 及非因果 contributors，否則隱藏精確機率並要求人工複核。

## Training and evaluation protocol

- Set A：mortality×ICUType stratified 70/15/15 train/validation/calibration，seed 2026。
- 模型 seeds：17、42、2026。
- Deep 只有在 validation AUPRC 比最佳 tabular 高至少 0.01，且 Brier/ECE 均不惡化時才升級。
- GRU-D 與 TCN 均未同時通過 deep promotion checks，因此依規則選定較簡單的 LightGBM；沒有因結果調整 metric、seed、split 或選模門檻。
- LightGBM 三個 seeds 已用 Set A train+validation 3,400 筆 refit；Platt calibrator 與 threshold `0.2974276505509685` 只 fit calibration 600 筆。
- Set B outcome 只允許 frozen model 的一次成功 final evaluation；目前尚未執行。

## Metrics

Primary metric 為 AUPRC，並報 AUROC、Brier、10-bin ECE、sensitivity/specificity、threshold、PPV/NPV 與 2,000 次 stratified bootstrap 95% CI。Gender、ICUType、age band 分組會顯示 n、death count、CI 與 unstable 標記；不據此宣稱公平性。

<!-- RESULTS_START -->
正式 frozen Set B 結果：待填。
<!-- RESULTS_END -->

## Explainability and safety

LightGBM 使用 TreeSHAP；deep 使用 variable-wise occlusion sensitivity。兩者描述模型行為，不代表因果效應。研究規格中的 guard 以 train-only 第 1 percentile coverage/count 與 IsolationForest score 定義；目前可執行 dashboard 預設使用 synthetic-only guard，凍結 batch evaluator 不應被當成即時臨床服務。

## Limitations and ethical considerations

- Mortality label 不能代表所有臨床價值或可避免傷害。
- Missingness 可能編碼照護流程、資源與 clinician behavior。
- 2012 年資料存在時間、設備、族群與 practice shift。
- Subgroup 樣本量與資料欄位不足以支持公平性結論。
- Demo 預設 bundle 完全由合成資料建立，其分數不是研究結果。
- 任何臨床使用前都需要治理核准、外部/前瞻性驗證、human factors、監測與失效處置；本專案未提供這些部署證據。
