# CareRisk Closed-World Source Scanner Fix Round 2

> **For agentic workers:** REQUIRED SUB-SKILL: use `subagent-driven-development`; implement this one task with strict RED/GREEN and independent review.

**Goal:** Close the protected re-export, loader-object, full monkeypatch-call, and exact-parent escapes found by fresh review of fix-round-1 candidate `28e8ce88c8a6248516bf36d7bcbd624f0af8d24e`.

**Architecture:** Remain source-token and exact-node based. Add receiver-independent protected attribute denial and complete canonical parent contracts. Do not add alias/value-flow/fixed-point evaluation.

**Breaker:** This is the final bounded candidate for this closed-world architecture. Candidate sequence is `84e2eaa...`, `28e8ce8...`, then this round. If fresh review finds any Critical or Important issue, stop for architecture review; no fix round 3 is authorized.

**Scope:** Modify only `tests/test_hf_space_source_boundary.py`. The Gradio contract file, application/product source, evidence, locks, dependencies, Docker, private custody paths, and all remote state are frozen.

---

### Task 1: Close exact capability-transfer contexts

**Files:**

- Modify: `tests/test_hf_space_source_boundary.py`
- Report only: `.superpowers/sdd/2026-09-01-carerisk-test-source-closed-world-fix-round-2/task-1-report.md`

- [ ] **Step 1: Verify BASE and rejected-candidate evidence**

Controller supplies an exact clean BASE on `docs/carerisk-hf-space-design`, exact remote `https://github.com/kuotunyu/CareRisk-48H.git`. Verify `28e8ce88...` is an ancestor, its single-file scope/Gradio/product freeze remains intact, and worktree is clean.

- [ ] **Step 2: Add exact 50-case RED matrix**

Add four stable parameterized nodes, each appending mutations to the complete current Gradio source and requiring the stated new category tag in both source and helper findings:

1. `test_gradio_contract_protected_reexports_are_denied` — 8 rows, tag `protected_attr:<name>`;
2. `test_gradio_contract_loader_object_context_is_exact` — 10 rows, tag `loader:context`;
3. `test_gradio_contract_setattr_calls_are_canonical` — 26 rows, tag `monkeypatch:canonical`;
4. `test_gradio_contract_reflection_parents_are_exact` — 6 rows, tag `exact_parent:<member>`.

Protected re-export rows include `ui_module.gr`, `entrypoint.gr`, captured `entrypoint.uvicorn`, `ui_module.Path`, `evidence_module.Path`, and equivalent `inspect`/`importlib`/`sys` re-exports. Preserve only the exact `entrypoint.uvicorn` node in the canonical `run` monkeypatch call.

Loader rows include `loader_alias = spec.loader`, `get_code`, `get_data`, `create_module`, extra `exec_module`, altered/moved assertion, reordered statements, captured `spec`, and another `spec.loader` use. Setattr rows mutate the third argument of each one of the 26 committed calls while preserving target/member, including `render_scenario -> os.system` and both helper-internal calls. Exact-parent rows include signature-result capture, `.return_annotation`, altered Parameter.empty parent, `super` nested under `if False`, `try`, and a non-first statement.

Run exactly these four nodes against rejected candidate behavior before implementation: expected 50 collected and 50 failed because the new category tags are absent. After implementation the same exact nodes must collect 50 and pass 50. Unrelated findings do not satisfy the tests.

- [ ] **Step 3: Deny protected re-export attributes**

Create a receiver-independent protected attribute set: `inspect`, `importlib`, `socket`, `sys`, `pytest`, `ui_module`, `gr`, `uvicorn`, `Path`, `SPACE_ROOT`, and `AppEntryMarker`. Reject every Attribute with one of these names before exceptions.

Construct exactly one allowed node: `entrypoint.uvicorn` as argument 0 of the exact canonical `monkeypatch.setattr(entrypoint.uvicorn, "run", fake_run)` call in the exact entrypoint owner. The whole call must also be one of the 26 canonical calls. No other receiver or parent context is allowed.

- [ ] **Step 4: Freeze the spec/loader chain**

In the exact entrypoint owner, require one ordered direct-body sequence:

```python
spec = importlib.util.spec_from_file_location(
    "carerisk_space_entrypoint", SPACE_ROOT / "app.py"
)
assert spec is not None and spec.loader is not None
entrypoint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entrypoint)
```

Compare complete canonical AST statements and require direct body adjacency/order. Construct allowed `spec` Name and `spec.loader` Attribute node sets only from those four statements; reject every other load/capture/member. Add receiver-independent forbidden loader members `get_code`, `get_data`, `create_module`, and any `exec_module` outside the exact node.

- [ ] **Step 5: Freeze complete monkeypatch and reflection parents**

Store a static canonical multiset of the complete AST dumps of all 26 current `monkeypatch.setattr` Call nodes. It must be authored from the committed positive source and then treated as a literal contract; do not derive the expected set from the candidate input. Require exact count, multiplicity, owner, direct callee, all positional arguments including replacement, and zero keywords. The existing exact `setenv` rule is unchanged.

Require these complete parents:

- the exact direct assignment `parameters = inspect.signature(ui_module.PublicSurfaceGuard).parameters` in `test_outer_guard_constructor_is_exact_and_rejects_empty_membership`;
- the exact direct Assert containing `inspect.Parameter.empty` in that same function;
- the exact `super().__init__(level=logging.DEBUG)` Expr as body index 0 of the sole exact `BoundedLogCapture.__init__` FunctionDef.

Allowed inspect/guard/super nodes must be descendants of these complete parents and no other matching subtree is accepted.

- [ ] **Step 6: Run GREEN and full gates**

Run the four new nodes (50/50), the previous four fix-round-1 nodes (81/81), the existing closed-world/source/helper nodes, full boundary/export, and the frozen Gradio suite. Then run Ruff check/format and strict Mypy on the boundary file plus scope/frozen/diff/identity gates.

```powershell
.venv-space\Scripts\python.exe -m pytest -q `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_protected_reexports_are_denied `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_loader_object_context_is_exact `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_setattr_calls_are_canonical `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_reflection_parents_are_exact `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_protected_identity_loads_are_exact `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_semantic_dunder_bindings_are_denied `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_monkeypatch_loads_are_exact `
  tests/test_hf_space_source_boundary.py::test_gradio_contract_sys_platform_contexts_are_exact
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

Expected: all pass except documented platform skips; only the boundary test is modified; Gradio/product source is byte-identical to `28e8ce88...`.

- [ ] **Step 7: Commit, fresh review, and breaker decision**

Stage exactly the boundary test and commit `test(space): freeze capability transfer contexts` using `kuotunyu <61350295+kuotunyu@users.noreply.github.com>`. No push/deploy/remote operation.

Dispatch a fresh independent reviewer with exact BASE-to-HEAD diff and all prior repros. Acceptance requires Spec ✅, Quality Approved, Critical=0, Important=0, followed by controller full rerun. Otherwise record the third failed candidate and invoke the architecture breaker; do not implement a fix round 3. Original HF Space Task 7 remains blocked until acceptance.
