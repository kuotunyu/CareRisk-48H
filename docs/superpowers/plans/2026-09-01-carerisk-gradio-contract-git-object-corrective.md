# CareRisk Gradio Contract Git-Object Corrective Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the exhausted Gradio test-source self-policing architecture with a controller-custodied Git-object identity gate while keeping the reviewed executable Gradio contract bytes and every product boundary frozen.

**Architecture:** Architecture C does not interpret `space/tests/test_gradio_contract.py` with another candidate-controlled Python meta-scanner. A generic boundary helper receives the expected tuple only from controller custody, resolves the target path to a Git object, and verifies the object's type, SHA-1, raw size, and raw SHA-256 using `git cat-file`. Direct raw-object source review and execution of the exact target suite remain separate safety gates because object identity proves provenance, not correctness.

**Tech Stack:** Git object plumbing (`rev-parse`, `cat-file`, `hash-object`), CPython 3.11, pytest, `hashlib`, `subprocess`, Ruff, strict Mypy, and task-owned temporary bare Git repositories.

## Global Constraints

- This is a qualitatively distinct Architecture C after two explicit architecture breakers. It is not closed-world fix round 3 and must not extend the alias evaluator or source-token AST patch series.
- Authoring parent is exact clean HEAD `b256f1757e604302d7c5cbfc52b2dd44ce26236e` on branch `docs/carerisk-hf-space-design`, remote `https://github.com/kuotunyu/CareRisk-48H.git`.
- The implementation BASE is the fresh-reviewed docs commit descended directly from that authoring parent. The controller records its exact lowercase 40-hex SHA as `CARERISK_GIT_OBJECT_CORRECTIVE_BASE` in the ignored task brief and custody ledger; implementation must verify exact equality and a clean tracked tree before editing.
- Commit identity is exactly `kuotunyu <61350295+kuotunyu@users.noreply.github.com>` with no co-author.
- Implementation modifies only `tests/test_hf_space_source_boundary.py`.
- `space/tests/test_gradio_contract.py` remains unchanged and resolves to blob SHA-1 `7c75d61c53eccdc93f69e7e3bb1eb09346eb5f04`, raw size `64847`, raw SHA-256 `101893daf6f20f9b507a00d0ac8da7fa383f83007520b4db61b710d1814df2a8`.
- The expected tuple is supplied only by the controller's ignored task brief/custody ledger through process environment. No tracked test constant, fallback, repository manifest, deployment manifest, generated candidate file, docs parser, or candidate-controlled fixture may supply or change it.
- Git-object bytes come only from `git cat-file blob`. `Path.read_bytes`, `open`, checkout content, PowerShell `Get-Content`, text-mode reads, newline conversion, and hashing a working-tree file are not identity authority.
- Do not change any product/application source, the target Gradio contract file, evidence, release, dependency, Docker, CI, model, data, checkpoint, Set B/Set C, or private custody asset.
- Do not read `.env`, private data/research artifacts, models, checkpoints, scientific locks, Set B/Set C, or unapproved evaluation outputs.
- Do not push, deploy, create/update a Hugging Face Space, mutate GitHub/Hugging Face metadata, or start a persistent service.
- Preserve the accepted application-source scanner, entry-point structural audit, `PublicSurfaceGuard` constructor audit, exporter/public-path checks, and frozen product/source gates.
- Never stage broadly. The implementation commit stages exactly `tests/test_hf_space_source_boundary.py`.

## Architecture-breaker history

- The bounded reflection alias evaluator ended after three rejected candidates; its mapping/callable fixed-point work is permanently superseded.
- The successor closed-world source-token architecture also ended after three rejected candidates: `84e2eaa508ac37f9b4d533efffc2da79c8ca1099`, `28e8ce88c8a6248516bf36d7bcbd624f0af8d24e`, and `b256f1757e604302d7c5cbfc52b2dd44ce26236e`.
- The decisive third-candidate Critical was architectural: canonical mutation ownership compared only a nearest function name, so duplicate, nested, or dead same-named functions could replace or suppress the executable pytest test while both candidate-controlled scanners returned no findings.
- All three candidates remain rejected. Architecture C may reuse the already-reviewed target Gradio blob as an immutable input, but it does not retroactively approve any retired scanner implementation.

