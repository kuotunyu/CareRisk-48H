# CareRisk 48H — 專案計畫與進度

> 本文件是專案唯一的執行與續作基準。開始任何工作前先讀「目前狀態」，完成後更新驗證證據與 session handoff。

## 目前狀態

| 欄位 | 內容 |
| --- | --- |
| 當前 milestone | M4 — clean Colab runtime quick/full 驗證；通過後進入 M5 final candidate refit/freeze |
| 狀態 | M0–M3 完成；M4 clean Colab CPU prepare 已通過，首次 L4 quick 於訓練前被 RAPIDS/Numba 相容 gate 擋下，修正版待重跑；M5 safety gate 已加固、正式 refit/calibration/freeze 未執行；M6 工程完成 |
| 本回合範圍 | 修正 L4 預裝 RAPIDS 與 CPU PyTensor 的共同 Numba 相容版本，重建 immutable handoff；不接觸 Set B |
| 已完成 | 乾淨 source export、固定 seeds/config fingerprint、resume provenance、Colab result package、schema-v2 freeze/final lock；CPU prepare 已通過；Numba 已鎖定 CPU PyTensor、L4 RAPIDS、Python 3.12 與 NumPy 2.2 的共同相容版本 |
| 尚待完成 | Colab quick/full GRU-D/TCN、依門檻選模、train+validation refit、正式 calibration/threshold/Set A dry-run/freeze、一次性 Set B final evaluation |
| 下一個最小動作 | 以新 bundle/receipt/notebook 開啟全新 L4 runtime，設定 `STAGE='train'`、`MODE='quick'`、`EXPECTED_GPU='L4'` 後全部執行並回收 quick ZIP/checksum |
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
- [ ] `notebooks/CareRisk48H_Deep_Experiments_Colab.ipynb` 可由空 runtime 一鍵執行。

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
| 2026-08-03 | Colab source 改採 cloneable Git bundle + SHA-256 receipt | Drive 只保存 immutable source handoff 與可恢復 data/checkpoints/artifacts；避免 notebook autosave 或漏追蹤 source 破壞 Git provenance |
| 2026-08-03 | Config hash 排除 checkout 絕對路徑，resume fingerprint 綁定 config/data/split/source/family/seed | 讓本機與 Colab 的研究設定 hash 一致，並拒絕錯誤資料、split、source 或 family 的 checkpoint |
| 2026-08-03 | Freeze manifest 升級 schema v2，Set B 成功後另寫 persistent final lock | Set B outcome 載入前重算 frozen artifacts，強制完整 provenance/Set A dry-run evidence，並可稽核唯一一次成功 access |
| 2026-08-04 | Colab lock 配合 hosted runtime 固定 `pandas==2.2.2`、`numba==0.65.1` | 首次 clean CPU prepare 的 `pip check` 證實新版 pins 與 Colab 內建 `google-colab`、`pytensor` 衝突；保留嚴格環境檢查並在相依來源修正 |
| 2026-08-04 | Colab lock 加入 `jedi==0.19.2` | 第二次 CPU prepare 的精確 `pip check` 顯示 hosted `ipython 7.34.0` 唯一缺少 `jedi`；官方 metadata 要求 `jedi>=0.16`，選用支援 Python 3.12 的固定版本並保留嚴格 gate |
| 2026-08-04 | Colab 專案套件改用一般安裝並立即 import | 第三次 CPU prepare 證明 editable install 可讓 distribution metadata 與 `pip check` 通過，卻未讓目前 kernel 重新處理 `.pth`；改為 `%pip install -q . --no-deps`，同一格立即 import 精確失敗模組，資料下載前 fail fast |
| 2026-08-04 | Colab Numba 鎖定改採 CPU 與 L4 hosted runtime 的 constraint 交集 `0.61.2` | CPU `pytensor 2.38.3` 要求 `>=0.58,<=0.65.1`，L4 `cudf/cuml 26.2` 要求 `>=0.60,<0.62`；Numba 官方 0.61.2 支援 Python 3.12 與 NumPy 2.2。保留嚴格全環境 `pip check`，不引入會增加 CUDA/PyTorch 風險的額外虛擬環境 |

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
| 2026-08-03 | M4 readiness | TDD `test_clean_git_source_contains_every_package_module` | 先失敗並列出 4 個被 `models/` 規則誤忽略的模組；修正為 root-only ignore 後通過，wheel 亦確認包含 Logistic/LightGBM/GRU-D/TCN |
| 2026-08-03 | M4 readiness | `pytest tests/test_colab_notebook.py tests/test_colab_handoff.py tests/test_config.py ...` | 通過；固定 seeds、machine-independent config hash、data/split/source-bound resume、cloneable source bundle、result ZIP tamper detection 均有 synthetic tests |
| 2026-08-03 | M3 provenance refresh | `PYTHONPATH=src python scripts/train_tabular.py --config configs/full.yaml`，CPU 2 threads | 通過；run `20260803T153347Z-tabular-full`，Git `c4b2c18...` clean，split/config/data/artifact hashes 驗證通過；狀態仍為 development，不更新 README |
| 2026-08-03 | Windows environment | 未設 `PYTHONPATH` 的同一 tabular command | 匯入階段失敗；舊 `.venv` editable path 因中文路徑解碼指向 stale site-packages。依既有決策使用 repo `PYTHONPATH=src` 後通過，未產生失敗 run |
| 2026-08-03 | M5 safety | freeze/final-gate red→green tests | schema-v2 required provenance、artifact re-hash-before-outcome、zero-success freeze、one-success ledger 與 persistent final-lock 均通過 synthetic fixture；真實 Set B access count 維持 0 |
| 2026-08-03 | 全域 | `pytest -q -ra` / `ruff check .` / `mypy` / `pip check` | 通過；73 tests collected（Torch-dependent module 在本機無 Torch，依協議留待 Colab）、Ruff passed、Mypy 34 source files、無 broken requirements |
| 2026-08-03 | 全域 | `PYTHONNOUSERSITE=1 pre-commit run --all-files` | 第一輪 Ruff formatter 改寫 5 個本次/新追蹤檔案，故未視為通過；提交格式化後第二輪全 hooks 通過 |
| 2026-08-03 | build | `pip wheel . --no-deps --wheel-dir artifacts/wheelhouse` + ZIP member gate | 最終重建通過；wheel 68,989 bytes、SHA-256 `1e9ead...98ee`，必要 model、Colab handoff、freeze/final-gate modules 均存在 |
| 2026-08-03 | M4 Windows handoff | Unicode-path Git bundle red→green regression | 首次實際 bundle verify 在中文 repo path 出現 background `UnicodeDecodeError`；固定 Git subprocess UTF-8 decoding 後，含中文 repo/output path 的 clone/receipt test 無 warning 通過 |
| 2026-08-04 | M4 clean Colab CPU | 首次 `prepare` 執行至 notebook environment gate | 如預期被 `pip check` 阻擋；`pandas 2.3.3` 違反 `google-colab==1.0.0` 的 `pandas==2.2.2`，`numba 0.66.0` 違反 `pytensor 2.38.3` 的 `numba<=0.65.1`；未開始 Set A 準備、未接觸 Set B |
| 2026-08-04 | M4 dependency TDD | `.venv\\Scripts\\python.exe -m pytest tests\\test_colab_notebook.py -q` | RED：notebook metadata 仍為舊名且 Colab pins 不相容；GREEN：3 tests passed，固定新名稱與 hosted-runtime-compatible pins |
| 2026-08-04 | M4 compatibility verification | full pytest、targeted handoff tests、notebook 6 code-cell AST、Ruff、Mypy、`pip check`、pre-commit all-files | 通過；74 tests passed、1 Torch module skipped per protocol；6 code cells syntax valid（排除 IPython magic）；Ruff、Mypy 34 source files、local dependency check 與全部 hooks 通過 |
| 2026-08-04 | build | `.venv\\Scripts\\python.exe -m pip wheel . --no-deps --wheel-dir artifacts\\wheelhouse` | 通過；wheel 68,999 bytes、SHA-256 `76a4397324601e8e11ba5742cf20366be065baa94468518756c33bea0e1d914f` |
| 2026-08-04 | M4 immutable handoff gate | `create_source_bundle(...)`、`git bundle verify`、clean clone 與 source-member assertions | 通過；source `747e9facfca103c725e9db69073249acc253c145` bundle 126,724 bytes、SHA-256 `884cde0d...9fb81`；clone SHA/cleanliness、新 notebook 路徑及 Colab pins 均驗證 |
| 2026-08-04 | M4 clean Colab CPU retry | source `77f8b1ac2286f023c4b005330a71b9d6e28396c3` environment gate 與手動 captured `pip check` | 失敗原因已精確定位：`ipython 7.34.0 requires jedi, which is not installed`；先前 pandas/numba 衝突已消失；未開始 Set A 準備、未接觸 Set B |
| 2026-08-04 | M4 jedi TDD/verification | targeted red→green、full pytest、Ruff、Mypy、local `pip check`、pre-commit all-files | RED：缺少 `jedi` pin；GREEN：3 targeted tests passed；完整驗證 74 tests passed、1 Torch module skipped per protocol，其餘 gates 全通過 |
| 2026-08-04 | build after jedi lock | `.venv\\Scripts\\python.exe -m pip wheel . --no-deps --wheel-dir artifacts\\wheelhouse` | 通過；wheel 68,999 bytes、SHA-256 `2e07fa5128197f465c37bdc3d3da2b2daaefe9616f8176ec1840d8edae1819a3` |
| 2026-08-04 | M4 jedi handoff gate | `create_source_bundle(...)`、`git bundle verify`、clean clone 與 exact pin assertions | 通過；source `6a8de02d359fd942b3386fd835799833e969aaff` bundle 128,537 bytes、SHA-256 `b7cebdb2...b3713`；clone 內 `jedi==0.19.2`、pandas/numba pins 與 notebook 均驗證 |
| 2026-08-04 | M4 clean Colab CPU third attempt | source `6ea2031913a1657476577a2a57d00969fffed8bd` 的標準環境 gate 後執行 Set A prepare | 失敗原因已精確定位：editable install 後目前 kernel `ModuleNotFoundError: No module named 'carerisk48h'`；未開始正式 deep run，未接觸 Set B |
| 2026-08-04 | M4 same-kernel import TDD | `.venv\\Scripts\\python.exe -m pytest tests\\test_colab_notebook.py -q` 與標準安裝後同 Python 行程 import probe | RED：舊 notebook 使用 `-e` 且無 import gate；GREEN：4 tests passed；一般安裝後立即從獨立 target 載入 `carerisk48h.artifacts.stable_hash` 成功 |
| 2026-08-04 | M4 full verification after import fix | full pytest、targeted Colab/handoff/config、notebook 6 code-cell AST、Ruff、CI Mypy、`pip check`、pre-commit all-files | 通過；75 tests passed、1 Torch module skipped per protocol；12 targeted tests、Ruff、Mypy 34 source files、local dependency check 與全部 hooks 通過；額外非 CI 範圍 `mypy src scripts app` 發現 dry-run script 2 個既有型別問題，未改研究邏輯 |
| 2026-08-04 | build after import fix | `.venv\\Scripts\\python.exe -m pip wheel . --no-deps --wheel-dir artifacts\\wheelhouse-57f960e` | 通過；wheel 68,999 bytes、SHA-256 `46eb948d7ed727a60570a7c7778dcc5fccb161c3b19837a63c87ee1f2c63bc19` |
| 2026-08-04 | M4 import-fix handoff candidate gate | `create_source_bundle(...)`、`git bundle verify`、receipt branch clean clone、import/install/pin assertions | 通過；source `57f960eaf7e426ad0ad78653e0bc4c5c058c5a41` bundle 129,670 bytes、SHA-256 `7a2cee42c1416aa85283e7f46008900219bf3d5e253568f5880f3efc1dad2ba4`；clean clone 內一般安裝、立即 import gate 與三個 hosted-runtime pins 均驗證 |
| 2026-08-04 | M4 clean Colab CPU prepare | 使用最終 source `e0d2d652a7f9e3df3d0bd963f0bb206aada68360`，使用者執行 CPU `STAGE='prepare'` 全部執行並提供完成截圖 | 通過；所有顯示 cell 為成功，訓練在 prepare 階段正確跳過且未誤產生 result package；未接觸 Set B |
| 2026-08-04 | M4 first L4 quick attempt | source `e0d2d652a7f9e3df3d0bd963f0bb206aada68360`，L4 `STAGE='train'`、`MODE='quick'` 全部執行 | 在訓練前被嚴格 `pip check` 擋下：`cudf-cu12/cuml-cu12 26.2` 要求 `numba>=0.60,<0.62`，舊 pin 為 `0.65.1`；未產生 quick run/package，未接觸 Set B |
| 2026-08-04 | M4 CPU/L4 dependency TDD | `.venv\\Scripts\\python.exe -m pytest tests\\test_colab_notebook.py -q` | RED：舊 Numba pin 違反 L4 RAPIDS constraint；GREEN：4 tests passed，`0.61.2` 同時滿足 CPU PyTensor、L4 RAPIDS 與 NumPy 2.2 支援下限 |
| 2026-08-04 | M4 cross-runtime compatibility verification | Numba 官方 support matrix、CPython 3.12 manylinux wheel download、full pytest、Ruff、Mypy、`pip check`、pre-commit all-files | 通過；官方 0.61.2 支援 Python 3.10–3.13 與 NumPy 2.2；實際取得 cp312 manylinux wheel；75 tests passed、1 Torch module skipped per protocol，其餘 gates 全通過 |
| 2026-08-04 | build after CPU/L4 lock | `.venv\\Scripts\\python.exe -m pip wheel . --no-deps --wheel-dir artifacts\\wheelhouse-df3a28c` | 通過；wheel 68,999 bytes、SHA-256 `322bcdf77d78124475719d9e9f2e81e6b0ab18e8eb255975823adece2ed70a5d` |
| 2026-08-04 | M4 CPU/L4 handoff candidate gate | `create_source_bundle(...)`、`git bundle verify`、receipt branch clean clone 與 Numba pin assertion | 通過；source `df3a28ca2e9599c2a9f65f0bd5edb45103d87aef` bundle 134,234 bytes、SHA-256 `87347bbe3bb51e8b4c157dd5fb398da23aebc8dc4800ed1cd7875badd1c5d5a5`；clean clone 內固定 `numba==0.61.2` |

