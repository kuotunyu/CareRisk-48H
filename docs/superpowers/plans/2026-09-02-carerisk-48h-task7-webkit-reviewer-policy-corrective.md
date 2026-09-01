# CareRisk 48H Task 7 WebKit Reviewer Policy Corrective Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Task 7 without weakening the public redistribution gate by inventorying one exact WebKit reviewer tuple as `NOASSERTION` and proving that its bytes remain local/CI-only and absent from every public, runtime, deployment, save, export, and push path.

**Architecture:** Keep the ordinary policy path universally approved-only. Route exactly one immutable reviewer WebKit record through a separate equality validator whose complete tuple, provenance, SPDX fields, disposition, notice-completeness flag, and exclusion evidence must match byte-for-byte constants. Carry only that record's metadata into the SBOM/license inventory; Task 8, Task 9, Task 11, and Task 13 independently prove that no reviewer or embedded-browser bytes reach a distributed surface.

**Tech Stack:** CPython 3.10 host control environment; exact Linux CPython 3.11.14 runtime image; exact Playwright Python 1.62.0 Ubuntu Noble reviewer image; canonical JSON; SPDX 2.3 JSON; pytest; Docker BuildKit; GitHub Actions YAML; SHA-256 canonical tree identities.

## Global Constraints

- Preserve the current Task 7 partials until the implementation session begins and its controller validates the custody table below. This docs-only correction does not authorize changing them.
- All bytes in a public export, candidate, final runtime, deployment artifact, saved archive, pushed image, uploaded artifact, published image, or other distributed output require an approved redistribution-compatible record. Unknown, missing, incompatible, or non-redistributable licensing is a hard stop.
- The sole exception is metadata inventory for reviewer tag `mcr.microsoft.com/playwright/python:v1.62.0-noble`, index `sha256:aa81288e738725378becba5b3e06cb0f3a7f012a610e87e8d767a090ea3f740d`, linux/amd64 manifest `sha256:51d31fdfacb0cff99a1a724152e34ae408d2bd4e7da310ff157450f49261cc59`, Playwright `1.62.0`/tag `v1.62.0`, WebKit revision `2336`, version `26.5`, canonical-tree SHA-256 `c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c`, and upstream base commit `343e13bf22dca9d0ec227801419aab0f9001a32f`.
- Its SPDX package values are exactly `licenseDeclared="NOASSERTION"` and `licenseConcluded="NOASSERTION"`; its policy value is exactly `review_disposition="reviewer_test_only_not_redistributed"`; and its notice status is exactly `complete_digest_bound_notice=false`.
- Do not claim bitwise source-to-binary attestation, a complete digest-bound notice set, redistribution approval, or any guessed SPDX expression.
- Chromium revision `1234`, Firefox revision `1538`, ffmpeg revision `1011`, both base/OS inventories, every Python package, and every deployed/public component remain on the ordinary approved-only path.
- The reviewer image and all Chromium/Firefox/WebKit/ffmpeg bytes are local/CI-only. They may be pulled and executed by exact digest but never saved, exported, pushed, uploaded, published, deployed, emitted as build output, copied into a public candidate, or inherited by/present in the final runtime.
- Task 9, Task 11, and Task 13 are local/CI-only. Creating/changing an Actions Environment or variable, pushing Git/Hugging Face content, publishing an image/artifact, deploying, or changing any remote metadata remains forbidden.
- Do not read or modify `.env`, private data, Set B/Set C, model artifacts, scientific ledgers, or remote state.
- Use explicit file staging only. No `git add .`, `git add -A`, wildcard, or directory staging.

## Protected partial custody at plan creation

