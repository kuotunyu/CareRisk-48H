# CareRisk 48H — 專案計畫與進度

> 本文件是專案唯一的執行與續作基準。開始任何工作前先讀「目前狀態」，完成後更新驗證證據與 session handoff。

## 目前狀態

| 欄位 | 內容 |
| --- | --- |
| 當前 milestone | M4 — Colab runtime 驗證；之後進入 M5 final candidate refit/freeze |
| 狀態 | M0–M3 完成；M4 code/notebook 完成但尚未在 Colab 跑；M5 安全基礎與 Set A dry-run 完成；M6 工程完成 |
| 本回合範圍 | 以 CPU 從 M1 持續完成所有不需 Colab 或 final Set B outcome 的工作 |
| 已完成 | M1–M3 全部驗收；GRU-D/TCN 與 Colab workflow；M5 calibrator/CI/subgroup/plots/freeze gate/Set B ledger；safe Gradio/demo/CI/Docker/docs |
| 尚待完成 | Colab quick/full deep runs、依門檻選模、train+validation refit、正式 freeze、一次性 Set B final evaluation |
| 下一個最小動作 | 使用者在 Colab CPU 先準備 Set A/Drive，再切 T4 執行 `notebooks/01_train_colab.ipynb` 的 quick 與 full mode |
| 結果狀態 | 正式結果待填；目前產物僅為 development/smoke evidence，不得更新公開結果表 |

## 目標與安全邊界

CareRisk 48H 使用 PhysioNet/Computing in Cardiology Challenge 2012 的 ICU 入院前 48 小時不規則、多缺失生理時序，研究住院死亡風險預測。專案優先考量可重現性、校準、錯誤分析、安全呈現與可解釋性，不以單一競賽分數為目標。

- 僅供研究與教育，不是臨床診斷、治療建議或照護決策工具。
- 資料來自 ICU 成人族群；不得暗示結果可直接遷移至長照、居家照護或其他醫療場域。
- 不需要人工標註；唯一標籤為官方 `In-hospital_death`。
- 原始及處理後資料不提交版本控制，不發布資料副本。
- 本機工作預設 CPU，不自行使用 RTX 4090；正式 deep training 預設在 Colab CPU/T4。
- 未經使用者另行要求，不設定 remote、不推送 GitHub/Hugging Face、不啟動常駐服務。
- 所有未實際執行的結果一律寫「待填」。

## Milestones 與驗收條件

### M0 — 治理與續作機制

- [x] 建立本文件，包含穩定規格、目前狀態、決策、證據與 handoff。
- [x] 建立 `AGENTS.md`，固定 repo 工作規則與安全邊界。
- [x] 使用官方 `skill-creator` 初始化 `.agents/skills/carerisk-48h`。
- [x] skill 通過 `quick_validate.py`。
- [x] 頂端狀態回填為完成，下一步指向 M1。

### M1 — Downloader、parser、logistic vertical slice

- [x] 在建立 `.gitignore` 並忽略 `.env`、data、artifacts、checkpoints 後，初始化本機 Git；不設定 remote。
- [x] 建立 `pyproject.toml`、`src/`、`configs/`、`scripts/`、`notebooks/`、`tests/`、`app/`、`reports/`。
- [x] Downloader 預設只取得 Set A 與 `Outcomes-a.txt`，具續傳、`.partial`、安全解壓、SHA-256、atomic rename 與 manifest。
- [x] Parser 產生 48×37 value/mask/delta、5 個 static descriptors 及 tabular features。
- [x] 建立 train-only preprocessing、class-weighted logistic baseline 與 quick metrics JSON。
- [x] parser、split、leakage、fit scope、metrics、端到端 fixture 測試通過。

### M2 — Data quality 與資料合約

- [x] 產生 missingness-by-hour heatmap、robust outlier、label prevalence、ICUType distribution。
- [x] 固定 Set A split，驗證無交集、標籤錯配或 outcome descriptor 洩漏。
- [x] 完成 inference schema、`DATA_CARD.md` 與資料品質摘要。

### M3 — Tabular trustworthy baselines

- [x] Logistic 與 LightGBM 使用相同固定 split、共同 base summaries 與三 seeds；LightGBM 依預定規格另含 slope。
- [x] LightGBM 使用 slope、class weights、row/feature subsampling 與受限的三組 grid。
- [x] 產生 SHAP global、dependence 與個案 waterfall explanation。
- [x] 報告三 seeds 的 validation 平均、標準差及完整 run metadata。

### M4 — GRU-D、TCN 與 Colab

