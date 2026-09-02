# CareRisk Portfolio MVP Implementation Plan

> **Required sub-skill for the implementing agent:** use `subagent-driven-development` for the four bounded tasks below, `test-driven-development` for product changes, and `verification-before-completion` before any completion claim.

**Goal:** Publish a small, credible portfolio demo named **CareRisk 48H — Synthetic Evidence Explorer** at `https://huggingface.co/spaces/steven0226/carerisk-48h`, then use that URL as the GitHub repository Website.

**Architecture:** Build a new, independent `portfolio_mvp/` source root. A frozen in-memory registry renders one escaped HTML document through a single Gradio `HTML` component. Native radio controls and CSS switch among four pre-rendered teaching states; there are no app-owned callbacks, uploads, model calls, filesystem reads, or network calls. A small source-only builder copies an exact allowlist into a disposable Space candidate directory.

**Tech stack:** Python 3.11, Gradio 6.26.0, Python standard library, pytest, Playwright for one external browser smoke, Docker Space on port 7860.

**Governing design:** `docs/superpowers/specs/2026-09-02-carerisk-portfolio-mvp-scope-cut-design.md`

## Global constraints

- Do not modify, import, copy, read at runtime, export, or make claims from legacy `space/`, `tools/space/`, `scripts/export_hf_space.py`, Tasks 7–13 evidence, receipts, releases, SBOM, reviewer/browser inventory, data, models, artifacts, reports, Set B/C, or training/evaluation code.
- Do not delete or rewrite the legacy assurance history. It remains frozen and non-deployable.
- Product code may import only Gradio and the Python standard library. It may not read environment variables, inspect the filesystem, start subprocesses, call a shell, use a network client, load a model, or accept arbitrary user input.
- Visible content must not contain probability, score, risk class, threshold, recommendation, diagnosis, treatment, prognosis, patient-specific claims, clinical validation, metrics, model performance, or care actions.
- Use TDD: add the focused failing test first, run it and observe the expected failure, implement the minimum change, rerun it, then commit.
- Use at most one scoped review after each task and one final whole-MVP review. Do not restart the superseded assurance review loop.
- Do not push or mutate GitHub/Hugging Face until Tasks 1–3 and the local gates in Task 4 pass.

## Target tree

```text
portfolio_mvp/
├── app.py
├── carerisk_mvp/
│   ├── __init__.py
│   ├── content.py
│   └── ui.py
├── Dockerfile
├── LICENSE
├── NOTICE
├── README.md
├── requirements.txt
├── scripts/
│   ├── browser_smoke.py
│   └── build_space_candidate.py
└── tests/
    ├── test_bundle_contract.py
    ├── test_content.py
    └── test_ui_contract.py
```

The Space candidate contains only these nine paths:

```python
SPACE_PATHS = (
    "README.md",
    "LICENSE",
    "NOTICE",
    "Dockerfile",
    "requirements.txt",
    "app.py",
    "carerisk_mvp/__init__.py",
    "carerisk_mvp/content.py",
    "carerisk_mvp/ui.py",
)
```

## Task 1: Fixed synthetic content contract

**Files:**

- Create: `portfolio_mvp/carerisk_mvp/__init__.py`
- Create: `portfolio_mvp/carerisk_mvp/content.py`
- Create: `portfolio_mvp/tests/test_content.py`

- [ ] Write tests that define the content boundary before implementation.

`test_content.py` must prove:

1. `STATE_IDS` is exactly this ordered tuple:

   ```python
   (
       "evidence_available",
       "evidence_withheld",
       "schema_withheld",
       "provenance_withheld",
   )
   ```

2. `EVIDENCE_STATES` is an immutable tuple of four frozen `EvidenceState` objects, one per ID.
3. Every field is non-empty authored text; two independent reads are equal and return no mutable nested object.
4. The source contains no date, patient identifier, physiological measure, outcome label, imported value, URL, HTML, or free-form placeholder.
5. The combined rendered vocabulary rejects, case-insensitively, `patient`, `risk`, `score`, `probability`, `threshold`, `metric`, `model`, `diagnosis`, `treatment`, `prognosis`, `recommendation`, `clinical validation`, and their specified zh-TW counterparts.

