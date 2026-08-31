"""Static evidence presentation and the closed public ASGI surface."""

from __future__ import annotations

import logging
import re
from html import escape
from pathlib import Path
from types import MappingProxyType
from typing import Final, cast

import gradio as gr
from gradio.routes import (  # type: ignore[attr-defined]
    BUILD_PATH_LIB,
    STATIC_PATH_LIB,
)
from starlette.types import ASGIApp, Receive, Scope, Send

from .contracts import (
    PRIMARY_CLAIM_ZH_TW,
    PRODUCT_NAME,
    SAFETY_SUBTITLE_EN,
    EvidenceFailure,
    EvidenceViewModel,
    MetricInterval,
)
from .evidence import RECEIPT_GIT_BLOB_SHA, RECEIPT_SHA256, load_evidence
from .scenarios import SCENARIOS, render_scenario

LOGGER = logging.getLogger(__name__)

THEME_CSS_SHA256: Final = "8ad6f9b14414574fe6c6d9b4362dcdd63dfdc66d8c34cbef0982888dfc44ff04"
THEME_QUERY: Final = b"v=" + THEME_CSS_SHA256.encode("ascii")
_ASSET_SUFFIXES: Final = frozenset({".css", ".js", ".svg", ".ttf", ".wasm", ".woff", ".woff2"})
_ASSET_SEGMENT = re.compile(r"[A-Za-z0-9_][A-Za-z0-9._@+~-]*")

Authority = tuple[str, tuple[str, int], tuple[str, int]]
AUTHORITY_MAP = MappingProxyType(
    {
        b"127.0.0.1:7860": ("http", ("127.0.0.1", 7860), ("127.0.0.1", 0)),
        b"localhost:7860": ("http", ("localhost", 7860), ("127.0.0.1", 0)),
        b"carerisk-app:7860": ("http", ("carerisk-app", 7860), ("127.0.0.1", 0)),
        b"steven0226-carerisk-48h.hf.space": (
            "https",
            ("steven0226-carerisk-48h.hf.space", 443),
            ("127.0.0.1", 0),
        ),
    }
)

_NOT_FOUND_HEADERS: Final = [
    (b"content-type", b"text/plain; charset=utf-8"),
    (b"content-length", b"9"),
]

