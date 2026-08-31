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
import sys
import threading
import time
from collections import Counter, deque
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast, get_args

import carerisk_space.evidence as evidence_module
import carerisk_space.ui as ui_module
import gradio as gr
import gradio.routes as gradio_routes
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

SAFE_INNER_ROUTES = (
    ("GET", "/"),
    ("HEAD", "/"),
    ("GET", "/assets/{path:path}"),
    ("GET", "/config"),
    ("GET", "/favicon.ico"),
    ("GET", "/manifest.json"),
    ("GET", "/static/{path:path}"),
    ("GET", "/theme.css"),
)
BLOCKED_INNER_ROUTES = (
    ("GET", "/config/"),
    ("GET", "/gradio_api/app_id"),
    ("GET", "/gradio_api/app_id/"),
    ("GET", "/gradio_api/call/v2/{api_name}/{event_id}"),
    ("GET", "/gradio_api/call/{api_name}/{event_id}"),
    ("GET", "/gradio_api/custom_component/{id}/{environment}/{type}/{file_name}"),
    ("GET", "/gradio_api/deep_link"),
    ("GET", "/gradio_api/dev/reload"),
    ("GET", "/gradio_api/file/{path:path}"),
    ("GET", "/gradio_api/file={path_or_url:path}"),
    ("GET", "/gradio_api/heartbeat/{session_hash}"),
    ("GET", "/gradio_api/info"),
    ("GET", "/gradio_api/info/"),
    ("GET", "/gradio_api/login_check"),
    ("GET", "/gradio_api/login_check/"),
    ("GET", "/gradio_api/openapi.json"),
    ("GET", "/gradio_api/proxy={url_path:path}"),
    ("GET", "/gradio_api/queue/data"),
    ("GET", "/gradio_api/queue/status"),
    ("GET", "/gradio_api/runs"),
    ("GET", "/gradio_api/runs/"),
    ("GET", "/gradio_api/startup-events"),
    ("GET", "/gradio_api/stream/{session_hash}/{run}/{component_id}/playlist-file"),
    ("GET", "/gradio_api/stream/{session_hash}/{run}/{component_id}/playlist.m3u8"),
    ("GET", "/gradio_api/stream/{session_hash}/{run}/{component_id}/{segment_id}.{ext}"),
    ("GET", "/gradio_api/theme.css"),
    ("GET", "/gradio_api/token"),
    ("GET", "/gradio_api/token/"),
    ("GET", "/gradio_api/upload_progress"),
    ("GET", "/gradio_api/user"),
    ("GET", "/gradio_api/user/"),
    ("GET", "/gradio_api/vibe-code"),
    ("GET", "/gradio_api/vibe-code/"),
    ("GET", "/logout"),
    ("GET", "/monitoring"),
    ("GET", "/monitoring/summary"),
    ("GET", "/monitoring/{key}"),
    ("GET", "/openapi.json"),
    ("GET", "/pwa_icon"),
    ("GET", "/pwa_icon/{size}"),
    ("GET", "/robots.txt"),
    ("GET", "/svelte/{path:path}"),
    ("HEAD", "/gradio_api/file={path_or_url:path}"),
    ("HEAD", "/gradio_api/proxy={url_path:path}"),
    ("HEAD", "/openapi.json"),
    ("POST", "/gradio_api/api/{api_name}"),
    ("POST", "/gradio_api/api/{api_name}/"),
    ("POST", "/gradio_api/call/v2/{api_name}"),
    ("POST", "/gradio_api/call/v2/{api_name}/"),
    ("POST", "/gradio_api/call/{api_name}"),
    ("POST", "/gradio_api/call/{api_name}/"),
    ("POST", "/gradio_api/cancel"),
    ("POST", "/gradio_api/component_server"),
    ("POST", "/gradio_api/component_server/"),
    ("POST", "/gradio_api/process_recording"),
    ("POST", "/gradio_api/queue/join"),
    ("POST", "/gradio_api/reset"),
    ("POST", "/gradio_api/reset/"),
    ("POST", "/gradio_api/run/{api_name}"),
    ("POST", "/gradio_api/run/{api_name}/"),
    ("POST", "/gradio_api/stream/{event_id}"),
    ("POST", "/gradio_api/stream/{event_id}/close"),
    ("POST", "/gradio_api/undo-vibe-edit"),
    ("POST", "/gradio_api/undo-vibe-edit/"),
    ("POST", "/gradio_api/upload"),
    ("POST", "/gradio_api/vibe-code"),
    ("POST", "/gradio_api/vibe-code/"),
    ("POST", "/gradio_api/vibe-edit"),
    ("POST", "/gradio_api/vibe-edit/"),
    ("POST", "/gradio_api/vibe-starter-queries"),
    ("POST", "/gradio_api/vibe-starter-queries/"),
    ("POST", "/login"),
    ("POST", "/login/"),
)


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


