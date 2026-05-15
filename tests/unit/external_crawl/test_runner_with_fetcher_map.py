"""Unit tests for s3.2 runner ↔ fetcher_map wiring (tests 10-14f)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

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
    PlanDecision,
    PlannedSeed,
    PlanRequest,
)
from veracrawl.contracts.enums import AdapterType
from veracrawl.external_crawl.runner import ExternalCrawlRunner
from veracrawl.ports.crawl_http_fetcher import FetchError, FetchOutcome


def _spec(
    *,
    seed_urls: list[str],
    source_adapters: list[AdapterType] | None = None,
) -> CrawlJobSpec:
    return CrawlJobSpec(
        id="spec:s3_2:1", project_id="project:s3_2",
        objective="s3.2 test",
        seed_urls=seed_urls,
        allowed_domains=["a.example", "b.example"],
        denied_domains=[], max_depth=1, max_pages=10, max_runtime_seconds=5,
        per_origin_concurrency=1,
        rate_limit=RateLimitSpec(requests_per_minute=600, crawl_delay_seconds=0.0),
        source_adapters=source_adapters or [
            AdapterType.HTTP, AdapterType.BROWSER_SNAPSHOT,
        ],
        robots_policy=RobotsPolicy.WARN,
        private_network_policy=PrivateNetworkPolicy.DENY,
        artifact_policy=ArtifactPolicySpec(
            store_raw_html=False, store_headers=False,
            # BROWSER_SNAPSHOT in source_adapters requires this.
            store_screenshots=True, store_documents=False,
        ),
        extraction=ExtractionSpec(
            mode=ExtractionMode.DETERMINISTIC, schema_ref=None,
            exploratory_schema_allowed=False,
        ),
        output=OutputSpec(format=OutputFormat.JSONL, include_raw_refs=False,
                          include_evidence=False),
    )


@dataclass
class _SpyFetcher:
    label: str
    calls: list[str] = field(default_factory=list)
    fail: bool = True

    def fetch(self, url: str, *, timeout_seconds: float) -> FetchOutcome:  # noqa: ARG002
        self.calls.append(url)
        if self.fail:
            raise FetchError(f"{self.label} refuses {url}")
        return FetchOutcome(
            requested_url=url, final_url=url, status_code=200,
            headers={}, body=b"", content_type="text/html",
        )


@dataclass
class _FakeCrawlPlanner:
    decision: PlanDecision

    def plan(self, request: PlanRequest) -> PlanDecision:  # noqa: ARG002
        return self.decision


def _plan_request() -> PlanRequest:
    return PlanRequest(
        id="plan-request:s3_2:1", run_ref="run:s3_2:1",
        objective_ref="objective:s3_2:1",
        seed_urls=["https://a.example/"],
        budget_ref="budget:s3_2:1",
        policy_snapshot_ref="policy-snapshot:s3_2:1",
        policy_decision_refs=["policy-decision:s3_2:1"],
        replay_config_ref="replay-config:s3_2:1",
    )


def _decision(
    *,
    seeds: list[tuple[str, float]],
    priors: list[AdapterPrior],
) -> PlanDecision:
    return PlanDecision(
        id="plan-decision:s3_2:1",
        request_ref="plan-request:s3_2:1",
        planner_adapter_ref="adapter:fake:v1",
        planned_seeds=[
            PlannedSeed(canonical_url=u, priority_score=p,
                        adapter_hint=AdapterType.HTTP,
                        rationale_ref=f"rationale:s3_2:{u}")
            for u, p in seeds
        ],
        adapter_priors=priors,
        frontier_priority_hints=[],
        extraction_strategy_refs=[],
        replay_refs=["plan-request:s3_2:1", "adapter:fake:v1"],
        policy_decision_refs=["policy-decision:s3_2:1"],
    )


def _report(tmp_path: Path) -> dict[str, Any]:
    return json.loads(
        (tmp_path / "run-s3_2" / "reports" / "run_report.json").read_text(),
    )


# Test 10
def test_runner_uses_default_fetcher_when_map_omitted(tmp_path: Path) -> None:
    fetcher = _SpyFetcher(label="default")
    spec = _spec(seed_urls=["https://a.example/"])
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s3_2")
    runner = ExternalCrawlRunner(
        spec=spec, store=store, run_root=store.run_root, fetcher=fetcher,
    )
    runner.run()
    assert fetcher.calls == ["https://a.example/"]
    # Legacy mode → s3.2 fields keyed but null.
    rep = _report(tmp_path)
    assert rep["replay_seed_ref"] is None
    assert rep["adapter_dispatch_choices"] is None


# Test 11
def test_runner_dispatches_via_fetcher_map_when_set(tmp_path: Path) -> None:
    http = _SpyFetcher(label="http")
    browser = _SpyFetcher(label="browser")
    spec = _spec(seed_urls=["https://a.example/"])
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s3_2")
    decision = _decision(
        seeds=[
            ("https://a.example/1", 1.0),
            ("https://a.example/2", 0.9),
            ("https://b.example/1", 0.8),
        ],
        priors=[
            AdapterPrior(adapter_type=AdapterType.HTTP, weight=0.5,
                         rationale_ref="r:http"),
            AdapterPrior(adapter_type=AdapterType.BROWSER_SNAPSHOT, weight=0.5,
                         rationale_ref="r:browser"),
        ],
    )
    runner = ExternalCrawlRunner(
        spec=spec, store=store, run_root=store.run_root, fetcher=http,
        planner=_FakeCrawlPlanner(decision=decision),
        plan_request_builder=lambda _s, _p: _plan_request(),
        fetcher_map={
            AdapterType.HTTP: http,
            AdapterType.BROWSER_SNAPSHOT: browser,
        },
        replay_seed_ref="seed:s3_2:run-1",
    )
    runner.run()
    # Every URL went through ONE of the spies; sum of calls = seed count.
    assert len(http.calls) + len(browser.calls) == 3


# Test 12
def test_run_report_contains_adapter_dispatch_choices(tmp_path: Path) -> None:
    http = _SpyFetcher(label="http")
    spec = _spec(seed_urls=["https://a.example/"])
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s3_2")
    decision = _decision(
        seeds=[("https://a.example/1", 1.0)],
        priors=[AdapterPrior(adapter_type=AdapterType.HTTP, weight=1.0,
                             rationale_ref="r:http")],
    )
    runner = ExternalCrawlRunner(
        spec=spec, store=store, run_root=store.run_root, fetcher=http,
        planner=_FakeCrawlPlanner(decision=decision),
        plan_request_builder=lambda _s, _p: _plan_request(),
        fetcher_map={AdapterType.HTTP: http},
        replay_seed_ref="seed:s3_2:run-12",
    )
    runner.run()
    rep = _report(tmp_path)
    assert rep["adapter_dispatch_choices"] == {"https://a.example/1": "http"}


# Test 13
def test_run_report_contains_replay_seed_ref(tmp_path: Path) -> None:
    http = _SpyFetcher(label="http")
    spec = _spec(seed_urls=["https://a.example/"])
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s3_2")
    decision = _decision(
        seeds=[("https://a.example/1", 1.0)],
        priors=[AdapterPrior(adapter_type=AdapterType.HTTP, weight=1.0,
                             rationale_ref="r:http")],
    )
    runner = ExternalCrawlRunner(
        spec=spec, store=store, run_root=store.run_root, fetcher=http,
        planner=_FakeCrawlPlanner(decision=decision),
        plan_request_builder=lambda _s, _p: _plan_request(),
        fetcher_map={AdapterType.HTTP: http},
        replay_seed_ref="seed:s3_2:run-13",
    )
    runner.run()
    rep = _report(tmp_path)
    assert rep["replay_seed_ref"] == "seed:s3_2:run-13"


# Test 14
def test_two_runs_with_same_seed_produce_byte_equal_dispatch_choices(
    tmp_path: Path,
) -> None:
    def _run(run_id: str) -> dict[str, Any]:
        http = _SpyFetcher(label="http")
        browser = _SpyFetcher(label="browser")
        spec = _spec(seed_urls=["https://a.example/"])
        store = LocalFsCrawlArtifactStore(root=tmp_path, run_id=run_id)
        decision = _decision(
            seeds=[
                ("https://a.example/1", 1.0),
                ("https://a.example/2", 0.9),
                ("https://a.example/3", 0.8),
            ],
            priors=[
                AdapterPrior(adapter_type=AdapterType.HTTP, weight=0.5,
                             rationale_ref="r:http"),
                AdapterPrior(adapter_type=AdapterType.BROWSER_SNAPSHOT,
                             weight=0.5, rationale_ref="r:browser"),
            ],
        )
        runner = ExternalCrawlRunner(
            spec=spec, store=store, run_root=store.run_root, fetcher=http,
            planner=_FakeCrawlPlanner(decision=decision),
            plan_request_builder=lambda _s, _p: _plan_request(),
            fetcher_map={
                AdapterType.HTTP: http,
                AdapterType.BROWSER_SNAPSHOT: browser,
            },
            replay_seed_ref="seed:s3_2:replay-invariant",
        )
        runner.run()
        return json.loads(
            (tmp_path / run_id / "reports" / "run_report.json").read_text(),
        )["adapter_dispatch_choices"]

    a = _run("run-s3_2-a")
    b = _run("run-s3_2-b")
    assert a == b


# Test 14c
def test_runner_rejects_fetcher_map_without_replay_seed_ref(
    tmp_path: Path,
) -> None:
    http = _SpyFetcher(label="http")
    spec = _spec(seed_urls=["https://a.example/"])
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s3_2")
    decision = _decision(
        seeds=[("https://a.example/", 1.0)],
        priors=[AdapterPrior(adapter_type=AdapterType.HTTP, weight=1.0,
                             rationale_ref="r:http")],
    )
    with pytest.raises(ValueError, match="replay_seed_ref"):
        ExternalCrawlRunner(
            spec=spec, store=store, run_root=store.run_root, fetcher=http,
            planner=_FakeCrawlPlanner(decision=decision),
            plan_request_builder=lambda _s, _p: _plan_request(),
            fetcher_map={AdapterType.HTTP: http},
            replay_seed_ref=None,
        )


# Test 14d
def test_runner_rejects_replay_seed_ref_without_fetcher_map(
    tmp_path: Path,
) -> None:
    http = _SpyFetcher(label="http")
    spec = _spec(seed_urls=["https://a.example/"])
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s3_2")
    decision = _decision(
        seeds=[("https://a.example/", 1.0)],
        priors=[AdapterPrior(adapter_type=AdapterType.HTTP, weight=1.0,
                             rationale_ref="r:http")],
    )
    with pytest.raises(ValueError, match="fetcher_map"):
        ExternalCrawlRunner(
            spec=spec, store=store, run_root=store.run_root, fetcher=http,
            planner=_FakeCrawlPlanner(decision=decision),
            plan_request_builder=lambda _s, _p: _plan_request(),
            fetcher_map=None,
            replay_seed_ref="seed:no-map",
        )


# Test 14e (helper-level — pinned in test_dispatch.py; here we verify
# the runner threads spec.source_adapters into _choose_fetcher).
def test_runner_does_not_call_unauthorized_adapter_fetcher(
    tmp_path: Path,
) -> None:
    http = _SpyFetcher(label="http")
    browser = _SpyFetcher(label="browser")
    spec = _spec(
        seed_urls=["https://a.example/"],
        source_adapters=[AdapterType.HTTP],  # browser NOT authorized
    )
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s3_2")
    decision = _decision(
        seeds=[("https://a.example/1", 1.0),
               ("https://a.example/2", 0.9)],
        priors=[
            AdapterPrior(adapter_type=AdapterType.HTTP, weight=0.5,
                         rationale_ref="r:http"),
            AdapterPrior(adapter_type=AdapterType.BROWSER_SNAPSHOT, weight=0.5,
                         rationale_ref="r:browser"),
        ],
    )
    runner = ExternalCrawlRunner(
        spec=spec, store=store, run_root=store.run_root, fetcher=http,
        planner=_FakeCrawlPlanner(decision=decision),
        plan_request_builder=lambda _s, _p: _plan_request(),
        fetcher_map={
            AdapterType.HTTP: http,
            AdapterType.BROWSER_SNAPSHOT: browser,
        },
        replay_seed_ref="seed:s3_2:unauthorized",
    )
    runner.run()
    assert browser.calls == []
    # All fetched URLs went through HTTP (the only authorized adapter).
    assert len(http.calls) == 2