- [ ] Run the new tests and confirm they fail because `carerisk_mvp.content` does not yet exist:

  ```powershell
  python -m pytest portfolio_mvp/tests/test_content.py -q
  ```

- [ ] Implement only this public interface:

  ```python
  @dataclass(frozen=True, slots=True)
  class EvidenceState:
      state_id: str
      label_zh: str
      label_en: str
      heading_zh: str
      body_zh: str
      process_note_zh: str

  STATE_IDS: tuple[str, ...]
  EVIDENCE_STATES: tuple[EvidenceState, ...]
  ```

  Content is fixed in the module. Do not generate random data and do not copy content or values from elsewhere in the repository.

- [ ] Run the focused tests and commit:

  ```powershell
  python -m pytest portfolio_mvp/tests/test_content.py -q
  git add portfolio_mvp/carerisk_mvp portfolio_mvp/tests/test_content.py
  git commit -m "feat(mvp): define synthetic evidence states"
  ```

## Task 2: Event-free Gradio UI

**Files:**

- Create: `portfolio_mvp/carerisk_mvp/ui.py`
- Create: `portfolio_mvp/app.py`
- Create: `portfolio_mvp/tests/test_ui_contract.py`

- [ ] Write failing UI contract tests for the exact safety and capability ceiling.

The tests must import the future API and assert:

- `SAFETY_ZH` equals `本頁僅使用固定合成資料作研究展示；不提供個案風險、診斷、治療或照護決策。`;
- `SAFETY_EN` equals `Synthetic research demonstration only — not for clinical or care decisions.`;
- `render_explorer_html()` produces one H1, declares `lang="zh-TW"`, places both safety strings before the first `<input`, renders exactly four labeled native radio controls, and HTML-escapes every registry value;
- the HTML contains no `script`, inline event attribute, form, upload, editable field, URL, external asset, or prohibited claim term;
- all four state panels exist in the initial HTML and are switched only by radio/CSS selectors;
- CSS includes visible `:focus-visible`, a 44px minimum control target, a single-column mobile rule, and overflow protection;
- `create_demo()` returns one Gradio Blocks tree with one app-authored HTML component and no registered app callback/dependency/API/queue;
- AST/source inspection rejects `os`, `pathlib`, `subprocess`, `socket`, `requests`, `httpx`, `urllib`, model/data packages, filesystem calls, environment access, and Gradio input/upload components.

- [ ] Observe the expected import failure:

  ```powershell
  python -m pytest portfolio_mvp/tests/test_ui_contract.py -q
  ```

- [ ] Implement these interfaces:

  ```python
  SAFETY_ZH: str
  SAFETY_EN: str
  def render_explorer_html() -> str: ...
  def render_unavailable_html() -> str: ...
  def create_demo() -> gr.Blocks: ...
  ```

  `render_explorer_html()` must use `html.escape(..., quote=True)` for registry text. `create_demo()` catches a fixed-registry construction failure and renders only the generic unavailable page; it does not expose exception text. Use `gr.Blocks(title=..., analytics_enabled=False)` and one `gr.HTML(...)`. Do not call `.click`, `.change`, `.select`, `.load`, `.queue`, or any event registration method.

  `app.py` exports `demo = create_demo()` and launches only under `if __name__ == "__main__"` with `server_name="0.0.0.0"`, `server_port=7860`, and `show_error=False`.

- [ ] Run Task 1–2 tests and commit:

  ```powershell
  python -m pytest portfolio_mvp/tests/test_content.py portfolio_mvp/tests/test_ui_contract.py -q
  git add portfolio_mvp/app.py portfolio_mvp/carerisk_mvp/ui.py portfolio_mvp/tests/test_ui_contract.py
  git commit -m "feat(mvp): add event-free evidence explorer"
  ```

## Task 3: Minimal Space bundle and fail-closed builder

**Files:**

