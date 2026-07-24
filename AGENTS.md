# CareRisk 48H Repository Instructions

## Start every task

1. Read `PROJECT_PLAN.md` completely before changing files or running project commands.
2. Read the top-level current status, current milestone, validation evidence, and session handoff.
3. Work only on the requested milestone or explicitly authorized scope.
4. Preserve user-owned changes and inspect the worktree before editing.

## Safety and privacy

- Never read, print, modify, copy, source, or commit `.env`.
- Never commit `data/raw`, `data/processed`, model artifacts, checkpoints, caches, or downloaded PhysioNet files.
- Never use `SAPS-I`, `SOFA`, `Length_of_stay`, or `Survival` as model features.
- Never access Set B outcomes before the model, preprocessing, calibration method, threshold procedure, config, split, and artifacts are frozen.
- Never use Set C in development or reporting.
- Never fabricate metrics, plots, benchmark numbers, completed checkboxes, citations, or test results. Use `待填` for unexecuted results.
- Treat the dashboard and all predictions as research/education output, not clinical diagnosis or care advice.

## Compute and external systems

- Run data preparation, EDA, tests, and the local vertical slice on CPU.
- Do not use the local RTX 4090 unless the user explicitly requests it.
- Keep local CPU concurrency conservative because other projects may be running.
- Use Colab CPU/T4 for full deep training; warn users to use CPU for download and EDA stages.
- Do not create or modify Git remotes, push, publish, deploy, upload to Hugging Face, or start persistent services unless explicitly requested.

## Engineering workflow

- Keep paths config-driven and relative to the repository; do not add machine-specific absolute paths.
- Put importable code under `src/carerisk48h`; keep root CLIs thin.
- Fit preprocessing, imputation, scaling, feature selection, calibration, and threshold components only on the split allowed by `PROJECT_PLAN.md`.
- Keep Set A train/validation/calibration assignments identical across model families and seeds.
- Record run ID, UTC time, git SHA/dirtiness, config/data/split hashes, seeds, environment versions, and artifact hashes in result JSON.
- Mark quick runs as `evaluation_status=smoke_test`; they must not update formal README results.
- Prefer deterministic, testable code and small models over unnecessary complexity.

## Verification

- Add or update tests for every behavior change.
- Run the narrowest relevant tests first, then the milestone acceptance checks.
- Do not run formatters in write mode across unrelated user files.
- CI and unit tests must not depend on live PhysioNet downloads or GPU availability.
- Report commands actually run and their outcomes in `PROJECT_PLAN.md` under validation evidence.

## Finish every task

1. Update milestone checkboxes only for work that is demonstrably complete.
2. Update the top-level current status and next minimum action.
3. Append material decisions to the decision log; do not rewrite decision history silently.
4. Add test or validation evidence, including failures that remain relevant.
5. Refresh the session handoff so another agent can resume without reconstructing context.

## Project skill

Use `$carerisk-48h` for implementation, testing, training, evaluation, calibration, inference, demo, documentation, release preparation, or resuming this project. The skill defines the workflow; `PROJECT_PLAN.md` remains the source of truth for research decisions and progress.