## File and interface map

| Path | Responsibility after this corrective |
| --- | --- |
| `tests/test_hf_space_source_boundary.py` | Retains application/export boundary checks; removes Gradio-source meta-scanners; generically validates a controller-supplied Git-object tuple and exercises eight temporary-object mutations. |
| `space/tests/test_gradio_contract.py` | Frozen executable Gradio contract. It is reviewed and run directly; it is never edited by this corrective. |
| `.superpowers/sdd/2026-09-01-carerisk-gradio-contract-git-object-corrective/task-1-brief.md` | Ignored controller authority: exact implementation BASE, exact expected tuple, exact commands, and scope. |
| `.superpowers/sdd/2026-09-01-carerisk-gradio-contract-git-object-corrective/progress.md` | Ignored custody and reconciliation record; never an implementation commit input. |
| `.superpowers/sdd/2026-09-01-carerisk-gradio-contract-git-object-corrective/task-1-report.md` | Ignored implementer evidence only. |

The tracked boundary file produces these generic interfaces:

```python
def _controller_gradio_contract_identity() -> tuple[str, int, str]:
    """Return strict (blob_sha1, raw_size, raw_sha256) from controller environment."""

def _git_bytes(
    repository: Path,
    *arguments: str,
    input_bytes: bytes | None = None,
) -> bytes:
    """Run Git plumbing without a shell and return exact stdout bytes."""

def _git_blob_bytes(repository: Path, object_id: str) -> bytes:
    """Return only `git cat-file blob <object_id>` stdout bytes."""

def _assert_git_blob_identity(
    repository: Path,
    object_id: str,
    expected: tuple[str, int, str],
) -> None:
    """Require blob type, SHA-1, cat-file size, raw length, and raw SHA-256."""
```

The three environment names are fixed, while their values have no tracked fallback:

```python
_GRADIO_CONTRACT_BLOB_ENV = "CARERISK_GRADIO_CONTRACT_BLOB_SHA1"
_GRADIO_CONTRACT_SIZE_ENV = "CARERISK_GRADIO_CONTRACT_RAW_SIZE"
_GRADIO_CONTRACT_SHA256_ENV = "CARERISK_GRADIO_CONTRACT_RAW_SHA256"
```

## Pre-implementation direct-source authority gate

No implementation is authorized until a fresh architecture reviewer approves the exact docs commit containing the governing design, original Task 6/7 reconciliation, and this plan with Critical `0`, Important `0`, and no unresolved contradiction. That review records the exact docs HEAD in the ignored ledger. The controller then dispatches a separate fresh raw-source reviewer before implementation. The raw-source reviewer receives the tuple through the ignored brief, not through candidate code, and uses Git plumbing against the exact object:

```bash
test "$(git cat-file -t "$CARERISK_GRADIO_CONTRACT_BLOB_SHA1")" = blob
test "$(git cat-file -s "$CARERISK_GRADIO_CONTRACT_BLOB_SHA1")" = "$CARERISK_GRADIO_CONTRACT_RAW_SIZE"
test "$(git cat-file blob "$CARERISK_GRADIO_CONTRACT_BLOB_SHA1" | sha256sum | cut -d' ' -f1)" = "$CARERISK_GRADIO_CONTRACT_RAW_SHA256"
test "$(git rev-parse HEAD:space/tests/test_gradio_contract.py)" = "$CARERISK_GRADIO_CONTRACT_BLOB_SHA1"
git cat-file blob "$CARERISK_GRADIO_CONTRACT_BLOB_SHA1"
```

The last command is the review source. The reviewer must inspect those raw bytes directly, not a checkout, `Path.read_bytes`, or `Get-Content`, and report whether the executable tests meaningfully cover static component/API absence, evidence-failure surfaces, the outer guard, exact entrypoint/mount/Uvicorn composition, route classification, package-asset containment, no-network/no-write effects, and the claimed monkeypatch/fixture seams. Approval requires Critical `0` and Important `0`; a hash match without that source finding is HOLD.

