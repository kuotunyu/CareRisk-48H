# CareRisk 48H — Evidence & Abstention Explorer Design

**Date:** 2026-08-31
**Status:** Implementation authorized; Task 5 held until fresh authority review of the current docs-only correction
**Product surface:** Gradio Docker Space
**Canonical future destination:** `https://huggingface.co/spaces/steven0226/carerisk-48h`
**Evidence release:** GitHub tag `v0.2.0`
**Evidence tag object:** `2f1ddb0e2276fa894e124b856de488e31e21e88c`
**Evidence tag commit:** `f4c820cce953f401c1ec525bd8df3a3c1678bbf3`
**Design base:** `11184984ddd553aa3b45a3d5fc0ea4a866877722`

## 1. Decision and scope

Build a public, synthetic-only Hugging Face Docker Space named **CareRisk 48H — Evidence & Abstention Explorer**. The Space is an evidence viewer and an abstention-state explainer. It is not a patient-risk predictor, model-serving endpoint, clinical workflow simulation, or upload surface.

The MVP has two isolated information paths:

1. A read-only evidence path that renders a small, fixed subset of aggregate metrics from the exact `v0.2.0` final-result receipt and release manifest.
2. A fixed-scenario path that renders one of four abstract, in-memory synthetic gate states. It displays only `evidence available` or `evidence withheld` and enumerated reasons.

No patient-like payload crosses either path. No model, calibrator, threshold procedure, guard artifact, prediction function, or trained-data-derived runtime object is present in the Space.

This specification authorizes no product implementation, Space creation, upload, GitHub About change, deployment, or remote mutation. Those remain behind later written approvals.

## 2. Goals

- Make calibration, abstention, provenance, and claim limits understandable to portfolio reviewers within one page.
- Ensure every quantitative UI value is parsed from the exact committed aggregate receipt rather than copied into application source.
- Demonstrate fail-closed evidence validation and a bounded capability surface.
- Make it technically impossible through the intended static UI and outer public-surface firewall to enter, upload, paste, or submit arbitrary patient data.
- Produce an exact allowlist export from GitHub source into a separate Hugging Face repository without mirroring GitHub history.
- Keep runtime CPU-only, non-root, read-only except for a bounded ephemeral `/tmp`, and functional with external networking disabled.
- Preserve Apache-2.0 code licensing while clearly separating PhysioNet data and data-derived evidence licensing and attribution.

## 3. Non-goals

- No editable JSON, code editor, textbox, dataframe editor, file upload, image/audio/video input, chat input, or free-form API payload.
- No live probability, raw score, calibrated score, risk class, case recommendation, threshold comparison, threshold-based case decision, causal explanation, feature contribution, or clinical action.
- No model weights, model bundles, `joblib`, pickle, LightGBM, SHAP, scikit-learn, PyTorch, NumPy, pandas, matplotlib, Plotly, or existing inference/guard code.
- No real, deidentified, pseudonymized, or row-level PhysioNet data.
- No final evaluation rerun, receipt regeneration, Set B access, Set C access, model refit, calibration refit, or threshold selection.
- No runtime network fetch from GitHub, Hugging Face Hub, PhysioNet, CDNs, analytics services, or other external origins.
- No final-evaluation overview image in MVP. `docs/assets/final-evaluation-overview.png` remains excluded until an independently approved public hash-provenance relationship exists.
- No monitoring, user analytics, telemetry, feedback capture, persistence, session history, or logging of user interaction values.
- No mirroring of the GitHub repository or its commit history into the Hugging Face repository.

## 4. Claim ceiling exact-copy contract

The following two paragraphs are normative copy. Punctuation, capitalization, English terms, and paragraph order must be preserved in the rendered app and in the public Space card.

**Primary zh-TW claim ceiling:**

> 僅供研究與教育；不是臨床診斷、治療、分流、資源配置或照護決策工具。本 Space 僅使用內建 synthetic gate-state scenarios，不接受、儲存或處理任何使用者提供的病人資料；不輸出 live probability、risk class、case recommendation 或 threshold-based case decision。

**Brief English safety subtitle:**

> Research and education only. Non-clinical and synthetic-only. No patient data entry or upload, no live predictions, and no care decisions.

No shorter wording may replace these paragraphs in the primary surface. Other sections may repeat a shorter reminder only after the exact copy has appeared.

### 4.1 DOM and focus order

Within the app-owned root `#carerisk-space-root`, document order is fixed:

1. `header` containing the product name and one-sentence evidence-explorer description.
2. `section#claim-ceiling[role="note"]` containing the exact zh-TW paragraph followed by the exact English subtitle.
3. `section#scenario-explorer` whose scenario radio group is the first app-owned focusable element.
4. `section#scenario-result[aria-live="polite"]` containing the synthetic gate-state result.
5. `section#receipt-evidence` containing receipt-backed aggregate evidence.
6. `section#provenance` containing release, manifest, source, and license information.

There must be no app-owned `a[href]`, `button`, `input`, `select`, `textarea`, element with non-negative `tabindex`, or other focusable element before `#claim-ceiling` has rendered in full. Hugging Face platform chrome outside `#carerisk-space-root` is outside this contract.

The claim ceiling must be visible without expanding an accordion or opening a tab. CSS must not use fixed overlays, clipping, or scroll containers that can hide any part of it. At both required review viewports, the entire claim ceiling and the beginning of the first scenario control must appear in the initial viewport.

## 5. Page architecture

### 5.1 Header

- Product name: `CareRisk 48H — Evidence & Abstention Explorer`.
- One sentence: `以可稽核的 aggregate receipt 與固定 synthetic states 展示 calibration、evidence gates 與 abstention。`
- No model badge, clinical iconography, patient avatar, risk traffic light, “AI diagnosis” language, score, leaderboard, or performance superlative.

### 5.2 Fixed scenario explorer

The only user-controlled value is a single-select radio group. It has no preselected value. Its four allowed IDs, visible labels, output states, and reasons are immutable application constants:

| Scenario ID | zh-TW label | Output state | Enumerated reason text |
| --- | --- | --- | --- |
| `synthetic_evidence_available` | `Synthetic A｜所有示意 evidence gates 通過` | `evidence available` | `所有示意 evidence gates 均通過；此狀態不產生分數。` |
| `synthetic_schema_withheld` | `Synthetic B｜schema contract 不完整` | `evidence withheld` | `示意 schema contract 未通過，因此研究 evidence 不顯示。` |
| `synthetic_coverage_withheld` | `Synthetic C｜measurement coverage 不足` | `evidence withheld` | `示意 measurement coverage 不足，因此研究 evidence 不顯示。` |
| `synthetic_value_pattern_withheld` | `Synthetic D｜value pattern 超出 synthetic reference` | `evidence withheld` | `示意 value pattern 超出 synthetic reference，因此研究 evidence 不顯示。` |

The scenario objects contain only `id`, `label_zh_tw`, `state`, `reason_zh_tw`, and fixed gate booleans named `schema_contract`, `measurement_coverage`, and `value_pattern`. They contain no age, sex/gender, ICU type, measurement, timestamp, variable, record ID, label, outcome, probability, threshold, or model output.

The scenario registry is an immutable in-memory tuple. It is not loaded from a user-controlled file, request body, environment variable, URL, database, or remote service. Unknown, missing, duplicated, non-string, or altered scenario IDs return the safe state `evidence withheld` with reason code `unknown_synthetic_scenario`; they never echo the submitted value.

The scenario result may render the three gate names and pass/withheld status. It must not render numeric gate thresholds, OOD scores, coverage percentages, measurement counts, physiologic values, probability availability, or “human review” language that could imply a live clinical workflow.

### 5.3 Receipt-backed evidence

The evidence panel reads from `evidence/final-result-receipt.json` only after all validation gates in Section 7 pass. It renders:

- Dataset name and role, `n`, events, and prevalence.
- AUPRC estimate and 95% interval.
- AUROC estimate and 95% interval.
- Brier estimate and 95% interval.
- ECE estimate and 95% interval.
- Bootstrap method, samples, and seed.
- Evaluation status, one-success count, and final-lock status.
- The receipt `use_limitation` verbatim.

Formatting may round for display but must retain a machine-checkable relationship to the parsed value: AUPRC/AUROC/Brier/ECE estimates and interval endpoints display to three decimals, prevalence to one decimal percent, and counts as integers. Tests compare formatted UI text against values parsed from the receipt, never against duplicate application constants.

The primary MVP UI does not render the receipt threshold, confusion matrix, PPV, NPV, sensitivity, specificity, individual or subgroup results, candidate hashes, or artifact hashes. The receipt remains publicly available as a file for auditors, but the UI does not provide a raw JSON editor or JSON output component.

The calibration section consists of Brier and ECE estimate/interval rows with explanatory labels. It does not reconstruct reliability bins, invent calibration intercept/slope, display the excluded aggregate evaluation image, or call the same-source result external calibration.

### 5.4 Provenance and limitations

The provenance section renders only values validated from the release manifest and deployment manifest:

- Evidence tag `v0.2.0` and its immutable tag commit.
- Receipt Git blob SHA and SHA-256.
- Space app GitHub source commit recorded in the deployment manifest.
- Public destination repository identifier.
- `scientific_result_changed=false`, `set_b_rerun=false`, `set_c_used=false`, `frozen_model_changed=false`, and `threshold_changed=false` as release relationship statements.
- The release manifest’s five limitations, without positive reinterpretation.

