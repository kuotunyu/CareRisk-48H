# CareRisk Closed-World Gradio Test-Source Corrective Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `subagent-driven-development` or `executing-plans`. Implement exactly one task, with RED/GREEN and independent review.

**Goal:** Replace the exhausted guard-helper reflection alias evaluator with a closed-world source-token contract that is compatible with the current public Gradio test source and later Task 10 direct tests.

**Architecture:** The application scanner and all product sources remain unchanged. The test boundary scans the entire `space/tests/test_gradio_contract.py` before composition checks, permits two exact harmless builtin `getattr` calls and a finite set of static identity contexts, and rejects every other reflection origin at its source token. Guard and membership-builder references use exact direct contexts; one existing `guard_type` alias block is mechanically converted to direct calls.

**Tech stack:** Python 3.11, `ast`, Pytest, Ruff, strict Mypy, existing `.venv-space`.

## Global constraints

- The controller supplies an exact clean BASE on `docs/carerisk-hf-space-design`; remote must be `https://github.com/kuotunyu/CareRisk-48H.git`.
- Modify only `tests/test_hf_space_source_boundary.py` and the exact `guard_type` block in `space/tests/test_gradio_contract.py`.
- Do not modify `space/app.py`, `space/carerisk_space/*.py`, evidence, deployment identities, locks, Docker, UI behavior, or scientific artifacts.
- Do not read `.env`, private data/research/model/checkpoints, Set B locks/evaluation, or Set C. Do not run exporter/model/training/evaluation/persistent services.
- Do not push, deploy, create, or modify GitHub/Hugging Face resources.
- This plan supersedes the guard-helper alias-state portion of `2026-09-01-carerisk-reflection-boundary-corrective.md`; it does not change that plan's application-source scanner.
- Original HF Space Task 7 remains blocked until this task passes independent review and controller verification and the old ledger is explicitly released.
- Exact path staging only; never use `git add .`, `git add -A`, directory staging, or wildcard staging.

---

### Task 1: Enforce a closed-world Gradio test-source contract

**Files:**
- Modify: `tests/test_hf_space_source_boundary.py`
- Modify mechanically: `space/tests/test_gradio_contract.py`
- Report only: `.superpowers/sdd/2026-09-01-carerisk-test-source-closed-world-corrective/task-1-report.md`

**Produces:**
- `_gradio_test_source_violations(tree: ast.Module) -> list[str]`
- `_guard_helper_violations(tree: ast.Module) -> list[str]` remains signature-compatible but uses the whole-file source gate plus direct composition checks; remove the `_ReflectionAliasState` evaluator and its mapping/callable fixed-point helpers.

- [ ] **Step 1: Confirm exact BASE and frozen scope**

Run `git rev-parse HEAD`, root, remote, branch, clean status, design-ancestor, and immutable product diffs. Stop on any mismatch. Record exact output in the report.

- [ ] **Step 2: Add RED closed-world source tests**

Add one whole-current-file positive test and mutation tests under stable node IDs:

1. `test_gradio_contract_source_is_closed_world_reflection_free`
2. `test_gradio_contract_source_rejects_reflection_near_misses`
3. `test_gradio_contract_sensitive_members_have_exact_contexts`
4. `test_guard_helper_audit_rejects_sensitive_reflection_candidates`

The whole-current-file test initially fails only because the existing `guard_type = ui_module.PublicSurfaceGuard` alias is outside the new context allowlist.

The only permitted builtin reflection calls are exact AST matches with no keywords:

```python
getattr(inner, "original_router", None)
getattr(socket, "AF_UNIX", None)
```

For both, add negative mutations for changed receiver, member, missing/changed default, extra argument, keyword form, aliased callee, assignment/default/lambda capture of `getattr`, function/parameter/class named `getattr`, and imported/original/effective aliases. Any binding or shadowing of `getattr` makes even an otherwise exact call invalid.

Add negative source mutations for:

- bare or aliased `setattr`, `delattr`, `hasattr`, `vars`, `globals`, `locals`, `eval`, `exec`, `compile`, `__import__`, and `__builtins__`;
- `import builtins`, `from builtins import ...`, `operator.attrgetter`, `operator.methodcaller`, `inspect.getattr_static`, `inspect.getmembers`, and `importlib.import_module`;
- every non-allowlisted dunder attribute, including `__dict__`, `__globals__`, `__class__`, `__getattribute__`, `__getattr__`, `__setattr__`, `__delattr__`, `__getitem__`, and attribute `__call__`;
- near-miss `super().__init__`, `gr.__version__`, `type(exc).__name__`, `inspect.signature`, and `inspect.Parameter.empty` shapes;
- binding/shadowing/import aliases of `type`, `inspect`, `importlib`, `ui_module`, `gr`, and `uvicorn` outside their one exact existing top-level import;
- `monkeypatch.setattr` assigned to an alias, called through another receiver, called with a nonliteral member, or referenced without being the direct `Call.func`;
- `"PublicSurfaceGuard"` as a dynamic member string.

Keep current `import importlib.util` and its exact `spec_from_file_location` / `module_from_spec` calls. Keep exact unaliased `import inspect`, `inspect.Parameter.empty`, and the one exact signature call defined below. No wildcard or near-match is allowed.

Sensitive-member context mutations must include:

```python
guard = ui_module.PublicSurfaceGuard
guard_alias = guard
guard_alias(parent, membership)

builder = ui_module.build_package_asset_membership
builder()

from carerisk_space.ui import PublicSurfaceGuard as guard
from carerisk_space.ui import build_package_asset_membership as builder

reflect(ui_module, "PublicSurfaceGuard")
ui_alias = ui_module
ui_alias.PublicSurfaceGuard(parent, membership)
```

Required context rules:

- every `ui_module.build_package_asset_membership` attribute is the exact direct callee of a zero-argument, zero-keyword call;
- every `ui_module.PublicSurfaceGuard` attribute is exactly one of: direct `Call.func`; the sole positional argument of `inspect.signature(...)`; or argument index 1 of direct `isinstance(value, ui_module.PublicSurfaceGuard)` with no keywords;
- original/effective imports of either sensitive member are rejected;
- ordinary or two-level aliases are rejected.

- [ ] **Step 3: Run RED**

Run the four new node IDs plus the existing current application syntax/entrypoint tests. Record collected count and exact failing nodes. RED must include the current `guard_type` alias and the newly added reflection/context mutations; do not edit the Gradio file before this evidence exists.

- [ ] **Step 4: Implement the closed-world scanner**

Use a parent map and finite allowed-node sets. Do not resolve alias values.

`_gradio_test_source_violations` must:

- identify the two exact allowed `getattr` callee `Name` nodes;
- identify the one exact allowed `type` callee in `type(exc).__name__ == "Failed"`;
- reject any semantic binding/import original/effective name that shadows a protected builtin or protected module identity;
- reject every forbidden builtin `Name` load except the two recorded `getattr` nodes and the one recorded `type` node;
- reject reflection imports/helpers and `importlib.import_module` by source token;
- reject dunder attributes except exact `super().__init__()` inside a class-owned `__init__`, exact pinned `gr.__version__ == "6.26.0"`, and exact `type(exc).__name__ == "Failed"`;
- allow `__file__` load, `from __future__ import annotations`, and class-owned `__init__` / `__call__` definitions only; apply the existing semantic dunder-binding checks everywhere else;
- permit `monkeypatch.setattr` only as an exact direct callee with three positional arguments, no keywords, and a literal string second argument; every other attribute named `setattr` fails;
- permit `inspect.signature` only with one positional argument equal to the exact `ui_module.PublicSurfaceGuard` node and no keywords; permit only exact `inspect.Parameter.empty`; reject other `inspect` dynamic members;
- permit only the current exact `importlib.util` import and exact `importlib.util.spec_from_file_location` / `module_from_spec` callees;
- enforce the builder/guard context rules above;
- return deduplicated deterministic sorted findings.

Delete the `_ReflectionAliasState`, marker constants, `_owned_nodes`, mapping/callable state classifiers, fixed-point construction, and module/function reflection evaluator. `_guard_helper_violations` first appends whole-file source findings, then performs existing direct guard/builder argument, membership, assertion, and rejection-path checks without accepting aliases.

- [ ] **Step 5: Make the one mechanical Gradio test cleanup**

In `test_outer_guard_constructor_is_exact_and_rejects_empty_membership` only:

```python
parameters = inspect.signature(ui_module.PublicSurfaceGuard).parameters
...
guard = ui_module.PublicSurfaceGuard(DownstreamRecorder(), membership)
...
ui_module.PublicSurfaceGuard(DownstreamRecorder(), frozenset())
...
ui_module.PublicSurfaceGuard(DownstreamRecorder(), set(membership))
```

Remove `guard_type = ui_module.PublicSurfaceGuard`. Do not change assertions, test behavior, any other function, or product code.

- [ ] **Step 6: Run GREEN and complete verification**

Run:

```powershell
.venv-space\Scripts\python.exe -m pytest -q `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_source_is_closed_world_reflection_free `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_source_rejects_reflection_near_misses `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_sensitive_members_have_exact_contexts `
  tests/test_hf_space_source_boundary.py::test_guard_helper_audit_rejects_sensitive_reflection_candidates `
  tests/test_hf_space_source_boundary.py::test_application_syntax_identities_are_not_reflection `
  tests/test_hf_space_source_boundary.py::test_entrypoint_scanner_rejects_reflection_without_resolving_forbidden_flow
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_source_boundary.py space/tests/test_export_contract.py -q
$env:PYTHONPATH = (Resolve-Path space).Path
.venv-space\Scripts\python.exe -m pytest space/tests/test_gradio_contract.py -q
.venv-space\Scripts\python.exe -m ruff check tests/test_hf_space_source_boundary.py space/tests/test_gradio_contract.py
.venv-space\Scripts\python.exe -m ruff format --check tests/test_hf_space_source_boundary.py space/tests/test_gradio_contract.py
.venv-space\Scripts\python.exe -m mypy --strict tests/test_hf_space_source_boundary.py
git diff --check
git diff --name-only
git diff --exit-code -- space/app.py space/carerisk_space
```

Expected: all tests/static checks pass with only documented platform skips; exact modified paths are the two declared files; product source is byte-identical.

- [ ] **Step 7: Commit and independent acceptance**

Stage exactly the two files and commit as `test(space): close Gradio source reflection surface` using `kuotunyu <61350295+kuotunyu@users.noreply.github.com>`. No co-author, push, or deployment.

The controller generates a review package from exact BASE to HEAD and dispatches an independent reviewer. Acceptance requires Spec ✅, Quality Approved, Critical `0`, Important `0`. Controller reruns the targeted, full boundary/export, Gradio, Ruff, strict Mypy, scope, identity, and clean-tree gates. Only then may it record this plan complete and release the original HF Space Task 7.
