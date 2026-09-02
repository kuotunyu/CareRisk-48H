# CareRisk 48H Hugging Face Space Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a public-safe, synthetic-only Gradio Docker Space that explains receipt-backed evidence and four fixed abstention gate states without accepting patient data or producing case-level scores or decisions.

**Architecture:** Keep the new application isolated under `space/` as a small `carerisk_space` package. Pure standard-library contracts parse three committed JSON artifacts and fail closed before Gradio is constructed; Gradio presents one pre-rendered static HTML/CSS explorer with native radios and zero app-owned inputs, dependencies, functions, or API endpoints. An empty FastAPI parent mounts Gradio, a direct pure-ASGI wrapper forms the truly outer public-surface firewall with a closed authority map and exact locked-package asset membership, and fixed programmatic Uvicorn with explicit `http="h11"` serves it. A source-only exporter reads exact Git blobs into a fresh directory, with application files from an app-source commit, evidence and legal files from the annotated `v0.2.0` tag commit, and `deployment-manifest.json` from the immediately following manifest commit.

**Tech Stack:** CPython 3.11 slim-bookworm runtime image pinned by patch tag and OCI digest; an official Playwright Python test/reviewer image pinned by matching Playwright patch tag plus OCI index/linux-amd64 digests; Gradio `6.26.0`; standard-library `json`, `hashlib`, `html`, `dataclasses`, `pathlib`, and `typing`; pytest, Ruff, Mypy, Playwright, accessibility tooling, pip hash locks, SPDX 2.3 JSON, and Docker CPU-only smoke tests.

**Governing design:** `docs/superpowers/specs/2026-08-31-carerisk-48h-hf-space-design.md`. The original design approval was commit `10a85171afeb9fafb531b3bca1128cddc987619e`; central implementation authorization is anchored at corrective plan commit `b3803f6229d0de51f0a006978e26775012edcc3b`. Task 5 is complete and frozen at `3ef09639c4b08f1fc70e931507af79f4ff717fcb`; Task 6 is complete at controller-accepted Architecture C commit `29d93f3fca8a9706a6ee762ac67e0b0fa427b91f`. Central has approved the dated Task 7 reviewer-only WebKit policy correction; Task 7 must follow `docs/superpowers/plans/2026-09-02-carerisk-48h-task7-webkit-reviewer-policy-corrective.md`, and Tasks 8–13 remain blocked until its GREEN/review gates pass. No provisional self-SHA is fabricated in this document.

## Global Constraints

- Preserve this exact primary copy before the first app-owned interactive control: `僅供研究與教育；不是臨床診斷、治療、分流、資源配置或照護決策工具。本 Space 僅使用內建 synthetic gate-state scenarios，不接受、儲存或處理任何使用者提供的病人資料；不輸出 live probability、risk class、case recommendation 或 threshold-based case decision。`
- Preserve this exact English subtitle immediately after it: `Research and education only. Non-clinical and synthetic-only. No patient data entry or upload, no live predictions, and no care decisions.`
- The only user interaction is a native browser radio selection among four fixed pre-rendered scenario panels. It is resolved by HTML/CSS only and sends no request. There is no upload, editable JSON, free text, code, dataframe editor, arbitrary file/path/URL, live probability, score, risk class, recommendation, or threshold-based case decision.
- Scenario output is limited to `evidence available` or `evidence withheld`, fixed gate booleans, and one enumerated reason. Synthetic states are explanatory application constants, not clinical validation.
- Quantitative UI values come only from the exact committed `v0.2.0` aggregate receipt after byte, Git-blob, schema, release, and deployment-manifest validation. Any validation failure disables metrics and scenario controls.
- Receipt SHA-256 is `d32d833af25e4ebb2f5bd06b64343eb36d7cd180c8e9777f539f6401b78064b3`; receipt Git blob is `b13ec7655bbdb8db1079c3b4793a0bf5590ef69c` (3,363 bytes); formal metrics SHA-256 is `808525afad2ec550e8059c4ba37c2f5aaf8af748873a5a590dff7f1aeaaf47af`. The canonical byte domain is exactly the unmodified LF bytes emitted by `git cat-file blob b13ec7655bbdb8db1079c3b4793a0bf5590ef69c`; no line-ending normalization is allowed. The rejected noncanonical CRLF working-tree diagnostic SHA-256 `f1eb4958f253bf016bc73c405f498055b36cb8b7100654d8868a088f31d426fc` cannot be exported or used for validation.
- Evidence tag is annotated object `2f1ddb0e2276fa894e124b856de488e31e21e88c`, resolving to commit `f4c820cce953f401c1ec525bd8df3a3c1678bbf3`.
- Do not read, modify, copy, or stage `.env`, private data, private research artifacts, model bundles, checkpoints, Set B custody/evaluation working assets, private scientific ledgers/final locks, unapproved private evaluation outputs, or Set C. This prohibition does not cover the approved public `v0.2.0` receipt/release Git objects or the dependency lockfiles created and verified by this plan. Never run the receipt exporter or final evaluation.
- Do not import, copy, package, or execute existing `app/dashboard.py`, root `app.py`, `src/carerisk48h`, joblib, scoring, guard, inference, schema, model, calibrator, or synthetic-patient paths in the public application.
- Product code does not import `os`, reads no environment variable, and performs no network request, process spawn, shell call, filesystem write, persistence, analytics, telemetry, or dynamic import. Gradio exact-version instance/mount values and Uvicorn values are explicit programmatic configuration, never framework-global monkeypatches.
- Gradio is fixed exactly at `6.26.0`. The normal and all five taxonomy failure Blocks are unit/component constructible with zero app-owned input components, dependencies, functions, or API endpoints and empty in-process API metadata. Four scenarios are pre-rendered through `render_scenario`; normal browser interaction sends zero POST, callback, queue, event, or session traffic. Pinned `config.enable_queue == true` and Gradio's internal queue/state initialization are recorded facts, not failures and not monkeypatch targets; queue/event/session routes remain outer-blocked and public-interaction state delta must stay zero. Live final-image review covers normal plus only the four runtime-reachable failures; `receipt_schema_invalid` is dominated by the immutable receipt identity gate and has unit/component/ASGI evidence only.
- `create_app` fixes `dev_mode=False`, `vibe_mode=False`, `root_path=""`, `api_open=False`, and `space_id=None`. `gr.mount_gradio_app` receives only the supported fixed mount arguments listed in Task 5. `uvicorn.run` receives the wrapped application object plus fixed host/port/single-worker/no-proxy/no-access-log arguments and explicit `http="h11"`; source, container, cold-start, and receipt tests reject `auto`, `httptools`, CLI/environment selection, or accidental dependency absence as parser evidence. No Gradio `launch` path exists, and the existing h11 runtime/dev lock closure remains unchanged.
- `space/carerisk_space/ui.py` owns pure-ASGI `PublicSurfaceGuard` and the immutable locked-package asset membership builder. `space/app.py` creates an empty FastAPI parent without docs/OpenAPI, mounts Gradio, and directly wraps the resulting parent as `app = PublicSurfaceGuard(parent, build_package_asset_membership())` before Uvicorn. The guard is outside parent error handling and mounted Gradio Brotli/CORS/router/body parsing. It is not placed in `app_kwargs` or a framework middleware list.
- The guard accepts exactly four Host authorities: `127.0.0.1:7860` and `localhost:7860` over HTTP, the reviewer-only Docker alias `carerisk-app:7860` over HTTP, and `steven0226-carerisk-48h.hf.space` over HTTPS. It rebuilds a constant downstream scope/header tuple for the selected authority. In direct pure-ASGI scopes it rejects missing, duplicate, invalid, combined, whitespace-padded, case-variant, trailing-dot, userinfo, extra-port, or unlisted Host with the fixed 404 and no downstream/receive. On the pinned Uvicorn+h11 wire, missing/duplicate Host is instead rejected before the ASGI app with exact 400; this is parser-layer fail-closed evidence and must leave the app-entry/downstream marker unchanged. A valid unlisted single Host reaches the guard and receives 404. Uvicorn never trusts forwarded headers. A different real Hugging Face Host is a publication stop, not permission to broaden the map.
- At startup, `ui.py` reads only the source-audited locked-wheel constants `gradio.routes.BUILD_PATH_LIB` and `STATIC_PATH_LIB`, derives an immutable URL set from canonical regular non-symlink root-contained package files, and authorizes `/assets` and `/static` only by exact membership. Linux runtime and reviewer images independently record and compare sorted membership/content-tree digests. No unknown-valid filename or user/site/evidence/temp path reaches Gradio.
- Because Gradio `6.26.0` consults environment variables for falsy path lists, the mount retains truthy exact sentinels `allowed_paths=["/__carerisk_no_allowed_files__"]` and `blocked_paths=["/"]`; the allowed sentinel is an absolute nonexistent path. These and `max_file_size=0` are defense in depth only. The truly outer firewall, sanitized permitted scopes, and no-downstream/no-receive probes establish the public boundary.
- The final Docker exec-form `ENTRYPOINT` uses `/usr/bin/env -i` before Python import and rebuilds only the reviewed fixed environment allowlist, including the exact canonical `HF_HUB_DISABLE_TELEMETRY=True`. Its exec-form `CMD` remains `["python", "app.py"]`; neither `SPACE_ID`, `PORT`, secrets, nor arbitrary injected variables survive. Candidate verification poisons Docker `GRADIO_*`, `HF_HUB_DISABLE_TELEMETRY`, `SPACE_ID`, and `PORT` values and proves the pre-import, post-Blocks, PID 1, child, and runtime values cannot drift.
- Runtime is CPU-only, non-root, and read-only except framework-owned operations in bounded ephemeral `/tmp`. No persistent service is started during ordinary unit tests.
- The runtime account is non-login with `/usr/sbin/nologin`; the app uses exec-form startup and never spawns or invokes a shell; unnecessary shell utilities may be excluded. Debian slim may contain `/bin/sh`, and neither its removal nor physical absence is an acceptance requirement.
- `requirements.lock` contains the complete runtime closure. `requirements-dev.lock` contains the complete runtime-plus-development union closure; every normalized runtime package/version pair is present unchanged in the development lock. Both locks contain exact versions and accepted target-distribution hashes. Docker installation uses `python -m pip install --require-hashes --no-deps` against the appropriate complete closure.
- The final runtime base uses a real CPython 3.11 slim-bookworm patch tag plus real OCI index/linux-amd64 digests. The test/reviewer base uses the official Playwright Python image whose patch version exactly matches the locked Playwright Python package, with real tag, index digest, linux/amd64 digest, embedded browser revisions, OS/system-package inventory digest, license, and notices recorded. Mutable-only image references are rejected.
- All bytes that enter the public export, candidate, runtime stage, final runtime image, deployment artifact, saved archive, pushed image, uploaded artifact, published image, emitted build output, or any other distributed output remain universally approved-only. Unknown, missing, incompatible, or non-redistributable licensing for any such byte is a hard export stop.
- The sole exception is metadata inventory for the exact local/CI reviewer-only WebKit tuple: reviewer tag `mcr.microsoft.com/playwright/python:v1.62.0-noble`, index `sha256:aa81288e738725378becba5b3e06cb0f3a7f012a610e87e8d767a090ea3f740d`, linux/amd64 manifest `sha256:51d31fdfacb0cff99a1a724152e34ae408d2bd4e7da310ff157450f49261cc59`, Playwright `1.62.0`/tag `v1.62.0`, WebKit revision `2336`, version `26.5`, and tree SHA-256 `c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c`; plus the external source reference tag commit `e3950d9c140d007bd52853b45813c6274b24e36f`, relative path `browser_patches/webkit/UPSTREAM_CONFIG.sh`, commit-pinned raw URL, raw length/hash, and parsed `REMOTE_URL`/`BASE_BRANCH`/`BASE_REVISION` fixed in the Task 7 corrective plan. Its SPDX declared/concluded licenses are both exactly `NOASSERTION`, `review_disposition` is exactly `reviewer_test_only_not_redistributed`, and `complete_digest_bound_notice=false`. The source reference proves only the Playwright source configuration declaration, not a binary-image member or source/binary attestation; no source raw bytes are public, runtime, or export bytes. Chromium, Firefox, ffmpeg, OS/base-image inventories, and Python components remain approved-only.
- The exact reviewer image may be pulled and run locally or in CI only. It and all embedded browser/support bytes are never saved, exported, emitted as build output, pushed, uploaded, published, deployed, copied into a public candidate, or inherited by/present in the final runtime. The closed distribution-surface set is `public_export`, `candidate`, `runtime_stage`, `final_image`, `deployment_artifact`, `saved_archive`, `pushed_image`, `uploaded_artifact`, `published_image`, `build_output`, and `other_distributed_output`; every member is mandatory and mutation-tested, and an omitted/duplicate/unknown/empty/unclassified surface fails closed. Tuple, official Playwright tag/tag URL/`browsers.json`/registry/CDN, or the external commit-pinned source-reference tag commit/relative path/raw URL/length/hash/parsed assignments, WebKit tree algorithm/identity, official WebKit licensing-reference, `NOASSERTION`, disposition, notice-completeness, or exclusion drift fails closed. The immutable image tree must prove the source relative filename absent; source metadata never becomes a binary-image/distributed byte. Remote metadata remains forbidden unless separately authorized.
- Registry/package/browser acquisition and Docker build are controlled supply-chain phases: egress is allowed only to retrieve already selected tag/digest/hash-pinned inputs, and all resolved bytes are verified and inventoried. Hash locks and `--pull=false` do not make a networked build offline. Evidence export, test execution, runtime/cold-start execution, and browser review are separate no-egress phases.
- Never use broad staging (`git add .`, `git add -A`, directory staging, or wildcard staging). Every commit command below names every file explicitly.
- Export requires a clean source worktree and a nonexistent or empty destination. Never export by copying the working tree, and never commit an export directory.
- Hugging Face collision checking, Space creation, upload, visibility, Secrets/Variables, and live review are outside implementation. GitHub About, Pages, topics, pinning, visibility, releases, and metadata changes are also outside implementation.

## Planning Baseline Recorded on 2026-08-31

- Fresh `git fetch origin main --tags --prune` left `origin/main` at `11184984ddd553aa3b45a3d5fc0ea4a866877722`; the approved design commit is one commit ahead with the same merge-base.
- `v0.2.0` still resolves through annotated tag object `2f1ddb0e2276fa894e124b856de488e31e21e88c` to `f4c820cce953f401c1ec525bd8df3a3c1678bbf3`; the receipt blob remains `b13ec7655bbdb8db1079c3b4793a0bf5590ef69c`.
- The first local baseline command inherited a broken user-site Torch and stopped during collection with `WinError 1114`. This is environment contamination, not a test result.
- Repeating with `PYTHONNOUSERSITE=1` collected the existing suite and produced one failure: `tests/test_dashboard.py::test_create_app_uses_zh_tw_progressive_disclosure`, because the current global Python does not have the optional Gradio package. Running the same marker selection while deselecting that one dependency-bound test passed the other 154 tests.
- Ruff and Mypy executables are absent from the current global Python. `pip check` reports unrelated global Anaconda conflicts. Implementation must therefore use isolated, lock-installed verification environments and must not repair or rely on the global environment.
- Baseline commands used `PYTHONDONTWRITEBYTECODE=1`, disabled pytest cache, used two CPU threads, and left the worktree clean.

## Completed Task 5 Authority and Pinned-Source Evidence

- Central authorized local implementation at plan commit `b3803f6229d0de51f0a006978e26775012edcc3b`. Task 5 completed at `3ef09639c4b08f1fc70e931507af79f4ff717fcb`; its product/test bytes remain frozen while Task 6 is corrected through Architecture C.
- Pinned `.venv-space` reports Gradio `6.26.0`. `inspect.signature(gr.mount_gradio_app)` contains every fixed Task 5 mount argument, including `favicon_path`; `inspect.signature(uvicorn.run)` contains the fixed programmatic options, including `http`; no `launch` or CLI path is required. The server call fixes `http="h11"` independently of whether `httptools` happens to be installed.
- Direct composition `app = PublicSurfaceGuard(parent, build_package_asset_membership())` after `gr.mount_gradio_app(...)` was probed with hostile headers: permitted root/config requests remained healthy after scope sanitization, while `OPTIONS` and upload paths returned the fixed 404 outside Gradio with no canary, CORS, or compression. Every implementation and test construction uses this exact two-argument interface with the nonempty membership derived from the two pinned roots; there is no optional default or empty-set substitute.
- Pinned source registers both `GET` and `HEAD` for root, but GET-only handlers for config, theme, manifest, favicon, and package routes. The governing outer method table therefore allows root GET/HEAD, allows only GET for the other exact read-only resources, and returns its own fixed 404 for all other methods before Gradio.
- `gr.HTML` defaults `js_on_load` to a click-trigger script; explicit `js_on_load=None` removes that config key without creating dependencies. The pinned static config retains `enable_queue == true`, `dependencies == []`, `len(app.fns) == 0`, and empty API metadata. These are recorded as separate framework and app-owned facts.
- Pinned `gradio.routes.BUILD_PATH_LIB` and `STATIC_PATH_LIB` are the only authorized package roots. The local wheel audit found 916 and 50 regular files respectively and zero symlinks; counts are evidence only. One packaged member, `__vite-browser-external-B0RrT0g9.js`, requires the explicitly audited leading-underscore segment form; exact membership remains authoritative. Locked `STATIC_PATH_LIB/img/logo.svg` is 1,107 bytes/SHA-256 `3d131bff3fe15bcbb3e6e6552a8bee25377c3666723a9cbe68ceca953ea613df`, and `img/logo_nosize.svg` is 1,082 bytes/SHA-256 `89fd7687072f6c1ab52be3348494f0410c270f453e8306105719b2e3f7091469`.
- Pinned `Blocks(analytics_enabled=False)` writes `HF_HUB_DISABLE_TELEMETRY=True`. The entrypoint uses that exact value so pre-import, post-Blocks, PID 1, and child environments have one canonical representation.

## File and Interface Map

### Public Space source stored under `space/`

| File | Responsibility |
| --- | --- |
| `space/README.md` | Hugging Face card metadata, exact claim ceiling, evidence/license boundary, source links |
| `space/Dockerfile` | Digest-pinned official Playwright test/reviewer stage plus non-root CPython final CPU runtime |
| `space/requirements.lock` | Complete hash-locked runtime dependency closure |
| `space/requirements-dev.lock` | Complete hash-locked runtime-plus-development union closure for the reviewer target |
| `space/app.py` | Empty FastAPI parent, fixed Gradio mount, direct outer guard, and fixed programmatic Uvicorn entry point |
| `space/carerisk_space/__init__.py` | Package identity and version-free public surface |
| `space/carerisk_space/contracts.py` | Exact copy, hashes, schemas, immutable view models, bounded reason codes |
| `space/carerisk_space/evidence.py` | Strict JSON parsing, hash/schema/release/deployment validation, formatting |
| `space/carerisk_space/scenarios.py` | Four immutable abstract scenarios and exact-ID pure lookup/rendering |
| `space/carerisk_space/ui.py` | Safe/failure static Gradio `Blocks`, DOM ordering, and outer ASGI guard |
| `space/SBOM.spdx.json` | Deterministic SPDX record for app, both base images, embedded browsers/system inventory, and locked Python packages; the exact excluded reviewer-only WebKit package has declared/concluded `NOASSERTION` metadata |
| `space/THIRD_PARTY_LICENSES.json` | Reviewed license/notice records for every locked distribution, base image, and embedded browser identity, including the exact metadata-only WebKit `reviewer_test_only_not_redistributed` exception |
| `space/tests/test_claim_contract.py` | Exact card/UI copy and DOM/focus ordering |
| `space/tests/test_evidence_contract.py` | Receipt/release/deployment fail-closed validation |
| `space/tests/test_scenario_contract.py` | Four-state registry, no-score fields, adversarial pure lookup |
| `space/tests/test_gradio_contract.py` | Static config/API absence, outer-ASGI, route inventory, browser, accessibility, cold-start gates |
| `space/tests/test_export_contract.py` | Destination allowlist, hashes, capability and denylist checks |
| `space/tests/test_container_contract.py` | Dockerfile, UID/GID, read-only/tmpfs/CPU/network smoke contract |
| `space/deployment-manifest.json` | Added only in the second provenance commit; records app-source commit and export mapping |

`space/evidence/*.json`, `space/LICENSE`, `space/NOTICE`, and `space/CITATION.cff` are not copied into the GitHub app-source tree. The exporter reads those bytes directly from the `v0.2.0` tag commit and writes them only into the temporary candidate export.

### GitHub-source-only tooling

| File | Responsibility |
| --- | --- |
| `tools/space/requirements-runtime.in` | Reviewed direct runtime requirement input |
| `tools/space/requirements-dev.in` | Reviewed direct verification requirement input |
| `tools/space/lock-tooling.txt` | Hash-locked resolver/generator tooling |
| `tools/space/base-image.json` | Named runtime/reviewer records with patch tags, index/platform digests, Python/Playwright/browser identity, official tagged/CDN provenance, immutable tree absence proof, and external commit-pinned source-reference metadata/inventory hashes |
| `tools/space/license-policy.json` | Reviewed SPDX fields, dispositions, notice completeness, distribution scope, and exact fail-closed WebKit reviewer-only policy keyed by normalized package/version |
| `scripts/build_hf_space_supply_chain.py` | Resolve/verify locks, base reference, inventory, and SPDX outputs |
| `scripts/export_hf_space.py` | Generate deployment manifest and clean export from committed Git objects |
| `scripts/review_hf_space_local.py` | Ephemeral local browser/accessibility/cold-start evidence runner |
| `scripts/verify_hf_space_candidate.py` | Cross-platform ownership-safe final export/build/test/review orchestration with bounded temp cleanup |
| `tests/test_hf_space_source_boundary.py` | AST/import/no-write/no-network/no-existing-app boundary |
| `tests/test_hf_space_supply_chain.py` | Lock/base/SBOM/license reproducibility contracts |
| `tests/test_hf_space_exporter.py` | Git-object mapping, two-commit provenance, path and content rejection |
| `tests/test_hf_space_live_review.py` | Local 1440×900 and 390×844 review orchestration contract |
| `.github/workflows/space-ci.yml` | Space-specific locked tests, export verification, container smoke, SBOM/license scan |

### Core interfaces fixed for all tasks

```python
# space/carerisk_space/contracts.py
EvidenceFailureCode = Literal[
    "receipt_missing",
    "receipt_hash_mismatch",
    "receipt_schema_invalid",
    "release_relationship_invalid",
    "deployment_manifest_invalid",
]

@dataclass(frozen=True)
class EvidenceFailure:
    code: EvidenceFailureCode

@dataclass(frozen=True)
class MetricInterval:
    estimate: float
    lower: float
    upper: float

@dataclass(frozen=True)
class ReceiptEvidence:
    dataset_name: str
    dataset_role: str
    n: int
    events: int
    prevalence: float
    metrics: Mapping[str, MetricInterval]
    bootstrap_method: str
    bootstrap_samples: int
    bootstrap_seed: int
    evaluation_status: str
    success_count: int
    final_lock_status: str
    use_limitation: str
    formal_metrics_sha256: str

@dataclass(frozen=True)
class ManifestFile:
    source_ref: str
    source_path: str
    destination_path: str
    sha256: str | None
    byte_size: int | None
    media_type: str
    capability: Literal[
        "runtime_code", "evidence", "legal", "metadata", "supply_chain", "test"
    ]

@dataclass(frozen=True)
class ReleaseRelationship:
    release: str
    limitations: tuple[str, ...]
    scientific_change_flags: Mapping[str, bool]

@dataclass(frozen=True)
class DeploymentManifest:
    space_app_source_git_sha: str
    evidence_tag: str
    evidence_tag_object: str
    evidence_tag_commit: str
    destination_repository: str
    files: tuple[ManifestFile, ...]

@dataclass(frozen=True)
class EvidenceViewModel:
    receipt: ReceiptEvidence
    release: ReleaseRelationship
    manifest: DeploymentManifest

class ContractViolation(ValueError):
    pass

class ReceiptHashMismatch(ContractViolation):
    pass

EvidenceLoadResult = EvidenceViewModel | EvidenceFailure
```

```python
# space/carerisk_space/evidence.py signatures
# loads_strict_object(raw: bytes) -> dict[str, object]
# git_blob_sha1(raw: bytes) -> str
# validate_receipt(raw: bytes) -> ReceiptEvidence
# validate_release(raw: bytes, receipt: ReceiptEvidence) -> ReleaseRelationship
# validate_deployment_manifest(raw: bytes, *, receipt_raw: bytes, release_raw: bytes,
#                              receipt: ReceiptEvidence,
#                              release: ReleaseRelationship) -> DeploymentManifest
# load_evidence(bundle_root: Path) -> EvidenceLoadResult
# format_evidence(receipt: ReceiptEvidence, release: ReleaseRelationship,
#                 manifest: DeploymentManifest) -> EvidenceViewModel
```

```python
# space/carerisk_space/scenarios.py
@dataclass(frozen=True)
class ScenarioViewModel:
    id: str
    label_zh_tw: str
    state: Literal["evidence available", "evidence withheld"]
    reason_zh_tw: str
    schema_contract: bool
    measurement_coverage: bool
    value_pattern: bool

SCENARIOS: tuple[ScenarioViewModel, ...]
SCENARIO_IDS: tuple[str, ...]
# select_scenario(value: object) -> ScenarioViewModel  # startup-only pure lookup, never a server endpoint
# render_scenario(value: object) -> str
```

```python
# space/carerisk_space/ui.py signatures
# create_app(bundle_root: Path | None = None) -> gr.Blocks
# render_claim_header() -> str
# render_evidence(view: EvidenceViewModel) -> str
# render_evidence_failure(failure: EvidenceFailure) -> str
# PublicSurfaceGuard(
#     downstream: ASGIApp,
#     package_asset_urls: frozenset[str],
# )
```

```python
# scripts/export_hf_space.py
@dataclass(frozen=True)
class ExportedFile:
    path: str
    sha256: str
    byte_size: int

@dataclass(frozen=True)
class ExportReceipt:
    destination: Path
    files: tuple[ExportedFile, ...]
    tree_sha256: str

# build_deployment_manifest(*, repo_root: Path, app_source_sha: str) -> bytes
# export_space(*, repo_root: Path, app_source_sha: str, manifest_source_sha: str,
#              destination: Path) -> ExportReceipt
# verify_export(*, destination: Path) -> ExportReceipt
```

### Test-helper contracts

- `space/tests/test_evidence_contract.py` owns `source_or_bundled_evidence(name)`, `valid_manifest_bytes(receipt_raw, release_raw)`, `candidate_bundle(tmp_path)`, and `apply_mutation(bundle, mutation)`. The bundle fixture writes only three synthetic/public JSON files under pytest `tmp_path`; the manifest lists all 24 public paths but runtime tests re-hash only the three JSON files allowed to application code.
- `space/tests/test_gradio_contract.py` owns `valid_bundle`, `make_unit_failure_bundle(code, monkeypatch)`, `manifest_canary_bundle`, `RunningLocalApp`, `running_local_app`, `captured_app_logs`, `bounded_failure_codes(text)`, `exact_package_asset_urls()`, pure-ASGI bomb helpers, raw-wire Uvicorn+h11 helpers, and exact request-graph capture. `make_unit_failure_bundle` uses data-only mutations for the four runtime-reachable codes; only for `receipt_schema_invalid` does it invoke the already explicit controlled test anchor seam after changing strict-schema bytes. That seam is unit/component/ASGI-only and never enters `RunningLocalApp`, Docker, browser, cold-start, or final-image orchestration. `RunningLocalApp` exposes only `base_url`, the mounted parent/inner route inventory, an app-entry call marker installed outside the product guard, and callable in-memory log/request snapshots; it never persists logs. The server fixture binds loopback on port 7860 or an explicit test-only adapter that preserves the production scope constants, installs capture and the app-entry marker before startup, poisons framework-related host environment variables before application construction, yields only after permitted root/config/theme probes pass, and always closes server/capture in fixture cleanup. Its raw-wire helper sends exact HTTP/1.1 bytes to the explicitly configured Uvicorn+h11 server without monkeypatching the parser, so missing/duplicate Host 400 evidence can be distinguished from guard 404 evidence. It uses the public committed receipt/release bytes and a synthetic manifest; it never starts the existing dashboard. `manifest_canary_bundle` places `CANARY_7419` only in an invalid deployment-manifest field. `captured_app_logs` uses the same in-memory discipline for server-free construction, and `bounded_failure_codes` returns only exact members of `ALL_FAILURE_CODES`. `exact_package_asset_urls()` always calls the pinned-root membership builder, asserts a nonempty result, and is used by every guard unit helper; no helper supplies a default or empty set.
- `tests/test_hf_space_exporter.py` owns `git_repo`, `ExporterCase`, `APP_SOURCE_SHA`, and `MANIFEST_SOURCE_SHA`. The fixture creates a temporary two-commit Git repository containing synthetic text fixtures with the same path/capability rules, so exporter rejection tests never mutate the real repository.
- `tests/test_hf_space_live_review.py` owns `sample_record` and mocked process/browser adapters for unit tests. Real Docker/Playwright execution occurs only in Task 13 against the clean candidate.

---

### Task 0: Re-establish an isolated implementation baseline

**Files:**
- Read only: `AGENTS.md`
- Read only: `PROJECT_PLAN.md`
- Read only: `docs/superpowers/specs/2026-08-31-carerisk-48h-hf-space-design.md`
- Read only: `pyproject.toml`
- Read only: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: approved design commit and clean Git state.
- Produces: recorded branch/base/tool versions and honest legacy-suite baseline; no tracked file change.

- [ ] **Step 1: Verify exact branch, base, remote, and clean state**