External links to the GitHub tag, source repository, receipt, LICENSE, and NOTICE may appear only in this section, after the first scenario control. Clicking them is a user navigation; the application itself performs no fetch.

## 6. Component and data-flow design

The clean Space application is a standalone package named `carerisk_space`. It has these bounded units:

| Unit | Responsibility | Inputs | Outputs | Dependencies |
| --- | --- | --- | --- | --- |
| `contracts.py` | Constants, claim copy, reason codes, strict schemas, hash helpers | Public bundle bytes | Validated immutable values or bounded error code | Python standard library only |
| `evidence.py` | Read and validate receipt, release metadata, deployment manifest; format approved evidence | Three committed JSON files | `EvidenceViewModel` or `EvidenceFailure` | `contracts.py`, standard library |
| `scenarios.py` | Own four immutable abstract scenarios and exact-ID lookup | Enumerated scenario ID | `ScenarioViewModel` | `contracts.py`, standard library |
| `ui.py` | Pre-render the safe or evidence-failure static document, derive exact locked-package asset membership, and enforce the outer ASGI public-surface firewall | Evidence result, scenario registry, and the two source-audited Gradio package roots | Zero app-owned input/dependency/function/API Gradio Blocks plus immutable asset membership and `PublicSurfaceGuard` | Gradio, local units, minimal ASGI types |
| `app.py` | Compose an empty FastAPI parent, mount Gradio, wrap the parent with the guard, and run fixed Uvicorn on port 7860 | No user configuration | Running local server | FastAPI, Gradio, Uvicorn, `ui.py` |

Startup flow:

1. Read only the three allowlisted JSON files from package-relative paths.
2. Validate byte hashes, Git blob relationship, schemas, release relationship, and manifest path set.
3. If any gate fails, construct the evidence-failure UI in Section 12. Do not construct scenario controls or metric cards.
4. If all gates pass, call the canonical `render_scenario` function at startup for each of the four fixed IDs and embed all four bounded results into one static HTML/CSS radio explorer.
5. Browser interaction changes only native radio/CSS visibility among already-rendered panels. The application owns zero inputs, dependencies, functions, or API endpoints, and normal browser interaction generates zero POST, event, session, or queue traffic. Pinned Gradio still initializes internal queue/state machinery and reports `config.enable_queue == true`; the outer guard makes its queue, event, and session routes unreachable, and review probes require zero public-interaction state delta rather than claiming that framework state does not exist.

After startup there is no callback or event dependency. The application accepts no mappings, lists, files, paths, URLs, request objects, headers, cookies, query parameters, free text, or scenario values at the Gradio application layer.

## 7. Evidence and provenance validation

### 7.1 Fixed evidence anchors

The exact evidence anchors are:

- Release tag: `v0.2.0`.
- Annotated tag object: `2f1ddb0e2276fa894e124b856de488e31e21e88c`.
- Tag commit: `f4c820cce953f401c1ec525bd8df3a3c1678bbf3`.
- Release manifest source path: `docs/release-v0.2.0.json`.
- Receipt source path: `docs/final-result-receipt.json`.
- Receipt Git blob SHA: `b13ec7655bbdb8db1079c3b4793a0bf5590ef69c`.
- Receipt SHA-256: `d32d833af25e4ebb2f5bd06b64343eb36d7cd180c8e9777f539f6401b78064b3`.
- The canonical receipt byte domain is the 3,363 unmodified LF bytes emitted by `git cat-file blob b13ec7655bbdb8db1079c3b4793a0bf5590ef69c`; no checkout, text-mode, or line-ending normalization is permitted. The rejected noncanonical CRLF working-tree diagnostic SHA-256 `f1eb4958f253bf016bc73c405f498055b36cb8b7100654d8868a088f31d426fc` must not be exported or used for validation.
- Formal metrics SHA-256 named inside the receipt: `808525afad2ec550e8059c4ba37c2f5aaf8af748873a5a590dff7f1aeaaf47af`.

The export process must extract the receipt and release manifest from the tag commit with Git object reads, not copy them from an arbitrary working tree.

### 7.2 Runtime receipt gates

Receipt validation is fail-closed and must verify all of the following before parsing values for display:

1. File exists at exactly `evidence/final-result-receipt.json` and is a regular file, not a symlink.
2. Raw-byte SHA-256 equals the fixed receipt SHA-256 over the unmodified Git-blob bytes; CRLF-normalized bytes fail this gate.
3. Git blob hash computed as SHA-1 over `blob <byte-length>\0<raw-bytes>` equals the fixed receipt Git blob SHA.
4. UTF-8 JSON parses without duplicate keys, NaN, Infinity, or trailing data.
5. Top-level keys exactly equal `confidence_intervals`, `dataset`, `evaluation`, `evaluation_status`, `metrics`, `model`, `privacy`, `provenance`, `schema_version`, `title`, and `use_limitation`.
6. `schema_version == 1`, `evaluation_status == "final"`, `privacy.aggregate_only == true`, and `evaluation.set_b_final_evaluation_successes == 1`.
7. `evaluation.final_lock_status == "locked_after_one_success"`.
8. Every displayed metric and interval is finite, in `[0, 1]`, interval-ordered, and has interval estimate equal to the corresponding metric.
9. Dataset role is `final_test`, `n == 4000`, events `== 568`, and prevalence is finite and consistent with the receipt value.
10. Bootstrap method is `stratified percentile`, samples `== 2000`, and seed `== 2026`.
11. `provenance.formal_metrics_sha256` equals the fixed formal metrics hash.
12. The privacy exclusion list contains the seven committed exclusions and no displayed field comes from those excluded categories.

### 7.3 Runtime release relationship gates

Release validation verifies:

1. `evidence/release-v0.2.0.json` is a regular non-symlink file whose SHA-256 and size equal its deployment-manifest entry.
2. `schema_version == 1`, `release == "v0.2.0"`, and `release_kind == "research-software-portfolio-closure"`.
3. `scientific_evidence.final_result_receipt` identifies the source receipt path.
4. `scientific_evidence.final_result_receipt_git_blob_sha` equals the validated receipt blob SHA.
5. The five scientific-change booleans are all false.
6. The limitations array exactly contains the committed five limitations.

The Space performs no `git` command and no remote verification at runtime. Tag and source relationships are established during clean export and represented by the signed-off deployment manifest; runtime revalidates the local immutable bytes and manifest consistency.

## 8. Source-to-destination clean export

### 8.1 Separate histories

The GitHub source repository remains canonical for app source and evidence. The Hugging Face Space is a separate repository whose initial public commit contains only the clean export. It must not share Git object ancestry, branches, tags, reflogs, `.git` directory, or deleted history with GitHub.

Updates are regenerated from an exact GitHub source commit and exact evidence tag. They are committed as ordinary destination updates; GitHub history is never mirrored or force-pushed into Hugging Face.

### 8.2 Non-self-referential provenance sequence

Implementation uses two source commits so the deployment manifest can name an immutable Space app source commit without self-reference:

1. **App source commit:** contains the reviewed Space app, tests, locks, SBOM, license inventory, and export tooling. Its SHA becomes `space_app_source_git_sha`.
2. **Export-manifest commit:** adds the deployment manifest that records the app source commit, evidence tag/object/commit, exact source-to-destination paths, byte hashes, sizes, capabilities, base-image digest, and lock/SBOM/license hashes.

The export reads app files from the app source commit, evidence/legal files from the `v0.2.0` tag commit, and the deployment manifest from the export-manifest commit. The Hugging Face destination commit is recorded after upload in a separate post-deployment audit record; it is not self-embedded in the destination commit.

Both commits and any remote actions require later approval and are not created by this design task.

### 8.3 Exact destination allowlist

The clean export contains exactly these destination paths:

| Source category | Destination path | Capability |
| --- | --- | --- |
| Space source | `README.md` | Space card and safety copy |
| Space source | `Dockerfile` | Container build |
| Space source | `requirements.lock` | Hash-locked runtime dependencies |
| Space source | `requirements-dev.lock` | Hash-locked verification dependencies |
| Space source | `app.py` | Fixed FastAPI mount, outer guard composition, and programmatic Uvicorn entry point |
| Space source | `carerisk_space/__init__.py` | Package identity only |
| Space source | `carerisk_space/contracts.py` | Contracts and validation helpers |
| Space source | `carerisk_space/evidence.py` | Read-only evidence loader |
| Space source | `carerisk_space/scenarios.py` | Fixed in-memory scenarios |
| Space source | `carerisk_space/ui.py` | Gradio presentation |
| `v0.2.0` evidence | `evidence/final-result-receipt.json` | Aggregate final evidence |
| `v0.2.0` evidence | `evidence/release-v0.2.0.json` | Release/evidence relationship |
| Export-manifest commit | `deployment-manifest.json` | Source/destination provenance and allowlist |
| `v0.2.0` legal metadata | `LICENSE` | Apache-2.0 code license |
| `v0.2.0` legal metadata | `NOTICE` | PhysioNet attribution and boundary |
| `v0.2.0` legal metadata | `CITATION.cff` | v0.2.0 citation |
| Space source | `SBOM.spdx.json` | Exact source/runtime dependency SBOM |
| Space source | `THIRD_PARTY_LICENSES.json` | Dependency license inventory |
| Space source | `tests/test_claim_contract.py` | Exact copy and DOM-order contract |
| Space source | `tests/test_evidence_contract.py` | Receipt/release fail-closed contract |
| Space source | `tests/test_scenario_contract.py` | Fixed scenario and no-score contract |
| Space source | `tests/test_gradio_contract.py` | Static component/config, outer-ASGI, route, and API-absence contract |
| Space source | `tests/test_export_contract.py` | Exact path/hash/denylist contract |
| Space source | `tests/test_container_contract.py` | Container/runtime contract |

