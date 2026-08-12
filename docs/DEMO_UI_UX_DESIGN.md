# CareRisk 48H Demo UI/UX Redesign Specification

Status: implemented and locally verified with synthetic-only desktop/mobile interaction tests

Date: 2026-08-12

Primary target: `app/dashboard.py`

## 1. Outcome

Redesign the synthetic Gradio demo as a compact evidence console that a portfolio or interview reviewer can understand in one viewport, while preserving an advanced audit path for ML engineers and research reviewers.

The redesign has two immediate goals:

1. Raise uncomfortable small text to a readable scale.
2. Remove unproductive whitespace and hierarchy so the synthetic case, primary action, safety state, and result are visible without scrolling through a full JSON document.

Success is not a more clinical-looking dashboard. Success is a clearer research demonstration that makes the safety boundary, inference path, and evidence limitations hard to misread.

## 2. Evidence and current-state diagnosis

The current local demo was inspected at desktop and mobile widths using the synthetic-only bundle.

| Evidence | Current state | Consequence |
| --- | --- | --- |
| Heading | Approximately 26 px | Product identity is present but does not establish a strong first-view hierarchy. |
| Introductory copy | Approximately 14 px | The non-clinical boundary is easy to skim past. |
| Field labels | Approximately 12 px | Labels are below the intended comfort floor. |
| JSON text | Approximately 12 px with 16.8 px line height | The input is tiring to inspect and visually dominates the page. |
| JSON editor | Approximately 8,677 px tall in the observed desktop state | The primary action and result are displaced far below the first viewport. |
| Page | Approximately 9,447 px tall in the observed desktop state | Most scrolling communicates payload length rather than product value. |
| Results | Three separate text fields plus raw JSON panels | The hierarchy emphasizes implementation output rather than reviewer understanding. |

These measurements are interface observations, not model or clinical evidence.

## 3. Product truth and safety boundary

The surface must remain consistent with `PRODUCT.md`, `README.md`, `MODEL_CARD.md`, and `DATA_CARD.md`.

- The interactive surface is a synthetic demonstration, not a patient-care tool.
- It must not suggest diagnosis, treatment, triage, resource allocation, clinical readiness, or deployability.
- The frozen Set B result is formal research evidence and remains separate from the synthetic demo bundle.
- Set C, real patient data, model retraining, formal reevaluation, and deployment are outside this redesign.
- Schema validation, prohibited-outcome-field rejection, train-derived guard checks, precise-probability withholding, and abstention semantics must remain fail-closed.
- Contributors are descriptive model signals, not causal explanations.
- The threshold is a research operating point, not a clinical action boundary.

## 4. Audience, task, and interaction mode

Primary audience: a portfolio or interview reviewer deciding whether the repository demonstrates credible ML engineering, data science, and healthcare AI judgment.

Secondary audience: an ML engineer or research auditor checking input structure, guard behavior, contributors, and machine-readable output.

Mode: **Operate with a read-first opening**. The visitor should first understand what the demo proves, then run one synthetic case, then inspect technical details only if desired.

Primary task:

> Run one clearly labeled synthetic 48-hour case and understand whether output was shown or withheld, why, and which evidence boundary applies.

Target interaction cost: one primary click for the default demonstration; no JSON editing is required for the primary path.

## 5. Chosen direction: Compact Evidence Console

### Direction contract

**THESIS:** Make the evidence gate visible before the score; refuse the category-default hospital monitor and the opposite marketing landing page.

**OWN-WORLD:** A daylight research workstation using graphite/navy structure, white evidence fields, teal method markers, and amber review states; compact tables and measured rules replace nested cards.

**STORY:** The visitor recognizes a synthetic case, runs it, sees the safety disposition, reads the research output only when allowed, and can open the underlying payload and machine output for audit.

**FIRST VIEWPORT:** A concise title and persistent synthetic/non-clinical notice sit above a 38/62 desktop split: scenario/action on the left, empty or completed evidence state on the right. The primary action remains above the fold.

**FORM:** Compact Evidence Console, candidate 4 in the grounded operate-mode set; concept seed `f6eb12b1`.

**FINISH:** unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, and DESIGN.md

### Decision provenance

