# CareRisk 48H — Portfolio MVP Scope-Cut Design

**Status:** approved scope-cut design; implementation requires a separate written plan and review gate.

## 1. Decision

The previous Hugging Face assurance pipeline (old plan Tasks 7–13) is frozen and superseded for the portfolio MVP. It remains historical engineering work, is not deployable evidence, and must not be changed, deleted, exported, or presented as MVP assurance.

The MVP is a new, independent, minimal source bundle rooted at `portfolio_mvp/`. It is a public-safe synthetic explorer, not a clinical tool, model demonstration, or scientific-validation surface.

## 2. Product and claim ceiling

The product name is **CareRisk 48H — Synthetic Evidence Explorer**. The page uses zh-TW as its primary language with a concise English safety subtitle.

Before the first interactive control, the page displays this exact copy:

> 本頁僅使用固定合成資料作研究展示；不提供個案風險、診斷、治療或照護決策。
>
> Synthetic research demonstration only — not for clinical or care decisions.

The MVP must never display or infer a probability, score, risk class, threshold, recommendation, diagnosis, treatment, prognosis, patient-specific statement, clinical validation, or care-action claim. It must not describe a synthetic fixture as a real-world patient, validation cohort, or performance evidence.

## 3. MVP experience

The page is a small static explorer with four named, fixed synthetic evidence states:

1. `evidence_available` — a synthetic packet is complete enough to show a research-process illustration.
2. `evidence_withheld` — a synthetic packet is intentionally incomplete; the illustration is withheld.
3. `schema_withheld` — a synthetic structure check withholds the illustration.
4. `provenance_withheld` — a synthetic provenance check withholds the illustration.

Each state contains only authored, non-medical teaching copy and simple non-identifying labels. No fixture contains patient records, identifiers, dates, physiological measurements, outcome labels, free text, imported data, or values derived from the legacy repository.

All four states are pre-rendered from a fixed in-memory registry. Native radio controls and CSS may switch visibility in the browser, but the app has no app-owned server callback, event, queue, model call, upload, editable JSON, free-text field, code field, or arbitrary input transport. The normal browser request graph is read-only page and asset retrieval.

## 4. Independent MVP boundary

`portfolio_mvp/` is the only future MVP source root. The implementation may create only the minimum allowlisted files required for:

- application entry point and local UI modules;
- fixed synthetic fixture registry and authored styles;
- exact runtime requirements;
- Docker runtime definition;
- Hugging Face Space README/card;
- Apache-2.0 `LICENSE` and a narrow `NOTICE`;
- focused MVP tests.

The MVP bundle must not import, copy, read, package, mount, or reference legacy `space/`, `scripts/export_hf_space.py`, `tools/space/`, legacy receipt/release files, SBOM, third-party reviewer metadata, old Docker stages, `.env`, data, artifacts, models, reports, Set B/C, training/evaluation code, or private custody material. The old artifacts remain untouched in place.

The future source-to-Space copy is an explicit allowlist of `portfolio_mvp/` files only. A candidate fails if it includes a VCS directory, symlink, archive, binary, secret-shaped value, real-data path, model/weight format, reviewer/browser payload, legacy assurance artifact, or any path outside that allowlist.

## 5. Application and data contract

The application may depend on Gradio and the Python standard library only. It must not import model, numerical-training, joblib, data-processing, network-client, environment-reading, subprocess, shell, upload, filesystem-discovery, or credential libraries.

Fixture construction is deterministic and in memory. Product code reads no filesystem path at runtime; the framework may serve only explicitly packaged MVP UI assets. The app does not fetch a network resource, write a file, load a model, parse a receipt, or accept user-supplied data. The page contains no download of raw or generated research output.

Every rendered text node that identifies the source state is authored from the four-item registry. The UI escapes fixture text and does not echo request data. Failure-to-build or missing fixed fixtures fails closed to a short generic unavailable page rather than exposing stack traces or partial content.

## 6. Runtime and Space metadata