No directory wildcard is allowed. The export manifest lists every destination path explicitly, sorted by destination path. For every allowlisted file except `deployment-manifest.json`, it records source ref, source path, destination path, SHA-256, byte size, media type, and one capability from `runtime_code`, `evidence`, `legal`, `metadata`, `supply_chain`, or `test`.

The manifest lists itself in the path allowlist but does not attempt to embed its own hash. CI records the manifest SHA-256 in its immutable verification output, and the later post-deployment audit record binds that hash to the destination commit.

The exporter reads committed Git blobs into a fresh temporary directory, rejects symlinks and path traversal, compares the final recursive file set to the exact destination allowlist, verifies every hash and size, and refuses a dirty or mismatched source ref. It never copies the repository working directory wholesale.

### 8.4 Denylist

Any match is a hard export failure, including if a similarly named path is newly added:

- `.env`, `.env.*`, credentials, tokens, keys, cookies, auth state, Space Secrets, or Space Variables.
- `.git`, `.github`, worktrees, bundles, patches, reflogs, or GitHub history exports.
- `data`, `artifacts`, `models`, `checkpoints`, `results`, `reports`, notebooks, caches, temporary files, coverage output, or build output.
- Any raw/processed PhysioNet data, outcomes, row-level data, record IDs, predictions, subgroup rows, error cases, access ledger, final lock contents, artifact map, environment capture, or real-data-derived guard/model bundle.
- File suffixes `.joblib`, `.pkl`, `.pickle`, `.pt`, `.pth`, `.ckpt`, `.onnx`, `.parquet`, `.feather`, `.arrow`, `.npy`, `.npz`, `.csv`, `.tsv`, `.zip`, `.tar`, `.gz`, or database files.
- `docs/assets/final-evaluation-overview.png` and all other plots or screenshots.
- Existing `app/dashboard.py`, existing root `app.py`, `src/carerisk48h`, `configs/inference_schema.json`, training/downloader/evaluation scripts, and the existing synthetic scoring bundle path.
- `AGENTS.md`, `PROJECT_PLAN.md`, `.agents`, local design/product documents, interview guides, handoffs, or internal governance evidence.
- Any path not present in the exact allowlist, any file larger than 1 MiB, any symlink, device, FIFO, executable binary, or archive.

## 9. Import and capability boundary

Runtime application modules may import only:

- Python standard-library modules required for immutable data structures, strict JSON parsing, HTML escaping, hashing, package-relative read-only paths, and typing.
- The exactly locked `gradio==6.26.0` package and its already locked FastAPI/Uvicorn runtime dependencies. `app.py` imports Gradio's mount API, FastAPI, and Uvicorn only for the fixed parent/mount/server composition. `ui.py` imports only the Gradio `Blocks`/`HTML` presentation surface plus the source-audited `gradio.routes.BUILD_PATH_LIB` and `gradio.routes.STATIC_PATH_LIB` constants needed to construct the immutable packaged-asset membership set described in Section 13; no other Gradio route object or framework internal is authorized.
- Only the Starlette ASGI interfaces required by the approved pure-ASGI boundary: `ASGIApp`, `Scope`, `Receive`, and `Send`. `PublicSurfaceGuard` is direct ASGI composition, not Starlette/FastAPI middleware registration. This does not authorize request parsing, file/static responses, network clients, background work, temporary files, or writes.
- Local `carerisk_space` modules.

Application-source AST and import-graph tests reject:

- `joblib`, `pickle`, `cloudpickle`, `dill`, `eval`, `exec`, dynamic imports, and plugin discovery.
- `numpy`, `pandas`, `scipy`, `sklearn`, `lightgbm`, `shap`, `torch`, `tensorflow`, `onnx`, `matplotlib`, and `plotly`.
- `requests`, `httpx`, `urllib.request`, `huggingface_hub`, cloud SDKs, database clients, SMTP, SSH, and outbound socket clients.
- `subprocess`, shell execution, process spawning, file watching, and background workers.
- Application writes through `open` write/append/update modes, `Path.write_text`, `Path.write_bytes`, rename, replace, delete, mkdir, or persistence APIs.
- Reading environment variables, command-line file paths, user home, current working directory discovery, or arbitrary absolute paths.

The only application file reads are package-relative reads of the three committed JSON files plus the one startup-only, read-only inventory of the two exact locked Gradio package roots named above. That inventory accepts only regular non-symlink files whose resolved paths remain under the resolved source-audited root; it performs no write, network operation, package discovery, user/site/evidence/temp traversal, or arbitrary-path read. Application source does not import `os` or read the process environment. Docker and test infrastructure may set or poison operational environment values to verify the boundary, but product code has no environment-based configuration and the deployed Space requires zero user-defined Secrets or Variables.

### 9.1 Dynamic reflection is denied by construction

The public application is intentionally simple enough that it needs no dynamic attribute discovery or metaprogramming. Every application-source module therefore rejects direct or aliased use of `getattr`, `setattr`, `delattr`, `hasattr`, `vars`, `globals`, `locals`, `eval`, `exec`, `compile`, and `__import__`; calls through `__getattribute__`, `__getattr__`, `__setattr__`, or `__delattr__`; `__dict__` lookup or mutation; `operator.attrgetter`/`methodcaller`; `inspect.getattr_static`; and an equivalent callable, mapping, or alias chain used to obtain or mutate an attribute dynamically. A literal string does not make a reflective lookup acceptable. Unknown or newly encountered reflective forms fail closed rather than being interpreted by an increasingly general source evaluator.

This prohibition also governs the public bundle's Gradio contract source. That file uses a closed-world source-token contract rather than attempting to resolve reflection data flow: reflection origins are rejected across the whole file before exact direct builder/guard contexts are checked. The only builtin reflection calls permitted are the existing exact `getattr(inner, "original_router", None)` and `getattr(socket, "AF_UNIX", None)` probes. They cannot be aliased or shadowed, and changing their receiver, member, arity, default, or keywords is a design-review condition. Other test-only introspection is not implicitly allowed merely because its receiver appears unrelated.

Normal syntax-defined Python identities are not reflection capabilities: `__future__` imports, `__name__` and `__file__` reads, `__all__` declarations, and the required `__init__`/`__call__` method definitions remain permitted. They may not be used as a bridge to retrieve or mutate another attribute. The authoritative entry point continues to use direct named calls only: one `FastAPI(...)`, one `gr.mount_gradio_app(...)`, one `build_package_asset_membership()`, one `PublicSurfaceGuard(...)`, and one `uvicorn.run(...)` under the main guard.

This is a policy boundary, not a request to build a Python interpreter. The scanner proves absence of the forbidden reflection surface and then verifies the existing exact direct composition. Any future legitimate need for reflection requires a new design review; it cannot be introduced by extending an alias allowlist inside a feature task.

Enforcement is syntactic and reference-based rather than call-resolution based. A load of a forbidden builtin name or the implicit `__builtins__` mapping is itself a violation, whether it appears as a direct call, assignment, default argument, lambda capture, named expression, container member, mapping lookup, or another alias source. Import syntax cannot launder the boundary: both the original imported name and its effective local binding are checked, so `from allowed.module import __builtins__ as mapping` and equivalent dunder imports fail at the import token. Any double-underscore attribute reference is rejected, including `__dict__`, `__globals__`, `__class__`, and dynamic attribute protocol hooks; a load of a named reflection helper is rejected before alias analysis.

Every semantic double-underscore binding is rejected whether Python represents it as an `ast.Name` or as a string field: assignment/delete/loop/comprehension/with/walrus targets, parameters, function/class names, import originals and effective local aliases, exception targets, structural-pattern captures, and global/nonlocal declarations. The only exceptions are method definitions named `__init__` or `__call__` and at most one qualifying module-level literal-string `__all__` assignment target; neither exception applies to a class name, parameter, import, exception target, pattern capture, or other binding form. Duplicate, nonliteral, nested, or otherwise nonqualifying `__all__` declarations receive no exception. At name-load level only `__name__` and `__file__` are permitted. Exact dynamic protocol-name string literals are rejected so a mapping cannot install the protocol indirectly.

The builtin `type` name may be loaded only in the exact validation comparison `type(<non-starred expression>) is <allowed type name>` or `type(<non-starred expression>) is not <allowed type name>`, where the call has one positional argument, no keywords, the comparison has exactly one operator and comparator, and the comparator is the direct name `str`, `int`, or `frozenset`. These are the current application validations; the call result may not itself be called, assigned, or aliased. The module may not bind, import, define, parameterize, capture, rebind, or delete the name `type`, so the permitted load necessarily resolves to the builtin. Starred arguments, standalone one-argument calls, aliasing, and class-construction forms are forbidden.

