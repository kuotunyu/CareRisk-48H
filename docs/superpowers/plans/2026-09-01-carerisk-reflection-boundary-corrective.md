# CareRisk Reflection-Free Public Boundary Corrective Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the exhausted Task 6 reflection-alias chase with a fail-closed, reflection-free public application capability contract, then return the original HF Space plan to a reviewable boundary.

**Architecture:** The public application remains unchanged. One AST contract file gains a deny-by-construction reflection scanner that runs before the existing exact composition checks. Application sources reject every dynamic attribute primitive; entry-point and guard-helper audits additionally reject reflection that targets their framework objects or sensitive member names, without becoming a Python evaluator.

**Tech Stack:** Python 3.11, `ast`, Pytest, Ruff, Mypy, existing `.venv-space` environment.

## Global Constraints

- Start from design commit `190819a838634bd10412f2af72cdc252f6ecd31a` on branch `docs/carerisk-hf-space-design` with a clean tracked worktree.
- The sole product capability policy is design Section 9.1, “Dynamic reflection is denied by construction.”
- Do not modify `space/app.py`, `space/carerisk_space/*.py`, the public path list, evidence bytes, deployment identities, dependency locks, Docker files, UI behavior, or any scientific artifact.
- Do not read `.env`, private data, private research artifacts, model bundles, checkpoints, Set B custody/evaluation assets, private ledgers/final locks, or Set C.
- Do not run the receipt exporter, model code, training, evaluation, or persistent service.
- Do not create, upload, deploy, or modify a GitHub or Hugging Face resource; do not push this branch.
- Product application sources reject direct or aliased `getattr`, `setattr`, `delattr`, `hasattr`, `vars`, `globals`, `locals`, `eval`, `exec`, `compile`, and `__import__`; calls through `__getattribute__`, `__getattr__`, `__setattr__`, or `__delattr__`; `__dict__` access; `operator.attrgetter`/`operator.methodcaller`; and `inspect.getattr_static`.
- Syntax-defined `__future__`, `__name__`, `__file__`, `__all__`, `__init__`, and `__call__` uses remain permitted when they are not used to retrieve or mutate another attribute.
- The entry point still requires direct named construction: one `FastAPI(...)`, one `gr.mount_gradio_app(...)`, one `build_package_asset_membership()`, one `PublicSurfaceGuard(...)`, and one `uvicorn.run(...)` beneath the exact main guard.
- Existing unrelated test introspection in `space/tests/test_gradio_contract.py`, such as reading `original_router` or `AF_UNIX`, is not an application capability and must remain valid.
- Use exact path staging only. Never use `git add .`, `git add -A`, directory staging, or wildcard staging.

---

### Task 1: Enforce the reflection-free source and composition boundary

**Files:**
- Modify: `tests/test_hf_space_source_boundary.py`
- Verify unchanged: `space/tests/test_gradio_contract.py`

**Interfaces:**
- Consumes: `scan_capabilities(paths: Iterable[Path]) -> list[str]`, `_entrypoint_violations(tree: ast.Module) -> list[str]`, `_guard_helper_violations(tree: ast.Module) -> list[str]`, `_bounded_aliases(tree: ast.AST, roots: frozenset[str]) -> tuple[dict[str, str], set[str]]`.
- Produces: `_dynamic_reflection_violations(tree: ast.AST, aliases: dict[str, str] | None = None) -> list[str]` and `_sensitive_reflection_in_helper(function: ast.FunctionDef, aliases: dict[str, str]) -> bool`; the three existing public boundary interfaces remain signature-compatible.

- [ ] **Step 1: Confirm the exact baseline and immutable scope**

Run:

```powershell
git rev-parse HEAD
git branch --show-current
git status --short --branch
git diff --exit-code 190819a838634bd10412f2af72cdc252f6ecd31a -- space/app.py space/carerisk_space space/tests/test_gradio_contract.py
```

Expected: HEAD is exactly `190819a838634bd10412f2af72cdc252f6ecd31a`, branch is `docs/carerisk-hf-space-design`, tracked worktree is clean, and the immutable-scope diff exits zero.

- [ ] **Step 2: Add product-source reflection mutations**