After those raw-object gates pass, the reviewer requires a clean tracked checkout
and runs pytest against the tracked target path whose `HEAD:` object was just
bound to the reviewed blob. Pytest imports checkout files under normal clean-tree
execution semantics; it does not execute the `cat-file` pipe, a temporary file,
or an extracted object. Checkout bytes therefore serve execution only and never
replace raw Git-object identity authority:

```powershell
if (@(git status --porcelain=v1 --untracked-files=all).Count -ne 0) { throw 'target-suite review requires a clean tracked checkout' }
if ((git rev-parse HEAD:space/tests/test_gradio_contract.py).Trim() -cne $env:CARERISK_GRADIO_CONTRACT_BLOB_SHA1) { throw 'checkout target is not bound to reviewed blob' }
$env:PYTHONPATH = (Resolve-Path space).Path
.venv-space\Scripts\python.exe -m pytest space/tests/test_gradio_contract.py -q
```

If the raw-source review or target suite fails, stop before implementation. Do not change the target file or update custody under this corrective.

---

### Task 1: Replace Gradio source self-policing with external Git-object identity

**Files:**
- Modify: `tests/test_hf_space_source_boundary.py`
- Verify unchanged: `space/tests/test_gradio_contract.py`
- Report only: `.superpowers/sdd/2026-09-01-carerisk-gradio-contract-git-object-corrective/task-1-report.md`

**Interfaces:**
- Consumes: exact `CARERISK_GIT_OBJECT_CORRECTIVE_BASE` and the three tuple values from the controller's ignored brief/ledger.
- Consumes: Git object database containing the frozen Gradio contract blob.
- Produces: strict controller-custody parsing; generic raw Git-object identity validation; one positive current-path test; eight temporary-object rejection cases.
- Preserves: application/source/import/reflection scanner behavior for `APP_SOURCES`, entrypoint structural audits, guard-constructor audits, exporter/public paths, and frozen product gates.

- [ ] **Step 1: Verify exact authority, custody, and frozen bytes**

Run these read-only gates before editing:

```powershell
if ((git rev-parse HEAD).Trim() -ne $env:CARERISK_GIT_OBJECT_CORRECTIVE_BASE) { throw 'wrong corrective BASE' }
if ((git status --porcelain=v1).Count -ne 0) { throw 'tracked worktree is not clean' }
if ((git branch --show-current).Trim() -ne 'docs/carerisk-hf-space-design') { throw 'wrong branch' }
if ((git remote get-url origin).Trim() -ne 'https://github.com/kuotunyu/CareRisk-48H.git') { throw 'wrong remote' }
foreach ($name in @(
    'CARERISK_GRADIO_CONTRACT_BLOB_SHA1',
    'CARERISK_GRADIO_CONTRACT_RAW_SIZE',
    'CARERISK_GRADIO_CONTRACT_RAW_SHA256'
)) {
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name))) {
        throw "missing controller custody: $name"
    }
}
if ((git rev-parse HEAD:space/tests/test_gradio_contract.py).Trim() -ne $env:CARERISK_GRADIO_CONTRACT_BLOB_SHA1) { throw 'target path object mismatch' }
if ((git cat-file -t $env:CARERISK_GRADIO_CONTRACT_BLOB_SHA1).Trim() -ne 'blob') { throw 'target is not a Git blob' }
if ((git cat-file -s $env:CARERISK_GRADIO_CONTRACT_BLOB_SHA1).Trim() -ne $env:CARERISK_GRADIO_CONTRACT_RAW_SIZE) { throw 'target raw size mismatch' }
```

Use Git Bash for the raw SHA-256 so PowerShell never performs text conversion:

```bash
test "$(git cat-file blob "$CARERISK_GRADIO_CONTRACT_BLOB_SHA1" | sha256sum | cut -d' ' -f1)" = "$CARERISK_GRADIO_CONTRACT_RAW_SHA256"
```