Within the approved Python standard-library import surface, the denied dynamic class-construction sources are builtin `type` construction, all `types` APIs except `MappingProxyType`, `dataclasses.make_dataclass`, `collections.namedtuple`, and the functional `typing.NamedTuple` and `typing.TypedDict` factories. Their direct attributes and original imported names are rejected before alias flow; wildcard imports from `types`, `dataclasses`, `collections`, or `typing` are rejected. This boundary does not claim that every third-party callable is a class factory: third-party imports remain governed by the separate exact import and composition contracts. `__future__` remains an import form. This closes implicit mapping, builtin shadowing, class-body assignment/deletion, reachable standard-library dynamic-class construction, and object-protocol chains without enumerating arbitrary downstream data flow. Aliasing fails at its source token, and results are deduplicated and sorted so overlapping legacy capability checks cannot produce order- or count-dependent evidence.

The entry-point audit reports the reflection violation as the authoritative failure and does not attempt to infer a second mount or hidden route through already-forbidden syntax. Its existing structural mount, route, middleware, monkeypatch, and server counts continue to govern direct calls and ordinary non-reflective aliases.

The Gradio test-source contract rejects every load, import original/effective name, or semantic binding of the forbidden reflection builtins; `__builtins__`/`builtins`; `operator.attrgetter`/`methodcaller`; `inspect.getattr_static`, `getmembers`, and equivalent dynamic inspect members; `importlib.import_module`; and every non-allowlisted reflection-bearing dunder attribute. The two exact `getattr` callee nodes are the sole builtin-name-load exceptions. The identities `getattr`, `type`, `isinstance`, `super`, `frozenset`, `inspect`, `importlib`, `socket`, `pytest`, `ui_module`, `gr`, and `uvicorn` cannot be rebound or import-laundered outside their exact existing imports and contexts.

The file has an exact closed import surface: its 34 reviewed module-level `Import`/`ImportFrom` AST nodes, including order, original names, aliases, and imported members, are the complete allowlist; nested imports and every added, removed, reordered, aliased, or changed import require design review. The import sequence is the module-body prefix and is immediately followed by the exact `ALL_FAILURE_CODES = cast(tuple[EvidenceFailureCode, ...], get_args(EvidenceFailureCode))` assignment and then the sole exact assignment `SPACE_ROOT = Path(__file__).resolve().parents[1]`; no other statement may intervene. `Path` and `SPACE_ROOT` cannot be rebound, directly aliased as `alias = Path`, deleted, declared global/nonlocal, or imported under another effective name. The existing `real_is_symlink = Path.is_symlink` bound-method capture remains permitted. The only three `SPACE_ROOT` AST uses are that exact `Store` declaration plus the existing read-only `ui.py` source check and exact entrypoint-path `Load` contexts; every other use is rejected. This structurally excludes both alternate mutation libraries and a rewritten entrypoint root. Independently, the tokens and original/effective bindings `unittest`, `mock`, `patch`, `pytest_mock`, `mocker`, and builtin `breakpoint`, and every attribute named `patch`, are forbidden, covering `patch`, `patch.object`/`dict`/`multiple`, decorator/context-manager forms, pytest-mock fixtures, and `PYTHONBREAKPOINT`-driven import hooks. Frame, coroutine, generator, traceback, and leaked-module reflection sources are rejected receiver-independently: `gi_frame`, `cr_frame`, `ag_frame`, `tb_frame`, `f_builtins`, `f_globals`, `f_locals`, `f_back`, `_getframe`, `_current_frames`, and an attribute token named `sys`. Dynamic resolver source tokens are also forbidden: `importorskip`, `importer`, `import_from_string`, `resolve_name`, `locate`, `find_spec`, `import_plugin`, `load_setuptools_entrypoints`, `pluginmanager`, and equivalent module/callable loader members. `pytest` is closed to the current static test API contexts: `fixture`, `mark.parametrize`, `raises`, `skip`, `fail`, and annotation-only `MonkeyPatch`/`TempPathFactory`; every other `pytest` attribute and a `request` or `pytestconfig` fixture binding is rejected. The retained `importlib.util` capability is not a general import escape: exactly one `spec_from_file_location("carerisk_space_entrypoint", SPACE_ROOT / "app.py")`, one `module_from_spec(spec)`, and one `spec.loader.exec_module(entrypoint)` are permitted in the sole top-level entrypoint-contract test, with exact owner, count, direct receiver, arguments, and no keywords; `spec` and `entrypoint` cannot be rebound outside those reviewed statements. The sole `uvicorn.Config(...)` call is pinned to the reviewed `running_wire_app` fixture with direct first argument `marker` (never a string or path) and the complete current keyword/value AST. That local `marker` has exactly one assignment, `marker = AppEntryMarker(guarded, guarded.package_asset_urls)`, before the Config call; the top-level `AppEntryMarker` class identity is unique and cannot be rebound or imported, and its `ClassDef` header has no decorators, bases, keywords/metaclass, or type parameters. The only other binding named `marker` is the existing `RunningWireApp` dataclass field. `uvicorn` exposes only the reviewed direct `Config` and `Server` uses plus the entrypoint-test `run` exception.

`monkeypatch` exists only as an exact `pytest.MonkeyPatch` parameter owned by the function that uses it and cannot be rebound. `monkeypatch.setattr(...)` remains a test mutation API only as an exact direct attribute callee with a literal member name; it is not a builtin `setattr` exception and may not be aliased. Protected member literals are rejected independently of the first-argument receiver, so a module alias, registry lookup, or other receiver expression cannot launder an identity replacement. The receiver-independent protected set is `getattr`, `type`, `isinstance`, `super`, `frozenset`, `signature`, `Parameter`, `empty`, `__version__`, `AF_UNIX`, `spec_from_file_location`, `module_from_spec`, `PublicSurfaceGuard`, `create_app`, `build_package_asset_membership`, `mount_gradio_app`, and `run`. Every `Store` or `Del` attribute with one of those names is also rejected independently of its receiver. Access to an attribute token named `modules` is forbidden, as are original or effective `from sys import modules` bindings; the exact top-level `import sys` remains available only for the existing direct `sys.platform` load and the exact `monkeypatch.setattr(sys, "platform", "linux")` test call, so it cannot be aliased into a registry path. The last four protected names have exactly four full-node exceptions: one occurrence each, all owned by the sole top-level function `test_entrypoint_mount_and_uvicorn_contract_are_exact`, with exact direct receivers and replacement expressions matching the reviewed source. They remain default-denied in every other node. Existing unaliased `inspect` and `importlib.util` imports remain permitted only for their enumerated static contract uses. Any `monkeypatch` method other than the reviewed direct `setattr` calls and one exact `setenv` loop is outside this contract; in particular, `setitem` cannot mutate a module registry. The sole `setenv` occurrence is `monkeypatch.setenv(name, value)` in the sole top-level function `test_exact_instance_state_ignores_poisoned_framework_environment`, driven directly by the reviewed seven-pair literal dictionary and its `.items()` loop; its owner, count, call shape, loop target, keys, and values are frozen.

An attribute token named `build_package_asset_membership` or `PublicSurfaceGuard` is rejected on every receiver unless the receiver is the exact unshadowed `ui_module` name and its parent context is explicitly allowed. The builder appears only as a direct zero-argument call. After one test-only cleanup, the guard appears only as a direct constructor call, the sole argument to `inspect.signature(...)`, or the second argument to the exact unshadowed builtin `isinstance(...)`. Assignment, return, ordinary/two-level alias, import-from, alternate receiver, and reflective string lookup contexts fail. The exact identity exceptions retained by current test source are class-owned `__init__`/`__call__` definitions, `super().__init__()`, `gr.__version__ == "6.26.0"`, `type(exc).__name__ == "Failed"`, `__name__`/`__file__`, `__future__`, and `inspect.Parameter.empty`; their names cannot be rebound or generalized. The whole current test file is the positive fixture. Task 10 may add ordinary direct tests without a byte/hash update, but a third `getattr`, new inspect member, new dunder context, or guard/builder alias requires design review.

## 10. Dependency and supply-chain contract

- Runtime and development locks list every direct and transitive Python package with exact `==` versions and accepted distribution SHA-256 hashes.
- Docker installation uses `python -m pip install --require-hashes --no-deps -r requirements.lock`; the lock itself contains the complete transitive closure, so resolution cannot drift during build.
- The lock is compiled for the single supported Linux/Python target used by the Docker image. Cross-platform convenience ranges are not part of the public runtime contract.
- The Docker `FROM` instruction contains both an explicit CPython 3.11 slim-bookworm patch tag and its immutable OCI `sha256:` digest. A mutable tag without digest fails verification.
- The deployment manifest records the base image repository, tag, digest, runtime-lock SHA-256, development-lock SHA-256, SBOM SHA-256, and third-party-license inventory SHA-256.
- `SBOM.spdx.json` identifies the app, base image, and every locked Python distribution with version, package URL, hashes, and license expression.
- `THIRD_PARTY_LICENSES.json` contains one reviewed record per runtime and development dependency, including package, version, license expression, source URL, notice requirement, and review disposition.
- Unknown, missing, non-redistributable, or incompatible licenses block export. License conclusions are recorded as inventory evidence, not inferred from package names.
- Container scanning must report no unresolved critical or high vulnerability. A time-bounded, documented exception requires separate central approval; this design grants none.
- No build credential, private index, token, or authenticated package source is permitted.

