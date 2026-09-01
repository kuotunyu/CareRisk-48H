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
- every `monkeypatch.setattr` whose literal member is one of `getattr`, `type`, `isinstance`, `super`, `frozenset`, `signature`, `Parameter`, `empty`, `__version__`, `AF_UNIX`, `spec_from_file_location`, `module_from_spec`, or `PublicSurfaceGuard`, regardless of the first-argument receiver; RED cases must include direct receivers, a local receiver alias, `sys.modules["builtins"]`, `sys.modules["inspect"]`, and another registry/subscript receiver;
- every `monkeypatch.setattr` whose literal member is `create_app`, `build_package_asset_membership`, `mount_gradio_app`, or `run`, except the four exact full-node entrypoint substitutions below. Add RED cases for each exception with a wrong owner, duplicate call, alternate receiver, and changed replacement expression;
- every unapproved `monkeypatch` method, including `setitem`, `delattr`, and `delenv`; keep only exact direct `setattr` nodes and the current exact direct environment-only `setenv` nodes, and add a `monkeypatch.setitem(sys.modules, "inspect", sink)` RED mutation;
- direct protected-anchor mutation without `monkeypatch`: reject receiver-independently every `ast.Attribute` in `Store` or `Del` context whose member is in the protected-member set. RED cases must include `sys.modules["builtins"].isinstance = sink`, `target = inspect; target.signature = sink`, `del target.signature`, and alternate receivers for both builtin and inspect anchors;
- every access to an attribute token named `modules`, plus original/effective imports or aliases from `sys` of `modules`. Add RED cases for `sys.modules[...]`, `registry = sys.modules`, `from sys import modules`, aliased from-import, subscript replacement, and `.update(...)`; keep only exact top-level `import sys` and its two existing direct `sys.platform` contexts;
- alternate patch APIs: original/effective imports, aliases, bindings, parameters/fixtures, calls, decorators, and context managers involving `unittest.mock`, third-party `mock`, `patch`, `patch.object`, `patch.dict`, `patch.multiple`, `pytest_mock`, or `mocker`. Add RED cases for direct and aliased imports, original/effective `patch` names, decorator/context-manager calls, every named patch variant, `mocker` and aliased fixtures, and `mocker.patch(...)`;
- any drift from the exact 34 reviewed module-level import AST nodes: added/removed/reordered imports, changed original/effective names, aliases, imported members, wildcard, relative/nested imports, and imports inside functions/classes. The current 34-node import sequence is the positive fixture and later Task 10 must request design review before adding an import;
- any drift from the exact dynamic entrypoint-load statements in the sole top-level `test_entrypoint_mount_and_uvicorn_contract_are_exact`: one `importlib.util.spec_from_file_location("carerisk_space_entrypoint", SPACE_ROOT / "app.py")`, one `importlib.util.module_from_spec(spec)`, and one `spec.loader.exec_module(entrypoint)`, all direct, exact-count, positional, and keyword-free. Add wrong owner, duplicate/missing, changed literal/path/argument/receiver, keyword, and `spec`/`entrypoint` rebind REDs;
- dynamic import/resolver attributes and calls already reachable from allowed imports: `pytest.importorskip`, `uvicorn.importer`, `import_from_string`, `resolve_name`, `locate`, `find_spec`, and equivalent original/effective member tokens. Required REDs include `pytest.importorskip("pkgutil").resolve_name(...)`, `uvicorn.importer.import_from_string(...)`, an aliased resolver, and a resolver-returned callable applied to `ui_module.PublicSurfaceGuard`;
- drift from the sole exact module-body `SPACE_ROOT = Path(__file__).resolve().parents[1]` declaration immediately following the 34-import prefix, or any other load/binding/rebind/delete/global/nonlocal/import/alias of `SPACE_ROOT`. Protect the exact `Path` import identity and declaration source. Add REDs for a changed declaration, statement inserted before it, local/module rebind, alias source, delete, and a product-path write attempt;
- drift from the sole direct `uvicorn.Config(...)` call in `running_wire_app`: it must receive direct first positional argument `marker`, no other positional arguments, and exactly the current keyword/value AST (`host="127.0.0.1"`, `port=7860`, `workers=1`, `http="h11"`, `proxy_headers=False`, `forwarded_allow_ips=""`, `access_log=False`, `server_header=False`, `date_header=False`, `log_config=None`, `lifespan="on"`). Add REDs for a string/path/changed/extra positional app, wrong owner, duplicate, missing/changed keyword, alias, and alternate `uvicorn` receiver;
- assignment/parameter/function/class/import shadowing for `isinstance`, `super`, `frozenset`, `socket`, `pytest`, or any other protected identity; `monkeypatch` is positive only as an exact `pytest.MonkeyPatch` parameter in the owning function and every rebind/import/alternate annotation is negative;
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
- either sensitive attribute name is rejected on every receiver other than the exact unshadowed `ui_module` name, independently of alias analysis;
- original/effective imports of either sensitive member are rejected;
- ordinary or two-level aliases are rejected.