APP_CSS = """
:root { --ink:#14273a; --muted:#536878; --paper:#f4f0e7; --sheet:#fffdf8;
  --line:#c8d3d3; --teal:#0d6f6b; --teal-soft:#dceceb; --amber:#9a6426; }
html,body { box-sizing:border-box!important; margin:0!important; max-width:100%!important;
  min-width:0!important; width:100%!important; }
body,.gradio-container { background:var(--paper)!important; color:var(--ink)!important;
  font-family:Georgia,"Noto Serif TC","Microsoft JhengHei",serif!important;
  font-size:17px!important; }
.gradio-container { box-sizing:border-box!important; margin:0 auto!important;
  max-width:100%!important; min-width:0!important; padding:0!important;
  width:min(1120px,100%)!important; }
.gradio-container * { box-sizing:border-box!important; min-width:0!important; }
.gradio-container>* { max-width:100%!important; }
.gradio-container main { box-sizing:border-box!important; margin-inline:0!important;
  max-width:100%!important; min-width:0!important; width:100%!important; }
#carerisk-space-root { background:var(--sheet); border:1px solid var(--line);
  border-top:7px solid var(--teal); box-shadow:0 20px 50px rgba(20,39,58,.08);
  box-sizing:border-box; max-width:100%; min-width:0; padding:clamp(20px,4vw,52px);
  width:100%; }
#carerisk-space-root *,#carerisk-space-root *::before,#carerisk-space-root *::after {
  box-sizing:border-box; min-width:0; }
#carerisk-space-root :where(p,legend,label,li,dt,dd,th,td,a,code,span,strong,em,div) {
  font-size:16px!important; }
#carerisk-space-root :where(h2,h3,h4,h5,h6) { font-size:20px!important; }
.masthead { display:grid; gap:8px; border-bottom:1px solid var(--line); padding-bottom:20px; }
.eyebrow { color:var(--teal); font:700 16px/1.4 ui-monospace,Consolas,monospace;
  letter-spacing:.14em; text-transform:uppercase; margin:0; }
.masthead h1 { font-size:clamp(31px,5vw,52px)!important; letter-spacing:-.035em;
  line-height:1.02; margin:0; }
.deck { color:var(--muted); font-size:18px; line-height:1.65; margin:0; max-width:790px; }
#claim-ceiling { background:var(--teal-soft); border-left:5px solid var(--teal);
  margin:24px 0; padding:17px 20px; }
#claim-ceiling p { line-height:1.7; margin:0; }
#claim-ceiling p+p { color:var(--muted); font:16px/1.7 ui-monospace,Consolas,monospace;
  margin-top:8px; }
#scenario-explorer,#receipt-evidence,#provenance { border-top:1px solid var(--line);
  margin-top:26px; padding-top:22px; }
#scenario-explorer fieldset { border:0; display:grid; gap:10px; margin:18px 0 0; padding:0; }
#scenario-explorer legend { font-weight:700; margin-bottom:10px; }
#scenario-explorer input[type=radio] { height:1px; opacity:.01; position:absolute; width:1px; }
#scenario-explorer label { align-items:center; border:1px solid var(--line); cursor:pointer;
  display:flex; min-height:44px; padding:8px 14px; }
#scenario-explorer input:focus-visible+label { outline:3px solid #f0a93b; outline-offset:2px; }
#scenario-explorer input:checked+label { background:var(--teal-soft); border-color:var(--teal); }
.scenario-panel { display:none; }
#synthetic_evidence_available:checked~#scenario-result [data-panel="synthetic_evidence_available"],
#synthetic_schema_withheld:checked~#scenario-result [data-panel="synthetic_schema_withheld"],
#synthetic_coverage_withheld:checked~#scenario-result [data-panel="synthetic_coverage_withheld"],
#synthetic_value_pattern_withheld:checked~#scenario-result
  [data-panel="synthetic_value_pattern_withheld"]
  { display:block; }
#scenario-result { min-height:160px; margin-top:12px; }
.scenario-state,.evidence-failure { border:1px solid var(--line); border-left:5px solid var(--teal);
  padding:18px 20px; }
.scenario-state h3 { font:700 16px/1.4 ui-monospace,Consolas,monospace;
  letter-spacing:.06em; text-transform:uppercase; }
.scenario-state ul { display:grid; gap:6px; list-style:none; padding:0; }
.scenario-state li { background:#eef3f1; font-family:ui-monospace,Consolas,monospace;
  padding:8px 10px; }
.evidence-ledger { border-collapse:collapse; table-layout:fixed; width:100%; }
.evidence-ledger th,.evidence-ledger td { border-bottom:1px solid var(--line); padding:12px 8px;
  overflow-wrap:anywhere; text-align:left; }
.receipt-facts { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1px;
  background:var(--line); }
.receipt-facts div { background:var(--sheet); padding:14px; }
.receipt-facts dd { font-weight:700; margin:5px 0 0; overflow-wrap:anywhere; }
.provenance-list { font:16px/1.6 ui-monospace,Consolas,monospace; overflow-wrap:anywhere; }
.provenance-links { display:flex; flex-wrap:wrap; gap:12px 20px; }
.provenance-links a { color:var(--teal); overflow-wrap:anywhere; text-underline-offset:3px; }
.evidence-failure { border-left-color:var(--amber); margin-top:24px; }
.evidence-failure code { background:#f3eadc; color:#6d431a; display:inline-block; padding:7px 9px; }
@media(max-width:620px) {
  #carerisk-space-root{padding:20px 16px}.receipt-facts{grid-template-columns:1fr}
  .evidence-ledger{font-size:16px}.evidence-ledger th,.evidence-ledger td{padding:10px 4px} }
"""


def render_claim_header() -> str:
    """Render the exact bilingual claim before any app-owned control or link."""

    return (
        '<header class="masthead">'
        '<p class="eyebrow">PUBLIC EVIDENCE LEDGER · SYNTHETIC ONLY</p>'
        f"<h1>{escape(PRODUCT_NAME)}</h1>"
        '<p class="deck">以可稽核的 aggregate receipt 與固定 synthetic states 展示 '
        "calibration、evidence gates 與 abstention。</p>"
        "</header>"
        '<section id="claim-ceiling" role="note">'
        f"<p>{escape(PRIMARY_CLAIM_ZH_TW)}</p>"
        f'<p lang="en">{escape(SAFETY_SUBTITLE_EN)}</p>'
        "</section>"
    )