## 11. Container and runtime contract

- Single CPU image; no CUDA base, GPU package, GPU device request, or accelerator metadata.
- App listens on `0.0.0.0:7860`; Space card declares `sdk: docker` and `app_port: 7860`.
- Final image runs as a dedicated numeric non-root UID/GID whose passwd entry uses `/usr/sbin/nologin` and whose image has no writable home. The product uses exec-form startup and never spawns or invokes a shell; Debian slim may still contain `/bin/sh`, and its physical absence is not an acceptance requirement.
- Dockerfile uses explicit `COPY` statements for runtime files only; it never uses `COPY .`.
- Runtime image excludes tests, development lock, SBOM tooling, compiler, package cache, Git, curl, wget, and shell utilities not required to launch Python.
- Workspace, application source, evidence, legal files, and dependency environment are read-only.
- Product code performs zero filesystem writes. Framework-required temporary operations, if any, are confined to an empty bounded tmpfs mounted at `/tmp`; no persistent or workspace path is writable.
- Before Python or Gradio imports, the exec-form Docker `ENTRYPOINT` invokes `/usr/bin/env -i` and rebuilds only this fixed process-environment allowlist: `PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin`, `LANG=C.UTF-8`, `LC_ALL=C.UTF-8`, `PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1`, `GRADIO_ANALYTICS_ENABLED=False`, `HF_HUB_DISABLE_TELEMETRY=True`, `GRADIO_WATCH_DIRS=`, `GRADIO_VIBE_MODE=`, `GRADIO_HOT_RELOAD=false`, `GRADIO_RUN_HISTORY=False`, `GRADIO_SSR_MODE=False`, `GRADIO_MCP_SERVER=False`, `GRADIO_ALLOWED_PATHS=`, and `GRADIO_BLOCKED_PATHS=/`. The Dockerfile retains exec-form `CMD ["python", "app.py"]`. `/usr/bin/env` is a required, inventoried runtime binary; the app never invokes a shell. Tests prove the telemetry value is exactly `True` before import, after `Blocks(analytics_enabled=False)` construction, in PID 1, and in every child; hostile `0` or secret-shaped injected values are absent.
- The runtime contract includes no `SPACE_ID`, `PORT`, secret, credential, or user-provided environment value. Docker- or Hugging-Face-injected variables are discarded by `/usr/bin/env -i`; Gradio analytics, Hugging Face telemetry, watch/vibe/hot-reload, run history, SSR, MCP, and environment-derived file allowlists are fixed closed before import. No application analytics are implemented.
- Runtime smoke uses `--network none`, `--read-only`, a bounded `--tmpfs /tmp:rw,noexec,nosuid,size=64m`, `--cpus=2`, empty CUDA visibility, and no mounted secrets or host files.
- Smoke asserts non-root UID, non-writable workspace/evidence files, successful app construction, local loopback health response, visible exact claim copy, and absence of model libraries.
- Network-disabled runtime is the authoritative no-fetch proof. Static source scans are defense in depth, not a substitute.
- If the exact candidate image lacks a usable `/usr/bin/env -i` boundary, or a later authorized Hugging Face Docker Space compatibility review shows that boundary cannot operate, implementation stops for central review; it must not replace or weaken the environment threat boundary implicitly.

## 12. Evidence-failure UX

Validation failure must still produce a healthy static page so a broken evidence artifact cannot be mistaken for successful metrics.

The failure page contains, in order:

1. Product header.
2. The exact claim ceiling.
3. `Evidence unavailable` heading.
4. zh-TW explanation: `公開 evidence 未通過完整性驗證，因此本頁不顯示 metrics 或 synthetic gate states。`
5. Brief English line: `Evidence integrity checks failed; metrics and scenarios are disabled.`
6. Exactly one bounded reason code from `receipt_missing`, `receipt_hash_mismatch`, `receipt_schema_invalid`, `release_relationship_invalid`, or `deployment_manifest_invalid`.

It contains no scenario control, metric value, partially parsed evidence, path, raw exception, stack trace, file content, environment value, or retry/upload control. The server logs the same bounded reason code and no raw payload.

## 13. Gradio component, config, and API contract

The normal app is a single static HTML/CSS document inside one non-interactive `gr.HTML`. At startup it calls the existing canonical `render_scenario` function exactly once for each of the four fixed scenario IDs and embeds all four escaped results. Native HTML radio controls and CSS sibling selectors switch visibility locally. There is no app-authored inline JavaScript, Gradio input component, function binding, callback, or request-triggered render. The evidence-failure app uses the same one-document shape but contains no radio or other control. Gradio's pinned browser shell still contains its own framework JavaScript; the contract is that application HTML and component configuration add none.

The application and capability tests are pinned to Gradio `6.26.0`. The exact contract is:

- `create_app` constructs `gr.Blocks(analytics_enabled=False, title=PRODUCT_NAME)`, explicitly fixes per-instance state to `dev_mode=False`, `vibe_mode=False`, `root_path=""`, `api_open=False`, and `space_id=None`, and constructs every `gr.HTML` with `js_on_load=None`. Product source does not import `os` or read environment variables.
- `Blocks.get_config_file()` has one non-interactive HTML component in the normal and each failure state, zero input components, `dependencies == []`, and no functions (`len(app.fns) == 0`). Every HTML component config omits `js_on_load` and `server_functions`, has `buttons == []` and `_selectable == false`, and has no event dependency or other input capability. Source mutation tests fail if any `gr.HTML` omits the explicit `js_on_load=None` argument. `Blocks.get_api_info()` is exactly `{"named_endpoints": {}, "unnamed_endpoints": {}}`; every public `/gradio_api` route, including `/gradio_api/info`, is blocked by the outer guard.
- The normal document contains exactly four native radios in one named group, four exact fixed IDs/labels, and four pre-rendered scenario panels. The claim ceiling and English subtitle precede the first focusable radio in DOM order. CSS makes only the checked radio's corresponding panel visible; keyboard focus and checked-state transitions work without JavaScript or network activity. All five evidence-failure documents contain zero controls, metrics, or scenarios.
- No Gradio `Radio`, `Textbox`, `Code`, `File`, `UploadButton`, `Dataframe`, editable `JSON`, input media, chatbot, multimodal component, state, examples, flagging, feedback, analytics, persistence, or request object exists.
- Pinned Gradio reports `config.enable_queue == true` and initializes internal queue/state collections. This is recorded as a framework fact and must not be monkeypatched. The application-owned contract is zero inputs, dependencies, functions, and API endpoints; normal browser traffic has zero POST, event, session, or queue requests; the outer guard makes all related framework routes unreachable; and state snapshots before and after browser/probe traffic show zero public-interaction state delta.

The server composition is load-bearing. `space/app.py` creates an otherwise empty `FastAPI(docs_url=None, redoc_url=None, openapi_url=None)`, calls `gr.mount_gradio_app(parent, demo, path="/", ...)`, then assigns `app = PublicSurfaceGuard(parent, build_package_asset_membership())` and passes that directly to programmatic `uvicorn.run`. `PublicSurfaceGuard` always has exactly two constructor arguments, `downstream` and the nonempty immutable `package_asset_urls` derived from the two pinned Gradio roots; neither argument has an optional default, and tests never substitute an empty set. The guard is not registered through `app_kwargs`, `FastAPI.add_middleware`, or a Starlette middleware list. It is therefore outside the FastAPI server-error layer and the mounted Gradio application, including Gradio's inner Brotli, CORS, router, and body parsing. Framework-global monkeypatching is forbidden.

The exact Gradio `6.26.0` mount arguments are `path="/"`, `server_name="0.0.0.0"`, `server_port=7860`, `footer_links=[]`, `run_history=False`, `root_path=""`, `allowed_paths=["/__carerisk_no_allowed_files__"]`, `blocked_paths=["/"]`, `favicon_path=None`, `show_error=False`, `max_file_size=0`, `ssr_mode=False`, `enable_monitoring=False`, `pwa=False`, and `mcp_server=False`, with no authentication, authentication dependency, custom JavaScript/head path, custom static mount, or environment/CLI input. The sentinel must resolve to an absolute nonexistent path. The sentinel, root block, upload-size setting, and environment scrub are defense in depth only; the outer guard is authoritative.

Uvicorn is called with the application object rather than an import string and with exact programmatic values `host="0.0.0.0"`, `port=7860`, `workers=1`, `http="h11"`, `proxy_headers=False`, `forwarded_allow_ips=""`, `access_log=False`, `server_header=False`, `date_header=False`, `reload=False`, `factory=False`, `env_file=None`, and `log_config=None`. The explicit `http="h11"` is the wire-parser identity: source, configuration, container, cold-start, and final-receipt gates reject `auto`, `httptools`, CLI selection, environment selection, or reliance on the accidental absence of `httptools`. The existing exact runtime/dev lock closure already contains h11 and remains unchanged; this decision adds no dependency. The entry point has no CLI parsing or environment-derived configuration. Docker continues to invoke `python app.py`.

`PublicSurfaceGuard` passes only ASGI `lifespan` scopes to the parent. A WebSocket scope sends exactly `{"type": "websocket.close", "code": 1008, "reason": ""}` without calling downstream or `receive`. Any non-HTTP, non-WebSocket, non-lifespan scope returns without downstream, `receive`, or protocol-invalid output. For HTTP, the guard may inspect only `method`, `path`, `raw_path`, `query_string`, and headers needed for classification. It never logs those values and never reads a request body.