```powershell
$approvedDesign = '10a85171afeb9fafb531b3bca1128cddc987619e'
$expectedMain = '11184984ddd553aa3b45a3d5fc0ea4a866877722'
git fetch origin main --tags --prune
$approvedImplementationHead = ([string]$env:CARERISK_APPROVED_IMPLEMENTATION_SHA).Trim()
if ($approvedImplementationHead -notmatch '^[0-9a-f]{40}$') { throw 'Invalid implementation HEAD' }
$currentHead = (git rev-parse HEAD).Trim()
if ($currentHead -cne $approvedImplementationHead) { throw 'HEAD differs from central authorization' }
if ((git branch --show-current).Trim() -cne 'docs/carerisk-hf-space-design') { throw 'Unexpected implementation branch' }
if ((git rev-parse origin/main).Trim() -cne $expectedMain) { throw 'origin/main moved; stop for central review' }
if ((git merge-base HEAD origin/main).Trim() -cne $expectedMain) { throw 'Unexpected merge-base' }
git merge-base --is-ancestor $approvedDesign $approvedImplementationHead
if ($LASTEXITCODE -ne 0) { throw 'Approved design is not an ancestor' }
$postDesignPaths = @(git diff --name-only "$approvedDesign..$approvedImplementationHead")
if ($postDesignPaths.Count -ne 1 -or $postDesignPaths[0] -cne 'docs/superpowers/plans/2026-08-31-carerisk-48h-hf-space.md') { throw 'Unexpected post-design scope' }
if (@(git status --porcelain=v1 --untracked-files=all).Count -ne 0) { throw 'Dirty worktree' }
```

Expected: central has explicitly named `$approvedImplementationHead` in its written implementation authorization; the branch is clean, the approved design is an ancestor, every post-design change is confined to this plan file, and the merge-base is the exact approved main base. If the current SHA differs from central authorization or any assertion fails, stop without edits.

- [ ] **Step 2: Create isolated verification environments outside tracked paths**

```powershell
python -m venv .venv-space
.venv-space\Scripts\python.exe -m pip install --upgrade pip
.venv-space\Scripts\python.exe -m pip install -e '.[app,dev,tabular]'
```

Expected: the existing suite has its declared extras without changing the global Python. `.venv-space/` must be ignored and absent from `git status`.

- [ ] **Step 3: Run the existing CPU-only baseline**

```powershell
$env:PYTHONNOUSERSITE = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:CUDA_VISIBLE_DEVICES = ''
$env:OMP_NUM_THREADS = '2'
$env:MKL_NUM_THREADS = '2'
.venv-space\Scripts\python.exe -m pytest -m 'not integration and not slow' -p no:cacheprovider
.venv-space\Scripts\ruff.exe check .
.venv-space\Scripts\mypy.exe
.venv-space\Scripts\python.exe -m pip check
```

Expected: all existing synthetic/mocked tests pass, Ruff and Mypy exit 0, and the isolated environment has no broken requirements. This command must not run any final-result exporter, downloader, training, or evaluation command.

- [ ] **Step 4: Record baseline without committing**

```powershell
git status --short --branch
git diff --check
```

Expected: no tracked or untracked change. Do not create a baseline commit.

### Task 1: Establish the Space-only package and exact claim/card contract

**Files:**
- Create: `space/carerisk_space/__init__.py`
- Create: `space/carerisk_space/contracts.py`
- Create: `space/README.md`
- Create: `space/tests/test_claim_contract.py`

**Interfaces:**
- Consumes: exact normative copy and card-order requirements from the approved design.
- Produces: `PRIMARY_CLAIM_ZH_TW`, `SAFETY_SUBTITLE_EN`, `PRODUCT_NAME`, and the public card safety boundary. UI DOM construction begins in Task 5.

- [ ] **Step 1: Write the failing exact-copy and card tests**

```python
def test_claim_copy_is_exact_and_card_places_it_first() -> None:
    assert PRIMARY_CLAIM_ZH_TW == EXPECTED_ZH_TW
    assert SAFETY_SUBTITLE_EN == EXPECTED_EN
    card = (SPACE_ROOT / "README.md").read_text(encoding="utf-8")
    body = card.split("---", 2)[2]
    assert body.index(EXPECTED_ZH_TW) < body.index("## Evidence")
    assert "sdk: docker" in card
    assert "app_port: 7860" in card
    assert "license: apache-2.0" in card
```

- [ ] **Step 2: Run the test to verify RED**

```powershell
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests/test_claim_contract.py -q
```

Expected: FAIL because `carerisk_space.contracts` and `space/README.md` do not exist.

- [ ] **Step 3: Add the minimal constants, immutable contract types, and Space card**

```python
PRODUCT_NAME = "CareRisk 48H — Evidence & Abstention Explorer"
PRIMARY_CLAIM_ZH_TW = (
    "僅供研究與教育；不是臨床診斷、治療、分流、資源配置或照護決策工具。"
    "本 Space 僅使用內建 synthetic gate-state scenarios，不接受、儲存或處理任何使用者提供的病人資料；"
    "不輸出 live probability、risk class、case recommendation 或 threshold-based case decision。"
)
SAFETY_SUBTITLE_EN = (
    "Research and education only. Non-clinical and synthetic-only. "
    "No patient data entry or upload, no live predictions, and no care decisions."
)
```

The card YAML and first rendered paragraphs must use these exact values, must omit the excluded evaluation image, and must state that Apache-2.0 covers application code while PhysioNet data is absent and remains under its source license.

- [ ] **Step 4: Run GREEN and scan prohibited claims**

```powershell
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests/test_claim_contract.py -q
rg -n -i 'clinical prediction|medical device|decision support|deployment-ready|validated for care' space/README.md
```

Expected: tests PASS; `rg` returns no matches.

- [ ] **Step 5: Commit the exact files**

```powershell
git add -- space/carerisk_space/__init__.py space/carerisk_space/contracts.py space/README.md space/tests/test_claim_contract.py
git diff --cached --check
git commit -m 'feat(space): establish safety and claim contracts'
```

### Task 2: Implement strict receipt and release validation

**Files:**
- Create: `space/carerisk_space/evidence.py`
- Create: `space/tests/test_evidence_contract.py`
- Modify: `space/carerisk_space/contracts.py`

**Interfaces:**
- Consumes: exact receipt/release bytes and anchors from `v0.2.0`.
- Produces: `loads_strict_object`, `git_blob_sha1`, `validate_receipt`, `validate_release`, `ReceiptEvidence`, and `ReleaseRelationship`.

- [ ] **Step 1: Write strict JSON and hash tests first**

```python
SPACE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = SPACE_ROOT.parent

def source_or_bundled_evidence(name: str) -> Path:
    bundled = SPACE_ROOT / "evidence" / name
    if bundled.is_file():
        return bundled
    source = SOURCE_ROOT / "docs" / name
    if not source.is_file():
        raise AssertionError(f"missing public evidence fixture: {name}")
    return source

def test_receipt_rejects_duplicate_json_keys() -> None:
    with pytest.raises(ContractViolation, match="receipt_schema_invalid"):
        loads_strict_object(b'{"schema_version":1,"schema_version":1}')

@pytest.mark.parametrize("token", [b"NaN", b"Infinity", b"-Infinity"])
def test_receipt_rejects_nonfinite_json_constants(token: bytes) -> None:
    raw = b'{"schema_version":' + token + b"}"
    with pytest.raises(ContractViolation, match="receipt_schema_invalid"):
        loads_strict_object(raw)

def test_exact_committed_receipt_hash_and_git_blob() -> None:
    raw = source_or_bundled_evidence("final-result-receipt.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == RECEIPT_SHA256
    assert git_blob_sha1(raw) == RECEIPT_GIT_BLOB_SHA
```

Task 2 owns design Section 7.2 gates 2–12 and Section 7.3 gates 2–6: exact raw bytes, strict JSON, typed schema, finite metrics/privacy, and the supplied validated receipt relationship. Add named tests `test_receipt_schema_is_exact`, `test_receipt_metrics_and_intervals_are_finite_and_ordered`, `test_receipt_privacy_exclusions_are_exact`, `test_release_relationship_is_exact`, plus controlled-anchor mutation coverage for each of those numbered gates. Gate 2 must patch neither the canonical SHA nor the canonical Git-blob anchor (retain both unchanged) and therefore fail at the raw SHA gate; gate 3 must patch only the SHA anchor (retain the blob anchor) to reach the Git-blob mismatch; gates 4–12 must controlled-patch both anchors to exercise downstream validation. JSON mutations must never masquerade as path, existence, symlink, manifest hash, or manifest-size gates.

- [ ] **Step 2: Run RED**

```powershell
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests/test_evidence_contract.py -q
```

Expected: FAIL on missing evidence interfaces.

Task 3 owns Section 7.2 gate 1 and Section 7.3 gate 1 through `read_regular_file` and deployment-manifest validation: literal package-relative paths, existence, regular/non-symlink checks, and manifest-declared hash/size checks. Task 3 must add exact missing-file, non-regular/symlink, receipt/release hash, and size mutations; these path/manifest gates must not be represented by JSON mutations.

- [ ] **Step 3: Implement strict parsing without permissive fallbacks**

```python
def loads_strict_object(raw: bytes) -> dict[str, object]:
    def unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ContractViolation("receipt_schema_invalid")
            result[key] = value
        return result

    def reject_constant(_: str) -> NoReturn:
        raise ContractViolation("receipt_schema_invalid")

    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=unique_pairs,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractViolation("receipt_schema_invalid") from exc
    if not isinstance(value, dict):
        raise ContractViolation("receipt_schema_invalid")
    return value

def git_blob_sha1(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw, usedforsecurity=False).hexdigest()
```

Build immutable typed values only after exact top-level/nested keys, expected constants, finite/range/interval consistency, bootstrap, privacy exclusions, formal metrics hash, receipt SHA-256, and Git blob gates pass. Do not expose threshold, confusion, PPV, NPV, sensitivity, specificity, subgroup, artifact, or record-level values in `ReceiptEvidence.metrics`.

Receipt tests and runtime validation must hash the exact unmodified bytes read from the approved Git blob; they must not normalize CRLF/LF. A CRLF-normalized diagnostic is rejected and is never exported or accepted by a manifest/runtime gate.

- [ ] **Step 4: Run targeted GREEN and type checks**

```powershell
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests/test_evidence_contract.py -q
.venv-space\Scripts\ruff.exe check space/carerisk_space/contracts.py space/carerisk_space/evidence.py space/tests/test_evidence_contract.py
.venv-space\Scripts\mypy.exe --strict space/carerisk_space
```

Expected: all targeted tests, Ruff, and strict Mypy pass.

- [ ] **Step 5: Commit the exact files**

```powershell
git add -- space/carerisk_space/contracts.py space/carerisk_space/evidence.py space/tests/test_evidence_contract.py
git diff --cached --check
git commit -m 'feat(space): validate immutable release evidence'
```

### Task 3: Add deployment-manifest validation and five bounded failure states

**Files:**
- Modify: `space/carerisk_space/contracts.py`
- Modify: `space/carerisk_space/evidence.py`
- Modify: `space/tests/test_evidence_contract.py`

**Interfaces:**
- Consumes: `ReceiptEvidence`, `ReleaseRelationship`, and raw manifest bytes.
- Produces: `DeploymentManifest`, `validate_deployment_manifest`, `load_evidence`, and exactly five `EvidenceFailureCode` values.

- [ ] **Step 1: Add failing normal/failure matrix tests**

```python
@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("remove_receipt", "receipt_missing"),
        ("change_receipt_byte", "receipt_hash_mismatch"),
        ("duplicate_receipt_key", "receipt_schema_invalid"),
        ("change_release_flag", "release_relationship_invalid"),
        ("change_manifest_source_sha", "deployment_manifest_invalid"),
    ],
)
def test_evidence_failure_reason_is_bounded(
    candidate_bundle: Path, mutation: str, expected: str
) -> None:
    apply_mutation(candidate_bundle, mutation)
    assert load_evidence(candidate_bundle) == EvidenceFailure(expected)

def test_normal_state_returns_receipt_backed_view(candidate_bundle: Path) -> None:
    result = load_evidence(candidate_bundle)
    assert isinstance(result, EvidenceViewModel)
    assert set(result.receipt.metrics) == {"auprc", "auroc", "brier", "ece"}
```

- [ ] **Step 2: Run RED**

```powershell
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests/test_evidence_contract.py -q
```

Expected: FAIL because manifest validation and bounded loading are absent.

- [ ] **Step 3: Implement the fail-closed loader**

```python
def load_evidence(bundle_root: Path) -> EvidenceLoadResult:
    try:
        receipt_raw = read_regular_file(bundle_root, "evidence/final-result-receipt.json")
    except FileNotFoundError:
        return EvidenceFailure("receipt_missing")
    try:
        receipt = validate_receipt(receipt_raw)
    except ReceiptHashMismatch:
        return EvidenceFailure("receipt_hash_mismatch")
    except ContractViolation:
        return EvidenceFailure("receipt_schema_invalid")
    try:
        release_raw = read_regular_file(bundle_root, "evidence/release-v0.2.0.json")
        release = validate_release(release_raw, receipt)
    except (FileNotFoundError, ContractViolation):
        return EvidenceFailure("release_relationship_invalid")
    try:
        manifest_raw = read_regular_file(bundle_root, "deployment-manifest.json")
        manifest = validate_deployment_manifest(
            manifest_raw,
            receipt_raw=receipt_raw,
            release_raw=release_raw,
            receipt=receipt,
            release=release,
        )
    except (FileNotFoundError, ContractViolation):
        return EvidenceFailure("deployment_manifest_invalid")
    return format_evidence(receipt, release, manifest)
```

`read_regular_file` accepts only the three literal package-relative paths, rejects symlinks and non-regular files, and never receives a user value. This implements Task 3’s Section 7.2 gate 1 and Section 7.3 gate 1 ownership. Manifest validation requires exact keys, exact tag/object/commit, destination `steven0226/carerisk-48h`, exact allowlist, sorted unique paths, file sizes/hashes, capability enum, base-image/lock/SBOM/license hashes, and receipt/release relationships. Its tests must use exact missing, symlink/non-regular, hash, and size mutations; JSON mutations cannot stand in for these path/manifest gates.

Define the 24-entry `PUBLIC_PATHS: tuple[str, ...]` once in `contracts.py` using the exact order in the File and Interface Map. Runtime manifest validation, UI provenance, exporter source mapping, and tests all consume that single application constant; the export contract test retains an independent expected tuple to catch accidental edits.

- [ ] **Step 4: Run GREEN for normal plus all five failures**

```powershell
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests/test_evidence_contract.py -q
```

Expected: normal state and exactly five bounded failures pass; no exception text, file path, or submitted value appears in a failure object.

- [ ] **Step 5: Commit the exact files**

```powershell
git add -- space/carerisk_space/contracts.py space/carerisk_space/evidence.py space/tests/test_evidence_contract.py
git diff --cached --check
git commit -m 'feat(space): fail closed on evidence provenance'
```

### Task 4: Implement the four fixed synthetic gate states and fail-closed pure lookup

**Files:**
- Create: `space/carerisk_space/scenarios.py`
- Create: `space/tests/test_scenario_contract.py`
- Modify: `space/carerisk_space/contracts.py`

**Interfaces:**
- Consumes: one Python object for a pure in-memory lookup used during startup pre-rendering and unit probes; there is no transport ownership.
- Produces: `SCENARIOS`, `select_scenario(value: object)`, and escaped bounded HTML from `render_scenario(value: object)`.

- [ ] **Step 1: Write the failing fixed-registry and adversarial tests**

```python
EXPECTED_IDS = (
    "synthetic_evidence_available",
    "synthetic_schema_withheld",
    "synthetic_coverage_withheld",
    "synthetic_value_pattern_withheld",
)

def test_registry_contains_only_four_abstract_scenarios() -> None:
    assert tuple(item.id for item in SCENARIOS) == EXPECTED_IDS
    serialized = json.dumps([asdict(item) for item in SCENARIOS], ensure_ascii=False)
    for prohibited in ("probability", "score", "threshold", "age", "gender", "record", "outcome"):
        assert prohibited not in serialized.lower()

@pytest.mark.parametrize(
    "value",
    [None, "", "unknown", "x" * 1_048_576, [], {}, {"id": EXPECTED_IDS[0]}, 1, True],
)
def test_adversarial_lookup_fails_closed_without_echo(value: object) -> None:
    html = render_scenario(value)
    assert "unknown_synthetic_scenario" in html
    assert str(value) not in html
    assert "evidence withheld" in html
```

- [ ] **Step 2: Run RED**

```powershell
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests/test_scenario_contract.py -q
```

Expected: FAIL because the registry and pure lookup do not exist.

- [ ] **Step 3: Implement exact lookup with no coercion or echo**

```python
def select_scenario(value: object) -> ScenarioViewModel:
    if type(value) is not str:
        return UNKNOWN_SCENARIO
    for scenario in SCENARIOS:
        if value == scenario.id:
            return scenario
    return UNKNOWN_SCENARIO

def render_scenario(value: object) -> str:
    scenario = select_scenario(value)
    return render_bounded_scenario_html(scenario)
```

The available scenario has all three booleans true and states that no score is produced. Each withheld scenario changes one approved gate and uses only its enumerated reason. `UNKNOWN_SCENARIO` is not added to `SCENARIOS` and always returns `evidence withheld` plus `unknown_synthetic_scenario`.

Set `SCENARIO_IDS = tuple(item.id for item in SCENARIOS)` once after the immutable registry is constructed; UI and review tooling import that tuple rather than duplicating IDs.

- [ ] **Step 4: Run GREEN and a source term scan**

```powershell
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests/test_scenario_contract.py -q
rg -n -i 'raw_probability|calibrated_probability|risk_class|case_recommendation|requires_human_review' space/carerisk_space/scenarios.py
```

Expected: tests PASS; the source scan returns no matches.

- [ ] **Step 5: Commit the exact files**

```powershell
git add -- space/carerisk_space/contracts.py space/carerisk_space/scenarios.py space/tests/test_scenario_contract.py
git diff --cached --check
git commit -m 'feat(space): add fixed synthetic gate states'
```

### Task 5: Build the safe Gradio surface and capability contract

**Files:**
- Create: `space/carerisk_space/ui.py`
- Create: `space/app.py`
- Create: `space/tests/test_gradio_contract.py`
- Modify: `space/carerisk_space/scenarios.py`
- Modify: `space/tests/test_claim_contract.py`
- Modify: `space/tests/test_evidence_contract.py`
- Modify: `space/tests/test_scenario_contract.py`

**Interfaces:**
- Consumes: `EvidenceLoadResult`, `SCENARIOS`, and `render_scenario`.
- Produces: `create_app(bundle_root: Path | None = None) -> gr.Blocks`, a one-document static HTML/CSS explorer, `build_package_asset_membership() -> frozenset[str]`, `PublicSurfaceGuard(downstream: ASGIApp, package_asset_urls: frozenset[str])`, exact outer-ASGI authority/path/membership/scope sanitization, fixed FastAPI mount/Uvicorn composition, and a static evidence-failure page. Both constructor arguments are mandatory; the membership is always the nonempty exact pinned-root result.

- [ ] **Step 1: Write failing static-document and zero-app-owned-capability config tests**

```python
THEME_CSS_SHA256 = "8ad6f9b14414574fe6c6d9b4362dcdd63dfdc66d8c34cbef0982888dfc44ff04"
THEME_QUERY = b"v=" + THEME_CSS_SHA256.encode("ascii")

def test_gradio_version_and_normal_config_are_static_and_event_free(
    valid_bundle: Path,
) -> None:
    assert gr.__version__ == "6.26.0"
    app = create_app(valid_bundle)
    config = app.get_config_file()
    assert [item["type"] for item in config["components"]] == ["html"]
    assert config["dependencies"] == []
    assert config["enable_queue"] is True  # pinned framework fact, not app capability
    assert len(app.fns) == 0
    assert app.get_api_info() == {"named_endpoints": {}, "unnamed_endpoints": {}}
    props = config["components"][0]["props"]
    assert "js_on_load" not in props
    assert "server_functions" not in props
    assert props["buttons"] == []
    assert props["_selectable"] is False
    assert not {item["type"] for item in config["components"]} & {
        "radio",
        "textbox", "code", "file", "uploadbutton", "dataframe", "json",
        "image", "audio", "video", "chatbot", "multimodaltextbox",
    }

def test_static_document_prerenders_four_exact_scenarios_once(
    valid_bundle: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    original = ui_module.render_scenario
    monkeypatch.setattr(
        ui_module,
        "render_scenario",
        lambda value: calls.append(cast(str, value)) or original(value),
    )
    document = only_html_value(create_app(valid_bundle))
    assert calls == list(EXPECTED_IDS)
    parsed = parse_static_explorer(document)
    assert parsed.radio_ids == EXPECTED_IDS
    assert parsed.radio_group_names == ("synthetic-gate-scenario",) * 4
    assert parsed.checked_ids == ()
    assert parsed.labels == tuple(item.label_zh_tw for item in SCENARIOS)
    assert parsed.panel_html == tuple(render_scenario(item) for item in EXPECTED_IDS)
    assert "<script" not in document.casefold()
    assert not re.search(r"\bon[a-z]+\s*=", document, re.IGNORECASE)
    assert all_gr_html_calls_explicitly_disable_js_on_load(
        Path("space/carerisk_space/ui.py")
    )

def test_claim_dom_precedes_first_focusable_control(valid_bundle: Path) -> None:
    document = only_html_value(create_app(valid_bundle))
    parsed = parse_static_explorer(document)
    assert parsed.claim_position < parsed.first_focusable_position
    assert document.index(EXPECTED_ZH_TW) < document.index(EXPECTED_EN)
    assert parsed.fieldset_legend == "選擇固定 synthetic gate state"
    assert parsed.all_labels_reference_existing_controls

@pytest.mark.parametrize("failure_code", ALL_FAILURE_CODES)
def test_failure_page_is_one_static_document_with_no_inputs_or_functions(
    failure_code: EvidenceFailureCode,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = make_unit_failure_bundle(failure_code, monkeypatch)
    app = create_app(bundle)
    config = app.get_config_file()
    assert [item["type"] for item in config["components"]] == ["html"]
    assert config["dependencies"] == []
    assert config["enable_queue"] is True
    assert len(app.fns) == 0
    document = only_html_value(app)
    assert "Evidence unavailable" in document
    assert failure_code in document
    assert not re.search(r"<input\b|<button\b|<select\b|<textarea\b", document)
    for metric in ("0.555", "0.870", "0.087", "0.008"):
        assert metric not in document

def test_schema_failure_controlled_unit_seam_is_fail_closed_through_asgi(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = make_unit_failure_bundle("receipt_schema_invalid", monkeypatch)
    demo = create_app(bundle)
    app = compose_in_memory_outer_app(demo, exact_package_asset_urls())
    response = run_permitted_root_asgi(app)
    assert response.status == 200
    assert response.heading == "Evidence unavailable"
    assert response.zh_tw_explanation == (
        "公開 evidence 未通過完整性驗證，因此本頁不顯示 metrics 或 synthetic gate states。"
    )
    assert response.english_explanation == (
        "Evidence integrity checks failed; metrics and scenarios are disabled."
    )
    assert response.visible_failure_code == "receipt_schema_invalid"
    assert response.visible_bounded_codes == ("receipt_schema_invalid",)
    assert ordered_visible_failure_text(response.document) == (
        "Evidence unavailable",
        "公開 evidence 未通過完整性驗證，因此本頁不顯示 metrics 或 synthetic gate states。",
        "Evidence integrity checks failed; metrics and scenarios are disabled.",
        "receipt_schema_invalid",
    )
    assert response.radio_count == response.control_count == response.scenario_panel_count == 0
    assert response.visible_metric_count == response.visible_canonical_value_count == 0
    assert demo.get_config_file()["dependencies"] == []
    assert len(demo.fns) == 0
    assert demo.get_api_info() == {"named_endpoints": {}, "unnamed_endpoints": {}}
    assert response.app_owned_event_or_api_request_count == response.echo_count == 0

POISONED_FRAMEWORK_ENV = {
    "GRADIO_ANALYTICS_ENABLED": "true",
    "HF_HUB_DISABLE_TELEMETRY": "0",
    "GRADIO_WATCH_DIRS": "/CANARY_7419",
    "GRADIO_VIBE_MODE": "true",
    "GRADIO_HOT_RELOAD": "true",
    "GRADIO_RUN_HISTORY": "True",
    "GRADIO_SSR_MODE": "True",
    "GRADIO_MCP_SERVER": "True",
    "GRADIO_ALLOWED_PATHS": "/",
    "GRADIO_BLOCKED_PATHS": "",
    "GRADIO_ROOT_PATH": "/CANARY_7419",
    "GRADIO_SHARE": "true",
    "GRADIO_MONITORING_ENABLED": "true",
    "GRADIO_DEBUG": "true",
    "GRADIO_SERVER_NAME": "CANARY_7419.invalid",
    "GRADIO_SERVER_PORT": "9998",
    "GRADIO_NUM_WORKERS": "9",
    "GRADIO_NODE_PATH": "/CANARY_7419/node",
    "GRADIO_LOCAL_DEV_MODE": "true",
    "GRADIO_NODE_SERVER_PORT": "9997",
    "SPACE_ID": "CANARY_7419/poisoned-space",
    "PORT": "9999",
}

def test_exact_instance_state_ignores_poisoned_framework_environment(
    valid_bundle: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name, value in POISONED_FRAMEWORK_ENV.items():
        monkeypatch.setenv(name, value)
    app = create_app(valid_bundle)
    assert os.environ["HF_HUB_DISABLE_TELEMETRY"] == "True"
    assert app.dev_mode is False
    assert app.vibe_mode is False
    assert app.root_path == ""
    assert app.api_open is False
    assert app.space_id is None
    assert app.get_config_file()["dependencies"] == []
```

- [ ] **Step 2: Run RED**

```powershell
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests/test_gradio_contract.py space/tests/test_claim_contract.py -q
```

Expected: FAIL because the one-document renderer, explicit `js_on_load=None`, zero app-owned-capability config, asset membership, authority-aware outer guard, and fixed mount/server composition do not exist.

- [ ] **Step 3: Implement the minimal pre-rendered Blocks and direct outer composition**

```python
def create_app(bundle_root: Path | None = None) -> gr.Blocks:
    root = bundle_root if bundle_root is not None else Path(__file__).resolve().parents[1]
    evidence = load_evidence(root)
    document = (
        render_static_failure_document(evidence)
        if isinstance(evidence, EvidenceFailure)
        else render_static_explorer_document(
            evidence,
            tuple((item, render_scenario(item.id)) for item in SCENARIOS),
        )
    )
    with gr.Blocks(analytics_enabled=False, title=PRODUCT_NAME) as app:
        gr.HTML(
            document,
            elem_id="carerisk-static-document",
            js_on_load=None,
        )
    app.dev_mode = False
    app.vibe_mode = False
    app.root_path = ""
    app.api_open = False
    app.space_id = None
    return app
```

The one HTML document owns `#carerisk-space-root`, the complete claim ceiling, fixed evidence, the native `fieldset` radio explorer, every pre-rendered result panel, and provenance links. No link or focusable element precedes the claim. CSS uses exact ID/sibling selectors to reveal only the checked panel; it contains no `url(...)`, import, or external reference. Failure HTML includes one bounded code and no raw exception. `js_on_load=None` is explicit on every `gr.HTML`; source/config mutation tests reject its omission, any `js_on_load` or `server_functions` config entry, nonempty `buttons`, selectability, or event dependency. “No inline JavaScript” applies to app-authored HTML/config, not to Gradio's pinned shell JavaScript.

`PublicSurfaceGuard` and `build_package_asset_membership` remain in this same `ui.py`; no eighth Task 5 file is added. The guard is a pure ASGI wrapper that stores only the downstream app and immutable asset URL set. It passes only lifespan. WebSocket sends exactly `{"type": "websocket.close", "code": 1008, "reason": ""}` without downstream or receive; unknown scope types return with no downstream, receive, or output. For HTTP it may inspect method/path/raw path/query/headers only for classification and never reads the body or logs client values.

The method/path/query table is exact: only `/` accepts `GET` and `HEAD` with empty query because pinned Gradio explicitly registers both root methods. `/config`, `/manifest.json`, `/favicon.ico`, and every exact immutable package member accept `GET` only with empty query. `/theme.css` accepts `GET` only with exact query `v=8ad6f9b14414574fe6c6d9b4362dcdd63dfdc66d8c34cbef0982888dfc44ff04`. The frozen theme value must equal both `app.get_config_file()["theme_hash"]` and `sha256(app.theme_css.encode("utf-8"))`. Every other method/path/query, including `HEAD` for any non-root path, every Gradio API, and every non-allowlisted metadata route, is outer-blocked with the fixed 404.

The canonical predicate is global: `raw_path == path.encode("ascii")`; no percent/backslash/control/NUL/non-ASCII, dot/empty segment, duplicate slash, normalization, case alias, or alternate separator. Asset segments match `[A-Za-z0-9_][A-Za-z0-9._@+~-]*`; the leading underscore exists solely because the pinned package contains `__vite-browser-external-B0RrT0g9.js`. Suffixes are exactly `.css`, `.js`, `.svg`, `.ttf`, `.wasm`, `.woff`, or `.woff2`, and exact URL membership remains authoritative. A valid suffix or grammar cannot authorize an absent or differently cased package file.

At startup, enumerate only `gradio.routes.BUILD_PATH_LIB` as URL prefix `/assets/` and `gradio.routes.STATIC_PATH_LIB` as `/static/`. Resolve each source-audited root strictly; reject a missing, non-directory, or symlink root. Walk read-only with `pathlib`, accept only regular non-symlink files, and prove each strict resolution remains beneath its exact root with `Path.relative_to`; reject special files, symlink files/directories, containment escapes, duplicate URLs, noncanonical relative names, and case aliases. No argument, environment, working directory, user path, other site-package root, evidence path, or temporary path can extend the roots. Build a `frozenset[str]`. Tests derive sorted `url<TAB>size<TAB>sha256<LF>` records and compare membership/content-tree digest between the exact locked Linux runtime and reviewer images; the observed local 916/50 counts are evidence only, not assertions across wheels.

An otherwise permitted request is still rejected when `Transfer-Encoding` exists or `Content-Length` is malformed, duplicated, or nonzero. It also requires exactly one header entry with name bytes `b"host"` and value bytes exactly matching this immutable map:

```python
AUTHORITY_MAP = MappingProxyType({
    b"127.0.0.1:7860": ("http", ("127.0.0.1", 7860), ("127.0.0.1", 0)),
    b"localhost:7860": ("http", ("localhost", 7860), ("127.0.0.1", 0)),
    b"carerisk-app:7860": ("http", ("carerisk-app", 7860), ("127.0.0.1", 0)),
    b"steven0226-carerisk-48h.hf.space": (
        "https", ("steven0226-carerisk-48h.hf.space", 443), ("127.0.0.1", 0)
    ),
})
```