def _metric_row(label: str, metric: MetricInterval) -> str:
    return (
        f'<tr><th scope="row">{escape(label)}</th><td>{metric.estimate:.3f}</td>'
        f"<td>{metric.lower:.3f}–{metric.upper:.3f}</td></tr>"
    )


def render_evidence(view: EvidenceViewModel) -> str:
    """Render only fields admitted by the validated evidence view model."""

    receipt = view.receipt
    release = view.release
    manifest = view.manifest
    metric_rows = "".join(
        _metric_row(label, receipt.metrics[name])
        for name, label in (
            ("auprc", "AUPRC"),
            ("auroc", "AUROC"),
            ("brier", "Brier · calibration"),
            ("ece", "ECE · calibration"),
        )
    )
    flags = "".join(
        f"<li>{escape(name)}={str(value).lower()}</li>"
        for name, value in release.scientific_change_flags.items()
    )
    limitations = "".join(f"<li>{escape(item)}</li>" for item in release.limitations)
    source_sha = escape(manifest.space_app_source_git_sha)
    return (
        '<section id="receipt-evidence"><h2>Receipt-backed aggregate evidence</h2>'
        '<dl class="receipt-facts">'
        f"<div><dt>Dataset</dt><dd>{escape(receipt.dataset_name)}</dd></div>"
        f"<div><dt>Role</dt><dd>{escape(receipt.dataset_role)}</dd></div>"
        f"<div><dt>Cohort</dt><dd>n={receipt.n}; events={receipt.events}; "
        f"prevalence={receipt.prevalence:.1%}</dd></div>"
        f"<div><dt>Bootstrap</dt><dd>{escape(receipt.bootstrap_method)} · "
        f"{receipt.bootstrap_samples} samples · seed {receipt.bootstrap_seed}</dd></div>"
        f"<div><dt>Evaluation</dt><dd>{escape(receipt.evaluation_status)} · "
        f"one-success count {receipt.success_count}</dd></div>"
        f"<div><dt>Final lock</dt><dd>{escape(receipt.final_lock_status)}</dd></div></dl>"
        '<table class="evidence-ledger"><thead><tr><th>Measure</th><th>Estimate</th>'
        f"<th>95% interval</th></tr></thead><tbody>{metric_rows}</tbody></table>"
        f'<p class="use-limitation">{escape(receipt.use_limitation)}</p></section>'
        '<section id="provenance"><h2>Provenance &amp; limitations</h2>'
        '<ul class="provenance-list">'
        f"<li>evidence tag: {escape(manifest.evidence_tag)} · commit "
        f"{escape(manifest.evidence_tag_commit)}</li>"
        f"<li>receipt git blob: {RECEIPT_GIT_BLOB_SHA}</li>"
        f"<li>receipt sha256: {RECEIPT_SHA256}</li>"
        f"<li>Space app source commit: {source_sha}</li>"
        f"<li>destination: {escape(manifest.destination_repository)}</li>{flags}</ul>"
        f'<ol class="limitations">{limitations}</ol>'
        '<nav class="provenance-links" aria-label="Evidence source links">'
        '<a href="https://github.com/kuotunyu/CareRisk-48H/tree/v0.2.0" '
        'target="_blank" rel="noopener noreferrer">GitHub tag v0.2.0</a>'
        f'<a href="https://github.com/kuotunyu/CareRisk-48H/tree/{source_sha}" '
        'target="_blank" rel="noopener noreferrer">Space app source</a>'
        '<a href="https://github.com/kuotunyu/CareRisk-48H/blob/v0.2.0/'
        'docs/final-result-receipt.json" target="_blank" rel="noopener noreferrer">'
        "Aggregate receipt</a>"
        '<a href="https://github.com/kuotunyu/CareRisk-48H/blob/v0.2.0/LICENSE" '
        'target="_blank" rel="noopener noreferrer">LICENSE</a>'
        '<a href="https://github.com/kuotunyu/CareRisk-48H/blob/v0.2.0/NOTICE" '
        'target="_blank" rel="noopener noreferrer">NOTICE</a></nav></section>'
    )