The public HTTP allowlist is intentionally static and read-only:

- `GET` or `HEAD` for exact `/` with an empty query string. This is the only `HEAD` exception because pinned Gradio explicitly registers both methods for the root;
- `GET` only for exact `/config`, `/manifest.json`, and `/favicon.ico`, each with an empty query string;
- `GET` only for exact `/theme.css` with query bytes `v=8ad6f9b14414574fe6c6d9b4362dcdd63dfdc66d8c34cbef0982888dfc44ff04`. This value is the SHA-256 of the default-theme CSS generated by pinned Gradio `6.26.0`, must equal `demo.get_config_file()["theme_hash"]`, and is frozen by a response-content hash test; no other theme query or bare theme path is allowed;
- `GET` only for an exact URL member built at startup from the pinned package roots `gradio.routes.BUILD_PATH_LIB` mapped to `/assets/` and `gradio.routes.STATIC_PATH_LIB` mapped to `/static/`. The immutable `frozenset[str]` includes only non-empty canonical relative paths with suffix in the source-audited set `.css`, `.js`, `.svg`, `.ttf`, `.wasm`, `.woff`, or `.woff2`, whose source is a regular non-symlink file and whose resolved path remains beneath the corresponding resolved, non-symlink root. A syntactically valid but absent filename, directory, case variant, symlink, traversal, or file under any user-controlled, other site-package, evidence, temporary, or application path fails membership and is blocked before Gradio.

Pinned Gradio source defines the only two authorized roots. Startup walks them read-only and performs no network or filesystem write. Verification serializes each member as `url<TAB>byte_size<TAB>sha256<LF>` in code-point-sorted URL order and records the membership count and SHA-256 tree digest. The current Windows pinned-wheel audit observed 916 regular files beneath `BUILD_PATH_LIB` and 50 beneath `STATIC_PATH_LIB`, with zero symlinks; those counts are audit evidence, not guessed cross-wheel constants. The exact locked Linux runtime and reviewer images independently derive the inventory from their installed wheel and must match each other in sorted membership and content tree digest. A missing root, unexpected symlink/special file, containment failure, duplicate URL, or runtime/reviewer mismatch stops verification.

`/manifest.json` is an exact metadata exception required by Gradio's pinned shell. With `Blocks.title == PRODUCT_NAME` and `favicon_path=None`, `GET` must return media type `application/manifest+json` and exactly `{"name": PRODUCT_NAME, "icons": [{"src": "static/img/logo_nosize.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"}], "start_url": "./", "display": "standalone"}` with no canary or client-derived value. `/favicon.ico` returns the locked package file `STATIC_PATH_LIB / "img/logo.svg"`, exactly 1,107 bytes with SHA-256 `3d131bff3fe15bcbb3e6e6552a8bee25377c3666723a9cbe68ceca953ea613df`; the manifest icon resolves to `/static/img/logo_nosize.svg`, exactly 1,082 bytes with SHA-256 `89fd7687072f6c1ab52be3348494f0410c270f453e8306105719b2e3f7091469`. Tests bind both blobs to the locked package roots, require no network/write, and block every `/pwa_icon` variant. `HEAD` for metadata, config, theme, and package assets never reaches the pinned GET-only handlers; the outer guard returns its fixed 404.

All other HTTP methods, paths, or queries return an exact ASGI response start with status 404, fixed `content-type: text/plain; charset=utf-8`, fixed `content-length: 9`, and an ASGI response-body message containing `b"Not Found"`; there is no CORS header, compression, or reflected input. This includes every `POST` and `OPTIONS`, every `HEAD` except exact root, every `/gradio_api`, API, run, call, queue, session, file, upload, proxy, component, streaming, recording, monitoring, authentication, OpenAPI, docs, vibe, event, and non-allowlisted metadata route, and all encoded, traversal, alternate-slash, doubled-slash, or case variants. At the actual Uvicorn/HTTP wire boundary, HTTP semantics suppress the entity bytes for every `HEAD`: a blocked non-root `HEAD` is observed as status 404 with an exact zero-byte entity body while retaining `content-length: 9`. Tests keep the pure-ASGI message assertion and wire/client entity assertion separate; they do not require an inner 405, fabricate a GET body for `HEAD`, or reinterpret the empty wire entity as an empty ASGI body message.

The canonical-path predicate runs before allowlist classification for every HTTP request. `raw_path` must be ASCII and equal `path.encode("ascii")` byte-for-byte. The path contains no percent sign or percent-encoded form, backslash, control/NUL/non-ASCII character, `.` or `..` segment, empty interior segment, doubled slash, case alias, Unicode normalization, or alternate separator. Asset tails are non-empty relative paths whose segments each match `[A-Za-z0-9_][A-Za-z0-9._@+~-]*`; the leading underscore is required by the pinned packaged member `__vite-browser-external-B0RrT0g9.js`, not a prefix wildcard. A terminal suffix or grammar match alone never authorizes a path; exact immutable membership remains mandatory.

Before forwarding an otherwise permitted `GET`/`HEAD`, the guard rejects any `Transfer-Encoding`, malformed or duplicated `Content-Length`, or numeric `Content-Length` other than zero. It requires exactly one header entry whose name bytes are exactly `b"host"` and whose value selects from this closed byte-for-byte authority map; Host values are lowercase ASCII with no trailing dot, userinfo, whitespace, case alias, IPv6 alias, or additional/default port:

| Exact Host bytes | Sanitized scheme | Sanitized server | Sanitized client |
| --- | --- | --- | --- |
| `127.0.0.1:7860` | `http` | `("127.0.0.1", 7860)` | `("127.0.0.1", 0)` |
| `localhost:7860` | `http` | `("localhost", 7860)` | `("127.0.0.1", 0)` |
| `carerisk-app:7860` | `http` | `("carerisk-app", 7860)` | `("127.0.0.1", 0)` |
| `steven0226-carerisk-48h.hf.space` | `https` | `("steven0226-carerisk-48h.hf.space", 443)` | `("127.0.0.1", 0)` |

Host rejection has two explicit layers. In direct pure-ASGI unit probes, an absent, duplicated, malformed, or unlisted Host is delivered as a scope to `PublicSurfaceGuard` and returns the guard's fixed 404 without downstream or `receive`. On the actual Uvicorn+h11 wire, missing or duplicated Host may be rejected by the HTTP parser before any ASGI application call; the pinned contract accepts and requires exact status 400 for those two malformed wire cases. That 400 is parser-layer fail-closed evidence, not evidence that the guard ran: an app-entry/downstream marker must remain unchanged, and response headers/body plus captured bounded logs contain no CORS, compression, canary, or reflected Host/input. Tests do not monkeypatch h11/Uvicorn and do not rewrite the parser's 400 to 404. A syntactically valid single Host always reaches the guard; an unlisted or noncanonical single Host then returns the guard's fixed 404. For an accepted authority, the guard constructs a new downstream ASGI scope with the table's constant scheme/server/client, `root_path=""`, and the sole header `(b"host", <the selected exact Host bytes>)`; it preserves only the already-validated method, path, raw path, query, HTTP version, and ASGI version. Origin, Cookie, Authorization, every `X-*`, Forwarded, User-Agent, and all other attacker-controlled headers are absent downstream. Uvicorn retains `proxy_headers=False` and never reads forwarded identity. Local health uses `localhost:7860` or `127.0.0.1:7860`; the reviewer container reaches the app only through the fixed Docker internal-network alias `carerisk-app:7860`; and the only approved public identity is `steven0226-carerisk-48h.hf.space`. If the authorized Hugging Face candidate or iframe Host differs byte-for-byte, publication stops for central review; no wildcard, suffix match, additional Space alias, or forwarded-header trust is added.

Pure-ASGI probes instantiate `PublicSurfaceGuard(downstream, package_asset_urls)` with the exact nonempty membership derived from the pinned roots, pair every hostile scope with downstream and receive bombs, and require both counts to remain zero. Their fixed blocked-response assertion includes the 9-byte ASGI body message and `content-length: 9`. Response and captured output must exclude raw/decoded paths, query, URL, filename, multipart/body canaries, header/cookie canaries, and their representations. Running probes replace Gradio outbound fetch and temporary-file creation with bombs and snapshot the temp root around URL-file, local-file, zero/nonzero/oversized upload, hostile authority/query/header/cookie, CORS/Brotli, canonical-path, asset-membership, and alternate-scope matrices. Every request that reaches the guard and is blocked must be intercepted before the inner app with no network, temp delta, body receive, downstream call, CORS, compression, traceback, or echo. Separate raw-wire probes cover the pinned Uvicorn+h11 400 path for missing/duplicate Host and prove that ASGI app-entry/downstream markers do not move. Permitted root/config/theme/metadata/exact package members remain healthy and receive only the selected sanitized scope. Hostile-header probes for each accepted authority prove responses contain no canary, CORS reflection, or content encoding. Wire-level `HEAD` probes require zero entity bytes while retaining the fixed content length; pure-ASGI tests continue to require the deterministic body message.

