# CareRisk 48H Hugging Face Space Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a public-safe, synthetic-only Gradio Docker Space that explains receipt-backed evidence and four fixed abstention gate states without accepting patient data or producing case-level scores or decisions.

**Architecture:** Keep the new application isolated under `space/` as a small `carerisk_space` package. Pure standard-library contracts parse three committed JSON artifacts and fail closed before Gradio is constructed; Gradio presents one pre-rendered static HTML/CSS explorer with native radios and zero app-owned inputs, dependencies, functions, or API endpoints. An empty FastAPI parent mounts Gradio, a direct pure-ASGI wrapper forms the truly outer public-surface firewall with a closed authority map and exact locked-package asset membership, and fixed programmatic Uvicorn serves it. A source-only exporter reads exact Git blobs into a fresh directory, with application files from an app-source commit, evidence and legal files from the annotated `v0.2.0` tag commit, and `deployment-manifest.json` from the immediately following manifest commit.

**Tech Stack:** CPython 3.11 slim-bookworm runtime image pinned by patch tag and OCI digest; an official Playwright Python test/reviewer image pinned by matching Playwright patch tag plus OCI index/linux-amd64 digests; Gradio `6.26.0`; standard-library `json`, `hashlib`, `html`, `dataclasses`, `pathlib`, and `typing`; pytest, Ruff, Mypy, Playwright, accessibility tooling, pip hash locks, SPDX 2.3 JSON, and Docker CPU-only smoke tests.

**Governing design:** `docs/superpowers/specs/2026-08-31-carerisk-48h-hf-space-design.md`. The original design approval was commit `10a85171afeb9fafb531b3bca1128cddc987619e`; central implementation authorization is anchored at corrective plan commit `b3803f6229d0de51f0a006978e26775012edcc3b`. The current Task 5 docs-only authority gate starts from parent `07550dfb40d15801b6677a4b785a63f5e654af6f`; Task 5 may resume only after a fresh review of the resulting design/plan commit is clean. No provisional self-SHA is fabricated in this document.

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
- Gradio is fixed exactly at `6.26.0`. The normal and five failure Blocks have zero app-owned input components, dependencies, functions, or API endpoints and empty in-process API metadata. Four scenarios are pre-rendered through `render_scenario`; normal browser interaction sends zero POST, callback, queue, event, or session traffic. Pinned `config.enable_queue == true` and Gradio's internal queue/state initialization are recorded facts, not failures and not monkeypatch targets; queue/event/session routes remain outer-blocked and public-interaction state delta must stay zero.
- `create_app` fixes `dev_mode=False`, `vibe_mode=False`, `root_path=""`, `api_open=False`, and `space_id=None`. `gr.mount_gradio_app` receives only the supported fixed mount arguments listed in Task 5. `uvicorn.run` receives the wrapped application object plus fixed host/port/single-worker/no-proxy/no-access-log arguments; no Gradio `launch` path exists.
- `space/carerisk_space/ui.py` owns pure-ASGI `PublicSurfaceGuard` and the immutable locked-package asset membership builder. `space/app.py` creates an empty FastAPI parent without docs/OpenAPI, mounts Gradio, and directly wraps the resulting parent as `app = PublicSurfaceGuard(parent, build_package_asset_membership())` before Uvicorn. The guard is outside parent error handling and mounted Gradio Brotli/CORS/router/body parsing. It is not placed in `app_kwargs` or a framework middleware list.
- The guard accepts exactly four Host authorities: `127.0.0.1:7860` and `localhost:7860` over HTTP, the reviewer-only Docker alias `carerisk-app:7860` over HTTP, and `steven0226-carerisk-48h.hf.space` over HTTPS. It rebuilds a constant downstream scope/header tuple for the selected authority and rejects every missing, duplicate, combined, whitespace-padded, case-variant, trailing-dot, userinfo, or extra-port Host. Uvicorn never trusts forwarded headers. A different real Hugging Face Host is a publication stop, not permission to broaden the map.
- At startup, `ui.py` reads only the source-audited locked-wheel constants `gradio.routes.BUILD_PATH_LIB` and `STATIC_PATH_LIB`, derives an immutable URL set from canonical regular non-symlink root-contained package files, and authorizes `/assets` and `/static` only by exact membership. Linux runtime and reviewer images independently record and compare sorted membership/content-tree digests. No unknown-valid filename or user/site/evidence/temp path reaches Gradio.
- Because Gradio `6.26.0` consults environment variables for falsy path lists, the mount retains truthy exact sentinels `allowed_paths=["/__carerisk_no_allowed_files__"]` and `blocked_paths=["/"]`; the allowed sentinel is an absolute nonexistent path. These and `max_file_size=0` are defense in depth only. The truly outer firewall, sanitized permitted scopes, and no-downstream/no-receive probes establish the public boundary.
- The final Docker exec-form `ENTRYPOINT` uses `/usr/bin/env -i` before Python import and rebuilds only the reviewed fixed environment allowlist, including the exact canonical `HF_HUB_DISABLE_TELEMETRY=True`. Its exec-form `CMD` remains `["python", "app.py"]`; neither `SPACE_ID`, `PORT`, secrets, nor arbitrary injected variables survive. Candidate verification poisons Docker `GRADIO_*`, `HF_HUB_DISABLE_TELEMETRY`, `SPACE_ID`, and `PORT` values and proves the pre-import, post-Blocks, PID 1, child, and runtime values cannot drift.
- Runtime is CPU-only, non-root, and read-only except framework-owned operations in bounded ephemeral `/tmp`. No persistent service is started during ordinary unit tests.
- The approved “no shell” interpretation is precise: the runtime account is non-login with `/usr/sbin/nologin`, the app uses exec-form startup and never invokes a shell, and unnecessary shell utilities are excluded. Do not assert that Debian slim physically lacks `/bin/sh`.
- `requirements.lock` contains the complete runtime closure. `requirements-dev.lock` contains the complete runtime-plus-development union closure; every normalized runtime package/version pair is present unchanged in the development lock. Both locks contain exact versions and accepted target-distribution hashes. Docker installation uses `python -m pip install --require-hashes --no-deps` against the appropriate complete closure.
- The final runtime base uses a real CPython 3.11 slim-bookworm patch tag plus real OCI index/linux-amd64 digests. The test/reviewer base uses the official Playwright Python image whose patch version exactly matches the locked Playwright Python package, with real tag, index digest, linux/amd64 digest, embedded browser revisions, OS/system-package inventory digest, license, and notices recorded. Mutable-only image references are rejected.
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

