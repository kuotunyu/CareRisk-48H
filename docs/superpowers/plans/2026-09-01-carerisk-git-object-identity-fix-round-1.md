# CareRisk Git-Object Identity Fix Round 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden Architecture C Git-object identity plumbing against ambient repository redirection and unbounded Git subprocesses without changing the frozen target, controller tuple, or any non-boundary product behavior.

**Architecture:** Keep the generic external-custody identity architecture, but place every Git invocation behind one bounded binary runner. The runner uses a resolved absolute Git executable, a deterministic minimal environment, a fixed timeout, constant nonsecret failures, and an explicit resolved `--git-dir` binding after repository identity discovery. Temporary SHA-1 bare repositories use a separate bounded initialization path and then enter the same resolved-repository contract.

**Tech Stack:** CPython 3.11, `dataclasses`, `pathlib`, `shutil`, `subprocess`, Git plumbing, pytest, Ruff, and strict Mypy.

## Global Constraints

- Exact rejected candidate and authoring parent: `e9650ed00468f8bcc95b6972d44d1d9923e14b9f` on branch `docs/carerisk-hf-space-design`.
- Candidate review result: Spec not approved, Quality not approved, Critical `0`, Important `2`, Minor `0`.
- This is Architecture C fix round 1. It closes only ambient Git routing/environment redirection and missing subprocess bounds. No fix round 2 is authorized by this document.
- Future implementation begins only from the fresh-reviewed docs commit recorded by the controller as `CARERISK_GIT_OBJECT_FIX_R1_BASE`; no provisional self-SHA appears in tracked files.
- Implementation changes exactly `tests/test_hf_space_source_boundary.py` and commits it separately from these docs.
- `space/tests/test_gradio_contract.py`, all product/application files, evidence, release files, dependencies, Docker, CI, models, data, checkpoints, and scientific/private custody remain frozen.
- The external tuple and its three process names remain unchanged. No tracked executable constant, fallback, manifest, fixture, or docs parser may supply tuple values.
- Do not read `.env`, private data/research artifacts, models, checkpoints, Set B/Set C, scientific locks, or unapproved evaluation outputs.
- Do not push, deploy, mutate GitHub/Hugging Face metadata, create an Actions Environment, or start a persistent service.
- Do not restore `_gradio_test_source_violations`, `_guard_helper_violations`, an AST meta-scanner, or any successor test-source interpreter.
- All Git object bytes remain binary output from `git cat-file blob`; checkout bytes and text-mode reads remain non-authoritative.
- Every Git subprocess launched by `tests/test_hf_space_source_boundary.py` receives `timeout=10.0`, uses no shell, captures stdout/stderr, and fails with exact message `bounded Git plumbing failed` without including command arguments, paths, stdout, stderr, environment values, or custody.
- `_git_ascii_line` is mandatory for every typed Git metadata output: object type, raw size, the object ID returned by `hash-object`, object format, the positive `HEAD:space/tests/test_gradio_contract.py` path-object ID, and bare/non-bare topology tokens. Absolute Git-directory and top-level path outputs instead use `_git_path_line` so non-ASCII filesystem paths remain supported. Decode failure, empty output, multiline output, or non-ASCII typed metadata always maps to the same constant no-context failure.
- Commit identity is exactly `kuotunyu <61350295+kuotunyu@users.noreply.github.com>` with no co-author.
- Never stage broadly. The future implementation commit stages exactly `tests/test_hf_space_source_boundary.py`.

## Rejected alternatives

1. **Keep `cwd=repository` and clear only `GIT_DIR`.** Rejected because `GIT_WORK_TREE`, other `GIT_*` variables, inherited config, and later subprocesses remain ambient authorities.
2. **Add Dulwich, pygit2, or another Git library.** Rejected because the repository already uses reviewed Git plumbing, a new dependency expands supply-chain and behavioral scope, and neither finding requires it.
3. **Use shell-prefixed environment assignments or platform-specific wrappers.** Rejected because they create quoting and platform branches, obscure the exact subprocess environment, and weaken the no-shell contract.

The selected design sanitizes all inherited process authority, discovers the requested repository under that sanitized environment, validates its topology, and then pins every object command to the resolved Git directory.

## File and interface map

| Path | Responsibility in fix round 1 |
| --- | --- |
| `tests/test_hf_space_source_boundary.py` | Adds five hardening cases and replaces only the Git runner/repository initialization helpers. All existing application/export and 13 Architecture C tests remain. |
| `space/tests/test_gradio_contract.py` | Frozen target suite and immutable Git blob; verification only. |
| `.superpowers/sdd/2026-09-01-carerisk-git-object-identity-fix-round-1/task-1-brief.md` | Ignored controller authority: reviewed BASE, exact scope, tuple injection, commands, and stop conditions. |
| `.superpowers/sdd/2026-09-01-carerisk-git-object-identity-fix-round-1/task-1-report.md` | Ignored implementer evidence only. |
| `.superpowers/sdd/2026-09-01-carerisk-git-object-identity-fix-round-1/progress.md` | Ignored review and release custody; never a tracked implementation input. |

The changed boundary file produces these internal interfaces:

