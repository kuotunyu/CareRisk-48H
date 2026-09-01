# CareRisk 48H Task 7 WebKit Reviewer Policy Corrective Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Task 7 without weakening the public redistribution gate by inventorying one exact WebKit reviewer tuple as `NOASSERTION` and proving that its bytes remain local/CI-only and absent from every public, runtime, deployment, save, export, and push path.

**Architecture:** Keep the ordinary policy path universally approved-only. Route exactly one immutable reviewer WebKit record through a separate equality validator whose complete tuple, provenance, SPDX fields, disposition, notice-completeness flag, and exclusion evidence must match byte-for-byte constants. Carry only that record's metadata into the SBOM/license inventory; Task 8, Task 9, Task 11, and Task 13 independently prove that no reviewer or embedded-browser bytes reach a distributed surface.

**Tech Stack:** CPython 3.10 host control environment; exact Linux CPython 3.11.14 runtime image; exact Playwright Python 1.62.0 Ubuntu Noble reviewer image; canonical JSON; SPDX 2.3 JSON; pytest; Docker BuildKit; GitHub Actions YAML; SHA-256 canonical tree identities.

## Global Constraints

- Preserve the current Task 7 partials until the implementation session begins and its controller validates the custody table below. This docs-only correction does not authorize changing them.
- All bytes in a public export, candidate, runtime stage, final runtime, deployment artifact, saved archive, pushed image, uploaded artifact, published image, emitted build output, or other distributed output require an approved redistribution-compatible record. Unknown, missing, incompatible, or non-redistributable licensing is a hard stop.
- The sole exception is metadata inventory for reviewer tag `mcr.microsoft.com/playwright/python:v1.62.0-noble`, index `sha256:aa81288e738725378becba5b3e06cb0f3a7f012a610e87e8d767a090ea3f740d`, linux/amd64 manifest `sha256:51d31fdfacb0cff99a1a724152e34ae408d2bd4e7da310ff157450f49261cc59`, Playwright `1.62.0`/tag `v1.62.0`, WebKit revision `2336`, version `26.5`, immutable tree count/size `38`/`306401261`, and canonical-tree SHA-256 `c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c`. Its separate external source reference is exact: tag commit `e3950d9c140d007bd52853b45813c6274b24e36f`, relative path `browser_patches/webkit/UPSTREAM_CONFIG.sh`, raw URL `https://raw.githubusercontent.com/microsoft/playwright/e3950d9c140d007bd52853b45813c6274b24e36f/browser_patches/webkit/UPSTREAM_CONFIG.sh`, raw length `126`, raw SHA-256 `3554c5b666ed87032fb22e78956f8a2fffe1faede63ae8dcae60a26961f6419c`, parsed `REMOTE_URL=https://github.com/WebKit/WebKit.git`, `BASE_BRANCH=main`, and `BASE_REVISION=343e13bf22dca9d0ec227801419aab0f9001a32f`.
- Its SPDX package values are exactly `licenseDeclared="NOASSERTION"` and `licenseConcluded="NOASSERTION"`; its policy value is exactly `review_disposition="reviewer_test_only_not_redistributed"`; and its notice status is exactly `complete_digest_bound_notice=false`.
- The source reference proves only that Playwright `v1.62.0` source configuration declares the WebKit base revision. Do not claim that its file is in the binary image, bitwise source-to-binary attestation, a complete digest-bound notice set, redistribution approval, or any guessed SPDX expression.
- The controlled-acquisition phase may read only the exact commit-pinned raw URL and validates its raw bytes before retaining bounded parsed metadata/evidence in a verified GUID-owned OS-temp child; it never writes the raw source file or browser bytes into the repository, a public bundle, runtime, export, candidate, SBOM payload, or license-inventory payload. The later verify phase has no egress, consumes that explicit temp metadata path under a network bomb, and reads no remote input.
- Chromium revision `1234`, Firefox revision `1538`, ffmpeg revision `1011`, both base/OS inventories, every Python package, and every deployed/public component remain on the ordinary approved-only path.
- The reviewer image and all Chromium/Firefox/WebKit/ffmpeg bytes are local/CI-only. They may be pulled and executed by exact digest but never saved, exported, pushed, uploaded, published, deployed, emitted as build output, copied into a public candidate, or inherited by/present in the final runtime.
- Task 9, Task 11, and Task 13 are local/CI-only. Creating/changing an Actions Environment or variable, pushing Git/Hugging Face content, publishing an image/artifact, deploying, or changing any remote metadata remains forbidden.
- Do not read or modify `.env`, private data, Set B/Set C, model artifacts, scientific ledgers, or remote state.
- Use explicit file staging only. No `git add .`, `git add -A`, wildcard, or directory staging.

