"""Integration tests for AIMD rate limiter wiring in the runner.

Two scenarios:

* **Pacing**: a tight ``requests_per_minute=60`` (= 1 req/sec) floor
  pairs with a multi-page fixture. The two fetches must take at
  least ~1 second total, confirming the limiter actually waited
  rather than rubber-stamping every ``acquire``.
* **Throttle feedback**: a server that returns ``503 Retry-After: 0.4``
  reduces the per-bucket rate; the next ``acquire`` must therefore
  wait at least the retry window. We use ``InMemoryAimdLimiter``
  directly for this so the AIMD cooldown is observable.
"""

from __future__ import annotations

import socket
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from tests.integration._static_site import serve_static_site
from veracrawl.adapters.network.aimd_rate_limiter import InMemoryAimdLimiter
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
from veracrawl.contracts.enums import AdapterType, RouteClass
from veracrawl.external_crawl.runner import ExternalCrawlRunner


def _spec(site_url: str, rpm: int) -> CrawlJobSpec:
    return CrawlJobSpec(
        id="job:aimd",
        project_id="project:aimd",
        objective="AIMD pacing test",
        seed_urls=[site_url + "/"],
        allowed_domains=["127.0.0.1"],
        denied_domains=[],
        max_depth=1,
        max_pages=5,
        max_runtime_seconds=30,
        per_origin_concurrency=1,
        rate_limit=RateLimitSpec(
            requests_per_minute=rpm, crawl_delay_seconds=None
        ),
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


@pytest.fixture
def site_url() -> Iterator[str]:
    yield from serve_static_site()


def test_aimd_paces_back_to_back_fetches(
    tmp_path: Path, site_url: str
) -> None:
    spec = _spec(site_url, rpm=60)  # → request_rate = (60, 60) → 1s floor
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-aimd")
    fetcher = HttpxCrawlFetcher(
        user_agent="veracrawl-tests/0.1",
        max_response_bytes=64 * 1024,
        allow_loopback=True,
    )
    limiter = InMemoryAimdLimiter()
    try:
        runner = ExternalCrawlRunner(
            spec=spec,
            store=store,
            run_root=store.run_root,
            fetcher=fetcher,
            rate_limiter=limiter,
        )
        started = time.monotonic()
        report = runner.run()
        elapsed = time.monotonic() - started
    finally:
        fetcher.close()

    # ≥3 fetches with a 1-second floor. The static-site fixture spans
    # multiple ``RouteClass`` buckets (``/`` → LISTING, ``/page-a.html``
    # → DETAIL, ``/notes.txt`` → FILE) so only same-bucket fetches pay
    # the floor — but the two DETAIL fetches (``page-a`` and
    # ``page-b``) DO collide on a bucket, so elapsed must be at least
    # the 1-second floor minus the small first-grant grace.
    assert report["pages_fetched"] >= 3
    assert elapsed >= 0.9, f"expected ≥0.9s elapsed, got {elapsed:.3f}s"


class _ThrottleHandler(BaseHTTPRequestHandler):
    """Always returns 503 with a small ``Retry-After``."""

    def do_GET(self) -> None:  # noqa: N802
        self.send_response(503)
        self.send_header("Retry-After", "0.4")
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", "9")
        self.end_headers()
        self.wfile.write(b"throttled")

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture
def throttling_server() -> Iterator[str]:
    port = _free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), _ThrottleHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5.0)


def test_aimd_reports_throttle_on_503(
    tmp_path: Path, throttling_server: str
) -> None:
    spec = _spec(throttling_server, rpm=600)  # high floor — throttle is what slows us
    spec = spec.model_copy(update={"max_pages": 1})
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-throttle")
    fetcher = HttpxCrawlFetcher(
        user_agent="veracrawl-tests/0.1",
        max_response_bytes=64 * 1024,
        allow_loopback=True,
    )
    limiter = InMemoryAimdLimiter()

    # Acquire once before the run to populate the bucket. Then run the
    # spec; the runner will call report_throttled on the 503. After the
    # run, a fresh acquire on the same bucket must observe the cooldown.
    bucket_origin = throttling_server
    with limiter.acquire(
        origin=bucket_origin,
        route_class=RouteClass.DETAIL,
        adapter_type=AdapterType.HTTP,
    ) as permit:
        limiter.report_success(permit=permit)

    try:
        runner = ExternalCrawlRunner(
            spec=spec,
            store=store,
            run_root=store.run_root,
            fetcher=fetcher,
            rate_limiter=limiter,
        )
        runner.run()
    finally:
        fetcher.close()

    # The 503 should have triggered report_throttled; the next acquire
    # waits for the cooldown (Retry-After 0.4s + jittered base).
    started = time.monotonic()
    with limiter.acquire(
        origin=bucket_origin,
        route_class=RouteClass.DETAIL,
        adapter_type=AdapterType.HTTP,
    ):
        elapsed = time.monotonic() - started
    assert elapsed >= 0.3, f"expected cooldown ≥0.3s after 503, got {elapsed:.3f}s"