- [x] GRU-D 使用 value、mask、delta 與 train-derived decay statistics（code 與 numpy preprocessing tests 完成）。
- [x] TCN 使用 normalized value、mask、`log1p(delta)` 與小型 dilated residual blocks（code 完成）。
- [x] 兩模型各控制在約 250k parameters 內，使用 weighted BCE、early stopping、gradient clipping（runtime test 待 Colab torch）。
- [x] 完成 quick/full mode、Drive checkpoint、resume、config hash 與固定環境 lock。
- [ ] `notebooks/01_train_colab.ipynb` 可由空 runtime 一鍵執行。

### M5 — 校準、凍結與一次性 Set B 評估

- [ ] 依預先規則選模，建立 freeze manifest 與 artifact hashes。
- [x] Tabular Platt、isotonic 與 deep temperature calibrator 均完成 serialization tests；final family 尚未 fit 正式 calibrator。
- [x] Threshold 演算法及 Set A tabular dry-run 已驗證 specificity ≥ 90%；final threshold 尚未鎖定。
- [ ] 先以 Set A 模擬完整 evaluation，再經明確確認載入 `Outcomes-b.txt`。
- [x] Set B outcome access gate/ledger 完成測試，正常流程程式上只允許一次成功 final evaluation；真實 access 次數仍為 0。
- [x] Set A-only dry-run 已產生 bootstrap CI、reliability、PR/ROC、decision curve、錯誤與 subgroup reports；final 2,000 bootstrap 待 Set B。

### M6 — 安全 demo 與發布工程

- [x] Gradio 只附合成 fixture，呈現趨勢、缺失、raw/calibrated risk、threshold 與 contributors。
- [x] 缺失或 OOD guard 觸發時隱藏精確機率並要求人工複核。
- [x] 完成 CPU benchmark、Dockerfile、GitHub Actions、pre-commit、model/data cards、citation、license 與 HF Space 設定。
- [x] README 包含問題、方法、待填結果、校準、錯誤、subgroup、限制、ICU→長照差距與 90 秒 demo script。
- [x] `scripts/update_readme_results.py` 只接受正式、完整、一次成功且已鎖定的 Set B metrics JSON。

## 固定研究協議

### 官方資料與授權