## Protected partial custody at plan creation

| Path | Bytes | SHA-256 |
| --- | ---: | --- |
| `scripts/build_hf_space_supply_chain.py` | 41006 | `2d76522a3eefa695fa3baa695fcb84d4b518a53e1c2fce18fcb3aada75c9cc03` |
| `tests/test_hf_space_supply_chain.py` | 16227 | `2cffc4e06e87550ef085ba5214e00a4641f0dabefc9a0d6b7ab0055e22cb3288` |
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
    playwright_tag_url: str
    browsers_json_url: str
    registry_source_url: str
    cdn_artifact_url: str
    playwright_tag_commit: str
    repository_relative_path: str
    commit_pinned_raw_url: str
    raw_byte_length: int
    raw_sha256: str
    remote_url: str
    base_branch: str
    base_revision: str
    webkit_revision: str
    webkit_version: str
    webkit_tree_file_count: int
    webkit_tree_total_bytes: int
    webkit_tree_algorithm: str
    webkit_tree_sha256: str
    image_tree_source_relative_path_absence_proof: Mapping[str, object]
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
        "uploaded_artifact", "published_image", "build_output",
        "other_distributed_output",
    ]
    paths: tuple[str, ...]
    layer_digests: tuple[str, ...]
    content_sha256: tuple[str, ...]
    command_tokens: tuple[str, ...]

def exact_webkit_reviewer_policy() -> WebKitReviewerPolicy: ...
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