def render_evidence_failure(failure: EvidenceFailure) -> str:
    """Render one bounded failure reason and no partially parsed evidence."""

    return (
        '<section class="evidence-failure" aria-labelledby="evidence-unavailable">'
        '<h2 id="evidence-unavailable">Evidence unavailable</h2>'
        "<p>公開 evidence 未通過完整性驗證，因此本頁不顯示 metrics 或 synthetic gate states。</p>"
        '<p lang="en">Evidence integrity checks failed; metrics and scenarios are disabled.</p>'
        f"<code>{escape(failure.code)}</code></section>"
    )


def _render_static_explorer(view: EvidenceViewModel) -> str:
    controls: list[str] = []
    panels: list[str] = []
    for scenario in SCENARIOS:
        scenario_id = escape(scenario.id, quote=True)
        controls.append(
            f'<input type="radio" id="{scenario_id}" name="synthetic-gate-scenario" '
            f'value="{scenario_id}"><label for="{scenario_id}">'
            f"{escape(scenario.label_zh_tw)}</label>"
        )
        panels.append(
            f'<div class="scenario-panel" data-panel="{scenario_id}">'
            f"{render_scenario(scenario.id)}</div>"
        )
    return (
        f"<style>{APP_CSS}</style>"
        '<section id="carerisk-space-root" lang="zh-TW">'
        f"{render_claim_header()}"
        '<section id="scenario-explorer"><h2>Fixed synthetic gate-state explorer</h2>'
        "<p>選擇一個固定抽象情境，只檢視 evidence available / withheld 與原因；不產生分數。</p>"
        "<fieldset><legend>選擇固定 synthetic gate state</legend>"
        f"{''.join(controls)}"
        '<section id="scenario-result" aria-live="polite">'
        f"{''.join(panels)}</section></fieldset></section>"
        f"{render_evidence(view)}</section>"
    )


def _render_static_failure(failure: EvidenceFailure) -> str:
    return (
        f"<style>{APP_CSS}</style>"
        '<section id="carerisk-space-root" lang="zh-TW">'
        f"{render_claim_header()}{render_evidence_failure(failure)}</section>"
    )


def create_app(bundle_root: Path | None = None) -> gr.Blocks:
    """Construct one static normal or fail-closed document."""

    root = bundle_root if bundle_root is not None else Path(__file__).resolve().parents[1]
    evidence = load_evidence(root)
    if isinstance(evidence, EvidenceFailure):
        LOGGER.error("evidence_failure=%s", evidence.code)
        document = _render_static_failure(evidence)
    else:
        document = _render_static_explorer(evidence)
    with gr.Blocks(analytics_enabled=False, title=PRODUCT_NAME) as app:
        gr.HTML(document, elem_id="carerisk-static-document", js_on_load=None)
    app.dev_mode = False
    app.vibe_mode = False
    app.root_path = ""
    app.api_open = False
    app.space_id = None
    return app


def _canonical_asset_relative(relative: Path) -> str:
    parts = relative.parts
    if not parts or any(_ASSET_SEGMENT.fullmatch(part) is None for part in parts):
        raise ValueError("package_asset_path_invalid")
    value = relative.as_posix()
    if Path(value).suffix not in _ASSET_SUFFIXES:
        raise ValueError("package_asset_suffix_invalid")
    return value


def build_package_asset_membership() -> frozenset[str]:
    """Derive the immutable URL membership from the two pinned Gradio roots."""

    urls: set[str] = set()
    casefold_urls: dict[str, str] = {}
    for raw_root, prefix in (
        (BUILD_PATH_LIB, "/assets/"),
        (STATIC_PATH_LIB, "/static/"),
    ):
        root = Path(raw_root)
        if root.is_symlink():
            raise ValueError("package_asset_root_symlink")
        try:
            resolved_root = root.resolve(strict=True)
        except OSError as exc:
            raise ValueError("package_asset_root_invalid") from exc
        if not resolved_root.is_dir():
            raise ValueError("package_asset_root_invalid")
        for candidate in root.rglob("*"):
            if candidate.is_symlink():
                raise ValueError("package_asset_symlink")
            if candidate.is_dir():
                continue
            if not candidate.is_file():
                raise ValueError("package_asset_special_file")
            try:
                resolved = candidate.resolve(strict=True)
                relative = resolved.relative_to(resolved_root)
            except (OSError, ValueError) as exc:
                raise ValueError("package_asset_containment_invalid") from exc
            url = prefix + _canonical_asset_relative(relative)
            if url in urls:
                raise ValueError("package_asset_duplicate_url")
            folded_url = url.casefold()
            if folded_url in casefold_urls:
                raise ValueError("package_asset_case_alias")
            urls.add(url)
            casefold_urls[folded_url] = url
    if not urls:
        raise ValueError("package_asset_membership_empty")
    return frozenset(urls)