An exact Gradio `6.26.0` route inventory recursively expands both the parent mount and the mounted application's FastAPI `_IncludedRouter.original_router`. Every route/method must be explicitly classified as required read-only surface or outer-boundary-blocked; new, missing, or unclassified routes fail. Browser review records exact method/path/query tuples and requires all app traffic to follow the exact method table (`GET`, with `HEAD` permitted only for root), including the exact manifest, favicon, and static logo requests, with zero guard blocks, POSTs, event/session/queue requests, external requests, and console errors. It verifies keyboard radio switching, before/after panel visibility, and zero public-interaction state delta while recording the pinned `enable_queue == true` framework fact. If the mounted signature, outer ordering, route inventory, browser request graph, authority map, asset membership, sanitized scope, or later Hugging Face Docker behavior differs, implementation stops for exact source audit, a RED test, and central written approval; no wildcard is added.

## 14. Space card and licensing

The public `README.md` begins with Hugging Face YAML metadata declaring:

- Title `CareRisk 48H — Evidence & Abstention Explorer`.
- `sdk: docker`.
- `app_port: 7860`.
- `license: apache-2.0` for the application source.
- A short description that uses `research`, `synthetic-only`, `calibration`, `abstention`, and `reproducibility`, and does not say clinical prediction, medical device, decision support, deployment-ready, or validated for care.

Immediately after metadata, the rendered card repeats the exact claim ceiling before screenshots, links, instructions, or interactive claims.

License boundary copy must state:

- Space application code is Apache-2.0.
- PhysioNet Challenge 2012 data is not included and is not relicensed by Apache-2.0.
- No raw data, row-level derived data, outcomes, predictions, or data-derived model/guard artifacts are included.
- The aggregate receipt remains evidence from the source research release and is accompanied by `NOTICE`, PhysioNet attribution, and the ODC-By 1.0 source-license link.
- Synthetic gate states are original abstract application constants, not sampled, transformed, or reconstructed patient records and not validation evidence.

The card links to the exact GitHub `v0.2.0` tag, source repository, release manifest, aggregate receipt, Apache LICENSE, NOTICE, and citations. It does not embed the excluded final-evaluation image.

## 15. Verification strategy

### 15.1 Static and unit gates

- Exact-copy tests for both claim paragraphs in app config and Space card.
- DOM-order test proving the claim section precedes the first app-owned focusable element.
- Receipt byte SHA, Git blob SHA, strict JSON/schema, metric/CI, privacy, and release-relationship tests, including one mutation test per failure reason.
- Formatter tests proving every rendered quantitative value comes from parsed receipt fields.
- Scenario registry tests proving exactly four IDs, immutable fields, no numeric or patient-like fields, no score/probability/threshold strings, and fail-closed unknown input.
- Source AST/import boundary and no-write/no-network client tests.
- Gradio static-config, outer-ASGI, route-inventory, and API-absence capability tests from Section 13.
- Exact clean-export path, size, hash, symlink, denylist, secret-pattern, private-key, large-file, and binary-signature tests.
- Space card metadata, license boundary, citation, NOTICE, SBOM, and one-license-record-per-lock-package tests.
- `ruff`, strict type checking for Space modules, `pip check`, and full Space-specific pytest.

Tests must not import the existing dashboard, model package, data parser, guard, synthetic cohort generator, or final evaluation code. They use only committed public evidence bytes and abstract synthetic states.

### 15.2 Container gates

- Build from the digest-pinned base using the exact runtime lock and no credentials.
- Verify the final user is non-root with a non-login `/usr/sbin/nologin` passwd entry, the workspace is not writable, product source never spawns or invokes a shell, and exec-form startup inventories and executes the required `/usr/bin/env` binary. Debian `/bin/sh` may exist and is not removed or tested for absence.
- Start the candidate with adversarial `GRADIO_*`, `HF_HUB_DISABLE_TELEMETRY`, `SPACE_ID`, `PORT`, and secret-shaped Docker environment values; the fixed poison matrix includes `GRADIO_DEBUG`, `GRADIO_SERVER_NAME`, `GRADIO_SERVER_PORT`, `GRADIO_NUM_WORKERS`, `GRADIO_NODE_PATH`, `GRADIO_LOCAL_DEV_MODE`, and `GRADIO_NODE_SERVER_PORT` in addition to analytics, watch, vibe, hot-reload, run-history, SSR, MCP, allowed/blocked paths, root path, share, and monitoring variables. An exact Gradio `6.26.0` source-derived environment-read inventory must be covered as well. Prove that pre-import state, post-Blocks state, PID 1, and every child contain the same exact reviewed allowlist with `HF_HUB_DISABLE_TELEMETRY=True`, that hostile `0`/canary values are absent, that the app still binds fixed port 7860, and that no runtime behavior or capability is overridden.
- Run under read-only root, bounded tmpfs, two CPUs, no GPU, and `--network none`.
- Perform server-free app construction and a same-container loopback HTTP health/claim/config/theme/metadata/exact-package-asset probe. Verify the parent/mount/outer-wrapper order, exact two-argument guard construction with nonempty pinned-root membership, zero app-owned inputs/dependencies/functions/API, pinned `enable_queue == true`, zero public-interaction state delta, the absent allowed-path sentinel, and unavailable monitoring/run-history. Compare independently derived runtime/reviewer package membership and content-tree digests; verify manifest/favicon/logo bytes and the exact GET/root-HEAD table. Then exercise all four authorities plus the hostile authority/outer blocked matrix with downstream/body-receive, outbound-fetch, and temporary-file bombs. Direct pure-ASGI blocked scopes must produce the deterministic fixed 404 messages, including 9 body bytes and `content-length: 9`, outside FastAPI/Gradio. Separate actual programmatic Uvicorn with explicit `http="h11"` wire tests require exact 400 and zero app-entry/downstream marker delta for missing/duplicate Host, require valid unlisted single Host to reach the guard and receive 404, and require every blocked wire `HEAD` to contain zero entity bytes while retaining `content-length: 9`. Source and runtime identity records reject parser auto-selection, `httptools`, CLI selection, and environment-derived selection. All layers require no CORS, compression, network, temp-file delta, canary, or reflection. Root blocking and `max_file_size=0` are checked only as defense in depth.
- Verify the normal state only from the exact inspected final runtime image. Verify the four runtime-reachable evidence failures (`receipt_missing`, `receipt_hash_mismatch`, `release_relationship_invalid`, and `deployment_manifest_invalid`) only from local images derived from that exact final-image digest under the `NEVER_DEPLOY` contract below; do not alter committed files or add a product configuration surface. `receipt_schema_invalid` remains in the five-code fail-closed taxonomy but is not live-reachable because the immutable receipt SHA-256/Git-blob gate owns precedence in the candidate runtime.
- Generate and compare image SBOM to the committed dependency SBOM; inventory differences fail.
- Scan vulnerabilities and licenses under the contract in Section 10.

Four failure-review images are local verification instruments, never release candidates. After the exact final image is built and its digest is inspected, the verifier creates a task-owned GUID directory beneath the validated OS temporary root and writes one literal Dockerfile per runtime-reachable failure code. Each Dockerfile uses `FROM <exact-local-final-image-digest>`, is built with `--pull=false --network=none`, switches to `USER 0` only for the single package-relative evidence mutation needed by that state, and restores `USER 10001:10001`. The four mutually exclusive mutations are: remove only the receipt for `receipt_missing`; alter only receipt bytes for `receipt_hash_mismatch`; alter only release-relationship content for `release_relationship_invalid`; and alter only deployment-manifest content for `deployment_manifest_invalid`. Each mutation must produce exactly its expected bounded code and no other code.

The fifth taxonomy member, `receipt_schema_invalid`, is a unit/component downstream contract rather than a live image state. Canonical runtime receipt bytes are accepted only after their exact immutable SHA-256 and Git-blob identities pass; any changed receipt bytes are therefore dominated by `receipt_hash_mismatch` before strict schema parsing. Unit tests may use only the existing explicit controlled dependency-injection/anchor seam to isolate strict JSON/schema gates, and must prove the resulting exact failure message plus zero controls, metrics, scenarios, API capability, app-owned event/API request, or echo. The permitted ASGI root GET still reaches the mounted static document and is not miscounted as an event request. Tests must not patch a running/final image, change product anchors, claim runtime evidence, fabricate a hash collision, or mark this code live-reviewed. The final receipt records all five codes in a reachability/precedence matrix with owning gate, `live_reachable`, and evidence type; `receipt_schema_invalid` is exactly `live_reachable=false`, `evidence_type=unit_component_asgi`, and `precedence=dominated_by_immutable_receipt_anchor`.

