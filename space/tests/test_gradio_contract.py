from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import inspect
import io
import json
import logging
import os
import re
import socket
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast, get_args

import carerisk_space.evidence as evidence_module
import carerisk_space.ui as ui_module
import gradio as gr
import httpx
import pytest
import uvicorn
from carerisk_space.contracts import PRODUCT_NAME, EvidenceFailureCode, EvidenceViewModel
from carerisk_space.evidence import load_evidence
from carerisk_space.scenarios import SCENARIOS, render_scenario
from fastapi import FastAPI
from gradio.routes import BUILD_PATH_LIB, STATIC_PATH_LIB
from test_claim_contract import EXPECTED_EN, EXPECTED_ZH_TW
from test_evidence_contract import receipt_raw, release_raw, valid_manifest_bytes
from test_scenario_contract import EXPECTED_IDS

ALL_FAILURE_CODES = cast(tuple[EvidenceFailureCode, ...], get_args(EvidenceFailureCode))
SPACE_ROOT = Path(__file__).resolve().parents[1]
THEME_CSS_SHA256 = "8ad6f9b14414574fe6c6d9b4362dcdd63dfdc66d8c34cbef0982888dfc44ff04"
THEME_QUERY = f"v={THEME_CSS_SHA256}"
FAVICON_SHA256 = "3d131bff3fe15bcbb3e6e6552a8bee25377c3666723a9cbe68ceca953ea613df"
MANIFEST_LOGO_SHA256 = "89fd7687072f6c1ab52be3348494f0410c270f453e8306105719b2e3f7091469"


def _write_valid_bundle(bundle: Path) -> Path:
    evidence_dir = bundle / "evidence"
    evidence_dir.mkdir(parents=True)
    receipt = receipt_raw()
    release = release_raw()
    (evidence_dir / "final-result-receipt.json").write_bytes(receipt)
    (evidence_dir / "release-v0.2.0.json").write_bytes(release)
    (bundle / "deployment-manifest.json").write_bytes(valid_manifest_bytes(receipt, release))
    return bundle


@pytest.fixture(scope="module")
def valid_bundle(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _write_valid_bundle(tmp_path_factory.mktemp("valid-bundle"))


def make_unit_failure_bundle(
    tmp_path: Path, code: EvidenceFailureCode, monkeypatch: pytest.MonkeyPatch
) -> Path:
    bundle = _write_valid_bundle(tmp_path / code)
    receipt_path = bundle / "evidence" / "final-result-receipt.json"
    release_path = bundle / "evidence" / "release-v0.2.0.json"
    manifest_path = bundle / "deployment-manifest.json"
    if code == "receipt_missing":
        receipt_path.unlink()
    elif code == "receipt_hash_mismatch":
        receipt_path.write_bytes(receipt_path.read_bytes() + b"\n")
    elif code == "receipt_schema_invalid":
        raw = receipt_path.read_bytes().replace(b'"schema_version": 1,', b'"schema_version": 2,', 1)
        receipt_path.write_bytes(raw)
        monkeypatch.setattr(evidence_module, "RECEIPT_SHA256", hashlib.sha256(raw).hexdigest())
        monkeypatch.setattr(
            evidence_module, "RECEIPT_GIT_BLOB_SHA", evidence_module.git_blob_sha1(raw)
        )
    elif code == "release_relationship_invalid":
        release = json.loads(release_path.read_bytes())
        release["scientific_evidence"]["set_b_rerun"] = True
        release_path.write_text(json.dumps(release), encoding="utf-8")
    else:
        manifest = json.loads(manifest_path.read_bytes())
        manifest["destination_repository"] = "invalid/repository"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return bundle


@pytest.fixture
def manifest_canary_bundle(tmp_path: Path) -> Path:
    bundle = _write_valid_bundle(tmp_path / "manifest-canary")
    path = bundle / "deployment-manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest["destination_repository"] = {"secret": "CANARY_7419"}
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return bundle


@pytest.fixture
def captured_app_logs() -> Iterator[Callable[[], str]]:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger("carerisk_space.ui")
    old_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        yield stream.getvalue
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)


