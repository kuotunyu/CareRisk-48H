---
title: CareRisk 48H
emoji: 🫀
colorFrom: blue
colorTo: red
sdk: gradio
sdk_version: 6.20.0
app_file: app.py
pinned: false
license: apache-2.0
---

# CareRisk 48H

> **研究與教育用途，非臨床診斷或照護決策工具。** 本專案已依 freeze protocol 完成唯一一次 Set B final evaluation；這不構成臨床效度、部署核准或跨場域可遷移證據。

CareRisk 48H 用 ICU 入院最初 48 小時不規則、多缺失的生理時序預測住院死亡風險。專案重點不是單一 leaderboard 分數，而是可重現 split、防洩漏、類別不平衡下的 AUPRC、校準、90% specificity operating point、bootstrap uncertainty、錯誤/subgroup 分析與 fail-closed demo。

## 問題與研究邊界

- Outcome：`In-hospital_death`。
- Inputs：5 個 general descriptors、37 個 dynamic variables，轉成 48×37 value/mask/delta。
- 禁止特徵：SAPS-I、SOFA、Length of stay、Survival 與所有 outcome descriptors。
- Set A：train/validation/calibration = 70%/15%/15%，mortality×ICUType stratified，seed 2026。
- Set B：模型與 threshold 凍結後只允許一次 final evaluation。`Outcomes-b.txt` 現在公開，但 2012 challenge 期間 test outcomes 曾隱藏。
- Set C：不使用。

## 資料、授權與引用

