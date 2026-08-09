# CareRisk 48H

[![CI](https://github.com/kuotunyu/CareRisk-48H/actions/workflows/ci.yml/badge.svg)](https://github.com/kuotunyu/CareRisk-48H/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/kuotunyu/CareRisk-48H)](https://github.com/kuotunyu/CareRisk-48H/releases/tag/v0.1.0)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![LightGBM](https://img.shields.io/badge/LightGBM-3.3%2B-blue?logo=lightgbm&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C?logo=pytorch&logoColor=white)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

本專案基於 **PhysioNet Challenge 2012** 重症加護病房 (ICU) 入院前 48 小時生理時序資料，建立住院死亡風險預測與推論安全防護系統：著重於可重現資料分割、嚴格防洩漏、Platt 機率校準、事前註冊選模與一次性最終盲測 (One-Shot Final Evaluation)，在 4,000 例獨立測試集 (Set B) 上達成 AUPRC **0.555 (0.516–0.594)** 與 AUROC **0.870 (0.855–0.884)**。

> **研究聲明**：本專案僅供學術研究與工程探索，非臨床診斷、治療或照護決策工具；所有分析結果均需合格醫療專業人員複核。

---

## 系統設計與關鍵特性

1. **嚴格資料分割與防洩漏策略**：
   官方資料分為 Set A (開發資料，4,000 例) 與 Set B (最終測試，4,000 例)；特徵工程僅 fit 訓練集，閾值與校準器僅 fit 校準集，嚴防任何資料穿越。
2. **事前註冊選模與 3-Seed LightGBM Ensemble**：
   對比 Logistic Regression、LightGBM、GRU-D 與 TCN 架構，依事前註冊規則選用泛化最佳之 3-Seed LightGBM 集成模型 (Seeds 17, 42, 2026)。
3. **Platt 機率校準與固定操作閾值 (Fixed Operating Point)**：
   經 Platt Calibration 校準後達成極低校準誤差 (ECE **0.008**)，並在鎖定 90.9% Specificity 下取得 58.1% 敏感度 (Operating Threshold **0.297**)。
4. **多重推論安全防護門禁 (Inference Safety Guards)**：
   內建 JSON Schema 檢核、禁止欄位黑名單過濾、生命徵象覆蓋度 (Vital Coverage) 與分佈外 (OOD) 偵測門控，防範未達標資料誤判。

---

## 系統架構與 Pipeline

### 1. 研究評測與單次盲測流程

```mermaid
%%{init: {'themeVariables': {'fontSize': '18px'}}}%%
flowchart TD
    subgraph Stage1 ["階段一：資料分割與防洩漏策略 (Partition Strategy)"]
        direction LR
        Raw[("PhysioNet 2012 Set A<br/>(4,000 ICU Stays 開發資料)")] --> Strat["固定切分策略<br/>(Train / Validation / Calibration)"] --> Sets[("凍結資料清單<br/>(嚴格隔離獨立校準集)")]
    end

    subgraph Stage2 ["階段二：多架構評估與選模校準 (Training & Calibration)"]
        direction LR
        Sets --> Models["多模型評估對照<br/>(Logistic / LightGBM / GRU-D / TCN)"] --> Refit["3-Seed LightGBM Ensemble<br/>(Train+Val Refit · Seeds 17/42/2026)"] --> Calib["Platt 機率校準<br/>(Calibration 集鎖定閾值 0.297)"]
    end

    subgraph Stage3 ["階段三：流程驗證與單次盲測 (One-Shot Final Evaluation)"]
        direction LR
        Calib --> Manifest[("凍結產物清單<br/>(Freeze Manifest)")] --> DryRun["Set A 乾跑流程驗證<br/>(Dry-Run Pipeline)"] --> FinalEval[("Set B 單次盲測<br/>(4,000 例 One-Shot Evaluation)")]
    end

    Stage1 --> Stage2 --> Stage3

    classDef srcStyle fill:#e7f5ff,stroke:#1971c2,stroke-width:2px,color:#212529
    classDef procStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#212529
    classDef evalStyle fill:#e6fcf5,stroke:#0ca678,stroke-width:2px,color:#212529

    class Raw,Sets,Manifest,FinalEval srcStyle
    class Strat,Models,Refit,Calib,DryRun procStyle

    style Stage1 fill:#f8f9fa,stroke:#1971c2,stroke-width:2px,color:#1971c2,stroke-dasharray: 4 4
    style Stage2 fill:#faf5ff,stroke:#7b1fa2,stroke-width:2px,color:#7b1fa2,stroke-dasharray: 4 4
    style Stage3 fill:#f4fbf7,stroke:#0ca678,stroke-width:2px,color:#0ca678,stroke-dasharray: 4 4
```

### 2. 推論安全防護機制 (Inference Safety Guards)

```mermaid
%%{init: {'themeVariables': {'fontSize': '18px'}}}%%
flowchart TD
    subgraph InputStage ["階段一：輸入檢核與特徵提取"]
        direction LR
        Input[("48 小時 ICU 病歷記錄<br/>(時序生理數據)")] --> Schema["Parser 與 Schema 檢核<br/>(黑名單欄位過濾)"] --> Feat["Tabular 特徵提取<br/>(Missingness 與時序斜率)"]
    end

    subgraph ModelStage ["階段二：模型推理與機率校準"]
        direction LR
        Feat --> Model["3-Seed LightGBM Ensemble<br/>(集成模型推理)"] --> Platt["Platt Calibration<br/>(校準後風險機率)"]
    end

    subgraph GuardStage ["階段三：多重安全門禁與分流輸出"]
        direction LR
        Platt --> Guard{"Coverage / Vitals /<br/>OOD Guard 通過？"}
        Guard -->|"通過"| SafeOutput[("顯示 Calibrated Risk<br/>與固定操作閾值")]
        Guard -->|"未通過"| BlockOutput(["隱藏精確機率<br/>要求人工複核"])
    end

    InputStage --> ModelStage --> GuardStage

    classDef srcStyle fill:#e7f5ff,stroke:#1971c2,stroke-width:2px,color:#212529
    classDef procStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#212529
    classDef condStyle fill:#fff9db,stroke:#f59f00,stroke-width:2px,color:#212529
    classDef safeStyle fill:#e6fcf5,stroke:#0ca678,stroke-width:2px,color:#212529
    classDef blockStyle fill:#ffe3e3,stroke:#e03131,stroke-width:2px,color:#212529

    class Input srcStyle
    class Schema,Feat,Model,Platt procStyle
    class Guard condStyle
    class SafeOutput safeStyle
    class BlockOutput blockStyle

    style InputStage fill:#f8f9fa,stroke:#1971c2,stroke-width:2px,color:#1971c2,stroke-dasharray: 4 4
    style ModelStage fill:#faf5ff,stroke:#7b1fa2,stroke-width:2px,color:#7b1fa2,stroke-dasharray: 4 4
    style GuardStage fill:#f4fbf7,stroke:#0ca678,stroke-width:2px,color:#0ca678,stroke-dasharray: 4 4
```

---

## 評測結果與指標分析

最終測試資料（Set B，4,000 例）在模型與閾值完全凍結後進行單次一擊評測，信賴區間採用 2,000 次 Stratified Bootstrap 估計：

<!-- RESULTS_START -->
| Frozen model | Split | AUPRC (95% CI) | AUROC (95% CI) | Brier (95% CI) | ECE (95% CI) | Sensitivity @ ≥90% specificity | Threshold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lightgbm | 最終測試資料（Set B） | 0.555 (0.516–0.594) | 0.870 (0.855–0.884) | 0.087 (0.083–0.090) | 0.008 (0.007–0.019) | 0.581 @ 0.909 specificity | 0.297 |
<!-- RESULTS_END -->

### 核心評測指標解讀

| 指標名稱 | 實測數值 | 指標意義說明 |
|---|---|---|
| AUPRC | 0.555 (95% CI 0.516–0.594) | 核心指標，專門評估正負樣本極度不平衡情境下的預測精確度 |
| AUROC | 0.870 (95% CI 0.855–0.884) | 衡量模型對高風險個案與低風險個案之排序區辨能力 |
| ECE (校準誤差) | 0.008 (95% CI 0.007–0.019) | 預測機率與實際發生率之一致性，數值極低代表輸出機率極為可靠 |
| 固定操作點 | Sensitivity 58.1% @ Specificity 90.9% | 在優先保證 ≥90% 特異度的前提下，成功識別約 58% 死亡高風險個案 |

![最終測試資料評測總覽圖](docs/assets/final-evaluation-overview.png)

---

## 快速開始

### 1. 本機環境建立與套件安裝

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev,tabular,app]"
.\.venv\Scripts\python -m pytest
```

### 2. 資料下載與模型訓練

```powershell
# 下載 PhysioNet Set A 開發資料並產生品質報告
.\.venv\Scripts\python scripts/download_physionet.py --raw-dir data/raw --set a
.\.venv\Scripts\python scripts/generate_data_quality.py

# 執行 Tabular 完整訓練 (3-Seed LightGBM + Platt Calibration)
.\.venv\Scripts\python scripts/train_tabular.py --config configs/full.yaml
```

<details>
<summary><strong>啟動 Gradio 安全推論 Web UI</strong></summary>

```powershell
.\.venv\Scripts\python scripts/build_demo_bundle.py
.\.venv\Scripts\python app.py
```

</details>

---

## 研究邊界與限制

1. **預測目標與特徵隔離**：預測目標嚴格鎖定為 `In-hospital_death`；`SAPS-I`、`SOFA`、`Length of stay` 與直接結果描述欄位一律不得作為輸入特徵。
2. **資料切分原則**：Set A 專用於開發與校準；Set B 在凍結後僅評估一次，Set C 完全不使用。
3. **場域不可直接遷移**：ICU 重症監測密度、生理時序動態與醫療決策情境與長照或普通病房截然不同，本模型嚴禁直接跨領域遷移使用。

---

## 授權與聲明

本專案之程式碼採 [Apache-2.0 License](LICENSE)。PhysioNet 2012 原始數據集遵循 [ODC-By 1.0](https://physionet.org/content/challenge-2012/view-license/1.0.0/) 規範，詳見 [NOTICE](NOTICE)。