def _only_document(app: gr.Blocks) -> str:
    html_components = [
        item for item in app.get_config_file()["components"] if item["type"] == "html"
    ]
    assert len(html_components) == 1
    return cast(str, html_components[0]["props"]["value"])


def _compose(demo: gr.Blocks) -> Any:
    parent = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    gr.mount_gradio_app(
        parent,
        demo,
        path="/",
        server_name="0.0.0.0",
        server_port=7860,
        footer_links=[],
        run_history=False,
        root_path="",
        allowed_paths=["/__carerisk_no_allowed_files__"],
        blocked_paths=["/"],
        favicon_path=None,
        show_error=False,
        max_file_size=0,
        ssr_mode=False,
        enable_monitoring=False,
        pwa=False,
        mcp_server=False,
    )
    return ui_module.PublicSurfaceGuard(parent, ui_module.build_package_asset_membership())


def _scope(
    method: str,
    path: str,
    *,
    query: bytes = b"",
    host: bytes = b"127.0.0.1:7860",
    headers: list[tuple[bytes, bytes]] | None = None,
    scope_type: str = "http",
) -> dict[str, Any]:
    return {
        "type": scope_type,
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii", errors="ignore"),
        "query_string": query,
        "headers": [(b"host", host)] if headers is None else headers,
        "client": ("CANARY_7419", 9999),
        "server": ("CANARY_7419", 9999),
        "root_path": "/CANARY_7419",
    }


def _run_asgi(app: Any, scope: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    messages: list[dict[str, Any]] = []
    receive_calls = 0

    async def receive() -> dict[str, Any]:
        nonlocal receive_calls
        receive_calls += 1
        raise AssertionError("guard read request body")

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    asyncio.run(app(scope, receive, send))
    return messages, receive_calls


class DownstreamRecorder:
    def __init__(self) -> None:
        self.calls = 0
        self.scope: dict[str, Any] | None = None

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        self.calls += 1
        self.scope = scope
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b"", "more_body": False})


def _status(messages: list[dict[str, Any]]) -> int:
    return cast(int, messages[0]["status"])


def _http_get(app: Any, path: str, *, headers: dict[str, str] | None = None) -> httpx.Response:
    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://127.0.0.1:7860",
            headers={"host": "127.0.0.1:7860"},
        ) as client:
            return await client.get(path, headers=headers)

    return asyncio.run(request())


@dataclass(frozen=True)
class RawResponse:
    status: int
    headers: dict[bytes, bytes]
    body: bytes
    raw: bytes


class AppEntryMarker:
    def __init__(self, downstream: Any) -> None:
        self.downstream = downstream
        self.calls = 0

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        self.calls += 1
        await self.downstream(scope, receive, send)


@dataclass(frozen=True)
class RunningWireApp:
    marker: AppEntryMarker

    def request(self, request_bytes: bytes) -> RawResponse:
        chunks: list[bytes] = []
        with socket.create_connection(("127.0.0.1", 7860), timeout=5) as connection:
            connection.sendall(request_bytes)
            connection.shutdown(socket.SHUT_WR)
            while True:
                chunk = connection.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
        raw = b"".join(chunks)
        head, _, body = raw.partition(b"\r\n\r\n")
        lines = head.split(b"\r\n")
        status = int(lines[0].split(b" ", 2)[1])
        headers = {
            name.lower(): value.strip()
            for line in lines[1:]
            for name, value in [line.split(b":", 1)]
        }
        return RawResponse(status, headers, body, raw)


