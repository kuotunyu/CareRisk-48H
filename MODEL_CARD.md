# CareRisk 48H Model Card

## Model details

CareRisk 48H 是以 ICU 入院最初 48 小時的不規則、多缺失生理時序研究住院死亡風險的模型比較框架。候選包含 class-weighted logistic regression、LightGBM、compact GRU-D 與 small TCN。最終 family 尚未凍結，正式結果目前為「待填」。

程式碼採 Apache-2.0。PhysioNet 資料及其衍生 artifacts 另受 ODC-By 1.0 約束。

## Intended use

- 可信賴 clinical ML 的研究、教學、重現性與安全展示。
- 比較 discrimination、calibration、operating point、錯誤案例與 subgroup stability。
- 不適用於臨床診斷、治療、分流、資源配置或個別照護決策。
- 不可直接移植至長照、居家、一般病房、其他國家或其他年代資料。

## Inputs and outputs

輸入為 5 個 static descriptors 與 37 個 dynamic variables，轉成 48 hourly bins 的 value/mask/delta。輸出若通過 schema、missingness 與 OOD guard，才包含 raw 與 calibrated probability、固定 threshold 及非因果 contributors；否則精確機率被隱藏並要求人工複核。

## Training and evaluation protocol

- Set A：mortality×ICUType stratified 70/15/15 train/validation/calibration，seed 2026。
- 模型 seeds：17、42、2026。
- Deep 只有在 validation AUPRC 比最佳 tabular 高至少 0.01，且 Brier/ECE 均不惡化時才升級。
- 選模後以 train+validation refit；calibrator 與 ≥90% specificity threshold 只 fit calibration。
- Set B outcome 只允許 frozen model 的一次成功 final evaluation；目前尚未執行。

## Metrics

Primary metric 為 AUPRC，並報 AUROC、Brier、10-bin ECE、sensitivity/specificity、threshold、PPV/NPV 與 2,000 次 stratified bootstrap 95% CI。Gender、ICUType、age band 分組會顯示 n、death count、CI 與 unstable 標記；不據此宣稱公平性。

<!-- RESULTS_START -->
正式 frozen Set B 結果：待填。
<!-- RESULTS_END -->

## Explainability and safety

LightGBM 使用 TreeSHAP；deep 使用 variable-wise occlusion sensitivity。兩者描述模型行為，不代表因果效應。Guard 依 Set A train 的第 1 percentile coverage/count 與 IsolationForest score 定義，低品質/OOD 輸入不顯示精確機率。

## Limitations and ethical considerations

- Mortality label 不能代表所有臨床價值或可避免傷害。
- Missingness 可能編碼照護流程、資源與 clinician behavior。
- 2012 年資料存在時間、設備、族群與 practice shift。
- Subgroup 樣本量與資料欄位不足以支持公平性結論。
- Demo 預設 bundle 完全由合成資料建立，其分數不是研究結果。
- 任何臨床使用前都需要治理核准、外部/前瞻性驗證、human factors、監測與失效處置；本專案未提供這些部署證據。