```python
@dataclass(frozen=True)
class _ResolvedGitRepository:
    requested_path: Path
    git_dir: Path
    is_bare: bool

def _sanitized_git_environment() -> dict[str, str]:
    """Return the exact allowlisted runtime environment plus fixed Git controls."""

def _resolved_git_executable() -> Path:
    """Return a strict resolved regular executable from `shutil.which('git')`."""

def _run_git_process(
    executable: Path,
    cwd: Path,
    environment: dict[str, str],
    arguments: tuple[str, ...],
    *,
    input_bytes: bytes | None = None,
) -> bytes:
    """Run one bounded Git process and return exact stdout bytes."""

def _resolve_git_repository(
    repository: Path,
    executable: Path,
    environment: dict[str, str],
) -> _ResolvedGitRepository:
    """Validate requested path, absolute Git directory, and bare/non-bare identity."""

def _git_bytes(
    repository: Path,
    *arguments: str,
    input_bytes: bytes | None = None,
) -> bytes:
    """Discover safely, bind explicitly, and run one Git object command."""
```

## Exact environment and repository contract

The inherited runtime allowlist is exact:

```python
_GIT_RUNTIME_ENV_ALLOWLIST = frozenset(
    {
        "COMSPEC",
        "PATH",
        "PATHEXT",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "TMPDIR",
        "WINDIR",
    }
)
_GIT_FIXED_ENVIRONMENT = {
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_OPTIONAL_LOCKS": "0",
    "LC_ALL": "C",
    "LANG": "C",
}
_GIT_TIMEOUT_SECONDS = 10.0
_GIT_FAILURE_MESSAGE = "bounded Git plumbing failed"
```

Only exact uppercase inherited keys in `_GIT_RUNTIME_ENV_ALLOWLIST` may survive. Before selection, every inherited key whose `name.upper().startswith("GIT_")` or `name.upper().startswith("CARERISK_")` is discarded. The fixed controls are then written explicitly; inherited values cannot override them. `HOME`, `USERPROFILE`, `XDG_CONFIG_HOME`, credential helpers, askpass variables, SSH variables, and all other ambient keys are intentionally absent. The Git executable is absolute, so `PATH` is retained only for reviewed OS/Git runtime compatibility, not executable selection inside the call.

Repository discovery uses the sanitized environment and the resolved requested directory as `cwd`:

1. `git rev-parse --absolute-git-dir` returns one ASCII line and resolves to an existing directory.
2. `git rev-parse --is-bare-repository` returns exactly `true` or `false`.
3. For non-bare repositories, `git rev-parse --show-toplevel` returns one ASCII line whose strict resolved path equals the requested directory.
4. For bare repositories, the strict resolved absolute Git directory equals the requested directory.
5. After these checks, every caller command starts with exact global option `--git-dir=<resolved absolute git dir>`. Non-bare commands also receive `--work-tree=<resolved requested directory>`. No later object operation relies on discovery, `cwd`, or ambient routing alone.

The discovery calls are intentionally the only unbound Git calls. They are safe because the environment contains no inherited Git routing/config authority and the requested `cwd` is already a resolved directory. They still use the same 10-second runner and constant error boundary.

---

### Task 1: Harden Git routing, repository identity, and subprocess bounds

**Files:**
- Modify: `tests/test_hf_space_source_boundary.py`
- Verify unchanged: `space/tests/test_gradio_contract.py`
- Report only: `.superpowers/sdd/2026-09-01-carerisk-git-object-identity-fix-round-1/task-1-report.md`

**Interfaces:**
- Consumes: exact reviewed `CARERISK_GIT_OBJECT_FIX_R1_BASE`, existing three controller custody process variables, current `e9650ed...` boundary implementation, and Git object database.
- Produces: five new hardening cases; deterministic sanitized Git environment; validated repository topology; explicit Git-directory/work-tree binding; fixed timeout; constant failure surface.
- Preserves: the prior 13 Architecture C identity/custody/mutation cases, all application/import/capability/entrypoint/guard/export checks, frozen Gradio target, and exact tuple.

- [ ] **Step 1: Verify authority, frozen scope, and rejected baseline**

```powershell
if ((git rev-parse HEAD).Trim() -ne $env:CARERISK_GIT_OBJECT_FIX_R1_BASE) { throw 'wrong fix-round-1 BASE' }
if ((git branch --show-current).Trim() -ne 'docs/carerisk-hf-space-design') { throw 'wrong branch' }
if (@(git status --porcelain=v1 --untracked-files=all).Count -ne 0) { throw 'worktree is not clean' }
if ((git remote get-url origin).Trim() -ne 'https://github.com/kuotunyu/CareRisk-48H.git') { throw 'wrong remote' }
if ((git rev-parse HEAD:space/tests/test_gradio_contract.py).Trim() -ne $env:CARERISK_GRADIO_CONTRACT_BLOB_SHA1) { throw 'frozen target object changed' }
git diff --exit-code e9650ed00468f8bcc95b6972d44d1d9923e14b9f -- space/tests/test_gradio_contract.py space/app.py space/carerisk_space
```

Run the rejected helper baseline and confirm both findings are still present before editing:

```powershell
rg -n 'cwd=repository|capture_output=True|check=False' tests/test_hf_space_source_boundary.py
rg -n 'timeout=|env=|--git-dir=' tests/test_hf_space_source_boundary.py
```

Expected: frozen diff empty; the helper uses ambient `cwd=repository`, has no sanitized `env`, no `timeout`, and no explicit `--git-dir` binding. Stop if another tracked file is dirty or any frozen path differs.

- [ ] **Step 2: Add five strict RED cases**

Add these tests beside the existing Git-object tests. Do not change implementation helpers yet.

The first test reproduces both ambient routing variables against the rejected helper. Create the alternate bare repository before injecting redirection:

```python
def test_git_plumbing_ignores_ambient_repository_routing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    alternate_git_dir = _init_temporary_bare_repository(tmp_path)
    alternate_work_tree = tmp_path / "redirected-work-tree"
    alternate_work_tree.mkdir()
    monkeypatch.setenv("GIT_DIR", str(alternate_git_dir))
    monkeypatch.setenv("GIT_WORK_TREE", str(alternate_work_tree))

    actual = _git_path_line(
        _git_bytes(
            REPOSITORY_ROOT,
            "rev-parse",
            "--absolute-git-dir",
        )
    )

    assert Path(actual).resolve(strict=True) == (REPOSITORY_ROOT / ".git").resolve(
        strict=True
    )
```

The second test records real subprocess calls. It proves environment stripping, reviewed fixed controls, absolute executable, timeout, and explicit binding. Synthetic values are deliberately unrelated to controller custody:

```python
def test_git_plumbing_invocation_is_sanitized_bound_and_bounded(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    recorded: list[tuple[tuple[str, ...], dict[str, Any]]] = []
    real_run = subprocess.run

    def recording_run(
        command: tuple[str, ...],
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[bytes]:
        recorded.append((command, dict(kwargs)))
        return real_run(command, **kwargs)

    monkeypatch.setenv("GIT_DIR", "synthetic-alternate-git-dir")
    monkeypatch.setenv("GIT_WORK_TREE", "synthetic-alternate-work-tree")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "synthetic-global-config")
    monkeypatch.setenv("gIt_ASKPASS", "synthetic-askpass")
    monkeypatch.setenv("Git_Config_Count", "1")
    monkeypatch.setenv("CARERISK_GRADIO_CONTRACT_BLOB_SHA1", "synthetic-custody")
    monkeypatch.setenv("carerisk_gradio_contract_raw_size", "synthetic-size")
    monkeypatch.setattr(subprocess, "run", recording_run)

    result = _git_bytes(REPOSITORY_ROOT, "rev-parse", "HEAD^{commit}")
    assert re.fullmatch(rb"[0-9a-f]{40}\n?", result) is not None
    temporary_repository = _init_temporary_bare_repository(tmp_path)
    assert _git_ascii_line(
        _git_bytes(temporary_repository, "rev-parse", "--show-object-format")
    ) == "sha1"
    assert recorded

    for command, kwargs in recorded:
        assert Path(command[0]).is_absolute()
        assert kwargs["timeout"] == _GIT_TIMEOUT_SECONDS == 10.0
        assert kwargs["check"] is True
        assert kwargs["capture_output"] is True
        assert kwargs.get("shell") is not True
        environment = kwargs["env"]
        assert isinstance(environment, dict)
        assert not any(name.upper().startswith("CARERISK_") for name in environment)
        assert environment["GIT_CONFIG_NOSYSTEM"] == "1"
        assert environment["GIT_CONFIG_GLOBAL"] == os.devnull
        assert environment["GIT_TERMINAL_PROMPT"] == "0"
        assert environment["GIT_OPTIONAL_LOCKS"] == "0"
        assert environment["LC_ALL"] == environment["LANG"] == "C"
        assert set(environment) <= _GIT_RUNTIME_ENV_ALLOWLIST | set(
            _GIT_FIXED_ENVIRONMENT
        )

    expected_git_dir = (REPOSITORY_ROOT / ".git").resolve(strict=True)
    assert any(
        command[1:3]
        == (
            f"--git-dir={expected_git_dir}",
            f"--work-tree={REPOSITORY_ROOT.resolve(strict=True)}",
        )
        for command, _ in recorded
    )
    resolved_temporary = temporary_repository.resolve(strict=True)
    assert any(
        command[1] == f"--git-dir={resolved_temporary}"
        and not any(argument.startswith("--work-tree=") for argument in command)
        for command, _ in recorded
        if len(command) > 1
    )
```

The remaining parameterized node preserves exactly three collected rows. The
timeout and command rows fail at the bounded runner. The single `unicode` row
first completes real repository discovery/topology, then iterates every
post-discovery typed-metadata stage plus the bare-identity topology token. It
injects invalid ASCII bytes, empty output, multiline output, and valid UTF-8
that is nevertheless non-ASCII. Keeping this matrix inside one pytest row is
load-bearing: the complete new hardening set must still collect exactly five
cases rather than silently inflating the acceptance count.