def _route_inventory(parent: FastAPI) -> list[tuple[str, str, str]]:
    records: list[tuple[str, str, str]] = []
    for route in parent.routes:
        records.append(("parent", "MOUNT", cast(str, route.path)))
        mounted = route.app

        def collect(routes: list[Any]) -> None:
            for inner in routes:
                original = getattr(inner, "original_router", None)
                if original is not None:
                    collect(original.routes)
                    continue
                path = cast(str, inner.path)
                for method in sorted(inner.methods or ()):
                    records.append(("inner", method, path))

        collect(mounted.routes)
    return sorted(records)


def _assert_route_inventory(records: list[tuple[str, str, str]]) -> None:
    expected = [
        ("parent", "MOUNT", ""),
        *(("inner", method, path) for method, path in SAFE_INNER_ROUTES),
        *(("inner", method, path) for method, path in BLOCKED_INNER_ROUTES),
    ]
    assert len(records) == len(expected)
    assert Counter(records) == Counter(expected)
    assert all(count == 1 for count in Counter(records).values())


def _asset_tree_records() -> tuple[frozenset[str], bytes]:
    records: list[bytes] = []
    membership: set[str] = set()
    for raw_root, prefix in (
        (BUILD_PATH_LIB, "/assets/"),
        (STATIC_PATH_LIB, "/static/"),
    ):
        root = Path(raw_root).resolve(strict=True)
        for candidate in sorted(root.rglob("*")):
            if not candidate.is_file():
                continue
            relative = candidate.resolve(strict=True).relative_to(root).as_posix()
            url = prefix + relative
            payload = candidate.read_bytes()
            membership.add(url)
            records.append(
                f"{url}\t{len(payload)}\t{hashlib.sha256(payload).hexdigest()}\n".encode()
            )
    return frozenset(membership), b"".join(sorted(records))


def _queue_state_snapshot(demo: gr.Blocks) -> tuple[tuple[str, int], ...]:
    queue = demo._queue
    state_holder = demo.state_holder
    collections = {
        "active_jobs": queue.active_jobs,
        "asyncio_tasks": queue._asyncio_tasks,
        "event_analytics": queue.event_analytics,
        "event_ids": queue.event_ids_to_events,
        "event_queues": queue.event_queue_per_concurrency_id,
        "pending_ids": queue.pending_event_ids_session,
        "pending_messages": queue.pending_messages_per_session,
        "session_data": state_holder.session_data,
        "time_last_used": state_holder.time_last_used,
    }
    return tuple(sorted((name, len(value)) for name, value in collections.items()))


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
    def __init__(self, downstream: Any, package_asset_urls: frozenset[str]) -> None:
        self.downstream = downstream
        self.calls = 0
        self._requests: deque[tuple[str, str]] = deque(maxlen=128)
        self._package_asset_urls = package_asset_urls

    def snapshots(self) -> tuple[tuple[str, str], ...]:
        return tuple(self._requests)

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        self.calls += 1
        if scope.get("type") == "http":
            method = scope.get("method")
            path = scope.get("path")
            bounded_method = (
                method if method in {"GET", "HEAD", "POST", "OPTIONS"} else "OTHER"
            )
            safe_paths = {"/", "/config", "/theme.css", "/manifest.json", "/favicon.ico"}
            bounded_path = (
                path
                if isinstance(path, str)
                and (path in safe_paths or path in self._package_asset_urls)
                else "<blocked>"
            )
            self._requests.append((bounded_method, bounded_path))
        await self.downstream(scope, receive, send)