- 資料固定使用 [PhysioNet Challenge 2012 v1.0.0](https://physionet.org/content/challenge-2012/1.0.0/)。官方資料共 12,000 ICU stays，Set A/B/C 各 4,000。
- 官方目前提供個別 tarball、recursive `wget` 與匿名 S3 sync。Downloader 使用 version-pinned HTTPS URL，串流計算 SHA-256；官方未發布的 checksum 不得偽稱為官方 checksum。
- Set A 用於開發；Set B 只用於模型凍結後的 final evaluation；Set C 完全排除。
- `Outcomes-b.txt` 現在公開，但 README 必須說明 challenge 當年 test outcome 曾隱藏。
- 資料遵循 [Open Data Commons Attribution License v1.0](https://physionet.org/content/challenge-2012/view-license/1.0.0/)；Apache-2.0 只涵蓋本專案自有程式碼。
- Citation 同時包含 PhysioNet standard citation 與 [Challenge 2012 paper](https://www.cinc.org/archives/2012/pdf/0245.pdf)。

### Split、防洩漏與 final-test 防護

- Set A 以 mortality×ICUType stratification 分為 train/validation/calibration = 70%/15%/15%。
- split seed 固定 `2026`；model seeds 固定 `17, 42, 2026`，所有模型使用同一 split。
- model/hyperparameter selection 使用 train→validation；選定後以 train+validation 重訓。
- preprocessor 只 fit train 或最終重訓時的 train+validation；calibrator 與 threshold 只 fit calibration。
- 唯一 label 為 `In-hospital_death`。`SAPS-I`、`SOFA`、`Length_of_stay`、`Survival` 永不進入 feature pipeline。
- Set B evaluation 前必須存在 freeze manifest、config/data/split/artifact hashes，且先以 Set A 完成 evaluation dry run。
- 載入 Set B outcome 前先寫 access attempt；成功後寫 final lock。任何 override 必須附理由並在 README 公開 evaluation count。

### Parser 與 feature contract

- General descriptors：`Age`、`Gender`、`Height`、`ICUType`、initial `Weight`；`RecordID` 只作識別與 join key。
- Time-series variables 固定 37 個；輸出 schema：
  - `values`: float32 `[N, 48, 37]`
  - `mask`: bool `[N, 48, 37]`
  - `delta`: float32 `[N, 48, 37]`
  - `static`: typed table with five descriptors
  - `label`: int8 `[N]`
- Hour bin 使用 `[00:00, 48:00]`：`00:00→0`、`47:59→47`、精確 `48:00→47`；超過 `48:00` 為 schema error。
- 官方 `-1` 轉成 missing，不視為有效生理值。
- 同一 hour 內 continuous variable 取 mean、`Urine` 取 sum、`MechVent` 取 max、`Weight` 取最後值。
- mask 表示該 bin 是否至少有一筆有效值。已觀測 bin 的 delta 為 0；缺失時為距上次觀測的 bin 數；尚未觀測時為 `hour+1`。
- Logistic features：static + last/mean/min/max/count/missing fraction。
- LightGBM 另加 slope；至少兩筆 observation 時才以實際 hour 做 least-squares slope，否則 missing 並保留 indicator。

### 模型、校準與選擇

- Logistic：median imputation、standard scaling、ICUType one-hot、L2、balanced class weights。
- LightGBM：balanced class weights、受限 grid、TreeSHAP。
- GRU-D：hidden size 64、單層 recurrent core、小型 static branch、train-derived feature means 與 decay。
- TCN：32 channels、kernel 3、dilations 1/2/4/8、residual blocks、小型 static branch。
- Deep 使用 weighted BCE、early stopping、gradient clipping；三 seeds 組成平均 logit/probability ensemble。
- Primary selection metric 是平均 validation AUPRC。Deep 僅在比最佳 tabular 高至少 0.01 absolute AUPRC，且 Brier/ECE 均未惡化時升級；否則選 calibrated tabular。
- Logistic/LightGBM 使用 Platt calibration；deep ensemble 對 ensemble logits 使用 temperature scaling。
- Threshold：在 calibrated calibration predictions 中，從 specificity ≥ 0.90 的 thresholds 選 sensitivity 最高者；完全同分採較高 threshold。

### Metrics、CI 與 subgroup

- Primary metric：AUPRC。
- 同時輸出 AUROC、Brier、10-bin ECE、sensitivity、specificity、threshold，以及可定義時的 PPV/NPV。
- Set B 使用 2,000 次 stratified bootstrap percentile 95% CI；bootstrap seed 固定並寫入結果。
- Subgroups：gender、ICUType、age bands `<45`、`45–64`、`65–79`、`≥80`。
- 每組顯示 n、death count、CI；任一 class 少於 20 筆標記 `unstable`，缺少某一 class 時不計相應 metric，不作公平性結論。
- `results.json` / `metrics.json` 記錄 run ID、UTC timestamp、git SHA/dirtiness、config/data/split hashes、seeds、環境版本、artifact hashes、calibration、threshold、metrics。
- quick runs 固定 `evaluation_status=smoke_test`，不得更新 README 正式結果。

### Demo safety contract

- Schema、單位、timestamp 或 category 不合法時拒絕輸入。
- Dynamic coverage 或 measurement count 低於 train 第 1 percentile，或核心 vital groups 少於三組時，不輸出精確機率。
- 使用 train-only quality features 與固定 seed IsolationForest；OOD score 低於 training 第 1 percentile 時要求人工複核。
- LightGBM 使用 SHAP；deep 使用 variable-wise occlusion sensitivity，標示為模型敏感度而非因果解釋。
- 固定顯示：「研究與教育用途，非臨床診斷或照護決策工具」。

## 驗證矩陣

| 區域 | 必要驗證 |
| --- | --- |
| Downloader | mocked HTTP、resume、checksum mismatch、safe extraction、manifest；官方網路測試需手動 marker |
| Parser | timestamp 邊界、`-1`、duplicate aggregation、Urine/MechVent/Weight、mask、delta、dtype |
| Split/leakage | deterministic split、RecordID disjoint、label alignment、outcome column denylist、fit scope |
| Metrics | hand-computed fixtures、scikit-learn parity、single-class、zero division、bootstrap determinism |
| Serialization | preprocessor/model/calibrator/threshold/guard round-trip prediction parity |
| Inference | valid fixture、missingness/OOD guard、拒絕 outcome fields、schema error messages |
| Colab | quick smoke from clean runtime；full mode 不納入一般 CI |
| Demo | 合成資料、guarded/no-risk state、disclaimer、CPU-only launch smoke test |

CI 僅使用 CPU、合成資料與 mocked downloader，不下載官方資料。CPU benchmark 記錄 warm-up、p50/p95、peak RSS、bundle size；HF CPU basic 的 soft target 為單筆 p95 < 1 秒，未達成時誠實記錄而不捏造 SLA。

## 結果登錄

| 模型 | Split | AUPRC | AUROC | Brier | ECE | Sensitivity @ ≥90% specificity | 狀態 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Logistic | Validation | 待填 | 待填 | 待填 | 待填 | 待填 | development 已執行；正式待填 |
| LightGBM | Validation | 待填 | 待填 | 待填 | 待填 | 待填 | development 已執行；正式待填 |
| GRU-D | Validation | 待填 | 待填 | 待填 | 待填 | 待填 | 待 Colab |
| TCN | Validation | 待填 | 待填 | 待填 | 待填 | 待填 | 待 Colab |
| Frozen model | Set B final | 待填 | 待填 | 待填 | 待填 | 待填 | 未執行 |

正式結果只能由 `scripts/update_readme_results.py` 讀取合格的 full-run `metrics.json` 更新。

## 風險與緩解

| 風險 | 緩解方式 |
| --- | --- |
| Set B outcome 現已公開，容易無意間偷看 | Downloader 預設 Set A；gated final command、access ledger、freeze manifest、final lock |
| 小型 validation/calibration 導致不穩定 | 三 seeds、bootstrap CI、簡約優先、subgroup 小樣本警示 |
| Missingness 本身反映照護流程而非疾病 | 同時呈現 mask/coverage、錯誤分析與限制，不作因果陳述 |
| 生理 outlier 可能是真實病況或輸入錯誤 | Report-first；train-derived clipping/guard；不靜默刪除原始 observation |
| ICU 模型被誤用於長照 | README、MODEL_CARD、dashboard 顯著聲明 domain shift 與非臨床用途 |
| Colab/runtime 版本漂移 | Python/environment lock、config hash、package freeze、checkpoint resume |
| 其他本機專案正在執行 | 本地 CPU-only、有限 threads、不啟動 background service、不自行使用 GPU |
| Windows/Anaconda user-site 對中文路徑解碼失敗 | 指令使用 repo `PYTHONPATH=src`；pre-commit 設 `PYTHONNOUSERSITE=1`，不修改系統 Anaconda |

## 決策紀錄（append-only）

| 日期 | 決策 | 理由 |
| --- | --- | --- |
| 2026-07-19 | 第一回合只完成 M0 | 先建立可續作、可稽核的專案治理基準，再開始功能開發 |
| 2026-07-19 | 程式碼採 Apache-2.0 | 寬鬆開源並包含明確專利授權；資料授權獨立處理 |
| 2026-07-19 | 同時實作 GRU-D 與小型 TCN | 比較兩種適合 48 小時短序列的 missingness-aware inductive bias |
| 2026-07-19 | Deep 採 0.01 AUPRC 簡約門檻 | 避免為極小分數差犧牲解釋、校準與維運成本 |
| 2026-07-19 | Repo-local skill 放 `.agents/skills/carerisk-48h` | 讓工作流程隨 repo 保存並可由 Codex 自動探索 |
| 2026-07-19 | 官方 `TroponinI/TroponinT` 於 parser 邊界正規化為 `TropI/TropT` | 官方下載檔與公開變數表命名不同；維持單一內部 37-variable schema |
| 2026-07-19 | 除 `-1` 外不在 parser 刪除負值 outlier | Set A 含重複的 `Temp=-17.8`；依 report-first 原則保留並在 M2 標示，不擅自改寫原始觀測 |
| 2026-07-19 | Official quick run 先做 mortality×ICUType stratified sampling | 避免依 RecordID 取前 N 筆導致稀有 strata 無法安全切分 |
| 2026-07-19 | Deep runtime 不在本機安裝 PyTorch | 避免大型下載與誤用 RTX 4090；本機驗證 numpy preprocessing/語法，torch forward/training 留給 Colab |
| 2026-07-19 | Set A dry-run 明示 reused development | Validation 已參與選模，只能驗證 calibration/evaluation wiring，不能當成 test performance |

## 驗證證據

| 日期 | Milestone | Command / evidence | 結果 |
| --- | --- | --- | --- |
| 2026-07-19 | M0 | `skill-creator/init_skill.py carerisk-48h --path .agents/skills ...` | 通過；skill 骨架與 `agents/openai.yaml` 已建立 |
| 2026-07-19 | M0 | `python C:\Users\3Hml\.codex\skills\.system\skill-creator\scripts\quick_validate.py .agents\skills\carerisk-48h` | 通過；輸出 `Skill is valid!` |
| 2026-07-19 | M1 | `scripts/download_physionet.py --raw-dir data\\raw --set a` | 通過；Set A 4,000 records、Outcomes-a、SHA-256 manifest 均完成並驗證 |
| 2026-07-19 | M1 | `.venv\\Scripts\\python.exe -m pytest -q` | 通過；30 tests passed（加入官方欄位與負值回歸測試後 parser targeted tests 14 passed） |
| 2026-07-19 | M1 | `train.py --config configs\\full.yaml --model logistic`，CPU 2 threads | 通過；完整 Set A development run 與 artifacts/metrics JSON 產生；非凍結正式結果 |
| 2026-07-19 | M2 | `scripts/generate_data_quality.py`，完整 Set A、CPU 2 threads | 通過；4,000 stays，split 2,800/600/600，品質表、圖、固定 split 與 train-only guard thresholds 產生 |
| 2026-07-19 | M2 | `pytest tests/test_quality.py tests/test_schema.py -q` | 通過；5 tests passed |
| 2026-07-19 | M3 | `scripts/train_tabular.py --config configs/full.yaml`，完整 Set A、CPU 2 threads | 通過；三 seeds logistic/LightGBM、三組小型 grid、model hashes 與 SHAP artifacts 產生；狀態為 development |
| 2026-07-19 | M3 | 最終 M3 development run `20260718T183351Z-tabular-full` | LightGBM validation AUPRC mean/std 已寫入 ignored metrics JSON；正式 README 結果仍為待填 |
| 2026-07-19 | M3 | `pytest tests/test_lightgbm_model.py -q` 與 targeted Ruff | 通過；1 test passed，Ruff passed |
| 2026-07-19 | M4 | deep preprocessing/model/trainer/notebook 靜態與 synthetic tests | 通過；torch-dependent forward/training test 依設計留待 Colab |
| 2026-07-19 | M5 | calibration/evaluation/freeze/final-gate/model-selection tests | 通過；Platt/isotonic/temperature round-trip、bootstrap determinism、one-success ledger 均驗證 |
| 2026-07-19 | M5 | `scripts/dry_run_tabular_calibration.py --bootstrap-samples 200` | 通過；calibrator/threshold fit Set A calibration，reused validation 完整報告產生，`set_b_accessed=false` |
| 2026-07-19 | M6 | `scripts/fit_quality_guard.py --n-jobs 2` | 通過；IsolationForest 與門檻只 fit 固定 2,800 Set A train stays |
| 2026-07-19 | M6 | `benchmark.py --warmup 5 --iterations 30` | synthetic guarded CPU smoke p95 12.81 ms、bundle 2.53 MB；非 frozen benchmark |
| 2026-07-19 | M6 | Gradio `create_app(...)` launch-free smoke | 通過；建立 `Blocks`，未啟動常駐服務 |
| 2026-07-19 | 全域 | `pytest -q` / `ruff check .` / `mypy` / `pip check` | 通過；62 tests、Ruff passed、Mypy 33 source files、無 broken requirements |
| 2026-07-19 | 全域 | `PYTHONNOUSERSITE=1 pre-commit run --files ...` | 全 hooks 通過；large-file、JSON/YAML、private-key checks 通過 |
| 2026-07-19 | 全域 | `pip wheel . --no-deps` | 通過；建立可安裝的 0.1.0 wheel（ignored artifact） |
| 2026-07-19 | 官方查證 | PhysioNet v1.0.0 page、ODC-By、standard citation、CinC 2012 paper | 已核對 recursive wget/anonymous S3、Set A/B tarballs、12,000 stays、公開 Outcomes-b 與引用/授權 |

## Session handoff

- **最後更新：** 2026-07-19
- **完成內容：** M0–M3 全部驗收；M4 code/notebook、M5 安全元件與 Set A dry-run、M6 demo/guard/benchmark/發布工程均完成。完整驗證為 62 tests、Ruff、Mypy、pre-commit、wheel build passed。
- **尚未進行：** Colab quick/full deep runtime、deep/tabular 預註冊規則選模、train+validation final refit、正式 calibration/freeze、一次性 Set B final evaluation。
- **下一步：** 將 repo 放到 Google Drive 的 `CareRisk48H`（或修改 notebook 的 `PROJECT_DIR`）；Colab CPU 先把 Set A 下載至 Drive，再切 T4 執行 quick/full。把兩個 full run 的 metrics 帶回本 task 後繼續 M5。
- **注意：** `.env` 大小/時間戳維持 711 bytes、2026-07-14 22:39:30，未讀取或修改；無 Git remote；本機 GPU 未使用；`data/raw/Outcomes-b.txt` 與 `data/raw/set-b` 均不存在，Set B 成功 access 次數為 0。