| Path | Bytes | SHA-256 |
| --- | ---: | --- |
| `scripts/build_hf_space_supply_chain.py` | 41006 | `2d76522a3eefa695fa3baa695fcb84d4b518a53e1c2fce18fcb3aada75c9cc03` |
| `tests/test_hf_space_supply_chain.py` | 6987 | `31d7f9f904c7a1198f1048291c50f56f2ce65ff7218b25fac5029e0d84608577` |
| `tools/space/requirements-runtime.in` | 15 | `32694e165aaad642c474c32b655b742ed60499f8e64e3df59a0edb952b608ffc` |
| `tools/space/requirements-dev.in` | 235 | `eb2e873569c0a8a435d4173d88dc1221ef9b607f6fcadf5ee4c1ea0f72e8f719` |
| `tools/space/lock-tooling.txt` | 6228 | `2fb9a7ba1320540ff0a30dc6d18c1e7e64a4216b90a0de103bdb9376f137e63b` |
| `tools/space/base-image.json` | 150027 | `bc919a88f44fbc8a42941f1660e908a59a0c9b72a2ba9779f117f5d7650a4d0d` |
| `space/requirements.lock` | 4971 | `f7fdd6a12df45f74ea241ae4159d50f3aac71490e5d73b2bdc08e2dbde7d6a22` |
| `space/requirements-dev.lock` | 11193 | `bc70694deaab02f14d4a2edf100989ba031192d0252b48467ca7f00d7ad42466` |

The implementing controller must compare all eight size/hash pairs before the first change. A mismatch is a stop for custody reconciliation, not permission to regenerate or discard a partial.

## File and interface map

### Task 7 policy core

- Modify: `scripts/build_hf_space_supply_chain.py` — exact WebKit exception constants, strict policy parser, SPDX emission, distribution-exclusion validator, and `verify_all` integration.
- Modify: `tests/test_hf_space_supply_chain.py` — RED/GREEN coverage and complete mutation matrix.
- Modify: `tools/space/base-image.json` — add exact WebKit version and provenance fields measured from the existing exact reviewer manifest; do not re-resolve to another image.
- Create: `tools/space/license-policy.json` — ordinary approved records plus the sole exact WebKit exception.
- Create: `space/SBOM.spdx.json` — deterministic SPDX 2.3 output with exact WebKit declared/concluded `NOASSERTION`.
- Create: `space/THIRD_PARTY_LICENSES.json` — deterministic reviewed inventory with exact disposition and notice-completeness flag.

### Downstream exclusion owners

- Modify: `scripts/export_hf_space.py`, `tests/test_hf_space_exporter.py`, `space/tests/test_export_contract.py` — Task 8 public-export exclusion.
- Modify: `space/Dockerfile`, `space/tests/test_container_contract.py`, `scripts/build_hf_space_supply_chain.py`, `tests/test_hf_space_supply_chain.py` — Task 9 independent runtime stage and no reviewer byte flow.
- Modify: `.github/workflows/space-ci.yml`, `tests/test_hf_space_source_boundary.py`, `tests/test_hf_space_supply_chain.py`, `tests/test_hf_space_exporter.py` — Task 11 ephemeral reviewer/no artifact or distribution command.
- Modify: `scripts/verify_hf_space_candidate.py`, `tests/test_hf_space_live_review.py` — Task 13 authoritative clean-export/runtime/deployment inspection and receipt fields.

### Fixed interfaces

```python
@dataclass(frozen=True)
class WebKitReviewerPolicy:
    reviewer_image_tag: str
    reviewer_index_digest: str
    reviewer_linux_amd64_digest: str
    playwright_version: str
    playwright_tag: str
    browsers_json_url: str
    registry_source_url: str
    cdn_artifact_url: str
    upstream_config_path: str
    upstream_base_commit: str
    webkit_revision: str
    webkit_version: str
    webkit_tree_sha256: str
    official_webkit_licensing_references: tuple[str, ...]
    license_declared: str
    license_concluded: str
    review_disposition: str
    complete_digest_bound_notice: bool

@dataclass(frozen=True)
class DistributionSurface:
    name: Literal[
        "public_export", "candidate", "runtime_stage", "final_image",
        "deployment_artifact", "saved_archive", "pushed_image",
    ]
    paths: tuple[str, ...]
    layer_digests: tuple[str, ...]
    content_sha256: tuple[str, ...]
    command_tokens: tuple[str, ...]

def exact_webkit_reviewer_policy() -> WebKitReviewerPolicy: ...
def validate_license_policy(document: Mapping[str, object]) -> Mapping[tuple[str, str], Mapping[str, object]]: ...
def validate_distribution_exclusion(surfaces: Sequence[DistributionSurface]) -> None: ...
def verify_all(repo_root: Path) -> None: ...
```