```python
@pytest.mark.parametrize("failure", ("timeout", "called_process", "unicode"))
def test_git_plumbing_failures_are_constant_and_nonsecret(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failure: str,
) -> None:
    synthetic_secret = b"synthetic-private-output"
    real_run = subprocess.run

    def assert_constant_failure(action: Callable[[], object]) -> None:
        with pytest.raises(AssertionError) as captured:
            action()
        assert str(captured.value) == "bounded Git plumbing failed"
        assert "synthetic-private-output" not in str(captured.value)
        assert captured.value.__cause__ is None
        assert captured.value.__context__ is None

    def failing_run(
        command: tuple[str, ...],
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[bytes]:
        assert kwargs["timeout"] == 10.0
        if failure == "timeout":
            raise subprocess.TimeoutExpired(
                command,
                10.0,
                output=synthetic_secret,
                stderr=synthetic_secret,
            )
        if failure == "called_process":
            raise subprocess.CalledProcessError(
                2,
                command,
                output=synthetic_secret,
                stderr=synthetic_secret,
            )
        raise AssertionError("unreachable failure row")

    if failure != "unicode":
        monkeypatch.setattr(subprocess, "run", failing_run)
        assert_constant_failure(
            lambda: _git_bytes(REPOSITORY_ROOT, "rev-parse", "HEAD^{commit}")
        )
        return

    temporary_repository = _init_temporary_bare_repository(tmp_path)
    synthetic_raw = b"synthetic object for typed metadata"
    synthetic_object_id = hashlib.sha1(
        b"blob " + str(len(synthetic_raw)).encode("ascii") + b"\0" + synthetic_raw
    ).hexdigest()
    _git_bytes(
        temporary_repository,
        "hash-object",
        "-w",
        "--stdin",
        input_bytes=synthetic_raw,
    )
    synthetic_expected = (
        synthetic_object_id,
        len(synthetic_raw),
        hashlib.sha256(synthetic_raw).hexdigest(),
    )

    typed_stages: tuple[tuple[str, tuple[str, ...], Callable[[], object]], ...] = (
        (
            "positive_path_object_id",
            ("rev-parse", "HEAD:space/tests/test_gradio_contract.py"),
            lambda: _git_ascii_line(
                _git_bytes(
                    REPOSITORY_ROOT,
                    "rev-parse",
                    "HEAD:space/tests/test_gradio_contract.py",
                )
            ),
        ),
        (
            "object_type",
            ("cat-file", "-t", synthetic_object_id),
            lambda: _assert_git_blob_identity(
                temporary_repository,
                synthetic_object_id,
                synthetic_expected,
            ),
        ),
        (
            "raw_size",
            ("cat-file", "-s", synthetic_object_id),
            lambda: _assert_git_blob_identity(
                temporary_repository,
                synthetic_object_id,
                synthetic_expected,
            ),
        ),
        (
            "written_object_id",
            ("hash-object", "-w", "--stdin"),
            lambda: _write_temporary_blob(temporary_repository, b"second object"),
        ),
        (
            "object_format",
            ("rev-parse", "--show-object-format"),
            lambda: _git_ascii_line(
                _git_bytes(
                    temporary_repository,
                    "rev-parse",
                    "--show-object-format",
                )
            ),
        ),
        (
            "bare_identity",
            ("rev-parse", "--is-bare-repository"),
            lambda: _git_bytes(
                temporary_repository,
                "rev-parse",
                "--show-object-format",
            ),
        ),
    )
    invalid_typed_outputs = (
        b"\xff",
        b"",
        b"first\nsecond\n",
        "non-ascii-\N{LATIN SMALL LETTER E WITH ACUTE}".encode("utf-8"),
    )

    def poisoning_run_for(
        expected_suffix: tuple[str, ...],
        output: bytes,
    ) -> Callable[..., subprocess.CompletedProcess[bytes]]:
        def poisoning_run(
            command: tuple[str, ...],
            **kwargs: Any,
        ) -> subprocess.CompletedProcess[bytes]:
            assert kwargs["timeout"] == 10.0
            completed = real_run(command, **kwargs)
            if tuple(command[-len(expected_suffix) :]) == expected_suffix:
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=output,
                    stderr=synthetic_secret,
                )
            return completed

        return poisoning_run

    for _stage, suffix, action in typed_stages:
        for poisoned_output in invalid_typed_outputs:
            with monkeypatch.context() as context:
                context.setattr(
                    subprocess,
                    "run",
                    poisoning_run_for(suffix, poisoned_output),
                )
                assert_constant_failure(action)
```

Run only the three new nodes:

```powershell
.venv-space\Scripts\python.exe -m pytest `
  tests/test_hf_space_source_boundary.py::test_git_plumbing_ignores_ambient_repository_routing `
  tests/test_hf_space_source_boundary.py::test_git_plumbing_invocation_is_sanitized_bound_and_bounded `
  tests/test_hf_space_source_boundary.py::test_git_plumbing_failures_are_constant_and_nonsecret `
  -q
```

Expected strict RED: exactly 5 collected and 5 failed; no collection error or skip. The routing case must show alternate `GIT_DIR`/`GIT_WORK_TREE` influence, the invocation case must fail for missing `env`/absolute executable/timeout/binding, and the three failure rows must not produce the required constant `AssertionError`. In the `unicode` row, the recorded command sequence must prove successful discovery/topology precedes each poisoned post-discovery metadata response; no raw `UnicodeDecodeError` may escape. Record this output in the ignored task report.

- [ ] **Step 3: Implement the deterministic runner and repository identity boundary**

Add `from dataclasses import dataclass` and `import shutil`; extend the existing import to `from collections.abc import Callable, Iterable`, and add `from typing import Any, NoReturn`. `Any` and `Callable` are used only by the subprocess-recording RED doubles; production helpers retain concrete types. Importing `Callable` from `typing` is forbidden by Ruff `UP035`. Preserve all existing imports still used elsewhere.

Add the fixed constants and failure helper exactly:

```python
_GIT_RUNTIME_ENV_ALLOWLIST = frozenset(
    {
        "COMSPEC",
        "PATH",
        "PATHEXT",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "TMPDIR",
        "WINDIR",
    }
)
_GIT_FIXED_ENVIRONMENT = {
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_OPTIONAL_LOCKS": "0",
    "LC_ALL": "C",
    "LANG": "C",
}
_GIT_TIMEOUT_SECONDS = 10.0
_GIT_FAILURE_MESSAGE = "bounded Git plumbing failed"


def _raise_git_failure() -> NoReturn:
    raise AssertionError(_GIT_FAILURE_MESSAGE) from None
```

Add exact environment construction. The explicit prefix filters are required even though the allowlist would also exclude most hostile keys:

```python
def _sanitized_git_environment() -> dict[str, str]:
    environment: dict[str, str] = {}
    for name, value in os.environ.items():
        upper_name = name.upper()
        if upper_name.startswith("GIT_") or upper_name.startswith("CARERISK_"):
            continue
        if name != upper_name or upper_name not in _GIT_RUNTIME_ENV_ALLOWLIST:
            continue
        environment[upper_name] = value
    environment.update(_GIT_FIXED_ENVIRONMENT)
    return environment
```

