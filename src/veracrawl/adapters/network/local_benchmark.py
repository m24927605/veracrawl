"""Deterministic local HTTP benchmark server for network fixtures."""

from __future__ import annotations

import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import TracebackType
from typing import cast


class _BenchmarkHandler(BaseHTTPRequestHandler):
    server_version = "VeraCrawlBenchmark/1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, status: int, body: str, *, content_type: str = "text/html") -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(encoded)

    def do_GET(self) -> None:
        if self.path == "/static/basic":
            self._send(
                200,
                "<!doctype html><html><head><title>VeraCrawl Fixture</title></head>"
                "<body><main><h1>Static fixture</h1><a href='/static/detail'>Detail</a>"
                "</main></body></html>",
            )
            return
        if self.path == "/static/detail":
            self._send(200, "<html><body><article>Detail page</article></body></html>")
            return
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/static/basic")
            self.end_headers()
            return
        if self.path == "/redirect-denied":
            self.send_response(302)
            self.send_header("Location", "http://example.invalid/denied")
            self.end_headers()
            return
        if self.path == "/robots.txt":
            self._send(
                200,
                "User-agent: *\nDisallow: /robots-blocked\n",
                content_type="text/plain",
            )
            return
        if self.path == "/robots-blocked":
            self._send(200, "<html><body>Robots blocked fixture</body></html>")
            return
        if self.path == "/oversize":
            self._send(200, "<html><body>" + ("x" * 4096) + "</body></html>")
            return
        if self.path == "/slow":
            time.sleep(0.05)
            self._send(200, "<html><body>Slow fixture</body></html>")
            return
        if self.path == "/browser":
            self._send(
                200,
                "<html><body><div id='app'>Browser observation fixture</div>"
                "<script>window.__veracrawl_ready = true;</script></body></html>",
            )
            return
        self._send(404, "<html><body>Not found</body></html>")


class LocalBenchmarkServer:
    def __init__(self) -> None:
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _BenchmarkHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def origin(self) -> str:
        host, port = cast(tuple[str, int], self._server.server_address)
        return f"http://{host}:{port}"

    def __enter__(self) -> LocalBenchmarkServer:
        self._thread.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=1)