The exception validator compares a fully constructed immutable value to `exact_webkit_reviewer_policy()`. It does not accept subsets, default missing fields, a version range, an alternate platform, a truthy/falsy coercion, or an allowlist of `NOASSERTION` names.

---

### Task 1: Add the exact policy and mutation RED suite

**Files:**

- Modify: `tests/test_hf_space_supply_chain.py`

**Interfaces:**

- Consumes: current partial generator/base/locks and the fixed dataclasses above.
- Produces: named RED tests that fail against the current universal-approved parser and missing policy outputs.

- [ ] **Step 1: Add the exact positive-record fixture**

```python
def exact_webkit_policy_dict() -> dict[str, object]:
    return {
        "package": "webkit",
        "version": "26.5",
        "artifact_sha256": ["c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c"],
        "reviewer_image_tag": "mcr.microsoft.com/playwright/python:v1.62.0-noble",
        "reviewer_index_digest": "sha256:aa81288e738725378becba5b3e06cb0f3a7f012a610e87e8d767a090ea3f740d",
        "reviewer_linux_amd64_digest": "sha256:51d31fdfacb0cff99a1a724152e34ae408d2bd4e7da310ff157450f49261cc59",
        "playwright_version": "1.62.0",
        "playwright_tag": "v1.62.0",
        "browsers_json_url": "https://github.com/microsoft/playwright/blob/v1.62.0/packages/playwright-core/browsers.json",
        "registry_source_url": "https://github.com/microsoft/playwright/blob/v1.62.0/packages/playwright-core/src/server/registry/index.ts",
        "cdn_artifact_url": "https://cdn.playwright.dev/dbazure/download/playwright/builds/webkit/2336/webkit-ubuntu-24.04.zip",
        "upstream_config_path": "/ms-playwright/webkit-2336/UPSTREAM_CONFIG",
        "upstream_base_commit": "343e13bf22dca9d0ec227801419aab0f9001a32f",
        "webkit_revision": "2336",
        "webkit_version": "26.5",
        "webkit_tree_sha256": "c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c",
        "official_webkit_licensing_references": [
            "https://webkit.org/licensing-webkit/",
            "https://github.com/WebKit/WebKit/blob/343e13bf22dca9d0ec227801419aab0f9001a32f/Source/WebCore/LICENSE-APPLE",
            "https://github.com/WebKit/WebKit/blob/343e13bf22dca9d0ec227801419aab0f9001a32f/Source/WebCore/LICENSE-LGPL-2",
        ],
        "licenseDeclared": "NOASSERTION",
        "licenseConcluded": "NOASSERTION",
        "review_disposition": "reviewer_test_only_not_redistributed",
        "complete_digest_bound_notice": False,
    }
```

- [ ] **Step 2: Add and run the single-field mutation matrix**

Create `test_exact_webkit_reviewer_exception_rejects_every_single_field_drift`, parameterized over every fixture key after `package`/`version`, plus missing key, extra key, alternate list order, alternate case, integer revision, truthy string flag, guessed license expression, `approved` disposition, and `complete_digest_bound_notice=True`.