Add a parametrized mutation test that writes one synthetic application module at a time and requires the listed bounded violation suffix. Its cases must include these exact executable shapes:

```python
@pytest.mark.parametrize(
    ("source", "expected_suffix"),
    (
        ('getattr(target, "member")', "getattr"),
        ('reflect = getattr\nreflect(target, "member")', "getattr"),
        ('setattr(target, "member", value)', "setattr"),
        ('delattr(target, "member")', "delattr"),
        ('hasattr(target, "member")', "hasattr"),
        ('vars(target)["member"]', "vars"),
        ('globals()["target"]', "globals"),
        ('locals()["target"]', "locals"),
        ('compile("1", "<x>", "eval")', "compile"),
        ('target.__getattribute__("member")', "__getattribute__"),
        ('target.__getattr__("member")', "__getattr__"),
        ('target.__setattr__("member", value)', "__setattr__"),
        ('target.__delattr__("member")', "__delattr__"),
        ('target.__dict__["member"]', "__dict__"),
        ('operator.attrgetter("member")(target)', "operator.attrgetter"),
        ('operator.methodcaller("member")(target)', "operator.methodcaller"),
        ('inspect.getattr_static(target, "member")', "inspect.getattr_static"),
    ),
)
def test_application_reflection_is_denied_by_construction(
    tmp_path: Path,
    source: str,
    expected_suffix: str,
) -> None:
    synthetic = tmp_path / "synthetic.py"
    synthetic.write_text(source, encoding="utf-8")
    assert f"synthetic.py:{expected_suffix}" in scan_capabilities((synthetic,))
```

Keep the already covered `eval`, `exec`, and `__import__` cases; do not weaken or duplicate their assertions.

- [ ] **Step 3: Add entry-point and guard-helper bypass mutations**

Extend entry-point mutation coverage with the following exact families. Each mutation is appended to a parsed copy of `space/app.py` and must include `builtin_reflection`; mount/route cases must also preserve their existing structural violation:

```python
(
    'mount = gr.__getattribute__("mount_gradio_app")\nmount(parent, demo)',
    {"builtin_reflection", "mount_count"},
),
(
    'route = parent.__getattribute__("get")\n@route("/hidden")\ndef hidden():\n    pass',
    {"builtin_reflection", "parent_route"},
),
(
    'member = runtime_member\nmount = gr.__getattribute__(member)\nmount(parent, demo)',
    {"builtin_reflection", "mount_count"},
),
(
    'mount = vars(gr)["mount_gradio_app"]\nmount(parent, demo)',
    {"builtin_reflection", "mount_count"},
),
(
    'mount = gr.__dict__["mount_gradio_app"]\nmount(parent, demo)',
    {"builtin_reflection", "mount_count"},
),
```

Add guard-helper mutations that require `_guard_helper_violations(...)` to return a nonempty result even when no direct guard call is statically resolved:

```python
def _compose(parent):
    builder = ui_module.__getattribute__("build_package_asset_membership")
    guard = ui_module.__getattribute__("PublicSurfaceGuard")
    membership = builder()
    assert isinstance(membership, frozenset)
    assert membership
    return guard(parent, membership)
```

Repeat the guard mutation with `vars(ui_module)[...]`, `ui_module.__dict__[...]`, and a nonliteral member name. Preserve the existing positive test for direct bounded builder/guard aliases.

- [ ] **Step 4: Add a positive syntax-identity contract**

Add a synthetic application module proving that the allowed syntax identities do not trigger reflection violations:

```python
from __future__ import annotations

__all__ = ["CallableGuard"]

class CallableGuard:
    def __init__(self) -> None:
        self.source = __file__

    def __call__(self) -> str:
        return __name__
```

The test must assert `scan_capabilities((synthetic,)) == []`. Do not introduce an allowlist for arbitrary double-underscore member calls; the permission is limited to the syntax-defined uses above.

- [ ] **Step 5: Run RED and record the precise failure set**

