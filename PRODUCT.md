# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

The primary audience is a portfolio or interview reviewer assessing whether the repository demonstrates credible ML engineering, data science, and healthcare AI judgment. The secondary audience is an ML engineer or research auditor who needs to inspect the demo's input contract, safety gates, and evidence boundaries.

## Product Purpose

CareRisk 48H is a trustworthy clinical-ML research software example built around a 48-hour ICU mortality-risk study. It exists to demonstrate a reproducible, leakage-aware workflow covering cohort definition, preprocessing, calibration, pre-specified threshold selection, abstention, provenance, and auditable evaluation. Success means a reviewer can understand the research mechanism and its limitations without mistaking the project for a clinical product.

## Positioning

The repository pairs a frozen, auditable research evaluation with an intentionally separate synthetic-only interactive demonstration. Its differentiator is the visible chain from input validation and train-derived safety guards to calibrated research output and abstention, rather than a claim of clinical readiness.

## Operating Context

Reviewers typically encounter the project through GitHub documentation, the model and data cards, machine-readable evaluation evidence, and a local Gradio demo. The demo accepts a synthetic 48-hour JSON fixture, validates it against the inference schema, applies missingness and value-pattern guards, and either displays research output or withholds the precise probability for review.

## Capabilities and Constraints

- The public demo uses a synthetic-only bundle and synthetic fixtures; it must not imply that a displayed score is a real-patient prediction.
- The frozen Set B evaluation is a separate research artifact and must never be rerun, unlocked, overwritten, or presented as the model behind the synthetic demo.
- Set C, real patient data, deployment, diagnosis, treatment, triage, resource allocation, and care advice are outside scope.
- The interface must preserve schema validation, outcome-feature denial, missingness/value-pattern guards, abstention, and the existing inference semantics.
- The research operating point is not a clinically validated action threshold. Decision-curve results are descriptive and do not establish clinical utility.
- The repository is CPU-compatible for local demo and verification work. Full training and evaluation are not part of routine demo use.
- User-facing copy should prefer "synthetic demonstration score," "research operating point," and "review required" over clinical-decision language.

## Brand Commitments

The product name is "CareRisk 48H." Its voice is precise, restrained, evidence-led, and explicit about uncertainty. Safety limitations must remain visible rather than being hidden in secondary legal copy. The interface must avoid diagnostic traffic-light framing and any visual treatment that resembles a deployed hospital decision-support system.

## Evidence on Hand

- `README.md` documents the cohort, split roles, formal same-source holdout results, calibration limitations, decision-utility limits, abstention behavior, and research boundary.
- `MODEL_CARD.md` and `DATA_CARD.md` document intended use, limitations, provenance, and data constraints.
- `docs/final-result-receipt.json` is the machine-readable formal result receipt; the interactive demo does not replace it.
- `configs/inference_schema.json` defines the inference input contract.
- `app/fixtures/synthetic_patient.json` and the synthetic demo bundle support a non-clinical demonstration without distributing PhysioNet data.
- No external, prospective, contemporary, site-held-out, human-factors, workflow-utility, or clinical-validity evidence is available; future interface work must not fabricate or imply it.

## Product Principles

1. Make evidence boundaries as legible as the result.
2. Demonstrate the safety mechanism, not clinical authority.
3. Keep the primary reviewer path concise while preserving an auditable advanced path.
4. Prefer explicit uncertainty and abstention over false precision.
5. Preserve reproducibility, provenance, privacy, and frozen-evaluation controls.

## Accessibility & Inclusion

The demo must support comfortable reading without zoom: body and control text should be at least 16 px where practical, labels must not fall below 14 px, status must never rely on color alone, keyboard focus must remain visible, and desktop/mobile layouts must avoid horizontal overflow. Plain-language labels should accompany technical terms.