Run:

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_supply_chain.py -q
```

Expected: FAIL because `policy_records` rejects all `NOASSERTION` records and the policy/SBOM/license files do not exist.

- [ ] **Step 3: Add ordinary-component and distribution-surface mutations**

Add `test_noassertion_fails_for_public_or_any_other_component` for runtime base, reviewer base, Chromium, Firefox, ffmpeg, Gradio, an OS package, and a non-Gradio Python package. Add `test_reviewer_or_browser_bytes_fail_every_distribution_surface`, parameterized over all seven `DistributionSurface.name` values and signatures for reviewer manifest digest, `/ms-playwright`, WebKit tree digest, Chromium tree digest, Firefox tree digest, and `ffmpeg-1011`.

Run the same pytest command. Expected: the new tests remain RED without changing any generator/output.

### Task 2: Implement the separate exact exception and deterministic outputs

**Files:**

- Modify: `scripts/build_hf_space_supply_chain.py`
- Modify: `tools/space/base-image.json`
- Create: `tools/space/license-policy.json`
- Create: `space/SBOM.spdx.json`
- Create: `space/THIRD_PARTY_LICENSES.json`
- Test: `tests/test_hf_space_supply_chain.py`

**Interfaces:**

- Consumes: exact already measured reviewer manifest/tree plus policy fixture.
- Produces: `exact_webkit_reviewer_policy`, `validate_license_policy`, `validate_distribution_exclusion`, canonical outputs, and strict `verify_all`.

- [ ] **Step 1: Implement ordinary versus exception policy parsing**

Keep ordinary records on `review_disposition == "approved"` with nonempty, non-`NONE`, non-`NOASSERTION` declared and concluded fields. Match the WebKit key only after exact dict-key validation and immutable full-value equality. Reject every other `NOASSERTION` before output generation.

- [ ] **Step 2: Extend the measured base record without re-resolution**

Under `images.reviewer.embedded_browsers.webkit`, add exact `version="26.5"`, tagged Playwright references, CDN URL, `upstream_config.path`, `upstream_config.base_commit`, and the ordered official WebKit reference list from the fixture. Preserve the existing tag/index/manifest/content tree bytes. Validate that `UPSTREAM_CONFIG` is already inside the canonical 38-file tree; do not claim that the tree proves complete license notice coverage.

- [ ] **Step 3: Emit policy, license inventory, and SPDX**

For the WebKit inventory record, emit exact `licenseDeclared`, `licenseConcluded`, `review_disposition`, and boolean notice flag. For the SPDX package, emit both SPDX license fields as `NOASSERTION`. Emit ffmpeg as its own ordinary approved component. Do not derive an expression from the upstream reference text.

- [ ] **Step 4: Run GREEN and deterministic regeneration**

```powershell
.venv-space-lock\Scripts\python.exe scripts\build_hf_space_supply_chain.py inventory --base tools/space/base-image.json --runtime-lock space/requirements.lock --development-lock space/requirements-dev.lock --license-policy tools/space/license-policy.json --licenses-output space/THIRD_PARTY_LICENSES.json --sbom-output space/SBOM.spdx.json
.venv-space-lock\Scripts\python.exe scripts\build_hf_space_supply_chain.py verify --repo-root .
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_supply_chain.py -q
```

Hash `space/SBOM.spdx.json` and `space/THIRD_PARTY_LICENSES.json`, rerun `inventory`, and require identical hashes. Expected: GREEN; every mutation fails closed; ordinary records are approved-only; exact WebKit metadata is `NOASSERTION`/review-only/not-distributed.

- [ ] **Step 5: Commit the complete Task 7 source and outputs**

```powershell
git add -- tools/space/requirements-runtime.in tools/space/requirements-dev.in tools/space/lock-tooling.txt tools/space/base-image.json tools/space/license-policy.json scripts/build_hf_space_supply_chain.py tests/test_hf_space_supply_chain.py space/requirements.lock space/requirements-dev.lock space/SBOM.spdx.json space/THIRD_PARTY_LICENSES.json
git diff --cached --check
git commit -m 'build(space): constrain reviewer-only WebKit policy'
```

Expected: exactly the eleven Task 7 files are committed. Stop for fresh Task 7 review before Task 8.

### Task 3: Enforce metadata-only WebKit in the clean exporter

**Files:**

- Create: `scripts/export_hf_space.py`
- Create: `tests/test_hf_space_exporter.py`
- Modify: `space/tests/test_export_contract.py`

**Interfaces:**

- Consumes: canonical inventories plus exact public path maps.
- Produces: `assert_exact_webkit_metadata_only(candidate: Path) -> None` and reviewer-byte denylist evidence in `ExportReceipt`.

- [ ] **Step 1: Write exporter RED mutations**

Add `test_export_contains_webkit_policy_metadata_but_no_reviewer_or_browser_bytes` and parameterized `test_export_rejects_reviewer_or_browser_byte_signatures`. Mutate an extra path, an allowlisted runtime file, an allowlisted test file, a supply-chain file, and deployment-manifest content with each reviewer/browser signature.

- [ ] **Step 2: Run RED**

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_exporter.py space/tests/test_export_contract.py -q
```

Expected: FAIL because the exporter/exclusion interfaces do not exist.

- [ ] **Step 3: Implement metadata-only allowance and byte denial**