At the direct pure-ASGI layer, missing, duplicated, comma-combined, whitespace-padded, uppercase, trailing-dot, userinfo, extra/default-port, IPv6-alias, or unlisted Host is blocked by the guard. On the pinned Uvicorn+h11 wire, missing/duplicate Host is rejected by the parser before ASGI with exact 400 and zero app-entry/downstream marker delta; that evidence must not be labeled as a guard 404. A syntactically valid unlisted single Host reaches the guard and receives the fixed 404. For a listed Host, construct a fresh sanitized HTTP scope with the selected constant scheme/server/client, `root_path=""`, and sole header `(b"host", selected_host_bytes)`; preserve only validated method/path/raw path/query and protocol versions. Do not forward Origin, Cookie, Authorization, `X-*`, Forwarded, User-Agent, or any other client header. `proxy_headers=False` remains load-bearing. Direct-ASGI blocked HTTP emits the exact 404 start plus `b"Not Found"` response-body message and fixed `content-length: 9`, with no CORS/compression/echo and without downstream or receive. Uvicorn/HTTP wire observation of a blocked `HEAD` retains status 404 and `content-length: 9` but has an exact zero-byte entity body; this is asserted separately from the ASGI message sequence.

With `title=PRODUCT_NAME` and mount `favicon_path=None`, running tests require exact GET `/manifest.json` media type and body `{"name": PRODUCT_NAME, "icons": [{"src": "static/img/logo_nosize.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"}], "start_url": "./", "display": "standalone"}`. GET `/favicon.ico` must equal the locked `STATIC_PATH_LIB/img/logo.svg` blob (1,107 bytes, SHA-256 `3d131bff3fe15bcbb3e6e6552a8bee25377c3666723a9cbe68ceca953ea613df`); `/static/img/logo_nosize.svg` must equal 1,082 bytes and SHA-256 `89fd7687072f6c1ab52be3348494f0410c270f453e8306105719b2e3f7091469`. Responses contain no canary and trigger no network/write. Every `/pwa_icon` variant is blocked. HEAD for metadata/config/theme/package paths is blocked by the outer guard with the fixed 404 and must not reach Gradio; no inner 405 or fake GET-content parity is accepted.

The existing `select_scenario`/`render_scenario` functions remain pure startup-only render helpers. They are never bound to Gradio or exposed as endpoints. Task 5 removes no Task 4 input-hardening, but the public proof no longer depends on accepting or rejecting a transport value because no transport exists.

When startup evidence is invalid, `create_app` logs exactly one structured bounded failure code and no exception, path, artifact bytes, or submitted value. The logger receives `EvidenceFailure.code` only. Tests capture the startup log for `manifest_canary_bundle`, require the bounded code `deployment_manifest_invalid`, and prove `CANARY_7419` and its representation are absent, preserving Design Section 12 without weakening it.

The assignments after the `Blocks` context are exact Gradio `6.26.0` per-instance configuration, not framework-global monkeypatching. Product modules do not import `os` or read environment variables. Tests poison every listed framework variable before construction and prove the exact instance, mount, Uvicorn, static config, and outer-wrapper state remain unchanged.

`space/app.py` imports only pinned `fastapi`, `gradio`, `uvicorn`, `create_app`, `build_package_asset_membership`, and `PublicSurfaceGuard`. It builds `parent = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)`, mounts with exact `gr.mount_gradio_app(parent, demo, path="/", server_name="0.0.0.0", server_port=7860, footer_links=[], run_history=False, root_path="", allowed_paths=["/__carerisk_no_allowed_files__"], blocked_paths=["/"], favicon_path=None, show_error=False, max_file_size=0, ssr_mode=False, enable_monitoring=False, pwa=False, mcp_server=False)`, then assigns `app = PublicSurfaceGuard(parent, build_package_asset_membership())`. It calls `uvicorn.run(app, host="0.0.0.0", port=7860, workers=1, http="h11", proxy_headers=False, forwarded_allow_ips="", access_log=False, server_header=False, date_header=False, reload=False, factory=False, env_file=None, log_config=None)` only under the main guard. There is no `launch`, `app_kwargs`, CLI/config file, authentication, user mount, or environment read; `auto` and `httptools` are forbidden parser values.

- [ ] **Step 4: Add outer-ASGI, composition, route-inventory, and running probes**

```python
def test_outer_guard_blocks_http_before_downstream_or_receive() -> None:
    package_asset_urls = exact_package_asset_urls()
    for scope in hostile_http_scopes():
        downstream = DownstreamBomb()
        receive = ReceiveBomb()
        messages = run_asgi(
            PublicSurfaceGuard(downstream, package_asset_urls), scope, receive
        )
        assert downstream.calls == 0
        assert receive.calls == 0
        assert messages == fixed_not_found_messages()
        assert messages[-1] == {
            "type": "http.response.body", "body": b"Not Found", "more_body": False,
        }
        assert response_header(messages, b"content-length") == b"9"
        serialized = serialize_asgi_messages(messages)
        assert b"CANARY_7419" not in serialized
        assert b"access-control-allow-origin" not in serialized.lower()
        assert b"content-encoding" not in serialized.lower()

def test_outer_guard_constructor_is_exact_and_rejects_empty_membership() -> None:
    parameters = inspect.signature(PublicSurfaceGuard).parameters
    assert tuple(parameters) == ("downstream", "package_asset_urls")
    assert all(item.default is inspect.Parameter.empty for item in parameters.values())
    membership = exact_package_asset_urls()
    assert membership
    guard = PublicSurfaceGuard(ScopeRecorder(), membership)
    assert guard.package_asset_urls == membership
    with pytest.raises(PackageAssetContractError, match="package_asset_membership_empty"):
        PublicSurfaceGuard(ScopeRecorder(), frozenset())

def test_outer_guard_rejects_websocket_and_unknown_scope_without_inner_calls() -> None:
    package_asset_urls = exact_package_asset_urls()
    for scope in hostile_websocket_and_unknown_scopes():
        downstream = DownstreamBomb()
        receive = ReceiveBomb()
        messages = run_asgi(
            PublicSurfaceGuard(downstream, package_asset_urls), scope, receive
        )
        assert downstream.calls == 0
        assert receive.calls == 0
        assert messages == fixed_rejection_messages_for(scope["type"])

def test_permitted_http_is_canonical_bodyless_and_sanitized() -> None:
    for scope, expected in allowed_scopes_with_hostile_headers_for_each_authority():
        recorder = ScopeRecorder()
        receive = ReceiveBomb()
        run_asgi(PublicSurfaceGuard(recorder, exact_package_asset_urls()), scope, receive)
        assert receive.calls == 0
        assert recorder.scope == expected
        assert recorder.scope["headers"] == [(b"host", expected_host(scope))]
        assert not attacker_headers(recorder.scope)

def test_host_must_be_one_exact_canonical_authority() -> None:
    package_asset_urls = exact_package_asset_urls()
    for headers in direct_asgi_missing_duplicate_invalid_and_unlisted_hosts():
        downstream = DownstreamBomb()
        receive = ReceiveBomb()
        messages = run_asgi(
            PublicSurfaceGuard(downstream, package_asset_urls),
            make_scope("GET", "/", headers=headers),
            receive,
        )
        assert messages == fixed_not_found_messages()
        assert downstream.calls == receive.calls == 0

def test_pure_asgi_exact_read_only_method_table_and_blocked_head_messages() -> None:
    package_asset_urls = exact_package_asset_urls()
    assert direct_guard_status("GET", "/", package_asset_urls) == 200
    assert direct_guard_status("HEAD", "/", package_asset_urls) == 200
    for path, query in exact_get_only_paths_and_queries():
        assert direct_guard_status("GET", path, query, package_asset_urls) == 200
        messages = direct_guard_messages("HEAD", path, query, package_asset_urls)
        assert response_status(messages) == 404
        assert response_header(messages, b"content-length") == b"9"
        assert response_body_message(messages) == b"Not Found"
        assert direct_guard_status("OPTIONS", path, query, package_asset_urls) == 404
        assert direct_guard_status("POST", path, query, package_asset_urls) == 404
    assert all_fixed_404s_have_no_downstream_or_receive()

def test_uvicorn_h11_wire_missing_and_duplicate_host_fail_before_asgi(
    running_local_app: RunningLocalApp,
) -> None:
    before = running_local_app.app_entry_calls()
    for request_bytes in missing_and_duplicate_host_http11_requests("CANARY_7419"):
        response = running_local_app.send_raw_http11(request_bytes)
        assert response.status_code == 400
        assert running_local_app.app_entry_calls() == before
        assert b"CANARY_7419" not in response.raw
        assert b"access-control-allow-origin" not in response.raw.lower()
        assert b"content-encoding" not in response.raw.lower()
        assert b"CANARY_7419" not in running_local_app.captured_logs().encode()

def test_uvicorn_wire_head_entity_is_empty_but_content_length_is_deterministic(
    running_local_app: RunningLocalApp,
) -> None:
    root = head(running_local_app.base_url, "/", host="127.0.0.1:7860")
    assert root.status_code == 200
    assert root.content == b""
    for path, query in exact_get_only_paths_and_queries():
        response = head(
            running_local_app.base_url, path, query=query, host="127.0.0.1:7860"
        )
        assert response.status_code == 404
        assert response.content == b""
        assert response.headers["content-length"] == "9"

def test_valid_unlisted_single_wire_host_reaches_guard_and_returns_404(
    running_local_app: RunningLocalApp,
) -> None:
    before = running_local_app.app_entry_calls()
    response = get(running_local_app.base_url, "/", host="unlisted.invalid")
    assert response.status_code == 404
    assert response.content == b"Not Found"
    assert running_local_app.app_entry_calls() == before + 1

def test_package_asset_membership_is_exact_regular_and_root_contained() -> None:
    membership = build_package_asset_membership()
    audit = audit_locked_package_roots(BUILD_PATH_LIB, STATIC_PATH_LIB)
    assert membership == audit.urls
    assert audit.duplicates == ()
    assert audit.special_files == ()
    assert audit.symlinks == ()
    assert audit.containment_failures == ()
    assert all(url.startswith(("/assets/", "/static/")) for url in membership)
    assert unknown_valid_suffix_url(membership) not in membership

@pytest.mark.parametrize("mutation", [
    "missing_root", "symlink_root", "symlink_file", "symlink_directory",
    "case_alias", "containment_escape", "special_file", "duplicate_url",
])
def test_package_asset_membership_mutations_fail_closed(mutation: str) -> None:
    with source_root_mutation(mutation):
        with pytest.raises(PackageAssetContractError):
            build_package_asset_membership()

def test_exact_manifest_favicon_and_default_logo_are_locked(
    running_local_app: RunningLocalApp,
) -> None:
    manifest = get(running_local_app.base_url, "/manifest.json")
    assert manifest.status_code == 200
    assert manifest.headers["content-type"].startswith("application/manifest+json")
    assert manifest.json() == expected_manifest(PRODUCT_NAME)
    assert b"CANARY_7419" not in manifest.content
    favicon = get(running_local_app.base_url, "/favicon.ico")
    assert len(favicon.content) == 1107
    assert sha256(favicon.content).hexdigest() == FAVICON_SHA256
    logo = get(running_local_app.base_url, "/static/img/logo_nosize.svg")
    assert len(logo.content) == 1082
    assert sha256(logo.content).hexdigest() == MANIFEST_LOGO_SHA256
    assert no_network_or_write_delta()
    assert every_pwa_icon_variant_is_outer_blocked(running_local_app)

def test_theme_query_and_content_hash_are_exact(valid_bundle: Path) -> None:
    demo = create_app(valid_bundle)
    mounted = compose_app(demo)
    assert demo.get_config_file()["theme_hash"] == THEME_CSS_SHA256
    assert sha256(demo.theme_css.encode("utf-8")).hexdigest() == THEME_CSS_SHA256
    assert guard_accepts(make_scope("GET", "/theme.css", THEME_QUERY))
    assert not guard_accepts(make_scope("GET", "/theme.css", b""))
    assert not guard_accepts(make_scope("GET", "/theme.css", b"v=CANARY_7419"))

def test_failure_log_contains_only_bounded_reason(
    manifest_canary_bundle: Path,
    captured_app_logs: Callable[[], str],
) -> None:
    create_app(manifest_canary_bundle)
    captured = captured_app_logs()
    assert bounded_failure_codes(captured) == ("deployment_manifest_invalid",)
    assert "CANARY_7419" not in captured
    assert repr({"secret": "CANARY_7419"}) not in captured

def test_in_process_api_metadata_is_empty_and_public_api_route_is_blocked(
    running_local_app: RunningLocalApp,
) -> None:
    assert running_local_app.demo.get_api_info() == {
        "named_endpoints": {}, "unnamed_endpoints": {},
    }
    response = get(running_local_app.base_url, "/gradio_api/info")
    assert response.status_code == 404
    assert response.content == b"Not Found"

def test_entrypoint_mount_and_uvicorn_contract_are_exact_under_poisoned_environment(
    captured_composition: CapturedComposition,
) -> None:
    assert captured_composition.parent_constructor == {
        "docs_url": None, "redoc_url": None, "openapi_url": None,
    }
    assert captured_composition.mount == {
        "path": "/",
        "server_name": "0.0.0.0",
        "server_port": 7860,
        "footer_links": [],
        "run_history": False,
        "root_path": "",
        "allowed_paths": ["/__carerisk_no_allowed_files__"],
        "blocked_paths": ["/"],
        "favicon_path": None,
        "show_error": False,
        "max_file_size": 0,
        "ssr_mode": False,
        "enable_monitoring": False,
        "pwa": False,
        "mcp_server": False,
    }
    assert isinstance(captured_composition.served_app, PublicSurfaceGuard)
    assert captured_composition.served_app.app is captured_composition.parent
    assert captured_composition.served_app.package_asset_urls == build_package_asset_membership()
    assert captured_composition.parent.user_middleware == []
    assert captured_composition.uvicorn == {
        "host": "0.0.0.0", "port": 7860, "workers": 1,
        "http": "h11",
        "proxy_headers": False, "forwarded_allow_ips": "",
        "access_log": False, "server_header": False, "date_header": False,
        "reload": False, "factory": False, "env_file": None, "log_config": None,
    }

def test_registered_gradio_routes_are_exhaustively_classified(
    running_local_app: RunningLocalApp,
) -> None:
    registered = recursively_expand_parent_mount_and_inner_routes(
        running_local_app.parent,
        included_router_attribute="original_router",
    )
    classified = classify_gradio_626_routes(registered)
    assert classified.unclassified == frozenset()
    assert classified.safe_required == EXPECTED_SAFE_REQUIRED_ROUTE_METHODS
    assert classified.pre_boundary_blocked == EXPECTED_PRE_BOUNDARY_BLOCKED_ROUTE_METHODS

def test_running_outer_guard_precedes_fastapi_gradio_fetch_temp_and_body_capabilities(
    running_local_app: RunningLocalApp,
    gradio_outbound_fetch_bomb: OutboundFetchBomb,
    gradio_tempfile_bomb: TemporaryFileBomb,
    temp_entry_snapshot: Callable[[], frozenset[str]],
) -> None:
    assert get(running_local_app.base_url, "/").status_code == 200
    assert get(running_local_app.base_url, "/config").status_code == 200
    assert_exact_theme_metadata_and_packaged_assets_load(running_local_app.base_url)
    sentinel = Path("/__carerisk_no_allowed_files__").resolve(strict=False)
    assert sentinel.is_absolute()
    assert not sentinel.exists()
    assert_capability_unavailable(running_local_app.base_url, "run_history")
    assert_capability_unavailable(running_local_app.base_url, "monitoring")
    before = temp_entry_snapshot()
    for probe in guard_reachable_url_local_upload_authority_query_header_cookie_cors_brotli_and_ambiguity_probes():
        response = send_probe(running_local_app.base_url, probe)
        assert response.status_code == 404
        if probe.method == "HEAD":
            assert response.content == b""
            assert response.headers["content-length"] == "9"
        else:
            assert response.content == b"Not Found"
        assert_probe_not_echoed(response, probe)
        assert "access-control-allow-origin" not in response.headers
        assert "content-encoding" not in response.headers
    assert temp_entry_snapshot() == before
    assert gradio_outbound_fetch_bomb.calls == 0
    assert gradio_tempfile_bomb.calls == 0
    assert running_local_app.request_graph.posts == ()
    assert running_local_app.request_graph.event_or_session_requests == ()
    assert public_interaction_state_delta(running_local_app) == empty_state_delta()
```

The static config is the app-owned transport proof: it contains zero inputs, dependencies, functions, or API endpoints, while recording pinned `config.enable_queue == true` and framework internal queue/state initialization. The outer guard blocks every Gradio API/queue/event/session route. In-process API metadata is empty; `/gradio_api/info` is not a public endpoint. Browser radio transitions are native HTML/CSS; the request graph remains inside the exact read-only method/path/query table with zero API, POST, event, queue, or session request and zero public-interaction state delta. The controlled-seam `receipt_schema_invalid` unit/component/direct-ASGI probe must assert heading `Evidence unavailable`, zh-TW explanation `公開 evidence 未通過完整性驗證，因此本頁不顯示 metrics 或 synthetic gate states。`, English explanation `Evidence integrity checks failed; metrics and scenarios are disabled.`, and the sole bounded code `receipt_schema_invalid`, plus zero controls/metrics/scenarios/API/event/echo; it is never labeled live-reviewed. The evidence-failure startup probe separately requires exactly the bounded reason and no manifest sentinel in captured logs.

The poisoned-environment fixture covers application construction, exact telemetry value after Blocks, mount capture, exact two-argument direct wrapper identity, Uvicorn capture, and a running server. Pure-ASGI matrices always derive a nonempty package membership from the pinned roots and cover every non-allowlisted method; API/queue/file/upload/proxy/component/monitoring/auth/docs/vibe routes; hostile body framing/authority/query/cookie/header/raw path; URL/local file and multipart canaries; encoded/traversal/case/slash variants; WebSocket; and unknown scopes. Direct-ASGI blocked-response tests assert the exact 9-byte body message and `content-length: 9`. Running integration replaces Gradio outbound fetch and temporary-file construction with bombs and proves guard interception occurs outside FastAPI and Gradio with no downstream, receive, CORS, Brotli, temp delta, network call, response/log echo, or traceback. Separate raw-wire tests leave the pinned Uvicorn+h11 parser untouched, require exact 400 and zero ASGI app-entry marker delta for missing/duplicate Host, require valid unlisted Host to reach the guard's 404, and require blocked `HEAD` responses to expose zero entity bytes with `content-length: 9`. Permitted requests deliver only the selected constant sanitized scope to the inner app.

The route test expands the parent mount and inner Gradio `_IncludedRouter.original_router`. Every Gradio `6.26.0` method/route is explicitly classified as exact required read-only surface or outer-boundary-blocked; a new or unclassified item fails. Tests bind the package routes to only `BUILD_PATH_LIB` and `STATIC_PATH_LIB`, exercise root/symlink/case/containment mutations, block a syntactically valid nonexistent filename before Gradio, and record sorted membership/content-tree digests. Sentinel/root-block/max-size remain defense-in-depth state. If mount signature, outer order, authority map, sanitized scope, asset membership, normal browser route use, or later HF Docker behavior requires anything else, stop for exact source audit, a RED test, and central written review; do not add a wildcard.

- [ ] **Step 5: Run GREEN for normal plus all five taxonomy UI states at unit/component level**

```powershell
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests/test_claim_contract.py space/tests/test_evidence_contract.py space/tests/test_scenario_contract.py space/tests/test_gradio_contract.py -q
```

Expected: validated normal state plus all five bounded taxonomy failure surfaces pass at unit/component level; every Blocks has zero app-owned inputs/dependencies/functions/API and explicit no-component-JS config, while preserving the recorded `enable_queue == true` fact; outer-ASGI unit/integration bombs prove pre-FastAPI/pre-Gradio/pre-receive interception, exact authority sanitization, exact package membership and metadata; and every exact Gradio `6.26.0` route/method is classified. This step does not claim that `receipt_schema_invalid` is reachable from mutated canonical runtime bytes or live-reviewed.

- [ ] **Step 6: Commit the exact files**

```powershell
git add -- space/app.py space/carerisk_space/scenarios.py space/carerisk_space/ui.py space/tests/test_claim_contract.py space/tests/test_evidence_contract.py space/tests/test_scenario_contract.py space/tests/test_gradio_contract.py
git diff --cached --check
git commit -m 'feat(space): present bounded evidence explorer'
```

### Task 6: Enforce application import, capability, and existing-app exclusion

**Files:**
- Create: `tests/test_hf_space_source_boundary.py`
- Create: `space/tests/test_export_contract.py`
- Verify unchanged by Git object: `space/tests/test_gradio_contract.py`

The former Gradio test-source self-policing architecture and its test-only
`PublicSurfaceGuard` cleanup authorization are superseded. Task 6 must not modify
`space/tests/test_gradio_contract.py`. The target remains frozen as Git blob
`7c75d61c53eccdc93f69e7e3bb1eb09346eb5f04`, raw size `64847`, raw SHA-256
`101893daf6f20f9b507a00d0ac8da7fa383f83007520b4db61b710d1814df2a8`.
The expected tuple is supplied only through the controller's ignored task brief
and custody ledger. Tracked source and manifests contain no executable expected
tuple or fallback. Identity reads use `git cat-file blob`; checkout/text-mode
bytes are not authority. The detailed executable migration is governed by
`docs/superpowers/plans/2026-09-01-carerisk-gradio-contract-git-object-corrective.md`.

**Interfaces:**
- Consumes: Python AST for `space/app.py` and `space/carerisk_space/*.py`.
- Consumes: the controller-custodied tuple for the reviewed Gradio contract Git object.
- Produces: a hard application-source boundary plus an external Gradio-contract identity gate that later exporter and CI reuse.

- [ ] **Step 1: Write failing AST/import boundary tests**

```python
ALLOWED_IMPORT_ROOTS = {
    "__future__", "collections", "dataclasses", "hashlib", "html", "json", "logging",
    "math", "pathlib", "re", "stat", "types", "typing", "fastapi", "gradio", "starlette", "uvicorn",
    "carerisk_space",
}
FORBIDDEN_IMPORT_ROOTS = {
    "app", "carerisk48h", "joblib", "pickle", "cloudpickle", "dill",
    "numpy", "pandas", "scipy", "sklearn", "lightgbm", "shap", "torch",
    "tensorflow", "onnx", "matplotlib", "plotly", "requests", "httpx",
    "urllib", "huggingface_hub", "socket", "subprocess",
}

def test_application_import_graph_is_allowlisted() -> None:
    roots = imported_roots(APP_SOURCES)
    assert not roots & FORBIDDEN_IMPORT_ROOTS
    assert roots <= ALLOWED_IMPORT_ROOTS

def test_application_has_no_write_env_process_network_or_dynamic_code_capability() -> None:
    violations = scan_capabilities(APP_SOURCES)
    assert violations == []

def test_gradio_contract_git_object_matches_controller_custody() -> None:
    expected = _controller_gradio_contract_identity()
    object_id = _git_bytes(
        REPOSITORY_ROOT,
        "rev-parse",
        "HEAD:space/tests/test_gradio_contract.py",
    ).decode("ascii").strip()
    _assert_git_blob_identity(REPOSITORY_ROOT, object_id, expected)
```

`scan_capabilities` must identify write/append/update `open`, `Path.write_text`, `Path.write_bytes`, mkdir, rename, replace, delete, environment reads, `eval`, `exec`, dynamic import, process spawn, shell execution, network client construction, file watchers, and arbitrary absolute/current/home path discovery. The only additional filesystem-capability exception is in `ui.py`: read-only `pathlib` root resolution, `rglob`/iteration, `stat`/`is_file`/`is_dir`/`is_symlink`, `relative_to`, byte-size reads, and hash reads against the two fixed imported Gradio package roots. Calls accepting a runtime path argument, current/home/user/site discovery, `os.path`, globbing outside those roots, or any write remain forbidden.

`space/app.py` may import only `FastAPI`, pinned Gradio's mount API, `uvicorn`, and the two named local UI interfaces. `space/carerisk_space/ui.py` may import only Gradio `Blocks`/`HTML`, Starlette `ASGIApp`/`Scope`/`Receive`/`Send` type interfaces, and exactly `gradio.routes.BUILD_PATH_LIB`/`gradio.routes.STATIC_PATH_LIB` from framework code. Importing any other Gradio route/function/internal, Starlette `Middleware`, request/body parsing, response/file/static helpers, network clients, temporary-file APIs, background tasks, environment access, or filesystem writes is forbidden. Source and mutation tests prove the two roots are the only inputs, are resolved strictly, are non-symlink directories, and every accepted file is regular/non-symlink and passes strict resolved-root `Path.relative_to` containment. URL membership preserves the wheel's exact case and is compared case-sensitively, including on Windows where filesystem containment semantics alone are not a case proof. Missing roots, root/file/directory symlinks, request case aliases, special files, and escapes fail closed. The source test requires exactly one empty `FastAPI(docs_url=None, redoc_url=None, openapi_url=None)`, one `gr.mount_gradio_app` call with the full exact Task 5 mapping including `favicon_path=None`, direct `PublicSurfaceGuard(parent, build_package_asset_membership())` composition, and one fixed programmatic `uvicorn.run` under the main guard with exact `http="h11"`. It rejects `http="auto"`, `httptools`, an omitted parser argument, route decorators, `add_middleware`, `app_kwargs`, `Blocks.launch`, Gradio `Radio` or event binding, any second mount/router, and framework monkeypatching.

- [ ] **Step 2: Run RED**

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_source_boundary.py space/tests/test_export_contract.py -q
```

Expected: FAIL until the scanners and explicit source/export boundary are implemented.

The Task 6 application-source contract also inspects `PublicSurfaceGuard` and requires exactly two mandatory constructor parameters named `downstream` and `package_asset_urls`, with no default. It requires the constructor to reject an empty membership and the entry point to pass the pinned-root builder's exact nonempty result. A one-argument product call, optional default, or literal empty set fails the boundary test. Behavior of test-only helper construction sites is exercised by the frozen Gradio suite and direct source review; the boundary file does not interpret those sites.

The Gradio contract file itself is not interpreted by a candidate-controlled
meta-scanner. `tests/test_hf_space_source_boundary.py` must not contain
`_gradio_test_source_violations`, `_guard_helper_violations`, or successor
allowlists that attempt to model that test file's Python semantics. Its generic
identity helper validates controller custody, resolves the commit path object,
requires Git type `blob`, and compares SHA-1, `git cat-file -s`, raw byte length,
and SHA-256 over `git cat-file blob` output. Eight mutation categories are
written into a task-owned temporary Git object database and must all fail the
original tuple: same-length substitution, insertion, deletion, LF-to-CRLF,
UTF-8 BOM prefix, final-LF removal, appended comment, and appended NUL. A direct
reviewer separately inspects the exact raw object and its executable assertions;
hash identity alone is not a safety finding.

- [ ] **Step 3: Implement scanners and exact public path constants in the test contract**

```python
EXPECTED_PUBLIC_PATHS = (
    "README.md", "Dockerfile", "requirements.lock", "requirements-dev.lock",
    "app.py", "carerisk_space/__init__.py", "carerisk_space/contracts.py",
    "carerisk_space/evidence.py", "carerisk_space/scenarios.py",
    "carerisk_space/ui.py", "evidence/final-result-receipt.json",
    "evidence/release-v0.2.0.json", "deployment-manifest.json", "LICENSE",
    "NOTICE", "CITATION.cff", "SBOM.spdx.json", "THIRD_PARTY_LICENSES.json",
    "tests/test_claim_contract.py", "tests/test_evidence_contract.py",
    "tests/test_scenario_contract.py", "tests/test_gradio_contract.py",
    "tests/test_export_contract.py", "tests/test_container_contract.py",
)

def test_public_paths_are_exact_and_independently_repeated() -> None:
    assert PUBLIC_PATHS == EXPECTED_PUBLIC_PATHS
    assert len(PUBLIC_PATHS) == len(set(PUBLIC_PATHS)) == 24
```

Add explicit deny patterns from design Section 8.4, a 1 MiB limit, symlink/device/FIFO rejection, executable-binary signature rejection, and forbidden-content patterns for credentials/private keys. Tests must assert that `app/dashboard.py`, root `app.py`, `src/carerisk48h`, and the excluded PNG never appear in either path tuple.

Remove the retired Gradio test-source scanners, their solely supporting
constants/helpers, and their mutation tests while retaining the application
scanner, entry-point structural audit, guard-constructor audit, exporter/public
path checks, and all other product-boundary tests. No compatibility alias or
deprecated wrapper for either retired scanner remains.

- [ ] **Step 4: Run GREEN**

The Architecture C controller injects and validates the three custody values
exactly as specified by the successor corrective plan before this pytest run.

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_source_boundary.py space/tests/test_export_contract.py -q
```

Expected: all boundary tests pass without importing the existing application or model package.

- [ ] **Step 5: Commit the Architecture C corrective scope**

The already accepted `space/tests/test_export_contract.py` boundary is frozen
and is not restaged. The successor corrective plan governs the exact one-file
implementation commit:

```powershell
git add -- tests/test_hf_space_source_boundary.py
$staged = @(git diff --cached --name-only)
if ($staged.Count -ne 1 -or $staged[0] -cne 'tests/test_hf_space_source_boundary.py') { throw 'unexpected Task 6 corrective scope' }
git diff --cached --check
git commit -m 'test(space): replace source self-policing with Git object identity'
```

### Task 7: Build reproducible dependency, base-image, SBOM, and license workflows

**Task 7 release gate:** Do not start this task merely because the frozen hash
matches. The controller must first record all of the following in the ignored
custody ledgers: direct raw-object source review Critical `0`/Important `0`; the
exact object tuple above; Architecture C implementation review Spec ✅ and
Quality Approved with Critical `0`/Important `0`; fresh targeted, full
boundary/export, frozen Gradio, Ruff, strict Mypy, scope, and clean-tree gates;
the prior alias-evaluator and closed-world candidates remain explicitly
rejected/superseded; original Task 6 is complete via the accepted Architecture C
candidate; and one `Task 7 released` entry whose `CARERISK_TASK7_RELEASE_SHA`
value is a lowercase 40-hex commit supplied by the controller ledger and equals
the independently accepted Architecture C candidate. Task 7 preflight requires
`HEAD` to equal that ledger SHA, the worktree to be clean, and the Gradio path
object to equal the custodied blob.