class BoundedLogCapture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self._records: deque[str] = deque(maxlen=128)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            rendered = self.format(record)
        except Exception:
            rendered = "log_format_failed"
        self._records.append(rendered[:4096])

    def snapshot(self) -> str:
        return "\n".join(self._records)[-65_536:]


@dataclass(frozen=True)
class RunningWireApp:
    marker: AppEntryMarker
    demo: gr.Blocks
    log_capture: BoundedLogCapture

    def logs(self) -> str:
        return self.log_capture.snapshot()

    def requests(self) -> tuple[tuple[str, str], ...]:
        return self.marker.snapshots()

    @staticmethod
    def parse_raw_response(raw: bytes, *, context: str) -> RawResponse:
        if not raw:
            raise AssertionError(f"empty HTTP response: {context}")
        head, separator, body = raw.partition(b"\r\n\r\n")
        if not separator:
            raise AssertionError(f"incomplete HTTP response headers: {context}")
        lines = head.split(b"\r\n")
        status_parts = lines[0].split(b" ", 2)
        if len(status_parts) < 2 or not status_parts[1].isdigit():
            raise AssertionError(f"invalid HTTP status line: {context}")
        headers: dict[bytes, bytes] = {}
        for line in lines[1:]:
            if b":" not in line:
                raise AssertionError(f"invalid HTTP response header: {context}")
            name, value = line.split(b":", 1)
            headers[name.lower()] = value.strip()
        return RawResponse(int(status_parts[1]), headers, body, raw)

    def request(self, request_bytes: bytes) -> RawResponse:
        chunks: list[bytes] = []
        with socket.create_connection(("127.0.0.1", 7860), timeout=5) as connection:
            connection.sendall(request_bytes)
            while True:
                try:
                    chunk = connection.recv(65536)
                except (ConnectionAbortedError, ConnectionResetError):
                    break
                if not chunk:
                    break
                chunks.append(chunk)
        raw = b"".join(chunks)
        return self.parse_raw_response(raw, context="complete-request")

    def request_early_response(self, request_headers: bytes, body_prefix: bytes) -> RawResponse:
        if not request_headers.endswith(b"\r\n\r\n"):
            raise AssertionError("early-response request headers are incomplete")
        if len(body_prefix) > 4096:
            raise AssertionError("early-response body prefix exceeds bound")
        chunks: list[bytes] = []
        with socket.create_connection(("127.0.0.1", 7860), timeout=5) as connection:
            connection.sendall(request_headers)
            if body_prefix:
                connection.sendall(body_prefix)
            while True:
                try:
                    chunk = connection.recv(65536)
                except (ConnectionAbortedError, ConnectionResetError):
                    break
                except TimeoutError:
                    break
                if not chunk:
                    break
                chunks.append(chunk)
                raw = b"".join(chunks)
                _, separator, body = raw.partition(b"\r\n\r\n")
                if not separator:
                    continue
                partial = self.parse_raw_response(raw, context="early-response")
                content_length = partial.headers.get(b"content-length")
                if (
                    content_length is not None
                    and content_length.isdigit()
                    and len(body) >= int(content_length)
                ):
                    break
        return self.parse_raw_response(b"".join(chunks), context="early-response")


