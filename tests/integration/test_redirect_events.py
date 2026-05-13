"""Integration tests for redirect lineage events.

Stands up a tiny redirect server (``/a → /b → /c``) and verifies
that each hop becomes one structured event under
``events/redirects.jsonl``. The FetchOutcome also carries a typed
``redirect_history`` so callers don't have to re-parse the URL list.
"""

from __future__ import annotations

import json
import socket
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from veracrawl.adapters.network.httpx_crawl_fetcher import HttpxCrawlFetcher
from veracrawl.adapters.object_stores.local_fs_crawl_artifact_store import (
    LocalFsCrawlArtifactStore,
)
from veracrawl.contracts.crawl_job import (
    ArtifactPolicySpec,
    CrawlJobSpec,
    ExtractionMode,
    ExtractionSpec,
    OutputFormat,
    OutputSpec,
    PrivateNetworkPolicy,
    RateLimitSpec,
    RobotsPolicy,
)
from veracrawl.contracts.enums import AdapterType
from veracrawl.external_crawl.runner import ExternalCrawlRunner


class _RedirectHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/a":
            self.send_response(302)
            self.send_header("Location", "/b")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if self.path == "/b":
            self.send_response(301)
            self.send_header("Location", "/c")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if self.path == "/c":
            body = b"<html><body><h1>Final landing</h1></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
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
def redirect_server() -> Iterator[str]:
    port = _free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), _RedirectHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5.0)


def test_fetcher_records_typed_redirect_history(redirect_server: str) -> None:
    fetcher = HttpxCrawlFetcher(
        user_agent="veracrawl-tests/0.1",
        max_response_bytes=64 * 1024,
        allow_loopback=True,
    )
    try:
        outcome = fetcher.fetch(redirect_server + "/a", timeout_seconds=5.0)
    finally:
        fetcher.close()

    # 2 hops + a final 200; redirect_history captures the two 3xx hops.
    assert outcome.status_code == 200
    assert outcome.final_url.endswith("/c")
    assert len(outcome.redirect_history) == 2
    assert outcome.redirect_history[0].from_url.endswith("/a")
    assert outcome.redirect_history[0].to_url.endswith("/b")
    assert outcome.redirect_history[0].status_code == 302
    assert outcome.redirect_history[1].from_url.endswith("/b")
    assert outcome.redirect_history[1].to_url.endswith("/c")
    assert outcome.redirect_history[1].status_code == 301


def test_runner_writes_per_hop_redirect_events(
    tmp_path: Path, redirect_server: str
) -> None:
    spec = CrawlJobSpec(
        id="job:redirect",
        project_id="project:redirect",
        objective="redirect lineage smoke test",
        seed_urls=[redirect_server + "/a"],
        allowed_domains=["127.0.0.1"],
        denied_domains=[],
        max_depth=0,
        max_pages=1,
        max_runtime_seconds=10,
        per_origin_concurrency=1,
        rate_limit=RateLimitSpec(requests_per_minute=120, crawl_delay_seconds=0.0),
        source_adapters=[AdapterType.HTTP],
        robots_policy=RobotsPolicy.WARN,
        private_network_policy=PrivateNetworkPolicy.ALLOW_LOOPBACK_ONLY,
        artifact_policy=ArtifactPolicySpec(
            store_raw_html=True,
            store_headers=True,
            store_screenshots=False,
            store_documents=False,
        ),
        extraction=ExtractionSpec(
            mode=ExtractionMode.NONE,
            schema_ref=None,
            exploratory_schema_allowed=False,
        ),
        output=OutputSpec(
            format=OutputFormat.JSONL,
            include_raw_refs=True,
            include_evidence=False,
        ),
    )
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-redirect")
    fetcher = HttpxCrawlFetcher(
        user_agent="veracrawl-tests/0.1",
        max_response_bytes=64 * 1024,
        allow_loopback=True,
    )
    try:
        runner = ExternalCrawlRunner(
            spec=spec, store=store, run_root=store.run_root, fetcher=fetcher
        )
        runner.run()
    finally:
        fetcher.close()

    redirects_path = tmp_path / "run-redirect" / "events" / "redirects.jsonl"
    assert redirects_path.is_file()
    hops = [
        json.loads(line)
        for line in redirects_path.read_text("utf-8").splitlines()
        if line.strip()
    ]
    assert len(hops) == 2
    assert hops[0]["from_url"].endswith("/a")
    assert hops[0]["to_url"].endswith("/b")
    assert hops[0]["status_code"] == 302
    assert hops[1]["from_url"].endswith("/b")
    assert hops[1]["to_url"].endswith("/c")
    assert hops[1]["status_code"] == 301


def test_runner_redirects_jsonl_empty_when_no_hops_observed(
    tmp_path: Path, redirect_server: str
) -> None:
    # Seed directly at the terminal page so no redirects happen; the
    # redirects.jsonl file must exist (deterministic layout) but
    # contain no entries.
    spec = CrawlJobSpec(
        id="job:no-redirects",
        project_id="project:no-redirects",
        objective="confirm clean run produces no spurious redirect events",
        seed_urls=[redirect_server + "/c"],
        allowed_domains=["127.0.0.1"],
        denied_domains=[],
        max_depth=0,
        max_pages=1,
        max_runtime_seconds=10,
        per_origin_concurrency=1,
        rate_limit=RateLimitSpec(requests_per_minute=120, crawl_delay_seconds=0.0),
        source_adapters=[AdapterType.HTTP],
        robots_policy=RobotsPolicy.WARN,
        private_network_policy=PrivateNetworkPolicy.ALLOW_LOOPBACK_ONLY,
        artifact_policy=ArtifactPolicySpec(
            store_raw_html=True,
            store_headers=True,
            store_screenshots=False,
            store_documents=False,
        ),
        extraction=ExtractionSpec(
            mode=ExtractionMode.NONE,
            schema_ref=None,
            exploratory_schema_allowed=False,
        ),
        output=OutputSpec(
            format=OutputFormat.JSONL,
            include_raw_refs=True,
            include_evidence=False,
        ),
    )
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-noredir")
    fetcher = HttpxCrawlFetcher(
        user_agent="veracrawl-tests/0.1",
        max_response_bytes=64 * 1024,
        allow_loopback=True,
    )
    try:
        ExternalCrawlRunner(
            spec=spec, store=store, run_root=store.run_root, fetcher=fetcher
        ).run()
    finally:
        fetcher.close()

    redirects_path = tmp_path / "run-noredir" / "events" / "redirects.jsonl"
    # File should exist (deterministic layout) but be empty.
    assert redirects_path.is_file()
    assert redirects_path.read_text("utf-8").strip() == ""
