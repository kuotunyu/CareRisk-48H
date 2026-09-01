# CareRisk Reflection-Free Public Boundary Corrective Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the exhausted Task 6 reflection-alias chase with a fail-closed, reflection-free public application capability contract, then return the original HF Space plan to a reviewable boundary.

**Architecture:** The public application remains unchanged. One AST contract file gains a deny-by-construction reflection scanner that runs before the existing exact composition checks. Application sources reject every dynamic attribute primitive; entry-point and guard-helper audits additionally reject reflection that targets their framework objects or sensitive member names, without becoming a Python evaluator.

**Tech Stack:** Python 3.11, `ast`, Pytest, Ruff, Mypy, existing `.venv-space` environment.

## Global Constraints

- The governing design is commit `190819a838634bd10412f2af72cdc252f6ecd31a`; the SDD controller records the exact implementation BASE immediately before dispatch. BASE must be a clean descendant of the governing design on branch `docs/carerisk-hf-space-design`.
- Authority reconciliation: on 2026-09-01 the controller verified that the stale `AGENTS.md` desktop path does not exist, while the user-scoped `D:\AI-Portfolio\CC_github部隊\長照\4_CareRisk 48H` checkout has the exact canonical remote `https://github.com/kuotunyu/CareRisk-48H.git`. The user's repeated instruction to personally continue the unfinished CareRisk session authorizes local continuation on its existing `docs/carerisk-hf-space-design` branch. `AGENTS.md` still forbids another clone/worktree and all push/deploy/publication actions.
- The sole product capability policy is design Section 9.1, “Dynamic reflection is denied by construction.”
- Do not modify `space/app.py`, `space/carerisk_space/*.py`, the public path list, evidence bytes, deployment identities, dependency locks, Docker files, UI behavior, or any scientific artifact.
- Do not read `.env`, private data, private research artifacts, model bundles, checkpoints, Set B custody/evaluation assets, private ledgers/final locks, or Set C.
- Do not run the receipt exporter, model code, training, evaluation, or persistent service.
- Do not create, upload, deploy, or modify a GitHub or Hugging Face resource; do not push this branch.
- Product application sources reject direct or aliased `getattr`, `setattr`, `delattr`, `hasattr`, `vars`, `globals`, `locals`, `eval`, `exec`, `compile`, and `__import__`; the implicit `__builtins__` mapping; every double-underscore attribute reference; every double-underscore function definition except method definitions `__init__` and `__call__`; every double-underscore name load except `__name__` and `__file__`; every semantic double-underscore binding except at most one qualifying module-level literal-string `__all__` assignment target; exact dynamic protocol-name string literals; `operator.attrgetter`/`operator.methodcaller`; `inspect.getattr_static`; `type` outside an exact approved validation comparison; and the reachable standard-library class factories named in design Section 9.1. Import original names and effective local aliases are both checked, so an allowed module cannot export a forbidden dunder under a benign alias. The only permitted `type` loads are direct `type(<non-starred expression>) is [not] str|int|frozenset` comparisons with exactly one argument, no keywords, and one comparator, and no source form may bind or shadow the name `type`. From `types`, only `MappingProxyType` may be imported; `dataclasses.make_dataclass`, `collections.namedtuple`, functional `typing.NamedTuple`/`typing.TypedDict`, and wildcard imports from those four modules are denied.
- Enforcement rejects forbidden builtin `Name` loads and forbidden reflective/helper `Attribute` references at the source token. It does not resolve arbitrary downstream alias flow. Violations are deduplicated and returned in deterministic sorted order.
- Syntax-defined `__future__`, `__name__`, `__file__`, `__all__`, `__init__`, and `__call__` uses remain permitted when they are not used to retrieve or mutate another attribute.
- The entry point still requires direct named construction: one `FastAPI(...)`, one `gr.mount_gradio_app(...)`, one `build_package_asset_membership()`, one `PublicSurfaceGuard(...)`, and one `uvicorn.run(...)` beneath the exact main guard.
- Existing unrelated test introspection in `space/tests/test_gradio_contract.py`, such as reading `original_router` or `AF_UNIX`, is not an application capability and must remain valid. Guard-helper classification uses a bounded fixed point for ordinary name aliases of `__builtins__`, literal-key `[...]`/`.get(...)` callables derived from that mapping, and further ordinary callable aliases; it does not interpret containers, defaults, returns, or control flow.
- This corrective is a distinct plan authorized after the old Task 6 five-round breaker, not fix round 6. It does not release original-plan Task 7 by implementation alone: independent task review, controller verification, explicit old-ledger Task 6 completion, and a `Task 7 released` ledger entry are mandatory first.
- Use exact path staging only. Never use `git add .`, `git add -A`, directory staging, or wildcard staging.