Expected: exact BASE, clean branch/remote, exact blob type/path/size/SHA-256. Any mismatch stops the task.

- [ ] **Step 2: Add eight strict RED temporary-object cases**

Add `hashlib`, `os`, `re`, and `subprocess` imports only if the retained boundary file does not already provide the required interfaces. Add strict custody parsing with no defaults:

```python
def _controller_gradio_contract_identity() -> tuple[str, int, str]:
    blob = os.environ.get(_GRADIO_CONTRACT_BLOB_ENV, "")
    size_text = os.environ.get(_GRADIO_CONTRACT_SIZE_ENV, "")
    sha256 = os.environ.get(_GRADIO_CONTRACT_SHA256_ENV, "")
    if re.fullmatch(r"[0-9a-f]{40}", blob) is None:
        raise AssertionError("controller Gradio blob custody is missing or malformed")
    if re.fullmatch(r"(?:0|[1-9][0-9]*)", size_text) is None:
        raise AssertionError("controller Gradio raw-size custody is missing or malformed")
    if re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
        raise AssertionError("controller Gradio SHA-256 custody is missing or malformed")
    return blob, int(size_text), sha256
```

Add the final shell-free raw Git helpers before the RED test. They are not the behavior under test in this step, but the temporary-object cases require them to reach the deliberately empty identity stub:

```python
def _git_bytes(
    repository: Path,
    *arguments: str,
    input_bytes: bytes | None = None,
) -> bytes:
    if not repository.is_dir():
        raise AssertionError("Git repository path is not a directory")
    if not arguments or any(
        "\x00" in argument or "\r" in argument or "\n" in argument
        for argument in arguments
    ):
        raise AssertionError("Git arguments are empty or malformed")
    completed = subprocess.run(
        ("git", *arguments),
        cwd=repository,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"git {' '.join(arguments)} failed with exit {completed.returncode}"
        )
    return completed.stdout

def _git_blob_bytes(repository: Path, object_id: str) -> bytes:
    return _git_bytes(repository, "cat-file", "blob", object_id)
```

Add a temporary RED-only identity stub that returns without rejecting. It exists only long enough to demonstrate eight failures and must not be committed:

```python
def _assert_git_blob_identity(
    repository: Path,
    object_id: str,
    expected: tuple[str, int, str],
) -> None:
    del repository, object_id, expected
```

Create the frozen source bytes only through `git cat-file blob`. Initialize every task-owned bare repository below pytest's `tmp_path` with exact `git init --bare --object-format=sha1`, require `git rev-parse --show-object-format` to return exact `sha1`, and only then write each mutation as a real temporary Git blob using `git hash-object -w --stdin`. Parameterize exactly these deterministic categories:

```python
_GRADIO_GIT_OBJECT_MUTATIONS = (
    "same_length_substitution",
    "insert_byte",
    "delete_byte",
    "lf_to_crlf",
    "prepend_utf8_bom",
    "remove_final_lf",
    "append_comment",
    "append_nul",
)

@pytest.mark.parametrize("mutation", _GRADIO_GIT_OBJECT_MUTATIONS)
def test_gradio_contract_git_object_rejects_mutated_git_objects(
    tmp_path: Path,
    mutation: str,
) -> None:
    expected = _controller_gradio_contract_identity()
    original = _git_blob_bytes(REPOSITORY_ROOT, expected[0])
    mutated = _mutate_gradio_contract_blob(original, mutation)
    assert mutated != original
    temporary_repository = _init_temporary_bare_repository(tmp_path)
    object_id = _write_temporary_blob(temporary_repository, mutated)
    with pytest.raises(AssertionError):
        _assert_git_blob_identity(temporary_repository, object_id, expected)
```

The mutation implementation must be exact and byte-oriented:

- `same_length_substitution`: replace the first `b"from __future__"` with `b"from __Future__"` and assert one replacement;
- `insert_byte`: insert `b" "` immediately after the first LF;
- `delete_byte`: delete the first byte and assert the source is nonempty;
- `lf_to_crlf`: assert at least one LF and no CRLF, then replace every LF with CRLF;
- `prepend_utf8_bom`: prefix `b"\xef\xbb\xbf"`;
- `remove_final_lf`: assert the source ends in one LF, then remove exactly that byte;
- `append_comment`: append `b"# git-object custody mutation\n"`;
- `append_nul`: append `b"\x00"`.

Use these concrete helpers; all source and mutation bytes remain binary:

```python
def _init_temporary_bare_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "gradio-contract-objects.git"
    _git_bytes(
        tmp_path,
        "init",
        "--bare",
        "--object-format=sha1",
        str(repository),
    )
    assert repository.is_dir()
    object_format = _git_bytes(
        repository,
        "rev-parse",
        "--show-object-format",
    ).decode("ascii").strip()
    assert object_format == "sha1"
    return repository

def _write_temporary_blob(repository: Path, raw: bytes) -> str:
    object_id = _git_bytes(
        repository,
        "hash-object",
        "-w",
        "--stdin",
        input_bytes=raw,
    ).decode("ascii").strip()
    if re.fullmatch(r"[0-9a-f]{40}", object_id) is None:
        raise AssertionError("git hash-object returned a malformed object ID")
    return object_id

def _mutate_gradio_contract_blob(raw: bytes, mutation: str) -> bytes:
    if mutation == "same_length_substitution":
        needle = b"from __future__"
        replacement = b"from __Future__"
        if raw.count(needle) != 1 or len(needle) != len(replacement):
            raise AssertionError("same-length mutation anchor is not exact")
        return raw.replace(needle, replacement, 1)
    if mutation == "insert_byte":
        index = raw.find(b"\n")
        if index < 0:
            raise AssertionError("LF insertion anchor is absent")
        return raw[: index + 1] + b" " + raw[index + 1 :]
    if mutation == "delete_byte":
        if not raw:
            raise AssertionError("cannot delete from an empty blob")
        return raw[1:]
    if mutation == "lf_to_crlf":
        if b"\n" not in raw or b"\r\n" in raw:
            raise AssertionError("LF-only mutation precondition failed")
        return raw.replace(b"\n", b"\r\n")
    if mutation == "prepend_utf8_bom":
        return b"\xef\xbb\xbf" + raw
    if mutation == "remove_final_lf":
        if not raw.endswith(b"\n"):
            raise AssertionError("final-LF mutation precondition failed")
        return raw[:-1]
    if mutation == "append_comment":
        return raw + b"# git-object custody mutation\n"
    if mutation == "append_nul":
        return raw + b"\x00"
    raise AssertionError(f"unknown Git-object mutation: {mutation}")
```

Run only the new mutation node:

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_source_boundary.py::test_gradio_contract_git_object_rejects_mutated_git_objects -q
```

Expected RED: exactly 8 collected and 8 failed with `DID NOT RAISE`; no collection error, skip, or unrelated failure. Record the output in the ignored report before replacing the stub.

- [ ] **Step 3: Implement generic Git-object validation and positive custody tests**

Retain the Step 2 shell-free Git helpers and replace only the RED identity stub with the complete validator:

```python
def _assert_git_blob_identity(
    repository: Path,
    object_id: str,
    expected: tuple[str, int, str],
) -> None:
    expected_blob, expected_size, expected_sha256 = expected
    if re.fullmatch(r"[0-9a-f]{40}", object_id) is None:
        raise AssertionError("candidate Git object ID is malformed")
    object_type = _git_bytes(repository, "cat-file", "-t", object_id).decode("ascii").strip()
    size_text = _git_bytes(repository, "cat-file", "-s", object_id).decode("ascii").strip()
    raw = _git_blob_bytes(repository, object_id)
    actual_size = int(size_text)
    actual = (object_id, actual_size, hashlib.sha256(raw).hexdigest())
    assert object_type == "blob"
    assert len(raw) == actual_size
    assert actual == (expected_blob, expected_size, expected_sha256)