資料來自 [PhysioNet/Computing in Cardiology Challenge 2012 v1.0.0](https://physionet.org/content/challenge-2012/1.0.0/)，共 12,000 stays、每組 4,000。原始資料不 commit，依 [Open Data Commons Attribution License v1.0](https://physionet.org/content/challenge-2012/view-license/1.0.0/) 使用；Apache-2.0 只涵蓋本專案自有程式碼。

請同時引用 PhysioNet standard citation：Goldberger AL et al. *PhysioBank, PhysioToolkit, and PhysioNet: Components of a New Research Resource for Complex Physiologic Signals.* Circulation. 2000;101(23):e215–e220；以及 [Challenge 2012 paper](https://www.cinc.org/archives/2012/pdf/0245.pdf)。詳細資料限制見 [DATA_CARD.md](DATA_CARD.md)。

```powershell
python scripts/download_physionet.py --raw-dir data/raw --set a
python scripts/generate_data_quality.py
```

Downloader 預設只有 Set A + `Outcomes-a.txt`，支援 `.partial` 續傳、安全解壓、SHA-256 與 manifest。官方未發布的 checksum 不會被偽稱為官方 checksum。

## 方法

| Family | Inputs | Imbalance | Explanation |
| --- | --- | --- | --- |
| Logistic | static + last/mean/min/max/count/missing fraction | balanced class weights | standardized coefficients |
| LightGBM | base summaries + actual-time slope/presence | balanced class weights | TreeSHAP global/dependence/waterfall |
| GRU-D | normalized value + mask + delta + static | weighted BCE | variable-wise occlusion sensitivity |
| Small TCN | normalized value + mask + `log1p(delta)` + static | weighted BCE | variable-wise occlusion sensitivity |

三個 model seeds 為 17、42、2026。Deep 只有在平均 validation AUPRC 比最佳 tabular 高至少 0.01，且 Brier/ECE 都不惡化時才升級；否則優先選較簡單、較容易校準與解釋的模型。

## 執行

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev,tabular,app]"
.venv\Scripts\python -m pytest
python train.py --config configs/quick.yaml --synthetic
python scripts/train_tabular.py --config configs/full.yaml
```

正式 deep training 使用 [notebooks/CareRisk48H_Deep_Experiments_Colab.ipynb](notebooks/CareRisk48H_Deep_Experiments_Colab.ipynb)。Quick mode 只是 synthetic smoke；full mode 才產生候選。資料下載與 EDA 請使用 Colab CPU，資料到 Drive 後再切 L4，避免浪費 GPU runtime。本機流程預設 CPU，不需要 RTX 4090。

## 結果與校準

Primary metric 是 AUPRC；並報 AUROC、Brier、10-bin ECE、sensitivity/specificity、threshold、PPV/NPV。Final Set B 使用 2,000 次 outcome-stratified bootstrap percentile 95% CI。下表由通過 freeze、一次成功 ledger/final lock 與完整 provenance gate 的 `metrics.json` 自動更新；development/synthetic run 不得寫入。

<!-- RESULTS_START -->
| Frozen model | Split | AUPRC (95% CI) | AUROC (95% CI) | Brier (95% CI) | ECE (95% CI) | Sensitivity @ ≥90% specificity | Threshold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lightgbm | Set B final | 0.555 (0.516–0.594) | 0.870 (0.855–0.884) | 0.087 (0.083–0.090) | 0.008 (0.007–0.019) | 0.581 @ 0.909 specificity | 0.297 |
<!-- RESULTS_END -->

Tabular model 使用 Platt calibration，deep ensemble 使用 temperature scaling。選定 family/hyperparameters 後以 train+validation refit；calibrator 與 threshold 只 fit calibration。Threshold 是 calibrated calibration predictions 中 specificity ≥0.90 時 sensitivity 最高者；同分取較高 threshold。

## 錯誤與 subgroup 分析

Evaluation 已產生 reliability、PR、ROC、decision curve、high-confidence false-positive/false-negative table。Subgroup 預先限定 gender、ICUType 與 age bands `<45 / 45–64 / 65–79 / ≥80`，每組顯示 n、death count 與 CI；任一 class <20 標 `unstable`。正式 Set B 有 5 筆 gender missing，該小組依規則標為 unstable。這些都是描述性錯誤分析，不是公平性或因果結論。本機 ignored outputs 位於 `artifacts/final-candidate-c993493/set_b_final/`。

## 安全 demo

```powershell
python scripts/build_demo_bundle.py
python app.py
python benchmark.py --warmup 10 --iterations 100
```

預設 dashboard 只使用 deterministic synthetic fixture/bundle，顯示 48 小時趨勢、缺失、raw/calibrated risk、threshold、contributors 與聲明。若 coverage/count 低於 Set A train 第 1 percentile、核心 vital groups 少於三組，或 IsolationForest score 低於 train 第 1 percentile，精確機率會被隱藏並顯示「資料品質不足，需要人工複核」。Synthetic bundle 分數不是本研究結果。

Post-final CPU gates 已執行：完全離線 Docker 的 synthetic guarded bundle 以 2 CPU、10 warm-up/100 measured iterations 得到 p95 `18.08 ms`、peak RSS `269.85 MB`；frozen 3-model LightGBM+Platt batch candidate 以單一 CPU thread、相同迭代數得到 p95 `24.89 ms`、peak RSS `140.66 MB`。兩者皆低於本專案 1 秒 soft target，但這只是本機效能證據，不是臨床 SLA、臨床效度或部署核准。

## 限制與 ICU→長照遷移差距

- 2012 ICU cohort 與現代 ICU 已有 temporal/practice shift。
- Missingness 同時反映疾病與量測/照護流程，可能形成捷徑。
- Outcome 是住院死亡，不等同生活品質、可避免死亡或照護需求。
- 資料的 gender 編碼、族群與地理資訊不足以做完整公平性評估。
- ICU 的頻繁監測、急性病嚴重度、設備與 intervention 和長照完全不同；不能用本模型推論長照住民的風險。任何遷移都需重新定義 outcome、重建資料合約、外部/前瞻性驗證、重新校準與治理審查。
- 本 repo 沒有 prospective validation、human factors study、clinical workflow integration 或 post-deployment monitoring 證據。

更多內容見 [MODEL_CARD.md](MODEL_CARD.md)、[DATA_CARD.md](DATA_CARD.md) 與 [PROJECT_PLAN.md](PROJECT_PLAN.md)。

## 90 秒 demo script

1. **0–15 秒：** 說明輸入是 ICU 最初 48 小時的去識別/合成時序，工具僅供研究教育。
2. **15–35 秒：** 展示 HR、呼吸、體溫、血壓與 SaO2 趨勢；空白不是補成正常，而由 mask/delta 明確保留。
3. **35–55 秒：** 執行 synthetic fixture，說明 raw risk、calibrated probability、固定 90% specificity threshold 與非因果 contributors。
4. **55–75 秒：** 刪除多數 vital measurements，再執行；guard 隱藏機率並要求人工複核。
5. **75–90 秒：** 顯示正式 calibration/error/subgroup 報告入口，說明 Set B 只評估一次，並重申結果不可直接用於 ICU 或長照決策。

## 開發與發布狀態

本地 Git 不設定 remote；GitHub/Hugging Face 檔案已準備但不會自動發布。CI 僅用 CPU、合成資料與 mocked downloader。`scripts/update_readme_results.py` 只接受一次成功、frozen、2,000-bootstrap 的 Set B final metrics，拒絕 smoke/development artifacts。本次正式 evaluation access ledger 恰有一次成功且已建立不可覆寫的 final lock。