- Create: `portfolio_mvp/requirements.txt`
- Create: `portfolio_mvp/Dockerfile`
- Create: `portfolio_mvp/README.md`
- Create: `portfolio_mvp/LICENSE`
- Create: `portfolio_mvp/NOTICE`
- Create: `portfolio_mvp/scripts/build_space_candidate.py`
- Create: `portfolio_mvp/tests/test_bundle_contract.py`

- [ ] Write failing bundle tests first.

The tests must prove:

- `requirements.txt` is exactly `gradio==6.26.0` plus a final newline;
- the Dockerfile starts from `python:3.11.14-slim-bookworm`, creates and switches to a non-root user, installs only `requirements.txt`, copies only the nine `SPACE_PATHS`, exposes `7860`, and uses exec-form `CMD ["python", "app.py"]`;
- the Dockerfile does not use `ADD`, wildcard copies, the repository root, a legacy path, model/data path, browser/reviewer stage, secret, or environment-driven application behavior;
- README front matter is exactly a Docker Space with `app_port: 7860` and `license: apache-2.0`, followed by the exact safety copy and synthetic-only boundary without unsupported assurance claims;
- `LICENSE` is the repository Apache-2.0 text;
- `NOTICE` states that the MVP includes no PhysioNet data, patient data, trained weights, model artifacts, or formal evaluation evidence;
- the builder exports only the nine exact `SPACE_PATHS` from a supplied `--source-root` to a new supplied `--destination`, using literal resolved paths and refusing a pre-existing destination;
- it rejects missing/non-regular files, symlinks, archives, binaries, VCS paths, secret-shaped names or content, model/weight extensions, real-data paths, browser/reviewer artifacts, legacy assurance names, and any extra candidate member;
- negative tests use temporary fixtures only and never inspect or copy the frozen legacy directories.

- [ ] Observe the expected failures:

  ```powershell
  python -m pytest portfolio_mvp/tests/test_bundle_contract.py -q
  ```

- [ ] Implement a source-only builder with this interface:

  ```python
  SPACE_PATHS: tuple[str, ...]
  class CandidateError(RuntimeError): ...
  def build_candidate(source_root: Path, destination: Path) -> tuple[Path, ...]: ...
  def audit_candidate(destination: Path) -> tuple[Path, ...]: ...
  def main(argv: Sequence[str] | None = None) -> int: ...
  ```

  The builder reads only the explicit nine source paths under the caller-supplied `portfolio_mvp` root. It must not traverse the repository and must never reference the old exporter. On error, remove only the destination that this invocation created, after confirming its resolved parent and run-owned marker.

- [ ] Build and audit a disposable candidate outside the repository, then remove it after recording the printed file list:

  ```powershell
  $candidate = Join-Path ([System.IO.Path]::GetTempPath()) ("carerisk-mvp-" + [guid]::NewGuid())
  python portfolio_mvp/scripts/build_space_candidate.py --source-root portfolio_mvp --destination $candidate
  Get-ChildItem -LiteralPath $candidate -Recurse -File | ForEach-Object { $_.FullName.Substring($candidate.Length + 1) }
  Remove-Item -LiteralPath $candidate -Recurse
  ```

- [ ] Run Tasks 1–3 tests and commit:

  ```powershell
  python -m pytest portfolio_mvp/tests -q
  git add portfolio_mvp
  git commit -m "feat(mvp): package minimal Docker Space"
  ```

## Task 4: Verify once, publish once

**Files:**

- Create: `portfolio_mvp/scripts/browser_smoke.py`
- Modify: `portfolio_mvp/tests/test_bundle_contract.py` only if needed for the smoke-script contract
- Remote: GitHub `kuotunyu/CareRisk-48H`
- Remote: Hugging Face Space `steven0226/carerisk-48h`

- [ ] Add a browser smoke script that accepts only `--url` and runs desktop `1440x900` and mobile `390x844` checks. It must fail on:

  - missing or late safety copy;
  - H1 count other than one;
  - horizontal overflow;
  - radio target below 44 CSS pixels;
  - keyboard selection/focus failure;
  - console error or page error;
  - any request outside the tested origin after initial navigation;
  - any POST, upload, Gradio call/queue/event request;
  - any prohibited claim text.

  The smoke is UI/privacy verification only. Do not describe it as scientific, clinical, or formal assurance evidence.