Resolve one absolute regular executable, and place all subprocess calls behind the bounded runner:

```python
def _resolved_git_executable() -> Path:
    located = shutil.which("git")
    if located is None:
        _raise_git_failure()
    executable: Path | None
    try:
        executable = Path(located).resolve(strict=True)
    except (OSError, RuntimeError):
        executable = None
    if executable is None:
        _raise_git_failure()
    if not executable.is_file() or not os.access(executable, os.X_OK):
        _raise_git_failure()
    return executable


def _run_git_process(
    executable: Path,
    cwd: Path,
    environment: dict[str, str],
    arguments: tuple[str, ...],
    *,
    input_bytes: bytes | None = None,
) -> bytes:
    completed: subprocess.CompletedProcess[bytes] | None
    try:
        completed = subprocess.run(
            (str(executable), *arguments),
            cwd=cwd,
            env=environment,
            input=input_bytes,
            capture_output=True,
            check=True,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except (
        OSError,
        subprocess.TimeoutExpired,
        subprocess.CalledProcessError,
    ):
        completed = None
    if completed is None:
        _raise_git_failure()
    return completed.stdout
```

Decode every typed Git metadata token as strict ASCII and filesystem paths with
`os.fsdecode` so the repository's non-ASCII Windows path remains valid. Both
helpers accept exactly one nonempty line and translate decoding errors to the
constant failure. `_git_ascii_line` is not optional: object type, raw size,
written object ID, object format, positive path-object ID, and bare identity all
pass through it before parsing or comparison. `_git_path_line` is mandatory for
the absolute Git-directory and non-bare top-level discovery outputs:

```python
def _single_git_line(value: str) -> str:
    lines = value.splitlines()
    if len(lines) != 1 or not lines[0]:
        _raise_git_failure()
    return lines[0]


def _git_ascii_line(raw: bytes) -> str:
    value: str | None
    try:
        value = raw.decode("ascii")
    except UnicodeError:
        value = None
    if value is None:
        _raise_git_failure()
    return _single_git_line(value)


def _git_path_line(raw: bytes) -> str:
    value: str | None
    try:
        value = os.fsdecode(raw)
    except UnicodeError:
        value = None
    if value is None:
        _raise_git_failure()
    return _single_git_line(value)
```

Add resolved repository identity. `Path.resolve(strict=True)` and all metadata decodes are caught and translated to the constant message:

```python
@dataclass(frozen=True)
class _ResolvedGitRepository:
    requested_path: Path
    git_dir: Path
    is_bare: bool


def _resolved_directory(path: Path) -> Path:
    resolved: Path | None
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError):
        resolved = None
    if resolved is None:
        _raise_git_failure()
    if not resolved.is_dir():
        _raise_git_failure()
    return resolved


def _resolve_git_repository(
    repository: Path,
    executable: Path,
    environment: dict[str, str],
) -> _ResolvedGitRepository:
    requested = _resolved_directory(repository)
    git_dir_text = _git_path_line(
        _run_git_process(
            executable,
            requested,
            environment,
            ("rev-parse", "--absolute-git-dir"),
        )
    )
    bare_text = _git_ascii_line(
        _run_git_process(
            executable,
            requested,
            environment,
            ("rev-parse", "--is-bare-repository"),
        )
    )
    git_dir = _resolved_directory(Path(git_dir_text))
    if bare_text == "true":
        if git_dir != requested:
            _raise_git_failure()
        return _ResolvedGitRepository(requested, git_dir, True)
    if bare_text != "false":
        _raise_git_failure()
    top_level_text = _git_path_line(
        _run_git_process(
            executable,
            requested,
            environment,
            ("rev-parse", "--show-toplevel"),
        )
    )
    top_level = _resolved_directory(Path(top_level_text))
    if top_level != requested:
        _raise_git_failure()
    return _ResolvedGitRepository(requested, git_dir, False)
```

Replace `_git_bytes` with explicit final binding. Keep the existing argument NUL/CR/LF rejection, but replace its dynamic message with the same constant failure:

```python
def _git_bytes(
    repository: Path,
    *arguments: str,
    input_bytes: bytes | None = None,
) -> bytes:
    if not arguments or any(
        "\x00" in argument or "\r" in argument or "\n" in argument
        for argument in arguments
    ):
        _raise_git_failure()
    executable = _resolved_git_executable()
    environment = _sanitized_git_environment()
    resolved = _resolve_git_repository(repository, executable, environment)
    bound_arguments = (f"--git-dir={resolved.git_dir}",)
    if not resolved.is_bare:
        bound_arguments += (f"--work-tree={resolved.requested_path}",)
    return _run_git_process(
        executable,
        resolved.requested_path,
        environment,
        (*bound_arguments, *arguments),
        input_bytes=input_bytes,
    )
```

No exception message may include `arguments`, `repository`, `git_dir`, `completed.stdout`, `completed.stderr`, return code, or environment data. Do not use `shell=True`, `Popen`, a retry loop, a platform shell, or a timeout override.

- [ ] **Step 4: Put temporary bare SHA-1 initialization under the same boundary**

Initialization is the only command that runs before the target repository exists. Replace the old `_git_bytes(tmp_path, "init", ...)` call with this exact sequence:

