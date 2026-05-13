"""Cookie-persistence integration test for :class:`HttpxCrawlFetcher`.

Spins up a tiny session-cookie server: ``GET /set`` sends a cookie,
``GET /check`` returns ``200`` only if the cookie comes back. Two
sequential fetches on a single :class:`HttpxCrawlFetcher` must
therefore see the cookie persist via the underlying ``httpx.Client``.
"""

from __future__ import annotations

import socket
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from veracrawl.adapters.network.httpx_crawl_fetcher import HttpxCrawlFetcher


class _CookieHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/set":
            self.send_response(200)
            self.send_header("Set-Cookie", "session=abc; Path=/")
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"set")
            return
        if self.path == "/check":
            cookie_header = self.headers.get("Cookie", "")
            if "session=abc" in cookie_header:
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"ok")
            else:
                self.send_response(401)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"missing")
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture
def cookie_server() -> Iterator[str]:
    port = _free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), _CookieHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5.0)


def test_cookies_persist_across_fetches(cookie_server: str) -> None:
    with HttpxCrawlFetcher(
        user_agent="veracrawl-tests/0.1",
        max_response_bytes=64 * 1024,
        allow_loopback=True,
    ) as fetcher:
        set_outcome = fetcher.fetch(cookie_server + "/set", timeout_seconds=5.0)
        assert set_outcome.status_code == 200

        check_outcome = fetcher.fetch(cookie_server + "/check", timeout_seconds=5.0)
        assert check_outcome.status_code == 200
        assert check_outcome.body == b"ok"


def test_fresh_fetcher_does_not_carry_cookies(cookie_server: str) -> None:
    fetcher_a = HttpxCrawlFetcher(
        user_agent="veracrawl-tests/0.1",
        max_response_bytes=64 * 1024,
        allow_loopback=True,
    )
    try:
        fetcher_a.fetch(cookie_server + "/set", timeout_seconds=5.0)
    finally:
        fetcher_a.close()

    fetcher_b = HttpxCrawlFetcher(
        user_agent="veracrawl-tests/0.1",
        max_response_bytes=64 * 1024,
        allow_loopback=True,
    )
    try:
        check_outcome = fetcher_b.fetch(
            cookie_server + "/check", timeout_seconds=5.0
        )
        assert check_outcome.status_code == 401, (
            "a fresh fetcher must not inherit cookies from a prior instance"
        )
    finally:
        fetcher_b.close()