def acquire_webkit_source_reference(*, url: str, metadata_output: Path, run_guid: str, allow_network: Literal[True]) -> WebKitSourceReference: ...
def load_webkit_source_reference(path: Path) -> WebKitSourceReference: ...
def verify_existing_locks(runtime_lock: Path, development_lock: Path, *, source_reference: WebKitSourceReference, offline: Literal[True], network_bomb: Literal[True]) -> None: ...
def verify_all(repo_root: Path, *, source_reference: WebKitSourceReference, offline: Literal[True], network_bomb: Literal[True]) -> None: ...
def run_network_bombed_child(*, source_reference: Path, offline: Literal[True], network_bomb: Literal[True], child_argv: Sequence[str]) -> int: ...
def validate_license_policy(document: Mapping[str, object]) -> Mapping[tuple[str, str], Mapping[str, object]]: ...
def validate_distribution_exclusion(surfaces: Sequence[DistributionSurface]) -> None: ...
```

`DISTRIBUTION_SURFACE_NAMES` is the exact ordered eleven-member tuple `("public_export", "candidate", "runtime_stage", "final_image", "deployment_artifact", "saved_archive", "pushed_image", "uploaded_artifact", "published_image", "build_output", "other_distributed_output")`. The validator rejects an omitted, duplicate, unknown, empty, or unclassified member before it inspects content. `other_distributed_output` is a mandatory fail-closed catchall for any real distribution mechanism that does not match the ten specifically named mechanisms.

The exception validator compares a fully constructed immutable value to `exact_webkit_reviewer_policy()`. It does not accept subsets, default missing fields, a version range, an alternate platform, a truthy/falsy coercion, or an allowlist of `NOASSERTION` names.

---

### Task 1: Add the exact policy and mutation RED suite

**Files:**

- Modify: `tests/test_hf_space_supply_chain.py`

**Interfaces:**

- Consumes: current partial generator/base/locks and the fixed dataclasses above.
- Produces: named RED tests that fail against the current universal-approved parser and missing policy outputs.

**Controlled-session chronology:** Before any Task 7 RED/test, the controller runs Task 0 below once, retains `$sourceRef` through Task 1/2 work, and performs the Task 2 `try`/`finally` cleanup only after outputs/receipts succeed. Every later pytest, `verify-images`, `verify-locks`, `inventory`, and `verify` command must pass `$sourceRef --offline --network-bomb`; the runner validates it and installs the bomb before any in-process work or child pytest `argv`. No source-reference file is tracked or exported.

- [ ] **Task 0: Start the sole controlled source-reference acquisition before RED**

The actual locks and image measurement are frozen partials. Do not invoke `lock`, `resolve-images`, registry inspection, or any historic dependency/wheel acquisition in this corrective resume. The only permitted egress is the exact raw-source metadata acquisition below.

```powershell
$task7Guid = [guid]::NewGuid().ToString('N')
$task7OsTempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$task7TempRoot = Join-Path $task7OsTempRoot "carerisk-task7-$task7Guid"
$sourceRef = Join-Path $task7TempRoot 'webkit-source-reference.json'
if (([IO.Path]::GetFileName($task7TempRoot) -cne "carerisk-task7-$task7Guid") -or -not ([IO.Path]::GetFullPath($task7TempRoot).StartsWith($task7OsTempRoot, [StringComparison]::Ordinal)) -or [IO.Path]::GetFullPath($task7TempRoot).Equals($task7OsTempRoot, [StringComparison]::Ordinal)) { throw 'Task 7 temp root is not an owned OS-temp child' }
New-Item -ItemType Directory -LiteralPath $task7TempRoot -ErrorAction Stop | Out-Null
try {
    & .venv-space-lock\Scripts\python.exe scripts\build_hf_space_supply_chain.py acquire-webkit-source-reference --url https://raw.githubusercontent.com/microsoft/playwright/e3950d9c140d007bd52853b45813c6274b24e36f/browser_patches/webkit/UPSTREAM_CONFIG.sh --metadata-output $sourceRef --run-guid $task7Guid --allow-network
    if (-not (Test-Path -LiteralPath $sourceRef -PathType Leaf)) { throw 'Task 7 source-reference metadata was not created' }
} catch {
    if ((Test-Path -LiteralPath $task7TempRoot -PathType Container) -and ([IO.Path]::GetFileName((Resolve-Path -LiteralPath $task7TempRoot).Path) -ceq "carerisk-task7-$task7Guid")) { Remove-Item -LiteralPath $task7TempRoot -Recurse -Force -ErrorAction Stop }
    throw
}
```

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
        "playwright_tag_url": "https://github.com/microsoft/playwright/tree/v1.62.0",
        "browsers_json_url": "https://github.com/microsoft/playwright/blob/v1.62.0/packages/playwright-core/browsers.json",
        "registry_source_url": "https://github.com/microsoft/playwright/blob/v1.62.0/packages/playwright-core/src/server/registry/index.ts",
        "cdn_artifact_url": "https://cdn.playwright.dev/dbazure/download/playwright/builds/webkit/2336/webkit-ubuntu-24.04.zip",
        "playwright_tag_commit": "e3950d9c140d007bd52853b45813c6274b24e36f",
        "repository_relative_path": "browser_patches/webkit/UPSTREAM_CONFIG.sh",
        "commit_pinned_raw_url": "https://raw.githubusercontent.com/microsoft/playwright/e3950d9c140d007bd52853b45813c6274b24e36f/browser_patches/webkit/UPSTREAM_CONFIG.sh",
        "raw_byte_length": 126,
        "raw_sha256": "3554c5b666ed87032fb22e78956f8a2fffe1faede63ae8dcae60a26961f6419c",
        "remote_url": "https://github.com/WebKit/WebKit.git",
        "base_branch": "main",
        "base_revision": "343e13bf22dca9d0ec227801419aab0f9001a32f",
        "webkit_revision": "2336",
        "webkit_version": "26.5",
        "webkit_tree_file_count": 38,
        "webkit_tree_total_bytes": 306401261,
        "webkit_tree_algorithm": "sha256-canonical-tree-v1",
        "webkit_tree_sha256": "c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c",
        "image_tree_source_relative_path_absence_proof": {
            "repository_relative_path": "browser_patches/webkit/UPSTREAM_CONFIG.sh",
            "canonical_tree_algorithm": "sha256-canonical-tree-v1",
            "canonical_tree_file_count": 38,
            "canonical_tree_total_bytes": 306401261,
            "canonical_tree_sha256": "c9df99c2d0597f5c9d6bc8084a83c6ab9e929a17282859bee951cedc87562c8c",
            "present": False,
        },
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

Create `test_exact_webkit_reviewer_exception_rejects_every_single_field_drift`, parameterized over every fixture key after `package`/`version`, explicitly including `playwright_tag_commit`, `repository_relative_path`, `commit_pinned_raw_url`, `raw_byte_length`, `raw_sha256`, `remote_url`, `base_branch`, `base_revision`, `webkit_tree_file_count`, `webkit_tree_total_bytes`, `image_tree_source_relative_path_absence_proof`, `playwright_tag_url`, and `webkit_tree_algorithm`, plus missing key, extra key, alternate list order, alternate case, integer revision, truthy string flag, guessed license expression, `approved` disposition, and `complete_digest_bound_notice=True`. Mutate every nested absence-proof member independently as well. Add `test_webkit_source_relative_file_is_absent_from_immutable_image_tree`; it derives the whole typed absence proof from the canonical inventory's ordered paths while independently checking exact count, total bytes, algorithm, and digest, rather than accepting any self-asserted boolean or nested map. Add `test_source_reference_phase_contract_rejects_every_control_mutation` for omitted/false `--allow-network`, nonliteral or alternate URL, metadata path outside the GUID child, missing/wrong run GUID, any offline command missing/false `--offline` or `--network-bomb`, source-reference path drift, and phase inversion; add `test_offline_test_installs_network_bomb_before_child_argv` and reject a positive test call that omits a required typed argument.

Run:

```powershell
& .venv-space-lock\Scripts\python.exe scripts\build_hf_space_supply_chain.py offline-test --source-reference $sourceRef --offline --network-bomb -- .venv-space\Scripts\python.exe -m pytest tests/test_hf_space_supply_chain.py -q
```

Expected: FAIL because `policy_records` rejects all `NOASSERTION` records and the policy/SBOM/license files do not exist.

- [ ] **Step 3: Add ordinary-component and distribution-surface mutations**

Add `test_noassertion_fails_for_public_or_any_other_component` for runtime base, reviewer base, Chromium, Firefox, ffmpeg, Gradio, an OS package, and a non-Gradio Python package. Add `test_reviewer_or_browser_bytes_fail_every_distribution_surface`, parameterized over all eleven `DISTRIBUTION_SURFACE_NAMES` values and signatures for reviewer manifest digest, `/ms-playwright`, WebKit tree digest, Chromium tree digest, Firefox tree digest, and `ffmpeg-1011`. Add `test_distribution_surface_registry_is_closed_and_complete`, parameterized over omitted, duplicate, unknown, empty, and unclassified surface fixtures.

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

- [ ] **Step 2: Extend the frozen measured base record without re-resolution**

Under `images.reviewer.embedded_browsers.webkit`, add exact `version="26.5"`, `tree_algorithm="sha256-canonical-tree-v1"`, typed `tree_file_count=38`, typed `tree_total_bytes=306401261`, and typed `image_tree_source_relative_path_absence_proof` containing the exact source relative path, canonical-tree algorithm/count/bytes/digest, and `present=false`, derived from the canonical inventory rather than trusted as input. Add Playwright tag URL/tagged source references/CDN URL and an external `source_reference` object containing every exact tag-commit/relative-path/raw-URL/raw-byte/parsed-assignment field from the fixture. Preserve the existing tag/index/manifest/content-tree values byte-for-byte. The strict parser recomputes count/bytes and the whole absence proof from the canonical inventory before full tuple equality; it rejects a missing, non-integer, wrong count/size, wrong algorithm/digest, wrong nested proof member, or self-asserted absence claim. The current correction must call only the read-only `verify-images --input tools/space/base-image.json`; it must not call `resolve-images`, query for a replacement, overwrite the record from registry output, or select another tag/platform. A legitimate future re-resolution is outside this plan and requires separate central design approval, a newly fixed tuple, fresh measurement/license review, updated single-field and surface mutations, and a new custody baseline. Separately acquire and validate the source file only during the controlled HTTPS source-reference phase. Do not claim that either result proves complete license notice coverage.

- [ ] **Step 3: Emit policy, license inventory, and SPDX**

For the WebKit inventory record, emit exact `licenseDeclared`, `licenseConcluded`, `review_disposition`, and boolean notice flag. For the SPDX package, emit both SPDX license fields as `NOASSERTION`. Emit ffmpeg as its own ordinary approved component. Do not derive an expression from the upstream reference text.

- [ ] **Step 4: Run GREEN and deterministic regeneration**

```powershell
$task7Succeeded = $false
try {
& .venv-space-lock\Scripts\python.exe scripts\build_hf_space_supply_chain.py verify-images --input tools/space/base-image.json --source-reference $sourceRef --offline --network-bomb
& .venv-space-lock\Scripts\python.exe scripts\build_hf_space_supply_chain.py verify-locks --runtime-lock space/requirements.lock --development-lock space/requirements-dev.lock --source-reference $sourceRef --offline --network-bomb
& .venv-space-lock\Scripts\python.exe scripts\build_hf_space_supply_chain.py inventory --base tools/space/base-image.json --runtime-lock space/requirements.lock --development-lock space/requirements-dev.lock --license-policy tools/space/license-policy.json --source-reference $sourceRef --licenses-output space/THIRD_PARTY_LICENSES.json --sbom-output space/SBOM.spdx.json --offline --network-bomb
& .venv-space-lock\Scripts\python.exe scripts\build_hf_space_supply_chain.py verify --repo-root . --source-reference $sourceRef --offline --network-bomb
& .venv-space-lock\Scripts\python.exe scripts\build_hf_space_supply_chain.py offline-test --source-reference $sourceRef --offline --network-bomb -- .venv-space\Scripts\python.exe -m pytest tests/test_hf_space_supply_chain.py -q
$task7InventoryOutputs = @('space/SBOM.spdx.json', 'space/THIRD_PARTY_LICENSES.json')
$first = @($task7InventoryOutputs | ForEach-Object { $item = Get-FileHash -Algorithm SHA256 -LiteralPath $_; '{0}|{1}' -f $_, $item.Hash.ToLowerInvariant() })
& .venv-space-lock\Scripts\python.exe scripts\build_hf_space_supply_chain.py inventory --base tools/space/base-image.json --runtime-lock space/requirements.lock --development-lock space/requirements-dev.lock --license-policy tools/space/license-policy.json --source-reference $sourceRef --licenses-output space/THIRD_PARTY_LICENSES.json --sbom-output space/SBOM.spdx.json --offline --network-bomb
$second = @($task7InventoryOutputs | ForEach-Object { $item = Get-FileHash -Algorithm SHA256 -LiteralPath $_; '{0}|{1}' -f $_, $item.Hash.ToLowerInvariant() })
if ([string]::Join("`n", $first) -cne [string]::Join("`n", $second)) { throw 'Task 7 inventory is not reproducible' }
$task7Succeeded = $true
} finally {
    if ($task7Succeeded) {
        $resolvedTask7Root = (Resolve-Path -LiteralPath $task7TempRoot -ErrorAction Stop).Path
        $resolvedSourceRef = (Resolve-Path -LiteralPath $sourceRef -ErrorAction Stop).Path
        if (-not $resolvedTask7Root.StartsWith($task7OsTempRoot, [StringComparison]::Ordinal) -or -not $resolvedSourceRef.StartsWith($resolvedTask7Root, [StringComparison]::Ordinal) -or ([IO.Path]::GetFileName($resolvedTask7Root) -cne "carerisk-task7-$task7Guid")) { throw 'Refusing to clean an unowned Task 7 temp path' }
        Remove-Item -LiteralPath $resolvedTask7Root -Recurse -Force -ErrorAction Stop
    } else { Write-Error "Task 7 failed; retain bounded GUID-owned parsed metadata at $task7TempRoot for diagnosis. Never stage, copy, export, or upload it." }
}
```

Task 0's `acquire-webkit-source-reference` is the sole network-enabled interface and accepts only the literal URL, literal `--allow-network`, owned metadata path, and GUID. It validates raw length/hash and exact `REMOTE_URL`, `BASE_BRANCH`, and `BASE_REVISION`; it records only bounded parsed canonical metadata/evidence in the named GUID-owned OS-temp file, never raw source bytes. It is not a twelfth repository file or export input. Every later `verify-images`, `verify-locks`, both `inventory` runs, `verify`, and pytest command takes that exact `$sourceRef` under `--offline --network-bomb`; the runner loads/validates it and installs the bomb before work or child execution, so no later command may fetch or refetch. The finalizer cleans only an existing, resolved, exact GUID-named child of the verified OS temp root after all outputs/receipts succeed. A failed run retains the bounded owned metadata file for diagnosis, but it is never staged, copied into the repository, exported, uploaded, or used as a public bundle input. Only parsed canonical metadata necessary downstream is represented in the sanctioned policy/inventory outputs. Expected: GREEN; every mutation fails closed; ordinary records are approved-only; exact WebKit metadata is `NOASSERTION`/review-only/not-distributed.

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
- Produces: final receipt fields for complete tuple equality, the exact closed surface registry, and one zero reviewer-byte count per surface.

```python
WEBKIT_REVIEWER_POLICY_TUPLE_FIELDS = (
    "reviewer_image_tag", "reviewer_index_digest", "reviewer_linux_amd64_digest",
    "playwright_version", "playwright_tag", "playwright_tag_url",
    "browsers_json_url", "registry_source_url", "cdn_artifact_url",
    "playwright_tag_commit", "repository_relative_path", "commit_pinned_raw_url",
    "raw_byte_length", "raw_sha256", "remote_url", "base_branch", "base_revision", "webkit_revision",
    "webkit_version", "webkit_tree_file_count", "webkit_tree_total_bytes", "webkit_tree_algorithm", "webkit_tree_sha256", "image_tree_source_relative_path_absence_proof",
    "official_webkit_licensing_references", "license_declared",
    "license_concluded", "review_disposition", "complete_digest_bound_notice",
)

