"""Local static-site harness for external crawl integration tests.

Spins up :class:`http.server.ThreadingHTTPServer` on ``127.0.0.1`` with
a kernel-chosen port so tests can run in parallel. Used by Phase 1
smoke tests and (later) the Phase 2+ external-crawl integration
suite. Never reaches the public internet.
"""

from __future__ import annotations

import socket
import threading
from collections.abc import Generator
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

FIXTURE_ROOT = Path(__file__).resolve().parent.parent / "fixtures" / "static_site"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class _BoundHandler(SimpleHTTPRequestHandler):
    # Bind the directory at class scope so ThreadingHTTPServer can
    # instantiate handlers per request without the per-instance
    # ``directory=`` keyword.
    _serve_root: str = str(FIXTURE_ROOT)

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, directory=self._serve_root, **kwargs)  # type: ignore[arg-type]

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        # Silence the default access log in tests.
        return


def serve_static_site() -> Generator[str, None, None]:
    """Yield the base URL of a thread-backed static-site server.

    Resolves test fixtures from ``tests/fixtures/static_site/``. The
    server is shut down when the generator is exhausted.
    """
    port = _free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), _BoundHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5.0)


__all__ = ["FIXTURE_ROOT", "serve_static_site"]
