# CareRisk 48H — Zenodo Research Artifact Readiness

## Current status

**Candidate preparation only.** This checklist does not create a tag, GitHub Release, DOI or Zenodo record. Publication requires a separate explicit user approval after every gate below is evidenced.

Recommended artifact type: source-only research software with aggregate result receipt. Do not describe it as a clinical model, medical device, validated decision-support system or distributable patient-level dataset.

## Immutable controls

- Do not move, recreate or retag existing `v0.1.0`.
- Do not rerun Set B or change its one-success ledger/final lock.
- Do not change the formal metrics receipt to match new prose or code.
- Preserve formal metrics SHA-256 `808525afad2ec550e8059c4ba37c2f5aaf8af748873a5a590dff7f1aeaaf47af` and freeze manifest SHA-256 `22de6c8317c202372d2281bab5a4998ecc0b3a566b85cf2355d6ef80ba23db80`.
- Any future source release must use a new immutable version/tag selected before publication; it must cite that the frozen result originates from the earlier locked evaluation.

## Required green gates

### Source and tests

- [ ] Git worktree is clean at the exact candidate commit.
- [ ] Python 3.10, 3.11 and 3.12 CI jobs pass without weakening tests.
- [ ] Ruff, Mypy, full synthetic/mocked pytest, pip check, pre-commit and whitespace checks pass.
- [ ] Docker image builds and launch-free synthetic `create_app()` smoke passes as non-root.
- [ ] Wheel builds from a clean `git archive` and imports from an isolated target.

### Research claims

- [ ] README, Data Card and Model Card state the 48-hour landmark cohort and exact eligibility.
- [ ] Set A/B/C are described as historical same-source random partitions, not temporal/site/external validation.
- [ ] Set B is described as a self-audited one-time held-out evaluation, not a blind test.
- [ ] ECE is identified as fixed-width 10-bin and cohort-specific.
- [ ] Threshold is a research operating point, not a clinical decision threshold.
- [ ] Decision curve is descriptive and not clinical utility evidence.
- [ ] Missingness/value-pattern anomaly guard is not called a complete OOD or physiological safety system.
- [ ] No ICU-to-long-term-care transfer claim appears.

### Privacy and restricted-content scan

- [ ] `git ls-files` contains no `.env`, raw/processed data, outcomes, row-level predictions, error-case records, models, checkpoints, ledger, final lock or ignored reports.
- [ ] Source archive is scanned before upload for forbidden paths, private keys, large generated files and machine-specific absolute paths.
- [ ] Public result receipt remains aggregate-only and contains no RecordID, prediction array, subgroup row, outcome file hash or calibrator coefficients.
- [ ] NOTICE and Data Card preserve PhysioNet ODC-By attribution and state that data are not redistributed.

### Identity and metadata

- [ ] `CITATION.cff` validates against CFF 1.2.0.
- [ ] CFF, package metadata and archive version/date match the new release decision.
- [ ] Repository and release URLs resolve to the exact immutable tag.
- [ ] Git authors and committers are only `kuotunyu <61350295+kuotunyu@users.noreply.github.com>`.
- [ ] Commit messages contain zero `Co-authored-by` trailers.
- [ ] GitHub Contributors lists only `kuotunyu` before and after publication.
- [ ] Zenodo creators list only the user's chosen scholarly identity; no bot, Codex or assistant is added as author/contributor.

### Archive and checksum receipt

- [ ] Create the upload candidate from `git archive <new-tag>`, not from the working directory.
- [ ] Record archive filename, byte size and SHA-256 locally before upload.
- [ ] Confirm archive contains README, LICENSE, NOTICE, CFF, Data/Model Cards, monitoring contract, inference schema, tests, CI, Dockerfile and aggregate final-result receipt.
- [ ] Confirm archive contains no ignored/local-only plans, `PROJECT_PLAN.md`, interview notes or development artifacts.
- [ ] If Zenodo automatically archives GitHub, compare its resolved tag/commit and downloaded archive contents against the local candidate.

## Suggested Zenodo metadata draft

| Field | Candidate value |
| --- | --- |
| Upload type | Software |
| Title | CareRisk 48H |
| Description | Leakage-controlled and calibrated mortality-risk research software for irregular 48-hour ICU time series; includes reproducible evaluation, abstention and monitoring contracts; research/education only. |
| License | Apache-2.0 for project code; data excluded and separately ODC-By 1.0 |
| Keywords | trustworthy clinical machine learning; calibration; mortality risk; ICU time series; reproducible research; PhysioNet |
| Related identifiers | GitHub repository, immutable GitHub Release, PhysioNet Challenge 2012 source and Challenge paper |
| Access | Open source code only; no patient-level data or model artifact |

Do not assign a version, release date or DOI in the repository until the new release version is explicitly approved and the draft deposit is verified.

## Publication sequence requiring explicit approval

1. Freeze a clean local candidate and complete every checkbox with exact evidence.
2. Ask the user for one explicit approval covering new version/tag, GitHub push/Release and Zenodo draft creation.
3. Create the immutable GitHub tag/Release under the user's identity.
4. Create a Zenodo draft, verify creator identity, files, checksum, license, related identifiers and preview.
5. Ask for final publication approval if the Zenodo action is irreversible.
6. Publish, then record DOI and verify GitHub/Zenodo archive parity.