@pytest.fixture(scope="module")
def running_wire_app(valid_bundle: Path) -> Iterator[RunningWireApp]:
    demo = ui_module.create_app(valid_bundle)
    guarded = _compose(demo)
    marker = AppEntryMarker(guarded, guarded.package_asset_urls)
    log_capture = BoundedLogCapture()
    captured_loggers = (
        logging.getLogger(),
        logging.getLogger("uvicorn.error"),
        logging.getLogger("carerisk_space.ui"),
    )
    for logger in captured_loggers:
        logger.addHandler(log_capture)
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
        for logger in captured_loggers:
            logger.removeHandler(log_capture)
        raise AssertionError("programmatic Uvicorn+h11 did not start")
    running = RunningWireApp(marker, demo, log_capture)
    try:
        root = running.request(
            b"GET / HTTP/1.1\r\nHost: 127.0.0.1:7860\r\nConnection: close\r\n\r\n"
        )
        config_response = running.request(
            b"GET /config HTTP/1.1\r\nHost: 127.0.0.1:7860\r\nConnection: close\r\n\r\n"
        )
        theme = running.request(
            f"GET /theme.css?{THEME_QUERY} HTTP/1.1\r\n"
            "Host: 127.0.0.1:7860\r\nConnection: close\r\n\r\n".encode()
        )
        assert root.status == config_response.status == theme.status == 200
        assert json.loads(config_response.body)["dependencies"] == []
        assert hashlib.sha256(theme.body).hexdigest() == THEME_CSS_SHA256
        assert b"access-control-allow-origin" not in root.raw.lower()
        assert b"content-encoding" not in root.raw.lower()
        yield running
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        for logger in captured_loggers:
            logger.removeHandler(log_capture)
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
    root_response = _http_get(_compose(app), "/")
    assert root_response.status_code == 200
    root = root_response.text
    for value in expected:
        assert value in root
    assert root.count("receipt_schema_invalid") == 1
    assert tuple(code for code in ALL_FAILURE_CODES if code in root) == (
        "receipt_schema_invalid",
    )
    assert not re.search(r'<input[^>]+type=["\']radio["\']', root)
    assert 'class="scenario-panel"' not in root
    assert "synthetic-gate-scenario" not in root
    assert "/gradio_api/call" not in root
    assert "CANARY_7419" not in root
    for metric in ("0.555", "0.870", "0.087", "0.008"):
        assert metric not in root


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
        ("GET", "/", b"", [(b"Host", b"127.0.0.1:7860")]),
        ("GET", "/", b"", [(b"host", b"127.0.0.1:7860"), (b"host", b"localhost:7860")]),
        ("GET", "/", b"", [(b"host", b"127.0.0.1:7860"), (b"Host", b"localhost:7860")]),
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


def test_uvicorn_wire_permitted_root_head_has_no_entity_body(
    running_wire_app: RunningWireApp,
) -> None:
    before = running_wire_app.marker.calls
    response = running_wire_app.request(
        b"HEAD / HTTP/1.1\r\nHost: 127.0.0.1:7860\r\nConnection: close\r\n\r\n"
    )
    assert response.status == 200
    assert response.body == b""
    assert int(response.headers[b"content-length"]) > 0
    assert response.headers[b"content-type"].startswith(b"text/html")
    assert b"access-control-allow-origin" not in response.headers
    assert b"content-encoding" not in response.headers
    assert running_wire_app.marker.calls == before + 1


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


def _fake_asset_roots(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, Path]:
    build = tmp_path / "build"
    static = tmp_path / "static"
    build.mkdir()
    static.mkdir()
    (build / "app.js").write_bytes(b"app")
    (static / "logo.svg").write_bytes(b"logo")
    monkeypatch.setattr(ui_module, "BUILD_PATH_LIB", build)
    monkeypatch.setattr(ui_module, "STATIC_PATH_LIB", static)
    return build, static


def _symlink_or_skip(link: Path, target: Path, *, target_is_directory: bool = False) -> None:
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except OSError as exc:
        _capability_skip_or_fail(f"symlink creation unavailable: {exc}")


def _capability_skip_or_fail(reason: str) -> None:
    if sys.platform == "win32":
        pytest.skip(f"Windows fixture capability unavailable: {reason}")
    pytest.fail(f"mandatory Linux fixture capability unavailable: {reason}")