**External custody transport for Tasks 7–13:** Before dispatching any later local
task whose command includes `tests/test_hf_space_source_boundary.py`, the
controller reads the exact accepted tuple from the ignored custody ledger and
injects these three process variables: `CARERISK_GRADIO_CONTRACT_BLOB_SHA1`,
`CARERISK_GRADIO_CONTRACT_RAW_SIZE`, and
`CARERISK_GRADIO_CONTRACT_RAW_SHA256`. The task must run the following preflight
in its own process before pytest; it may not reconstruct values from this plan,
tracked source, a manifest, or Git history:

```powershell
$custodyPatterns = @{
    CARERISK_GRADIO_CONTRACT_BLOB_SHA1 = '^[0-9a-f]{40}$'
    CARERISK_GRADIO_CONTRACT_RAW_SIZE = '^(0|[1-9][0-9]*)$'
    CARERISK_GRADIO_CONTRACT_RAW_SHA256 = '^[0-9a-f]{64}$'
}
foreach ($entry in $custodyPatterns.GetEnumerator()) {
    $value = [Environment]::GetEnvironmentVariable($entry.Key)
    if ([string]::IsNullOrWhiteSpace($value) -or $value -cnotmatch $entry.Value) {
        throw "missing or malformed external custody: $($entry.Key)"
    }
}
```

This block validates transport only; the boundary test performs the authoritative
path-object/type/size/raw-hash comparison. The controller reinjects custody for
each task/session rather than relying on inherited shell state.

**Files:**
- Create: `tools/space/requirements-runtime.in`
- Create: `tools/space/requirements-dev.in`
- Create: `tools/space/lock-tooling.txt`
- Create: `tools/space/base-image.json`
- Create: `tools/space/license-policy.json`
- Create: `scripts/build_hf_space_supply_chain.py`
- Create: `tests/test_hf_space_supply_chain.py`
- Create: `space/requirements.lock`
- Create: `space/requirements-dev.lock`
- Create: `space/SBOM.spdx.json`
- Create: `space/THIRD_PARTY_LICENSES.json`

**Interfaces:**
- Consumes: reviewed direct requirement inputs, the already measured and frozen lock/image records with their historic official-index/OCI provenance, the controller-created bounded source-reference metadata, and reviewed SPDX license policy. This corrective resume performs no package-index, wheel, registry, image, or browser acquisition.
- Produces: deterministic locks and public supply-chain files plus `verify_all(repo_root: Path, *, source_reference: WebKitSourceReference, offline: Literal[True], network_bomb: Literal[True]) -> None`.

- [ ] **Step 0: Start the one controller-owned source-reference session before any Task 7 RED/test**

Run this controller-owned PowerShell procedure once in the session that will execute every later Task 7 command. It is intentionally before Step 1/RED and does not call product code or a future `scripts/build_hf_space_supply_chain.py` command. The actual lock and image measured partials already exist as frozen custody inputs: this correction must not re-resolve/reselect them or repeat any earlier controlled dependency/wheel acquisition. The only newly authorized network action in this resume is one normal-TLS HTTPS GET of the literal commit-pinned raw-source URL below. The response exists only as a transient raw file under this run's exact OS-temp child; after raw-byte validation, only bounded parsed metadata/evidence remains in `$sourceRef`.

```powershell
$toolVenv = '.venv-space-lock'
$task7Guid = [guid]::NewGuid().ToString('N')
$sourceUrl = 'https://raw.githubusercontent.com/microsoft/playwright/e3950d9c140d007bd52853b45813c6274b24e36f/browser_patches/webkit/UPSTREAM_CONFIG.sh'
$task7OsTempItem = Get-Item -LiteralPath ([IO.Path]::GetFullPath([IO.Path]::GetTempPath())) -Force -ErrorAction Stop
if (-not $task7OsTempItem.PSIsContainer -or ($task7OsTempItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'OS temp root is not an exact regular directory' }
$task7OsTempRoot = [IO.Path]::GetFullPath($task7OsTempItem.FullName)
$task7TempRoot = Join-Path $task7OsTempRoot "carerisk-task7-$task7Guid"
$sourceRaw = Join-Path $task7TempRoot 'webkit-upstream-config.raw'
$sourceRef = Join-Path $task7TempRoot 'webkit-source-reference.json'
if (([IO.Path]::GetFileName($task7TempRoot) -cne "carerisk-task7-$task7Guid") -or ([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($task7TempRoot)) -cne $task7OsTempRoot) -or [IO.Path]::GetFullPath($task7TempRoot).Equals($task7OsTempRoot, [StringComparison]::Ordinal)) { throw 'Task 7 temp root is not an owned OS-temp child' }

function Resolve-Task7OwnedCleanupTarget {
    param(
        [Parameter(Mandatory)][string]$CandidateRoot,
        [Parameter(Mandatory)][string]$VerifiedOsTempRoot,
        [Parameter(Mandatory)][string]$RunGuid,
        [Parameter(Mandatory)][string[]]$AllowedChildNames,
        [Parameter(Mandatory)][string[]]$RequiredChildNames
    )
    if ($RunGuid -cnotmatch '^[0-9a-f]{32}$') { throw 'Task 7 cleanup GUID is invalid' }
    $osTemp = Get-Item -LiteralPath $VerifiedOsTempRoot -Force -ErrorAction Stop
    $candidate = Get-Item -LiteralPath $CandidateRoot -Force -ErrorAction Stop
    if (-not $osTemp.PSIsContainer -or -not $candidate.PSIsContainer -or ($osTemp.Attributes -band [IO.FileAttributes]::ReparsePoint) -or ($candidate.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Task 7 cleanup root is not a regular directory' }
    $resolvedOsTemp = [IO.Path]::GetFullPath($osTemp.FullName)
    $resolvedCandidate = [IO.Path]::GetFullPath($candidate.FullName)
    if ($resolvedCandidate.Equals($resolvedOsTemp, [StringComparison]::Ordinal) -or ([IO.Path]::GetDirectoryName($resolvedCandidate) -cne $resolvedOsTemp) -or ([IO.Path]::GetFileName($resolvedCandidate) -cne "carerisk-task7-$RunGuid")) { throw 'Task 7 cleanup target is outside the exact owned OS-temp child' }
    $children = @(Get-ChildItem -LiteralPath $resolvedCandidate -Force -ErrorAction Stop)
    foreach ($child in $children) {
        if ($child.PSIsContainer -or ($child.Attributes -band [IO.FileAttributes]::ReparsePoint) -or ($AllowedChildNames -cnotcontains $child.Name) -or ([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($child.FullName)) -cne $resolvedCandidate)) { throw 'Task 7 cleanup child identity is ambiguous' }
    }
    foreach ($required in $RequiredChildNames) {
        if (@($children.Name) -cnotcontains $required) { throw 'Task 7 cleanup required child is missing' }
    }
    return $resolvedCandidate
}

New-Item -ItemType Directory -LiteralPath $task7TempRoot -ErrorAction Stop | Out-Null
[void](Resolve-Task7OwnedCleanupTarget -CandidateRoot $task7TempRoot -VerifiedOsTempRoot $task7OsTempRoot -RunGuid $task7Guid -AllowedChildNames @() -RequiredChildNames @())
try {
    $handler = [Net.Http.HttpClientHandler]::new()
    $handler.AllowAutoRedirect = $false
    $client = [Net.Http.HttpClient]::new($handler)
    $client.Timeout = [TimeSpan]::FromSeconds(30)
    $request = [Net.Http.HttpRequestMessage]::new([Net.Http.HttpMethod]::Get, [Uri]$sourceUrl)
    try {
        $response = $client.SendAsync($request).GetAwaiter().GetResult()
        if ([int]$response.StatusCode -ne 200) { throw 'Pinned upstream source GET did not return HTTP 200' }
        $rawBytes = $response.Content.ReadAsByteArrayAsync().GetAwaiter().GetResult()
    } finally {
        if ($null -ne $response) { $response.Dispose() }
        $request.Dispose()
        $client.Dispose()
        $handler.Dispose()
    }
    $rawStream = [IO.FileStream]::new($sourceRaw, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $rawStream.Write($rawBytes, 0, $rawBytes.Length) } finally { $rawStream.Dispose() }
    if ($rawBytes.Length -ne 126) { throw 'Pinned upstream source length drift' }
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $rawHash = -join ($sha.ComputeHash($rawBytes) | ForEach-Object { $_.ToString('x2') }) } finally { $sha.Dispose() }
    if ($rawHash -cne '3554c5b666ed87032fb22e78956f8a2fffe1faede63ae8dcae60a26961f6419c') { throw 'Pinned upstream source hash drift' }
    $sourceText = [Text.UTF8Encoding]::new($false, $true).GetString($rawBytes)
    function Read-ExactUpstreamAssignment([string]$Name) {
        $matches = [regex]::Matches($sourceText, ('(?m)^{0}="([^"\r\n]+)"$' -f [regex]::Escape($Name)))
        if ($matches.Count -ne 1) { throw "Pinned upstream assignment drift: $Name" }
        return $matches[0].Groups[1].Value
    }
    $remoteUrl = Read-ExactUpstreamAssignment 'REMOTE_URL'
    $baseBranch = Read-ExactUpstreamAssignment 'BASE_BRANCH'
    $baseRevision = Read-ExactUpstreamAssignment 'BASE_REVISION'
    if ($remoteUrl -cne 'https://github.com/WebKit/WebKit.git' -or $baseBranch -cne 'main' -or $baseRevision -cne '343e13bf22dca9d0ec227801419aab0f9001a32f') { throw 'Pinned upstream assignments drift' }
    $ownedRoot = Resolve-Task7OwnedCleanupTarget -CandidateRoot $task7TempRoot -VerifiedOsTempRoot $task7OsTempRoot -RunGuid $task7Guid -AllowedChildNames @('webkit-upstream-config.raw', 'webkit-source-reference.json') -RequiredChildNames @('webkit-upstream-config.raw')
    Remove-Item -LiteralPath $sourceRaw -Force -ErrorAction Stop
    $sourceMetadata = [ordered]@{
        schema_version = 1; run_guid = $task7Guid; phase = 'controller_controlled_acquisition_complete'
        network_permission = 'exact_commit_pinned_https_get_once'; https_get_count = 1; raw_body_retained = $false
        playwright_tag = 'v1.62.0'; playwright_tag_commit = 'e3950d9c140d007bd52853b45813c6274b24e36f'
        repository_relative_path = 'browser_patches/webkit/UPSTREAM_CONFIG.sh'; commit_pinned_raw_url = $sourceUrl
        raw_byte_length = 126; raw_sha256 = $rawHash; remote_url = $remoteUrl; base_branch = $baseBranch; base_revision = $baseRevision
    }
    $sourceJson = $sourceMetadata | ConvertTo-Json -Compress -Depth 3
    $metadataBytes = [Text.UTF8Encoding]::new($false).GetBytes($sourceJson + "`n")
    $metadataStream = [IO.FileStream]::new($sourceRef, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $metadataStream.Write($metadataBytes, 0, $metadataBytes.Length) } finally { $metadataStream.Dispose() }
    [void](Resolve-Task7OwnedCleanupTarget -CandidateRoot $task7TempRoot -VerifiedOsTempRoot $task7OsTempRoot -RunGuid $task7Guid -AllowedChildNames @('webkit-source-reference.json') -RequiredChildNames @('webkit-source-reference.json'))
} catch {
    $acquisitionError = $_
    try {
        $ownedRoot = Resolve-Task7OwnedCleanupTarget -CandidateRoot $task7TempRoot -VerifiedOsTempRoot $task7OsTempRoot -RunGuid $task7Guid -AllowedChildNames @('webkit-upstream-config.raw', 'webkit-source-reference.json') -RequiredChildNames @()
        Remove-Item -LiteralPath $ownedRoot -Recurse -Force -ErrorAction Stop
    } catch {
        throw "Task 7 acquisition failed and ambiguous cleanup target was retained: $($_.Exception.Message)"
    }
    throw $acquisitionError
}
```

This inline controller procedure is the complete network-acquisition owner. It uses platform TLS validation, disables redirects, sends exactly one GET, accepts only HTTP 200 from the exact URL, validates raw length/hash and the three quoted assignments, removes the transient raw file, and writes only bounded metadata/evidence to `$sourceRef`. There is no generator acquisition subcommand. Before Task 1, run controller lifecycle probes that mutate the URL, HTTP status/redirect, request count, length, hash, each assignment, output root, metadata name, run GUID, phase, network-permission value, and retained-raw flag; every mutation must fail closed. Run cleanup probes for root-as-candidate, sibling/outside/prefix-collision candidate, wrong GUID-derived name, OS-temp or candidate reparse point, symlink/reparse/unknown/directory child, missing phase-required child, and extra child. Both the acquisition catch path and the later success finalizer must call the same `Resolve-Task7OwnedCleanupTarget`; any ambiguity retains the target untouched. Keep the live session and exact `$sourceRef` through the later offline commands. Never stage, copy, export, upload, or serialize its path, raw body, or run GUID into a distributed receipt.

- [ ] **Step 1: Write failing lock/base/inventory tests**

```python
def test_locks_are_complete_exact_and_hashed() -> None:
    for path in (RUNTIME_LOCK, DEVELOPMENT_LOCK):
        entries = parse_hash_lock(path.read_text(encoding="utf-8"))
        assert entries
        assert all(entry.version_operator == "==" for entry in entries)
        assert all(entry.sha256_hashes for entry in entries)
        assert not any(entry.editable or entry.url_without_hash for entry in entries)
    runtime = normalized_package_versions(RUNTIME_LOCK)
    development = normalized_package_versions(DEVELOPMENT_LOCK)
    assert runtime <= development
    assert direct_pin(RUNTIME_INPUT, "gradio") == "6.26.0"
    assert direct_pin(DEVELOPMENT_INPUT, "gradio") == "6.26.0"
    assert ("gradio", "6.26.0") in runtime
    assert ("gradio", "6.26.0") in development

def test_both_base_images_are_patch_tagged_digest_pinned_and_compatible() -> None:
    bases = json.loads(BASE_IMAGE.read_text(encoding="utf-8"))["images"]
    runtime, reviewer = bases["runtime"], bases["reviewer"]
    assert re.fullmatch(r"python:3\.11\.\d+-slim-bookworm", runtime["tag"])
    assert re.fullmatch(r"mcr\.microsoft\.com/playwright/python:v\d+\.\d+\.\d+-(jammy|noble)", reviewer["tag"])
    assert reviewer["playwright_python_version"] == direct_pin(
        DEVELOPMENT_INPUT, "playwright"
    )
    assert set(reviewer["embedded_browsers"]) == {"chromium", "firefox", "webkit"}
    for base in (runtime, reviewer):
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", base["index_digest"])
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", base["linux_amd64_digest"])
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", base["system_inventory_sha256"])

def test_sbom_and_license_inventory_cover_every_lock_package_once() -> None:
    locked = normalized_locked_packages(RUNTIME_LOCK, DEVELOPMENT_LOCK)
    image_components = {
        "carerisk-space", "python-runtime-base", "playwright-reviewer-base",
        "chromium", "firefox", "webkit", "ffmpeg",
    }
    assert sbom_package_keys(SBOM) == locked | image_components
    assert license_inventory_keys(LICENSES) == locked | (image_components - {"carerisk-space"})
    records = {item["package"]: item for item in load_licenses(LICENSES)}
    assert records["webkit"] == exact_webkit_reviewer_policy_record()
    assert records["webkit"]["licenseDeclared"] == "NOASSERTION"
    assert records["webkit"]["licenseConcluded"] == "NOASSERTION"
    assert records["webkit"]["review_disposition"] == "reviewer_test_only_not_redistributed"
    assert records["webkit"]["complete_digest_bound_notice"] is False
    assert all(
        item["review_disposition"] == "approved"
        and item["licenseDeclared"] != "NOASSERTION"
        and item["licenseConcluded"] != "NOASSERTION"
        for name, item in records.items()
        if name != "webkit"
    )

@pytest.mark.parametrize(
    "field",
    [
        "reviewer_image_tag", "reviewer_index_digest", "reviewer_linux_amd64_digest",
        "playwright_version", "playwright_tag", "playwright_tag_url", "browsers_json_url",
        "registry_source_url", "cdn_artifact_url", "playwright_tag_commit",
        "repository_relative_path", "commit_pinned_raw_url", "raw_byte_length",
        "raw_sha256", "remote_url", "base_branch", "base_revision", "webkit_revision", "webkit_version",
        "webkit_tree_file_count", "webkit_tree_total_bytes", "webkit_tree_algorithm", "webkit_tree_sha256", "image_tree_source_relative_path_absence_proof", "official_webkit_licensing_references",
        "licenseDeclared", "licenseConcluded", "review_disposition",
        "complete_digest_bound_notice",
    ],
)
def test_exact_webkit_reviewer_exception_rejects_every_single_field_drift(field: str) -> None:
    mutated = mutate_exact_webkit_policy(field)
    with pytest.raises(ValueError, match="WebKit reviewer exception drift"):
        validate_license_policy(mutated)

def test_noassertion_fails_for_public_or_any_other_component() -> None:
    for component in ("python-runtime-base", "gradio", "chromium", "firefox", "ffmpeg"):
        with pytest.raises(ValueError, match="NOASSERTION outside exact reviewer-only WebKit"):
            validate_license_policy(policy_with_noassertion(component))

@pytest.mark.parametrize(
    "surface",
    [
        "public_export", "candidate", "runtime_stage", "final_image",
        "deployment_artifact", "saved_archive", "pushed_image",
        "uploaded_artifact", "published_image", "build_output",
        "other_distributed_output",
    ],
)
def test_reviewer_or_browser_bytes_fail_every_distribution_surface(surface: str) -> None:
    with pytest.raises(ValueError, match="reviewer bytes reached distributed surface"):
        validate_distribution_exclusion(distribution_fixture(surface, "webkit-2336"))

@pytest.mark.parametrize("mutation", ["missing", "duplicate", "unknown", "empty", "unclassified"])
def test_distribution_surface_registry_is_closed_and_complete(mutation: str) -> None:
    with pytest.raises(ValueError, match="distribution surface registry is not exact"):
        validate_distribution_exclusion(mutated_surface_registry(mutation))

@pytest.mark.parametrize("mutation", [
    "source_reference_missing", "source_reference_alternate", "run_guid_missing",
    "run_guid_wrong", "phase_missing", "phase_wrong", "offline_missing",
    "offline_false", "network_bomb_missing", "network_bomb_false",
    "metadata_network_permission_missing", "metadata_network_permission_wrong",
    "metadata_https_get_count_wrong", "metadata_raw_body_retained_true",
])
def test_source_reference_phase_contract_rejects_every_control_mutation(mutation: str) -> None:
    with pytest.raises(ValueError, match="source reference phase contract"):
        run_or_parse_mutated_source_reference_phase(mutation)

def test_offline_test_installs_network_bomb_before_argv() -> None:
    events: list[str] = []
    assert run_network_bombed_child(
        source_reference=SOURCE_REFERENCE_PATH, run_guid=RUN_GUID,
        phase="offline_verify", offline=True, network_bomb=True,
        argv=("pytest", "-q"), event_sink=events.append,
    ) == 0
    assert events == ["load_reference", "install_network_bomb", "spawn_child"]
```

- [ ] **Step 2: Run RED**

```powershell
& "$toolVenv\Scripts\python.exe" scripts/build_hf_space_supply_chain.py offline-test --source-reference $sourceRef --run-guid $task7Guid --phase offline-verify --offline --network-bomb -- .venv-space\Scripts\python.exe -m pytest tests/test_hf_space_supply_chain.py -q
```

Expected: FAIL because inputs, generator, locks, base record, SBOM, and license inventory do not exist.

- [ ] **Step 3: Implement deterministic supply-chain commands**

```python
@dataclass(frozen=True)
class WebKitSourceReference:
    playwright_tag_commit: str
    repository_relative_path: str
    commit_pinned_raw_url: str
    raw_byte_length: int
    raw_sha256: str
    remote_url: str
    base_branch: str
    base_revision: str

def load_webkit_source_reference(path: Path, *, run_guid: str, phase: Literal["offline_verify"], offline: Literal[True], network_bomb: Literal[True]) -> WebKitSourceReference: ...
def verify_image_record(path: Path, *, source_reference: WebKitSourceReference, offline: Literal[True], network_bomb: Literal[True]) -> None: ...
def verify_existing_locks(runtime_lock: Path, development_lock: Path, *, source_reference: WebKitSourceReference, offline: Literal[True], network_bomb: Literal[True]) -> None: ...
def build_inventory_and_sbom(args: argparse.Namespace, *, source_reference: WebKitSourceReference, offline: Literal[True], network_bomb: Literal[True]) -> None: ...
def verify_all(repo_root: Path, *, source_reference: WebKitSourceReference, offline: Literal[True], network_bomb: Literal[True]) -> None: ...
def emit_bounded_lifecycle_event(event: str) -> None: ...
def run_network_bombed_child(*, source_reference: Path, run_guid: str, phase: Literal["offline_verify"], offline: Literal[True], network_bomb: Literal[True], argv: Sequence[str], event_sink: Callable[[str], None]) -> int: ...

def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "verify-images":
        source_reference = load_webkit_source_reference(Path(args.source_reference), run_guid=args.run_guid, phase=require_offline_phase(args.phase), offline=require_literal_true(args.offline), network_bomb=require_literal_true(args.network_bomb))
        install_network_bomb_before_work_or_child(args, offline=require_literal_true(args.offline), network_bomb=require_literal_true(args.network_bomb))
        verify_image_record(Path(args.input), source_reference=source_reference, offline=True, network_bomb=True)
        return 0
    if args.command == "lock":
        return build_locks(args)
    if args.command == "verify-locks":
        source_reference = load_webkit_source_reference(Path(args.source_reference), run_guid=args.run_guid, phase=require_offline_phase(args.phase), offline=require_literal_true(args.offline), network_bomb=require_literal_true(args.network_bomb))
        install_network_bomb_before_work_or_child(args, offline=require_literal_true(args.offline), network_bomb=require_literal_true(args.network_bomb))
        verify_existing_locks(Path(args.runtime_lock), Path(args.development_lock), source_reference=source_reference, offline=True, network_bomb=True)
        return 0
    if args.command == "inventory":
        source_reference = load_webkit_source_reference(Path(args.source_reference), run_guid=args.run_guid, phase=require_offline_phase(args.phase), offline=require_literal_true(args.offline), network_bomb=require_literal_true(args.network_bomb))
        install_network_bomb_before_work_or_child(args, offline=require_literal_true(args.offline), network_bomb=require_literal_true(args.network_bomb))
        build_inventory_and_sbom(args, source_reference=source_reference, offline=True, network_bomb=True)
        return 0
    if args.command == "verify":
        source_reference = load_webkit_source_reference(Path(args.source_reference), run_guid=args.run_guid, phase=require_offline_phase(args.phase), offline=require_literal_true(args.offline), network_bomb=require_literal_true(args.network_bomb))
        install_network_bomb_before_work_or_child(args, offline=require_literal_true(args.offline), network_bomb=require_literal_true(args.network_bomb))
        verify_all(Path(args.repo_root), source_reference=source_reference, offline=True, network_bomb=True)
        return 0
    if args.command == "offline-test":
        return run_network_bombed_child(source_reference=Path(args.source_reference), run_guid=args.run_guid, phase=require_offline_phase(args.phase), offline=require_literal_true(args.offline), network_bomb=require_literal_true(args.network_bomb), argv=args.child_command, event_sink=emit_bounded_lifecycle_event)
    raise AssertionError("unreachable")
```

There is no product/generator network-acquisition command. Step 0 creates the bounded controller metadata before this implementation exists. `load_webkit_source_reference` requires the exact live GUID-child path, matching GUID, literal `phase="offline_verify"`, `offline=True`, and `network_bomb=True`; it rejects a missing/alternate source path, GUID, phase, flag, controller acquisition phase, network-permission value, request count, or retained-raw status before producing `WebKitSourceReference`. Each CLI subcommand requires `--source-reference $sourceRef --run-guid $task7Guid --phase offline-verify --offline --network-bomb`, then installs the network bomb before any in-process verifier/inventory work or child/pytest `argv`. `run_network_bombed_child` has no optional/default control arguments; direct tests pass `event_sink=events.append`, while `main() -> int` passes the declared bounded event function and returns only an integer status. `verify-images` is read-only: it validates the existing measured `base-image.json` against the frozen runtime/reviewer tag, OCI index digest, linux/amd64 manifest digest, Python target, system-package inventory digest, source registry, browser/support revision/version/tree identity, and exact WebKit provenance contract. The current Task 7 correction may extend that measured record only with the exact WebKit version/provenance fields; it must not run `resolve-images`, query for a replacement, overwrite the record from a registry response, or select another tag/platform. A legitimate future image re-resolution is outside this plan and requires a separately approved design/policy tuple, fresh measurement and license review, updated mutations, and a new custody baseline.

`lock` is the separately authorized historic controlled dependency/wheel acquisition interface: it emits `requirements.lock` as the complete runtime closure for the runtime Linux/Python target and `requirements-dev.lock` as the complete runtime-plus-development union closure for the reviewer Linux/Python target. The normalized package/version pairs from the runtime lock must be an unchanged subset of the development lock. Each lock was installed alone with `--require-hashes --no-deps`; its prior controlled acquisition filled a temporary wheelhouse with accepted hashes, then a separate no-egress `--no-index` step verified installation. Do not describe that historic dependency acquisition as offline, and do not re-run it in this Task 7 corrective resume. This resume invokes only `verify-locks` with `$sourceRef --offline --network-bomb`, which validates the frozen existing lock bytes and installs the bomb before inspection.

`inventory` requires the acquired `$sourceRef` and explicit offline/network-bomb flags. It extracts metadata and notices from exact accepted wheels and both exact image manifests/inventories, includes the reviewer image's embedded browser revisions/versions/system packages, joins every component to `license-policy.json`, and serializes sorted canonical JSON with a final newline. Ordinary records must be approved with concluded redistribution-compatible expressions. One separate validator recognizes only the exact WebKit reviewer tuple and emits the metadata-only exception; it may not share a permissive `NOASSERTION` branch with ordinary components. `SBOM.spdx.json` and `THIRD_PARTY_LICENSES.json` cover both base-image inventories and browser identities, but the final runtime and every distributed byte set still contain only approved runtime bytes.

The exact WebKit record is version `26.5`, revision `2336`, tree algorithm `sha256-canonical-tree-v1`, tree SHA-256 `c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c`, and is bound to reviewer tag/index/manifest `mcr.microsoft.com/playwright/python:v1.62.0-noble` / `sha256:aa81288e738725378becba5b3e06cb0f3a7f012a610e87e8d767a090ea3f740d` / `sha256:51d31fdfacb0cff99a1a724152e34ae408d2bd4e7da310ff157450f49261cc59`. It records Playwright `1.62.0`, tag `v1.62.0`, official tag URL `https://github.com/microsoft/playwright/tree/v1.62.0`, the official tagged `browsers.json` and registry source, and the resolved official CDN artifact. Its separate source-reference fields are `playwright_tag_commit=e3950d9c140d007bd52853b45813c6274b24e36f`, `repository_relative_path=browser_patches/webkit/UPSTREAM_CONFIG.sh`, `commit_pinned_raw_url=https://raw.githubusercontent.com/microsoft/playwright/e3950d9c140d007bd52853b45813c6274b24e36f/browser_patches/webkit/UPSTREAM_CONFIG.sh`, `raw_byte_length=126`, `raw_sha256=3554c5b666ed87032fb22e78956f8a2fffe1faede63ae8dcae60a26961f6419c`, parsed `remote_url=https://github.com/WebKit/WebKit.git`, `base_branch=main`, and `base_revision=343e13bf22dca9d0ec227801419aab0f9001a32f`; the immutable 38-file tree must derive `image_tree_source_relative_path_absence_proof` with the same relative path, canonical algorithm/count/bytes/digest, and `present=false` from its ordered inventory rather than trusting an input flag. It records the exact official WebKit licensing-reference set from design Section 10.1. Its SPDX declared and concluded values are exactly `NOASSERTION`, its `review_disposition` is exactly `reviewer_test_only_not_redistributed`, and `complete_digest_bound_notice` is exactly false. This source reference proves only that Playwright `v1.62.0` source configuration declares the WebKit base revision; it does not claim the source file is in the binary image, bitwise source/binary attestation, complete notice, redistribution approval, or a guessed expression.

The strict `WebKitReviewerPolicy` types `webkit_tree_file_count: int` exactly `38` and `webkit_tree_total_bytes: int` exactly `306401261`. It types `image_tree_source_relative_path_absence_proof: Mapping[str, object]` as the inventory-derived object `{repository_relative_path, canonical_tree_algorithm, canonical_tree_file_count, canonical_tree_total_bytes, canonical_tree_sha256, present}` with exact values `browser_patches/webkit/UPSTREAM_CONFIG.sh`, `sha256-canonical-tree-v1`, `38`, `306401261`, `c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c`, and `false`. Strict validation recomputes this complete object from the canonical ordered image-tree inventory before fixture/key equality; a supplied boolean or map is not proof.

`verify_all` also consumes the exact closed eleven-member distribution-surface description and rejects reviewer/WebKit/browser bytes in every member. It first rejects an omitted, duplicate, unknown, empty, or unclassified surface. Until Task 8/9/11/13 provide their concrete manifests and image inspections, Task 7 tests use synthetic fixtures for all eleven; the downstream tasks replace those fixtures with authoritative exporter/workflow/image evidence without weakening this pure fail-closed validator. Chromium, Firefox, ffmpeg, operating-system/base-image records, and Python packages remain approved-only.

The direct runtime input contains only `gradio==6.26.0`; a candidate range such as a broad major-version interval is forbidden. The direct development input contains the same exact Gradio pin plus pytest, Ruff, Mypy, PyYAML, packaging, the exact Playwright Python pin matching the reviewer image, accessibility tooling, lock verification, vulnerability scanning, and license/SBOM verification tools. The development lock remains the complete runtime-plus-development union closure, and contract tests verify the installed Gradio version as well as the exact direct pin and equal runtime/development lock entries. It does not rely on Playwright wheels to supply browsers or Debian packages, and Dockerfile generation must not run `playwright install` or `apt-get install` in the reviewer stage. Product code still imports only Gradio, standard library, and local modules.