---

### Task 1: Enforce the reflection-free source and composition boundary

**Files:**
- Modify: `tests/test_hf_space_source_boundary.py`
- Verify unchanged: `space/tests/test_gradio_contract.py`
- Report only: `.superpowers/sdd/2026-09-01-carerisk-reflection-boundary-corrective/task-1-report.md`

**Interfaces:**
- Consumes: the exact implementation BASE recorded by the SDD controller; `scan_capabilities(paths: Iterable[Path]) -> list[str]`, `_entrypoint_violations(tree: ast.Module) -> list[str]`, `_guard_helper_violations(tree: ast.Module) -> list[str]`, `_bounded_aliases(tree: ast.AST, roots: frozenset[str]) -> tuple[dict[str, str], set[str]]`.
- Produces: `_dynamic_reflection_violations(tree: ast.AST) -> list[str]` and `_sensitive_reflection_in_helper(function: ast.FunctionDef, aliases: dict[str, str]) -> bool`; the three existing public boundary interfaces remain signature-compatible. The report path above records RED/GREEN commands, exact outputs, scope, commit, and concerns and is excluded from Git.

- [ ] **Step 1: Confirm the exact baseline and immutable scope**

Run:

```powershell
git rev-parse HEAD
git rev-parse --show-toplevel
git remote get-url origin
git branch --show-current
git status --short --branch
git merge-base --is-ancestor 190819a838634bd10412f2af72cdc252f6ecd31a HEAD
git diff --exit-code b01a79315b7b5716159f7bdea802be1339ef0c9b -- space/app.py space/carerisk_space space/tests/test_gradio_contract.py
```

Expected: HEAD equals the BASE supplied by the SDD controller; root is exactly `D:/AI-Portfolio/CC_github部隊/長照/4_CareRisk 48H`; remote is exactly `https://github.com/kuotunyu/CareRisk-48H.git`; branch is `docs/carerisk-hf-space-design`; tracked worktree is clean; the governing design is an ancestor; and the immutable-scope diff from the final old Task 6 implementation exits zero.

- [ ] **Step 2: Add product-source reflection mutations**

Add five independent mutation-test groups. The first proves every forbidden builtin is rejected at the `Name` load, including alias sources that require no call-signature knowledge:

```python
@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    "forbidden_name",
    (
        "getattr", "setattr", "delattr", "hasattr", "vars", "globals",
        "locals", "eval", "exec", "compile", "__import__",
    ),
)
def test_application_forbidden_reflection_name_load_is_denied(
    tmp_path: Path,
    forbidden_name: str,
) -> None:
    for source in (
        forbidden_name,
        f"alias = {forbidden_name}",
        f"def capture(value={forbidden_name}):\n    return value",
        f"capture = lambda: {forbidden_name}",
        f"captured = ({forbidden_name} := {forbidden_name})",
        f"captured = [{forbidden_name}]",
    ):
        synthetic = tmp_path / "synthetic.py"
        synthetic.write_text(source, encoding="utf-8")
        assert f"synthetic.py:{forbidden_name}" in scan_capabilities((synthetic,))
```

The named-expression case intentionally reuses the builtin identifier as its store target; the `Load` on the right remains the violation. Add a second parametrized test over the same exact builtin-name tuple that writes both `f'captured = __builtins__["{forbidden_name}"]'` and `f'captured = __builtins__.get("{forbidden_name}")'` and requires `synthetic.py:__builtins__` for every case. Keep the existing direct dynamic-code tests as independent legacy coverage. Add the same direct-expression plus ordinary-alias pair for every forbidden reflective attribute and named helper:

```python
@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("expression", "expected_suffix"),
    (
        ("target.__getattribute__", "__getattribute__"),
        ("target.__getattr__", "__getattr__"),
        ("target.__setattr__", "__setattr__"),
        ("target.__delattr__", "__delattr__"),
        ("target.__dict__", "__dict__"),
        ("target.__globals__", "__globals__"),
        ("target.__class__", "__class__"),
        ("operator.attrgetter", "operator.attrgetter"),
        ("operator.methodcaller", "operator.methodcaller"),
        ("inspect.getattr_static", "inspect.getattr_static"),
    ),
)
def test_application_forbidden_reflective_attribute_load_is_denied(
    tmp_path: Path,
    expression: str,
    expected_suffix: str,
) -> None:
    for source in (expression, f"alias = {expression}"):
        synthetic = tmp_path / "synthetic.py"
        synthetic.write_text(source, encoding="utf-8")
        assert f"synthetic.py:{expected_suffix}" in scan_capabilities((synthetic,))
```

Add a separate protocol-definition mutation because a method definition is not an `ast.Attribute`:

```python
@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    "hook_name",
    ("__getattribute__", "__getattr__", "__setattr__", "__delattr__", "__iter__"),
)
def test_application_dynamic_protocol_definitions_are_denied(
    tmp_path: Path,
    hook_name: str,
) -> None:
    synthetic = tmp_path / "synthetic.py"
    synthetic.write_text(
        f"class Dynamic:\n    def {hook_name}(self, *args):\n        return None\n",
        encoding="utf-8",
    )
    assert f"synthetic.py:{hook_name}" in scan_capabilities((synthetic,))
```

Add one test named `test_application_dunder_assignment_and_dynamic_class_construction_are_denied`. Its mutations and required suffixes are exact:

```python
(
    "class Dynamic:\n    __getattr__ = lambda self, name: None",
    "__getattr__",
),
(
    "class Dynamic:\n    __getattr__: object = handler",
    "__getattr__",
),
(
    "class Dynamic:\n    __getattr__ += handler",
    "__getattr__",
),
(
    "del __getattr__",
    "__getattr__",
),
(
    "Dynamic = type('Dynamic', (), {'__getattr__': handler})",
    "dynamic_type",
),
(
    "class_factory = type\nDynamic = class_factory('Dynamic', (), {})",
    "dynamic_type",
),
(
    "factory = type(ExistingClass)\nDynamic = factory('Dynamic', (), {})",
    "dynamic_type",
),
(
    "Dynamic = type(ExistingClass)('Dynamic', (), {})",
    "dynamic_type",
),
(
    "Dynamic = type(*args)",
    "dynamic_type",
),
(
    "type = factory\ntype(value) is str",
    "dynamic_type_binding",
),
(
    "def validate(type):\n    return type(value) is str",
    "dynamic_type_binding",
),
(
    "def type(value):\n    return value",
    "dynamic_type_binding",
),
(
    "class type:\n    pass",
    "dynamic_type_binding",
),
(
    "import dataclasses as type\ntype.make_dataclass('Dynamic', [])",
    "dynamic_type_binding",
),
(
    "from dataclasses import make_dataclass as type\ntype('Dynamic', []) is str",
    "dynamic_type_binding",
),
(
    "try:\n    raise RuntimeError\nexcept RuntimeError as type:\n    pass",
    "dynamic_type_binding",
),
(
    "match value:\n    case type:\n        pass",
    "dynamic_type_binding",
),
(
    "type: object = factory",
    "dynamic_type_binding",
),
(
    "type += factory",
    "dynamic_type_binding",
),
(
    "captured = (type := factory)",
    "dynamic_type_binding",
),
(
    "for type in values:\n    pass",
    "dynamic_type_binding",
),
(
    "captured = [value for type in values]",
    "dynamic_type_binding",
),
(
    "with manager() as type:\n    pass",
    "dynamic_type_binding",
),
(
    "def positional_only(type, /):\n    pass",
    "dynamic_type_binding",
),
(
    "def variadic(*type):\n    pass",
    "dynamic_type_binding",
),
(
    "def keyword_only(*, type):\n    pass",
    "dynamic_type_binding",
),
(
    "def variadic_keyword(**type):\n    pass",
    "dynamic_type_binding",
),
(
    "capture = lambda type: type",
    "dynamic_type_binding",
),
(
    "async def type():\n    pass",
    "dynamic_type_binding",
),
(
    "match values:\n    case [*type]:\n        pass",
    "dynamic_type_binding",
),
(
    "match mapping:\n    case {**type}:\n        pass",
    "dynamic_type_binding",
),
(
    "from types import new_class\nDynamic = new_class('Dynamic')",
    "dynamic_class_factory",
),
(
    "import types",
    "dynamic_class_factory",
),
(
    "import types as t",
    "dynamic_class_factory",
),
(
    "from types import new_class as factory",
    "dynamic_class_factory",
),
(
    "from types import MappingProxyType, new_class",
    "dynamic_class_factory",
),
(
    "import dataclasses\nDynamic = dataclasses.make_dataclass('Dynamic', [])",
    "dynamic_class_factory",
),
(
    "from dataclasses import make_dataclass as factory\nDynamic = factory('Dynamic', [])",
    "dynamic_class_factory",
),
(
    "import collections as c\nDynamic = c.namedtuple('Dynamic', 'value')",
    "dynamic_class_factory",
),
(
    "from collections import namedtuple as factory\nDynamic = factory('Dynamic', 'value')",
    "dynamic_class_factory",
),
(
    "import typing\nDynamic = typing.NamedTuple('Dynamic', [('value', int)])",
    "dynamic_class_factory",
),
(
    "from typing import TypedDict as factory\nDynamic = factory('Dynamic', {'value': int})",
    "dynamic_class_factory",
),
(
    "from typing import *",
    "dynamic_class_factory",
),
(
    "class __all__:\n    pass",
    "__all__",
),
(
    "class __init__:\n    pass",
    "__init__",
),
(
    "def __init__():\n    pass",
    "__init__",
),
(
    "import json as __all__",
    "__all__",
),
(
    "from json import loads as __all__",
    "__all__",
),
(
    "from carerisk_space.ui import __builtins__ as builtin_map",
    "__builtins__",
),
(
    "def validate(__all__):\n    pass",
    "__all__",
),
(
    "try:\n    raise RuntimeError\nexcept RuntimeError as __all__:\n    pass",
    "__all__",
),
(
    "match value:\n    case __all__:\n        pass",
    "__all__",
),
(
    "match values:\n    case [*__all__]:\n        pass",
    "__all__",
),
(
    "match mapping:\n    case {**__all__}:\n        pass",
    "__all__",
),
(
    "def declare():\n    global __all__",
    "__all__",
),
```

