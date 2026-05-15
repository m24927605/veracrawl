"""s3 integration test: runner + DeterministicCrawlPlanner vs httpbin.org."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from veracrawl.adapters.network.httpx_crawl_fetcher import HttpxCrawlFetcher
from veracrawl.adapters.object_stores.local_fs_crawl_artifact_store import (
    LocalFsCrawlArtifactStore,
)
from veracrawl.adapters.planning.deterministic_crawl_planner import (
    DeterministicCrawlPlanner,
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
from veracrawl.contracts.crawl_planner import PlanRequest
from veracrawl.contracts.enums import AdapterType
from veracrawl.external_crawl.runner import ExternalCrawlRunner


@pytest.mark.live
def test_runner_plans_with_deterministic_planner_against_httpbin(tmp_path: Path) -> None:
    spec = CrawlJobSpec(
        id="spec:s3:httpbin", project_id="project:s3",
        objective="s3 deterministic-planner smoke test against httpbin.org",
        seed_urls=["https://httpbin.org/links/3/0"],
        allowed_domains=["httpbin.org"], denied_domains=[],
        max_depth=1, max_pages=4, max_runtime_seconds=20,
        per_origin_concurrency=1,
        rate_limit=RateLimitSpec(requests_per_minute=60, crawl_delay_seconds=0.0),
        source_adapters=[AdapterType.HTTP], robots_policy=RobotsPolicy.WARN,
        private_network_policy=PrivateNetworkPolicy.DENY,
        artifact_policy=ArtifactPolicySpec(
            store_raw_html=True, store_headers=True,
            store_screenshots=False, store_documents=False,
        ),
        extraction=ExtractionSpec(
            mode=ExtractionMode.DETERMINISTIC, schema_ref=None,
            exploratory_schema_allowed=False,
        ),
        output=OutputSpec(format=OutputFormat.JSONL, include_raw_refs=True,
                          include_evidence=False),
    )
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s3-httpbin")
    fetcher = HttpxCrawlFetcher(user_agent="veracrawl-s3-tests/0.1",
                                 connect_timeout_seconds=5.0, read_timeout_seconds=10.0)

    def _builder(s: CrawlJobSpec, _root: Path) -> PlanRequest:
        return PlanRequest(
            id=f"plan-request:test:{s.id}", run_ref=f"run:test:{s.id}",
            objective_ref=f"objective:test:{s.id}", seed_urls=list(s.seed_urls),
            budget_ref=f"budget:test:{s.id}",
            policy_snapshot_ref=f"policy-snapshot:test:{s.id}",
            policy_decision_refs=[f"policy-decision:test:{s.id}"],
            replay_config_ref=f"replay-config:test:{s.id}",
        )

    runner = ExternalCrawlRunner(
        spec=spec, store=store, run_root=store.run_root, fetcher=fetcher,
        planner=DeterministicCrawlPlanner(), plan_request_builder=_builder,
    )
    runner.run()
    report = json.loads((store.run_root / "reports" / "run_report.json").read_text())
    assert report["plan_decision_ref"], "plan_decision_ref must be present"
    assert (store.run_root / "outputs" / "documents.jsonl").read_text().strip(), (
        "at least one document should be fetched via the planned seed"
    )