- [ ] **Step 4: Verify the frozen measured pins and review the exact policy extension**

```powershell
$task7Succeeded = $false
try {
& "$toolVenv\Scripts\python.exe" scripts/build_hf_space_supply_chain.py verify-images --input tools/space/base-image.json --source-reference $sourceRef --run-guid $task7Guid --phase offline-verify --offline --network-bomb
& "$toolVenv\Scripts\python.exe" scripts/build_hf_space_supply_chain.py verify-locks --runtime-lock space/requirements.lock --development-lock space/requirements-dev.lock --source-reference $sourceRef --run-guid $task7Guid --phase offline-verify --offline --network-bomb
& "$toolVenv\Scripts\python.exe" scripts/build_hf_space_supply_chain.py inventory --base tools/space/base-image.json --runtime-lock space/requirements.lock --development-lock space/requirements-dev.lock --license-policy tools/space/license-policy.json --source-reference $sourceRef --run-guid $task7Guid --phase offline-verify --licenses-output space/THIRD_PARTY_LICENSES.json --sbom-output space/SBOM.spdx.json --offline --network-bomb
& "$toolVenv\Scripts\python.exe" scripts/build_hf_space_supply_chain.py verify --repo-root . --source-reference $sourceRef --run-guid $task7Guid --phase offline-verify --offline --network-bomb
& "$toolVenv\Scripts\python.exe" scripts/build_hf_space_supply_chain.py offline-test --source-reference $sourceRef --run-guid $task7Guid --phase offline-verify --offline --network-bomb -- .venv-space\Scripts\python.exe -m pytest tests/test_hf_space_supply_chain.py -q
$trackedOutputs = @('space/requirements.lock', 'space/requirements-dev.lock', 'space/SBOM.spdx.json', 'space/THIRD_PARTY_LICENSES.json')
$first = @($trackedOutputs | ForEach-Object { $item = Get-FileHash -Algorithm SHA256 -LiteralPath $_; '{0}|{1}' -f $_, $item.Hash.ToLowerInvariant() })
& "$toolVenv\Scripts\python.exe" scripts/build_hf_space_supply_chain.py inventory --base tools/space/base-image.json --runtime-lock space/requirements.lock --development-lock space/requirements-dev.lock --license-policy tools/space/license-policy.json --source-reference $sourceRef --run-guid $task7Guid --phase offline-verify --licenses-output space/THIRD_PARTY_LICENSES.json --sbom-output space/SBOM.spdx.json --offline --network-bomb
$second = @($trackedOutputs | ForEach-Object { $item = Get-FileHash -Algorithm SHA256 -LiteralPath $_; '{0}|{1}' -f $_, $item.Hash.ToLowerInvariant() })
if ([string]::Join("`n", $first) -cne [string]::Join("`n", $second)) { throw 'Supply-chain outputs are not reproducible' }
$task7Succeeded = $true
} finally {
    if ($task7Succeeded) {
        $ownedRoot = Resolve-Task7OwnedCleanupTarget -CandidateRoot $task7TempRoot -VerifiedOsTempRoot $task7OsTempRoot -RunGuid $task7Guid -AllowedChildNames @('webkit-source-reference.json') -RequiredChildNames @('webkit-source-reference.json')
        Remove-Item -LiteralPath $ownedRoot -Recurse -Force -ErrorAction Stop
    } else { Write-Error "Task 7 failed; retain bounded GUID-owned parsed metadata at $task7TempRoot for diagnosis. Never stage, copy, export, or upload it." }
}
```

Expected: the Step 0 controller acquisition is the sole network-enabled Task 7 provenance action. This correction performs no dependency-lock re-acquisition, no image re-resolution, and no overwrite/reselection of `base-image.json`; `verify-locks` and `verify-images` accept only frozen measured custody inputs plus the exact added provenance/version fields. Every later `verify-images`, `verify-locks`, both deterministic `inventory` runs, `verify`, and pytest uses the exact `$sourceRef --run-guid $task7Guid --phase offline-verify --offline --network-bomb` contract; its runner installs the bomb before any work or child process, and no later command may fetch or refetch. The success finalizer invokes the same ownership validator as Task 0 catch and removes only the validated current GUID root; a missing/extra/ambiguous child, wrong identity, or reparse/symlink condition leaves it untouched. On verification failure the bounded owned metadata remains for diagnosis and is never staged, copied, exported, or uploaded. The eleven sanctioned Task 7 tracked paths remain the only tracked outputs; only parsed canonical metadata needed downstream appears in their policy/inventory records. Review package source URLs, both base-image inventories, embedded-browser revisions/versions, typed tree count/size/algorithm/identity and derived source-relative-file absence, official Playwright tag URL/registry/CDN, exact external source-reference provenance, license texts/references, notices, notice completeness, all eleven distribution surfaces, and dispositions before proceeding. Unknown, missing, incompatible, or non-redistributable components whose bytes could be exported/deployed stop the task.

- [ ] **Step 5: Run reproducibility and installation GREEN**

The reproducibility commands are intentionally inside Step 4's live `try` block so both inventory runs consume the same verified `$sourceRef` before the ownership-safe finalizer runs. Expected: verify and tests pass, regeneration is byte-for-byte stable, every ordinary component is approved-only, the exact WebKit record preserves both SPDX `NOASSERTION` fields plus `reviewer_test_only_not_redistributed` and `complete_digest_bound_notice=false`, and every named distribution-surface mutation is rejected.

- [ ] **Step 6: Commit every source and generated supply-chain file explicitly**

```powershell
git add -- tools/space/requirements-runtime.in tools/space/requirements-dev.in tools/space/lock-tooling.txt tools/space/base-image.json tools/space/license-policy.json scripts/build_hf_space_supply_chain.py tests/test_hf_space_supply_chain.py space/requirements.lock space/requirements-dev.lock space/SBOM.spdx.json space/THIRD_PARTY_LICENSES.json
git diff --cached --check
git commit -m 'build(space): lock runtime supply chain'
```

### Task 8: Implement the clean Git-object exporter and exact path mapping

**Files:**
- Create: `scripts/export_hf_space.py`
- Create: `tests/test_hf_space_exporter.py`
- Modify: `space/tests/test_export_contract.py`

**Interfaces:**
- Consumes: clean repository, exact app-source SHA, exact manifest-source SHA, and fresh destination.
- Produces: canonical deployment-manifest bytes, clean export bytes, and `ExportReceipt`.

- [ ] **Step 1: Write failing exporter tests**

```python
def test_export_reads_committed_blobs_and_matches_exact_allowlist(tmp_path: Path, git_repo: Path) -> None:
    receipt = export_space(
        repo_root=git_repo,
        app_source_sha=APP_SOURCE_SHA,
        manifest_source_sha=MANIFEST_SOURCE_SHA,
        destination=tmp_path / "candidate",
    )
    assert tuple(item.path for item in receipt.files) == PUBLIC_PATHS
    assert not (receipt.destination / ".git").exists()

@pytest.mark.parametrize(
    "case",
    ["dirty_source", "nonempty_destination", "symlink", "extra_path", "large_file",
     "secret_signature", "binary_signature", "path_traversal", "wrong_tag_commit"],
)
def test_export_rejects_unsafe_source_or_destination(case: str, exporter_case: ExporterCase) -> None:
    with pytest.raises(ExportError, match=case):
        exporter_case.run(case)

def test_manifest_is_non_self_referential(git_repo: Path) -> None:
    manifest = json.loads(git_show(git_repo, MANIFEST_SOURCE_SHA, "space/deployment-manifest.json"))
    assert manifest["space_app_source_git_sha"] == APP_SOURCE_SHA
    assert MANIFEST_SOURCE_SHA != APP_SOURCE_SHA
    assert is_ancestor(git_repo, APP_SOURCE_SHA, MANIFEST_SOURCE_SHA)
    assert "destination_commit" not in manifest
    assert manifest_entry(manifest, "deployment-manifest.json").get("sha256") is None

def test_export_contains_webkit_policy_metadata_but_no_reviewer_or_browser_bytes(
    tmp_path: Path, git_repo: Path
) -> None:
    receipt = export_space(
        repo_root=git_repo,
        app_source_sha=APP_SOURCE_SHA,
        manifest_source_sha=MANIFEST_SOURCE_SHA,
        destination=tmp_path / "candidate",
    )
    assert_exact_webkit_metadata_only(receipt.destination)
    assert_no_reviewer_or_browser_bytes(receipt.destination)

@pytest.mark.parametrize("token", REVIEWER_BROWSER_BYTE_SIGNATURES)
def test_export_rejects_reviewer_or_browser_byte_signatures(
    token: bytes, exporter_case: ExporterCase
) -> None:
    with pytest.raises(ExportError, match="reviewer bytes reached public export"):
        exporter_case.run_with_added_bytes("runtime_code", token)
```

- [ ] **Step 2: Run RED**

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_exporter.py space/tests/test_export_contract.py -q
```

Expected: FAIL because exporter interfaces do not exist.

- [ ] **Step 3: Implement exact source mappings**

```python
APP_SOURCE_MAP = {
    "README.md": "space/README.md",
    "Dockerfile": "space/Dockerfile",
    "requirements.lock": "space/requirements.lock",
    "requirements-dev.lock": "space/requirements-dev.lock",
    "app.py": "space/app.py",
    "carerisk_space/__init__.py": "space/carerisk_space/__init__.py",
    "carerisk_space/contracts.py": "space/carerisk_space/contracts.py",
    "carerisk_space/evidence.py": "space/carerisk_space/evidence.py",
    "carerisk_space/scenarios.py": "space/carerisk_space/scenarios.py",
    "carerisk_space/ui.py": "space/carerisk_space/ui.py",
    "SBOM.spdx.json": "space/SBOM.spdx.json",
    "THIRD_PARTY_LICENSES.json": "space/THIRD_PARTY_LICENSES.json",
    "tests/test_claim_contract.py": "space/tests/test_claim_contract.py",
    "tests/test_evidence_contract.py": "space/tests/test_evidence_contract.py",
    "tests/test_scenario_contract.py": "space/tests/test_scenario_contract.py",
    "tests/test_gradio_contract.py": "space/tests/test_gradio_contract.py",
    "tests/test_export_contract.py": "space/tests/test_export_contract.py",
    "tests/test_container_contract.py": "space/tests/test_container_contract.py",
}
TAG_SOURCE_MAP = {
    "evidence/final-result-receipt.json": "docs/final-result-receipt.json",
    "evidence/release-v0.2.0.json": "docs/release-v0.2.0.json",
    "LICENSE": "LICENSE",
    "NOTICE": "NOTICE",
    "CITATION.cff": "CITATION.cff",
}
MANIFEST_SOURCE_MAP = {"deployment-manifest.json": "space/deployment-manifest.json"}
```

In `tests/test_hf_space_exporter.py`, independently assert the cardinalities and partition:

```python
def test_source_maps_partition_the_exact_public_allowlist() -> None:
    source_sets = tuple(map(set, (APP_SOURCE_MAP, TAG_SOURCE_MAP, MANIFEST_SOURCE_MAP)))
    assert tuple(map(len, source_sets)) == (18, 5, 1)
    assert not (source_sets[0] & source_sets[1] or source_sets[0] & source_sets[2] or source_sets[1] & source_sets[2])
    assert set().union(*source_sets) == set(PUBLIC_PATHS)
    assert "scripts/verify_hf_space_candidate.py" not in set().union(*source_sets)
```

Invoke `git cat-file blob` with the already validated exact commit-and-path argument, or use an equivalent no-checkout Git object read. Reject a dirty worktree before manifest generation or export. Reject missing/non-commit SHAs, non-ancestor manifest commit, mutable tag mismatch, path traversal, symlinks, special files, collisions, unsorted/duplicate paths, hash/size mismatch, secret/private-key signatures, denied suffixes/content, and any final path-set difference. Write into a newly created destination only; on failure remove only that verified temporary destination.

The exporter permits the canonical text metadata record for the exact WebKit reviewer exception only inside `SBOM.spdx.json` and `THIRD_PARTY_LICENSES.json`. It rejects an executable/archive/binary payload, filesystem entry, source mapping, Docker context addition, manifest capability, or byte signature from the reviewer image or any embedded Chromium/Firefox/WebKit/ffmpeg tree. Tests mutate each destination category, including otherwise allowlisted `runtime_code`, `test`, `supply_chain`, and `metadata` files, so changing a capability label cannot launder reviewer bytes. `deployment-manifest.json` records the reviewer tuple only as non-distributed verification provenance and never as a source/destination artifact.

For `docs/final-result-receipt.json`, the exporter must read blob `b13ec7655bbdb8db1079c3b4793a0bf5590ef69c` (3,363 bytes) and require SHA-256 `d32d833af25e4ebb2f5bd06b64343eb36d7cd180c8e9777f539f6401b78064b3`; checkout line endings and normalization are invalid.

Compute `ExportReceipt.tree_sha256` as SHA-256 over the UTF-8 bytes of each sorted `destination_path`, NUL, lowercase file SHA-256, NUL, decimal byte size, and newline. This is an audit digest for the exact tree listing, not a substitute for per-file hashes or a Hugging Face destination commit.

- [ ] **Step 4: Run GREEN using temporary synthetic Git repositories**

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_exporter.py space/tests/test_export_contract.py -q
.venv-space\Scripts\ruff.exe check scripts/export_hf_space.py tests/test_hf_space_exporter.py space/tests/test_export_contract.py
```

Expected: all normal and rejection cases pass without reading ignored repository assets.

- [ ] **Step 5: Commit exporter source before any deployment manifest exists**

```powershell
git add -- scripts/export_hf_space.py tests/test_hf_space_exporter.py space/tests/test_export_contract.py
git diff --cached --check
git commit -m 'feat(space): export exact public Git objects'
```

### Task 9: Add separate digest-pinned reviewer and final runtime stages

**Files:**
- Create: `space/Dockerfile`
- Create: `space/tests/test_container_contract.py`
- Modify: `scripts/build_hf_space_supply_chain.py`
- Modify: `tests/test_hf_space_supply_chain.py`

**Interfaces:**
- Consumes: both named images in `tools/space/base-image.json`, the runtime/development locks, and the temporary clean export as Docker build context.
- Produces: a static non-root/nologin Docker contract; Task 13 produces the actual runtime smoke evidence.

- [ ] **Step 1: Write failing Dockerfile contract tests**

```python
def test_dockerfile_uses_both_recorded_patch_tags_and_platform_digests() -> None:
    images = load_base_images()
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    assert f'FROM {images["reviewer"]["tag"]}@{images["reviewer"]["linux_amd64_digest"]} AS test' in dockerfile
    assert f'FROM {images["runtime"]["tag"]}@{images["runtime"]["linux_amd64_digest"]} AS runtime' in dockerfile
    assert "COPY ." not in dockerfile
    assert "pip install --require-hashes --no-deps -r requirements-dev.lock" in dockerfile
    assert "pip install --require-hashes --no-deps -r requirements.lock" in dockerfile
    assert "playwright install" not in dockerfile
    assert "playwright install-deps" not in dockerfile

def test_runtime_account_is_non_root_and_non_login_without_claiming_bin_sh_absent() -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    assert "--shell /usr/sbin/nologin" in dockerfile
    assert final_user(dockerfile) == "10001:10001"
    assert 'CMD ["python", "app.py"]' in dockerfile
    assert "test ! -e /bin/sh" not in dockerfile

def test_runtime_starts_fixed_programmatic_uvicorn_not_cli_or_gradio_launch() -> None:
    source = APP_ENTRYPOINT.read_text(encoding="utf-8")
    assert 'CMD ["python", "app.py"]' in DOCKERFILE.read_text(encoding="utf-8")
    server_call = assert_exact_fastapi_mount_outer_guard_and_uvicorn_calls(source)
    assert literal_keyword(server_call, "http") == "h11"
    assert literal_keyword(server_call, "workers") == 1
    assert literal_keyword(server_call, "proxy_headers") is False
    assert "uvicorn " not in DOCKERFILE.read_text(encoding="utf-8")
    assert "httptools" not in source
    assert 'http="auto"' not in source
    assert ".launch(" not in source

def test_runtime_entrypoint_clears_injected_environment_before_python_import() -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    assert json_instruction(dockerfile, "ENTRYPOINT") == [
        "/usr/bin/env", "-i",
        "PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin",
        "LANG=C.UTF-8", "LC_ALL=C.UTF-8",
        "PYTHONUNBUFFERED=1", "PYTHONDONTWRITEBYTECODE=1",
        "GRADIO_ANALYTICS_ENABLED=False", "HF_HUB_DISABLE_TELEMETRY=True",
        "GRADIO_WATCH_DIRS=", "GRADIO_VIBE_MODE=", "GRADIO_HOT_RELOAD=false",
        "GRADIO_RUN_HISTORY=False", "GRADIO_SSR_MODE=False",
        "GRADIO_MCP_SERVER=False", "GRADIO_ALLOWED_PATHS=",
        "GRADIO_BLOCKED_PATHS=/",
    ]
    assert json_instruction(dockerfile, "CMD") == ["python", "app.py"]
    assert "SPACE_ID=" not in dockerfile
    assert "PORT=" not in dockerfile

def test_reviewer_stage_is_local_ci_only_and_cannot_flow_into_runtime_or_export() -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    graph = parse_dockerfile_stage_graph(dockerfile)
    assert graph.parents("runtime") == ()
    assert graph.base("runtime") == recorded_runtime_platform_ref()
    assert graph.base("test") == recorded_reviewer_platform_ref()
    assert not graph.copies_from("runtime", "test")
    assert_no_reviewer_or_browser_byte_signatures(graph.runtime_instructions("runtime"))
    assert_no_distribution_commands(dockerfile, forbidden=(
        "docker save", "docker export", "docker push", "buildx --output",
        "--output=type=registry", "--push",
    ))

@pytest.mark.parametrize(
    "mutation",
    ["runtime_from_test", "copy_from_test", "copy_ms_playwright", "runtime_browser_path", "runtime_reviewer_digest"],
)
def test_runtime_rejects_each_reviewer_byte_flow_mutation(mutation: str) -> None:
    with pytest.raises(ValueError, match="reviewer bytes reached runtime"):
        validate_dockerfile_policy(mutated_dockerfile(mutation))
```

- [ ] **Step 2: Run RED**

```powershell
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests/test_container_contract.py tests/test_hf_space_supply_chain.py -q
```

Expected: FAIL because the Space Dockerfile and smoke contract do not exist.

- [ ] **Step 3: Generate the Dockerfile from the verified base record**

The generated Dockerfile must expose named `test` and `runtime` stages with no ancestry between them. `test` starts from the exact official Playwright Python reviewer tag plus recorded linux/amd64 digest, installs the complete `requirements-dev.lock` union closure with hashes and no dependency resolution, and contains the six public test modules. Its Playwright Python version is exactly the one matched by the reviewer image and it uses only the Chromium/Firefox/WebKit bytes already embedded in that pinned image; it runs no browser download, `playwright install`, or unrecorded `apt` acquisition. This stage never becomes or contributes a filesystem layer to the deployed stage.

`runtime` starts independently from the exact CPython 3.11 slim-bookworm runtime tag plus recorded linux/amd64 digest. It uses explicit `COPY` for runtime files only, creates numeric UID/GID `10001`, assigns `/usr/sbin/nologin`, retains no writable home, installs `requirements.lock` with hashes and no dependency resolution, excludes tests/dev tools/browser/reviewer layers from the final image, and uses `USER 10001:10001`. The image inventory must prove `/usr/bin/env` exists and record its owning Debian package/version. The exec-form `ENTRYPOINT` is exactly `/usr/bin/env -i` followed by the fixed assignments `PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin`, `LANG=C.UTF-8`, `LC_ALL=C.UTF-8`, `PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1`, `GRADIO_ANALYTICS_ENABLED=False`, `HF_HUB_DISABLE_TELEMETRY=True`, `GRADIO_WATCH_DIRS=`, `GRADIO_VIBE_MODE=`, `GRADIO_HOT_RELOAD=false`, `GRADIO_RUN_HISTORY=False`, `GRADIO_SSR_MODE=False`, `GRADIO_MCP_SERVER=False`, `GRADIO_ALLOWED_PATHS=`, and `GRADIO_BLOCKED_PATHS=/`; exec-form `CMD ["python", "app.py"]` follows it. This clears Docker/Hugging Face environment injection before any Python or Gradio import while retaining only the reviewed runtime variables. Gradio `Blocks(analytics_enabled=False)` writes the same exact value `True`, so tests require pre-import, post-Blocks, PID 1, and every child to agree without a two-value exception. Poison runs inject `0` and secret-shaped alternatives and prove they are scrubbed. No `SPACE_ID`, `PORT`, Secret, Variable, or credential is required or preserved. Tests inspect final image history/package inventory and fail if Playwright, pytest, browser files, a reviewer-layer digest, or any reviewer/browser byte signature appears.

The `test` stage is review infrastructure only. It can be built and run locally or in CI by exact digest, but build/review tooling must not save, export, push, upload, publish, deploy, or emit it as any artifact/output. The runtime stage has no ancestry from `test`, no `COPY --from=test`, no `/ms-playwright` content, and no browser/reviewer layer or package. Static mutations independently introduce each forbidden ancestry/copy/path/digest form and must fail before a build.

Do not add an assertion or removal step for `/bin/sh`. The accepted proof is non-login passwd metadata plus absence of shell calls in application AST and exec-form startup.

- [ ] **Step 4: Run the static Docker/source GREEN available before provenance freeze**

The controller injects the three external custody values for this Task 9
process. Repeat the exact Tasks 7–13 custody preflight before this pytest command;
absence or malformed input stops before collection.

```powershell
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests/test_container_contract.py tests/test_hf_space_supply_chain.py tests/test_hf_space_source_boundary.py -q
.venv-space\Scripts\python.exe scripts/build_hf_space_supply_chain.py verify --repo-root .
```

Expected: Dockerfile/two-base/union-lock/account/startup/source contracts pass, including `python app.py` invoking the exact programmatic Uvicorn contract with explicit `http="h11"`, the exact `/usr/bin/env -i` allowlist, and absence of `SPACE_ID`/`PORT` configuration. The test may not infer h11 from an environment where `httptools` is absent. Do not build from `space/` directly because it intentionally lacks tag-sourced evidence/legal files, and do not invent a provisional manifest. Actual `/usr/bin/env` inventory, image, final-stage inventory, injected-environment stripping, UID/GID, read-only/tmpfs, CPU, no-network, loopback, outer-guard/file-capability, exact parser identity, and cold-start evidence is required from the two-commit clean export in Task 13 before any runtime success claim.

- [ ] **Step 5: Run tests and commit exact files**

```powershell
$env:PYTHONPATH = (Resolve-Path space)
git add -- space/Dockerfile space/tests/test_container_contract.py scripts/build_hf_space_supply_chain.py tests/test_hf_space_supply_chain.py
git diff --cached --check
git commit -m 'build(space): harden CPU-only container runtime'
```

### Task 10: Add local desktop, mobile, accessibility, and cold-start gates

**Files:**
- Create: `scripts/review_hf_space_local.py`
- Create: `scripts/verify_hf_space_candidate.py`
- Create: `tests/test_hf_space_live_review.py`
- Modify: `space/tests/test_gradio_contract.py`

**Interfaces:**
- Consumes: the inspected exact local final-image digest plus an owned GUID-named temporary run root outside the repository. No caller supplies a registry, remote image, bind mount, failure-state environment variable, evidence path, Dockerfile, mutation command, local tag, push/save/export destination, or other injection surface.
- Produces: `ReviewPlan`, split-invariant `LiveReviewRecord`, controller-retained `FailureVariantRecord`, post-inspection `FailureCleanupRecord`, `EvidenceReachabilityRecord`, `WireBoundaryRecord`, `CleanupTarget`, and ownership-safe orchestration that Task 13 exercises against the final clean candidate. Normal records always come from the exact final image; live failure records always come from one of four final-image-derived, local-only, labeled `NEVER_DEPLOY` images. The fifth taxonomy code is represented only by its explicit unit/component/ASGI precedence record. Every task-owned Docker resource carries exact run GUID plus a role-specific complete ownership schema: normal container=`normal` plus exact final digest, reviewer container=`reviewer` plus exact reviewer digest, shared internal network=`network`, and only the four failure images/containers=`failure_variant` plus exact base digest/code/`NEVER_DEPLOY=true`. After each successful variant build and inspection, the controller retains that code's exact local image reference plus inspected image ID/content digest; cleanup freshly re-inspects the actual image/container and requires those identities to match the retained record in addition to labels.

- [ ] **Step 1: Write failing review-contract tests**

```python
def test_default_review_plan_covers_exact_viewports_states_and_starts() -> None:
    plan = ReviewPlan.default()
    assert plan.viewports == ((1440, 900), (390, 844))
    assert plan.scenario_ids == EXPECTED_IDS
    assert plan.page_states == (
        "validated_normal",
        "receipt_missing",
        "receipt_hash_mismatch",
        "release_relationship_invalid",
        "deployment_manifest_invalid",
    )
    assert plan.cold_starts == 3
    assert plan.expected_live_records == 10  # five live states at two viewports

def test_failure_taxonomy_reachability_and_precedence_are_explicit() -> None:
    records = default_evidence_reachability_records()
    assert tuple(item.failure_code for item in records) == ALL_FAILURE_CODES
    by_code = {item.failure_code: item for item in records}
    assert by_code["receipt_missing"].live_reachable is True
    assert by_code["receipt_hash_mismatch"].live_reachable is True
    assert by_code["release_relationship_invalid"].live_reachable is True
    assert by_code["deployment_manifest_invalid"].live_reachable is True
    schema = by_code["receipt_schema_invalid"]
    assert schema.live_reachable is False
    assert schema.evidence_type == "unit_component_asgi"
    assert schema.precedence == "dominated_by_immutable_receipt_anchor"
    assert schema.live_review_status == "not_live_reviewed"

def test_container_cold_start_command_is_hardened() -> None:
    final_digest = "sha256:" + "a" * 64
    guid = "00000000-0000-0000-0000-000000000001"
    command = build_container_command(final_digest, run_guid=guid)
    joined = " ".join(command)
    for required in ("--cpus=2", "--network=none", "--read-only", "--tmpfs"):
        assert required in joined
    assert "mode=1777" in joined
    assert docker_ownership_labels(command) == ownership_labels(
        "normal", guid, final_digest=final_digest,
    )

def test_failure_variant_build_is_local_digest_derived_and_network_disabled() -> None:
    final_digest = "sha256:" + "a" * 64
    guid = "00000000-0000-0000-0000-000000000001"
    expected_reference = f"carerisk-local:{guid}-NEVER_DEPLOY-receipt_missing"
    command, dockerfile = build_never_deploy_variant(
        final_digest=final_digest,
        failure_code="receipt_missing",
        run_guid=guid,
        owned_temp_root=owned_temp_root(),
    )
    assert command[:4] == ["docker", "build", "--pull=false", "--network=none"]
    assert option_value(command, "--tag") == expected_reference
    assert dockerfile.startswith(f"FROM {final_digest}\n")
    assert "USER 0" in dockerfile
    assert 'RUN ["rm", "--", "/app/evidence/final-result-receipt.json"]' in dockerfile
    assert dockerfile.rstrip().endswith("USER 10001:10001")
    assert docker_ownership_labels(command) == ownership_labels(
        "failure_variant", guid,
        base_digest=final_digest, failure_code="receipt_missing",
    )

def test_successful_variant_inspection_freezes_exact_controller_record() -> None:
    built = sample_successfully_built_variant("receipt_missing")
    retained: dict[str, FailureVariantRecord] = {}
    record = inspect_validate_and_retain_variant(built, retained)
    assert record.image_reference == (
        f"carerisk-local:{record.run_guid}-NEVER_DEPLOY-receipt_missing"
    )
    assert record.image_id == record.image_digest == "sha256:" + "c" * 64
    assert record.base_final_image_digest == "sha256:" + "a" * 64
    assert record.expected_failure_code == "receipt_missing"
    assert retained == {"receipt_missing": record}

@pytest.mark.parametrize("forbidden", [
    "registry.example/x", "--push", "--output", "--save", "--mount", "--env",
])
def test_failure_variant_interface_rejects_remote_or_injection_inputs(forbidden: str) -> None:
    with pytest.raises(ReviewFailure, match="NEVER_DEPLOY input"):
        parse_failure_variant_arguments([forbidden])

def test_reviewer_app_uses_exact_internal_network_alias() -> None:
    final_digest = "sha256:" + "a" * 64
    reviewer_digest = "sha256:" + "b" * 64
    guid = "00000000-0000-0000-0000-000000000001"
    app_command = build_reviewed_app_command(final_digest, run_guid=guid)
    assert option_value(app_command, "--network-alias") == "carerisk-app"
    assert docker_ownership_labels(app_command) == ownership_labels(
        "normal", guid, final_digest=final_digest,
    )
    reviewer_command = build_reviewer_command(
        reviewer_digest, run_guid=guid, base_url="http://carerisk-app:7860",
    )
    assert reviewer_base_url(reviewer_command) == "http://carerisk-app:7860"
    assert docker_ownership_labels(reviewer_command) == ownership_labels(
        "reviewer", guid, reviewer_digest=reviewer_digest,
    )
    network_command = build_internal_network_command(run_guid=guid)
    assert docker_ownership_labels(network_command) == ownership_labels("network", guid)

def test_normal_reviewer_and_network_names_never_claim_never_deploy() -> None:
    commands = sample_normal_reviewer_and_network_create_commands()
    assert tuple(resource_role(command) for command in commands) == (
        "normal", "reviewer", "network",
    )
    assert all("NEVER_DEPLOY" not in option_value(command, "--name") for command in commands)

def test_cleanup_ownership_labels_are_exact_and_role_specific() -> None:
    guid = "00000000-0000-0000-0000-000000000001"
    final_digest = "sha256:" + "a" * 64
    reviewer_digest = "sha256:" + "b" * 64
    assert ownership_labels("normal", guid, final_digest=final_digest) == {
        "carerisk.run_guid": guid,
        "carerisk.resource_role": "normal",
        "carerisk.final_image_digest": final_digest,
    }
    assert ownership_labels("reviewer", guid, reviewer_digest=reviewer_digest) == {
        "carerisk.run_guid": guid,
        "carerisk.resource_role": "reviewer",
        "carerisk.reviewer_image_digest": reviewer_digest,
    }
    assert ownership_labels("network", guid) == {
        "carerisk.run_guid": guid,
        "carerisk.resource_role": "network",
    }
    assert ownership_labels(
        "failure_variant", guid, base_digest=final_digest,
        failure_code="receipt_missing",
    ) == {
        "carerisk.run_guid": guid,
        "carerisk.resource_role": "failure_variant",
        "carerisk.base_digest": final_digest,
        "carerisk.failure_code": "receipt_missing",
        "carerisk.never_deploy": "true",
    }
    failure_container = build_failure_app_command(
        variant_digest="sha256:" + "c" * 64,
        variant_reference=f"carerisk-local:{guid}-NEVER_DEPLOY-receipt_missing",
        run_guid=guid,
        base_digest=final_digest,
        failure_code="receipt_missing",
    )
    assert option_value(failure_container, "--name") == (
        f"carerisk-{guid}-NEVER_DEPLOY-receipt_missing"
    )
    assert docker_ownership_labels(failure_container) == ownership_labels(
        "failure_variant", guid, base_digest=final_digest,
        failure_code="receipt_missing",
    )

@pytest.mark.parametrize("mutation", [
    "missing_role", "extra_ownership_label", "contradictory_role",
    "duplicate_ownership_label", "wrong_guid", "wrong_digest", "ambiguous_reference",
])
def test_cleanup_preserves_resource_when_type_specific_ownership_is_not_exact(
    mutation: str,
) -> None:
    target, inspector = type_specific_cleanup_case_with_inspection_mutation(mutation)
    remover = RemovalSpy()
    with pytest.raises(ReviewFailure, match="cleanup ownership"):
        cleanup_owned_target(
            target, sample_run_guid(), sample_expected_variant_records(), inspector, remover
        )
    assert remover.calls == ()

@pytest.mark.parametrize("mutation", [
    "swapped_variant_image_digest", "wrong_variant_image_reference",
    "wrong_container_image_id", "wrong_container_config_image_reference",
    "wrong_failure_container_name",
])
def test_failure_cleanup_preserves_correctly_labeled_but_wrong_image_identity(
    mutation: str,
) -> None:
    records = sample_expected_variant_records()
    target, inspector = correctly_labeled_failure_target_with_inspection_mutation(
        mutation, records
    )
    remover = RemovalSpy()
    with pytest.raises(ReviewFailure, match="failure variant identity"):
        cleanup_owned_target(target, sample_run_guid(), records, inspector, remover)
    assert remover.calls == ()

def test_cleanup_validates_each_role_and_resource_type_before_literal_remove() -> None:
    records = sample_expected_variant_records()
    for target in sample_exact_cleanup_targets_for_all_roles_and_types():
        inspector = InspectionStub.for_target(target, expected_variants=records)
        remover = RemovalSpy()
        cleanup_owned_target(target, sample_run_guid(), records, inspector, remover)
        assert remover.calls == ((target.resource_type, target.resource_id),)

def test_failed_live_record_cannot_be_reported_as_green() -> None:
    record = sample_record(serious_accessibility_findings=1)
    with pytest.raises(ReviewFailure, match="accessibility"):
        assert_review_passed(record)

def test_normal_and_failure_records_use_disjoint_assertions() -> None:
    normal = sample_normal_record()
    assert_review_passed(normal)
    assert normal.radio_count == normal.control_count == normal.scenario_panel_count == 4
    assert normal.keyboard_selection_performed is True
    assert normal.scenario_visibility_before_after == EXPECTED_VISIBILITY_TRANSITIONS

    failure = sample_failure_record("receipt_missing")
    assert_review_passed(failure)
    assert failure.radio_count == failure.control_count == failure.scenario_panel_count == 0
    assert failure.keyboard_selection_performed is False
    assert failure.scenario_visibility_before_after == ()
    assert failure.visible_metric_count == failure.visible_canonical_value_count == 0
    assert failure.visible_failure_code == "receipt_missing"

def test_normal_assertions_are_never_applied_to_failure_record() -> None:
    with pytest.raises(ReviewFailure, match="failure-only surface"):
        assert_review_passed(replace(sample_failure_record("receipt_missing"), radio_count=4))
    with pytest.raises(ReviewFailure, match="normal-only surface"):
        assert_review_passed(replace(sample_normal_record(), keyboard_selection_performed=False))

def test_candidate_verifier_temp_self_test_rejects_unowned_or_outside_paths() -> None:
    result = run_candidate_verifier("--self-test-temp-ownership")
    assert result.returncode == 0
    assert "rejected-unowned" in result.stdout
    assert "rejected-outside-temp-root" in result.stdout

def test_boundary_record_keeps_asgi_messages_and_wire_observations_distinct() -> None:
    record = sample_wire_boundary_record()
    assert record.pure_asgi_invalid_host_statuses == (404, 404, 404)
    assert record.pure_asgi_blocked_body == b"Not Found"
    assert record.pure_asgi_blocked_content_length == 9
    assert record.wire_missing_duplicate_host_statuses == (400, 400)
    assert record.wire_parser_app_entry_delta == 0
    assert record.wire_blocked_head_entity_bytes == 0
    assert record.wire_blocked_head_content_length == 9
    assert_wire_boundary_passed(record)
```

