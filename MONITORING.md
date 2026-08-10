# CareRisk 48H Monitoring Contract

## Scope

This contract defines offline, aggregate monitoring for research evaluation or a separately governed shadow deployment. It does not authorize clinical use. The frozen Set B result is a batch research artifact; it is not a live monitoring baseline or deployable clinical bundle.

`carerisk48h.monitoring.build_monitoring_report` compares a reference window with a current window without using outcomes or patient identifiers. Its output is aggregate-only.

## Baseline and windows

- Preferred research baseline: the approved Set A train input-quality distribution used to fit the guard.
- Deployment/shadow baseline: a separately approved local baseline collected after schema, unit, cohort and governance review. Do not silently substitute Set A if the operational population differs.
- Evaluate at least weekly or after each 200 successfully parsed records, whichever is later. Smaller windows may be retained for troubleshooting but must be labelled unstable.
- Count schema-rejected inputs separately because they never reach the guard.
- Keep reference definition, software version, config hash, input schema version, guard version and UTC window boundaries with every report.

## Required outcome-free signals

| Domain | Signal | Interpretation |
| --- | --- | --- |
| Schema | rejection count and rate | Contract, timestamp, category or finite-number failures. |
| Missingness | dynamic variable coverage, log measurement count, core vital groups | Measurement-process shift; may reflect workflow rather than physiology. |
| Pattern anomaly | IsolationForest score | Train-derived missingness-pattern difference, not external OOD validity. |
| Value pattern | robust value-shift score | Possible scale/unit/equipment/population shift; not a physiological validity guarantee. |
| Abstention | rate and fixed-code reason rates | Fraction for which exact probability is hidden; unknown reason text is bucketed as `other`. |
| Prediction | probability PSI among displayed predictions | Model-output distribution shift; not performance drift. |
| Operations | batch size, failure count and latency outside this module | Engineering health, not model validity. |

Population Stability Index (PSI) uses reference-derived quantile bins. `0.20` is the default research alert threshold. An absolute abstention or schema-rejection rate change of `0.10` is the default rate alert. These are review triggers, not validated clinical limits.

## Outcome-linked monitoring

Without delayed outcomes, do not claim AUROC, AUPRC, Brier, ECE, calibration slope/intercept, sensitivity, specificity or clinical utility drift. When outcomes become available under an approved protocol:

- verify cohort and label definition before linkage;
- report delay and completeness of outcome capture;
- recompute discrimination and calibration with uncertainty;
- stratify by prespecified site/time/population groups only when denominators support it;
- compare against a prospectively declared reference and avoid repeated uncorrected significance testing;
- never recalibrate, retrain or change the research operating point automatically.

## Alert response

1. Freeze automated probability display for affected inputs when schema or guard failures rise materially.
2. Confirm software/config/schema version and rule out instrumentation or unit changes.
3. Review aggregate missingness, value-pattern and reason-rate changes; do not export individual records into the repository.
4. Decide whether the window is out of scope, a data-quality incident or a candidate distribution shift.
5. Require governance approval and independent validation before any model, calibrator or threshold change.
6. Record the decision, evidence, owner and resolution time. An alert can be closed as explained, mitigated or unresolved; it must not be deleted silently.

## Privacy and retention

Monitoring reports must not contain `RecordID`, raw measurements, free text, individual probabilities, outcomes or row-level explanations. Reason strings are converted to a fixed code vocabulary, unknown values are bucketed as `other`, and repeated reasons count at most once per assessment. Signal availability counts/rates and `not_comparable` states must remain visible so missing probability or guard telemetry is not silently omitted. Store only aggregate distributions, counts/rates, version metadata and alert decisions. Apply the receiving institution's privacy, security and retention controls before any real-world use.

## Known limitations

- PSI depends on binning and sample size; it does not identify a causal source of shift.
- Train-derived anomaly thresholds can miss clinically implausible values seen during training and can flag legitimate rare physiology.
- The inference payload has canonical units but no independent unit metadata, so unit reconciliation remains an upstream responsibility.
- Monitoring cannot repair the absence of temporal, site-held-out, external, prospective or clinical-utility validation.