```

The generic command wrapper must reject NULs/newlines in arguments, must invoke `git` without `shell=True`, and must never decode blob output. The temporary bare-repository helpers use the same wrapper for exact `git init --bare --object-format=sha1`, verify exact `sha1` before `git hash-object -w --stdin`, and validate the returned object ID as lowercase 40-hex before passing it to `cat-file`.

Add the positive path-binding test and strict no-fallback custody tests:

```python
def test_gradio_contract_git_object_matches_controller_custody() -> None:
    expected = _controller_gradio_contract_identity()
    object_id = _git_bytes(
        REPOSITORY_ROOT,
        "rev-parse",
        "HEAD:space/tests/test_gradio_contract.py",
    ).decode("ascii").strip()
    _assert_git_blob_identity(REPOSITORY_ROOT, object_id, expected)

@pytest.mark.parametrize(
    ("name", "value"),
    (
        (_GRADIO_CONTRACT_BLOB_ENV, ""),
        (_GRADIO_CONTRACT_BLOB_ENV, "A" * 40),
        (_GRADIO_CONTRACT_SIZE_ENV, "064847"),
        (_GRADIO_CONTRACT_SHA256_ENV, "g" * 64),
    ),
)
def test_gradio_contract_controller_custody_is_strict(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    monkeypatch.setenv(name, value)
    with pytest.raises(AssertionError):
        _controller_gradio_contract_identity()
```

The strict-custody node may mutate only the three process variables in the test process. It must not read tracked docs, manifests, the target source, or Git history to synthesize an expected value.

- [ ] **Step 4: Remove the retired self-policing architecture**

Delete `_gradio_test_source_violations`, `_guard_helper_violations`, and every constant/helper/test whose only transitive consumer is one of those functions. This includes the closed-world import/protected/member/canonical-call tables, current-source mutation builders, and the mutation nodes for protected re-exports, loader contexts, canonical `monkeypatch.setattr`, exact reflection parents, protected identity loads, semantic dunder bindings, monkeypatch loads, `sys.platform` contexts, source near-misses, sensitive member contexts, and guard-helper alias/reflection candidates.

Do not delete or weaken:

- `_tree`, `imported_roots`, or application capability/reflection scanning over `APP_SOURCES`;
- entrypoint composition/mount/Uvicorn structural audits over `space/app.py`;
- `_guard_constructor_violations` and its direct product-interface tests;
- public path, denylist, exporter, secret, binary, symlink, size, or existing-app exclusion checks;
- any frozen-product/source diff test unrelated to the retired Gradio meta-scanners.

Use reference searches before and after deletion. After GREEN, both retired symbol names and the old mutation node names must be absent. Do not leave compatibility wrappers, deprecated aliases, or an equivalent new Python-source interpreter under another name.

- [ ] **Step 5: Run targeted GREEN and custody-leak gates**

Run the positive identity, strict custody, and eight temporary-object cases:

```powershell
.venv-space\Scripts\python.exe -m pytest `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_git_object_matches_controller_custody `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_controller_custody_is_strict `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_git_object_rejects_mutated_git_objects `
  -q
```

Expected: one positive case, four strict-custody cases, and eight mutation cases all pass; no skip or collection error.

Prove that executable code, workflows, and manifests do not embed the expected values. Each `git grep` must return exit 1 and no match when scoped to `.github`, `tests`, `space`, `scripts`, and `tools`; tracked governance docs are intentionally outside this scan:

```powershell
foreach ($value in @(
    $env:CARERISK_GRADIO_CONTRACT_BLOB_SHA1,
    $env:CARERISK_GRADIO_CONTRACT_RAW_SIZE,
    $env:CARERISK_GRADIO_CONTRACT_RAW_SHA256
)) {
    git grep -n -F -- $value -- .github tests space scripts tools
    if ($LASTEXITCODE -eq 0) { throw 'controller custody leaked into candidate code or manifest' }
    if ($LASTEXITCODE -ne 1) { throw 'custody leak scan failed' }
}
```

Expected: no candidate code/manifest match. Environment variable *names* are expected in the generic boundary file; values are forbidden.

- [ ] **Step 6: Run full, static, frozen-scope, and raw-object GREEN gates**

```powershell
$env:PYTHONPATH = (Resolve-Path space).Path
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_source_boundary.py space/tests/test_export_contract.py -q
.venv-space\Scripts\python.exe -m pytest space/tests/test_gradio_contract.py -q
.venv-space\Scripts\python.exe -m ruff check tests/test_hf_space_source_boundary.py
.venv-space\Scripts\python.exe -m ruff format --check tests/test_hf_space_source_boundary.py
.venv-space\Scripts\python.exe -m mypy --strict tests/test_hf_space_source_boundary.py
git diff --check
git diff --exit-code $env:CARERISK_GIT_OBJECT_CORRECTIVE_BASE -- space/tests/test_gradio_contract.py space/app.py space/carerisk_space
git diff --name-only $env:CARERISK_GIT_OBJECT_CORRECTIVE_BASE
git status --short
```

Expected: full boundary/export and frozen Gradio suites pass with only already documented platform skips; Ruff, format, and strict Mypy pass; frozen target/product diff is empty; the only tracked changed path is `tests/test_hf_space_source_boundary.py`.

Repeat raw-object verification with Git Bash and require the controller tuple. This is independent of the Python test result:

```bash
test "$(git rev-parse HEAD:space/tests/test_gradio_contract.py)" = "$CARERISK_GRADIO_CONTRACT_BLOB_SHA1"
test "$(git cat-file -t "$CARERISK_GRADIO_CONTRACT_BLOB_SHA1")" = blob
test "$(git cat-file -s "$CARERISK_GRADIO_CONTRACT_BLOB_SHA1")" = "$CARERISK_GRADIO_CONTRACT_RAW_SIZE"
test "$(git cat-file blob "$CARERISK_GRADIO_CONTRACT_BLOB_SHA1" | wc -c | tr -d ' ')" = "$CARERISK_GRADIO_CONTRACT_RAW_SIZE"
test "$(git cat-file blob "$CARERISK_GRADIO_CONTRACT_BLOB_SHA1" | sha256sum | cut -d' ' -f1)" = "$CARERISK_GRADIO_CONTRACT_RAW_SHA256"
```

- [ ] **Step 7: Commit exact scope and request fresh review**

```powershell
git add -- tests/test_hf_space_source_boundary.py
git diff --cached --name-only
git diff --cached --check
git -c user.name=kuotunyu `
    -c user.email=61350295+kuotunyu@users.noreply.github.com `
    commit -m 'test(space): replace source self-policing with Git object identity'
```

Expected staged path is exactly `tests/test_hf_space_source_boundary.py`. Do not push.

The controller creates an exact BASE-to-HEAD review package and dispatches a fresh reviewer. Review must cover:

1. no target/product/evidence/dependency/Docker/CI change;
2. no candidate tuple value or fallback in executable code/manifests;
3. no checkout/text-mode byte authority;
4. no surviving or successor Gradio-source meta-scanner;
5. exact preservation of application/export/product boundary checks;
6. real temporary Git objects for all eight byte mutations;
7. strict missing/malformed custody failure;
8. direct raw-object review receipt and exact target-suite evidence.

Acceptance requires Spec ✅, Quality Approved, Critical `0`, Important `0`, followed by the controller independently rerunning every Step 5 and Step 6 gate. A candidate failure returns to architecture review; it does not authorize editing the frozen target or resurrecting either retired scanner architecture.

## Two-phase target-update workflow

This workflow governs every future legitimate change to `space/tests/test_gradio_contract.py`:

### Phase A — target source candidate

1. Start from the last accepted clean commit and old controller custody.
2. Change only `space/tests/test_gradio_contract.py` in a standalone commit.
3. Require the old identity gate to fail because `HEAD:space/tests/test_gradio_contract.py` changed.
4. Derive the candidate blob only with `git rev-parse` and `git cat-file`; do not hash checkout bytes.
5. Dispatch a fresh reviewer to inspect the exact raw candidate object and run the candidate target suite.
6. Approve only with Critical `0` and Important `0`. The controller records the candidate tuple and review receipt in ignored custody. Candidate code cannot edit that record.

### Phase B — custody activation

1. Begin only after Phase A approval.
2. Update the controller's ignored custody tuple to the approved object.
3. Do not amend or rewrite the Phase A target commit.
4. If the generic boundary mechanism needs no change, rerun it unchanged against new custody. If it needs a change, commit only `tests/test_hf_space_source_boundary.py` in a separate candidate; never include the target file.
5. Run identity, eight mutation, target-suite, full boundary/export, static, frozen-product, scope, clean-tree, and fresh-review gates.
6. Activate the tuple only after all gates pass. Any mismatch restores the last accepted custody and leaves the target candidate unreleased.

No target-file commit can update, infer, or carry its own expected tuple. No single reviewer approves both a target source change and a same-candidate tuple update.

## Post-acceptance external custody transport

Architecture C remains active after Task 6. For every local Task 7–13 process
that invokes `tests/test_hf_space_source_boundary.py`, the controller reads the
accepted tuple from the ignored custody ledger and injects exactly the same three
environment values used by this corrective. Each fresh task validates the
40-hex SHA-1, canonical unsigned decimal size, and 64-hex SHA-256 before pytest;
missing, inherited-but-stale, uppercase, signed, leading-zero, or otherwise
malformed values fail before collection. No later task reads governance docs or
Git history to reconstruct custody.

Task 11 may add tracked references to the three names only after its local
workflow-contract RED. A future remote run requires separate written authority
to create/use GitHub Actions Environment `carerisk-contract-custody` and set the
three external Actions variables. Both workflow jobs bind that environment and
map `${{ vars.CARERISK_GRADIO_CONTRACT_BLOB_SHA1 }}`,
`${{ vars.CARERISK_GRADIO_CONTRACT_RAW_SIZE }}`, and
`${{ vars.CARERISK_GRADIO_CONTRACT_RAW_SHA256 }}` into the process. The reviewer
`docker run` forwards every value with an explicit same-name `--env` argument.
The workflow performs the same fail-closed shape checks before tests or Docker,
and workflow-contract tests prove exact three-name transfer, preflight ordering,
explicit container forwarding, and absence of tuple values from tracked
workflow text. Controller leak scans cover `.github`, `tests`, `space`,
`scripts`, and `tools`. Task 11 does not authorize creating the Environment,
setting variables, triggering a remote workflow, or changing any other remote
metadata.

## Exact Task 7 release reconciliation

After Architecture C acceptance, the controller performs all ledger writes in ignored custody; the implementation commit does not edit ledgers. The final state must say exactly:

- reflection-boundary alias-evaluator candidates remain rejected and are superseded by Architecture C;
- closed-world candidates `84e2eaa508ac37f9b4d533efffc2da79c8ca1099`, `28e8ce88c8a6248516bf36d7bcbd624f0af8d24e`, and `b256f1757e604302d7c5cbfc52b2dd44ce26236e` remain rejected, with no fix round 3;
- the new corrective's direct raw-object review is approved for blob `7c75d61c53eccdc93f69e7e3bb1eb09346eb5f04`, raw size `64847`, raw SHA-256 `101893daf6f20f9b507a00d0ac8da7fa383f83007520b4db61b710d1814df2a8`;
- the Architecture C implementation candidate is accepted only after independent review and controller reruns;
- original HF Space plan Task 6 is complete via that accepted Architecture C commit, not via any rejected predecessor;
- the original ledger contains one `Task 7 released` entry whose `CARERISK_TASK7_RELEASE_SHA` is the accepted full lowercase 40-hex Architecture C commit;
- Task 7 preflight must require `HEAD == CARERISK_TASK7_RELEASE_SHA`, a clean tracked tree, and `HEAD:space/tests/test_gradio_contract.py == CARERISK_GRADIO_CONTRACT_BLOB_SHA1` before any supply-chain file is changed.

If any item is missing or inconsistent, Task 7 remains blocked. No ledger release authorizes push, deployment, Hugging Face/GitHub mutation, or access to private evidence.