Also mutate a module-level `__all__ = ["Allowed"]` declaration into each of: a class-body `__all__ = ["NotAllowed"]`, two top-level qualifying `__all__` declarations, and one top-level `__all__ = [runtime_name]`; require `__all__` for every mutation. The exception applies to at most one top-level `Assign` or `AnnAssign`, targets only `__all__`, and its value is a list or tuple containing only string literals. Add positive assertions for singular qualifying `Assign` and `AnnAssign` forms and for the exact approved `type(value) is not str`, `type(value) is not int`, and `type(value) is not frozenset` comparisons. Standalone `type(value)`, nested calls, and starred calls remain negative.

- [ ] **Step 3: Add entry-point and guard-helper bypass mutations**

Extend entry-point mutation coverage with the following exact families. Each mutation is appended to a parsed copy of `space/app.py` and must include `builtin_reflection`. It must not require `mount_count` or `parent_route`: reflection is already forbidden, so the scanner deliberately does not resolve the hidden data flow. Existing direct and ordinary-alias mutations continue to prove structural counts.

```python
(
    'mount = gr.__getattribute__("mount_gradio_app")\nmount(parent, demo)',
    {"builtin_reflection"},
),
(
    'route = parent.__getattribute__("get")\n@route("/hidden")\ndef hidden():\n    pass',
    {"builtin_reflection"},
),
(
    'member = runtime_member\nmount = gr.__getattribute__(member)\nmount(parent, demo)',
    {"builtin_reflection"},
),
(
    'mount = vars(gr)["mount_gradio_app"]\nmount(parent, demo)',
    {"builtin_reflection"},
),
(
    'mount = gr.__dict__["mount_gradio_app"]\nmount(parent, demo)',
    {"builtin_reflection"},
),
(
    'from carerisk_space.ui import __builtins__ as builtin_map\n'
    'reflect = builtin_map["getattr"]\n'
    'hidden_mount = reflect(gr, "mount_gradio_app")\n'
    'hidden_mount(parent, demo)',
    {"builtin_reflection"},
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

Repeat the guard mutation with `vars(ui_module)[...]`, `ui_module.__dict__[...]`, and a nonliteral member on the `ui_module` root. Add the exact bounded builtin-alias mutation `reflect = getattr; member = runtime_member; guard = reflect(ui_module, member)` and the implicit-mapping mutation `reflect = __builtins__["getattr"]; guard = reflect(ui_module, "PublicSurfaceGuard")`; both must produce a nonempty guard-helper violation even though no direct guard call resolves.

Add both fixed-point variants below and require nonempty guard-helper findings:

```python
def _compose(parent):
    builtins_map = __builtins__
    return builtins_map["getattr"](ui_module, "PublicSurfaceGuard")