REVIEWER_BYTE_COUNT_FIELDS = {
    "public_export": "public_export_reviewer_byte_count",
    "candidate": "candidate_reviewer_byte_count",
    "runtime_stage": "runtime_stage_reviewer_byte_count",
    "final_image": "final_image_reviewer_byte_count",
    "deployment_artifact": "deployment_artifact_reviewer_byte_count",
    "saved_archive": "saved_archive_reviewer_byte_count",
    "pushed_image": "pushed_image_reviewer_byte_count",
    "uploaded_artifact": "uploaded_artifact_reviewer_byte_count",
    "published_image": "published_image_reviewer_byte_count",
    "build_output": "build_output_reviewer_byte_count",
    "other_distributed_output": "other_distributed_output_reviewer_byte_count",
}
```

The receipt serializes `webkit_reviewer_policy_tuple` as the ordered values for every field above, including the ordered three-member official licensing-reference array, and serializes `distribution_surface_names` as exactly `DISTRIBUTION_SURFACE_NAMES`. It emits no abbreviated tuple, inferred defaults, or alternate surface aliases.

- [ ] **Step 1: Write receipt RED tests**

Add `test_final_receipt_binds_complete_webkit_reviewer_policy_tuple`, parameterized `test_final_verifier_rejects_reviewer_bytes_on_each_distribution_surface`, `test_final_receipt_requires_zero_count_for_each_distribution_surface`, and `test_final_verifier_rejects_nonclosed_distribution_surface_registry`. The tuple test compares all `WEBKIT_REVIEWER_POLICY_TUPLE_FIELDS` against `exact_webkit_policy_dict()`, including tag URL, tagged `browsers.json`, registry, CDN, exact source tag commit/relative path/raw URL/raw length/raw hash/parsed `REMOTE_URL`/`BASE_BRANCH`/`BASE_REVISION`, explicit image-tree absence, tree algorithm, tree digest, and the ordered official licensing references. Parameterize tuple mutations over every field and surface mutations over all eleven names plus omitted, duplicate, unknown, empty, and unclassified registries.

Require booleans `webkit_reviewer_exception_tuple_exact`, `webkit_spdx_declared_noassertion_exact`, `webkit_spdx_concluded_noassertion_exact`, `webkit_reviewer_test_only_not_redistributed_exact`, `webkit_complete_digest_bound_notice_false`, `public_export_approved_bytes_only`, `candidate_reviewer_bytes_absent`, `runtime_stage_reviewer_bytes_absent`, `final_image_reviewer_bytes_absent`, `deployment_artifact_reviewer_bytes_absent`, `saved_archive_reviewer_bytes_absent`, `pushed_image_reviewer_bytes_absent`, `uploaded_artifact_reviewer_bytes_absent`, `published_image_reviewer_bytes_absent`, `build_output_reviewer_bytes_absent`, `other_distributed_output_reviewer_bytes_absent`, `distribution_surface_registry_exact`, and `reviewer_distribution_commands_absent`. Require every value in `REVIEWER_BYTE_COUNT_FIELDS` to be present as an integer and equal zero; a missing, non-integer, duplicate/aliased, or nonzero count fails.

- [ ] **Step 2: Run RED**

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_live_review.py tests/test_hf_space_supply_chain.py tests/test_hf_space_exporter.py space/tests/test_container_contract.py -q
```