## Session handoff

- **最後更新：** 2026-08-04
- **完成內容：** clean Colab CPU prepare 已使用 source `e0d2d652a7f9e3df3d0bd963f0bb206aada68360` 通過；首次 L4 quick 在訓練前精確暴露 RAPIDS/Numba 衝突。Numba 改鎖 `0.61.2`，同時符合 CPU PyTensor、L4 RAPIDS、Python 3.12 與 NumPy 2.2；schema-v2 freeze/final lock 維持不變。
- **本機驗證：** CPU/L4 dependency regression 已完成 red→green；75 tests passed、1 Torch module skipped per protocol；Ruff、CI Mypy 34 source files、pip check、pre-commit all-files、CPython 3.12 manylinux wheel、wheel build 與 bundle clean-clone pin gate 均通過。
- **Commits：** `df3a28c` lock a CPU and L4 compatible Numba；本段文件更新另見最新 commit。
- **尚未進行：** 修正版 L4 quick、L4 full GRU-D/TCN、預註冊選模、train+validation final refit、正式 calibration/threshold、final Set A simulated evaluation、freeze manifest、使用者確認後唯一一次 Set B final evaluation。
- **下一步：** 使用者以本回合最終 bundle/receipt/notebook 取代 Drive 舊檔，開全新 L4 runtime 執行 quick，將 ZIP 與 `.sha256` 帶回本 task；quick 只作 smoke，通過後才執行 L4 full。
- **注意：** 未讀取、顯示、修改或提交 `.env`；無 Git remote；本機 GPU 未使用；未搜尋或接觸真實 Set B outcome path，真實 Set B success ledger/final lock 均不存在，成功 access 次數為 0。Quick package 固定 `smoke_test`，不得更新 README。