The visual-world exploration excluded two category ruts: a fake hospital/EHR monitoring dashboard and a generic portfolio marketing page. Seven grounded systems were considered: registry audit sheet, waveform field guide, statistical appendix, compact evidence console, laboratory batch record, provenance receipt, and incident command board. The operate-mode seed assigned candidate 4. The user had already approved the same Compact Evidence Console direction, so it is pinned.

Catalog challengers were not selected:

- Darkroom process sequencing makes state transitions memorable but weakens immediate product clarity.
- Cassette-deck instrumentation has strong control grammar but risks turning research evidence into novelty hardware.
- Tensegrity makes dependencies visible but is less legible for a one-click evidence review.
- Pixel-arcade, PC-98, and alphabet-storm systems do not meet the restraint or accessibility needed for this research surface.

### Approved composition

The approved composition uses **A — Balanced split console** as the responsive page structure and borrows **B — Three-stage evidence flow** for the visible sequence from synthetic fixture to `evidence gates` to research output. C was not selected because its oversized score gives the demonstration value more authority than the evidence boundary.

Approved comp: `.impeccable/mocks/carerisk-demo-comp-a-split.png`

Sequencing reference: `.impeccable/mocks/carerisk-demo-comp-b-flow.png`

Generated dates, counts, units, fixture descriptors, guard labels, contributor names, and contribution values in the comps are visual placeholders. Implementation must derive every displayed fact from the existing synthetic payload, validated stay, guard assessment, and `SafePrediction`; no comp text may create a new capability or claim.

## 6. Information architecture

### 6.1 Persistent page header

- Eyebrow: `SYNTHETIC RESEARCH DEMO`.
- Product name: `CareRisk 48H`.
- One-sentence value statement: demonstrate schema validation, train-derived guards, calibrated research output, and abstention on synthetic input.
- Always-visible notice: `Synthetic data only · Research and education · Not for clinical decisions`.
- The notice uses an icon plus text and is never relegated to a tooltip or footer.

### 6.2 Scenario and action panel

Show a concise, human-readable summary derived from the bundled synthetic fixture:

- 48-hour observation window.
- Number of observed measurements.
- Coverage percentage.
- Vital groups represented.
- Explicit `Synthetic fixture` label.

Primary action: `Run synthetic case`.

Secondary disclosure: `Inspect or edit synthetic JSON`. The JSON editor is collapsed by default, fixed-height when open, internally scrollable, and clearly labeled as synthetic.

Do not describe the fixture as a patient or imply that its values represent a real person.

### 6.3 Evidence/result panel

The right panel has four explicit states:

1. **Ready:** explains what will appear after the synthetic case runs; contains no empty output boxes.
2. **Output allowed:** shows a safety disposition, synthetic demonstration score, research operating point comparison, and short interpretation bounded to the demo.
3. **Review required / abstained:** withholds precise probabilities, names the guard categories that triggered, and explains that the demonstration requires review. Amber is paired with an icon and text.
4. **Invalid input:** shows a concise schema message and keeps machine detail in the advanced disclosure. No plot or stale result remains visible.

Required labels:

- `Synthetic demonstration score` instead of `Risk`.
- `Research operating point` instead of `Decision threshold`.
- `Output available` or `Review required` instead of diagnostic safe/unsafe language.
- `Model signals (descriptive, not causal)` instead of unqualified feature importance.

Raw and calibrated values may remain available to the advanced reviewer, but the main hierarchy must explain their research meaning and must not present `1.000` as clinical certainty.

### 6.4 Trend, contributors, and guard summary

Below the primary state, use one shared evidence hierarchy rather than separate nested cards.

- Trend: retain the 48-hour visualization and explicitly state that gaps are missing bins.
- Contributors: render a ranked, readable table with feature name, direction or contribution value when available, and the non-causal disclaimer.
- Guard summary: render human-readable rows for coverage, measurement count, vital-group presence, missingness-pattern check, value-pattern check, and final disposition.
- Machine-readable contributors, full guard object, and serialized output move into `Advanced audit details` disclosures.

The UI must not invent units, reference ranges, physiologic validity, OOD guarantees, or causal meaning that the bundle does not provide.

## 7. Layout and density

### Desktop, 1,100 px and above