def test_linux_symlink_fixture_failure_is_a_failure_not_a_skip(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")

    def unavailable(*args: object, **kwargs: object) -> None:
        raise OSError("CANARY_7419 fixture unavailable")

    monkeypatch.setattr(Path, "symlink_to", unavailable)
    try:
        _symlink_or_skip(tmp_path / "link", tmp_path / "target")
    except BaseException as exc:
        assert type(exc).__name__ == "Failed"
        assert "mandatory Linux" in str(exc)
    else:
        pytest.fail("Linux symlink fixture failure was not reported")


def test_package_asset_root_symlink_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    real_build = tmp_path / "real-build"
    real_build.mkdir()
    (real_build / "app.js").write_bytes(b"app")
    build_link = tmp_path / "build-link"
    _symlink_or_skip(build_link, real_build, target_is_directory=True)
    static = tmp_path / "static"
    static.mkdir()
    (static / "logo.svg").write_bytes(b"logo")
    monkeypatch.setattr(ui_module, "BUILD_PATH_LIB", build_link)
    monkeypatch.setattr(ui_module, "STATIC_PATH_LIB", static)
    with pytest.raises(ValueError, match="package_asset_root_symlink"):
        ui_module.build_package_asset_membership()


@pytest.mark.parametrize("directory", (False, True))
def test_package_asset_file_or_directory_symlink_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, directory: bool
) -> None:
    build, _ = _fake_asset_roots(monkeypatch, tmp_path)
    target = tmp_path / ("target-dir" if directory else "target.js")
    if directory:
        target.mkdir()
        (target / "nested.js").write_bytes(b"nested")
    else:
        target.write_bytes(b"target")
    _symlink_or_skip(
        build / ("linked-dir" if directory else "linked.js"),
        target,
        target_is_directory=directory,
    )
    with pytest.raises(ValueError, match="package_asset_symlink"):
        ui_module.build_package_asset_membership()


def test_package_asset_containment_escape_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    build, _ = _fake_asset_roots(monkeypatch, tmp_path)
    outside = tmp_path / "outside.js"
    outside.write_bytes(b"outside")
    escape = build / "escape.js"
    _symlink_or_skip(escape, outside)
    real_is_symlink = Path.is_symlink
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda path: False if path == escape else real_is_symlink(path),
    )
    with pytest.raises(ValueError, match="package_asset_containment_invalid"):
        ui_module.build_package_asset_membership()


def test_package_asset_special_file_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    build, _ = _fake_asset_roots(monkeypatch, tmp_path)
    special = build / "special.sock"
    unix_family = getattr(socket, "AF_UNIX", None)
    if unix_family is None:
        _capability_skip_or_fail("AF_UNIX is absent")
        raise AssertionError("unreachable")
    unix_socket = socket.socket(unix_family, socket.SOCK_STREAM)
    try:
        unix_socket.bind(str(special))
    except (AttributeError, OSError) as exc:
        unix_socket.close()
        _capability_skip_or_fail(f"filesystem special-file creation unavailable: {exc}")
    try:
        with pytest.raises(ValueError, match="package_asset_special_file"):
            ui_module.build_package_asset_membership()
    finally:
        unix_socket.close()


def test_package_asset_duplicate_url_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    build, _ = _fake_asset_roots(monkeypatch, tmp_path)
    (build / "other.js").write_bytes(b"other")
    monkeypatch.setattr(ui_module, "_canonical_asset_relative", lambda relative: "same.js")
    with pytest.raises(ValueError, match="package_asset_duplicate_url"):
        ui_module.build_package_asset_membership()


def test_package_asset_case_alias_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    build, _ = _fake_asset_roots(monkeypatch, tmp_path)
    upper = build / "CaseAlias.js"
    lower = build / "casealias.js"
    upper.write_bytes(b"upper")
    lower.write_bytes(b"lower")
    if upper.samefile(lower):
        _capability_skip_or_fail("case-sensitive alias fixture unavailable")
    with pytest.raises(ValueError, match="package_asset_case_alias"):
        ui_module.build_package_asset_membership()


def test_package_asset_membership_has_sorted_content_tree_evidence() -> None:
    membership, records = _asset_tree_records()
    repeated_membership, repeated_records = _asset_tree_records()
    assert membership == ui_module.build_package_asset_membership()
    assert repeated_membership == membership
    assert repeated_records == records
    assert records == b"".join(sorted(records.splitlines(keepends=True)))
    assert len(records.splitlines()) == len(membership)
    assert all(len(record.split(b"\t")) == 3 for record in records.splitlines())
    assert hashlib.sha256(records).digest() == hashlib.sha256(repeated_records).digest()


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