Allow exact WebKit strings only at the canonical JSON pointer for its package/component records in the two inventory files. Reject the reviewer manifest digest, `/ms-playwright`, embedded tree identities, executable/archive signatures, or reviewer artifact mappings elsewhere. Deployment manifest may record verification provenance but may not list the reviewer image/browser as a distributed source or destination.

- [ ] **Step 4: Run GREEN and commit**

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_exporter.py space/tests/test_export_contract.py -q
.venv-space\Scripts\ruff.exe check scripts/export_hf_space.py tests/test_hf_space_exporter.py space/tests/test_export_contract.py
git add -- scripts/export_hf_space.py tests/test_hf_space_exporter.py space/tests/test_export_contract.py
git diff --cached --check
git commit -m 'feat(space): exclude reviewer bytes from export'
```

### Task 4: Enforce independent reviewer and runtime stages

**Files:**

- Create: `space/Dockerfile`
- Create: `space/tests/test_container_contract.py`
- Modify: `scripts/build_hf_space_supply_chain.py`
- Modify: `tests/test_hf_space_supply_chain.py`

**Interfaces:**

- Consumes: exact reviewer/runtime base records and clean candidate.
- Produces: independent `test` and `runtime` stage graph; runtime exclusion evidence.

- [ ] **Step 1: Write Docker graph RED mutations**

Add `test_reviewer_stage_is_local_ci_only_and_cannot_flow_into_runtime_or_export` and `test_runtime_rejects_each_reviewer_byte_flow_mutation` for runtime-from-test ancestry, `COPY --from=test`, `/ms-playwright`, reviewer digest, Chromium/Firefox/WebKit/ffmpeg path, and save/export/push/output flags.

- [ ] **Step 2: Run RED**

```powershell
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests/test_container_contract.py tests/test_hf_space_supply_chain.py -q
```

Expected: FAIL because the Dockerfile and graph checks do not exist.

- [ ] **Step 3: Implement and verify independent stages**

Make `test` and `runtime` independent roots. Permit reviewer bytes only in `test`; prohibit cross-stage copies and distribution commands. Inspect final image history/filesystem and require zero reviewer/browser matches while retaining the two canonical metadata inventory files.

- [ ] **Step 4: Run GREEN and commit**

```powershell
$env:PYTHONPATH = (Resolve-Path space)
.venv-space\Scripts\python.exe -m pytest space/tests/test_container_contract.py tests/test_hf_space_supply_chain.py -q
git add -- space/Dockerfile space/tests/test_container_contract.py scripts/build_hf_space_supply_chain.py tests/test_hf_space_supply_chain.py
git diff --cached --check
git commit -m 'build(space): isolate reviewer from runtime bytes'
```

### Task 5: Make CI reviewer execution ephemeral and non-distributing

**Files:**

- Create: `.github/workflows/space-ci.yml`
- Modify: `tests/test_hf_space_source_boundary.py`
- Modify: `tests/test_hf_space_supply_chain.py`
- Modify: `tests/test_hf_space_exporter.py`

**Interfaces:**

- Consumes: exact reviewer digest, custody variables, and Task 11 checkout ownership boundary.
- Produces: local/CI-only reviewer runs with no artifact/image distribution path.

- [ ] **Step 1: Add workflow RED**

Add `test_ci_never_distributes_reviewer_image_or_browser_bytes`. Parse every `run` and `uses`; reject `docker save`, `docker export`, `docker push`, `buildx --push`, registry/OCI/Docker `--output`, `actions/upload-artifact`, reviewer image cache export, and any non-read permission. Mutation fixtures add each token independently and must fail.

- [ ] **Step 2: Run RED with controller custody**

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_source_boundary.py tests/test_hf_space_supply_chain.py tests/test_hf_space_exporter.py -q
```

Expected: FAIL because the workflow is absent; custody preflight must already have passed.

- [ ] **Step 3: Implement least-privilege ephemeral reviewer jobs**

Use exact reviewer digest only for `docker run --rm --network none --read-only`. Do not upload artifacts or export caches/images. Keep permissions `contents: read`. Preserve the separately approved checkout ownership and external custody transfers. Do not create or modify the Actions Environment/variables.