- [ ] **Step 2: Run RED**

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_live_review.py -q
```

Expected: FAIL because the review runner and records do not exist.

- [ ] **Step 3: Implement ephemeral review orchestration**

```python
LivePageState = Literal[
    "validated_normal",
    "receipt_missing",
    "receipt_hash_mismatch",
    "release_relationship_invalid",
    "deployment_manifest_invalid",
]

@dataclass(frozen=True)
class ReviewPlan:
    viewports: tuple[tuple[int, int], ...]
    scenario_ids: tuple[str, ...]
    page_states: tuple[LivePageState, ...]
    cold_starts: int

    @property
    def expected_live_records(self) -> int:
        return len(self.viewports) * len(self.page_states)

    @classmethod
    def default(cls) -> "ReviewPlan":
        return cls(
            viewports=((1440, 900), (390, 844)),
            scenario_ids=SCENARIO_IDS,
            page_states=(
                "validated_normal",
                "receipt_missing",
                "receipt_hash_mismatch",
                "release_relationship_invalid",
                "deployment_manifest_invalid",
            ),
            cold_starts=3,
        )

@dataclass(frozen=True)
class LiveReviewRecord:
    viewport: tuple[int, int]
    page_state: LivePageState
    truth_and_headline_order_valid: bool
    truth_and_headline_visible: bool
    horizontal_overflow_px: int
    body_font_px: float
    responsive_layout_valid: bool
    fonts_loaded: bool
    heading_hierarchy_valid: bool
    non_color_only_status: bool
    radio_count: int
    control_count: int
    scenario_panel_count: int
    minimum_control_target_px: float | None
    keyboard_selection_performed: bool
    scenario_visibility_before_after: tuple[tuple[str, bool, bool], ...]
    focus_review: Literal["passed", "not_applicable"]
    visible_metric_count: int
    visible_canonical_value_count: int
    normal_claims_and_metrics_exact: bool
    visible_failure_code: str | None
    expected_failure_message_visible: bool
    serious_accessibility_findings: int
    critical_accessibility_findings: int
    console_errors: tuple[str, ...]
    external_app_requests: tuple[str, ...]
    app_request_method_path_queries: tuple[tuple[str, str, str], ...]
    outer_guard_blocked_count: int
    post_request_count: int
    event_or_session_request_count: int
    queue_request_count: int
    public_interaction_state_delta: int
    sanitized_scope_compatible: bool
    package_asset_membership_digest: str
    accepted_manifest_count: int
    accepted_favicon_count: int
    first_http_200_seconds: float
    claim_visible_seconds: float
    partial_metrics: bool
    download_or_model_initialization: bool
    cold_start_source_is_exact_final_or_derived_digest: bool

@dataclass(frozen=True)
class FailureVariantRecord:
    run_guid: str
    image_reference: str
    image_id: str
    image_digest: str
    base_final_image_digest: str
    expected_failure_code: Literal[
        "receipt_missing",
        "receipt_hash_mismatch",
        "release_relationship_invalid",
        "deployment_manifest_invalid",
    ]
    labels: tuple[tuple[str, str], ...]
    dockerfile_sha256: str
    build_pull_disabled: bool
    build_network_none: bool
    image_user: str
    entrypoint_and_cmd_match_final: bool
    intended_path_delta: tuple[str, ...]
    unexpected_path_or_byte_deltas: tuple[str, ...]
    app_source_locks_assets_match_final: bool
    observed_failure_codes: tuple[str, ...]
    remote_or_export_input_count: int

@dataclass(frozen=True)
class FailureCleanupRecord:
    run_guid: str
    expected_failure_code: str
    container_name: str
    expected_image_reference: str
    expected_image_id: str
    expected_image_digest: str
    actual_image_reference: str
    actual_image_id: str
    actual_image_digest: str
    container_image_id: str
    container_config_image_reference: str
    labels_exact: bool

@dataclass(frozen=True)
class EvidenceReachabilityRecord:
    failure_code: EvidenceFailureCode
    owning_gate: str
    live_reachable: bool
    evidence_type: Literal["final_image_variant", "unit_component_asgi"]
    precedence: Literal[
        "runtime_reachable",
        "dominated_by_immutable_receipt_anchor",
    ]
    live_review_status: Literal["reviewed", "not_live_reviewed"]

@dataclass(frozen=True)
class WireBoundaryRecord:
    pure_asgi_invalid_host_statuses: tuple[int, ...]
    pure_asgi_blocked_body: bytes
    pure_asgi_blocked_content_length: int
    wire_missing_duplicate_host_statuses: tuple[int, ...]
    wire_parser_app_entry_delta: int
    wire_parser_has_cors_or_compression: bool
    wire_parser_canary_or_reflection_count: int
    valid_unlisted_host_guard_status: int
    valid_unlisted_host_app_entry_delta: int
    wire_blocked_head_entity_bytes: int
    wire_blocked_head_content_length: int

ResourceRole = Literal["normal", "reviewer", "network", "failure_variant"]

@dataclass(frozen=True)
class CleanupTarget:
    resource_type: Literal["container", "image", "network"]
    resource_id: str
    expected_role: ResourceRole
    expected_final_digest: str | None = None
    expected_reviewer_digest: str | None = None
    expected_base_digest: str | None = None
    expected_failure_code: str | None = None

@dataclass(frozen=True)
class InspectedDockerResource:
    resource_type: Literal["container", "image", "network"]
    resource_id: str
    resource_name: str
    labels: tuple[tuple[str, str], ...]
    image_reference: str | None
    image_id: str | None
    image_digest: str | None
    container_image_id: str | None
    container_config_image_reference: str | None

class DockerResourceInspector(Protocol):
    def inspect_literal(
        self, resource_type: str, resource_id: str,
    ) -> InspectedDockerResource: ...

class LiteralResourceRemover(Protocol):
    def remove_literal(self, resource_type: str, resource_id: str) -> None: ...

def assert_wire_boundary_passed(record: WireBoundaryRecord) -> None:
    if record.pure_asgi_invalid_host_statuses != (404, 404, 404):
        raise ReviewFailure("pure-ASGI Host gate")
    if record.pure_asgi_blocked_body != b"Not Found":
        raise ReviewFailure("pure-ASGI fixed body")
    if record.pure_asgi_blocked_content_length != 9:
        raise ReviewFailure("pure-ASGI fixed content length")
    if record.wire_missing_duplicate_host_statuses != (400, 400):
        raise ReviewFailure("pinned wire parser Host status")
    if record.wire_parser_app_entry_delta != 0:
        raise ReviewFailure("wire parser reached ASGI app")
    if record.wire_parser_has_cors_or_compression:
        raise ReviewFailure("wire parser added CORS or compression")
    if record.wire_parser_canary_or_reflection_count:
        raise ReviewFailure("wire parser reflected hostile input")
    if (record.valid_unlisted_host_guard_status, record.valid_unlisted_host_app_entry_delta) != (404, 1):
        raise ReviewFailure("valid unlisted Host did not reach guard")
    if (record.wire_blocked_head_entity_bytes, record.wire_blocked_head_content_length) != (0, 9):
        raise ReviewFailure("wire HEAD representation")

class ReviewFailure(RuntimeError):
    pass

def assert_review_passed(record: LiveReviewRecord) -> None:
    if record.serious_accessibility_findings or record.critical_accessibility_findings:
        raise ReviewFailure("accessibility findings")
    if not record.truth_and_headline_order_valid or not record.truth_and_headline_visible:
        raise ReviewFailure("truth or headline order/visibility")
    if (
        record.horizontal_overflow_px
        or record.body_font_px < 16
        or not record.responsive_layout_valid
        or not record.fonts_loaded
        or not record.heading_hierarchy_valid
        or not record.non_color_only_status
    ):
        raise ReviewFailure("responsive layout")
    if record.console_errors or record.external_app_requests:
        raise ReviewFailure("console or external request")
    if record.outer_guard_blocked_count:
        raise ReviewFailure("normal browser request blocked by public-surface guard")
    if record.post_request_count or record.event_or_session_request_count or record.queue_request_count:
        raise ReviewFailure("static explorer emitted server interaction")
    if record.public_interaction_state_delta:
        raise ReviewFailure("public interaction changed framework state")
    if record.accepted_manifest_count < 1 or record.accepted_favicon_count < 1:
        raise ReviewFailure("required metadata request was not observed")
    if not is_expected_package_membership_digest(record.package_asset_membership_digest):
        raise ReviewFailure("package asset membership drift")
    if not record.sanitized_scope_compatible:
        raise ReviewFailure("authority-selected sanitized scope is incompatible")
    if not all(
        is_expected_public_scope(method, path, query)
        for method, path, query in record.app_request_method_path_queries
    ):
        raise ReviewFailure("browser used a non-allowlisted app route")
    if record.partial_metrics or record.download_or_model_initialization:
        raise ReviewFailure("partial evidence or runtime download")
    if not record.cold_start_source_is_exact_final_or_derived_digest:
        raise ReviewFailure("unbound review image")

    if record.page_state == "validated_normal":
        if (record.radio_count, record.control_count, record.scenario_panel_count) != (4, 4, 4):
            raise ReviewFailure("normal-only surface counts")
        if record.minimum_control_target_px is None or record.minimum_control_target_px < 44:
            raise ReviewFailure("normal-only control target")
        if not record.keyboard_selection_performed or record.focus_review != "passed":
            raise ReviewFailure("normal-only surface keyboard/focus")
        if record.scenario_visibility_before_after != EXPECTED_VISIBILITY_TRANSITIONS:
            raise ReviewFailure("normal-only surface transitions")
        if not record.normal_claims_and_metrics_exact:
            raise ReviewFailure("normal-only claims/metrics")
        if record.visible_failure_code is not None or record.expected_failure_message_visible:
            raise ReviewFailure("normal-only failure content")
    else:
        if (record.radio_count, record.control_count, record.scenario_panel_count) != (0, 0, 0):
            raise ReviewFailure("failure-only surface counts")
        if record.minimum_control_target_px is not None:
            raise ReviewFailure("failure-only control target")
        if record.keyboard_selection_performed or record.focus_review != "not_applicable":
            raise ReviewFailure("failure-only surface keyboard/focus")
        if record.scenario_visibility_before_after:
            raise ReviewFailure("failure-only surface transitions")
        if record.visible_metric_count or record.visible_canonical_value_count:
            raise ReviewFailure("failure-only surface metrics")
        if record.normal_claims_and_metrics_exact:
            raise ReviewFailure("failure-only normal evidence")
        if record.visible_failure_code != record.page_state or not record.expected_failure_message_visible:
            raise ReviewFailure("failure-only code/message")

def assert_failure_variant_passed(record: FailureVariantRecord) -> None:
    expected_labels = {
        "carerisk.never_deploy": "true",
        "carerisk.run_guid": record.run_guid,
        "carerisk.resource_role": "failure_variant",
        "carerisk.base_digest": record.base_final_image_digest,
        "carerisk.failure_code": record.expected_failure_code,
    }
    expected_reference = (
        f"carerisk-local:{record.run_guid}-NEVER_DEPLOY-"
        f"{record.expected_failure_code}"
    )
    if record.image_reference != expected_reference or dict(record.labels) != expected_labels:
        raise ReviewFailure("NEVER_DEPLOY labels")
    if record.image_id != record.image_digest:
        raise ReviewFailure("NEVER_DEPLOY inspected image identity")
    if not record.build_pull_disabled or not record.build_network_none:
        raise ReviewFailure("NEVER_DEPLOY build boundary")
    if record.image_user != "10001:10001":
        raise ReviewFailure("NEVER_DEPLOY final user")
    if not record.entrypoint_and_cmd_match_final or not record.app_source_locks_assets_match_final:
        raise ReviewFailure("NEVER_DEPLOY final-image identity")
    if len(record.intended_path_delta) != 1 or record.unexpected_path_or_byte_deltas:
        raise ReviewFailure("NEVER_DEPLOY mutation delta")
    if record.observed_failure_codes != (record.expected_failure_code,):
        raise ReviewFailure("NEVER_DEPLOY failure-code isolation")
    if record.remote_or_export_input_count:
        raise ReviewFailure("NEVER_DEPLOY remote/export input")

def validate_cleanup_target(
    target: CleanupTarget,
    current_run_guid: str,
    expected_variants: Mapping[str, FailureVariantRecord],
    inspector: DockerResourceInspector,
) -> None:
    actual = inspector.inspect_literal(target.resource_type, target.resource_id)
    labels = dict(actual.labels)
    if len(labels) != len(actual.labels):
        raise ReviewFailure("cleanup ownership duplicate labels")
    expected = ownership_labels_for_target(target, current_run_guid)
    ownership_labels_found = {
        key: value for key, value in labels.items() if key.startswith("carerisk.")
    }
    if ownership_labels_found != expected:
        raise ReviewFailure("cleanup ownership labels")
    assert_exact_resource_type_identity_reference_and_digest(target, actual)
    if target.expected_role == "failure_variant":
        if target.expected_failure_code not in expected_variants:
            raise ReviewFailure("failure variant identity record missing")
        expected = expected_variants[target.expected_failure_code]
        assert_failure_cleanup_matches_expected_record(target, actual, expected)

def cleanup_owned_target(
    target: CleanupTarget,
    current_run_guid: str,
    expected_variants: Mapping[str, FailureVariantRecord],
    inspector: DockerResourceInspector,
    remover: LiteralResourceRemover,
) -> None:
    validate_cleanup_target(target, current_run_guid, expected_variants, inspector)
    remover.remove_literal(target.resource_type, target.resource_id)

def assert_evidence_reachability_passed(
    records: tuple[EvidenceReachabilityRecord, ...],
) -> None:
    if tuple(item.failure_code for item in records) != ALL_FAILURE_CODES:
        raise ReviewFailure("failure taxonomy reachability order")
    live_codes = tuple(item.failure_code for item in records if item.live_reachable)
    if live_codes != (
        "receipt_missing",
        "receipt_hash_mismatch",
        "release_relationship_invalid",
        "deployment_manifest_invalid",
    ):
        raise ReviewFailure("runtime-reachable failure matrix")
    schema = next(item for item in records if item.failure_code == "receipt_schema_invalid")
    if schema != EvidenceReachabilityRecord(
        failure_code="receipt_schema_invalid",
        owning_gate="strict_receipt_json_schema_after_identity",
        live_reachable=False,
        evidence_type="unit_component_asgi",
        precedence="dominated_by_immutable_receipt_anchor",
        live_review_status="not_live_reviewed",
    ):
        raise ReviewFailure("receipt schema precedence")
```

The Python runner has two explicit execution modes plus one local derivation phase. Container cold-start mode starts the exact inspected final-image digest with the same two-CPU/no-network/read-only/tmpfs flags as Task 9 and uses `docker exec` with Host `127.0.0.1:7860` to probe exact root/config/theme/manifest/favicon/package-member responses and claim copy on loopback. It records the exact `uvicorn.run(..., http="h11", ...)` source/config/runtime identity, locked package membership/content-tree digest, and authoritative blocked matrix, including method-table HEAD probes, nonexistent-valid asset names, authority mutations, metadata/PWA paths, and downstream/receive/fetch/temp bombs. Every direct pure-ASGI helper constructs `PublicSurfaceGuard(downstream, exact_package_asset_urls())`, where the helper derives and asserts the nonempty pinned-root membership. `WireBoundaryRecord` then keeps those deterministic ASGI messages separate from raw HTTP/1.1 observations against that explicit h11 Uvicorn server: missing/duplicate Host must return `(400, 400)` before the app-entry marker, a valid unlisted single Host must increment that marker and receive guard 404, and every blocked non-root wire `HEAD` must have zero entity bytes with `content-length: 9` even though the pure-ASGI response body message is `b"Not Found"`. All records require zero CORS/compression/canary/reflection and preserve exact selected sanitized downstream scope and defense-in-depth state separately.

Only after final-image inspection, a derivation phase creates four task-owned local images for runtime-reachable failure review. The verifier itself generates a literal Dockerfile and minimal context beneath its validated GUID temp root for each exact reachable failure code. Every Dockerfile begins `FROM <exact inspected local final digest>`, uses `USER 0` only around one package-relative evidence mutation, and ends `USER 10001:10001`. `receipt_missing` uses exec-form `RUN ["rm", "--", "/app/evidence/final-result-receipt.json"]`; the other variants `COPY` one generated mutated artifact over exactly `/app/evidence/final-result-receipt.json`, `/app/evidence/release-v0.2.0.json`, or `/app/deployment-manifest.json` to produce `receipt_hash_mismatch`, `release_relationship_invalid`, or `deployment_manifest_invalid`. Each variant has exactly one intended path delta; no manifest compensation or secondary mutation is allowed. The build command is exact `docker build --pull=false --network=none`, with no remote registry or output/export option. For code `<code>`, the verifier generates exact local reference `carerisk-local:<GUID>-NEVER_DEPLOY-<code>` and exact reserved ownership labels `carerisk.never_deploy=true`, `carerisk.run_guid=<GUID>`, `carerisk.resource_role=failure_variant`, `carerisk.base_digest=<digest>`, and `carerisk.failure_code=<code>`. After build succeeds, it freshly inspects and validates that image, then creates and retains exactly one immutable `FailureVariantRecord` keyed by code containing the local reference, inspected image ID/content digest, final base digest, code, GUID, labels, and delta evidence. Failure review and cleanup consume that retained object; they do not reconstruct identity from labels or tag text. It rejects caller-controlled image names, paths, Dockerfile content, mutation commands, remote/tag/push/save/export inputs, bind mounts, runtime environment/path switches, and monkeypatches.

`receipt_schema_invalid` deliberately has no derived image. The canonical receipt SHA-256 and Git-blob checks precede strict JSON/schema validation, so any live byte mutation is owned by `receipt_hash_mismatch`. The existing explicit controlled anchor seam is allowed only in unit tests to isolate downstream strict-parser/schema behavior; component and direct-ASGI tests then require its exact bounded message and zero controls, metrics, scenarios, dependency/function/API surface, app-owned event/API traffic, or echo. The permitted root GET still enters the mounted static document and is not counted as an event. A running container, final image, derived image, browser record, or cold-start record must never patch those anchors or describe schema failure as live evidence. `EvidenceReachabilityRecord` makes this precedence and `not_live_reviewed` status machine-verifiable instead of silently omitting the code.

Image inspection and filesystem comparison bind each derived image to the final digest, require unchanged entrypoint/CMD and final `USER 10001:10001`, require the intended single evidence delta, and require every application source, lock, package asset, and other path to match the final image byte-for-byte. Each image must emit exactly its one expected bounded code. Browser-review mode creates one GUID-labeled Docker `--internal` network, always uses exact alias `carerisk-app`, and runs the exact Playwright reviewer against the exact final image for normal review and each of the four `NEVER_DEPLOY` images for its one failure review. Each failure container has exact name `carerisk-<GUID>-NEVER_DEPLOY-<code>` and is created from the exact local image reference held by that code's retained record; normal/reviewer containers and the shared network have role-specific names without `NEVER_DEPLOY`. All five live page states are exercised at both viewports with the same entrypoint and runtime flags. Shared assertions cover only truth/headline ordering, responsive/font/heading/non-color accessibility, console/external/request graph, guard/state-delta/package membership/sanitized scope, and cold-start/no-download/no-model-init behavior. Normal-only assertions cover four radios/controls/panels, targets, keyboard/focus, exact visibility transitions, and receipt-backed claims/metrics. Failure-only assertions cover zero radios/controls/panels/transitions/metrics/canonical values, false or not-applicable keyboard/focus, the exact visible failure code/message, and no partial evidence. Normal traffic follows the exact method table (`GET` except root may also use `HEAD`), includes observed manifest/favicon/static-logo requests, and has zero guard blocks, POSTs, event/session/queue requests, public state delta, external requests, or console errors. The internal network permits reviewer-to-app traffic but has no external route and no dependency download. Browser review never substitutes for `--network none` smoke.

If the normal Gradio `6.26.0` browser needs a route/query/method not in the approved table, emits any POST/event/session/queue traffic, changes framework public-interaction state, cannot use the exact `carerisk-app:7860` authority-selected sanitized scope behind the reviewer network, produces an asset inventory mismatch, or if outer ordering lets a blocked probe reach FastAPI/Gradio/body receive, the runner raises a load-bearing incompatibility and stops. If an authorized Hugging Face candidate or iframe Host is not exactly `steven0226-carerisk-48h.hf.space`, publication stops and reports centrally. The implementation must source-audit the exact issue, add a RED test, and report centrally; it must not accept a generic prefix, method, static, upload, file, header, host, authority suffix, or query wildcard.

`verify_hf_space_candidate.py` owns final orchestration. It creates exactly one GUID-named run directory beneath `Path(tempfile.gettempdir()).resolve(strict=True)` and writes an ownership marker containing that GUID and canonical root. Candidate, review, and `NEVER_DEPLOY` build-context directories are children of that run root and contain that literal marker in their names. Each task-owned Docker resource has exact `carerisk.run_guid=<GUID>` and one explicit role: the normal final-image container has `resource_role=normal` plus exact final-image digest; the reviewer container has `resource_role=reviewer` plus exact reviewer-image digest; the shared internal network has `resource_role=network`; and only the four failure containers/images have `resource_role=failure_variant` plus exact base digest, expected code, and `NEVER_DEPLOY=true`. A `try/finally` dispatches by Docker resource type and freshly inspects the literal current resource ID. It validates the complete exact reserved ownership-label set, literal resource ID/reference, inspected image/base/reviewer/final digest as applicable, expected failure code as applicable, and current GUID before issuing one literal removal. For each failure image/container it also requires the controller-retained record for that code; the actual image reference, image ID, and content digest must equal the record, while a container's `.Image` and configured image reference must resolve to the same recorded image. Labels are necessary but never substitute for these comparisons. A swapped image, wrong digest/reference with correct labels, missing record, duplicate/additional/contradictory label, ambiguous/stale identity, or type/name mismatch is a hard stop and leaves the resource untouched. The exact failure container name must be `carerisk-<GUID>-NEVER_DEPLOY-<code>`; normal/reviewer/network names must not contain `NEVER_DEPLOY`. It then calls a cleanup function that re-resolves the OS temp root, rejects symlinks/reparse points, requires the exact GUID prefix plus matching ownership marker/canonical root, and applies `shutil.rmtree` only to that one run directory. It never deletes by name prefix alone, dangling image list, broad Docker filter, or unverified path. Unowned, missing-label/marker, mismatched, symlink/reparse-point, workspace, temp-root itself, or outside-temp resources are a hard stop and are left untouched for manual inspection. The script emits its final verification receipt to stdout after cleanup; it persists no review or derived-image artifact and exposes no remote/upload/tag/push/save/export path.

- [ ] **Step 4: Run orchestration/config GREEN before the final candidate exists**

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_live_review.py space/tests/test_gradio_contract.py -q -m 'not integration'
```

Expected: orchestration, exact 10-record live viewport/state matrix, final-digest-only normal command, four local-only `NEVER_DEPLOY` variant build/inspect/retained-reference-ID-digest/label/delta/code/cleanup contracts, literal `NEVER_DEPLOY` failure-container name tests, role-specific normal/reviewer/network/failure ownership schemas, and fail-closed swapped/wrong image digest/reference preservation tests pass. Five-code reachability/precedence records, split shared/normal/failure assertions, hardened command construction, Gradio config, exact `http="h11"` identity, distinct pure-ASGI/wire boundary records, and failure-reporting contracts also pass. Unit records require the nonempty pinned-root membership and prove no result can pass through constructor `TypeError`; schema failure asserts the exact three-part failure copy, sole bounded code, and zero surface/echo as unit/component/ASGI evidence and is explicitly not live-reviewed. Do not claim a built variant, live Uvicorn parser, HEAD wire, viewport, container, accessibility, or cold-start success here, because those require the clean candidate in Task 13. Thirty seconds remains a recorded soft local target, never a public SLA.

- [ ] **Step 5: Commit exact review files**

```powershell
git add -- scripts/review_hf_space_local.py scripts/verify_hf_space_candidate.py tests/test_hf_space_live_review.py space/tests/test_gradio_contract.py
git diff --cached --check
git commit -m 'test(space): gate local accessibility and cold start'
```

### Task 11: Add Space-specific CI and freeze the app-source commit

**Files:**
- Create: `.github/workflows/space-ci.yml`
- Modify: `tests/test_hf_space_source_boundary.py`
- Modify: `tests/test_hf_space_supply_chain.py`
- Modify: `tests/test_hf_space_exporter.py`

**Interfaces:**
- Consumes: complete app source, tests, locks, supply-chain outputs, exporter, and Docker contract.
- Consumes locally: the controller-injected three-value custody transport.
- Consumes in Actions only after separate remote authorization: GitHub Actions Environment `carerisk-contract-custody` with three external variables named exactly `CARERISK_GRADIO_CONTRACT_BLOB_SHA1`, `CARERISK_GRADIO_CONTRACT_RAW_SIZE`, and `CARERISK_GRADIO_CONTRACT_RAW_SHA256`.
- Consumes in the future Task 11 reviewer container only: a fail-closed checkout-ownership contract selected independently of candidate repository content—either the reviewer runs with the host checkout's exact numeric UID/GID, or it receives the controller-resolved exact mounted checkout path as its sole `safe.directory` value.
- Produces: a reviewed app-source commit whose SHA is the immutable `space_app_source_git_sha`.