def _is_canonical_path(scope: Scope) -> bool:
    path = scope.get("path")
    raw_path = scope.get("raw_path")
    if not isinstance(path, str) or not isinstance(raw_path, bytes):
        return False
    try:
        encoded = path.encode("ascii")
    except UnicodeEncodeError:
        return False
    if raw_path != encoded or "%" in path or "\\" in path:
        return False
    if any(ord(character) < 32 or ord(character) == 127 for character in path):
        return False
    if not path.startswith("/") or (path != "/" and path.endswith("/")):
        return False
    if path != "/":
        parts = path[1:].split("/")
        if any(not part or part in {".", ".."} for part in parts):
            return False
    return True


def _allowed_request(
    method: object,
    path: object,
    query: object,
    package_asset_urls: frozenset[str],
) -> bool:
    if not isinstance(method, str) or not isinstance(path, str) or not isinstance(query, bytes):
        return False
    if path == "/":
        return method in {"GET", "HEAD"} and query == b""
    if path in {"/config", "/manifest.json", "/favicon.ico"}:
        return method == "GET" and query == b""
    if path == "/theme.css":
        return method == "GET" and query == THEME_QUERY
    return method == "GET" and query == b"" and path in package_asset_urls


def _selected_authority(headers: object) -> tuple[bytes, Authority] | None:
    if not isinstance(headers, list):
        return None
    typed_headers: list[tuple[bytes, bytes]] = []
    for header in headers:
        if (
            not isinstance(header, tuple)
            or len(header) != 2
            or not isinstance(header[0], bytes)
            or not isinstance(header[1], bytes)
        ):
            return None
        typed_headers.append(header)
    host_headers = [(name, value) for name, value in typed_headers if name.lower() == b"host"]
    if len(host_headers) != 1 or host_headers[0][0] != b"host":
        return None
    host = host_headers[0][1]
    selected = AUTHORITY_MAP.get(host)
    if selected is None:
        return None
    lowered_names = [name.lower() for name, _ in typed_headers]
    if b"transfer-encoding" in lowered_names:
        return None
    lengths = [value for (name, value) in typed_headers if name.lower() == b"content-length"]
    if len(lengths) > 1 or (lengths and lengths[0] != b"0"):
        return None
    return host, selected


async def _not_found(send: Send) -> None:
    await send({"type": "http.response.start", "status": 404, "headers": _NOT_FOUND_HEADERS.copy()})
    await send({"type": "http.response.body", "body": b"Not Found", "more_body": False})


class PublicSurfaceGuard:
    """Truly outer ASGI allowlist; blocked requests never reach body parsing."""

    def __init__(self, downstream: ASGIApp, package_asset_urls: frozenset[str]) -> None:
        if type(package_asset_urls) is not frozenset:
            raise ValueError("package_asset_membership_not_immutable")
        if not package_asset_urls:
            raise ValueError("package_asset_membership_empty")
        self.downstream = downstream
        self.package_asset_urls = package_asset_urls

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope_type = scope.get("type")
        if scope_type == "lifespan":
            await self.downstream(scope, receive, send)
            return
        if scope_type == "websocket":
            await send({"type": "websocket.close", "code": 1008, "reason": ""})
            return
        if scope_type != "http":
            return
        if not _is_canonical_path(scope) or not _allowed_request(
            scope.get("method"),
            scope.get("path"),
            scope.get("query_string"),
            self.package_asset_urls,
        ):
            await _not_found(send)
            return
        authority = _selected_authority(scope.get("headers"))
        if authority is None:
            await _not_found(send)
            return
        host, (scheme, server, client) = authority
        sanitized = cast(
            Scope,
            {
                "type": "http",
                "asgi": scope.get("asgi", {"version": "3.0", "spec_version": "2.3"}),
                "http_version": scope.get("http_version", "1.1"),
                "method": scope["method"],
                "scheme": scheme,
                "path": scope["path"],
                "raw_path": scope["raw_path"],
                "query_string": scope["query_string"],
                "root_path": "",
                "headers": [(b"host", host)],
                "server": server,
                "client": client,
            },
        )
        await self.downstream(sanitized, receive, send)
