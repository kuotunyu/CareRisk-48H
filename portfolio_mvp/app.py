"""Hugging Face Space entry point for the portfolio MVP."""

from collections.abc import Awaitable, Callable

from carerisk_mvp.ui import create_demo

Message = dict[str, object]
Scope = dict[str, object]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

_ALLOWED_EXACT_PATHS = {"/", "/theme.css"}
_ALLOWED_PATH_PREFIXES = ("/assets/", "/static/")
_LOWER_HEX_BYTES = frozenset(b"0123456789abcdef")


class PublicSurfaceGuard:
    """Expose only the static read surface required by the browser."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope_type = scope.get("type")
        if scope_type == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return
        if scope_type != "http":
            return

        method = scope.get("method")
        path = scope.get("path")
        query_string = scope.get("query_string", b"")
        if method not in {"GET", "HEAD"}:
            await self._empty_response(send, status=405)
            return
        if path == "/gradio_api/startup-events" and query_string in {b"", ""}:
            await self._empty_response(send, status=200)
            return
        if (
            not isinstance(path, str)
            or not self._query_allowed(path, query_string)
            or not self._path_allowed(path)
        ):
            await self._empty_response(send, status=404)
            return
        if method == "GET" and path == "/":
            await self._serve_localized_root(scope, receive, send)
            return
        await self.app(scope, receive, send)

    @staticmethod
    def _path_allowed(path: str) -> bool:
        if "\\" in path or "%" in path or "//" in path or ".." in path.split("/"):
            return False
        return path in _ALLOWED_EXACT_PATHS or path.startswith(_ALLOWED_PATH_PREFIXES)

    @staticmethod
    def _query_allowed(path: str, query_string: object) -> bool:
        if query_string in {b"", ""}:
            return True
        if path != "/theme.css" or not isinstance(query_string, bytes):
            return False
        digest = query_string.removeprefix(b"v=")
        return (
            query_string.startswith(b"v=") and len(digest) == 64 and set(digest) <= _LOWER_HEX_BYTES
        )

    @staticmethod
    async def _empty_response(send: Send, status: int) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-length", b"0"),
                    (b"cache-control", b"no-store"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": b"", "more_body": False})

    async def _serve_localized_root(self, scope: Scope, receive: Receive, send: Send) -> None:
        response_start: Message | None = None
        body_parts: list[bytes] = []

        async def capture(message: Message) -> None:
            nonlocal response_start
            message_type = message.get("type")
            if message_type == "http.response.start":
                response_start = dict(message)
                return
            if message_type == "http.response.body":
                body = message.get("body", b"")
                if isinstance(body, bytes):
                    body_parts.append(body)
                if message.get("more_body", False):
                    return
                await flush()
                return
            await send(message)

        async def flush() -> None:
            if response_start is None:
                raise RuntimeError("root_response_start_missing")
            body = b"".join(body_parts).replace(b'lang="en"', b'lang="zh-TW"', 1)
            headers = [
                header
                for header in response_start.get("headers", [])
                if isinstance(header, tuple) and header[0].lower() != b"content-length"
            ]
            headers.append((b"content-length", str(len(body)).encode("ascii")))
            localized_start = dict(response_start)
            localized_start["headers"] = headers
            await send(localized_start)
            await send({"type": "http.response.body", "body": body, "more_body": False})

        await self.app(scope, receive, capture)


demo = create_demo()


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=False,
        app_kwargs={"middleware": [(PublicSurfaceGuard, (), {})]},
    )