The four entrypoint exceptions are allowed only when the file contains exactly one top-level function named `test_entrypoint_mount_and_uvicorn_contract_are_exact` and that function owns exactly these four calls, one occurrence each, with no keywords and these exact AST shapes:

```python
monkeypatch.setattr(ui_module, "create_app", lambda bundle_root=None: demo)
monkeypatch.setattr(ui_module, "build_package_asset_membership", lambda: membership)
monkeypatch.setattr(gr, "mount_gradio_app", fake_mount)
monkeypatch.setattr(entrypoint.uvicorn, "run", fake_run)
```

The names `create_app`, `build_package_asset_membership`, `mount_gradio_app`, and `run` are default-denied as `monkeypatch.setattr` member literals before these four full-node exceptions are applied. An exception does not arise from a receiver/member pair alone.

The only `monkeypatch.setenv` exception is exactly one call, owned by the sole top-level function `test_exact_instance_state_ignores_poisoned_framework_environment`, with direct callee `monkeypatch.setenv`, positional arguments `name, value`, and no keywords. It must be the body of the existing `for name, value in { ... }.items():` loop whose literal mapping is exactly:

```python
{
    "GRADIO_ANALYTICS_ENABLED": "true",
    "HF_HUB_DISABLE_TELEMETRY": "0",
    "GRADIO_WATCH_DIRS": "/CANARY_7419",
    "GRADIO_VIBE_MODE": "true",
    "GRADIO_ROOT_PATH": "/CANARY_7419",
    "SPACE_ID": "CANARY_7419/space",
    "PORT": "9999",
}
```

Add RED mutations for a wrong owner, duplicate call, changed argument, keyword form, changed loop target, and changed/additional key or value.

Replace the existing positive test `test_guard_helper_audit_accepts_bounded_builder_and_guard_alias_lineage` with a negative test of the same alias lineage. No test may continue to assert that builder or guard aliases are accepted.

- [ ] **Step 3: Run RED**

Run the four new node IDs plus the existing current application syntax/entrypoint tests. Record collected count and exact failing nodes. RED must include the current `guard_type` alias and the newly added reflection/context mutations; do not edit the Gradio file before this evidence exists.

- [ ] **Step 4: Implement the closed-world scanner**

Use a parent map and finite allowed-node sets. Do not resolve alias values.

`_gradio_test_source_violations` must:

- identify the two exact allowed `getattr` callee `Name` nodes;
- identify the one exact allowed `type` callee in `type(exc).__name__ == "Failed"`;
- reject any semantic binding/import original/effective name that shadows a protected builtin or protected module identity. Protected identities include `getattr`, `type`, `isinstance`, `super`, `frozenset`, `inspect`, `importlib`, `socket`, `sys`, `pytest`, `ui_module`, `gr`, and `uvicorn`; allow only their exact existing top-level import nodes where applicable;
- reject every forbidden builtin `Name` load except the two recorded `getattr` nodes and the one recorded `type` node;
- reject reflection imports/helpers and `importlib.import_module` by source token;
- require the module-level `Import`/`ImportFrom` nodes to equal the exact current 34-node canonical AST sequence, preserving order, original names, aliases, members, and level; require that sequence to be the module-body prefix immediately followed by the sole exact `SPACE_ROOT = Path(__file__).resolve().parents[1]` assignment; reject every nested import. Independently reject every original/effective token or semantic binding named `unittest`, `mock`, `patch`, `pytest_mock`, or `mocker`, and every attribute token named `patch`;
- reject dunder attributes except exact `super().__init__()` inside a class-owned `__init__`, exact pinned `gr.__version__ == "6.26.0"`, and exact `type(exc).__name__ == "Failed"`;
- allow `__name__` and `__file__` loads, `from __future__ import annotations`, and class-owned `__init__` / `__call__` definitions only; apply the existing semantic dunder-binding checks everywhere else;
- permit `monkeypatch` only as an `ast.arg` with exact annotation `pytest.MonkeyPatch` in the owning function; reject every other semantic binding of that name. Permit `monkeypatch.setattr` only as an exact direct callee with three positional arguments, no keywords, and a literal string second argument; every other attribute named `setattr` fails. Permit exactly one `monkeypatch.setenv(name, value)` node with no keywords in the sole top-level owner `test_exact_instance_state_ignores_poisoned_framework_environment`, and require its immediate `for name, value in <exact seven-pair literal dict>.items()` parent structure; reject wrong owner/count/call arguments/keywords/loop target/literal mapping. Reject every other `monkeypatch` method, including `setitem`, `delattr`, and `delenv`;
- apply a receiver-independent member-literal denial before any exception: every `monkeypatch.setattr` with member `getattr`, `type`, `isinstance`, `super`, `frozenset`, `signature`, `Parameter`, `empty`, `__version__`, `AF_UNIX`, `spec_from_file_location`, `module_from_spec`, `PublicSurfaceGuard`, `create_app`, `build_package_asset_membership`, `mount_gradio_app`, or `run` fails regardless of whether its receiver is direct, aliased, or obtained through `sys.modules`/another registry;
- construct exactly four full-node exceptions to that denial, requiring exactly one top-level owner function named `test_entrypoint_mount_and_uvicorn_contract_are_exact`, exactly one occurrence of each call, exact direct callee/receiver/member/replacement AST, three positional arguments, and no keywords: `monkeypatch.setattr(ui_module, "create_app", lambda bundle_root=None: demo)`, `monkeypatch.setattr(ui_module, "build_package_asset_membership", lambda: membership)`, `monkeypatch.setattr(gr, "mount_gradio_app", fake_mount)`, and `monkeypatch.setattr(entrypoint.uvicorn, "run", fake_run)`. Reject wrong owner, duplicate, missing, alternate receiver, changed replacement, or any fifth protected-member substitution;
- reject every `ast.Attribute` in `Store` or `Del` context whose member is in the receiver-independent protected-member set; no full-node exception writes or deletes an anchor. Reject any attribute token named `modules`, any original/effective `from sys import modules` binding, and every alias/assignment path sourced from `sys` outside the two exact direct `sys.platform` contexts. This rejects direct subscript assignment and registry `.update(...)` before value-flow interpretation;
- permit `inspect.signature` only with one positional argument equal to the exact `ui_module.PublicSurfaceGuard` node and no keywords; permit only exact `inspect.Parameter.empty`; reject other `inspect` dynamic members;
- permit only the current exact `importlib.util` import and exact `importlib.util.spec_from_file_location` / `module_from_spec` callees;
- permit the `importlib.util` execution path only as exactly one three-statement chain inside the sole top-level `test_entrypoint_mount_and_uvicorn_contract_are_exact`: `spec = importlib.util.spec_from_file_location("carerisk_space_entrypoint", SPACE_ROOT / "app.py")`, `entrypoint = importlib.util.module_from_spec(spec)`, and `spec.loader.exec_module(entrypoint)`. Require exact direct receivers, count, assignment targets, positional arguments, and no keywords; reject every other semantic binding of `spec` or `entrypoint` and every other `exec_module` attribute;
- reject receiver-independently every attribute/member token `importorskip`, `importer`, `import_from_string`, `resolve_name`, `locate`, or `find_spec`, plus original/effective imports or bindings of those names. Do not infer whether the call would import; reject the source token;
- treat `Path` and `SPACE_ROOT` as protected identities. Permit `Path`'s exact current import and ordinary existing type/path uses, but no semantic rebinding, alias assignment sourced from it, or import alias. Permit exactly three reviewed `SPACE_ROOT` Name nodes: the exact module assignment target in `Store` context, `(SPACE_ROOT / "carerisk_space" / "ui.py").read_text(encoding="utf-8")`, and `SPACE_ROOT / "app.py"` as argument 1 of the exact `spec_from_file_location` call; reject every other load or binding. This source-token rule also rejects product-path writes;
- permit `uvicorn` attributes only in their current reviewed direct contexts: the sole exact `uvicorn.Config(marker, ...)` call in `running_wire_app` with the complete pinned keyword/value AST, the direct `uvicorn.Server(config)` call, and the exact entrypoint `run` substitution already enumerated. Reject string/path app targets, `uvicorn.importer`, alternate receivers, aliases, changed owner/count/arguments, and every other `uvicorn` attribute;
- reject any `ast.Attribute` whose `.attr` is `PublicSurfaceGuard` or `build_package_asset_membership` unless its receiver is exact `ast.Name(id="ui_module")` and its parent shape is one of the allowed contexts above; enforce this receiver-independent check before the context exceptions;
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