- Content width: approximately 1,180–1,280 px, centered.
- Main composition: 38% scenario/action and 62% evidence/result.
- Page padding: 20–24 px; primary gaps: 20–24 px.
- Use a single dominant container boundary for the two-column console. Avoid cards inside cards.
- The title, notice, synthetic scenario summary, primary action, and ready/result heading must be visible in a typical 900 px-high first viewport.
- JSON and raw machine output are collapsed by default.

### Tablet, 720–1,099 px

- Use a balanced two-column layout only while labels and the action remain comfortable.
- Otherwise stack scenario above result without changing reading order.
- Tables may become labeled rows; do not introduce horizontal page scrolling.

### Mobile, below 720 px

- Use one column in this order: header, notice, scenario summary, primary action, result state, evidence sections, advanced details.
- The primary action must appear in the first viewport on a 390 x 844 px reference viewport.
- JSON remains collapsed and opens to a fixed-height, internally scrollable editor.
- Result grids become single-column rows; controls remain at least 44 px high.

### Whitespace rules

- Use whitespace to separate task phases, not to wrap every value.
- Section spacing must be greater above a heading than below it.
- Remove empty result controls before a run.
- Remove redundant component labels when the section heading already supplies the meaning.
- Do not use a stack of full-width cards where a rule, row, or table is sufficient.

## 8. Typography and visual system

### Type scale

| Role | Target |
| --- | --- |
| Product title | 34 px desktop; 30 px mobile; 1.1–1.2 line height |
| Section heading | 22–24 px; 1.25 line height |
| Body and explanatory copy | 16–17 px; at least 1.5 line height |
| Controls | 16 px minimum |
| Labels and metadata | 14 px minimum; not used for long paragraphs |
| JSON / machine detail | 13–14 px; at least 1.45 line height |

Use the native UI workhorse stack headed by Segoe UI/Segoe UI Variable so the interface is fast, familiar, and readable without adding a web-font dependency. Monospace is reserved for JSON, hashes, and machine values.

### Color strategy

Use a restrained daylight research palette:

- Canvas: very light cool gray, not pure white.
- Primary ink and structural field: graphite/deep navy.
- Evidence surfaces: white with quiet cool borders.
- Method accent: teal, used for selected or active research state.
- Review accent: amber, used only with an icon and explicit status text.
- Error: a muted red reserved for invalid input, never for risk classification.

The surface must remain understandable in grayscale. Avoid gradients, glow, glassmorphism, medical monitor green, and diagnostic red/green traffic lights.

### Shape and iconography

- Use modest 8–12 px radii, not pill-shaped containers.
- Use thin rules and compact evidence rows to carry structure.
- Use a small, consistent outline icon set only where an icon improves status recognition.
- Do not use emoji as functional status symbols.

## 9. Content rules

### Language and terminology

- Set the document language to `zh-TW` where the Gradio runtime permits.
- User-facing sentences, actions, instructions, errors, and safety explanations use Traditional Chinese first.
- Established technical and domain terms remain in their original language. Do not force-translate terms such as `calibration`, `abstention`, `missingness`, `OOD`, `research operating point`, model names, feature names, or schema field names.
- When a technical term may be unfamiliar, keep the original term and add a concise Traditional Chinese explanation beside it.
- Do not mix Simplified Chinese into interface copy.
- Examples of the intended voice include `執行 synthetic case`, `evidence gates 已通過`, `觸發 abstention，需要人工複核`, and `model signals（描述性、非因果）`.

### Required visible copy

- `僅使用 synthetic data`.
- `僅供研究與教育`.
- `不得用於臨床決策`.
- `合成示範分數` when a precise score is allowed, with an explanation that it is not clinical certainty.
- `research operating point` for the fixed threshold.
- `描述性、非因果` adjacent to `model signals`.

### Prohibited or qualified copy

- Do not call the synthetic fixture a patient.
- Do not call the score a diagnosis, prognosis, recommendation, alert, or clinical risk determination.
- Do not say that a guard proves in-distribution status, safety, physiologic validity, or readiness for use.
- Do not interpret a high or low demonstration score as a care action.
- Do not call the research operating point optimal without naming the pre-specified research rule and its limitations.
- Do not merge synthetic-demo output with the formal Set B results.

## 10. Behavior and data contract