def _compose(parent):
    builtins_map = __builtins__
    mapping_alias = builtins_map
    reflect = mapping_alias.get("getattr")
    reflect_alias = reflect
    return reflect_alias(ui_module, "PublicSurfaceGuard")
```

The fixed point is limited to ordinary `Name` assignments, literal forbidden-builtin keys, and `[...]`/`.get(...)`; it does not evaluate arbitrary mappings or expressions. Preserve the existing positive test for direct bounded builder/guard aliases. Add one explicit acceptance test whose functions contain only `getattr(other, "get")`, `getattr(inner, "original_router", None)`, and `getattr(socket, "AF_UNIX", None)` and assert `_guard_helper_violations(tree) == []`; a sensitive word on an unrelated receiver is not helper candidacy.

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
.venv-space\Scripts\python.exe -m pytest -q `
  tests/test_hf_space_source_boundary.py::test_application_forbidden_reflection_name_load_is_denied `
  tests/test_hf_space_source_boundary.py::test_application_implicit_builtins_mapping_is_denied `
  tests/test_hf_space_source_boundary.py::test_application_forbidden_reflective_attribute_load_is_denied `
  tests/test_hf_space_source_boundary.py::test_application_dynamic_protocol_definitions_are_denied `
  tests/test_hf_space_source_boundary.py::test_application_dunder_assignment_and_dynamic_class_construction_are_denied `
  tests/test_hf_space_source_boundary.py::test_entrypoint_scanner_rejects_reflection_without_resolving_forbidden_flow `
  tests/test_hf_space_source_boundary.py::test_guard_helper_audit_rejects_sensitive_reflection_candidates `
  tests/test_hf_space_source_boundary.py::test_guard_helper_audit_allows_unrelated_test_introspection `
  tests/test_hf_space_source_boundary.py::test_application_syntax_identities_are_not_reflection
