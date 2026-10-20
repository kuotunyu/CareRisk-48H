"""Offline resume-integrity tests for download_file.

Responses are real ``http.client.HTTPResponse`` objects parsed from in-memory
bytes, so the stdlib read semantics under test are the genuine ones. No socket,
no server, no network.
"""

from __future__ import annotations

import http.client
import io
import urllib.request
from pathlib import Path

import pytest

from carerisk48h.data.downloader import download_file, sha256_file

URL = "http://example.invalid/set-a.tar.gz"
FULL = b"abcdef"


class _Sock:
    """Socket stand-in; http.client only reads through makefile here."""

    def __init__(self, data: bytes) -> None:
        self._data = data

    def makefile(self, mode: str = "rb", *args: object, **kwargs: object) -> io.BufferedReader:
        return io.BufferedReader(io.BytesIO(self._data))

    def close(self) -> None:
        pass


def _wire(status_line: str, headers: dict[str, str], body: bytes) -> bytes:
    head = f"HTTP/1.1 {status_line}\r\n" + "".join(f"{k}: {v}\r\n" for k, v in headers.items())
    return head.encode("ascii") + b"\r\n" + body


def _responder(raw: bytes, captured: dict[str, object] | None = None):
    def fake_urlopen(request, timeout=None):  # noqa: ANN001, ANN202, ARG001
        if captured is not None:
            captured["range"] = request.get_header("Range")
        response = http.client.HTTPResponse(_Sock(raw), method="GET", url=URL)
        response.begin()
        return response

    return fake_urlopen


@pytest.fixture
def serve(monkeypatch: pytest.MonkeyPatch):
    def install(raw: bytes, captured: dict[str, object] | None = None) -> None:
        monkeypatch.setattr(urllib.request, "urlopen", _responder(raw, captured))

    return install


def _partial(target: Path) -> Path:
    return target.with_name(target.name + ".partial")


def test_valid_206_resume_completes(tmp_path: Path, serve) -> None:
    target = tmp_path / "set-a.tar.gz"
    _partial(target).write_bytes(FULL[:3])
    captured: dict[str, object] = {}
    serve(
        _wire(
            "206 Partial Content",
            {"Content-Range": "bytes 3-5/6", "Content-Length": "3"},
            FULL[3:],
        ),
        captured,
    )
    record = download_file(URL, target)
    assert captured["range"] == "bytes=3-"
    assert target.read_bytes() == FULL
    assert record.bytes == len(FULL)
    assert record.sha256 == sha256_file(target)
    assert not _partial(target).exists()


def test_valid_200_with_length_completes(tmp_path: Path, serve) -> None:
    target = tmp_path / "set-a.tar.gz"
    serve(_wire("200 OK", {"Content-Length": "6", "Accept-Ranges": "bytes"}, FULL))
    record = download_file(URL, target)
    assert target.read_bytes() == FULL
    assert record.bytes == len(FULL)


def test_valid_200_without_content_length_completes(tmp_path: Path, serve) -> None:
    target = tmp_path / "set-a.tar.gz"
    serve(_wire("200 OK", {"Connection": "close"}, FULL))
    record = download_file(URL, target)
    assert target.read_bytes() == FULL
    assert record.bytes == len(FULL)


def test_200_fallback_ignoring_range_restarts_from_scratch(tmp_path: Path, serve) -> None:
    target = tmp_path / "set-a.tar.gz"
    _partial(target).write_bytes(FULL[:3])
    serve(_wire("200 OK", {"Content-Length": "6"}, FULL))
    record = download_file(URL, target)
    assert target.read_bytes() == FULL
    assert record.bytes == len(FULL)