Expected: FAIL because the verifier receipt lacks these fields.

- [ ] **Step 3: Implement authoritative inspections**

Before any test execution, scan the public export, exact candidate tree, deployment mapping, and any upload/publication/build-output plan. After build, inspect the runtime stage graph, final history/filesystem inventory, saved-archive and pushed-image plans, and every other distributed-output classification. Permit WebKit strings only at the two canonical metadata records; reject every reviewer/browser byte/path/layer elsewhere. Record the complete ordered tuple and exact surface registry required by the main plan. An absent inspection or output class is still represented by its named surface with zero observed reviewer bytes and authoritative evidence that no such path exists; it is never omitted. Do not save/export/push/upload/publish or otherwise distribute the reviewer/test image.

- [ ] **Step 4: Run final local GREEN**

```powershell
.venv-space\Scripts\python.exe scripts\verify_hf_space_candidate.py --repo-root (Resolve-Path .).Path --app-source-sha $appSourceSha --manifest-source-sha $manifestSourceSha
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_live_review.py tests/test_hf_space_supply_chain.py tests/test_hf_space_exporter.py space/tests/test_container_contract.py -q
```

Expected: receipt status `passed`; every complete tuple field matches; the exact eleven-member registry is present; all eleven reviewer-byte counts are integer zero; reviewer resource is cleaned through exact ownership; no tracked file changes.

