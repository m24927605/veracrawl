"""Integration tests for the runner's robots-policy gate."""

from __future__ import annotations

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
from veracrawl.ports.robots import RobotsAdvice


class _DenyAllRobots:
    """Stub RobotsPort that disallows every URL."""

    def evaluate(self, url: str, *, user_agent: str) -> RobotsAdvice:
        return RobotsAdvice(is_allowed=False, disallow_reason="test deny")


class _AllowAllRobots:
    def evaluate(self, url: str, *, user_agent: str) -> RobotsAdvice:
        return RobotsAdvice(is_allowed=True)


@pytest.fixture
def site_url() -> Iterator[str]:
    yield from serve_static_site()


def _spec(site_url: str, robots_policy: RobotsPolicy) -> CrawlJobSpec:
    return CrawlJobSpec(
        id="job:robots",
        project_id="project:robots",
        objective="Robots gate test",
        seed_urls=[site_url + "/"],
        allowed_domains=["127.0.0.1"],
        denied_domains=[],
        max_depth=1,
        max_pages=5,
        max_runtime_seconds=15,
        per_origin_concurrency=1,
        rate_limit=RateLimitSpec(requests_per_minute=120, crawl_delay_seconds=0.0),
        source_adapters=[AdapterType.HTTP],
        robots_policy=robots_policy,
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


def _runner(spec: CrawlJobSpec, tmp_path: Path, robots_port: object) -> ExternalCrawlRunner:
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-robots")
    fetcher = HttpxCrawlFetcher(
        user_agent="veracrawl-tests/0.1",
        max_response_bytes=64 * 1024,
        allow_loopback=True,
    )
    return ExternalCrawlRunner(
        spec=spec,
        store=store,
        run_root=store.run_root,
        fetcher=fetcher,
        robots_port=robots_port,  # type: ignore[arg-type]
        user_agent="veracrawl-tests/0.1",
    )


def test_runner_obeys_robots_denial(tmp_path: Path, site_url: str) -> None:
    runner = _runner(_spec(site_url, RobotsPolicy.OBEY), tmp_path, _DenyAllRobots())
    report = runner.run()
    assert report["pages_fetched"] == 0
    assert report["skipped_by_reason"].get("robots_denied", 0) >= 1


def test_runner_warns_but_proceeds_under_warn_policy(
    tmp_path: Path, site_url: str
) -> None:
    runner = _runner(_spec(site_url, RobotsPolicy.WARN), tmp_path, _DenyAllRobots())
    report = runner.run()
    # WARN policy ignores the deny — runner proceeds and fetches.
    assert report["pages_fetched"] >= 1


def test_runner_allows_when_robots_allows(
    tmp_path: Path, site_url: str
) -> None:
    runner = _runner(_spec(site_url, RobotsPolicy.OBEY), tmp_path, _AllowAllRobots())
    report = runner.run()
    assert report["pages_fetched"] >= 1
    assert report["skipped_by_reason"].get("robots_denied", 0) == 0