```python
def _init_temporary_bare_repository(tmp_path: Path) -> Path:
    parent = _resolved_directory(tmp_path)
    repository = (parent / "gradio-contract-objects.git").resolve(strict=False)
    if repository.parent != parent or repository.exists():
        _raise_git_failure()
    executable = _resolved_git_executable()
    environment = _sanitized_git_environment()
    _run_git_process(
        executable,
        parent,
        environment,
        (
            "init",
            "--bare",
            "--object-format=sha1",
            str(repository),
        ),
    )
    resolved = _resolve_git_repository(repository, executable, environment)
    if not resolved.is_bare or resolved.git_dir != repository:
        _raise_git_failure()
    object_format = _git_ascii_line(
        _git_bytes(repository, "rev-parse", "--show-object-format")
    )
    if object_format != "sha1":
        _raise_git_failure()
    return repository
```

`git init` receives the same sanitized environment, absolute executable, captured binary output, `check=True`, and 10-second timeout. After creation, the repository must be bare, its resolved Git directory must equal the requested repository, and its object format must be exact `sha1` before any `hash-object -w --stdin` call.

Replace every inherited typed-metadata decode rather than leaving a permissive
"may call" seam. The positive path-binding test, temporary writer, and blob
validator use these exact forms; `_git_blob_bytes` alone remains undecoded raw
binary output:

```python
object_id = _git_ascii_line(
    _git_bytes(
        REPOSITORY_ROOT,
        "rev-parse",
        "HEAD:space/tests/test_gradio_contract.py",
    )
)

def _write_temporary_blob(repository: Path, raw: bytes) -> str:
    object_id = _git_ascii_line(
        _git_bytes(
            repository,
            "hash-object",
            "-w",
            "--stdin",
            input_bytes=raw,
        )
    )
    if re.fullmatch(r"[0-9a-f]{40}", object_id) is None:
        _raise_git_failure()
    return object_id


def _assert_git_blob_identity(
    repository: Path,
    object_id: str,
    expected: tuple[str, int, str],
) -> None:
    expected_blob, expected_size, expected_sha256 = expected
    if re.fullmatch(r"[0-9a-f]{40}", object_id) is None:
        _raise_git_failure()
    object_type = _git_ascii_line(
        _git_bytes(repository, "cat-file", "-t", object_id)
    )
    size_text = _git_ascii_line(
        _git_bytes(repository, "cat-file", "-s", object_id)
    )
    if re.fullmatch(r"0|[1-9][0-9]*", size_text) is None:
        _raise_git_failure()
    raw = _git_blob_bytes(repository, object_id)
    actual_size = int(size_text)
    actual = (object_id, actual_size, hashlib.sha256(raw).hexdigest())
    assert object_type == "blob"
    assert len(raw) == actual_size
    assert actual == (expected_blob, expected_size, expected_sha256)
```

Keep mutation generation and custody parsing otherwise unchanged. No `.decode`,
`.strip`, text-mode read, or alternate decoder remains at a typed Git metadata
call site. Malformed typed metadata always enters `_raise_git_failure()` and
therefore has the exact constant message with neither cause nor context.

- [ ] **Step 5: Run five-case GREEN and all prior 13 Architecture C cases**

```powershell
.venv-space\Scripts\python.exe -m pytest `
  tests/test_hf_space_source_boundary.py::test_git_plumbing_ignores_ambient_repository_routing `
  tests/test_hf_space_source_boundary.py::test_git_plumbing_invocation_is_sanitized_bound_and_bounded `
  tests/test_hf_space_source_boundary.py::test_git_plumbing_failures_are_constant_and_nonsecret `
  -q

.venv-space\Scripts\python.exe -m pytest `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_git_object_matches_controller_custody `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_controller_custody_is_strict `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_git_object_rejects_mutated_git_objects `
  -q
```

Expected: new hardening nodes collect exactly 5 and all pass. Prior nodes collect exactly 13—one positive identity, four strict custody rows, and eight real temporary-object mutations—and all pass without skip or collection error.

Repeat the routing test with mixed-case hostile names in the invocation-contract test's environment capture (`gIt_ASKPASS`, `Git_Config_Count`, and `carerisk_gradio_contract_raw_size`). The captured subprocess environment must still contain none of them because filtering compares `name.upper()` before allowlisting.

- [ ] **Step 6: Run full boundary/export, target, static, tuple, leak, and scope gates**

Inject the exact external tuple only into the pytest controller process. `_sanitized_git_environment()` must remove it from every Git subprocess.

```powershell
$env:PYTHONPATH = (Resolve-Path space).Path
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_source_boundary.py space/tests/test_export_contract.py -q
.venv-space\Scripts\python.exe -m pytest space/tests/test_gradio_contract.py -q
.venv-space\Scripts\python.exe -m ruff check tests/test_hf_space_source_boundary.py
.venv-space\Scripts\python.exe -m ruff format --check tests/test_hf_space_source_boundary.py
.venv-space\Scripts\python.exe -m mypy --strict tests/test_hf_space_source_boundary.py
git diff --check
git diff --exit-code $env:CARERISK_GIT_OBJECT_FIX_R1_BASE -- space/tests/test_gradio_contract.py space/app.py space/carerisk_space
git diff --name-only $env:CARERISK_GIT_OBJECT_FIX_R1_BASE
git status --short
```

Expected baseline-derived counts: boundary/export `116 passed, 1` documented platform skip; target Gradio `61 passed, 6` documented Windows capability skips. If collection changes for an unrelated reason, stop and report rather than editing frozen scope. Ruff, formatter, strict Mypy, diff check, and frozen-product diff all pass. The only tracked changed path is `tests/test_hf_space_source_boundary.py`.

Run all three custody-value leak checks. Missing tracked pathspec directories are still passed to `git grep`; Git exit `1` with no match is required for each value:

```powershell
foreach ($value in @(
    $env:CARERISK_GRADIO_CONTRACT_BLOB_SHA1,
    $env:CARERISK_GRADIO_CONTRACT_RAW_SIZE,
    $env:CARERISK_GRADIO_CONTRACT_RAW_SHA256
)) {
    git grep -n -F -- $value -- .github tests space scripts tools
    if ($LASTEXITCODE -eq 0) { throw 'controller custody leaked into tracked executable scope' }
    if ($LASTEXITCODE -ne 1) { throw 'custody leak scan failed' }
}
```

Repeat raw-object authority independently in Git Bash:

```bash
test "$(git rev-parse HEAD:space/tests/test_gradio_contract.py)" = "$CARERISK_GRADIO_CONTRACT_BLOB_SHA1"
test "$(git cat-file -t "$CARERISK_GRADIO_CONTRACT_BLOB_SHA1")" = blob
test "$(git cat-file -s "$CARERISK_GRADIO_CONTRACT_BLOB_SHA1")" = "$CARERISK_GRADIO_CONTRACT_RAW_SIZE"
test "$(git cat-file blob "$CARERISK_GRADIO_CONTRACT_BLOB_SHA1" | wc -c | tr -d ' ')" = "$CARERISK_GRADIO_CONTRACT_RAW_SIZE"
test "$(git cat-file blob "$CARERISK_GRADIO_CONTRACT_BLOB_SHA1" | sha256sum | cut -d' ' -f1)" = "$CARERISK_GRADIO_CONTRACT_RAW_SHA256"
```

Run the executable source-structure gate below. This gate inspects actual AST
definitions and calls, not source substrings. It therefore preserves denylist
constants such as `_PROCESS_CALLS = {"subprocess.Popen", ...}`, source fixtures,
and the required `monkeypatch.setenv("GIT_DIR", ...)` / `GIT_WORK_TREE` RED rows.
Those strings are evidence, not process execution.

```powershell
$structuralGate = @'
import ast
from pathlib import Path

SOURCE_PATH = Path("tests/test_hf_space_source_boundary.py")
source = SOURCE_PATH.read_text(encoding="utf-8")
tree = ast.parse(source, filename=str(SOURCE_PATH))
violations: list[str] = []


def qualified_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        owner = qualified_name(node.value)
        return f"{owner}.{node.attr}" if owner else node.attr
    return ""


def only_module_function(name: str) -> ast.FunctionDef | None:
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    if len(matches) != 1:
        violations.append(f"{name}: expected exactly one module function")
        return None
    return matches[0]


def keyword_value(call: ast.Call, name: str) -> ast.AST | None:
    matches = [keyword.value for keyword in call.keywords if keyword.arg == name]
    if len(matches) > 1:
        violations.append(f"{qualified_name(call.func)}: duplicate {name}")
        return None
    return matches[0] if matches else None


def is_name(node: ast.AST | None, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


retired_definitions = {
    "_gradio_test_source_violations",
    "_guard_helper_violations",
}
subprocess_api_names = {
    "Popen",
    "run",
    "call",
    "check_call",
    "check_output",
}

for node in ast.walk(tree):
    if (
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in retired_definitions
    ):
        violations.append(f"retired definition remains: {node.name}")
    if not isinstance(node, ast.Call):
        continue
    name = qualified_name(node.func)
    if name in {"Popen", "subprocess.Popen"}:
        violations.append(f"process creation call is forbidden: {name}")
    is_subprocess_api = name.startswith("subprocess.") or name in subprocess_api_names
    if not is_subprocess_api:
        continue
    shell = keyword_value(node, "shell")
    if shell is not None and not (
        isinstance(shell, ast.Constant) and shell.value is False
    ):
        violations.append(f"{name}: shell must be absent or literal False")
    timeout = keyword_value(node, "timeout")
    if isinstance(timeout, ast.Constant) and timeout.value is None:
        violations.append(f"{name}: timeout=None is forbidden")

timeout_assignments = [
    statement
    for statement in tree.body
    if isinstance(statement, ast.Assign)
    and any(
        isinstance(target, ast.Name) and target.id == "_GIT_TIMEOUT_SECONDS"
        for target in statement.targets
    )
]
if len(timeout_assignments) != 1 or not (
    isinstance(timeout_assignments[0].value, ast.Constant)
    and timeout_assignments[0].value.value == 10.0
):
    violations.append("_GIT_TIMEOUT_SECONDS must be one literal 10.0 assignment")

runner = only_module_function("_run_git_process")
if runner is not None:
    if any(
        isinstance(node, ast.Attribute) and qualified_name(node) == "os.environ"
        for node in ast.walk(runner)
    ):
        violations.append("_run_git_process must not read or forward os.environ")
    if any(
        isinstance(node, ast.Name)
        and node.id == "environment"
        and isinstance(node.ctx, ast.Store)
        for node in ast.walk(runner)
    ):
        violations.append("_run_git_process must not replace its sanitized environment")
    runner_calls = [
        node
        for node in ast.walk(runner)
        if isinstance(node, ast.Call) and qualified_name(node.func) == "subprocess.run"
    ]
    if len(runner_calls) != 1:
        violations.append("_run_git_process must contain one subprocess.run call")
    else:
        call = runner_calls[0]
        required_keywords = {
            "cwd": "cwd",
            "env": "environment",
            "input": "input_bytes",
            "timeout": "_GIT_TIMEOUT_SECONDS",
        }
        for keyword, required_name in required_keywords.items():
            if not is_name(keyword_value(call, keyword), required_name):
                violations.append(
                    f"_run_git_process subprocess.run {keyword} must be {required_name}"
                )
        for keyword in ("capture_output", "check"):
            value = keyword_value(call, keyword)
            if not (isinstance(value, ast.Constant) and value.value is True):
                violations.append(
                    f"_run_git_process subprocess.run {keyword} must be literal True"
                )
        shell = keyword_value(call, "shell")
        if shell is not None and not (
            isinstance(shell, ast.Constant) and shell.value is False
        ):
            violations.append("_run_git_process subprocess.run shell is unsafe")

sanitizer = only_module_function("_sanitized_git_environment")
if sanitizer is not None:
    sanitizer_literals = {
        node.value
        for node in ast.walk(sanitizer)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    if not {"GIT_", "CARERISK_"} <= sanitizer_literals:
        violations.append("sanitizer must reject GIT_ and CARERISK_ prefixes")
    environment_reads = [
        node
        for node in ast.walk(sanitizer)
        if isinstance(node, ast.Call)
        and qualified_name(node.func) == "os.environ.items"
    ]
    if len(environment_reads) != 1:
        violations.append("sanitizer must inspect os.environ.items exactly once")
    fixed_updates = [
        node
        for node in ast.walk(sanitizer)
        if isinstance(node, ast.Call)
        and qualified_name(node.func) == "environment.update"
        and len(node.args) == 1
        and is_name(node.args[0], "_GIT_FIXED_ENVIRONMENT")
        and not node.keywords
    ]
    if len(fixed_updates) != 1:
        violations.append("sanitizer must add only reviewed fixed Git controls")
    returns = [node for node in ast.walk(sanitizer) if isinstance(node, ast.Return)]
    if len(returns) != 1 or not is_name(returns[0].value, "environment"):
        violations.append("sanitizer must return the constructed environment")

git_bytes = only_module_function("_git_bytes")
if git_bytes is not None:
    sanitized_assignments = [
        node
        for node in ast.walk(git_bytes)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and is_name(node.targets[0], "environment")
        and isinstance(node.value, ast.Call)
        and qualified_name(node.value.func) == "_sanitized_git_environment"
        and not node.value.args
        and not node.value.keywords
    ]
    if len(sanitized_assignments) != 1:
        violations.append("_git_bytes must construct one sanitized environment")
    if any(
        isinstance(node, ast.Attribute) and qualified_name(node) == "os.environ"
        for node in ast.walk(git_bytes)
    ):
        violations.append("_git_bytes must not read or forward os.environ")

for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
        continue
    if qualified_name(node.func) not in {
        "_resolve_git_repository",
        "_run_git_process",
    }:
        continue
    if len(node.args) < 3 or not is_name(node.args[2], "environment"):
        violations.append(
            f"{qualified_name(node.func)} must receive the sanitized environment"
        )

if violations:
    raise AssertionError(
        "plumbing structural gate failed:\n" + "\n".join(sorted(set(violations)))
    )
print("plumbing structural gate passed")
'@
$structuralGate | .venv-space\Scripts\python.exe -
if ($LASTEXITCODE -ne 0) { throw 'plumbing structural gate failed' }
```