```

Expected: the new negative mutations fail because the current scanner accepts at least the dunder-reflection forms; the positive syntax-identity test may already pass. Record test count and failure names in the task report before implementation.

- [ ] **Step 6: Implement one bounded reflection scanner**

Add immutable exact-name sets near the existing capability constants:

```python
_FORBIDDEN_REFLECTION_NAMES = frozenset(
    {
        "getattr",
        "setattr",
        "delattr",
        "hasattr",
        "vars",
        "globals",
        "locals",
        "eval",
        "exec",
        "compile",
        "__import__",
        "__builtins__",
    }
)
_ALLOWED_DUNDER_NAME_LOADS = frozenset({"__name__", "__file__"})
_ALLOWED_DUNDER_DEFINITIONS = frozenset({"__init__", "__call__"})
_FORBIDDEN_DYNAMIC_PROTOCOL_LITERALS = frozenset(
    {"__getattribute__", "__getattr__", "__setattr__", "__delattr__"}
)
_FORBIDDEN_REFLECTION_HELPERS = frozenset(
    {"operator.attrgetter", "operator.methodcaller", "inspect.getattr_static"}
)
_FORBIDDEN_STDLIB_CLASS_FACTORIES = frozenset(
    {"make_dataclass", "namedtuple", "NamedTuple", "TypedDict"}
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

Implement `_is_dunder(name: str) -> bool` as `len(name) > 4 and name.startswith("__") and name.endswith("__")`. Identify a permitted `__all__` target node only when the module contains exactly one top-level `Assign` or `AnnAssign` targeting only `__all__`, its value is a literal list or tuple containing only string constants, and there is no second top-level `__all__` declaration; otherwise permit no `__all__` target. Build an AST parent map. A `FunctionDef`/`AsyncFunctionDef` named `__init__` or `__call__` is permitted only when its direct parent is an `ast.ClassDef`; a module or nested function with either name is not a method exception. No class-name exception exists.

Add one unified semantic dunder-binding check. In addition to `ast.Name` `Store`/`Del`, inspect every `ast.arg`; `FunctionDef`, `AsyncFunctionDef`, and `ClassDef` name; both the original leaf name and effective local name of each `ast.alias` (using its `Import` versus `ImportFrom` parent); `ExceptHandler.name`; `MatchAs.name`; `MatchStar.name`; `MatchMapping.rest`; and each string in `Global.names` and `Nonlocal.names`. Reject every dunder discovered there except the exact method and sole `__all__` target exceptions above. Thus a benign alias cannot hide an imported `__builtins__`, and an allowed original import cannot bind to `__all__`.

Identify permitted `type` load nodes only when all of these facts hold: the node is the exact direct `ast.Name(id="type")` callee of an `ast.Call`; the call has exactly one non-`ast.Starred` positional argument and no keywords; the call is the left operand of an `ast.Compare` with exactly one operator and one comparator; the operator is `ast.Is` or `ast.IsNot`; and the comparator is a direct `ast.Name` in `{str, int, frozenset}`. The permitted compare cannot serve as an alias exception for any other `type` load. Every other `type` load is `dynamic_type`.

Before granting any permitted `type` load, reject every source binding whose local name is exactly `type`: `ast.Name` in `Store` or `Del`; every positional, keyword-only, variadic, or lambda `ast.arg`; `FunctionDef`, `AsyncFunctionDef`, or `ClassDef` names; the effective local name of any `ast.alias`; `ExceptHandler.name`; and capture names in `MatchAs`, `MatchStar`, or `MatchMapping`. Emit `dynamic_type_binding`. This covers ordinary/annotated/augmented/walrus assignments, loop/comprehension/with targets, parameters, definitions, imports, exception targets, and structural-pattern captures without interpreting control flow.

Implement `_dynamic_reflection_violations(...)` as a pure AST walk with a `set[str]` accumulator and `sorted(...)` return. Reject an `ast.Name` in `ast.Load` context when its identifier is in `_FORBIDDEN_REFLECTION_NAMES`, when it is a dunder outside `_ALLOWED_DUNDER_NAME_LOADS`, or when it is `type` outside the permitted node set; apply the unified semantic binding check above; reject every dunder `ast.Attribute`; reject an `ast.Attribute` whose `_call_name(...)` is in `_FORBIDDEN_REFLECTION_HELPERS`; and reject an exact string constant in `_FORBIDDEN_DYNAMIC_PROTOCOL_LITERALS`. Reject every `ast.Import` whose imported module is `types`, including aliased imports; for `ImportFrom(module="types")`, require every original imported name to equal `MappingProxyType`, regardless of local alias, so a mixed import also fails. Every `Import`/`ImportFrom` is also subject to the dunder original/effective-name check before these module-specific rules.

Reject any `ast.Attribute` whose member is in `_FORBIDDEN_STDLIB_CLASS_FACTORIES`, regardless of receiver; this deliberate fail-closed member-name rule means a module alias cannot hide the source token. For `ImportFrom` nodes rooted at `dataclasses`, `collections`, or `typing`, reject aliases whose original imported name is in that set. Reject wildcard `ImportFrom` aliases from `types`, `dataclasses`, `collections`, or `typing`. `dataclasses.dataclass` and the currently imported nonfactory typing/collections names remain allowed. Do not evaluate Python, fold arbitrary expressions, import a module, or follow the value after the forbidden reference.

Integrate it in three places:

1. `scan_capabilities` accumulates existing and dynamic-reflection findings in a set of full `path.name:suffix` strings and returns one deterministic sorted list. Overlap with legacy `eval`, `exec`, or `__import__` checks produces one result, not duplicates.
2. `_entrypoint_violations` adds `builtin_reflection` whenever the entry-point tree contains a dynamic-reflection violation. It continues the existing checks, but reflective mutations are not required to produce structural tags. Direct and ordinary non-reflective aliases remain subject to mount/router/monkeypatch/server counts.
3. `_guard_helper_violations` performs a fail-closed candidate pre-pass before `if not all_guard_calls: continue`. `_sensitive_reflection_in_helper` uses bounded fixed-point sets. Sensitive-root and direct forbidden-builtin aliases still use `_bounded_aliases`. A second fixed point seeds the mapping name `__builtins__`, propagates only exact ordinary `Name = Name` assignments, marks any callable obtained from a tracked mapping through `mapping[...]` or `mapping.get(...)`, and propagates further exact ordinary callable aliases. A nonliteral mapping key fails closed when that callable is applied to a sensitive root. It does not follow defaults, returns, other containers, control flow, or arbitrary expressions. The helper returns true only when a reflective builtin/attribute/helper or tracked mapping-derived callable acts on one of the resolved sensitive roots. A literal member string without a sensitive receiver is insufficient. A nonliteral member on a sensitive receiver fails. The accepted unrelated receiver mutations are mandatory regression coverage.

- [ ] **Step 7: Run GREEN and mutation coverage**

Run:

```powershell
.venv-space\Scripts\python.exe -m pytest -q `
  tests/test_hf_space_source_boundary.py::test_application_forbidden_reflection_name_load_is_denied `
  tests/test_hf_space_source_boundary.py::test_application_implicit_builtins_mapping_is_denied `
  tests/test_hf_space_source_boundary.py::test_application_forbidden_reflective_attribute_load_is_denied `
  tests/test_hf_space_source_boundary.py::test_application_dynamic_protocol_definitions_are_denied `
  tests/test_hf_space_source_boundary.py::test_application_dunder_assignment_and_dynamic_class_construction_are_denied `
  tests/test_hf_space_source_boundary.py::test_entrypoint_scanner_rejects_reflection_without_resolving_forbidden_flow `
  tests/test_hf_space_source_boundary.py::test_guard_helper_audit_rejects_sensitive_reflection_candidates `
  tests/test_hf_space_source_boundary.py::test_guard_helper_audit_allows_unrelated_test_introspection `
  tests/test_hf_space_source_boundary.py::test_application_syntax_identities_are_not_reflection
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_source_boundary.py space/tests/test_export_contract.py -q
$env:PYTHONPATH = (Resolve-Path space).Path
.venv-space\Scripts\python.exe -m pytest space/tests/test_gradio_contract.py -q
```

Expected: all new reflection mutations pass; the complete Task 6 boundary suite passes; the Gradio contract resolves the isolated public package through the same exact `PYTHONPATH=space` environment used throughout the governing HF Space plan and remains green with only an already documented platform-capability skip if Windows cannot create the required symlink fixture. Missing `carerisk_space` without that environment is a plan-command defect, not permission to modify or install the frozen product package.

- [ ] **Step 8: Run static and immutable-scope verification**

Run:

```powershell
.venv-space\Scripts\python.exe -m ruff check tests/test_hf_space_source_boundary.py
.venv-space\Scripts\python.exe -m ruff format --check tests/test_hf_space_source_boundary.py
.venv-space\Scripts\python.exe -m mypy --strict tests/test_hf_space_source_boundary.py
git diff --check
git diff --name-only
git diff --exit-code -- space/app.py space/carerisk_space space/tests/test_gradio_contract.py
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

- [ ] **Step 10: Independent acceptance and old-breaker release (controller only)**

The SDD controller generates a review package from the exact recorded implementation BASE to the implementation HEAD and dispatches an independent reviewer. Acceptance requires Spec ✅, Quality Approved, Critical `0`, Important `0`; Minor findings are recorded under the standard SDD policy. The controller then reruns the nine exact node IDs, the complete Task 6 boundary suite, Gradio contract, Ruff, strict Mypy, immutable-scope diff, commit identity, and clean-worktree checks.

Only after both gates pass, resolve `corrective_head` from `git rev-parse HEAD`, then append these state transitions to the original plan's ignored ledger `.superpowers/sdd/2026-08-31-carerisk-hf-space/progress.md` using that full SHA in both named positions and the actual evidence counts:

```text
Task 6: architecture corrective accepted — reflection-free policy implemented under distinct plan docs/superpowers/plans/2026-09-01-carerisk-reflection-boundary-corrective.md; independent review clean; controller verification clean.
Task 6: complete (commits 3ef0963..corrective_head, five-round breaker resolved by separately approved architecture corrective; review clean).
Task 7: released — Tasks 7–13 may resume from corrective_head; remote Hugging Face/GitHub operations remain out of scope.
```

`corrective_head` above names the resolved controller variable; the literal word is never written to the ledger. Append the matching `Task 1: complete` line to the exact corrective ledger `.superpowers/sdd/2026-09-01-carerisk-reflection-boundary-corrective/progress.md`. If review or controller verification fails, append a `Task 1: BLOCKED` line naming the exact reviewer or command finding only to that corrective ledger and do not release Task 7.