@pytest.fixture(scope="module")
def running_wire_app(valid_bundle: Path) -> Iterator[RunningWireApp]:
    guarded = _compose(ui_module.create_app(valid_bundle))
    marker = AppEntryMarker(guarded)
    config = uvicorn.Config(
        marker,
        host="127.0.0.1",
        port=7860,
        workers=1,
        http="h11",
        proxy_headers=False,
        forwarded_allow_ips="",
        access_log=False,
        server_header=False,
        date_header=False,
        log_config=None,
        lifespan="on",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 15
    while not server.started and thread.is_alive() and time.monotonic() < deadline:
        time.sleep(0.02)
    if not server.started:
        server.should_exit = True
        thread.join(timeout=5)
        raise AssertionError("programmatic Uvicorn+h11 did not start")
    try:
        yield RunningWireApp(marker)
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        assert not thread.is_alive()


def test_gradio_version_and_normal_config_are_static_and_event_free(valid_bundle: Path) -> None:
    assert gr.__version__ == "6.26.0"
    app = ui_module.create_app(valid_bundle)
    config = app.get_config_file()
    assert [item["type"] for item in config["components"]] == ["html"]
    assert config["dependencies"] == []
    assert config["enable_queue"] is True
    assert len(app.fns) == 0
    assert app.get_api_info() == {"named_endpoints": {}, "unnamed_endpoints": {}}
    props = config["components"][0]["props"]
    assert "js_on_load" not in props
    assert "server_functions" not in props
    assert props["buttons"] == []
    assert props["_selectable"] is False


def test_static_document_prerenders_four_exact_scenarios_once(
    valid_bundle: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    original = ui_module.render_scenario

    def recording_render(value: object) -> str:
        calls.append(cast(str, value))
        return original(value)

    monkeypatch.setattr(ui_module, "render_scenario", recording_render)
    document = _only_document(ui_module.create_app(valid_bundle))
    assert calls == list(EXPECTED_IDS)
    assert document.count('type="radio"') == 4
    assert tuple(re.findall(r'type="radio" id="([^"]+)"', document)) == EXPECTED_IDS
    assert document.count('name="synthetic-gate-scenario"') == 4
    assert " checked" not in document
    for scenario, scenario_id in zip(SCENARIOS, EXPECTED_IDS, strict=True):
        assert scenario.label_zh_tw in document
        assert render_scenario(scenario_id) in document
    assert "<script" not in document.casefold()
    assert not re.search(r"\son[a-z]+\s*=", document, re.IGNORECASE)


def test_claim_dom_precedes_first_focusable_control(valid_bundle: Path) -> None:
    document = _only_document(ui_module.create_app(valid_bundle))
    claim = document.index('id="claim-ceiling"')
    first_radio = document.index('type="radio"')
    assert claim < first_radio
    assert document.index(EXPECTED_ZH_TW) < document.index(EXPECTED_EN) < first_radio
    assert "<legend>選擇固定 synthetic gate state</legend>" in document


@pytest.mark.parametrize("failure_code", ALL_FAILURE_CODES)
def test_failure_page_is_one_static_document_with_no_capabilities(
    tmp_path: Path, failure_code: EvidenceFailureCode, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = ui_module.create_app(make_unit_failure_bundle(tmp_path, failure_code, monkeypatch))
    config = app.get_config_file()
    document = _only_document(app)
    assert [item["type"] for item in config["components"]] == ["html"]
    assert config["dependencies"] == []
    assert len(app.fns) == 0
    assert app.get_api_info() == {"named_endpoints": {}, "unnamed_endpoints": {}}
    assert "Evidence unavailable" in document
    assert failure_code in document
    assert not re.search(r"<input\b|<button\b|<select\b|<textarea\b", document)
    assert 'class="scenario-panel"' not in document
    for metric in ("0.555", "0.870", "0.087", "0.008"):
        assert metric not in document


def test_schema_failure_controlled_seam_has_exact_copy_and_no_partial_surface(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = ui_module.create_app(
        make_unit_failure_bundle(tmp_path, "receipt_schema_invalid", monkeypatch)
    )
    document = _only_document(app)
    expected = (
        "Evidence unavailable",
        "公開 evidence 未通過完整性驗證，因此本頁不顯示 metrics 或 synthetic gate states。",
        "Evidence integrity checks failed; metrics and scenarios are disabled.",
        "receipt_schema_invalid",
    )
    positions = tuple(document.index(value) for value in expected)
    assert positions == tuple(sorted(positions))
    assert document.count("receipt_schema_invalid") == 1
    assert 'type="radio"' not in document
    assert "0.555" not in document
    response = _http_get(_compose(app), "/config")
    assert response.status_code == 200
    asgi_config = response.json()
    assert asgi_config["dependencies"] == []
    assert len(asgi_config["components"]) == 1
    assert asgi_config["components"][0]["props"]["value"] == document


def test_every_html_constructor_explicitly_disables_component_js() -> None:
    source = (SPACE_ROOT / "carerisk_space" / "ui.py").read_text(encoding="utf-8")
    calls = list(re.finditer(r"gr\.HTML\s*\(", source))
    assert calls
    for call in calls:
        tail = source[call.start() : source.find(")", call.start()) + 1]
        assert "js_on_load=None" in tail


def test_exact_instance_state_ignores_poisoned_framework_environment(
    valid_bundle: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name, value in {
        "GRADIO_ANALYTICS_ENABLED": "true",
        "HF_HUB_DISABLE_TELEMETRY": "0",
        "GRADIO_WATCH_DIRS": "/CANARY_7419",
        "GRADIO_VIBE_MODE": "true",
        "GRADIO_ROOT_PATH": "/CANARY_7419",
        "SPACE_ID": "CANARY_7419/space",
        "PORT": "9999",
    }.items():
        monkeypatch.setenv(name, value)
    app = ui_module.create_app(valid_bundle)
    assert os.environ["HF_HUB_DISABLE_TELEMETRY"] == "True"
    assert app.dev_mode is False
    assert app.vibe_mode is False
    assert app.root_path == ""
    assert app.api_open is False
    assert app.space_id is None


def test_outer_guard_constructor_is_exact_and_rejects_empty_membership() -> None:
    guard_type = ui_module.PublicSurfaceGuard
    parameters = inspect.signature(guard_type).parameters
    assert tuple(parameters) == ("downstream", "package_asset_urls")
    assert all(item.default is inspect.Parameter.empty for item in parameters.values())
    membership = ui_module.build_package_asset_membership()
    assert membership
    guard = guard_type(DownstreamRecorder(), membership)
    assert guard.package_asset_urls == membership
    with pytest.raises(ValueError, match="package_asset_membership_empty"):
        guard_type(DownstreamRecorder(), frozenset())
    with pytest.raises(ValueError, match="package_asset_membership_not_immutable"):
        guard_type(DownstreamRecorder(), set(membership))


@pytest.mark.parametrize(
    ("method", "path", "query", "headers"),
    (
        ("POST", "/", b"", [(b"host", b"127.0.0.1:7860")]),
        ("OPTIONS", "/", b"", [(b"host", b"127.0.0.1:7860"), (b"origin", b"CANARY_7419")]),
        ("GET", "/gradio_api/upload", b"", [(b"host", b"127.0.0.1:7860")]),
        ("GET", "/file=CANARY_7419", b"", [(b"host", b"127.0.0.1:7860")]),
        ("GET", "/config/", b"", [(b"host", b"127.0.0.1:7860")]),
        (
            "GET",
            "/assets/definitely-not-a-real-gradio-package-file.js",
            b"",
            [(b"host", b"127.0.0.1:7860")],
        ),
        ("GET", "/config", b"CANARY_7419=1", [(b"host", b"127.0.0.1:7860")]),
        ("GET", "/", b"", []),
        ("GET", "/", b"", [(b"host", b"127.0.0.1:7860"), (b"host", b"localhost:7860")]),
        ("GET", "/", b"", [(b"host", b"UNLISTED.invalid")]),
        ("GET", "/%2e%2e/config", b"", [(b"host", b"127.0.0.1:7860")]),
        ("GET", "//config", b"", [(b"host", b"127.0.0.1:7860")]),
    ),
)
def test_outer_guard_blocks_hostile_http_before_downstream_or_receive(
    method: str, path: str, query: bytes, headers: list[tuple[bytes, bytes]]
) -> None:
    downstream = DownstreamRecorder()
    scope = _scope(method, path, query=query, headers=headers)
    messages, receive_calls = _run_asgi(
        ui_module.PublicSurfaceGuard(downstream, ui_module.build_package_asset_membership()), scope
    )
    assert downstream.calls == receive_calls == 0
    assert messages == [
        {
            "type": "http.response.start",
            "status": 404,
            "headers": [(b"content-type", b"text/plain; charset=utf-8"), (b"content-length", b"9")],
        },
        {"type": "http.response.body", "body": b"Not Found", "more_body": False},
    ]
    assert b"CANARY_7419" not in repr(messages).encode()


@pytest.mark.parametrize(
    ("host", "scheme", "server"),
    (
        (b"127.0.0.1:7860", "http", ("127.0.0.1", 7860)),
        (b"localhost:7860", "http", ("localhost", 7860)),
        (b"carerisk-app:7860", "http", ("carerisk-app", 7860)),
        (b"steven0226-carerisk-48h.hf.space", "https", ("steven0226-carerisk-48h.hf.space", 443)),
    ),
)
def test_permitted_root_scope_is_rebuilt_from_exact_authority(
    host: bytes, scheme: str, server: tuple[str, int]
) -> None:
    downstream = DownstreamRecorder()
    scope = _scope(
        "GET",
        "/",
        host=host,
        headers=[
            (b"host", host),
            (b"origin", b"https://CANARY_7419.invalid"),
            (b"cookie", b"secret=CANARY_7419"),
            (b"authorization", b"Bearer CANARY_7419"),
            (b"x-forwarded-host", b"CANARY_7419.invalid"),
            (b"user-agent", b"CANARY_7419"),
            (b"content-length", b"0"),
        ],
    )
    messages, receive_calls = _run_asgi(
        ui_module.PublicSurfaceGuard(downstream, ui_module.build_package_asset_membership()), scope
    )
    assert _status(messages) == 204
    assert downstream.calls == 1 and receive_calls == 0
    assert downstream.scope is not None
    assert downstream.scope["headers"] == [(b"host", host)]
    assert downstream.scope["scheme"] == scheme
    assert downstream.scope["server"] == server
    assert downstream.scope["client"] == ("127.0.0.1", 0)
    assert downstream.scope["root_path"] == ""
    assert "CANARY_7419" not in repr(downstream.scope)


def test_body_framing_is_rejected_without_receive() -> None:
    for headers in (
        [(b"host", b"127.0.0.1:7860"), (b"transfer-encoding", b"chunked")],
        [(b"host", b"127.0.0.1:7860"), (b"content-length", b"1")],
        [(b"host", b"127.0.0.1:7860"), (b"content-length", b"0"), (b"content-length", b"0")],
        [(b"host", b"127.0.0.1:7860"), (b"content-length", b"CANARY_7419")],
    ):
        downstream = DownstreamRecorder()
        messages, receive_calls = _run_asgi(
            ui_module.PublicSurfaceGuard(downstream, ui_module.build_package_asset_membership()),
            _scope("GET", "/", headers=headers),
        )
        assert _status(messages) == 404
        assert downstream.calls == receive_calls == 0


def test_websocket_and_unknown_scopes_never_reach_downstream_or_receive() -> None:
    membership = ui_module.build_package_asset_membership()
    downstream = DownstreamRecorder()
    messages, receive_calls = _run_asgi(
        ui_module.PublicSurfaceGuard(downstream, membership),
        {"type": "websocket", "path": "/", "headers": []},
    )
    assert messages == [{"type": "websocket.close", "code": 1008, "reason": ""}]
    assert downstream.calls == receive_calls == 0
    downstream = DownstreamRecorder()
    messages, receive_calls = _run_asgi(
        ui_module.PublicSurfaceGuard(downstream, membership), {"type": "CANARY_7419"}
    )
    assert messages == []
    assert downstream.calls == receive_calls == 0


def test_lifespan_is_the_only_non_http_scope_forwarded() -> None:
    calls: list[str] = []

    async def downstream(scope: Any, receive: Any, send: Any) -> None:
        calls.append(cast(str, scope["type"]))

    messages, receive_calls = _run_asgi(
        ui_module.PublicSurfaceGuard(downstream, ui_module.build_package_asset_membership()),
        {"type": "lifespan"},
    )
    assert calls == ["lifespan"]
    assert messages == []
    assert receive_calls == 0


@pytest.mark.parametrize(
    ("path", "raw_path"),
    (
        ("/config", b"/Config"),
        ("/../config", b"/%2e%2e/config"),
        ("/config", b"/config%2f"),
        ("/config", b"/config\\"),
        ("/config", b"/config\x00"),
    ),
)
def test_raw_path_must_be_exact_canonical_ascii(path: str, raw_path: bytes) -> None:
    downstream = DownstreamRecorder()
    scope = _scope("GET", path)
    scope["raw_path"] = raw_path
    messages, receive_calls = _run_asgi(
        ui_module.PublicSurfaceGuard(downstream, ui_module.build_package_asset_membership()),
        scope,
    )
    assert _status(messages) == 404
    assert downstream.calls == receive_calls == 0


def test_uvicorn_h11_rejects_missing_and_duplicate_host_before_asgi(
    running_wire_app: RunningWireApp,
) -> None:
    requests = (
        b"GET / HTTP/1.1\r\nConnection: close\r\nX-Test: CANARY_7419\r\n\r\n",
        b"GET / HTTP/1.1\r\nHost: localhost:7860\r\nHost: 127.0.0.1:7860\r\n"
        b"Connection: close\r\nX-Test: CANARY_7419\r\n\r\n",
    )
    before = running_wire_app.marker.calls
    for request in requests:
        response = running_wire_app.request(request)
        assert response.status == 400
        assert b"CANARY_7419" not in response.raw
        assert b"access-control-allow-origin" not in response.raw.lower()
        assert b"content-encoding" not in response.raw.lower()
        assert running_wire_app.marker.calls == before


def test_uvicorn_wire_unlisted_host_reaches_guard_and_head_body_is_suppressed(
    running_wire_app: RunningWireApp,
) -> None:
    before = running_wire_app.marker.calls
    unlisted = running_wire_app.request(
        b"GET / HTTP/1.1\r\nHost: unlisted.invalid\r\nConnection: close\r\n\r\n"
    )
    assert unlisted.status == 404
    assert unlisted.body == b"Not Found"
    assert running_wire_app.marker.calls == before + 1
    head = running_wire_app.request(
        b"HEAD /config HTTP/1.1\r\nHost: 127.0.0.1:7860\r\nConnection: close\r\n\r\n"
    )
    assert head.status == 404
    assert head.headers[b"content-length"] == b"9"
    assert head.body == b""


def test_exact_read_only_method_table_uses_membership() -> None:
    membership = ui_module.build_package_asset_membership()
    asset = sorted(membership)[0]
    permitted = (
        ("GET", "/", b""),
        ("HEAD", "/", b""),
        ("GET", "/config", b""),
        ("GET", "/manifest.json", b""),
        ("GET", "/favicon.ico", b""),
        ("GET", "/theme.css", THEME_QUERY.encode()),
        ("GET", asset, b""),
    )
    for method, path, query in permitted:
        downstream = DownstreamRecorder()
        messages, receive_calls = _run_asgi(
            ui_module.PublicSurfaceGuard(downstream, membership),
            _scope(method, path, query=query),
        )
        assert _status(messages) == 204
        assert downstream.calls == 1 and receive_calls == 0
    for path, query in (
        ("/config", b""),
        ("/manifest.json", b""),
        ("/favicon.ico", b""),
        ("/theme.css", THEME_QUERY.encode()),
        (asset, b""),
    ):
        downstream = DownstreamRecorder()
        messages, _ = _run_asgi(
            ui_module.PublicSurfaceGuard(downstream, membership), _scope("HEAD", path, query=query)
        )
        assert _status(messages) == 404
        assert dict(messages[0]["headers"])[b"content-length"] == b"9"
        assert messages[1] == {
            "type": "http.response.body",
            "body": b"Not Found",
            "more_body": False,
        }
        assert downstream.calls == 0


def test_package_asset_membership_is_exact_regular_and_root_contained() -> None:
    membership = ui_module.build_package_asset_membership()
    assert membership
    assert all(item.startswith(("/assets/", "/static/")) for item in membership)
    assert "/static/img/logo.svg" in membership
    assert "/static/img/logo_nosize.svg" in membership
    assert "/assets/definitely-not-a-real-gradio-package-file.js" not in membership
    for raw_root in (BUILD_PATH_LIB, STATIC_PATH_LIB):
        root = Path(raw_root)
        assert root.resolve(strict=True).is_dir()
        assert not root.is_symlink()


def test_package_asset_missing_root_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(ui_module, "BUILD_PATH_LIB", tmp_path / "missing")
    with pytest.raises(ValueError):
        ui_module.build_package_asset_membership()


def test_theme_manifest_favicon_and_default_logo_are_exact(valid_bundle: Path) -> None:
    demo = ui_module.create_app(valid_bundle)
    guarded_app = _compose(demo)
    assert demo.get_config_file()["theme_hash"] == THEME_CSS_SHA256
    assert hashlib.sha256(demo.theme_css.encode()).hexdigest() == THEME_CSS_SHA256
    hostile_headers = {
        "host": "127.0.0.1:7860",
        "origin": "https://CANARY_7419.invalid",
        "cookie": "secret=CANARY_7419",
        "authorization": "Bearer CANARY_7419",
    }
    for path in ("/", "/config", f"/theme.css?{THEME_QUERY}"):
        response = _http_get(guarded_app, path, headers=hostile_headers)
        assert response.status_code == 200
        assert b"CANARY_7419" not in response.content
        assert "access-control-allow-origin" not in response.headers
        assert "content-encoding" not in response.headers
    manifest = _http_get(guarded_app, "/manifest.json")
    assert manifest.status_code == 200
    assert manifest.headers["content-type"].startswith("application/manifest+json")
    assert manifest.json() == {
        "name": PRODUCT_NAME,
        "icons": [
            {
                "src": "static/img/logo_nosize.svg",
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any",
            }
        ],
        "start_url": "./",
        "display": "standalone",
    }
    favicon = _http_get(guarded_app, "/favicon.ico")
    assert favicon.status_code == 200 and len(favicon.content) == 1107
    assert hashlib.sha256(favicon.content).hexdigest() == FAVICON_SHA256
    logo = _http_get(guarded_app, "/static/img/logo_nosize.svg")
    assert logo.status_code == 200 and len(logo.content) == 1082
    assert hashlib.sha256(logo.content).hexdigest() == MANIFEST_LOGO_SHA256
    for path in (
        "/pwa_icon",
        "/pwa_icon/192.png",
        "/gradio_api/info",
        "/gradio_api/upload",
    ):
        response = _http_get(guarded_app, path)
        assert response.status_code == 404
        assert response.content == b"Not Found"


def test_registered_gradio_routes_are_exactly_inventoried_and_classified(
    valid_bundle: Path,
) -> None:
    guarded_app = _compose(ui_module.create_app(valid_bundle))
    parent = guarded_app.downstream
    mounted = parent.routes[0].app
    records: set[tuple[str, str]] = set()

    def collect(routes: list[Any]) -> None:
        for route in routes:
            original = getattr(route, "original_router", None)
            if original is not None:
                collect(original.routes)
                continue
            path = getattr(route, "path", None)
            for method in getattr(route, "methods", set()) or set():
                records.add((method, path))

    collect(mounted.routes)
    serialized = "".join(
        f"{method}\t{path}\n" for method, path in sorted(records)
    ).encode()
    assert len(records) == 81
    assert hashlib.sha256(serialized).hexdigest() == (
        "832697792e92dd8f11200a458f8b259780308ed15b4a7ab5137d4aab8509c2e9"
    )
    safe_required = {
        ("GET", "/"),
        ("HEAD", "/"),
        ("GET", "/config"),
        ("GET", "/theme.css"),
        ("GET", "/manifest.json"),
        ("GET", "/favicon.ico"),
        ("GET", "/assets/{path:path}"),
        ("GET", "/static/{path:path}"),
    }
    assert safe_required <= records
    blocked = records - safe_required
    assert blocked
    assert ("POST", "/gradio_api/upload") in blocked
    assert ("GET", "/gradio_api/info") in blocked
    assert ("GET", "/monitoring") in blocked
    assert ("GET", "/openapi.json") in blocked


def test_failure_log_contains_only_bounded_reason(
    manifest_canary_bundle: Path, captured_app_logs: Callable[[], str]
) -> None:
    ui_module.create_app(manifest_canary_bundle)
    captured = captured_app_logs()
    assert tuple(code for code in ALL_FAILURE_CODES if code in captured) == (
        "deployment_manifest_invalid",
    )
    assert "CANARY_7419" not in captured
    assert repr({"secret": "CANARY_7419"}) not in captured


def test_entrypoint_mount_and_uvicorn_contract_are_exact(
    valid_bundle: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mount_capture: dict[str, object] = {}
    uvicorn_capture: dict[str, object] = {}
    demo = ui_module.create_app(valid_bundle)
    membership = ui_module.build_package_asset_membership()

    monkeypatch.setattr(ui_module, "create_app", lambda bundle_root=None: demo)
    monkeypatch.setattr(ui_module, "build_package_asset_membership", lambda: membership)

    def fake_mount(parent: FastAPI, mounted_demo: gr.Blocks, **kwargs: object) -> FastAPI:
        mount_capture.update(kwargs)
        assert mounted_demo is demo
        return parent

    monkeypatch.setattr(gr, "mount_gradio_app", fake_mount)
    spec = importlib.util.spec_from_file_location(
        "carerisk_space_entrypoint", SPACE_ROOT / "app.py"
    )
    assert spec is not None and spec.loader is not None
    entrypoint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entrypoint)
    def fake_run(app: Any, **kwargs: object) -> None:
        uvicorn_capture.update(kwargs)

    monkeypatch.setattr(entrypoint.uvicorn, "run", fake_run)
    entrypoint.main()
    assert mount_capture == {
        "path": "/",
        "server_name": "0.0.0.0",
        "server_port": 7860,
        "footer_links": [],
        "run_history": False,
        "root_path": "",
        "allowed_paths": ["/__carerisk_no_allowed_files__"],
        "blocked_paths": ["/"],
        "favicon_path": None,
        "show_error": False,
        "max_file_size": 0,
        "ssr_mode": False,
        "enable_monitoring": False,
        "pwa": False,
        "mcp_server": False,
    }
    assert isinstance(entrypoint.parent, FastAPI)
    assert entrypoint.parent.docs_url is None and entrypoint.parent.redoc_url is None
    assert entrypoint.parent.openapi_url is None
    assert isinstance(entrypoint.app, ui_module.PublicSurfaceGuard)
    assert entrypoint.app.downstream is entrypoint.parent
    assert entrypoint.app.package_asset_urls == membership
    assert uvicorn_capture == {
        "host": "0.0.0.0",
        "port": 7860,
        "workers": 1,
        "http": "h11",
        "proxy_headers": False,
        "forwarded_allow_ips": "",
        "access_log": False,
        "server_header": False,
        "date_header": False,
        "reload": False,
        "factory": False,
        "env_file": None,
        "log_config": None,
    }


def test_valid_evidence_is_used_for_normal_page(valid_bundle: Path) -> None:
    assert isinstance(load_evidence(valid_bundle), EvidenceViewModel)
