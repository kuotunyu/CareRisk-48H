# CareRisk 48H Model Card

## Model details

CareRisk 48H 是以 historical 48-hour ICU landmark cohort 研究住院死亡風險的 model-comparison framework。候選包含 class-weighted logistic regression、LightGBM、compact GRU-D 與 small TCN。依事前固定的 promotion rule 選定 3-seed LightGBM ensemble，搭配 Platt calibration 與 Set A calibration-only threshold，再於凍結後完成一次 Set B held-out evaluation。

程式碼採 Apache-2.0。PhysioNet data 及其衍生 artifacts 另受 ODC-By 1.0 約束。

## Intended use

- 可信賴 clinical ML、reproducibility、calibration、abstention 與 reporting 的研究／教學範例。
- 比較 discrimination、calibration、research operating point、error pattern 與 subgroup stability。
- 不適用於臨床診斷、治療、分流、資源配置、警示或個別照護決策。
- 不可直接移植至長照、居家、一般病房、其他國家、其他醫院或其他年代資料。

## Population, inputs and output

官方 cohort 納入年齡至少 16 歲、首次可用 ICU stay 且 initial ICU stay 至少 48 小時者；DNR/CMO 未排除。輸入為 5 個 static descriptors 與 37 個 dynamic variables，轉成 48 hourly bins 的 value／mask／delta。輸出是住院死亡 research probability，不是 treatment recommendation 或可避免死亡的估計。

這個 eligibility 形成 48-hour landmark selection：模型不涵蓋早於 48 小時死亡或離 ICU 的病人。資料是單一機構 BIDMC 的 MIMIC-II historical cohort，雖涵蓋四種 adult ICU type，卻沒有跨醫院 variation。Set A／B／C 是同一 source 的隨機分組；本研究沒有 chronological、site-held-out、external 或 prospective validation。

## Training and leakage controls

- Set A：mortality×ICUType stratified 70%／15%／15% train／validation／calibration，seed 2026。
- 模型 seeds：17、42、2026；所有 families 使用相同 assignments。
- Model／hyperparameter selection 使用 train→validation；選定後只用 train+validation refit。
- Platt calibrator 與 threshold `0.2974276505509685` 只 fit calibration 600 筆。
- `In-hospital_death` 是唯一 label；`SAPS-I`、`SOFA`、`Length_of_stay`、`Survival`、outcome descriptors 與 `RecordID` 永不作 features。
- GRU-D 與 TCN 均未同時通過 +0.01 validation AUPRC 且 Brier／ECE 不惡化的 promotion checks，因此依規則選定較簡單的 LightGBM；沒有依結果更動 metric、seed、split 或 promotion threshold。
- Set B outcome 只允許 frozen candidate 的一次成功 evaluation；ledger 已有一次 success 且 final lock 已建立，不得重跑或覆寫。

來源 cohort 宣稱每位 patient 只取首次可用 ICU stay；repo 可另外證明 `RecordID` split-disjoint，但公開資料缺少可獨立重建 patient linkage 的 identifier，因此不把 RecordID audit 稱為完整 patient-level identity verification。

## Evaluation results

Primary metric 為 AUPRC，並報 AUROC、Brier、fixed-width 10-bin ECE、sensitivity／specificity、threshold、PPV／NPV 與 2,000 次 outcome-stratified percentile bootstrap 95% CI。Gender、ICUType、age-band results 只作描述並顯示 small-class instability，不支持 fairness claims。

<!-- RESULTS_START -->
正式 frozen Set B（n=4,000；death=568）結果：AUPRC `0.555`（95% CI `0.516–0.594`）、AUROC `0.870`（`0.855–0.884`）、Brier `0.0866`（`0.0829–0.0904`）、10-bin ECE `0.00784`（`0.00699–0.0193`）。在 frozen threshold `0.2974276505509685` 下，sensitivity `0.581`、specificity `0.909`、PPV `0.513`、NPV `0.929`。CI 使用固定 seed 2026 的 2,000 次 stratified percentile bootstrap。
<!-- RESULTS_END -->

Set B 是同來源 random holdout，evaluation 由 repository owner 自我稽核而非 independent external audit。低 ECE 只描述此 cohort 與此 binning estimator；沒有 calibration intercept／slope 的 external estimate、跨 site calibration 或 prospective calibration evidence。

Set A calibration-only 2,000-bootstrap internal diagnostic 得到 apparent intercept `-0.0002`（`-0.273–0.329`）、slope `1.000`（`0.833–1.220`），以及 threshold `0.297` 的 resampling range `0.267–0.340`。因 Platt 本身已 fit 同一 600-record split，這些是 apparent fit/stability statistics，不是 external calibration；slope 與 threshold ranges 也顯示 calibration-sample uncertainty 不可忽略。

## Operating point and utility

Threshold 是 Set A calibration split 上維持 specificity 至少 0.90 時最大化 sensitivity 的 research operating point。它沒有連結到已驗證的 clinical action、false-positive／false-negative harm、resource capacity 或 cost ratio。Decision curve 是描述性 sensitivity analysis，不是 clinical utility trial。

## Explainability, guard and monitoring status

LightGBM 使用 TreeSHAP；deep models 使用 variable-wise occlusion sensitivity。兩者描述 model behavior，不代表 causal effect。

研究 demo 的 guard 使用 train-only coverage／measurement count、core vital groups、missingness-pattern IsolationForest score 與 robust value-pattern shift，未通過時隱藏精確機率。這是 abstention mechanism，不是 clinical plausibility engine、完整 unit validator 或 externally validated OOD detector。Frozen Set B candidate 是 batch research artifact；synthetic demo bundle 不是正式模型結果。

Outcome-free monitoring 可以觀察 schema rejection、missingness、value-pattern、score／probability distribution 與 abstention drift；沒有 delayed outcomes 時不能判定 discrimination 或 calibration drift，也不得自動重新訓練或修改 threshold。

## Limitations and ethical considerations

- Mortality label 不代表所有 clinical value、quality of life 或 avoidable harm。
- 48-hour landmark 排除了 early exits/deaths，存在明確 selection boundary。
- Missingness 可能編碼照護流程、資源與 clinician behavior。
- 2012 data 存在 temporal、equipment、population 與 practice shift。
- 沒有 site、external、prospective、human-factors 或 clinical utility validation。
- Subgroup field 與 sample size 不足以支持 fairness conclusion。
- 任何 clinical use 前都需要 governance approval、external/prospective validation、unit reconciliation、workflow study、monitoring 與 incident response；本專案沒有提供 deployment evidence。