Expected: the structural gate prints `plumbing structural gate passed`. It
rejects real retired function definitions, `Popen` calls, unsafe subprocess
shell/timeout calls, a missing or non-10-second Git-runner timeout, ambient
environment forwarding, and loss of the sanitizer boundary. It deliberately
allows denylist/test-fixture strings and `monkeypatch.setenv` RED setup. Do not
weaken unrelated application, guard, entrypoint, exporter, denylist, secret,
symlink, binary, or frozen-product tests to make counts pass.

- [ ] **Step 7: Commit exact implementation scope and request fresh review**

```powershell
git add -- tests/test_hf_space_source_boundary.py
$staged = @(git diff --cached --name-only)
if ($staged.Count -ne 1 -or $staged[0] -cne 'tests/test_hf_space_source_boundary.py') { throw 'unexpected fix-round-1 scope' }
git diff --cached --check
git -c user.name=kuotunyu `
    -c user.email=61350295+kuotunyu@users.noreply.github.com `
    commit -m 'test(space): harden bounded Git object plumbing'
```

Do not push. Record exact parent, HEAD, identity, one-file scope, test counts, tuple proof, leak exits, and clean tree in the ignored report.

The fresh reviewer receives the exact reviewed docs BASE-to-candidate diff and both original repros. Review must verify:

1. every Git subprocess has absolute executable, sanitized env, `check=True`, captured binary output, and `timeout=10.0`;
2. no inherited key whose uppercase form begins `GIT_` or `CARERISK_` reaches a Git process, apart from the six explicitly set reviewed Git/locale controls;
3. repository discovery validates absolute Git directory plus bare/non-bare identity, then every object command has explicit resolved Git-directory binding;
4. bare SHA-1 temp initialization uses the same runner and validates topology/object format before `hash-object`;
5. timeout and command failure plus invalid-ASCII, empty, multiline, and non-ASCII typed metadata at every mandatory decode site expose only `bounded Git plumbing failed`, never stdout, stderr, command, path, custody, cause, context, or a raw `UnicodeDecodeError`;
6. alternate `GIT_DIR` and `GIT_WORK_TREE` cannot redirect the requested repository;
7. all prior 13 Architecture C cases and every application/export/frozen-product boundary remain intact;
8. target/product/tuple/remote/private scope is unchanged.

Acceptance requires Spec ✅, Quality Approved, Critical `0`, Important `0`, followed by an independent controller rerun of Steps 5 and 6. Any finding stops before ledger release. This plan does not authorize another fix round, Task 7, push, deployment, remote metadata, or target-file changes.