def test_direct_outer_boundary_blocks_file_and_upload_before_receive(
    valid_bundle: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    demo = ui_module.create_app(valid_bundle)
    guarded = _compose(demo)
    bomb_calls: list[str] = []

    def bomb(*args: object, **kwargs: object) -> None:
        bomb_calls.append(repr((args, kwargs)))
        raise AssertionError("inner fetch/temp capability reached")

    monkeypatch.setattr(gradio_routes, "secure_url_stream_response", bomb)
    monkeypatch.setattr(gradio_routes, "file_fetch", bomb)
    monkeypatch.setattr(gradio_routes.tempfile, "NamedTemporaryFile", bomb)
    monkeypatch.setattr(gradio_routes.tempfile, "TemporaryDirectory", bomb)
    temp_root = tmp_path / "owned-temp"
    temp_root.mkdir()
    monkeypatch.setattr(gradio_routes.tempfile, "tempdir", str(temp_root))
    before_temp = tuple(temp_root.iterdir())
    before_state = _queue_state_snapshot(demo)
    probes = (
        ("GET", "/gradio_api/file=http://CANARY_7419.invalid/a", [], b""),
        ("GET", "/gradio_api/file=/tmp/CANARY_7419", [], b""),
        ("POST", "/gradio_api/upload", [(b"content-length", b"0")], b""),
        ("POST", "/gradio_api/upload", [(b"content-length", b"11")], b"CANARY_7419"),
        (
            "POST",
            "/gradio_api/upload",
            [(b"content-length", b"1048577")],
            b"CANARY_7419" * 8192,
        ),
    )
    for method, path, extra_headers, payload in probes:
        scope = _scope(
            method,
            path,
            headers=[(b"host", b"127.0.0.1:7860"), *extra_headers],
        )
        messages, receive_calls = _run_asgi(guarded, scope)
        assert receive_calls == 0
        assert messages == [
            {
                "type": "http.response.start",
                "status": 404,
                "headers": [
                    (b"content-type", b"text/plain; charset=utf-8"),
                    (b"content-length", b"9"),
                ],
            },
            {"type": "http.response.body", "body": b"Not Found", "more_body": False},
        ]
        serialized = repr(messages).encode()
        assert b"CANARY_7419" not in serialized
        if payload:
            assert payload not in serialized
    assert bomb_calls == []
    assert tuple(temp_root.iterdir()) == before_temp
    assert _queue_state_snapshot(demo) == before_state


def test_running_outer_boundary_blocks_file_and_upload_before_fetch_or_temp(
    running_wire_app: RunningWireApp,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    bomb_calls: list[str] = []

    def bomb(*args: object, **kwargs: object) -> None:
        bomb_calls.append(repr((args, kwargs)))
        raise AssertionError("inner fetch/temp capability reached")

    monkeypatch.setattr(gradio_routes, "secure_url_stream_response", bomb)
    monkeypatch.setattr(gradio_routes, "file_fetch", bomb)
    monkeypatch.setattr(gradio_routes.tempfile, "NamedTemporaryFile", bomb)
    monkeypatch.setattr(gradio_routes.tempfile, "TemporaryDirectory", bomb)
    temp_root = tmp_path / "owned-wire-temp"
    temp_root.mkdir()
    monkeypatch.setattr(gradio_routes.tempfile, "tempdir", str(temp_root))
    before_temp = tuple(temp_root.iterdir())
    before_state = _queue_state_snapshot(running_wire_app.demo)
    before_logs = running_wire_app.logs()
    before_requests = running_wire_app.requests()
    probes = (
        (
            b"GET /gradio_api/file=http://CANARY_7419.invalid/a HTTP/1.1\r\n"
            b"Host: 127.0.0.1:7860\r\nConnection: close\r\n\r\n",
            b"CANARY_7419",
            b"",
            False,
        ),
        (
            b"GET /gradio_api/file=/tmp/CANARY_7419 HTTP/1.1\r\n"
            b"Host: 127.0.0.1:7860\r\nConnection: close\r\n\r\n",
            b"CANARY_7419",
            b"",
            False,
        ),
        (
            b"POST /gradio_api/upload HTTP/1.1\r\nHost: 127.0.0.1:7860\r\n"
            b"Content-Length: 0\r\nConnection: close\r\n\r\n",
            b"CANARY_7419",
            b"",
            False,
        ),
        (
            b"POST /gradio_api/upload HTTP/1.1\r\nHost: 127.0.0.1:7860\r\n"
            b"Content-Length: 11\r\nX-Payload-Name: CANARY_7419\r\n"
            b"Connection: keep-alive\r\n\r\n",
            b"CANARY_7419",
            b"",
            True,
        ),
        (
            b"POST /gradio_api/upload HTTP/1.1\r\nHost: 127.0.0.1:7860\r\n"
            b"Content-Length: 1048588\r\n"
            b"Content-Type: multipart/form-data; boundary=CANARY_7419\r\n"
            b"Connection: keep-alive\r\n\r\n",
            b"CANARY_7419",
            b"--CANARY_7419\r\nContent-Disposition: form-data; name=\"file\"; ",
            True,
        ),
    )
    before_entry = running_wire_app.marker.calls
    payload_reprs: list[str] = []
    for request, canary, bounded_prefix, early_response in probes:
        if bounded_prefix:
            payload_reprs.append(repr(bounded_prefix))
        if early_response:
            response = running_wire_app.request_early_response(request, bounded_prefix)
        else:
            response = running_wire_app.request(request)
        assert response.status == 404
        assert response.headers[b"content-length"] == b"9"
        assert response.body == b"Not Found"
        assert canary not in response.raw
        assert b"access-control-allow-origin" not in response.raw.lower()
        assert b"content-encoding" not in response.raw.lower()
    assert running_wire_app.marker.calls == before_entry + len(probes)
    assert bomb_calls == []
    assert tuple(temp_root.iterdir()) == before_temp
    assert _queue_state_snapshot(running_wire_app.demo) == before_state
    captured = (
        running_wire_app.logs()[len(before_logs) :]
        + repr(running_wire_app.requests()[len(before_requests) :])
    )
    assert "CANARY_7419" not in captured
    assert repr({"secret": "CANARY_7419"}) not in captured
    assert all(payload_repr not in captured for payload_repr in payload_reprs)
    assert "Traceback" not in captured


def test_raw_wire_parser_reports_empty_response_without_index_error(
    running_wire_app: RunningWireApp,
) -> None:
    with pytest.raises(AssertionError, match="empty HTTP response: oversized-header-first"):
        running_wire_app.parse_raw_response(b"", context="oversized-header-first")


def test_running_fixture_health_gate_and_snapshots_are_bounded(
    running_wire_app: RunningWireApp,
) -> None:
    requests = running_wire_app.requests()
    assert requests[:3] == (
        ("GET", "/"),
        ("GET", "/config"),
        ("GET", "/theme.css"),
    )
    assert len(requests) <= 128
    assert len(running_wire_app.logs()) <= 65_536


def test_registered_gradio_routes_are_exactly_inventoried_and_classified(
    valid_bundle: Path,
) -> None:
    guarded_app = _compose(ui_module.create_app(valid_bundle))
    parent = guarded_app.downstream
    records = _route_inventory(parent)
    _assert_route_inventory(records)
    serialized = "".join(f"{layer}\t{method}\t{path}\n" for layer, method, path in records).encode()
    assert len(records) == 82
    assert hashlib.sha256(serialized).hexdigest() == (
        "726e9c3304cafc0d5f06c8752bfa916ebf76ca625ef7fe2493144a8145130843"
    )
    assert set(SAFE_INNER_ROUTES).isdisjoint(BLOCKED_INNER_ROUTES)
    assert ("POST", "/gradio_api/upload") in BLOCKED_INNER_ROUTES
    assert ("GET", "/gradio_api/info") in BLOCKED_INNER_ROUTES
    assert ("GET", "/monitoring") in BLOCKED_INNER_ROUTES
    assert ("GET", "/openapi.json") in BLOCKED_INNER_ROUTES


def test_route_inventory_rejects_duplicate_unknown_and_missing_records() -> None:
    expected = [
        ("parent", "MOUNT", ""),
        *(("inner", method, path) for method, path in SAFE_INNER_ROUTES),
        *(("inner", method, path) for method, path in BLOCKED_INNER_ROUTES),
    ]
    mutations = (
        [*expected, expected[-1]],
        [*expected, ("inner", "GET", "/CANARY_7419")],
        expected[:-1],
    )
    for mutation in mutations:
        with pytest.raises(AssertionError):
            _assert_route_inventory(sorted(mutation))


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