## Task 5 Authority and Pinned-Source Evidence

- Central authorized local implementation at plan commit `b3803f6229d0de51f0a006978e26775012edcc3b`. Task 5 is currently held at docs parent `07550dfb40d15801b6677a4b785a63f5e654af6f`; this correction changes only the governing design and plan. Product/test files remain byte-frozen until a fresh authority review is clean.
- Pinned `.venv-space` reports Gradio `6.26.0`. `inspect.signature(gr.mount_gradio_app)` contains every fixed Task 5 mount argument, including `favicon_path`; `inspect.signature(uvicorn.run)` contains the fixed programmatic options; no `launch` or CLI path is required.
- Direct composition `app = PublicSurfaceGuard(parent)` after `gr.mount_gradio_app(...)` was probed with hostile headers: permitted root/config requests remained healthy after scope sanitization, while `OPTIONS` and upload paths returned the fixed 404 outside Gradio with no canary, CORS, or compression. The final implementation additionally passes immutable package membership into the guard.
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
| `space/SBOM.spdx.json` | Deterministic SPDX record for app, both base images, embedded browsers/system inventory, and locked Python packages |
| `space/THIRD_PARTY_LICENSES.json` | Reviewed license/notice records for every locked distribution, base image, and embedded browser identity |
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
| `tools/space/base-image.json` | Named runtime/reviewer records with patch tags, index/platform digests, Python/Playwright/browser identity, and inventory hashes |
| `tools/space/license-policy.json` | Reviewed SPDX expressions and dispositions keyed by normalized package/version |
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
# PublicSurfaceGuard(app: ASGIApp)
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
- `space/tests/test_gradio_contract.py` owns `valid_bundle`, `failure_bundle`, `manifest_canary_bundle`, `RunningLocalApp`, `running_local_app`, `captured_app_logs`, `bounded_failure_codes(text)`, pure-ASGI bomb helpers, and exact request-graph capture. `RunningLocalApp` exposes only `base_url`, the mounted parent/inner route inventory, and callable in-memory log/request snapshots; it never persists logs. The server fixture binds loopback on port 7860 or an explicit test-only adapter that preserves the production scope constants, installs capture before startup, poisons framework-related host environment variables before application construction, yields only after permitted root/config/theme probes pass, and always closes server/capture in fixture cleanup. It uses the public committed receipt/release bytes and a synthetic manifest; it never starts the existing dashboard. `manifest_canary_bundle` places `CANARY_7419` only in an invalid deployment-manifest field. `captured_app_logs` uses the same in-memory discipline for server-free construction, and `bounded_failure_codes` returns only exact members of `ALL_FAILURE_CODES`.
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
- Produces: `create_app(bundle_root: Path | None = None) -> gr.Blocks`, a one-document static HTML/CSS explorer, `build_package_asset_membership() -> frozenset[str]`, `PublicSurfaceGuard(app: ASGIApp, package_asset_urls: frozenset[str])`, exact outer-ASGI authority/path/membership/scope sanitization, fixed FastAPI mount/Uvicorn composition, and a static evidence-failure page.

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
    failure_bundle: Path, failure_code: str,
) -> None:
    app = create_app(failure_bundle)
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

Missing, duplicated, comma-combined, whitespace-padded, uppercase, trailing-dot, userinfo, extra/default-port, IPv6-alias, or unlisted Host is blocked. For a listed Host, construct a fresh sanitized HTTP scope with the selected constant scheme/server/client, `root_path=""`, and sole header `(b"host", selected_host_bytes)`; preserve only validated method/path/raw path/query and protocol versions. Do not forward Origin, Cookie, Authorization, `X-*`, Forwarded, User-Agent, or any other client header. `proxy_headers=False` remains load-bearing. Blocked HTTP sends exact 404 `Not Found` with fixed content headers and no CORS/compression/echo, without downstream or receive.

With `title=PRODUCT_NAME` and mount `favicon_path=None`, running tests require exact GET `/manifest.json` media type and body `{"name": PRODUCT_NAME, "icons": [{"src": "static/img/logo_nosize.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"}], "start_url": "./", "display": "standalone"}`. GET `/favicon.ico` must equal the locked `STATIC_PATH_LIB/img/logo.svg` blob (1,107 bytes, SHA-256 `3d131bff3fe15bcbb3e6e6552a8bee25377c3666723a9cbe68ceca953ea613df`); `/static/img/logo_nosize.svg` must equal 1,082 bytes and SHA-256 `89fd7687072f6c1ab52be3348494f0410c270f453e8306105719b2e3f7091469`. Responses contain no canary and trigger no network/write. Every `/pwa_icon` variant is blocked. HEAD for metadata/config/theme/package paths is blocked by the outer guard with the fixed 404 and must not reach Gradio; no inner 405 or fake GET-content parity is accepted.

The existing `select_scenario`/`render_scenario` functions remain pure startup-only render helpers. They are never bound to Gradio or exposed as endpoints. Task 5 removes no Task 4 input-hardening, but the public proof no longer depends on accepting or rejecting a transport value because no transport exists.

When startup evidence is invalid, `create_app` logs exactly one structured bounded failure code and no exception, path, artifact bytes, or submitted value. The logger receives `EvidenceFailure.code` only. Tests capture the startup log for `manifest_canary_bundle`, require the bounded code `deployment_manifest_invalid`, and prove `CANARY_7419` and its representation are absent, preserving Design Section 12 without weakening it.

The assignments after the `Blocks` context are exact Gradio `6.26.0` per-instance configuration, not framework-global monkeypatching. Product modules do not import `os` or read environment variables. Tests poison every listed framework variable before construction and prove the exact instance, mount, Uvicorn, static config, and outer-wrapper state remain unchanged.