The redesign may refactor presentation data into explicit view models, but prediction behavior remains unchanged.

```text
bundled synthetic fixture
  -> JSON parse and inference schema validation
  -> existing predict_stay path
  -> existing guard and abstention semantics
  -> presentation-only state mapping
  -> ready / output allowed / review required / invalid input
```

Behavioral requirements:

- A new run clears stale state before presenting the next result.
- An exception never exposes a partial score or stale plot.
- An abstention never exposes raw or calibrated probability through a hidden visible component.
- Advanced details reflect the same result object as the human-readable summary.
- Editing the fixture remains optional and does not become the main path.
- No analytics, telemetry, remote request, persistent service, or data upload is added.

## 11. Accessibility requirements

- Meet WCAG 2.1 AA contrast for text and meaningful controls where the Gradio surface permits.
- Keep labels at least 14 px and body/control text at least 16 px where practical.
- Preserve visible keyboard focus and logical tab order: synthetic action before optional JSON editing details unless browser semantics require the disclosure first.
- Associate controls with persistent labels; placeholders are not labels.
- Announce result-state changes through a semantic status/live region where Gradio permits.
- Pair all color states with text and an icon or shape.
- Provide accessible names for disclosures and the primary action.
- Respect reduced-motion preferences; no essential information may depend on animation.
- Avoid horizontal page overflow at 390 px width and 200% browser zoom.

## 12. Implementation boundary

In scope:

- `app/dashboard.py` presentation structure, copy, CSS/theme, and presentation-only formatting helpers.
- Narrow tests for UI state mapping, safe terminology, app construction, and fail-closed output behavior.
- Desktop and mobile visual verification using the synthetic-only bundle.
- README/demo documentation only if the launch experience or labels change materially.

Out of scope:

- Model features, preprocessing, training, calibration, threshold selection, formal evaluation, Set B artifacts, Set C, cohort logic, and inference safety policy.
- Real data, personal data, PhysioNet downloads, GPU work, deployment, publishing, or release creation.
- Authentication, patient workflow, clinical workflow, alerting, monitoring service, or backend API expansion.
- A general site redesign or new marketing UI.

## 13. Verification plan

Implementation is acceptable only when all of the following pass:

### Functional gates

- Existing schema validation and fail-closed behavior remain intact.
- The default synthetic fixture produces the expected allow/abstain behavior without changing model output.
- Invalid JSON/schema input produces the invalid-input state and no score.
- An abstained result withholds precise probabilities in both primary and advanced visible output.
- `create_app()` can be constructed in tests without launching a persistent server.

### Content and safety gates

- Automated checks find the required synthetic/non-clinical wording.
- The primary UI does not contain unqualified `patient risk`, diagnostic, treatment, triage, clinical-safe, or clinically optimal claims.
- Contributors are labeled non-causal and the threshold is labeled a research operating point.
- Formal Set B metrics are not inserted into the synthetic result surface.

### Visual and responsive gates

- At a desktop reference viewport, the notice, scenario summary, primary action, and ready/result heading appear above the fold.
- At 390 x 844 px, the primary action appears in the first viewport and there is no horizontal page overflow.
- Computed label font size is at least 14 px; body and primary controls are at least 16 px; the JSON editor is at least 13 px.
- The JSON editor and machine output are collapsed by default and have bounded internal scrolling when open.
- Empty output boxes and redundant nested containers are absent before the first run.
- Ready, allowed, abstained, and invalid-input states remain understandable without color.

### Engineering gates

- Add or update the narrowest relevant tests before implementation changes.
- Run the focused dashboard tests, then the repository milestone acceptance checks required by `PROJECT_PLAN.md`.
- Run the UI detector once on the changed target, then inspect desktop and mobile screenshots in two batched rounds at most.
- Record commands and actual outcomes in `PROJECT_PLAN.md`; never fabricate a pass.

## 14. Resolved implementation decisions

- The human-readable summary uses only observation-window length, measurement count, dynamic-variable coverage, core vital-group count, and explicit synthetic-fixture type derived from validated synthetic input.
- The trend remains Matplotlib, with larger labels and explicit wording that gaps are missing bins.
- The verified implementation is recorded in root `DESIGN.md`; locally ignored `.impeccable/design.json` carries the extended design-system sidecar.