- [ ] Run the complete local source gates from a clean process:

  ```powershell
  python -m pytest portfolio_mvp/tests -q
  python -m compileall -q portfolio_mvp/app.py portfolio_mvp/carerisk_mvp portfolio_mvp/scripts
  git diff --check
  git status --short
  ```

- [ ] Start the local app on a task-owned process, run the smoke, and terminate only that exact process in `finally`:

  ```powershell
  python portfolio_mvp/scripts/browser_smoke.py --url http://127.0.0.1:7860
  ```

  The controlling implementation may use a bounded helper to start `portfolio_mvp/app.py`, capture its PID, wait for HTTP readiness, invoke the command above, and stop only that PID.

- [ ] Check Docker capability once with `docker version`. If healthy, build the exact `portfolio_mvp/` context, assert the configured user is non-root, run it on a task-owned port, smoke it, and stop only that container. If Docker is unhealthy, record `LOCAL_DOCKER_NOT_AVAILABLE` and continue without reset, factory reset, deletion, service mutation, or repeated repair attempts. The Hugging Face remote build and anonymous live smoke then govern runtime publication readiness.

- [ ] Perform one final whole-MVP review against the approved scope-cut spec. Resolve only Critical or Important findings within `portfolio_mvp/`, rerun the complete local gates once, and commit the browser smoke/final corrective if any:

  ```powershell
  git add portfolio_mvp/scripts/browser_smoke.py portfolio_mvp/tests/test_bundle_contract.py
  git commit -m "test(mvp): add browser privacy smoke"
  ```

- [ ] Confirm the working tree is clean, branch history contains only intended MVP/spec/plan work, GitHub authentication resolves to `kuotunyu`, the remote is exactly `https://github.com/kuotunyu/CareRisk-48H.git`, and the push is a fast-forward. Then push normally; never force-push.

- [ ] Build a fresh candidate into a new temporary directory. Before remote mutation, check Hugging Face authentication resolves to `steven0226` without printing a token. Perform an authenticated collision check for `steven0226/carerisk-48h`:

  - if absent, create a public Docker Space;
  - if present and owned by `steven0226`, update it from the exact nine-file candidate;
  - if the owner, visibility, SDK, or target is unexpected, stop without mutation.

  Upload only the candidate directory. Do not upload repository history, tests, scripts, receipts, models, data, `.env`, caches, or legacy content.

- [ ] Wait boundedly for the Space build to reach `RUNNING`. If it fails or times out, inspect only build/runtime logs needed to diagnose the MVP; do not broaden scope into old assurance work. Run the browser smoke anonymously against `https://steven0226-carerisk-48h.hf.space` and verify the public Space page is `https://huggingface.co/spaces/steven0226/carerisk-48h`.

- [ ] Only after the anonymous live smoke passes, set the GitHub About Website to the canonical Space page URL:

  ```powershell
  gh repo edit kuotunyu/CareRisk-48H --homepage "https://huggingface.co/spaces/steven0226/carerisk-48h"
  ```

  Verify the GitHub API returns the exact homepage URL and anonymously fetch both the repository and Space pages. Do not change tags, releases, Pages, topics, visibility, secrets, variables, or other repository metadata.

- [ ] Final evidence record in the task response must include: exact Git commit and remote head, test counts, browser-smoke result at both viewports, Docker capability outcome, exact nine uploaded paths, HF build/runtime state, anonymous URLs, GitHub homepage value, clean worktree, and any explicitly waived local-only gate. Do not claim the frozen assurance pipeline is complete or reused.

## Stop conditions

Stop without publication if any of these occurs: dirty unrelated worktree state; extra candidate path; symlink/binary/secret/model/data/legacy content; identity mismatch; unexpected existing Space owner/SDK/visibility; unsupported visible claim; external request or POST/event traffic; failed source test; failed live smoke; or non-fast-forward GitHub push. Report the exact blocker and preserve all existing remote state.