The MVP uses one small Docker runtime that serves the app on port `7860` as a non-root user. It copies only the MVP runtime allowlist, installs only its exact requirements, and starts with an exec-form Python command. The runtime contains no model, data, browser, reviewer image, developer toolchain, build output, or legacy dependency inventory.

Runtime code makes no outbound request. A future build may retrieve the explicitly pinned Python dependencies in its build phase, but the README must not claim an air-gapped build, digest provenance, SBOM attestation, or the superseded eleven-surface assurance model.

The Space card identifies a Docker Space, port `7860`, Apache-2.0 code license, synthetic-only content, and the non-clinical claim ceiling. `NOTICE` states that the MVP includes no PhysioNet data, patient data, trained weights, model artifacts, or formal evaluation evidence. It does not copy the legacy third-party or reviewer inventories.

## 7. Visual and accessibility contract

The first viewport shows the title, exact safety copy, and the fixed-state selector without scrolling at `1440×900`. At `390×844`, content is single-column, controls remain at least 44 CSS pixels high, no horizontal overflow occurs, and the safety copy precedes the selector.

The document declares `lang="zh-TW"`, has one H1, uses semantic headings, visible keyboard focus, labeled radio controls, sufficient contrast, and no essential information conveyed only by color. App-authored HTML and component configuration have no inline JavaScript or event capability. The explorer should be calm and evidence-oriented, not styled like an alert, triage, charting, or clinical-monitoring system.

## 8. Focused verification

Implementation must add focused unit and contract tests that prove:

- the exact safety copy and DOM order precede every control;
- exactly four immutable synthetic states render, with no score, risk, threshold, recommendation, patient, metric, or model claim;
- the app has no upload, file, textbox, code, editable JSON, app-owned callback/API/event/queue, model, network, environment, shell, or legacy import capability;
- fixture source is fixed, in-memory, deterministic, escaped, and contains no prohibited real-data patterns;
- Docker and Space card copy only the MVP allowlist and disclose the stated boundary;
- candidate path scanning rejects forbidden legacy, private, model, data, secret, browser/reviewer, and VCS material.

One local browser accessibility/privacy smoke covers desktop and mobile viewports. It verifies keyboard radio selection, visible focus, safety-copy order, no horizontal overflow, no console error, no external request, and no POST/upload/event traffic. This is a UI smoke, not clinical validation, formal evaluation, or an assurance-matrix substitute.

## 9. Delivery sequence and remote gates

After implementation and local review, the only delivery steps are:

1. audit the isolated MVP source/bundle against its allowlist and denylist;
2. push the approved GitHub commit with a normal non-force push;
3. authenticated collision-check and create the public Space `steven0226/carerisk-48h` from the isolated MVP bundle only;
4. perform an anonymous live safety/accessibility/privacy smoke;
5. set the GitHub About Website field to the verified Space URL.

No release, tag, Pages, topic, visibility, secret, variable, model, data, or unrelated GitHub metadata change is part of this MVP. A collision, unexpected public host, extra bundle path, claim-boundary failure, or anonymous smoke failure stops publication.

## 10. Explicitly out of scope

The MVP excludes the old Tasks 7–13 clean-export, receipt, SBOM, reviewer-image, failure-image, eleven-surface, container-forensics, provenance-matrix, and multi-state evidence-assurance work. It also excludes model scoring, training, evaluation, calibration, thresholds, Set B/C, clinical performance metrics, model cards based on legacy evidence, user uploads, arbitrary inputs, login, analytics, telemetry, remote data access, and any clinical or care-decision use.

## 11. Success criteria

The MVP is ready for its delivery gates only when the independent source bundle is allowlist-clean; every visible state is fixed synthetic content; the exact claim ceiling is first; focused tests and the single browser smoke pass; Docker runs the small non-root UI; the Space card and notices make no unsupported claim; and the final public Space anonymously shows the same boundary with no data, model, upload, score, or external request surface.

## 12. Review handoff

This document is the only scope-cut design artifact. It authorizes no product code, remote mutation, or deletion. Central review must approve this committed spec before a new MVP implementation plan is written.
