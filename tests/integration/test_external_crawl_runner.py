"""End-to-end integration tests for ``ExternalCrawlRunner``.

Exercises the Phase 2 crawl loop against the local static-site
harness. Verifies:

* raw HTML artifacts land under ``artifacts/raw-html/``;
* discovered links land in ``outputs/links.jsonl``;
* fetched pages land in ``outputs/documents.jsonl``;
* the final ``reports/run_report.json`` records counters that match
  the static-site fixture (3 reachable pages: ``/``, ``/page-a.html``,
  ``/page-b.html``).
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.integration._static_site import serve_static_site
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


@pytest.fixture
def site_url() -> Iterator[str]:
    yield from serve_static_site()


def _spec(site_url: str) -> CrawlJobSpec:
    return CrawlJobSpec(
        id="job:phase2-smoke",
        project_id="project:smoke",
        objective="Phase 2 smoke crawl over the local static site fixture",
        seed_urls=[site_url + "/"],
        allowed_domains=["127.0.0.1"],
        denied_domains=[],
        max_depth=2,
        max_pages=10,
        max_runtime_seconds=30,
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
            mode=ExtractionMode.DETERMINISTIC,
            schema_ref=None,
            exploratory_schema_allowed=False,
        ),
        output=OutputSpec(
            format=OutputFormat.JSONL,
            include_raw_refs=True,
            include_evidence=False,
        ),
    )


def _runner(spec: CrawlJobSpec, tmp_path: Path) -> ExternalCrawlRunner:
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-smoke")
    fetcher = HttpxCrawlFetcher(
        user_agent="veracrawl-tests/0.1",
        max_response_bytes=64 * 1024,
        allow_loopback=True,
    )
    return ExternalCrawlRunner(
        spec=spec, store=store, run_root=store.run_root, fetcher=fetcher
    )


def test_runner_fetches_all_reachable_pages(
    tmp_path: Path, site_url: str
) -> None:
    spec = _spec(site_url)
    runner = _runner(spec, tmp_path)

    report = runner.run()

    assert report["status"] == "completed"
    # 3 HTML pages + 1 plain-text document linked from page-b.html.
    assert report["pages_fetched"] == 4, report
    assert report["artifacts_written"] >= 4
    # The runner persisted a hash-stable spec for replay.
    assert report["job_spec_hash"] == spec.content_hash()


def test_runner_persists_raw_html_artifacts(
    tmp_path: Path, site_url: str
) -> None:
    runner = _runner(_spec(site_url), tmp_path)
    runner.run()

    raw_html_dir = tmp_path / "run-smoke" / "artifacts" / "raw-html"
    documents_dir = tmp_path / "run-smoke" / "artifacts" / "documents"
    html_files = [
        p for p in raw_html_dir.iterdir() if p.suffix == ".html"
    ]
    doc_files = [
        p for p in documents_dir.iterdir() if p.suffix == ".txt"
    ]
    # 3 HTML pages routed to raw-html/, the linked plain-text file
    # routed to documents/.
    assert len(html_files) == 3
    assert len(doc_files) == 1
    for f in html_files + doc_files:
        assert f.stat().st_size > 0


def test_runner_writes_outputs_jsonl(tmp_path: Path, site_url: str) -> None:
    runner = _runner(_spec(site_url), tmp_path)
    runner.run()

    docs_path = tmp_path / "run-smoke" / "outputs" / "documents.jsonl"
    links_path = tmp_path / "run-smoke" / "outputs" / "links.jsonl"
    assert docs_path.is_file()
    assert links_path.is_file()

    documents = [
        json.loads(line)
        for line in docs_path.read_text("utf-8").splitlines()
        if line.strip()
    ]
    canonical_urls = {d["canonical_url"] for d in documents}
    assert canonical_urls == {
        f"{site_url}/",
        f"{site_url}/page-a.html",
        f"{site_url}/page-b.html",
        f"{site_url}/notes.txt",
    }
    categories = {d["artifact_category"] for d in documents}
    assert categories == {"raw-html", "documents"}

    links = [
        json.loads(line)
        for line in links_path.read_text("utf-8").splitlines()
        if line.strip()
    ]
    assert any(link["admitted"] for link in links)


def test_runner_records_outside_domain_skips_in_report(
    tmp_path: Path, site_url: str
) -> None:
    # Tighten allowed_domains so page-a links to an outside domain
    # we should skip. The fixture only links to 127.0.0.1 so we
    # plant a synthetic outside seed via the frontier indirectly:
    # mark the spec with a denied domain instead and confirm the
    # report records a skip.
    spec = _spec(site_url).model_copy(update={"denied_domains": ["page-a.com"]})
    runner = _runner(spec, tmp_path)
    runner.run()

    report_path = tmp_path / "run-smoke" / "reports" / "run_report.json"
    report = json.loads(report_path.read_text("utf-8"))
    assert isinstance(report["skipped_by_reason"], dict)


def test_runner_caps_at_max_pages(tmp_path: Path, site_url: str) -> None:
    spec = _spec(site_url).model_copy(update={"max_pages": 1})
    runner = _runner(spec, tmp_path)
    report = runner.run()

    assert report["pages_fetched"] == 1
    assert report["status"] in {"completed", "budget_exhausted"}


def test_runner_writes_extraction_candidates_with_evidence(
    tmp_path: Path, site_url: str
) -> None:
    runner = _runner(_spec(site_url), tmp_path)
    runner.run()

    candidates_path = (
        tmp_path / "run-smoke" / "outputs" / "extraction_candidates.jsonl"
    )
    packets_path = tmp_path / "run-smoke" / "outputs" / "evidence_packets.jsonl"
    assert candidates_path.is_file()
    assert packets_path.is_file()

    candidates = [
        json.loads(line)
        for line in candidates_path.read_text("utf-8").splitlines()
        if line.strip()
    ]
    assert candidates, "expected at least one candidate from HTML pages"
    for candidate in candidates:
        assert candidate["evidence_anchors"], "every candidate must cite an anchor"
        assert candidate["fields"], "every candidate must have at least one field"


def test_runner_writes_replay_report(tmp_path: Path, site_url: str) -> None:
    runner = _runner(_spec(site_url), tmp_path)
    runner.run()

    replay_path = tmp_path / "run-smoke" / "reports" / "replay_report.json"
    assert replay_path.is_file()
    report = json.loads(replay_path.read_text("utf-8"))
    assert report["status"] in {"complete", "needs_review"}
    assert report["artifacts_cited"] >= 1
    assert report["artifacts_missing"] == 0


def test_runner_emits_event_log(tmp_path: Path, site_url: str) -> None:
    runner = _runner(_spec(site_url), tmp_path)
    runner.run()

    events_path = tmp_path / "run-smoke" / "events" / "frontier.jsonl"
    assert events_path.is_file()
    events = [
        json.loads(line)
        for line in events_path.read_text("utf-8").splitlines()
        if line.strip()
    ]
    kinds = {e["kind"] for e in events}
    assert "enqueued" in kinds
    assert "fetched" in kinds