- [ ] **Step 4: Run GREEN and commit**

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_source_boundary.py tests/test_hf_space_supply_chain.py tests/test_hf_space_exporter.py -q
git add -- .github/workflows/space-ci.yml tests/test_hf_space_source_boundary.py tests/test_hf_space_supply_chain.py tests/test_hf_space_exporter.py
git diff --cached --check
git commit -m 'ci(space): keep reviewer artifacts local only'
```

### Task 6: Prove final export/runtime exclusion in the Task 13 receipt

**Files:**

- Modify: `scripts/verify_hf_space_candidate.py`
- Modify: `tests/test_hf_space_live_review.py`

**Interfaces:**

- Consumes: clean export, deployment manifest, final runtime image, ephemeral reviewer image, and exact policy record.
- Produces: final receipt fields for tuple equality and zero reviewer-byte distribution counts.

- [ ] **Step 1: Write receipt RED tests**

Add `test_final_receipt_binds_exact_webkit_reviewer_policy` and parameterized `test_final_verifier_rejects_reviewer_bytes_on_each_distribution_surface`. Require booleans `webkit_reviewer_exception_tuple_exact`, `webkit_spdx_declared_noassertion_exact`, `webkit_spdx_concluded_noassertion_exact`, `webkit_reviewer_test_only_not_redistributed_exact`, `webkit_complete_digest_bound_notice_false`, `public_export_approved_bytes_only`, `candidate_reviewer_bytes_absent`, `runtime_reviewer_bytes_absent`, `deployment_reviewer_bytes_absent`, and `reviewer_distribution_commands_absent`. Require zero counts for public export, candidate, runtime, deployment, and distribution commands.

- [ ] **Step 2: Run RED**

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_live_review.py tests/test_hf_space_supply_chain.py tests/test_hf_space_exporter.py space/tests/test_container_contract.py -q
```

Expected: FAIL because the verifier receipt lacks these fields.

- [ ] **Step 3: Implement authoritative inspections**

Before any test execution, scan the exact candidate tree and deployment mapping. After build, inspect stage graph, final history, final filesystem inventory, and planned Docker commands. Permit WebKit strings only at the two canonical metadata records; reject every reviewer/browser byte/path/layer elsewhere. Record the exact pipe-delimited tuple required by the main plan. Do not save/export/push/upload the reviewer/test image.

- [ ] **Step 4: Run final local GREEN**

```powershell
.venv-space\Scripts\python.exe scripts\verify_hf_space_candidate.py --repo-root (Resolve-Path .).Path --app-source-sha $appSourceSha --manifest-source-sha $manifestSourceSha
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_live_review.py tests/test_hf_space_supply_chain.py tests/test_hf_space_exporter.py space/tests/test_container_contract.py -q
```

Expected: receipt status `passed`; exact tuple fields true; all reviewer-byte counts zero; reviewer resource cleaned through exact ownership; no tracked file changes.

- [ ] **Step 5: Finish without another implementation commit**

Task 13 is verification-only after the app-source and manifest commits. Require clean `git status --porcelain=v1 --untracked-files=all`, `git diff --check`, and the exact two-commit provenance relationship. Stop for central review; do not push, upload, deploy, publish, or mutate remote metadata.

## Plan self-review checklist

- [ ] Exact tuple strings and digests occur consistently in design, main plan, generated policy, inventory, SPDX, and final receipt expectations.
- [ ] Only WebKit has `NOASSERTION`; both SPDX fields use it; no ordinary component is excepted.
- [ ] `reviewer_test_only_not_redistributed` and `complete_digest_bound_notice=false` are exact, typed values.
- [ ] Tests cover public/deployed `NOASSERTION`, every other-component `NOASSERTION`, every tuple/provenance/notice/exclusion field drift, and reviewer/browser bytes on every named distribution/runtime surface.
- [ ] Task 8, Task 9, Task 11, and Task 13 have independent enforcement; metadata presence is never confused with byte distribution.
- [ ] No prose claims source/binary attestation, complete notice, redistribution approval, or a guessed license expression.
- [ ] No remote action, private data, Set B/Set C, Task 8 implementation, or product partial change occurs during the docs-only corrective commit.
