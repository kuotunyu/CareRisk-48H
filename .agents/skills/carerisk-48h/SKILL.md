---
name: carerisk-48h
description: Operate and resume the CareRisk 48H trustworthy clinical ML repository. Use when Codex implements, tests, trains, evaluates, calibrates, documents, benchmarks, packages, or resumes work on CareRisk 48H, including its PhysioNet data pipeline, tabular baselines, GRU-D, TCN, Gradio safety demo, and milestone handoff.
---

# CareRisk 48H Workflow

Follow the repository plan as the source of truth. Keep each work session scoped, reproducible, leakage-safe, and easy for a later agent to resume.

## 1. Establish the project state

1. Locate the repository root containing `PROJECT_PLAN.md`.
2. Read `PROJECT_PLAN.md` completely, then read the applicable `AGENTS.md` files.
3. Inspect the current worktree without reading `.env` or ignored data/artifact contents.
4. Identify the current milestone, incomplete acceptance criteria, recorded evidence, risks, and next minimum action.
5. Treat the latest explicit user request as the scope boundary. Do not advance unrelated milestones implicitly.

## 2. Select and state the work unit

1. Choose the smallest coherent acceptance item that produces verifiable progress.
2. State whether the work is documentation, implementation, training, final evaluation, or release preparation.
3. Call out any requested action that conflicts with the frozen research protocol before acting.
4. Prefer CPU for local data work, EDA, tests, and smoke runs. Do not use the local GPU without explicit user authorization.

## 3. Implement without leakage

1. Keep code importable under `src/carerisk48h` and paths config-driven.
2. Preserve the fixed Set A split and fit-scope rules in `PROJECT_PLAN.md`.
3. Reject outcome-related descriptors at the feature-schema boundary.
4. Keep Set B outcomes gated until a freeze manifest exists and the Set A evaluation dry run passes.
5. Keep quick/smoke outputs distinguishable from full research results.
6. Record reproducibility metadata and artifact hashes for every experiment-producing command.
7. Never invent results or infer that a command passed without running it.

## 4. Verify proportionately

1. Add or update tests for changed behavior.
2. Run targeted tests first, followed by milestone acceptance checks when practical.
3. Keep ordinary CI and unit tests CPU-only, synthetic or mocked, and independent of live PhysioNet downloads.
4. For model work, verify data hashes, split hashes, seeds, calibration fit scope, serialized inference parity, and guard behavior.
5. For final evaluation, follow the freeze, confirmation, access-ledger, and final-lock protocol exactly.

## 5. Update the durable handoff

Before finishing:

1. Update the current status table in `PROJECT_PLAN.md`.
2. Check off only acceptance criteria supported by evidence.
3. Append material decisions instead of silently rewriting history.
4. Add the exact validation commands and honest outcomes.
5. Refresh the session handoff with completed work, remaining work, blockers, and one next minimum action.
6. Summarize user-visible changes and clearly label any unrun checks.

## Non-negotiable boundaries

- Never read, expose, modify, or commit `.env`.
- Never treat SAPS-I, SOFA, length of stay, or survival as input features.
- Never use Set C.
- Never access Set B outcomes during development or model selection.
- Never present the dashboard or model as ready for clinical or long-term-care deployment.
- Never publish, push, deploy, or create a remote unless the user explicitly requests it.
