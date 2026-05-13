"""Integration test: redirect lineage propagates into NormalizedDocumentAnchor.

When the seed URL 302→ another path, the resulting document's anchor
must carry the redirect chain so replay tooling can reconstruct the
lineage without joining ``events/redirects.jsonl``.
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


class _RedirectThenHtmlHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/start":
            self.send_response(302)
            self.send_header("Location", "/landing")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if self.path == "/landing":
            body = (
                b"<html><body><h1>Landed</h1></body></html>"
            )
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
def site() -> Iterator[str]:
    port = _free_port()
    server = ThreadingHTTPServer(
        ("127.0.0.1", port), _RedirectThenHtmlHandler
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5.0)


def test_anchor_carries_redirect_chain(tmp_path: Path, site: str) -> None:
    spec = CrawlJobSpec(
        id="job:redirect-anchor",
        project_id="project:redirect-anchor",
        objective="redirect lineage on anchor",
        seed_urls=[site + "/start"],
        allowed_domains=["127.0.0.1"],
        denied_domains=[],
        max_depth=0,
        max_pages=1,
        max_runtime_seconds=10,
        per_origin_concurrency=1,
        rate_limit=RateLimitSpec(
            requests_per_minute=120, crawl_delay_seconds=0.0
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
            mode=ExtractionMode.DETERMINISTIC,
            schema_ref=None,
            exploratory_schema_allowed=False,
        ),
        output=OutputSpec(
            format=OutputFormat.JSONL,
            include_raw_refs=True,
            include_evidence=True,
        ),
    )
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-redir-anchor")
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

    norm_path = (
        tmp_path / "run-redir-anchor" / "outputs" / "normalized_documents.jsonl"
    )
    records = [
        json.loads(line)
        for line in norm_path.read_text("utf-8").splitlines()
        if line.strip()
    ]
    assert records, "expected one normalized document"
    anchors = records[0]["anchors"]
    assert anchors, "document has no anchors"
    lineage = anchors[0]["redirect_lineage"]
    # Lineage covers the 3xx hop's from_url plus the final URL.
    assert any(url.endswith("/start") for url in lineage), lineage
    assert any(url.endswith("/landing") for url in lineage), lineage

    # Candidate evidence anchors must carry the lineage too so replay
    # can verify each cited span back to the redirect source.
    cands_path = (
        tmp_path / "run-redir-anchor" / "outputs" / "extraction_candidates.jsonl"
    )
    cands = [
        json.loads(line)
        for line in cands_path.read_text("utf-8").splitlines()
        if line.strip()
    ]
    if cands:
        assert cands[0]["evidence_anchors"][0]["redirect_lineage"], (
            "candidate anchors must inherit redirect lineage"
        )


def test_non_redirected_fetch_has_single_entry_lineage(
    tmp_path: Path, site: str
) -> None:
    # Seed directly at /landing — no redirect. Lineage should be just
    # the final URL.
    spec = CrawlJobSpec(
        id="job:no-redir-anchor",
        project_id="project:no-redir-anchor",
        objective="no redirect → singleton lineage",
        seed_urls=[site + "/landing"],
        allowed_domains=["127.0.0.1"],
        denied_domains=[],
        max_depth=0,
        max_pages=1,
        max_runtime_seconds=10,
        per_origin_concurrency=1,
        rate_limit=RateLimitSpec(
            requests_per_minute=120, crawl_delay_seconds=0.0
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
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-singleton")
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

    norm_path = tmp_path / "run-singleton" / "outputs" / "normalized_documents.jsonl"
    records = [
        json.loads(line)
        for line in norm_path.read_text("utf-8").splitlines()
        if line.strip()
    ]
    lineage = records[0]["anchors"][0]["redirect_lineage"]
    assert len(lineage) == 1
    assert lineage[0].endswith("/landing")