Creating the Actions Environment or setting/changing any of its variables is
remote metadata mutation and is not authorized by Task 11. The tracked workflow
and its local contract tests may be committed while the remote channel is
absent; any remote run must then fail closed until separate written
authorization provisions the exact external values.

The checkout-ownership requirement is future Task 11 work and does not add or
change any current Task 6 acceptance gate. Before Task 11 implementation, its
workflow-contract tests must parse the reviewer invocation and prove exactly
one supported mode: either `--user` receives the host checkout owner's exact
numeric UID and GID, or a controller-owned pre-step resolves the read-only
mounted checkout and supplies that one exact path as `safe.directory`. The
second mode must compare the supplied value byte-for-byte with an independently
resolved mount path before Git or pytest. Missing, empty, relative, unresolved,
mismatched, multiple, or wildcard values fail before tests. `safe.directory=*`,
repository-local or candidate-controlled Git config, a candidate-provided path,
and a broad parent directory are forbidden. Contract mutations must remove the
ownership control, change either UID/GID, substitute a sibling/parent path, add
`safe.directory=*`, and source config from the checkout; every mutation must
fail closed.

- [ ] **Step 1: Write failing workflow-contract tests**

```python
def test_space_ci_is_read_only_pinned_and_runs_all_gates() -> None:
    workflow = yaml.safe_load(SPACE_CI.read_text(encoding="utf-8"))
    assert workflow["permissions"] == {"contents": "read"}
    uses = [step["uses"] for job in workflow["jobs"].values() for step in job["steps"] if "uses" in step]
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", item) for item in uses)
    commands = "\n".join(
        step.get("run", "") for job in workflow["jobs"].values() for step in job["steps"]
    )
    for required in (
        "--require-hashes", "test_hf_space_source_boundary.py", "test_hf_space_supply_chain.py",
        "test_hf_space_exporter.py", "space/tests", "--network none", "--read-only",
        "--tmpfs", "--cpus=2", "pip check",
    ):
        assert required in commands

def test_app_source_workflow_runs_source_gates_only_without_manifest() -> None:
    workflow = yaml.safe_load(SPACE_CI.read_text(encoding="utf-8"))
    source = workflow["jobs"]["source_gates"]
    candidate = workflow["jobs"]["candidate_gates"]
    assert source["env"]["REVIEWER_IMAGE"] == recorded_reviewer_platform_ref()
    assert source["outputs"]["manifest_present"] == "${{ steps.manifest.outputs.present }}"
    assert candidate["needs"] == "source_gates"
    assert candidate["if"] == "${{ needs.source_gates.outputs.manifest_present == 'true' }}"
    source_commands = "\n".join(step.get("run", "") for step in source["steps"])
    candidate_commands = "\n".join(step.get("run", "") for step in candidate["steps"])
    assert "--require-hashes --no-deps" in source_commands
    assert "--network none" in source_commands
    assert "verify_hf_space_candidate.py" not in source_commands
    assert "verify_hf_space_candidate.py" in candidate_commands
    assert "provisional" not in SPACE_CI.read_text(encoding="utf-8").lower()

def test_ci_never_distributes_reviewer_image_or_browser_bytes() -> None:
    workflow = yaml.safe_load(SPACE_CI.read_text(encoding="utf-8"))
    commands = "\n".join(
        step.get("run", "") for job in workflow["jobs"].values() for step in job["steps"]
    )
    assert recorded_reviewer_platform_ref() in commands
    assert_no_distribution_commands(commands, forbidden=(
        "docker save", "docker export", "docker push", "buildx --push",
        "--output=type=registry", "--output=type=oci", "--output=type=docker",
    ))
    assert not any(
        "actions/upload-artifact" in step.get("uses", "")
        for job in workflow["jobs"].values()
        for step in job["steps"]
    )
    assert_reviewer_runs_are_ephemeral_local_ci_only(workflow)

CUSTODY_ENVIRONMENT = "carerisk-contract-custody"
CUSTODY_NAMES = (
    "CARERISK_GRADIO_CONTRACT_BLOB_SHA1",
    "CARERISK_GRADIO_CONTRACT_RAW_SIZE",
    "CARERISK_GRADIO_CONTRACT_RAW_SHA256",
)
CUSTODY_VALIDATOR_LINES = (
    '[[ "$CARERISK_GRADIO_CONTRACT_BLOB_SHA1" =~ ^[0-9a-f]{40}$ ]] || exit 1',
    '[[ "$CARERISK_GRADIO_CONTRACT_RAW_SIZE" =~ ^(0|[1-9][0-9]*)$ ]] || exit 1',
    '[[ "$CARERISK_GRADIO_CONTRACT_RAW_SHA256" =~ ^[0-9a-f]{64}$ ]] || exit 1',
)
CUSTODY_VALIDATOR = "\n".join(CUSTODY_VALIDATOR_LINES)
CUSTODY_VARIABLE_REFERENCES = {
    CUSTODY_NAMES[0]: "${{ vars.CARERISK_GRADIO_CONTRACT_BLOB_SHA1 }}",
    CUSTODY_NAMES[1]: "${{ vars.CARERISK_GRADIO_CONTRACT_RAW_SIZE }}",
    CUSTODY_NAMES[2]: "${{ vars.CARERISK_GRADIO_CONTRACT_RAW_SHA256 }}",
}


def _normalized_custody_script(value: str) -> str:
    return "\n".join(
        line.rstrip()
        for line in value.replace("\r\n", "\n").strip().split("\n")
    )


def _custody_step(job: dict[str, Any]) -> dict[str, Any]:
    steps = [step for step in job["steps"] if step.get("id") == "custody"]
    assert len(steps) == 1
    return steps[0]


def _validated_regular_executable(candidate: Path) -> Path:
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise AssertionError(f"custody shell path is unavailable: {candidate}") from exc
    assert resolved.is_file()
    assert os.access(resolved, os.X_OK)
    return resolved


def _windows_shell_path_is_rejected(value: str) -> bool:
    candidate = PureWindowsPath(value)
    folded_parts = {part.casefold() for part in candidate.parts}
    return (
        candidate.name.casefold() != "bash.exe"
        or "system32" in folded_parts
        or "windowsapps" in folded_parts
    )


def _git_for_windows_bash_candidate(git_executable: Path) -> Path:
    git_path = PureWindowsPath(str(git_executable))
    if git_path.name.casefold() != "git.exe":
        raise AssertionError("Windows custody runner requires git.exe")
    if git_path.parent.name.casefold() == "cmd":
        candidate = git_path.parent.parent / "bin" / "bash.exe"
    elif git_path.parent.name.casefold() == "bin":
        candidate = git_path.parent / "bash.exe"
    else:
        raise AssertionError("unsupported Git for Windows executable layout")
    return Path(str(candidate))


def _resolve_custody_bash() -> Path:
    if os.name != "nt":
        located = shutil.which("bash")
        assert located is not None
        return _validated_regular_executable(Path(located))

    located_git = shutil.which("git")
    assert located_git is not None
    git_executable = _validated_regular_executable(Path(located_git))
    candidate = _git_for_windows_bash_candidate(git_executable)
    bash = _validated_regular_executable(candidate)
    assert not _windows_shell_path_is_rejected(str(bash))
    return bash


def _validated_custody_shell() -> tuple[Path, dict[str, str]]:
    bash = _resolve_custody_bash()
    environment = {
        name: value for name, value in os.environ.items() if name not in CUSTODY_NAMES
    }
    sentinel_name = f"CARERISK_CUSTODY_SENTINEL_{uuid.uuid4().hex.upper()}"
    sentinel_value = uuid.uuid4().hex
    sentinel_environment = {**environment, sentinel_name: sentinel_value}
    sentinel_script = f'printf "%s" "${{{sentinel_name}-}}"'
    sentinel = subprocess.run(
        [str(bash), "-c", sentinel_script],
        env=sentinel_environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert sentinel.returncode == 0
    assert sentinel.stdout == sentinel_value
    assert sentinel.stderr == ""
    return bash, environment


def _run_extracted_custody_validator(
    validator: str,
    values: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    bash, environment = _validated_custody_shell()
    environment.update(values)
    return subprocess.run(
        [str(bash), "-c", validator],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_space_ci_transports_external_custody_without_literal_values() -> None:
    workflow_text = SPACE_CI.read_text(encoding="utf-8")
    workflow = yaml.safe_load(workflow_text)
    expected_values = _controller_gradio_contract_identity()
    for job_name in ("source_gates", "candidate_gates"):
        job = workflow["jobs"][job_name]
        assert job["environment"] == CUSTODY_ENVIRONMENT
        assert set(job["env"]) >= set(CUSTODY_NAMES)
        assert {
            name for name in job["env"] if name.startswith("CARERISK_GRADIO_CONTRACT_")
        } == set(CUSTODY_NAMES)
        for name in CUSTODY_NAMES:
            assert job["env"][name] == CUSTODY_VARIABLE_REFERENCES[name]
        assert "continue-on-error" not in job
        custody_step = _custody_step(job)
        assert custody_step["shell"] == "bash"
        assert "if" not in custody_step
        assert "continue-on-error" not in custody_step
        custody_command = _normalized_custody_script(custody_step["run"])
        assert custody_command == CUSTODY_VALIDATOR
        for required_line in CUSTODY_VALIDATOR_LINES:
            assert required_line in custody_command
        guarded_steps = [
            index
            for index, step in enumerate(job["steps"])
            if any(
                token in step.get("run", "")
                for token in ("pytest", "docker run", "verify_hf_space_candidate.py")
            )
        ]
        assert guarded_steps
        assert job["steps"].index(custody_step) < min(guarded_steps)
    source_commands = "\n".join(
        step.get("run", "") for step in workflow["jobs"]["source_gates"]["steps"]
    )
    for name in CUSTODY_NAMES:
        assert f"--env {name}" in source_commands
    for value in (expected_values[0], str(expected_values[1]), expected_values[2]):
        assert value not in workflow_text


def test_custody_shell_runner_rejects_windows_launchers_and_proves_sentinel() -> None:
    assert _windows_shell_path_is_rejected(r"C:\Windows\System32\bash.exe")
    assert _windows_shell_path_is_rejected(
        r"C:\Users\runner\AppData\Local\Microsoft\WindowsApps\bash.exe"
    )
    assert _windows_shell_path_is_rejected(r"C:\Windows\System32\wsl.exe")
    bash, clean_environment = _validated_custody_shell()
    assert bash.is_file()
    assert os.access(bash, os.X_OK)
    assert all(name not in clean_environment for name in CUSTODY_NAMES)


def test_space_ci_executes_the_extracted_custody_validator_fail_closed() -> None:
    workflow = yaml.safe_load(SPACE_CI.read_text(encoding="utf-8"))
    source_validator = _normalized_custody_script(
        _custody_step(workflow["jobs"]["source_gates"])["run"]
    )
    candidate_validator = _normalized_custody_script(
        _custody_step(workflow["jobs"]["candidate_gates"])["run"]
    )
    assert source_validator == candidate_validator == CUSTODY_VALIDATOR

    valid = {
        CUSTODY_NAMES[0]: "a" * 40,
        CUSTODY_NAMES[1]: "1",
        CUSTODY_NAMES[2]: "b" * 64,
    }
    invalid = (
        {},
        {name: value for name, value in valid.items() if name != CUSTODY_NAMES[0]},
        {name: value for name, value in valid.items() if name != CUSTODY_NAMES[1]},
        {name: value for name, value in valid.items() if name != CUSTODY_NAMES[2]},
        {**valid, CUSTODY_NAMES[0]: "A" * 40},
        {**valid, CUSTODY_NAMES[2]: "B" * 64},
        {**valid, CUSTODY_NAMES[1]: "01"},
        {**valid, CUSTODY_NAMES[1]: "+1"},
        {**valid, CUSTODY_NAMES[1]: "-1"},
        {**valid, CUSTODY_NAMES[0]: "g" * 40},
        {**valid, CUSTODY_NAMES[1]: "1.0"},
        {**valid, CUSTODY_NAMES[2]: "g" * 64},
    )
    for values in invalid:
        assert _run_extracted_custody_validator(source_validator, values).returncode != 0
    assert _run_extracted_custody_validator(source_validator, valid).returncode == 0
```

Add the existing-standard-library imports `os`, `shutil`, `subprocess`, and
`uuid`; add `PureWindowsPath` beside the existing `Path` import and `Any` from
`typing`. The test executes the
normalized `run` value extracted
from the parsed workflow, not a replacement validator assembled by the test.
Consequently, echoing regex text, putting validation behind `if`, marking the
step or job `continue-on-error`, or changing `shell: bash` cannot satisfy the
contract. The shape-only positive values above are deliberately not the
controller's real tuple.

Runner resolution is fail closed. POSIX accepts only the resolved regular,
executable result of `shutil.which("bash")`. Windows never resolves `bash`
directly: it resolves `git.exe` from `shutil.which("git")`, accepts only the
documented Git for Windows `cmd\git.exe` or `bin\git.exe` layouts, derives that
installation's `bin\bash.exe`, resolves it strictly, and rejects System32,
WindowsApps, `wsl.exe`, non-files, and non-executables. No machine-specific path
is tracked. Every validator subprocess first repeats the unique-name sentinel;
the sentinel value exists only in that `subprocess.run(env=...)` mapping and must
return exact stdout with exit `0` before any custody case is trusted.

- [ ] **Step 2: Run RED**

The controller injects the three external custody values for this Task 11 local
process. Repeat the exact Tasks 7–13 custody preflight before pytest; local RED
is about the absent workflow, never about absent custody.

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_source_boundary.py tests/test_hf_space_supply_chain.py tests/test_hf_space_exporter.py -q
```

Expected: FAIL because the workflow does not exist.

- [ ] **Step 3: Add the least-privilege workflow with immutable action SHAs**

Resolve official action tag commits read-only and write the resulting real 40-character SHAs directly into the workflow. The `source_gates` job always runs and binds `REVIEWER_IMAGE` to the same exact reviewer tag plus linux/amd64 digest recorded in `base-image.json`. A controlled acquisition step fills an ephemeral wheelhouse from `space/requirements-dev.lock` and rejects every non-matching hash. A separate invocation of that reviewer image uses `--network none`, mounts the repository read-only plus the wheelhouse, installs the development union lock alone with `--no-index --require-hashes --no-deps`, verifies the runtime-package/version subset relation, and runs source/Space/static/supply-chain gates. The job exports a literal `manifest_present` output from an exact Linux check (`if [ -f space/deployment-manifest.json ]; then echo 'present=true' >> "$GITHUB_OUTPUT"; else echo 'present=false' >> "$GITHUB_OUTPUT"; fi`). It never calls manifest generation, export, candidate build, or candidate verification.

That future reviewer invocation also implements one—and only one—of the two
reviewed checkout-ownership modes above. Matching host UID/GID is derived by the
controller from the checkout owner and passed as the exact numeric Docker user;
it is not a candidate-authored constant. If platform constraints require
`safe.directory` instead, the controller resolves the exact mounted checkout
outside repository content, passes only that exact path into the container, and
the reviewer applies only `git -c safe.directory=<exact-resolved-mount> ...` (or
an equivalently isolated controller-created protected config) after equality
validation. It never writes global/system config, consumes `.gitconfig` from the
checkout, accepts multiple directories, or uses `safe.directory=*`. Absence or
validation failure stops before dependency installation, Git inspection, or
pytest. The workflow-contract suite proves the selected transfer and all
negative mutations; remote metadata remains separately blocked.

Both jobs declare `environment: carerisk-contract-custody`. Their tracked `env`
maps contain exactly these custody references and no tuple values:
`${{ vars.CARERISK_GRADIO_CONTRACT_BLOB_SHA1 }}`,
`${{ vars.CARERISK_GRADIO_CONTRACT_RAW_SIZE }}`, and
`${{ vars.CARERISK_GRADIO_CONTRACT_RAW_SHA256 }}`. Before any pytest or Docker
command, a Bash step requires lowercase 40-hex blob SHA-1, canonical unsigned
decimal size, and lowercase 64-hex SHA-256; absent, empty, uppercase, signed,
leading-zero, or otherwise malformed values exit nonzero. The `source_gates`
reviewer `docker run` passes all three explicitly as `--env
CARERISK_GRADIO_CONTRACT_BLOB_SHA1`, `--env
CARERISK_GRADIO_CONTRACT_RAW_SIZE`, and `--env
CARERISK_GRADIO_CONTRACT_RAW_SHA256`; it never bakes them into an image, command
literal, artifact, cache, or log. The candidate verifier receives the same
process environment and must use explicit `--env` forwarding for any reviewer
container that invokes the boundary test. Workflow-contract tests prove the
three-name mapping, both jobs' environment binding, fail-closed preflight,
explicit reviewer-container forwarding, and absence of the controller-supplied
values from tracked workflow text. The Architecture C controller gate also scans
`.github`, `tests`, `space`, `scripts`, and `tools` for tuple-value leakage.

Use this exact custody fragment in each job before its first pytest or Docker
step; `source_gates` then appends the three shown `--env` flags to its reviewer
`docker run` command:

```yaml
environment: carerisk-contract-custody
env:
  CARERISK_GRADIO_CONTRACT_BLOB_SHA1: ${{ vars.CARERISK_GRADIO_CONTRACT_BLOB_SHA1 }}
  CARERISK_GRADIO_CONTRACT_RAW_SIZE: ${{ vars.CARERISK_GRADIO_CONTRACT_RAW_SIZE }}
  CARERISK_GRADIO_CONTRACT_RAW_SHA256: ${{ vars.CARERISK_GRADIO_CONTRACT_RAW_SHA256 }}
steps:
  - id: custody
    shell: bash
    run: |
      [[ "$CARERISK_GRADIO_CONTRACT_BLOB_SHA1" =~ ^[0-9a-f]{40}$ ]] || exit 1
      [[ "$CARERISK_GRADIO_CONTRACT_RAW_SIZE" =~ ^(0|[1-9][0-9]*)$ ]] || exit 1
      [[ "$CARERISK_GRADIO_CONTRACT_RAW_SHA256" =~ ^[0-9a-f]{64}$ ]] || exit 1
  - name: Run source gates in reviewer
    run: >-
      docker run --rm --network none --read-only
      --env CARERISK_GRADIO_CONTRACT_BLOB_SHA1
      --env CARERISK_GRADIO_CONTRACT_RAW_SIZE
      --env CARERISK_GRADIO_CONTRACT_RAW_SHA256
      "$REVIEWER_IMAGE" python -m pytest tests/test_hf_space_source_boundary.py
```

The separate `candidate_gates` job has `needs: source_gates` and the exact condition `${{ needs.source_gates.outputs.manifest_present == 'true' }}`. Thus it is skipped on the app-source commit, where the manifest does not yet exist, and becomes required after the manifest commit exists. Only that job invokes the ownership-safe clean-export verifier, controlled digest/hash-pinned image/dependency acquisition and build, followed by no-egress tests/runtime/browser review and vulnerability/license scan. Neither job uploads artifacts or caches reviewer/browser image bytes. Both jobs forbid image save/export/output/push/upload/publish/deploy commands; the exact reviewer image is ephemeral local/CI-only and is removed only through exact task ownership. Workflow-contract tests assert both branches and mutation-test every forbidden reviewer distribution command/output form. A fabricated, empty, copied, or provisional manifest is forbidden; absence is a normal source-only state, not something CI repairs. Creating/changing Actions Environment values or any other remote metadata remains separately forbidden.

- [ ] **Step 4: Run the complete app-source verification locally**

The controller reinjects the same three values into this fresh local process and
the exact Tasks 7–13 custody preflight must pass before the combined pytest run.

```powershell
$env:PYTHONNOUSERSITE = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:CUDA_VISIBLE_DEVICES = ''
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests tests/test_hf_space_source_boundary.py tests/test_hf_space_supply_chain.py tests/test_hf_space_exporter.py tests/test_hf_space_live_review.py -p no:cacheprovider
.venv-space\Scripts\ruff.exe check space scripts/build_hf_space_supply_chain.py scripts/export_hf_space.py scripts/review_hf_space_local.py scripts/verify_hf_space_candidate.py tests/test_hf_space_source_boundary.py tests/test_hf_space_supply_chain.py tests/test_hf_space_exporter.py tests/test_hf_space_live_review.py
.venv-space\Scripts\mypy.exe --strict space/carerisk_space scripts/build_hf_space_supply_chain.py scripts/export_hf_space.py scripts/review_hf_space_local.py scripts/verify_hf_space_candidate.py
.venv-space\Scripts\python.exe -m pip check
git diff --check
```

Expected: every app-source gate is green before defining its provenance SHA. No unpinned `pre-commit` executable is invoked; Ruff, Mypy, pytest, the exact workflow/file-list tests, and `git diff --check` provide the equivalent source gates using already declared tooling.

- [ ] **Step 5: Commit the workflow and designate the resulting commit**

```powershell
git add -- .github/workflows/space-ci.yml tests/test_hf_space_source_boundary.py tests/test_hf_space_supply_chain.py tests/test_hf_space_exporter.py
git diff --cached --check
git commit -m 'ci(space): verify clean public candidate'
$appSourceSha = (git rev-parse HEAD).Trim()
if ($appSourceSha -notmatch '^[0-9a-f]{40}$') { throw 'Invalid app source SHA' }
```

This commit is the app-source commit. No application, test, lock, SBOM, license, exporter, Docker, or workflow file may change after this point without discarding the manifest task and designating a new app-source commit.

### Task 12: Create the second, non-self-referential deployment-manifest commit

**Files:**
- Create: `space/deployment-manifest.json`

**Interfaces:**
- Consumes: the immediately preceding app-source commit and exact tag objects.
- Produces: canonical manifest bytes that name the app-source commit but not their own commit.

- [ ] **Step 1: Verify the source boundary is clean and immutable**

```powershell
$appSourceSha = (git rev-parse HEAD).Trim()
if (@(git status --porcelain=v1 --untracked-files=all).Count -ne 0) { throw 'Dirty source before manifest generation' }
if ((git rev-parse 'v0.2.0^{tag}').Trim() -cne '2f1ddb0e2276fa894e124b856de488e31e21e88c') { throw 'Tag object mismatch' }
if ((git rev-parse 'v0.2.0^{}').Trim() -cne 'f4c820cce953f401c1ec525bd8df3a3c1678bbf3') { throw 'Tag commit mismatch' }
if ((git rev-parse 'v0.2.0:docs/final-result-receipt.json').Trim() -cne 'b13ec7655bbdb8db1079c3b4793a0bf5590ef69c') { throw 'Receipt blob mismatch' }
if ((git cat-file -s 'v0.2.0:docs/final-result-receipt.json').Trim() -cne '3363') { throw 'Receipt byte size mismatch' }
```

- [ ] **Step 2: Generate the real manifest from committed objects**

```powershell
.venv-space\Scripts\python.exe scripts/export_hf_space.py manifest --repo-root . --app-source-sha $appSourceSha --output space/deployment-manifest.json
```

Expected: canonical JSON records `space_app_source_git_sha`, tag/object/commit, destination, base image, locks, SBOM/licenses, every source/destination path, capability, byte size, and SHA-256. Its own allowlist entry has no self-hash, and it has no destination commit field.

- [ ] **Step 3: Run manifest RED/GREEN relationship tests against the uncommitted file**

```powershell
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests/test_evidence_contract.py space/tests/test_export_contract.py tests/test_hf_space_exporter.py -q
.venv-space\Scripts\python.exe scripts/export_hf_space.py verify-manifest --repo-root . --app-source-sha $appSourceSha --manifest space/deployment-manifest.json
```

Expected: manifest relation, hashes, exact paths, and non-self-reference pass.

- [ ] **Step 4: Commit only the deployment manifest**

```powershell
$stagedBefore = @(git diff --cached --name-only)
if ($stagedBefore.Count -ne 0) { throw 'Unexpected staged paths' }
git add -- space/deployment-manifest.json
$staged = @(git diff --cached --name-only)
if ($staged.Count -ne 1 -or $staged[0] -ne 'space/deployment-manifest.json') { throw 'Manifest commit scope mismatch' }
git diff --cached --check
git commit -m 'chore(space): bind deployment provenance manifest'
$manifestSourceSha = (git rev-parse HEAD).Trim()
if ((git rev-parse HEAD^).Trim() -cne $appSourceSha) { throw 'Manifest is not the immediate second commit' }
```

### Task 13: Run full final verification from a clean export

**Files:**
- Verify only: every file named above.
- Temporary only: one ownership-marked GUID run root beneath the resolved OS temp root, containing candidate, review, and four code-specific `NEVER_DEPLOY` build-context children.

**Interfaces:**
- Consumes: app-source SHA from `deployment-manifest.json` and current manifest-source SHA.
- Consumes: the complete Task 7 `WebKitReviewerPolicy` value, including Playwright tag URL, tagged `browsers.json`, registry source, CDN artifact, external tag-commit/source-relative-path/raw-byte/parsed-assignment provenance, WebKit tree algorithm/digest and image-tree absence proof, and ordered official licensing references; abbreviated tuples are invalid.
- Produces: a final JSON receipt on stdout after ownership-safe cleanup, including the complete WebKit metadata tuple, the exact closed eleven-member distribution-surface registry, and an integer zero reviewer-byte count for each surface; no tracked change and no commit.
- Owns: first-party `carerisk-space@0.2.0` source/bundle exact hashes and final receipt/SBOM identity; Task 7's trust root and dependency artifacts are external-only.

Before Task 13 implementation can be considered ready, `tests/test_hf_space_live_review.py` must contain `test_final_receipt_binds_complete_webkit_reviewer_policy_tuple`, `test_final_verifier_rejects_reviewer_bytes_on_each_distribution_surface`, `test_final_receipt_requires_zero_count_for_each_distribution_surface`, `test_final_verifier_rejects_nonclosed_distribution_surface_registry`, `test_final_receipt_records_bounded_task7_source_reference_lifecycle_evidence`, and `test_final_receipt_excludes_transient_source_reference_execution_fields`. The first test mutates every tuple/provenance field independently, including `playwright_tag_commit`, `repository_relative_path`, `commit_pinned_raw_url`, `raw_byte_length`, `raw_sha256`, `remote_url`, `base_branch`, `base_revision`, `playwright_tag_url`, and `webkit_tree_algorithm`; it also rejects a source filename represented as an image-tree member. The bounded lifecycle test requires the exact canonical evidence object `{controller_owned_acquisition: true, exact_https_get_count: 1, redirect_count: 0, raw_body_retained: false, offline_phase: "offline_verify", network_bomb_before_work: true, shared_cleanup_validator: true, cleanup_mutation_matrix_passed: true}` and rejects any missing/extra/type/value drift. The receipt-exclusion test proves the Task 13 receipt carries only the sanctioned policy tuple/derived absence proof and this bounded lifecycle object—never a transient source-reference path, raw body, run GUID, task temp name, or command-line flag value. The next two parameterize all eleven surfaces: `public_export`, `candidate`, `runtime_stage`, `final_image`, `deployment_artifact`, `saved_archive`, `pushed_image`, `uploaded_artifact`, `published_image`, `build_output`, and `other_distributed_output`. The registry test rejects an omitted, duplicate, unknown, empty, or unclassified member. These tests run in the Task 13 pytest command in Step 3 and must fail before the receipt/verifier contract is complete.

- [ ] **Step 1: Verify clean two-commit inputs before creating any temporary path**

```powershell
$dirty = @(git status --porcelain=v1 --untracked-files=all)
if ($dirty.Count -ne 0) { throw 'Final verification requires a clean worktree' }
$manifest = Get-Content -Raw -LiteralPath space/deployment-manifest.json | ConvertFrom-Json
$appSourceSha = ([string]$manifest.space_app_source_git_sha).Trim()
$manifestSourceSha = (git rev-parse HEAD).Trim()
if ($appSourceSha -notmatch '^[0-9a-f]{40}$' -or $manifestSourceSha -notmatch '^[0-9a-f]{40}$') { throw 'Invalid provenance SHA' }
if ((git rev-parse "$manifestSourceSha^").Trim() -cne $appSourceSha) { throw 'Manifest is not the immediate second commit' }
.venv-space\Scripts\python.exe scripts/export_hf_space.py verify-manifest --repo-root . --app-source-sha $appSourceSha --manifest space/deployment-manifest.json
```

Expected: the worktree is clean, SHAs are exact 40-character values, the current commit immediately follows the app-source commit, and the committed manifest verifies before any export/build/review action.

- [ ] **Step 2: Run the ownership-safe phased candidate verifier**

```powershell
$output = @(.venv-space\Scripts\python.exe scripts/verify_hf_space_candidate.py --repo-root (Resolve-Path .).Path --app-source-sha $appSourceSha --manifest-source-sha $manifestSourceSha)
if ($LASTEXITCODE -ne 0) { throw "Candidate verification failed: $($output -join [Environment]::NewLine)" }
$receipt = $output[-1] | ConvertFrom-Json
if ($receipt.schema_version -ne 1 -or $receipt.status -cne 'passed') { throw 'Invalid final verification receipt' }
```

`verify_hf_space_candidate.py` implements these ordered phases inside one ownership-marked GUID run root and a `try/finally`:

1. Re-check clean-worktree and two-commit preconditions. Create `candidate` and `review` children only beneath the owned run root. Run exporter and `verify-export` before any controlled acquisition/build command. Export code is restricted by source tests to local Git object reads and has no networking API/import/call path.
2. Read both exact tag/platform-digest records from `base-image.json`. For each, run `docker image inspect` against the concatenated recorded tag and linux/amd64 digest and verify `RepoDigests`; if and only if that exact image is absent, perform a logged controlled `docker pull` of the same immutable reference, then re-inspect. Reject a tag-only or wrong-platform image. This is controlled supply-chain acquisition, not test execution.
3. In the same controlled supply-chain/build phase, build `--target test` and `--target runtime` from the exact candidate. Network access is permitted only for digest/hash-pinned base and Python package acquisition and every accepted byte must match the image digest or lock hash. `--pull=false` may be used only after exact local image verification and is never evidence that the build was offline. Verify built image histories/inventories: test uses the reviewer base; runtime uses only the CPython base and contains no dev/browser/model package. The build command has no `--push`, registry/OCI/Docker `--output`, exporter, saver, uploader, or publisher. The test image is retained only as an exact task-owned local/CI resource and may not be emitted or persisted outside that local engine.
4. End the acquisition/build phase. Before execution, validate the exact WebKit exception record and independently classify and inspect every member of the closed distribution registry: public export, candidate build context, runtime-stage history/filesystem, final image history/filesystem, deployment artifacts/mapping, saved-archive plan, pushed-image plan, upload plan, publication plan, emitted build-output plan, and the mandatory other-distributed-output catchall. Independently inspect planned Docker commands as command-path evidence. An unavailable path is represented by its named surface with authoritative evidence that no such mechanism exists and a zero byte count; it is never omitted. The only allowed WebKit occurrence outside the ephemeral reviewer/test image is the metadata-only record in `SBOM.spdx.json` and `THIRD_PARTY_LICENSES.json`; every other reviewer/browser/support byte signature or artifact path fails. Run all six public tests and `pip check` from the standalone test image with `docker run --network none --cpus=2`. Inventory `/usr/bin/env` in the final runtime and its owning Debian package/version, then run UID/GID/nologin/read-only/tmpfs/CPU smoke and three cold starts with `--network none`. Every runtime start passes adversarial values for the exact Gradio `6.26.0` source-derived environment-read inventory. The required named matrix includes `GRADIO_ANALYTICS_ENABLED`, `HF_HUB_DISABLE_TELEMETRY`, `GRADIO_WATCH_DIRS`, `GRADIO_VIBE_MODE`, `GRADIO_HOT_RELOAD`, `GRADIO_RUN_HISTORY`, `GRADIO_SSR_MODE`, `GRADIO_MCP_SERVER`, `GRADIO_ALLOWED_PATHS`, `GRADIO_BLOCKED_PATHS`, `GRADIO_ROOT_PATH`, `GRADIO_SHARE`, `GRADIO_MONITORING_ENABLED`, `GRADIO_DEBUG`, `GRADIO_SERVER_NAME`, `GRADIO_SERVER_PORT`, `GRADIO_NUM_WORKERS`, `GRADIO_NODE_PATH`, `GRADIO_LOCAL_DEV_MODE`, and `GRADIO_NODE_SERVER_PORT`, plus `SPACE_ID`, `PORT`, and a secret-shaped canary. Inspect pre-import state, post-Blocks state, `/proc/1/environ`, and every runtime child environment and require exact equality with the fixed `ENTRYPOINT` allowlist, including `HF_HUB_DISABLE_TELEMETRY=True`; poison values `0` and hostile strings must be absent. Prove fixed port 7860, zero app-owned input/dependency/function/API config, pinned `enable_queue == true`, zero public state delta, mount mapping, exact two-argument direct outer-wrapper identity with nonempty pinned-root membership, and exact programmatic Uvicorn `http="h11"`; reject `auto`, `httptools`, CLI/environment selection, or inference from an absent package. Derive sorted package membership/content-tree digests from the exact runtime wheel and compare them with the reviewer image; require only regular non-symlink root-contained members. Against loopback Host `127.0.0.1:7860`, require healthy exact root/config/theme/manifest/favicon/package members and logo digests plus unavailable API/queue/history/monitoring. Direct pure-ASGI probes require the fixed guard 404 message sequence with `b"Not Found"` and `content-length: 9` before FastAPI/Gradio/downstream/body receive for the complete hostile method/path/query/authority/header/cookie/raw-path/WebSocket matrix, including `HEAD` on every non-root path, syntactically valid nonexistent assets, metadata/PWA variants, and missing/duplicate/combined/whitespace/unlisted Host scopes. Separately send raw HTTP/1.1 bytes to the untouched explicitly configured Uvicorn+h11 server: missing and duplicate Host must each return exact 400 with no ASGI app-entry marker delta, while a valid unlisted single Host must enter the guard and return 404. Wire-level blocked non-root `HEAD` must return 404 with zero entity bytes and `content-length: 9`; root `HEAD` remains the sole allowed HEAD and also has zero wire entity bytes. Record zero CORS/compression, canary/reflection, outbound fetches, temp delta, and echo at each layer. Sentinel/root-block/max-upload remain separate defense-in-depth observations. No execution-phase command downloads a dependency.
5. Inspect and record the exact final runtime image digest before creating any variant. Generate four literal task-owned Dockerfiles and minimal contexts for only `receipt_missing`, `receipt_hash_mismatch`, `release_relationship_invalid`, and `deployment_manifest_invalid`. Each uses `FROM <exact local final digest>`, `--pull=false --network=none`, the complete exact ownership labels GUID/`resource_role=failure_variant`/base digest/code/`NEVER_DEPLOY=true`, exact local reference `carerisk-local:<GUID>-NEVER_DEPLOY-<code>`, temporary `USER 0`, one literal package-relative evidence removal/replacement, and final `USER 10001:10001`. Reject remote registries, caller-controlled images/paths/Dockerfiles/commands, bind mounts, environment/path injection, push, save, export/output, or any fifth variant. After each successful build, freshly inspect the exact local reference and require exactly one intended evidence-path delta, exact entrypoint/CMD/app-source/lock/asset/other-path byte parity with the final image, and exactly its own expected failure code. Only then create and controller-retain the code's immutable `FailureVariantRecord` containing exact reference, inspected image ID/content digest, final base digest, code, GUID, labels, and inspection evidence. A record may not be synthesized from a later label lookup. `receipt_schema_invalid` receives no image: its strict-parser/UI/ASGI behavior is exercised only with the existing explicit unit test anchor seam, while the final receipt records that live bytes are dominated by the immutable receipt identity gate and marks it `not_live_reviewed`.
6. Create the Docker `--internal` network with the complete ownership labels exact current GUID plus `resource_role=network`. Run the exact final image with network alias `carerisk-app` in a normal container labeled exact GUID/`resource_role=normal`/exact final-image digest, then separately run each retained variant reference in a container named exactly `carerisk-<GUID>-NEVER_DEPLOY-<code>` and labeled exact GUID/`resource_role=failure_variant`/exact base digest/code/`NEVER_DEPLOY=true`, all with the same alias, entrypoint, command, environment scrub, runtime flags, and no-egress network. Normal, reviewer, and network resource names must not contain `NEVER_DEPLOY`. Run the exact reviewer image in a container labeled exact GUID/`resource_role=reviewer`/exact reviewer-image digest against `http://carerisk-app:7860` for all five live page states at 1440×900 and 390×844. The reviewer container is local/CI-only, ephemeral, and is never committed, saved, exported, pushed, uploaded, published, or deployed. Apply shared assertions to all ten records; apply four-radio/panel/keyboard/focus/visibility/normal-claims assertions only to the two normal records; apply zero-control/panel/transition/metric/canonical-value plus exact code/message assertions only to the eight reachable-failure records. Verify root/config/exact theme/manifest/favicon/package members, exact membership/tree digest parity, zero app-owned inputs/dependencies/functions/API, pinned `enable_queue == true`, exact request method/path/query, zero outer blocks/POST/event/session/queue/public-state delta/external/console errors, and no partial evidence/download/model initialization. Separately repeat URL/local-file, zero/nonzero/oversized upload, body-framing, hostile authority/query/cookie/header, CORS/Brotli, WebSocket, dangerous-family, metadata/PWA, absent-asset, encoded, traversal, case, and slash probes. Missing/duplicate raw-wire Host and blocked-wire-HEAD evidence remains layer-separated. Any route, parser, variant, delta, authority, asset, state, or assertion drift stops verification for exact source audit, RED test, and central review; no wildcard or fifth live failure is added.
7. In `finally`, enumerate only the literal resource IDs recorded by the current run and freshly inspect each one before deletion. Dispatch by Docker resource type and validate the complete exact reserved ownership-label schema, current GUID, role, identity/reference, and applicable final/reviewer/base digest and failure code. For failure images and containers, retrieve the controller-retained expected record by code and independently compare the actual image reference, image ID, and content digest to it; for a container, also require Docker `.Image` and configured image reference to identify that same record. Labels are necessary but insufficient. Tests with labels/base/code left correct but variant digest swapped, reference changed, container `.Image` wrong, or configured image reference wrong must fail closed and preserve the resource. Failure-container names must exactly match `carerisk-<GUID>-NEVER_DEPLOY-<code>`; normal/reviewer/network names must omit `NEVER_DEPLOY`. Normal, reviewer, and network resources never carry or are validated as failure variants. Missing retained records, missing or extra contradictory labels, ambiguous reference/identity, stale GUID, digest/code/reference mismatch, or type/role/name mismatch fails closed and preserves that resource. Only after every Docker resource passes its own schema may the verifier validate and delete the current ownership-marked temp run root. Emit the JSON receipt after cleanup. Any cleanup validation failure is itself a failed run and leaves the suspect resource/path untouched for manual inspection; it never uses broad filters or broadens the delete target.