Run only the newly added tests:

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_source_boundary.py -q -k "reflection or syntax_identity"
```

Expected: the new negative mutations fail because the current scanner accepts at least the dunder-reflection forms; the positive syntax-identity test may already pass. Record test count and failure names in the task report before implementation.

- [ ] **Step 6: Implement one bounded reflection scanner**

Add immutable exact-name sets near the existing capability constants:

```python
_FORBIDDEN_REFLECTION_CALLS = frozenset(
    {
        "getattr",
        "setattr",
        "delattr",
        "hasattr",
        "vars",
        "globals",
        "locals",
        "compile",
    }
)
_FORBIDDEN_REFLECTIVE_ATTRIBUTES = frozenset(
    {"__getattribute__", "__getattr__", "__setattr__", "__delattr__", "__dict__"}
)
_FORBIDDEN_REFLECTION_HELPERS = frozenset(
    {"operator.attrgetter", "operator.methodcaller", "inspect.getattr_static"}
)
_SENSITIVE_COMPOSITION_MEMBERS = frozenset(
    {
        "mount_gradio_app",
        "run",
        "add_middleware",
        "add_api_route",
        "include_router",
        "get",
        "post",
        "route",
        "build_package_asset_membership",
        "PublicSurfaceGuard",
    }
)
```

Implement `_dynamic_reflection_violations(...)` as a pure AST walk. It may resolve ordinary name/attribute aliases through the existing bounded resolver, but it must not evaluate Python, fold arbitrary expressions, import a module, or execute source. It returns stable exact suffixes for forbidden builtin calls, forbidden reflective attributes, `__dict__`, and the three named helper calls. Aliasing a forbidden builtin or named helper remains forbidden.

Integrate it in three places:

1. `scan_capabilities` appends `f"{path.name}:{suffix}"` for every dynamic-reflection violation before applying the existing read/write/network checks.
2. `_entrypoint_violations` adds `builtin_reflection` whenever the entry-point tree contains a dynamic-reflection violation. It then continues the existing mount/router/monkeypatch checks so the structural violation is also reported.
3. `_guard_helper_violations` performs a fail-closed pre-pass for each function. It marks `function_name:dynamic_reflection` when reflection targets `ui_module`, `gr`, `parent`, `uvicorn`, their ordinary aliases, or a literal `_SENSITIVE_COMPOSITION_MEMBERS` value. A nonliteral member on one of those roots also fails. This pre-pass happens before the early `if not all_guard_calls: continue`, so a hidden guard constructor cannot escape audit. Unrelated test-only `getattr(inner, "original_router", None)` and `getattr(socket, "AF_UNIX", None)` remain accepted.

- [ ] **Step 7: Run GREEN and mutation coverage**

Run:

```powershell
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_source_boundary.py -q -k "reflection or syntax_identity"
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_source_boundary.py space/tests/test_export_contract.py -q
.venv-space\Scripts\python.exe -m pytest space/tests/test_gradio_contract.py -q
```

Expected: all new reflection mutations pass; the complete Task 6 boundary suite passes; the Gradio contract remains green with only an already documented platform-capability skip if Windows cannot create the required symlink fixture.

- [ ] **Step 8: Run static and immutable-scope verification**

Run:

```powershell
.venv-space\Scripts\python.exe -m ruff check tests/test_hf_space_source_boundary.py
.venv-space\Scripts\python.exe -m ruff format --check tests/test_hf_space_source_boundary.py
.venv-space\Scripts\python.exe -m mypy --strict tests/test_hf_space_source_boundary.py
git diff --check
git diff --name-only 190819a838634bd10412f2af72cdc252f6ecd31a
git diff --exit-code 190819a838634bd10412f2af72cdc252f6ecd31a -- space/app.py space/carerisk_space space/tests/test_gradio_contract.py
```

Expected: Ruff, format check, strict Mypy, and whitespace checks pass; the only implementation path is `tests/test_hf_space_source_boundary.py`; all product and Gradio contract files remain byte-identical.

- [ ] **Step 9: Commit the exact implementation file**

```powershell
git add -- tests/test_hf_space_source_boundary.py
git diff --cached --check
git diff --cached --name-only
git commit -m "test(space): deny dynamic reflection boundary"
```

Expected: one implementation commit with exactly `tests/test_hf_space_source_boundary.py`, correct `kuotunyu <61350295+kuotunyu@users.noreply.github.com>` author/committer identity, no co-author trailer, clean tracked worktree, and no push.