def test_existing_target_needs_no_request(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "set-a.tar.gz"
    target.write_bytes(FULL)

    def unexpected(*args: object, **kwargs: object) -> None:
        raise AssertionError("an existing target must not be re-requested")

    monkeypatch.setattr(urllib.request, "urlopen", unexpected)
    record = download_file(URL, target)
    assert record.bytes == len(FULL)
    assert record.sha256 == sha256_file(target)


def test_206_with_wrong_range_start_is_rejected_without_touching_partial(
    tmp_path: Path, serve
) -> None:
    target = tmp_path / "set-a.tar.gz"
    _partial(target).write_bytes(FULL[:3])
    serve(
        _wire(
            "206 Partial Content",
            {"Content-Range": "bytes 1-5/6", "Content-Length": "5"},
            FULL[1:],
        )
    )
    with pytest.raises(RuntimeError, match="Content-Range"):
        download_file(URL, target)
    assert not target.exists()
    assert _partial(target).read_bytes() == FULL[:3]


def test_206_with_zero_start_while_resuming_is_rejected_preserving_partial(
    tmp_path: Path, serve
) -> None:
    """Byte 0 is outside the requested bytes=3- range; reject before touching the prefix."""
    target = tmp_path / "set-a.tar.gz"
    _partial(target).write_bytes(FULL[:3])
    serve(
        _wire(
            "206 Partial Content",
            {"Content-Range": "bytes 0-5/6", "Content-Length": "6"},
            FULL,
        )
    )
    with pytest.raises(RuntimeError, match="Content-Range"):
        download_file(URL, target)
    assert not target.exists()
    assert _partial(target).read_bytes() == FULL[:3]


def test_206_with_unknown_total_is_rejected_preserving_partial(tmp_path: Path, serve) -> None:
    """An unknown total cannot establish completion, so end+1 must never stand in for it."""
    target = tmp_path / "set-a.tar.gz"
    _partial(target).write_bytes(FULL[:3])
    serve(
        _wire(
            "206 Partial Content",
            {"Content-Range": "bytes 3-4/*", "Content-Length": "2"},
            FULL[3:5],
        )
    )
    with pytest.raises(RuntimeError, match="unknown"):
        download_file(URL, target)
    assert not target.exists()
    assert _partial(target).read_bytes() == FULL[:3]


def test_206_with_unknown_total_is_rejected_even_when_body_completes_the_file(
    tmp_path: Path, serve
) -> None:
    target = tmp_path / "set-a.tar.gz"
    _partial(target).write_bytes(FULL[:3])
    serve(
        _wire(
            "206 Partial Content",
            {"Content-Range": "bytes 3-5/*", "Content-Length": "3"},
            FULL[3:],
        )
    )
    with pytest.raises(RuntimeError, match="unknown"):
        download_file(URL, target)
    assert not target.exists()
    assert _partial(target).read_bytes() == FULL[:3]


def test_206_with_malformed_content_range_is_rejected(tmp_path: Path, serve) -> None:
    target = tmp_path / "set-a.tar.gz"
    _partial(target).write_bytes(FULL[:3])
    serve(
        _wire(
            "206 Partial Content",
            {"Content-Range": "bytes garbage/6", "Content-Length": "3"},
            FULL[3:],
        )
    )
    with pytest.raises(RuntimeError, match="Content-Range"):
        download_file(URL, target)
    assert not target.exists()
    assert _partial(target).read_bytes() == FULL[:3]


def test_206_without_content_range_is_rejected(tmp_path: Path, serve) -> None:
    target = tmp_path / "set-a.tar.gz"
    _partial(target).write_bytes(FULL[:3])
    serve(_wire("206 Partial Content", {"Content-Length": "3"}, FULL[3:]))
    with pytest.raises(RuntimeError, match="Content-Range"):
        download_file(URL, target)
    assert not target.exists()
    assert _partial(target).read_bytes() == FULL[:3]


def test_206_range_inconsistent_with_total_is_rejected(tmp_path: Path, serve) -> None:
    target = tmp_path / "set-a.tar.gz"
    _partial(target).write_bytes(FULL[:3])
    serve(
        _wire(
            "206 Partial Content",
            {"Content-Range": "bytes 3-9/6", "Content-Length": "3"},
            FULL[3:],
        )
    )
    with pytest.raises(RuntimeError, match="Content-Range"):
        download_file(URL, target)
    assert not target.exists()
    assert _partial(target).read_bytes() == FULL[:3]


def test_206_partial_tail_is_not_promoted_as_complete(tmp_path: Path, serve) -> None:
    target = tmp_path / "set-a.tar.gz"
    _partial(target).write_bytes(FULL[:3])
    serve(
        _wire(
            "206 Partial Content",
            {"Content-Range": "bytes 3-4/6", "Content-Length": "2"},
            FULL[3:5],
        )
    )
    with pytest.raises(RuntimeError, match="incomplete"):
        download_file(URL, target)
    assert not target.exists()
    assert _partial(target).read_bytes() == FULL[:5]


def test_short_200_body_is_rejected_and_partial_kept(tmp_path: Path, serve) -> None:
    target = tmp_path / "set-a.tar.gz"
    serve(_wire("200 OK", {"Content-Length": "6"}, FULL[:3]))
    with pytest.raises(RuntimeError, match="advertised"):
        download_file(URL, target)
    assert not target.exists()
    assert _partial(target).read_bytes() == FULL[:3]


def test_short_206_body_is_rejected_and_partial_kept(tmp_path: Path, serve) -> None:
    target = tmp_path / "set-a.tar.gz"
    _partial(target).write_bytes(FULL[:3])
    serve(
        _wire(
            "206 Partial Content",
            {"Content-Range": "bytes 3-5/6", "Content-Length": "3"},
            FULL[3:4],
        )
    )
    with pytest.raises(RuntimeError, match="advertised"):
        download_file(URL, target)
    assert not target.exists()
    assert _partial(target).read_bytes() == FULL[:4]