Each derived image uses the controller-generated exact local reference `carerisk-local:<GUID>-NEVER_DEPLOY-<failure-code>` and the complete task-ownership label set: exact run GUID, `resource_role=failure_variant`, exact base digest, exact expected failure code, and `NEVER_DEPLOY=true`. Immediately after a successful build and inspection, the controller retains one immutable expected `FailureVariantRecord` per code containing that exact local reference, the inspected image ID/content digest, final base digest, code, GUID, and labels. A record is created only after build and single-delta inspection pass; it is never reconstructed later from labels or names. Each failure container uses the exact name `carerisk-<GUID>-NEVER_DEPLOY-<failure-code>`, so both image reference and container name contain literal `NEVER_DEPLOY`, and uses the same role and complete failure-variant labels. Normal, reviewer, and network names must not contain `NEVER_DEPLOY`. Other task-owned Docker resources use disjoint complete ownership schemas rather than pretending to be failures: the normal container has exact run GUID, `resource_role=normal`, and exact final-image digest; the reviewer container has exact run GUID, `resource_role=reviewer`, and exact reviewer-image digest; and the shared internal network has exact run GUID plus `resource_role=network`. Only this reserved task-ownership label namespace is used for cleanup selection; an omitted, duplicate, unexpected, or contradictory ownership label fails closed even if the resource name appears correct. The verifier rejects any remote registry reference, upload, tag, push, save/export input, bind mount, product environment switch, runtime path override, framework monkeypatch, or deployable injection. Image inspection proves the intended single evidence delta and byte identity for entrypoint, command, application source, dependency locks, package assets, and every other final-image path. Normal review always uses the exact final image; failure review always uses these final-image-derived local variants with the same entrypoint, command, runtime flags, and internal no-egress network.

Cleanup treats labels as necessary but insufficient. It first dispatches by Docker resource type and, for a failure image or container, looks up the controller-retained expected record by exact GUID and code. Immediately before deletion it freshly inspects the actual image and container. The actual image's local reference, image ID, and content digest must each equal the expected record; the actual container `.Image` ID and configured image reference must identify that same record. These identity checks are required in addition to the complete labels, final base digest, code, GUID, literal `NEVER_DEPLOY` name schema, and resource reference. A swapped variant image, a correct-looking label set attached to the wrong image digest/reference, or a container configured from a different variant fails closed and is preserved. Cleanup removes only the one exact current task-owned resource after all comparisons pass; missing records or labels, extra or contradictory labels, ambiguous references, digest/reference/identity mismatch, or type/name mismatch preserve the resource for manual inspection, and one role's schema is never broadened to another.

### 15.3 Browser and accessibility gates

Every one of the five live-reachable page states is actually reviewed at both `1440×900` and `390×844`: the exact final image supplies the validated-normal state, and the four exact `NEVER_DEPLOY` derived images supply the four runtime-reachable failure states. Shared assertions are limited to conditions that apply to both page shapes:

- The exact claim/truth ceiling and state or failure headline have the required DOM order and are visible; no horizontal overflow; body text is at least 16 px; responsive layout, font loading, logical headings, non-color-only status, and WCAG 2.2 AA automated/manual checks pass.
- Browser console has zero errors and no runtime external requests. The exact app method/path/query graph follows the GET/root-HEAD table, including manifest, favicon, and manifest-logo requests; outer-guard blocks, POSTs, event/session/queue requests, and public-interaction state delta are zero. Package membership and sanitized-scope records match, and cold-start observations contain no download, model initialization, or partial evidence.

Normal-only assertions require exactly four radios, four controls, and four scenario panels; the exact claim ceiling precedes the first control; each control is at least 44×44 CSS pixels with exact label association, visible focus, and keyboard-only selection; and every expected checked/panel before-after transition is observed. All four scenarios render only the allowed state/reason pair and the receipt-backed normal claims/metrics, with no score, probability, risk, recommendation, threshold comparison, patient-like values, or stale prior state.

Failure-only assertions require zero radios, zero controls, zero scenario panels, zero transitions, zero metrics, and zero canonical quantitative values. Keyboard scenario selection is recorded as false or explicitly not applicable, never as a passing normal interaction. The exact expected bounded failure code and message are visible, and there is no partial metric, download, model initialization, or control/event capability.

A newly required path, query, method, authority, forwarded header, or review mechanism is a stop-and-review condition, not permission to broaden a wildcard or add a product failure-state switch.

### 15.4 Cold-start review

- Record three fresh local container starts under the two-CPU, no-network contract and three fresh public Space cold starts after later deployment authorization.
- Record time to first HTTP 200 and time until the exact claim ceiling is visible.
- Thirty seconds is the local engineering soft target, not a public SLA. Missing the soft target requires an optimization or an explicit documented observation; timing must never be fabricated.
- A hard gate is that every start resolves to either the validated normal page or the bounded evidence-failure page without partial metrics, crash loop, download, or model initialization.

## 16. Existing app reuse boundary

Permitted conceptual reuse:

- Navy/teal daylight palette, typography scale, visible focus treatment, responsive stacking, and compact evidence-row concepts.
- Exact safety-first ordering discipline, HTML escaping discipline, stale-state clearing test concept, non-root container concept, and desktop/mobile review method.
- Gradio `Blocks` as the presentation framework.

Forbidden reuse:

- Copying, importing, packaging, or executing existing `app/dashboard.py`, existing root `app.py`, `carerisk48h.demo`, `carerisk48h.synthetic`, `carerisk48h.inference`, `carerisk48h.guard`, `carerisk48h.schema`, feature builders, models, calibrators, or scoring helpers.
- Existing editable JSON, machine-output JSON, trend chart, contributor table, patient-shaped synthetic payload, synthetic trained bundle, joblib serialization, probability display, threshold marker, or “人工複核” workflow.
- Existing Dockerfile or broad `pyproject.toml` dependency extras as the Space runtime definition.

Implementation must create a standalone Space-specific surface. Similar CSS values or test ideas do not make the existing scoring app part of the public bundle.

## 17. Authenticated and remote gates outside implementation

These gates are sequential and remain outside the design/spec commit and outside the later product-code implementation unless separately authorized:

1. With the namespace owner authenticated, verify `steven0226/carerisk-48h` has no public, private, deleted, reserved, or organization-policy collision. Any ambiguity stops before creation.
2. Obtain explicit authorization to create the public Space repository.
3. Verify the clean export and deployment manifest locally from approved source commits.
4. Obtain explicit authorization to upload the exact clean export.
5. Compare the public destination tree and bytes to the deployment manifest; verify destination commit and record it in the separate post-deployment audit record.
6. Before live review, prove that the actual Space application/iframe Host is byte-for-byte `steven0226-carerisk-48h.hf.space`. Any different canonical, alias, preview, organization-policy, or iframe identity stops publication for central review; do not add a wildcard. Then execute live cold-start, browser, accessibility, source-tree, license, log, secret/variable, exact-authority sanitization, and no-external-request reviews.
7. Obtain explicit authorization before setting GitHub About Website to the Space URL. About description, topics, visibility, Pages, pinning, releases, and other GitHub metadata are not implicitly authorized.

No collision check authorizes creation. No creation authorizes upload. No successful upload authorizes an About change.

## 18. Acceptance criteria for implementation review

Implementation is eligible for deployment review only when all statements below have fresh evidence:

- The public candidate contains exactly the allowlisted files and no denylisted path/content.
- Exact claim copy and DOM order pass at code, config, and live-browser levels.
- Only four abstract in-memory scenarios are selectable; arbitrary values fail closed without echo.
- Scenario output is limited to `evidence available`/`evidence withheld`, gate booleans, and one enumerated reason; no score or case decision exists anywhere in source, config, response, card, or screenshot.
- Every displayed quantitative value is derived from the validated exact receipt.
- Receipt, release, tag, app-source commit, export paths, hashes, locks, base digest, SBOM, and licenses are mutually consistent.
- App source has no model/data/scoring imports, no product filesystem writes, no environment configuration, and no outbound network capability.
- Container passes non-root, read-only, bounded tmpfs, CPU-only, network-disabled smoke; its `/usr/bin/env -i` entrypoint removes injected environment values before import and preserves only the reviewed allowlist.
- Gradio config proves zero app-owned inputs, dependencies, functions, and API endpoints; the pre-rendered HTML/CSS explorer proves scenario switching requires no server request. Pinned `config.enable_queue == true` and framework internal queue/state initialization are recorded without monkeypatching. The truly outer two-argument `PublicSurfaceGuard`, exact authority map, immutable nonempty package-asset membership, exhaustive parent/inner route inventory, sanitized permitted scopes, direct-ASGI fixed-message probes, pinned Uvicorn+h11 parser-layer 400 evidence, wire-level HEAD entity suppression, downstream/receive/fetch/temp bombs, zero public traffic/state delta, and container/browser records prove that data-entry, upload/file, queue/event/session routes, network, write, CORS, and compression are not publicly reachable.
- The exact final image passes the normal state at both viewports, and all four final-image-derived local-only `NEVER_DEPLOY` variants each pass their exact runtime-reachable failure state at both viewports. Shared, normal-only, and failure-only assertions remain separate and the variant inspection proves only the intended evidence delta. The fifth code, `receipt_schema_invalid`, has unit/component/ASGI evidence only and is explicitly recorded as not live-reachable and not live-reviewed.
- Space creation, upload, and GitHub About remain unperformed until their explicit gates are approved.

## 19. Design review handoff

This specification is the governing design for the already authorized local implementation plan. Task 5 remains held while the docs-only executable correction based on exact parent `7b116846c9ed9fcfc1ed0ab4f62ad803f7322050`—binding failure cleanup to controller-retained image records, requiring literal `NEVER_DEPLOY` failure-container names, and correcting the non-login/no-shell-invocation wording—receives a fresh authority review. If and only if that review reports Critical=0, Important=0, and Minor=0, the next permitted action is to resume Task 5 from new RED tests against this exact design; if it reports any finding or load-bearing mismatch, work stops for another central ruling. Export generation, container candidate work, authenticated collision checking, Space creation/upload, and GitHub About work remain behind their later plan and written gates.