`space/app.py` imports only pinned `fastapi`, `gradio`, `uvicorn`, `create_app`, `build_package_asset_membership`, and `PublicSurfaceGuard`. It builds `parent = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)`, mounts with exact `gr.mount_gradio_app(parent, demo, path="/", server_name="0.0.0.0", server_port=7860, footer_links=[], run_history=False, root_path="", allowed_paths=["/__carerisk_no_allowed_files__"], blocked_paths=["/"], favicon_path=None, show_error=False, max_file_size=0, ssr_mode=False, enable_monitoring=False, pwa=False, mcp_server=False)`, then assigns `app = PublicSurfaceGuard(parent, build_package_asset_membership())`. It calls `uvicorn.run(app, host="0.0.0.0", port=7860, workers=1, proxy_headers=False, forwarded_allow_ips="", access_log=False, server_header=False, date_header=False, reload=False, factory=False, env_file=None, log_config=None)` only under the main guard. There is no `launch`, `app_kwargs`, CLI/config file, authentication, user mount, or environment read.

- [ ] **Step 4: Add outer-ASGI, composition, route-inventory, and running probes**

```python
def test_outer_guard_blocks_http_before_downstream_or_receive() -> None:
    for scope in hostile_http_scopes():
        downstream = DownstreamBomb()
        receive = ReceiveBomb()
        messages = run_asgi(PublicSurfaceGuard(downstream), scope, receive)
        assert downstream.calls == 0
        assert receive.calls == 0
        assert messages == fixed_not_found_messages()
        serialized = serialize_asgi_messages(messages)
        assert b"CANARY_7419" not in serialized
        assert b"access-control-allow-origin" not in serialized.lower()
        assert b"content-encoding" not in serialized.lower()

def test_outer_guard_rejects_websocket_and_unknown_scope_without_inner_calls() -> None:
    for scope in hostile_websocket_and_unknown_scopes():
        downstream = DownstreamBomb()
        receive = ReceiveBomb()
        messages = run_asgi(PublicSurfaceGuard(downstream), scope, receive)
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
    for headers in missing_duplicate_combined_whitespace_case_dot_userinfo_port_hosts():
        downstream = DownstreamBomb()
        receive = ReceiveBomb()
        messages = run_asgi(
            PublicSurfaceGuard(downstream, exact_package_asset_urls()),
            make_scope("GET", "/", headers=headers),
            receive,
        )
        assert messages == fixed_not_found_messages()
        assert downstream.calls == receive.calls == 0

def test_exact_read_only_method_table_is_outer_enforced() -> None:
    assert guard_status("GET", "/") == 200
    assert guard_status("HEAD", "/") == 200
    for path, query in exact_get_only_paths_and_queries():
        assert guard_status("GET", path, query) == 200
        assert guard_status("HEAD", path, query) == 404
        assert guard_status("OPTIONS", path, query) == 404
        assert guard_status("POST", path, query) == 404
    assert all_fixed_404s_have_no_downstream_or_receive()

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
    for probe in url_local_upload_authority_query_header_cookie_cors_brotli_and_ambiguity_probes():
        response = send_probe(running_local_app.base_url, probe)
        assert response.status_code == 404
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

The static config is the app-owned transport proof: it contains zero inputs, dependencies, functions, or API endpoints, while recording pinned `config.enable_queue == true` and framework internal queue/state initialization. The outer guard blocks every Gradio API/queue/event/session route. In-process API metadata is empty; `/gradio_api/info` is not a public endpoint. Browser radio transitions are native HTML/CSS; the request graph remains inside the exact read-only method/path/query table with zero API, POST, event, queue, or session request and zero public-interaction state delta. The evidence-failure startup probe separately requires exactly the bounded reason and no manifest sentinel in captured logs.

The poisoned-environment fixture covers application construction, exact telemetry value after Blocks, mount capture, direct wrapper identity, Uvicorn capture, and a running server. Pure-ASGI matrices cover every non-allowlisted method; API/queue/file/upload/proxy/component/monitoring/auth/docs/vibe routes; hostile body framing/authority/query/cookie/header/raw path; URL/local file and multipart canaries; encoded/traversal/case/slash variants; WebSocket; and unknown scopes. Running integration replaces Gradio outbound fetch and temporary-file construction with bombs and proves interception occurs outside FastAPI and Gradio with no downstream, receive, CORS, Brotli, temp delta, network call, response/log echo, or traceback. Permitted requests deliver only the selected constant sanitized scope to the inner app.

The route test expands the parent mount and inner Gradio `_IncludedRouter.original_router`. Every Gradio `6.26.0` method/route is explicitly classified as exact required read-only surface or outer-boundary-blocked; a new or unclassified item fails. Tests bind the package routes to only `BUILD_PATH_LIB` and `STATIC_PATH_LIB`, exercise root/symlink/case/containment mutations, block a syntactically valid nonexistent filename before Gradio, and record sorted membership/content-tree digests. Sentinel/root-block/max-size remain defense-in-depth state. If mount signature, outer order, authority map, sanitized scope, asset membership, normal browser route use, or later HF Docker behavior requires anything else, stop for exact source audit, a RED test, and central written review; do not add a wildcard.

- [ ] **Step 5: Run GREEN and all six UI states**

```powershell
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests/test_claim_contract.py space/tests/test_evidence_contract.py space/tests/test_scenario_contract.py space/tests/test_gradio_contract.py -q
```

Expected: validated normal state plus all five bounded evidence-failure states pass; every Blocks has zero app-owned inputs/dependencies/functions/API and explicit no-component-JS config, while preserving the recorded `enable_queue == true` fact; outer-ASGI unit/integration bombs prove pre-FastAPI/pre-Gradio/pre-receive interception, exact authority sanitization, exact package membership and metadata; and every exact Gradio `6.26.0` route/method is classified.

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

**Interfaces:**
- Consumes: Python AST for `space/app.py` and `space/carerisk_space/*.py`.
- Produces: a hard source boundary that later exporter and CI reuse.

- [ ] **Step 1: Write failing AST/import boundary tests**

```python
ALLOWED_IMPORT_ROOTS = {
    "__future__", "dataclasses", "hashlib", "html", "json", "logging", "math",
    "pathlib", "re", "types", "typing", "fastapi", "gradio", "starlette", "uvicorn",
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
```

`scan_capabilities` must identify write/append/update `open`, `Path.write_text`, `Path.write_bytes`, mkdir, rename, replace, delete, environment reads, `eval`, `exec`, dynamic import, process spawn, shell execution, network client construction, file watchers, and arbitrary absolute/current/home path discovery. The only additional filesystem-capability exception is in `ui.py`: read-only `pathlib` root resolution, `rglob`/iteration, `stat`/`is_file`/`is_dir`/`is_symlink`, `relative_to`, byte-size reads, and hash reads against the two fixed imported Gradio package roots. Calls accepting a runtime path argument, current/home/user/site discovery, `os.path`, globbing outside those roots, or any write remain forbidden.

`space/app.py` may import only `FastAPI`, pinned Gradio's mount API, `uvicorn`, and the two named local UI interfaces. `space/carerisk_space/ui.py` may import only Gradio `Blocks`/`HTML`, Starlette `ASGIApp`/`Scope`/`Receive`/`Send` type interfaces, and exactly `gradio.routes.BUILD_PATH_LIB`/`gradio.routes.STATIC_PATH_LIB` from framework code. Importing any other Gradio route/function/internal, Starlette `Middleware`, request/body parsing, response/file/static helpers, network clients, temporary-file APIs, background tasks, environment access, or filesystem writes is forbidden. Source and mutation tests prove the two roots are the only inputs, are resolved strictly, are non-symlink directories, and every accepted file is regular/non-symlink and passes strict resolved-root `Path.relative_to` containment. URL membership preserves the wheel's exact case and is compared case-sensitively, including on Windows where filesystem containment semantics alone are not a case proof. Missing roots, root/file/directory symlinks, request case aliases, special files, and escapes fail closed. The source test requires exactly one empty `FastAPI(docs_url=None, redoc_url=None, openapi_url=None)`, one `gr.mount_gradio_app` call with the full exact Task 5 mapping including `favicon_path=None`, direct `PublicSurfaceGuard(parent, build_package_asset_membership())` composition, and one fixed programmatic `uvicorn.run` under the main guard. It rejects route decorators, `add_middleware`, `app_kwargs`, `Blocks.launch`, Gradio `Radio` or event binding, any second mount/router, and framework monkeypatching.

- [ ] **Step 2: Run RED**

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_source_boundary.py space/tests/test_export_contract.py -q
```

Expected: FAIL until the scanners and explicit source/export boundary are implemented.

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

- [ ] **Step 4: Run GREEN**

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_source_boundary.py space/tests/test_export_contract.py -q
```

Expected: all boundary tests pass without importing the existing application or model package.

- [ ] **Step 5: Commit the exact files**

```powershell
git add -- tests/test_hf_space_source_boundary.py space/tests/test_export_contract.py
git diff --cached --check
git commit -m 'test(space): enforce public capability boundary'
```

### Task 7: Build reproducible dependency, base-image, SBOM, and license workflows

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
- Consumes: reviewed direct requirement inputs, official package indexes, official OCI registry metadata, and reviewed SPDX license policy.
- Produces: deterministic locks and public supply-chain files plus `verify_all(repo_root: Path) -> None`.

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
        "chromium", "firefox", "webkit",
    }
    assert sbom_package_keys(SBOM) == locked | image_components
    assert license_inventory_keys(LICENSES) == locked | (image_components - {"carerisk-space"})
    assert all(item["review_disposition"] == "approved" for item in load_licenses(LICENSES))
```

- [ ] **Step 2: Run RED**

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_supply_chain.py -q
```

Expected: FAIL because inputs, generator, locks, base record, SBOM, and license inventory do not exist.

- [ ] **Step 3: Implement deterministic supply-chain commands**

```python
def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "resolve-images":
        return resolve_images(args)
    if args.command == "lock":
        return build_locks(args)
    if args.command == "inventory":
        return build_inventory_and_sbom(args)
    if args.command == "verify":
        verify_all(args.repo_root)
        return 0
    raise AssertionError("unreachable")
```

`resolve-images` queries the official image registries during the controlled supply-chain phase. It selects (a) a concrete CPython 3.11 patch `slim-bookworm` runtime image and (b) an official Playwright Python reviewer image whose exact patch version equals the direct locked Playwright Python pin. It records each tag, OCI index digest, linux/amd64 manifest digest, Python target, system-package inventory digest, source registry, license/notices, and, for the reviewer, the exact Chromium/Firefox/WebKit revisions and content identities. Mutable-only or cross-platform-only responses are rejected.

`lock` runs only the hash-locked resolver tooling from `lock-tooling.txt`. It emits `requirements.lock` as the complete runtime closure for the runtime Linux/Python target and `requirements-dev.lock` as the complete runtime-plus-development union closure for the reviewer Linux/Python target. The normalized package/version pairs from the runtime lock must be an unchanged subset of the development lock. Each lock is installed alone with `--require-hashes --no-deps`; a controlled acquisition step first fills a temporary wheelhouse with only accepted hashes, then a separate no-egress `--no-index` step verifies installation from that wheelhouse. Do not describe the controlled acquisition step as offline.

`inventory` extracts metadata and notices from exact accepted wheels and both exact image manifests/inventories, includes the reviewer image's embedded browser revisions and system packages, joins every component to an explicit approved `license-policy.json` record, and serializes sorted canonical JSON with a final newline. `SBOM.spdx.json`, `THIRD_PARTY_LICENSES.json`, and their tests cover both base images as well as the Python and browser components; the final runtime image still contains only the runtime base and runtime lock.

The direct runtime input contains only `gradio==6.26.0`; a candidate range such as a broad major-version interval is forbidden. The direct development input contains the same exact Gradio pin plus pytest, Ruff, Mypy, PyYAML, packaging, the exact Playwright Python pin matching the reviewer image, accessibility tooling, lock verification, vulnerability scanning, and license/SBOM verification tools. The development lock remains the complete runtime-plus-development union closure, and contract tests verify the installed Gradio version as well as the exact direct pin and equal runtime/development lock entries. It does not rely on Playwright wheels to supply browsers or Debian packages, and Dockerfile generation must not run `playwright install` or `apt-get install` in the reviewer stage. Product code still imports only Gradio, standard library, and local modules.

- [ ] **Step 4: Resolve and review real pins rather than writing guessed values**

```powershell
$toolVenv = '.venv-space-lock'
python -m venv $toolVenv
& "$toolVenv\Scripts\python.exe" -m pip install --require-hashes -r tools/space/lock-tooling.txt
& "$toolVenv\Scripts\python.exe" scripts/build_hf_space_supply_chain.py resolve-images --output tools/space/base-image.json
& "$toolVenv\Scripts\python.exe" scripts/build_hf_space_supply_chain.py lock --runtime-input tools/space/requirements-runtime.in --development-input tools/space/requirements-dev.in --runtime-output space/requirements.lock --development-output space/requirements-dev.lock
& "$toolVenv\Scripts\python.exe" scripts/build_hf_space_supply_chain.py inventory --base tools/space/base-image.json --runtime-lock space/requirements.lock --development-lock space/requirements-dev.lock --license-policy tools/space/license-policy.json --licenses-output space/THIRD_PARTY_LICENSES.json --sbom-output space/SBOM.spdx.json
```

Expected: this explicitly controlled, logged egress phase acquires only the selected registry/package/browser references and verifies every digest/hash. Every generated file contains actual values and hashes. Review package source URLs, both base-image inventories, embedded-browser revisions, license texts, notices, and dispositions before proceeding. Unknown, missing, incompatible, or non-redistributable components stop the task.

- [ ] **Step 5: Run reproducibility and installation GREEN**

```powershell
& "$toolVenv\Scripts\python.exe" scripts/build_hf_space_supply_chain.py verify --repo-root .
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_supply_chain.py -q
$trackedOutputs = @('space/requirements.lock', 'space/requirements-dev.lock', 'space/SBOM.spdx.json', 'space/THIRD_PARTY_LICENSES.json')
$first = @($trackedOutputs | ForEach-Object {
    $item = Get-FileHash -Algorithm SHA256 -LiteralPath $_
    '{0}|{1}' -f $_, $item.Hash.ToLowerInvariant()
})
& "$toolVenv\Scripts\python.exe" scripts/build_hf_space_supply_chain.py inventory --base tools/space/base-image.json --runtime-lock space/requirements.lock --development-lock space/requirements-dev.lock --license-policy tools/space/license-policy.json --licenses-output space/THIRD_PARTY_LICENSES.json --sbom-output space/SBOM.spdx.json
$second = @($trackedOutputs | ForEach-Object {
    $item = Get-FileHash -Algorithm SHA256 -LiteralPath $_
    '{0}|{1}' -f $_, $item.Hash.ToLowerInvariant()
})
if ([string]::Join("`n", $first) -cne [string]::Join("`n", $second)) { throw 'Supply-chain outputs are not reproducible' }
```

Expected: verify and tests pass, and regeneration is byte-for-byte stable.

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
    assert_exact_fastapi_mount_outer_guard_and_uvicorn_calls(source)
    assert "uvicorn " not in DOCKERFILE.read_text(encoding="utf-8")
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
```

- [ ] **Step 2: Run RED**

```powershell
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests/test_container_contract.py tests/test_hf_space_supply_chain.py -q
```

Expected: FAIL because the Space Dockerfile and smoke contract do not exist.

- [ ] **Step 3: Generate the Dockerfile from the verified base record**

The generated Dockerfile must expose named `test` and `runtime` stages with no ancestry between them. `test` starts from the exact official Playwright Python reviewer tag plus recorded linux/amd64 digest, installs the complete `requirements-dev.lock` union closure with hashes and no dependency resolution, and contains the six public test modules. Its Playwright Python version is exactly the one matched by the reviewer image and it uses only the Chromium/Firefox/WebKit bytes already embedded in that pinned image; it runs no browser download, `playwright install`, or unrecorded `apt` acquisition. This stage never becomes or contributes a filesystem layer to the deployed stage.

`runtime` starts independently from the exact CPython 3.11 slim-bookworm runtime tag plus recorded linux/amd64 digest. It uses explicit `COPY` for runtime files only, creates numeric UID/GID `10001`, assigns `/usr/sbin/nologin`, retains no writable home, installs `requirements.lock` with hashes and no dependency resolution, excludes tests/dev tools/browser/reviewer layers from the final image, and uses `USER 10001:10001`. The image inventory must prove `/usr/bin/env` exists and record its owning Debian package/version. The exec-form `ENTRYPOINT` is exactly `/usr/bin/env -i` followed by the fixed assignments `PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin`, `LANG=C.UTF-8`, `LC_ALL=C.UTF-8`, `PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1`, `GRADIO_ANALYTICS_ENABLED=False`, `HF_HUB_DISABLE_TELEMETRY=True`, `GRADIO_WATCH_DIRS=`, `GRADIO_VIBE_MODE=`, `GRADIO_HOT_RELOAD=false`, `GRADIO_RUN_HISTORY=False`, `GRADIO_SSR_MODE=False`, `GRADIO_MCP_SERVER=False`, `GRADIO_ALLOWED_PATHS=`, and `GRADIO_BLOCKED_PATHS=/`; exec-form `CMD ["python", "app.py"]` follows it. This clears Docker/Hugging Face environment injection before any Python or Gradio import while retaining only the reviewed runtime variables. Gradio `Blocks(analytics_enabled=False)` writes the same exact value `True`, so tests require pre-import, post-Blocks, PID 1, and every child to agree without a two-value exception. Poison runs inject `0` and secret-shaped alternatives and prove they are scrubbed. No `SPACE_ID`, `PORT`, Secret, Variable, or credential is required or preserved. Tests inspect final image history/package inventory and fail if Playwright, pytest, browser files, or a reviewer-layer digest appears.

Do not add an assertion or removal step for `/bin/sh`. The accepted proof is non-login passwd metadata plus absence of shell calls in application AST and exec-form startup.

- [ ] **Step 4: Run the static Docker/source GREEN available before provenance freeze**

```powershell
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests/test_container_contract.py tests/test_hf_space_supply_chain.py tests/test_hf_space_source_boundary.py -q
.venv-space\Scripts\python.exe scripts/build_hf_space_supply_chain.py verify --repo-root .
```

Expected: Dockerfile/two-base/union-lock/account/startup/source contracts pass, including `python app.py` invoking the exact programmatic Uvicorn contract, the exact `/usr/bin/env -i` allowlist, and absence of `SPACE_ID`/`PORT` configuration. Do not build from `space/` directly because it intentionally lacks tag-sourced evidence/legal files, and do not invent a provisional manifest. Actual `/usr/bin/env` inventory, image, final-stage inventory, injected-environment stripping, UID/GID, read-only/tmpfs, CPU, no-network, loopback, outer-guard/file-capability, and cold-start evidence is required from the two-commit clean export in Task 13 before any runtime success claim.

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
- Consumes: a local container image or local candidate process plus an owned GUID-named temporary run root outside the repository.
- Produces: `ReviewPlan`, `LiveReviewRecord`, and ownership-safe orchestration that Task 13 exercises against the final clean candidate.

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
        "receipt_schema_invalid",
        "release_relationship_invalid",
        "deployment_manifest_invalid",
    )
    assert plan.cold_starts == 3

def test_container_cold_start_command_is_hardened() -> None:
    command = build_container_command("carerisk-space:final")
    joined = " ".join(command)
    for required in ("--cpus=2", "--network=none", "--read-only", "--tmpfs"):
        assert required in joined
    assert "mode=1777" in joined

def test_reviewer_app_uses_exact_internal_network_alias() -> None:
    command = build_reviewer_app_command("carerisk-space:final")
    assert option_value(command, "--network-alias") == "carerisk-app"
    assert reviewer_base_url(command) == "http://carerisk-app:7860"

def test_failed_live_record_cannot_be_reported_as_green() -> None:
    record = sample_record(serious_accessibility_findings=1)
    with pytest.raises(ReviewFailure, match="accessibility"):
        assert_review_passed(record)

def test_candidate_verifier_temp_self_test_rejects_unowned_or_outside_paths() -> None:
    result = run_candidate_verifier("--self-test-temp-ownership")
    assert result.returncode == 0
    assert "rejected-unowned" in result.stdout
    assert "rejected-outside-temp-root" in result.stdout
```

- [ ] **Step 2: Run RED**

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_live_review.py -q
```

Expected: FAIL because the review runner and records do not exist.

- [ ] **Step 3: Implement ephemeral review orchestration**

```python
PageState = Literal[
    "validated_normal",
    "receipt_missing",
    "receipt_hash_mismatch",
    "receipt_schema_invalid",
    "release_relationship_invalid",
    "deployment_manifest_invalid",
]

@dataclass(frozen=True)
class ReviewPlan:
    viewports: tuple[tuple[int, int], ...]
    scenario_ids: tuple[str, ...]
    page_states: tuple[PageState, ...]
    cold_starts: int

    @classmethod
    def default(cls) -> "ReviewPlan":
        return cls(
            viewports=((1440, 900), (390, 844)),
            scenario_ids=SCENARIO_IDS,
            page_states=(
                "validated_normal",
                "receipt_missing",
                "receipt_hash_mismatch",
                "receipt_schema_invalid",
                "release_relationship_invalid",
                "deployment_manifest_invalid",
            ),
            cold_starts=3,
        )

@dataclass(frozen=True)
class LiveReviewRecord:
    viewport: tuple[int, int]
    page_state: PageState
    claim_fully_visible_before_control: bool
    horizontal_overflow_px: int
    body_font_px: float
    minimum_control_target_px: float
    keyboard_radio_selection: bool
    scenario_visibility_before_after: tuple[tuple[str, bool, bool], ...]
    visible_focus: bool
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

class ReviewFailure(RuntimeError):
    pass

def assert_review_passed(record: LiveReviewRecord) -> None:
    if record.serious_accessibility_findings or record.critical_accessibility_findings:
        raise ReviewFailure("accessibility findings")
    if not record.claim_fully_visible_before_control:
        raise ReviewFailure("claim order or visibility")
    if record.horizontal_overflow_px or record.body_font_px < 16:
        raise ReviewFailure("responsive layout")
    if record.minimum_control_target_px < 44 or not record.keyboard_radio_selection:
        raise ReviewFailure("control accessibility")
    if record.scenario_visibility_before_after != EXPECTED_VISIBILITY_TRANSITIONS:
        raise ReviewFailure("static scenario visibility")
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
```

The Python runner has two explicit modes. Container cold-start mode starts the app image with the same two-CPU/no-network/read-only/tmpfs flags as Task 9 and uses `docker exec` with Host `127.0.0.1:7860` to probe exact root/config/theme/manifest/favicon/package-member responses and claim copy on loopback. It records the locked package membership/content-tree digest and submits the authoritative blocked matrix, including method-table HEAD probes, nonexistent-valid asset names, authority mutations, metadata/PWA paths, and downstream/receive/fetch/temp bombs. Records include outer-guard-first status/body, zero CORS/compression/echo, exact selected sanitized downstream scope, and defense-in-depth state separately. Browser-review mode creates a temporary Docker `--internal` network, starts the final app image with the exact network alias `carerisk-app`, starts the pinned Playwright reviewer against `http://carerisk-app:7860`, drives both viewports, selects all four native radios by keyboard, records before/after checked-panel visibility, tests normal plus five failure bundles, runs WCAG checks, and records every exact app method/path/query plus block, POST, event/session/queue, state-delta, console, and external-request counts. Normal traffic must follow the exact method table (`GET` except root may also use `HEAD`), must include the observed manifest/favicon/static-logo requests, and must be exactly allowlisted; guard blocks, POSTs, event/session/queue requests, public state delta, external requests, and console errors are each zero. The internal network permits reviewer-to-app traffic but has no external route and no dependency download. Browser review never substitutes for `--network none` smoke.

If the normal Gradio `6.26.0` browser needs a route/query/method not in the approved table, emits any POST/event/session/queue traffic, changes framework public-interaction state, cannot use the exact `carerisk-app:7860` authority-selected sanitized scope behind the reviewer network, produces an asset inventory mismatch, or if outer ordering lets a blocked probe reach FastAPI/Gradio/body receive, the runner raises a load-bearing incompatibility and stops. If an authorized Hugging Face candidate or iframe Host is not exactly `steven0226-carerisk-48h.hf.space`, publication stops and reports centrally. The implementation must source-audit the exact issue, add a RED test, and report centrally; it must not accept a generic prefix, method, static, upload, file, header, host, authority suffix, or query wildcard.

`verify_hf_space_candidate.py` owns final orchestration. It creates exactly one GUID-named run directory beneath `Path(tempfile.gettempdir()).resolve(strict=True)` and writes an ownership marker containing that GUID and canonical root. Candidate and review directories are children of that run root. A `try/finally` always stops only containers/networks labeled with the same GUID and calls a cleanup function that re-resolves the OS temp root, rejects symlinks/reparse points, requires the exact GUID prefix plus matching ownership marker/canonical root, and then applies `shutil.rmtree` only to that one run directory. Unowned, missing-marker, mismatched, symlink/reparse-point, workspace, temp-root itself, or outside-temp paths are a hard stop and are never deleted. The script emits its final verification receipt to stdout after cleanup; it persists no review file unless central later provides a separately authorized, explicit outside-repository retention path.

- [ ] **Step 4: Run orchestration/config GREEN before the final candidate exists**

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_live_review.py space/tests/test_gradio_contract.py -q -m 'not integration'
```

Expected: orchestration, exact viewport/state matrix, hardened command construction, Gradio config, and failure-reporting contracts pass. Do not claim live viewport, container, accessibility, or cold-start success here; those require the clean candidate in Task 13. Thirty seconds remains a recorded soft local target, never a public SLA.

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
- Produces: a reviewed app-source commit whose SHA is the immutable `space_app_source_git_sha`.

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
```

- [ ] **Step 2: Run RED**

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_source_boundary.py tests/test_hf_space_supply_chain.py tests/test_hf_space_exporter.py -q
```

Expected: FAIL because the workflow does not exist.

- [ ] **Step 3: Add the least-privilege workflow with immutable action SHAs**

Resolve official action tag commits read-only and write the resulting real 40-character SHAs directly into the workflow. The `source_gates` job always runs and binds `REVIEWER_IMAGE` to the same exact reviewer tag plus linux/amd64 digest recorded in `base-image.json`. A controlled acquisition step fills an ephemeral wheelhouse from `space/requirements-dev.lock` and rejects every non-matching hash. A separate invocation of that reviewer image uses `--network none`, mounts the repository read-only plus the wheelhouse, installs the development union lock alone with `--no-index --require-hashes --no-deps`, verifies the runtime-package/version subset relation, and runs source/Space/static/supply-chain gates. The job exports a literal `manifest_present` output from an exact Linux check (`if [ -f space/deployment-manifest.json ]; then echo 'present=true' >> "$GITHUB_OUTPUT"; else echo 'present=false' >> "$GITHUB_OUTPUT"; fi`). It never calls manifest generation, export, candidate build, or candidate verification.

The separate `candidate_gates` job has `needs: source_gates` and the exact condition `${{ needs.source_gates.outputs.manifest_present == 'true' }}`. Thus it is skipped on the app-source commit, where the manifest does not yet exist, and becomes required after the manifest commit exists. Only that job invokes the ownership-safe clean-export verifier, controlled digest/hash-pinned image/dependency acquisition and build, followed by no-egress tests/runtime/browser review, vulnerability/license scan, and no public artifact upload. Workflow-contract tests assert both branches. A fabricated, empty, copied, or provisional manifest is forbidden; absence is a normal source-only state, not something CI repairs.

- [ ] **Step 4: Run the complete app-source verification locally**

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
- Temporary only: one ownership-marked GUID run root beneath the resolved OS temp root, containing candidate and review children.

**Interfaces:**
- Consumes: app-source SHA from `deployment-manifest.json` and current manifest-source SHA.
- Produces: a final JSON receipt on stdout after ownership-safe cleanup; no tracked change and no commit.

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
3. In the same controlled supply-chain/build phase, build `--target test` and `--target runtime` from the exact candidate. Network access is permitted only for digest/hash-pinned base and Python package acquisition and every accepted byte must match the image digest or lock hash. `--pull=false` may be used only after exact local image verification and is never evidence that the build was offline. Verify built image histories/inventories: test uses the reviewer base; runtime uses only the CPython base and contains no dev/browser/model package.
4. End the acquisition/build phase. Run all six public tests and `pip check` from the standalone test image with `docker run --network none --cpus=2`. Inventory `/usr/bin/env` in the final runtime and its owning Debian package/version, then run UID/GID/nologin/read-only/tmpfs/CPU smoke and three cold starts with `--network none`. Every runtime start passes adversarial values for the exact Gradio `6.26.0` source-derived environment-read inventory. The required named matrix includes `GRADIO_ANALYTICS_ENABLED`, `HF_HUB_DISABLE_TELEMETRY`, `GRADIO_WATCH_DIRS`, `GRADIO_VIBE_MODE`, `GRADIO_HOT_RELOAD`, `GRADIO_RUN_HISTORY`, `GRADIO_SSR_MODE`, `GRADIO_MCP_SERVER`, `GRADIO_ALLOWED_PATHS`, `GRADIO_BLOCKED_PATHS`, `GRADIO_ROOT_PATH`, `GRADIO_SHARE`, `GRADIO_MONITORING_ENABLED`, `GRADIO_DEBUG`, `GRADIO_SERVER_NAME`, `GRADIO_SERVER_PORT`, `GRADIO_NUM_WORKERS`, `GRADIO_NODE_PATH`, `GRADIO_LOCAL_DEV_MODE`, and `GRADIO_NODE_SERVER_PORT`, plus `SPACE_ID`, `PORT`, and a secret-shaped canary. Inspect pre-import state, post-Blocks state, `/proc/1/environ`, and every runtime child environment and require exact equality with the fixed `ENTRYPOINT` allowlist, including `HF_HUB_DISABLE_TELEMETRY=True`; poison values `0` and hostile strings must be absent. Prove fixed port 7860, zero app-owned input/dependency/function/API config, pinned `enable_queue == true`, zero public state delta, mount mapping, direct outer-wrapper identity, and programmatic Uvicorn values do not drift. Derive sorted package membership/content-tree digests from the exact runtime wheel and compare them with the reviewer image; require only regular non-symlink root-contained members. Against loopback Host `127.0.0.1:7860`, require healthy exact root/config/theme/manifest/favicon/package members and logo digests; unavailable API/queue/history/monitoring; and fixed 404 before FastAPI/Gradio/downstream/body receive for the complete hostile method/path/query/authority/header/cookie/raw-path/WebSocket matrix, including HEAD on every non-root path, syntactically valid nonexistent assets, metadata/PWA variants, missing/duplicate/combined/whitespace Host, and every unlisted authority. Record zero CORS/compression, outbound fetches, temp delta, and echo. Sentinel/root-block/max-upload remain separate defense-in-depth observations. No execution-phase command downloads a dependency.
5. Create a GUID-labeled Docker `--internal` network, start the final app with exact network alias `carerisk-app`, and run the exact reviewer image against `http://carerisk-app:7860` for normal/five-failure, four-scenario, 1440×900/390×844, keyboard/focus, WCAG, console, and request-graph review. Repeat adversarial environment injection and require the same PID 1/child allowlist. Verify root/config/exact theme/manifest/favicon/package members, exact membership/tree digest parity, zero app-owned inputs/dependencies/functions/API, pinned `enable_queue == true`, and all four pre-rendered scenario panels. For every radio, record checked state and corresponding panel visibility before and after keyboard selection plus zero public-interaction state delta. Record every browser app method/path/query and require the exact method table: `GET` for all allowed resources and optional `HEAD` only for root. Require the exact manifest/favicon/static-logo requests to appear as accepted traffic; outer-guard blocks, POSTs, event/session/queue requests, external requests, and console errors must all be zero. Separately repeat URL/local-file, zero/nonzero/oversized upload, body-framing, hostile authority/query/cookie/header, CORS/Brotli, WebSocket, dangerous-family, metadata/PWA, absent-asset, encoded, traversal, case, and slash probes and require outer-guard fixed responses, no downstream/body receive, no outbound network, no temp delta, and no echo. Record the exact authority-selected sanitized inner scope/header observation for all four approved authorities and fail if local/container proxy operation requires forwarding attacker headers. The absolute sentinel, root block, and `max_file_size=0` remain defense in depth. Only reviewer-to-app traffic is possible; all egress is absent. Record reviewer image/digests/browser revisions. Any normal route/query/method outside the table, POST/event/session/queue traffic, public state delta, outer-order failure, asset mismatch, authority/sanitized-scope incompatibility, or authorized Hugging Face identity other than exact `steven0226-carerisk-48h.hf.space` stops verification for exact source audit, RED test, and central review; no wildcard is added.
6. In `finally`, stop/remove only containers and the internal network carrying the current GUID label, then validate and delete only the current ownership-marked temp run root. Emit the JSON receipt after cleanup. Any cleanup validation failure is itself a failed run and leaves the suspect directory untouched for manual inspection; it never broadens the delete target.

Expected: the candidate has exactly the 24 paths in `PUBLIC_PATHS`, no `.git`, no extra bytes, and every file matches its manifest source/hash/size relationship. Linux tests run only in the reviewer image from the standalone candidate; the Windows host never attempts to install a Linux-only lock. The final receipt includes clean-export tree digest; both base/platform digests; lock/SBOM/license hashes; test counts; runtime image digest; `/usr/bin/env` inventory; exact pre-import/post-Blocks/PID 1/child environments; poisoned-environment behavior; zero app-owned input/dependency/function/API observations; pinned `config.enable_queue == true`; zero public-interaction state delta; parent/inner registered-route classification; mount/outer-wrapper/Uvicorn identity; four-authority map and exact sanitized scopes; package membership counts/tree digests in runtime and reviewer; exact manifest/favicon/logo body hashes; exact browser method/path/query graph; accepted metadata counts; guard-block/POST/event/session/queue/external/console counts; static radio visibility transitions; blocked-probe downstream/receive/CORS/compression/fetch/temp/echo counts; defense-in-depth state; history/monitoring results; cold starts; viewport/state results; cleanup; and no-egress observations. If `/usr/bin/env -i`, the direct outer ASGI/authority boundary, exact package membership, or accepted Host identity is absent, ineffective, or incompatible with the Hugging Face Docker Space runtime, verification stops and the threat boundary is not weakened.

- [ ] **Step 3: Re-run legacy baseline and source-only final gates after candidate cleanup**

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
    'runtime_public_surface_guard_pre_router', 'runtime_history_monitoring_closed',
    'runtime_telemetry_value_exact', 'runtime_authority_map_exact',
    'runtime_package_asset_membership_exact', 'runtime_reviewer_asset_tree_match',
    'runtime_manifest_exact', 'runtime_favicon_exact', 'runtime_logo_exact',
    'framework_enable_queue_true_recorded', 'app_owned_api_surface_zero',
    'browser_request_allowlist_exact', 'browser_network_internal',
    'browser_reviewer_alias_exact', 'browser_metadata_requests_observed',
    'accessibility_passed', 'cleanup_passed'
)
foreach ($field in $requiredTrue) {
    if ($receipt.$field -ne $true) { throw "Final receipt gate failed: $field" }
}
if ($receipt.cold_starts -ne 3 -or $receipt.viewport_count -ne 2 -or $receipt.page_state_count -ne 6 -or $receipt.scenario_count -ne 4) { throw 'Final review matrix mismatch' }
foreach ($field in @('blocked_downstream_call_count', 'blocked_receive_call_count', 'blocked_outbound_fetch_count', 'blocked_temp_entry_delta', 'blocked_echo_count', 'browser_middleware_blocked_count', 'browser_post_request_count', 'browser_event_or_session_request_count', 'browser_queue_request_count', 'public_interaction_state_delta', 'external_request_count', 'console_error_count')) {
    if ($receipt.$field -ne 0) { throw "Final public-surface evidence is not clean: $field" }
}
```

Expected: container evidence proves non-root/nologin, read-only/tmpfs, CPU/no-network, inventoried `/usr/bin/env`, exact `HF_HUB_DISABLE_TELEMETRY=True` before import/after Blocks/in PID 1/children, fixed port and zero app-owned input/dependency/function/API config, recorded framework `enable_queue == true`, mount/Uvicorn state, direct outer-ASGI interception before FastAPI/Gradio/downstream/body receive, all four authority-selected sanitized scopes, runtime/reviewer package membership-tree equality, exact metadata/logo bytes, zero CORS/compression/network/temp/echo side effects, unavailable API/queue/history/monitoring, and three cold starts. Browser evidence separately proves the exact GET/root-HEAD method table, required manifest/favicon/logo traffic, fixed `carerisk-app` alias, zero outer-guard blocks/POSTs/events/sessions/queues/public-state delta, native-radio visibility transitions, normal/five-failure, four-scenario, desktop/mobile, keyboard/focus, accessibility, console, and external-request gates on an internal no-egress Docker network. Sentinel/root-block/max-size evidence remains defense in depth. Cleanup is proven. The test does not require `/bin/sh` to be absent.

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
