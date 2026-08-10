# CareRisk 48H — TRIPOD+AI / PROBAST+AI Evidence Audit

## Purpose and method

This is a repository-level prepublication mapping, not a completed journal checklist and not an independent risk-of-bias assessment. It uses the [TRIPOD+AI statement](https://www.bmj.com/content/385/bmj-2023-078378) for reporting coverage and the [PROBAST+AI framework](https://www.bmj.com/content/388/bmj-2024-082505) for structured quality, risk-of-bias and applicability concerns.

TRIPOD+AI is a reporting guideline, not a development-quality score. PROBAST+AI serves a different purpose. A repository can report a limitation well and still have a serious evidence gap.

Status meanings:

- **Supported** — public source/docs contain direct evidence and executable or machine-readable support.
- **Partial** — material information exists, but a publication-grade item or independent evidence remains incomplete.
- **Missing** — the study did not perform the activity or the public artifact does not support it.

## TRIPOD+AI reporting coverage

| Reporting domain | Status | Repository evidence | Remaining gap |
| --- | --- | --- | --- |
| Identification of prediction-model study, target population and outcome | Supported | README and Model Card identify a 48-hour ICU landmark in-hospital mortality study. | A future paper still needs a structured title and abstract. |
| Background, rationale and intended role | Partial | README and Model Card explain trustworthy ML and explicitly reject clinical use. | No clinical pathway, user group or proposed action has been justified because no clinical implementation is proposed. |
| Data source, setting and study design | Partial | Data Card names the single-center MIMIC-II/BIDMC 2001–2007 source, four adult ICU types and random A/B/C partitions. | No cross-hospital variation exists; ICU-type-specific distributions and exact patient-level dates are unavailable to this analysis. |
| Eligibility, exclusions and landmark | Supported | Age at least 16, first available ICU stay, initial stay at least 48 hours and DNR/CMO non-exclusion are explicit. | Official source does not provide a richer exclusion flow; early exits/deaths are outside the landmark cohort. |
| Participant flow and analysed sample | Partial | Set A/B/C each have 4,000 stays; Set B has 568 deaths; split sizes are fixed. | No publication-style flow diagram with every source exclusion or missing-record count can be independently reconstructed. |
| Outcome definition and timing | Partial | `In-hospital_death` is the sole binary outcome; outcome descriptors are denied from features. | Adjudication details, competing events, discharge practices and treatment-limitation effects are not available. |
| Predictor definition, measurement window and availability | Supported | Five static and 37 dynamic variables, first-48-hour bins, aggregation, mask/delta and denylist are documented and tested. | Independent unit metadata is absent; upstream unit reconciliation cannot be verified. |
| Sample-size rationale | Partial | Cohort/event counts and unstable subgroup rules are reported. | No a priori sample-size calculation or effective-complexity justification was possible for the fixed challenge cohort. |
| Missing-data handling | Supported | Missing sentinel handling, masks/deltas, median imputation and train-only fit scope are documented and tested. | No sensitivity analysis across plausible missingness mechanisms; missingness may encode care process. |
| Data partition and leakage control | Supported | Deterministic mortality×ICUType split, common assignments, fit-scope tests, outcome denylist, freeze manifest and one-success final lock. | Patient identity beyond official first-stay construction cannot be independently linked; A/B are not temporal or site held out. |
| Model specification and training | Supported | Logistic, LightGBM, GRU-D and TCN code/configs, fixed seeds, class weighting, refit and promotion rule are public. | Trained artifacts and source data are not redistributed, so exact prediction reproduction requires licensed source acquisition and retraining. |
| Hyperparameter selection and optimism control | Supported | Limited grids and preregistered validation rule are documented; Set B was accessed after freeze once. | No repeated external cohorts; development uncertainty is not eliminated by a single same-source holdout. |
| Calibration method | Partial | Platt fit scope, Brier, fixed-width ECE, apparent intercept/slope code and bootstrap stability tool are present. | No external calibration intercept/slope or contemporary/site calibration evidence; ECE depends on binning. |
| Threshold selection | Partial | Set A calibration-only rule targets specificity at least 0.90 and maximises sensitivity; bootstrap stability code is available. | No clinical action, harm, cost, capacity or preference study validates this research operating point. |
| Discrimination, calibration and classification performance | Supported | AUPRC, AUROC, Brier, ECE, sensitivity, specificity, PPV/NPV and confidence intervals are machine readable. | Evidence is one historical same-source holdout only. |
| Uncertainty | Supported | 2,000 outcome-stratified percentile bootstrap intervals and fixed seed are recorded. | No uncertainty propagation across site/time shift or clinical action consequences. |
| Class imbalance | Supported | Outcome prevalence, AUPRC priority, class weighting and PPV/NPV are reported. | No decision-analytic cost weighting beyond the descriptive threshold analysis. |
| Subgroup performance and fairness | Partial | Prespecified age, gender and ICUType groups include counts, events, intervals and instability flags. | Fields are limited, some groups are small, representativeness is uncertain and no fairness conclusion is supported. |
| Explainability | Supported | TreeSHAP/occlusion methods and non-causal interpretation are documented. | No clinician comprehension, actionability or human-factors study. |
| Input quality, OOD and abstention | Partial | Schema denial, train-derived missingness/value-pattern anomaly gate and outcome-free monitoring contract are executable. | No external OOD benchmark, detection sensitivity/specificity, false-abstention study or validated physiological unit engine. |
| Clinical utility and decision analysis | Missing | Decision curve is labelled descriptive and non-clinical. | No intervention, workflow, harm-benefit, capacity, randomised, prospective or impact evaluation. |
| External, temporal and geographic validation | Missing | Absence is explicit in README/cards. | Requires independent contemporary cohorts with site/time separation and prespecified analysis. |
| Model updating | Missing | Automatic retraining and threshold changes are prohibited. | No approved updating/recalibration protocol or new validation cohort. |
| Open science, protocol, code and data availability | Partial | Source, tests, CI, CFF, license, Data/Model Cards, schema and aggregate receipt are public; data license is explicit. | Internal protocol history is local-only; raw data and trained artifacts cannot be redistributed; no archival DOI yet. |
| Patient and public involvement | Missing | None is claimed. | A clinical programme would need documented patient/public and professional involvement before prospective evaluation. |
| Discussion and limitations | Supported | Landmark, temporal/practice shift, missingness, fairness, generalisability and non-clinical boundaries are explicit. | Limitations need independent peer review in a manuscript. |

## PROBAST+AI concern matrix

The judgements below are conservative repository-owner assessments. They do not replace independent PROBAST+AI review.

| Domain | Development/evaluation concern | Applicability concern | Evidence-based reason |
| --- | --- | --- | --- |
| Participants and data sources | **Some concerns** | **High for present-day clinical use** | Fixed challenge cohort, single-center historical source with four adult ICU types, 48-hour survivor/retention landmark, random same-source split and no site/time identifiers. |
| Predictors and input quality | **Some concerns** | **High outside the challenge schema** | Predictors precede the outcome and leakage denylist is strong, but missingness reflects care process, unit metadata is incomplete and robust value guard is not a clinical plausibility validator. |
| Outcome | **Some concerns** | **High for broader care value** | In-hospital mortality is objective and official, but discharge practice, DNR/CMO, competing events and avoidable harm are not represented. |
| Analysis and model development | **Some concerns** | **High for deployment** | Common split, limited search, class weighting, calibration-only threshold and one-success final lock are strong; calibration set is 600, threshold and calibrator share it, and there is no external validation. |
| Evaluation evidence | **Some concerns** | **High for any claimed clinical setting** | Set B is held out after freeze with bootstrap uncertainty, but remains a self-audited historical same-source random holdout. |
| Fairness and subgroup evidence | **High concern for fairness claims** | **High** | Prespecified descriptive groups exist, but protected attributes, sample sizes and representativeness do not support fairness assessment. |
| Clinical utility, human factors and implementation | **High concern / evidence absent** | **High** | No prospective workflow, alert-response, impact, harm-benefit, patient/public involvement or human-factors evaluation. |

## Overall judgement

- **Research software quality:** credible and unusually auditable for a portfolio/research artifact once CI and container gates are green.
- **Prediction-study evidence:** useful internal development plus one historical same-source held-out evaluation; not external clinical validation.
- **Risk of overclaim:** controlled only if README/cards preserve the current landmark, same-source, calibration-estimator, abstention and utility limitations.
- **Clinical applicability:** high concern; no clinical or long-term-care use is supported.
- **Next evidence-producing study:** a prespecified temporal and site-separated external validation with unit/schema reconciliation, calibration intercept/slope, threshold stability, abstention performance, subgroup uncertainty and an independently reviewed analysis plan.
