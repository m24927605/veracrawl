"""Unit tests for s3.1 runner ↔ PriorityCrawlFrontier wiring (tests 19-21)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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
from veracrawl.contracts.crawl_planner import (
    AdapterPrior,
    FrontierPriorityHint,
    PlanDecision,
    PlannedSeed,
    PlanRequest,
)
from veracrawl.contracts.enums import (
    AdapterType,
    FrontierMatchKind,
)
from veracrawl.external_crawl.frontier import ExternalCrawlFrontier
from veracrawl.external_crawl.priority_frontier import PriorityCrawlFrontier
from veracrawl.external_crawl.runner import ExternalCrawlRunner
from veracrawl.ports.crawl_http_fetcher import FetchError


def _spec(*, seed_urls: list[str]) -> CrawlJobSpec:
    return CrawlJobSpec(
        id="spec:s3_1:1", project_id="project:s3_1",
        objective="s3.1 test",
        seed_urls=seed_urls,
        allowed_domains=["a.example", "b.example", "c.example"],
        denied_domains=[], max_depth=1, max_pages=10, max_runtime_seconds=5,
        per_origin_concurrency=1,
        rate_limit=RateLimitSpec(requests_per_minute=600, crawl_delay_seconds=0.0),
        source_adapters=[AdapterType.HTTP],
        robots_policy=RobotsPolicy.WARN,
        private_network_policy=PrivateNetworkPolicy.DENY,
        artifact_policy=ArtifactPolicySpec(
            store_raw_html=False, store_headers=False,
            store_screenshots=False, store_documents=False,
        ),
        extraction=ExtractionSpec(
            mode=ExtractionMode.DETERMINISTIC, schema_ref=None,
            exploratory_schema_allowed=False,
        ),
        output=OutputSpec(format=OutputFormat.JSONL, include_raw_refs=False,
                          include_evidence=False),
    )


@dataclass
class _FailingFetcher:
    calls: list[str] = field(default_factory=list)

    def fetch(self, url: str, *, timeout_seconds: float) -> Any:  # noqa: ARG002
        self.calls.append(url)
        raise FetchError(f"refuse: {url}")


@dataclass
class _FakeCrawlPlanner:
    decision: PlanDecision
    recorded: list[PlanRequest] = field(default_factory=list)

    def plan(self, request: PlanRequest) -> PlanDecision:
        self.recorded.append(request)
        return self.decision


def _plan_request() -> PlanRequest:
    return PlanRequest(
        id="plan-request:s3_1:1", run_ref="run:s3_1:1",
        objective_ref="objective:s3_1:1",
        seed_urls=["https://a.example/"],
        budget_ref="budget:s3_1:1",
        policy_snapshot_ref="policy-snapshot:s3_1:1",
        policy_decision_refs=["policy-decision:s3_1:1"],
        replay_config_ref="replay-config:s3_1:1",
    )


def _decision(
    *,
    seeds: list[tuple[str, float]],
    hints: list[FrontierPriorityHint] | None = None,
) -> PlanDecision:
    return PlanDecision(
        id="plan-decision:s3_1:1",
        request_ref="plan-request:s3_1:1",
        planner_adapter_ref="adapter:fake:v1",
        planned_seeds=[
            PlannedSeed(canonical_url=u, priority_score=p,
                        adapter_hint=AdapterType.HTTP,
                        rationale_ref=f"rationale:s3_1:{u}")
            for u, p in seeds
        ],
        adapter_priors=[AdapterPrior(
            adapter_type=AdapterType.HTTP, weight=1.0,
            rationale_ref="rationale:s3_1:http",
        )],
        frontier_priority_hints=hints or [],
        extraction_strategy_refs=[],
        replay_refs=["plan-request:s3_1:1", "adapter:fake:v1"],
        policy_decision_refs=["policy-decision:s3_1:1"],
    )


def _read_report(tmp_path: Path) -> dict[str, Any]:
    return json.loads(
        (tmp_path / "run-s3_1" / "reports" / "run_report.json").read_text(),
    )


# Test 19
def test_runner_uses_default_fifo_frontier_when_frontier_omitted(
    tmp_path: Path,
) -> None:
    spec = _spec(seed_urls=["https://a.example/"])
    fetcher = _FailingFetcher()
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s3_1")
    runner = ExternalCrawlRunner(
        spec=spec, store=store, run_root=store.run_root, fetcher=fetcher,
    )
    runner.run()
    # Internal type is the legacy FIFO frontier.
    assert isinstance(runner._frontier, ExternalCrawlFrontier)
    # Run still drains via FIFO order.
    _read_report(tmp_path)  # smoke: report writes


# Test 20
def test_runner_uses_injected_priority_frontier_with_planner_hints(
    tmp_path: Path,
) -> None:
    decision = _decision(
        seeds=[
            ("https://a.example/low/", 0.5),
            ("https://b.example/high/", 0.5),
        ],
        hints=[FrontierPriorityHint(
            match_kind=FrontierMatchKind.URL_PREFIX,
            match_value="https://b.example/high/",
            priority_delta=0.9,
            rationale_ref="rationale:s3_1:boost-b",
        )],
    )
    planner = _FakeCrawlPlanner(decision=decision)
    spec = _spec(seed_urls=["https://a.example/"])
    fetcher = _FailingFetcher()
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s3_1")
    priority_frontier = PriorityCrawlFrontier(
        allowed_domains=frozenset(spec.allowed_domains),
        denied_domains=frozenset(spec.denied_domains),
        max_depth=spec.max_depth, max_pages=spec.max_pages,
    )
    runner = ExternalCrawlRunner(
        spec=spec, store=store, run_root=store.run_root, fetcher=fetcher,
        planner=planner,
        plan_request_builder=lambda _s, _p: _plan_request(),
        frontier=priority_frontier,
    )
    runner.run()
    # URL_PREFIX hint should boost b.example/high/ above a.example/low/.
    assert fetcher.calls[0] == "https://b.example/high/"


# Test 21
def test_runner_calls_add_hints_after_initial_plan_via_spy(
    tmp_path: Path,
) -> None:
    """Pin add_hints invocation against a recording-spy frontier so
    the runner→frontier call is verified directly without relying on
    pop-order side effects.
    """

    decision = _decision(
        seeds=[("https://a.example/", 1.0)],
        hints=[FrontierPriorityHint(
            match_kind=FrontierMatchKind.URL_PREFIX,
            match_value="https://a.example/",
            priority_delta=0.5,
            rationale_ref="rationale:s3_1:boost",
        )],
    )

    class _SpyFrontier(PriorityCrawlFrontier):
        add_hints_calls: list[list[FrontierPriorityHint]]

        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            self.add_hints_calls = []

        def add_hints(self, new_hints: list[FrontierPriorityHint]) -> None:
            self.add_hints_calls.append(list(new_hints))
            super().add_hints(new_hints)

    spec = _spec(seed_urls=["https://a.example/"])
    fetcher = _FailingFetcher()
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s3_1")
    spy = _SpyFrontier(
        allowed_domains=frozenset(spec.allowed_domains),
        denied_domains=frozenset(spec.denied_domains),
        max_depth=spec.max_depth, max_pages=spec.max_pages,
    )
    planner = _FakeCrawlPlanner(decision=decision)
    runner = ExternalCrawlRunner(
        spec=spec, store=store, run_root=store.run_root, fetcher=fetcher,
        planner=planner,
        plan_request_builder=lambda _s, _p: _plan_request(),
        frontier=spy,
    )
    runner.run()
    # Initial plan triggered exactly one add_hints with one hint.
    assert len(spy.add_hints_calls) == 1
    assert len(spy.add_hints_calls[0]) == 1
    assert spy.add_hints_calls[0][0].match_value == "https://a.example/"
