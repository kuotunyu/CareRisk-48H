# CareRisk Closed-World Source Scanner Fix Round 1

> **For agentic workers:** REQUIRED SUB-SKILL: use `subagent-driven-development`; implement exactly one task with RED/GREEN, a report, and independent review.

**Goal:** Close the protected-load, semantic-dunder, monkeypatch-alias, and `sys.platform` escapes found by fresh review of candidate `84e2eaa508ac37f9b4d533efffc2da79c8ca1099` without reviving value-flow evaluation.

**Architecture:** Keep the whole-file source-token scanner. Add finite allowed-node sets for protected identity loads, reuse the complete semantic dunder-binding audit, and make mutation/loader members fail closed before exact current exceptions. No alias resolution or fixed-point state is permitted.

**Scope:** Modify only `tests/test_hf_space_source_boundary.py`; do not change the committed Gradio cleanup, product source, evidence, locks, Docker, dependencies, private custody paths, or remote state.

## Governing evidence

- Candidate parent: `6871dfc6ac69d4a0591f52a0a4dc96fadf3e5a77`.
- Rejected candidate: `84e2eaa508ac37f9b4d533efffc2da79c8ca1099`.
- Independent review: Spec ❌, Quality Not Approved; Critical=2, Important=2, Minor=0.
- Fresh controller reproduction appended each escape to the complete current Gradio source and obtained empty findings from both `_gradio_test_source_violations` and `_guard_helper_violations`.
- Existing application scanner and product source are accepted and frozen.

---

### Task 1: Close review escapes with exact source-node gates

**Files:**

- Modify: `tests/test_hf_space_source_boundary.py`
- Report only: `.superpowers/sdd/2026-09-01-carerisk-test-source-closed-world-fix-round-1/task-1-report.md`

- [ ] **Step 1: Verify exact BASE and scope**

Controller supplies the exact clean docs-corrected BASE on branch `docs/carerisk-hf-space-design`, remote `https://github.com/kuotunyu/CareRisk-48H.git`. Verify candidate `84e2eaa...` is an ancestor, the committed Gradio blob equals candidate, product diff from candidate is empty, and worktree is clean. Stop on mismatch.

- [ ] **Step 2: Add RED mutations for every review finding**

Append each mutation to the complete current Gradio source; do not use incomplete synthetic modules as positives. Require a nonempty source finding and helper finding for:

```python
inspection = inspect
inspection.signature(ui_module.PublicSurfaceGuard)

inspect.signature(ui_module.create_app)

api = importlib
api.import_module("evil")

runner = uvicorn
config = runner.Config("carerisk_space.ui:Public" + "SurfaceGuard")
config.load()

mp = monkeypatch
mp.setitem(mapping, "x", 1)

env_setter = monkeypatch.setenv

sys.platform = "evil"
```

Add direct and aliased variants for extra `importlib.util.spec_from_file_location(...)`, captured/extra `module_from_spec`, extra `exec_module`, `load_module`, extra `gr.mount_gradio_app`, `gr` alias, extra/aliased `uvicorn.Config` and `Server`, `socket` alias, `super` alias, `ui_module` bare capture, `isinstance` capture, and `frozenset` capture.

Add semantic dunder mutations covering:

- function/async-function/class names;
- positional-only, normal, keyword-only, vararg, and kwarg parameters;
- assignment/delete/for/comprehension/with/walrus targets;
- import original/effective aliases;
- exception targets, `MatchAs`, `MatchStar`, `MatchMapping.rest`, global, and nonlocal;
- allowed positive class-owned `__init__` and `__call__` definitions.

For `monkeypatch.setattr`, add all dunder member strings including `__class__`, `__dict__`, `__globals__`, `__getitem__`, and `__call__`. Add method-reference, direct alias, two-level alias, alternate receiver, `setitem`, `delattr`, and extra `setenv` mutations. Add `sys.platform` Load/Store/Del/alias mutations while retaining the two exact positive contexts.

Run the new review-regression node IDs and record RED counts. The rejected candidate must fail the new mutations before implementation changes.

- [ ] **Step 3: Implement finite protected-load sets**

Build exact allowed `ast.Name(ctx=Load)` node sets. Do not collect arbitrary input occurrences as allowed and do not resolve aliases.

Required categories:

1. `getattr` and `type`: retain their existing exact-call recognizers and cardinalities; every other load fails.
2. `super`: allow only the existing exact zero-argument call inside `BoundedLogCapture.__init__`; reject every other load.
3. `inspect`: allow only the Name roots of exact `inspect.signature(ui_module.PublicSurfaceGuard)` and exact `inspect.Parameter.empty`; reject extra direct calls and captures.
4. `importlib`: allow only the Name roots of the one exact `spec_from_file_location` and one exact `module_from_spec` chain in the entrypoint test. Allow the single `exec_module` attribute only in its exact reviewed call. Reject every other load/member/call.
5. `uvicorn`: allow only exact `uvicorn.Config(marker, complete pinned kwargs)` and `uvicorn.Server(config)` Name roots. The entrypoint patch uses `entrypoint.uvicorn` and remains governed by its separate exact exception. Reject aliases, extra loads, and string/path app targets.
6. `gr`: allow only current direct `gr.Blocks` annotation nodes, the one `_compose` mount call, exact version comparison, and the one exact monkeypatch target. Require current cardinalities and reject aliases/extra mounts.
7. `socket`: allow only two direct `create_connection` calls, one `socket.socket` constructor, one `SOCK_STREAM` read, and the exact AF_UNIX `getattr` receiver; reject aliases and extras.
8. `sys`: allow exactly the reviewed platform comparison Name root and exact monkeypatch target Name root. Reject all other loads; reject `platform` Attribute Store/Del receiver-independently.
9. `pytest`: retain existing exact decorator/call/annotation receiver contexts and reject every other load.
10. `ui_module`: permit a load only as the immediate receiver of an `ast.Attribute` or the exact first argument of an already approved direct `monkeypatch.setattr` node; bare capture fails. Sensitive guard/builder attribute contexts remain independently exact.
11. `monkeypatch`: permit a load only as the immediate receiver Name of an approved exact direct `monkeypatch.setattr(...)` call or the sole exact `setenv` call. A method reference, assignment, alias source, alternate receiver, or unapproved method fails.
12. `isinstance`: permit only direct call-callee loads. `frozenset`: permit only direct call-callee loads, exact type-annotation subscripts, or the exact second type operand of a direct `isinstance` call. Never permit bare capture or reassignment.

Add receiver-independent forbidden loader member tokens `import_module`, `load_module`, and `load`. Treat `spec_from_file_location`, `module_from_spec`, `exec_module`, `signature`, `Parameter`, `empty`, `Config`, `Server`, and `mount_gradio_app` as protected members permitted only in their exact allowed nodes.

- [ ] **Step 4: Apply complete semantic dunder and mutation denial**

Call the existing `_semantic_dunder_bindings(tree, parents, permitted_all_target=None)` from the Gradio scanner and append deterministic findings. Preserve only its existing class-owned `__init__`/`__call__` definition exceptions. Keep the separate dunder Attribute/Name-load checks.

For every `monkeypatch.setattr` literal member, reject `_is_dunder(member)` before any protected-member exception. No current dunder mutation is allowed. Preserve exact ordinary current monkeypatch calls.

Return sorted deduplicated findings. `_guard_helper_violations` must continue to prepend the whole-file source findings, so every new source mutation yields both source and helper failure without separate alias logic.

- [ ] **Step 5: Run GREEN and complete verification**

Run:

```powershell
.venv-space\Scripts\python.exe -m pytest -q `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_source_is_closed_world_reflection_free `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_source_rejects_reflection_near_misses `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_sensitive_members_have_exact_contexts `
  tests/test_hf_space_source_boundary.py::test_guard_helper_audit_rejects_sensitive_reflection_candidates
.venv-space\Scripts\python.exe -m pytest tests/test_hf_space_source_boundary.py space/tests/test_export_contract.py -q
$env:PYTHONPATH = (Resolve-Path space).Path
.venv-space\Scripts\python.exe -m pytest space/tests/test_gradio_contract.py -q
.venv-space\Scripts\python.exe -m ruff check tests/test_hf_space_source_boundary.py
.venv-space\Scripts\python.exe -m ruff format --check tests/test_hf_space_source_boundary.py
.venv-space\Scripts\python.exe -m mypy --strict tests/test_hf_space_source_boundary.py
git diff --check
git diff --name-only
git diff --exit-code -- space/tests/test_gradio_contract.py space/app.py space/carerisk_space
```

Expected: all tests/static checks pass with only documented platform skips; the sole modified tracked file is the boundary test; Gradio cleanup and product source are byte-identical to rejected candidate.

- [ ] **Step 6: Commit and review**

Stage exactly `tests/test_hf_space_source_boundary.py` and commit `test(space): close protected source loads` with `kuotunyu <61350295+kuotunyu@users.noreply.github.com>`. No co-author, push, deployment, or remote operation.

Generate an exact BASE-to-HEAD review package and dispatch a fresh independent reviewer. Acceptance requires Spec ✅, Quality Approved, Critical=0, Important=0, followed by controller rerun of every gate. Original HF Space Task 7 remains blocked until acceptance and ledger release.