Expected: the candidate has exactly the 24 paths in `PUBLIC_PATHS`, no `.git`, no extra bytes, and every file matches its manifest source/hash/size relationship. Linux tests run only in the reviewer image from the standalone candidate; the Windows host never attempts to install a Linux-only lock. The exact reviewer image remains local/CI-only and no save/export/output/push/upload/publication/deployment path exists. All eleven closed surfaces and the Docker command plan contain no reviewer/browser bytes; upload, publication, build-output, and other-distributed-output absence is recorded explicitly rather than inferred from omission. Only the exact metadata-only WebKit record is present in the two inventory documents. The final receipt includes the exact tag/index/manifest/Playwright tag and tag URL/tagged `browsers.json`/registry/CDN, external tag commit/source-relative-path/commit-pinned raw URL/raw length/raw SHA-256/parsed `REMOTE_URL`/`BASE_BRANCH`/`BASE_REVISION`, explicit immutable-image-tree absence proof, WebKit revision/version/tree algorithm/tree digest/ordered licensing-reference tuple, both SPDX `NOASSERTION` values, `reviewer_test_only_not_redistributed`, `complete_digest_bound_notice=false`, and the exact bounded Task 7 lifecycle object proving controller ownership, one GET/no redirect, no retained raw body, offline verification, bomb-before-work, one shared cleanup validator, and the passed cleanup mutation matrix without exposing a transient path/GUID/flag value. It also includes the exact eleven-member surface registry, every named exclusion gate, and eleven integer-zero reviewer-byte observations, in addition to clean-export tree digest; both base/platform digests; lock/SBOM/license hashes; test counts; runtime and four derived image digests; exact parser identity `h11`; `/usr/bin/env` inventory; exact pre-import/post-Blocks/PID 1/child environments; poisoned-environment behavior; zero app-owned input/dependency/function/API observations; pinned `config.enable_queue == true`; zero public-interaction state delta; parent/inner registered-route classification; mount/exact-two-argument-outer-wrapper/Uvicorn identity; four-authority map and exact sanitized scopes; package membership counts/tree digests in runtime and reviewer; exact manifest/favicon/logo body hashes; exact browser method/path/query graph; accepted metadata counts; guard-block/POST/event/session/queue/external/console counts; normal-only static radio visibility transitions; failure-only zero-surface counts; direct-ASGI fixed Host/HEAD message evidence; pinned Uvicorn+h11 missing/duplicate Host 400 statuses and zero app-entry delta; valid-unlisted-Host guard 404 evidence; blocked wire HEAD zero-entity/content-length evidence; blocked-probe downstream/receive/CORS/compression/fetch/temp/echo counts; defense-in-depth state; history/monitoring results; three normal cold starts; ten viewport/state records; four controller-retained variant reference/ID/digest/base/code/GUID/label/delta records; five-code owning-gate/live-reachability/evidence-type/precedence/status records; exact role-specific normal/reviewer/network/failure cleanup records including failure container names and actual image/container-to-record identity comparisons; and no-egress observations. `receipt_schema_invalid` is recorded as unit/component/ASGI evidence with its exact three-part failure copy and sole bounded code, dominated by the immutable receipt anchor, and `not_live_reviewed`, never as a passed live state. Parser-layer 400s are never labeled as guard executions. If `/usr/bin/env -i`, the explicit h11 parser, direct outer ASGI/authority boundary, exact package membership, accepted Host identity, WebKit exception/exclusion boundary, or role-specific cleanup identity is absent, ineffective, ambiguous, or incompatible with the Hugging Face Docker Space runtime, verification stops and the threat boundary is not weakened.

- [ ] **Step 3: Re-run legacy baseline and source-only final gates after candidate cleanup**

The controller injects the three external custody values for this final local
Task 13 process. Repeat the exact Tasks 7–13 custody preflight before either
pytest command that includes the boundary suite.

```powershell
$env:PYTHONNOUSERSITE = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:CUDA_VISIBLE_DEVICES = ''
$env:OMP_NUM_THREADS = '2'
$env:MKL_NUM_THREADS = '2'
.venv-space\Scripts\python.exe -m pytest -m 'not integration and not slow' -p no:cacheprovider
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_source_boundary.py tests/test_hf_space_supply_chain.py tests/test_hf_space_exporter.py tests/test_hf_space_live_review.py -p no:cacheprovider
.venv-space\Scripts\ruff.exe check .
.venv-space\Scripts\mypy.exe
.venv-space\Scripts\python.exe -m pip check
```

Expected: the existing repository suite and all Space source-only gates pass. No Set B, data, artifact, model, download, training, evaluation, or receipt-generation command is invoked.

- [ ] **Step 4: Assert the final receipt proves all container/live gates and cleanup**

```powershell
$requiredTrue = @(
    'public_tests_passed', 'runtime_inventory_clean', 'runtime_network_none',
    'runtime_read_only', 'runtime_non_root_nologin', 'runtime_env_binary_inventoried',
    'runtime_environment_scrubbed', 'runtime_fixed_port',
    'runtime_uvicorn_h11_exact',
    'runtime_public_surface_guard_pre_router', 'runtime_history_monitoring_closed',
    'runtime_telemetry_value_exact', 'runtime_authority_map_exact',
    'runtime_package_asset_membership_exact', 'runtime_reviewer_asset_tree_match',
    'runtime_manifest_exact', 'runtime_favicon_exact', 'runtime_logo_exact',
    'pure_asgi_host_404_exact', 'pure_asgi_blocked_body_exact',
    'wire_host_parser_400_exact', 'wire_blocked_head_entity_empty',
    'wire_blocked_head_content_length_exact', 'valid_unlisted_host_guard_404',
    'framework_enable_queue_true_recorded', 'app_owned_api_surface_zero',
    'browser_request_allowlist_exact', 'browser_network_internal',
    'browser_reviewer_alias_exact', 'browser_metadata_requests_observed',
    'failure_variants_final_digest_derived', 'failure_variant_single_deltas_exact',
    'failure_variant_labels_exact', 'failure_variant_records_exact',
    'failure_container_names_exact', 'failure_taxonomy_precedence_exact',
    'cleanup_normal_role_exact', 'cleanup_reviewer_role_exact',
    'cleanup_network_role_exact', 'cleanup_failure_variant_roles_exact',
    'cleanup_failure_variant_image_identity_exact',
    'cleanup_failure_variant_container_identity_exact',
    'cleanup_ambiguous_resources_preserved',
    'webkit_reviewer_exception_tuple_exact',
    'webkit_spdx_declared_noassertion_exact',
    'webkit_spdx_concluded_noassertion_exact',
    'webkit_reviewer_test_only_not_redistributed_exact',
    'webkit_complete_digest_bound_notice_false',
    'public_export_approved_bytes_only', 'distribution_surface_registry_exact',
    'candidate_reviewer_bytes_absent', 'runtime_stage_reviewer_bytes_absent',
    'final_image_reviewer_bytes_absent', 'deployment_artifact_reviewer_bytes_absent',
    'saved_archive_reviewer_bytes_absent', 'pushed_image_reviewer_bytes_absent',
    'uploaded_artifact_reviewer_bytes_absent', 'published_image_reviewer_bytes_absent',
    'build_output_reviewer_bytes_absent', 'other_distributed_output_reviewer_bytes_absent',
    'reviewer_distribution_commands_absent',
    'accessibility_passed', 'cleanup_passed'
)
foreach ($field in $requiredTrue) {
    if ($receipt.$field -ne $true) { throw "Final receipt gate failed: $field" }
}
if ($receipt.cold_starts -ne 3 -or $receipt.viewport_count -ne 2 -or $receipt.page_state_count -ne 5 -or $receipt.live_review_record_count -ne 10 -or $receipt.failure_variant_count -ne 4 -or $receipt.scenario_count -ne 4) { throw 'Final review matrix mismatch' }
$expectedLiveStates = @('validated_normal', 'receipt_missing', 'receipt_hash_mismatch', 'release_relationship_invalid', 'deployment_manifest_invalid')
if ([string]::Join('|', [string[]]@($receipt.live_page_states)) -cne [string]::Join('|', [string[]]$expectedLiveStates)) { throw 'Live page-state matrix mismatch' }
$expectedVariantCodes = @('receipt_missing', 'receipt_hash_mismatch', 'release_relationship_invalid', 'deployment_manifest_invalid')
if ([string]::Join('|', [string[]]@($receipt.failure_variant_codes)) -cne [string]::Join('|', [string[]]$expectedVariantCodes)) { throw 'Failure variant matrix mismatch' }
$variantRecords = @($receipt.failure_variant_records)
if ($variantRecords.Count -ne 4) { throw 'Failure variant record count mismatch' }
$cleanupRecords = @($receipt.failure_cleanup_records)
if ($cleanupRecords.Count -ne 4) { throw 'Failure cleanup record count mismatch' }
foreach ($code in $expectedVariantCodes) {
    $matching = @($variantRecords | Where-Object { ([string]$_.expected_failure_code) -ceq $code })
    if ($matching.Count -ne 1) { throw "Failure variant record missing or duplicated: $code" }
    $record = $matching[0]
    $expectedReference = "carerisk-local:$($receipt.run_guid)-NEVER_DEPLOY-$code"
    if ([string]$record.run_guid -cne [string]$receipt.run_guid) { throw "Failure variant GUID mismatch: $code" }
    if ([string]$record.image_reference -cne $expectedReference) { throw "Failure variant reference mismatch: $code" }
    if ([string]$record.image_id -notmatch '^sha256:[0-9a-f]{64}$') { throw "Failure variant image ID invalid: $code" }
    if ([string]$record.image_digest -cne [string]$record.image_id) { throw "Failure variant image digest mismatch: $code" }
    if ([string]$record.base_final_image_digest -cne [string]$receipt.runtime_image_digest) { throw "Failure variant base digest mismatch: $code" }

    $cleanupMatching = @($cleanupRecords | Where-Object { ([string]$_.expected_failure_code) -ceq $code })
    if ($cleanupMatching.Count -ne 1) { throw "Failure cleanup record missing or duplicated: $code" }
    $cleanup = $cleanupMatching[0]
    $expectedContainerName = "carerisk-$($receipt.run_guid)-NEVER_DEPLOY-$code"
    if ([string]$cleanup.run_guid -cne [string]$receipt.run_guid -or
        [string]$cleanup.container_name -cne $expectedContainerName -or
        [string]$cleanup.expected_image_reference -cne [string]$record.image_reference -or
        [string]$cleanup.expected_image_id -cne [string]$record.image_id -or
        [string]$cleanup.expected_image_digest -cne [string]$record.image_digest -or
        [string]$cleanup.actual_image_reference -cne [string]$record.image_reference -or
        [string]$cleanup.actual_image_id -cne [string]$record.image_id -or
        [string]$cleanup.actual_image_digest -cne [string]$record.image_digest -or
        [string]$cleanup.container_image_id -cne [string]$record.image_id -or
        [string]$cleanup.container_config_image_reference -cne [string]$record.image_reference -or
        $cleanup.labels_exact -ne $true) {
        throw "Failure cleanup identity mismatch: $code"
    }
}
$expectedCleanupRoles = @('normal', 'reviewer', 'network', 'failure_variant')
if ([string]::Join('|', [string[]]@($receipt.cleanup_resource_roles)) -cne [string]::Join('|', [string[]]$expectedCleanupRoles)) { throw 'Cleanup role matrix mismatch' }
if ([string]$receipt.cleanup_normal_final_image_digest -cne [string]$receipt.runtime_image_digest) { throw 'Normal cleanup digest mismatch' }
if ([string]$receipt.cleanup_reviewer_image_digest -cne [string]$receipt.reviewer_image_digest) { throw 'Reviewer cleanup digest mismatch' }
if ($receipt.cleanup_failure_variant_resource_count -ne 8) { throw 'Failure cleanup resource count mismatch' } # four images + four containers
$expectedWebKit = [ordered]@{
    reviewer_image_tag = 'mcr.microsoft.com/playwright/python:v1.62.0-noble'
    reviewer_index_digest = 'sha256:aa81288e738725378becba5b3e06cb0f3a7f012a610e87e8d767a090ea3f740d'
    reviewer_linux_amd64_digest = 'sha256:51d31fdfacb0cff99a1a724152e34ae408d2bd4e7da310ff157450f49261cc59'
    playwright_version = '1.62.0'
    playwright_tag = 'v1.62.0'
    playwright_tag_url = 'https://github.com/microsoft/playwright/tree/v1.62.0'
    browsers_json_url = 'https://github.com/microsoft/playwright/blob/v1.62.0/packages/playwright-core/browsers.json'
    registry_source_url = 'https://github.com/microsoft/playwright/blob/v1.62.0/packages/playwright-core/src/server/registry/index.ts'
    cdn_artifact_url = 'https://cdn.playwright.dev/dbazure/download/playwright/builds/webkit/2336/webkit-ubuntu-24.04.zip'
    playwright_tag_commit = 'e3950d9c140d007bd52853b45813c6274b24e36f'
    repository_relative_path = 'browser_patches/webkit/UPSTREAM_CONFIG.sh'
    commit_pinned_raw_url = 'https://raw.githubusercontent.com/microsoft/playwright/e3950d9c140d007bd52853b45813c6274b24e36f/browser_patches/webkit/UPSTREAM_CONFIG.sh'
    raw_byte_length = 126
    raw_sha256 = '3554c5b666ed87032fb22e78956f8a2fffe1faede63ae8dcae60a26961f6419c'
    remote_url = 'https://github.com/WebKit/WebKit.git'
    base_branch = 'main'
    base_revision = '343e13bf22dca9d0ec227801419aab0f9001a32f'
    webkit_revision = '2336'
    webkit_version = '26.5'
    webkit_tree_file_count = 38
    webkit_tree_total_bytes = 306401261
    webkit_tree_algorithm = 'sha256-canonical-tree-v1'
    webkit_tree_sha256 = 'c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c'
    image_tree_source_relative_path_absence_proof = @{ repository_relative_path = 'browser_patches/webkit/UPSTREAM_CONFIG.sh'; canonical_tree_algorithm = 'sha256-canonical-tree-v1'; canonical_tree_file_count = 38; canonical_tree_total_bytes = 306401261; canonical_tree_sha256 = 'c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c'; present = $false }
    official_webkit_licensing_references = @(
        'https://webkit.org/licensing-webkit/',
        'https://github.com/WebKit/WebKit/blob/343e13bf22dca9d0ec227801419aab0f9001a32f/Source/WebCore/LICENSE-APPLE',
        'https://github.com/WebKit/WebKit/blob/343e13bf22dca9d0ec227801419aab0f9001a32f/Source/WebCore/LICENSE-LGPL-2'
    )
    license_declared = 'NOASSERTION'
    license_concluded = 'NOASSERTION'
    review_disposition = 'reviewer_test_only_not_redistributed'
    complete_digest_bound_notice = $false
}
$actualWebKitJson = $receipt.webkit_reviewer_policy_tuple | ConvertTo-Json -Compress -Depth 5
$expectedWebKitJson = $expectedWebKit | ConvertTo-Json -Compress -Depth 5
if ($actualWebKitJson -cne $expectedWebKitJson) { throw 'Exact complete WebKit reviewer policy tuple mismatch' }
$expectedDistributionSurfaces = @('public_export', 'candidate', 'runtime_stage', 'final_image', 'deployment_artifact', 'saved_archive', 'pushed_image', 'uploaded_artifact', 'published_image', 'build_output', 'other_distributed_output')
if ([string]::Join('|', [string[]]@($receipt.distribution_surface_names)) -cne [string]::Join('|', [string[]]$expectedDistributionSurfaces)) { throw 'Distribution surface registry mismatch' }
foreach ($field in @(
    'public_export_reviewer_byte_count', 'candidate_reviewer_byte_count',
    'runtime_stage_reviewer_byte_count', 'final_image_reviewer_byte_count',
    'deployment_artifact_reviewer_byte_count', 'saved_archive_reviewer_byte_count',
    'pushed_image_reviewer_byte_count', 'uploaded_artifact_reviewer_byte_count',
    'published_image_reviewer_byte_count', 'build_output_reviewer_byte_count',
    'other_distributed_output_reviewer_byte_count', 'reviewer_distribution_command_count'
)) {
    if ($receipt.$field -ne 0) { throw "Reviewer-only bytes crossed distribution boundary: $field" }
}
$expectedReachability = @(
    'receipt_missing|literal_receipt_path|true|final_image_variant|runtime_reachable|reviewed',
    'receipt_hash_mismatch|immutable_receipt_sha256_git_blob|true|final_image_variant|runtime_reachable|reviewed',
    'receipt_schema_invalid|strict_receipt_json_schema_after_identity|false|unit_component_asgi|dominated_by_immutable_receipt_anchor|not_live_reviewed',
    'release_relationship_invalid|release_relationship|true|final_image_variant|runtime_reachable|reviewed',
    'deployment_manifest_invalid|deployment_manifest|true|final_image_variant|runtime_reachable|reviewed'
)
$actualReachability = @($receipt.evidence_reachability | ForEach-Object {
    "$($_.failure_code)|$($_.owning_gate)|$(([bool]$_.live_reachable).ToString().ToLowerInvariant())|$($_.evidence_type)|$($_.precedence)|$($_.live_review_status)"
})
if ([string]::Join("`n", [string[]]$actualReachability) -cne [string]::Join("`n", [string[]]$expectedReachability)) { throw 'Failure reachability/precedence matrix mismatch' }
foreach ($field in @('blocked_downstream_call_count', 'blocked_receive_call_count', 'blocked_outbound_fetch_count', 'blocked_temp_entry_delta', 'blocked_echo_count', 'wire_host_parser_app_entry_delta', 'wire_host_parser_canary_or_reflection_count', 'browser_middleware_blocked_count', 'browser_post_request_count', 'browser_event_or_session_request_count', 'browser_queue_request_count', 'public_interaction_state_delta', 'external_request_count', 'console_error_count')) {
    if ($receipt.$field -ne 0) { throw "Final public-surface evidence is not clean: $field" }
}
```

Expected: container evidence proves non-root/nologin, read-only/tmpfs, CPU/no-network, inventoried `/usr/bin/env`, exact `HF_HUB_DISABLE_TELEMETRY=True` before import/after Blocks/in PID 1/children, fixed port, explicit Uvicorn `http="h11"`, zero app-owned input/dependency/function/API config, recorded framework `enable_queue == true`, exact two-argument outer-ASGI composition with nonempty pinned-root membership, direct guard interception before FastAPI/Gradio/downstream/body receive, all four authority-selected sanitized scopes, runtime/reviewer package membership-tree equality, exact metadata/logo bytes, zero CORS/compression/network/temp/echo side effects, unavailable API/queue/history/monitoring, and three normal cold starts. Direct-ASGI evidence proves missing/duplicate/invalid Host guard 404 and deterministic blocked HEAD messages; raw-wire evidence separately proves the explicitly selected Uvicorn+h11 missing/duplicate Host 400 before ASGI, zero app-entry/canary/reflection delta, valid unlisted single Host guard 404, and zero wire HEAD entity bytes with `content-length: 9`. Browser evidence separately proves normal plus four runtime-reachable failures at both viewports, exact GET/root-HEAD traffic, fixed `carerisk-app` alias, zero public interaction/state delta, normal-only four-radio transitions, failure-only zero-surface counts, accessibility, console, and external-request gates. Four final-digest-derived `NEVER_DEPLOY` images have exact labels and one path delta each. The receipt's five-code matrix explicitly marks `receipt_schema_invalid` as unit/component/ASGI-only, anchor-dominated, not live-reviewed, and covered by the exact failure copy/code/zero-surface assertions. Cleanup proves exact type-specific labels and identities for the normal container, reviewer container, shared network, four failure containers, and four failure images; any ambiguous or mismatched resource remains preserved. Sentinel/root-block/max-size evidence remains defense in depth. The test does not require `/bin/sh` to be absent.

- [ ] **Step 5: Verify clean scope and provenance one final time**

```powershell
$changed = @(git status --porcelain=v1 --untracked-files=all)
if ($changed.Count -ne 0) { throw 'Final verification dirtied the repository' }
if ((git rev-parse HEAD^).Trim() -cne $appSourceSha) { throw 'Two-commit provenance relationship changed' }
git diff --check
git log -2 --format='%H %P %s'
```

Expected: clean repository; manifest commit immediately follows the app-source commit; no additional implementation commit is created.

## Post-Implementation Remote Runbook Gates — Explicitly Out of Scope

The implementation session stops after Task 13 and central written review. These are later, separately authorized gates, not executable tasks in this plan:

1. Authenticate as the namespace owner and check `steven0226/carerisk-48h` for public, private, deleted, reserved, and organization-policy collision. Any ambiguity is a hard stop.
2. Obtain explicit authorization to create the Space. Collision clearance alone does not authorize creation.
3. Reproduce the exact clean export from the reviewed two commits and compare every byte to `deployment-manifest.json`.
4. Obtain explicit authorization to upload that exact candidate. Space creation alone does not authorize upload.
5. After upload, compare the public tree and bytes, record the Hugging Face destination commit plus deployment-manifest SHA-256 in a separate post-deployment audit record, and inspect logs, Secrets/Variables, external requests, licenses, and source tree.
6. Before public traffic, verify the actual Space application/iframe Host is byte-for-byte `steven0226-carerisk-48h.hf.space`; any alias or different identity is a publication stop for central review, not permission to amend the authority map. Then run three real public cold starts and the 1440×900/390×844 accessibility, authority-sanitization, metadata, asset-membership, and request-graph review. Local results do not stand in for public live review.
7. Obtain explicit authorization before changing GitHub About Website. A successful Space upload does not authorize About, Pages, description, topics, visibility, pinning, release, or other metadata changes.

## Implementation Completion Handoff

After Task 13, report the app-source SHA, manifest-source SHA, manifest SHA-256, clean-export tree digest, exact dependency/base/SBOM/license digests, test counts, Docker image digest, local viewport/cold-start observations, and any unresolved vulnerability/license observation. Stop for central review; do not run any remote gate.