- [ ] **Step 5: Finish without another implementation commit**

Task 13 is verification-only after the app-source and manifest commits. Require clean `git status --porcelain=v1 --untracked-files=all`, `git diff --check`, and the exact two-commit provenance relationship. Stop for central review; do not push, upload, deploy, publish, or mutate remote metadata.

## Plan self-review checklist

- [ ] Exact tuple strings and digests, source-reference names, and image-tree-absence evidence occur consistently in design, main plan, generated policy, inventory, SPDX, and final receipt expectations.
- [ ] Only WebKit has `NOASSERTION`; both SPDX fields use it; no ordinary component is excepted.
- [ ] `reviewer_test_only_not_redistributed` and `complete_digest_bound_notice=false` are exact, typed values.
- [ ] Tests cover public/deployed `NOASSERTION`, every other-component `NOASSERTION`, every tuple/provenance/notice/exclusion field drift, image-tree absence, and reviewer/browser bytes on every named distribution/runtime surface.
- [ ] Task 8, Task 9, Task 11, and Task 13 have independent enforcement; metadata presence is never confused with byte distribution.
- [ ] No prose claims that a source file is in the binary image, source/binary attestation, complete notice, redistribution approval, or a guessed license expression.
- [ ] No remote action, private data, Set B/Set C, Task 8 implementation, or product partial change occurs during the docs-only corrective commit.
