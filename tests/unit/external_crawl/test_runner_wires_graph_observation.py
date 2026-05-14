"""Unit tests for s6 runner-wires-graph-observation (tests 1-1a, 2-4e).

Step-2 scope: ctor validation across three modes (legacy / s3 / s6)
plus the s3-pair-only regression test. Event recording + replan
trigger tests land in step 3 / step 4.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
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
from veracrawl.contracts.crawl_planner import PlanRequest
from veracrawl.contracts.enums import AdapterType
from veracrawl.contracts.planner_observation_feedback import PlannerObservationFeedback
from veracrawl.external_crawl.runner import ExternalCrawlRunner
from veracrawl.ports.crawl_http_fetcher import FetchError


def _spec() -> CrawlJobSpec:
    return CrawlJobSpec(
        id="spec:s6:1", project_id="project:s6",
        objective="s6 wiring test",
        seed_urls=["https://a.example/"],
        allowed_domains=["a.example"], denied_domains=[],
        max_depth=1, max_pages=10, max_runtime_seconds=5,
        per_origin_concurrency=1,
        rate_limit=RateLimitSpec(requests_per_minute=600, crawl_delay_seconds=0.0),
        source_adapters=[AdapterType.HTTP], robots_policy=RobotsPolicy.WARN,
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


class _FailingFetcher:
    def fetch(self, url: str, *, timeout_seconds: float) -> Any:  # noqa: ARG002
        raise FetchError(f"fake refuses {url}")


class _FakeObserver:
    def record_url_observed(self, event: Any) -> None: ...
    def record_redirect_observed(self, event: Any) -> None: ...
    def record_canonical_observed(self, event: Any) -> None: ...
    def record_page_structure_observed(self, event: Any) -> None: ...
    def snapshot(self, *, id: str, snapshot_at: datetime) -> Any:  # noqa: A002
        raise NotImplementedError


class _FakePlanner:
    def plan(self, request: PlanRequest) -> Any:
        raise NotImplementedError


def _builder(spec: CrawlJobSpec, run_root: Path) -> PlanRequest:  # noqa: ARG001
    return PlanRequest(
        id="plan-req:1", run_ref="run:test:1", objective_ref="objective:1",
        seed_urls=["https://a.example/"], budget_ref="budget:1",
        policy_snapshot_ref="policy-snap:1",
        policy_decision_refs=["policy-decision:1"],
        replay_config_ref="replay-config:1",
    )


def _factory(_fb: PlannerObservationFeedback) -> _FakePlanner:
    return _FakePlanner()


def _utc() -> datetime:
    return datetime(2026, 5, 14, 12, 0, tzinfo=UTC)


def _build(tmp_path: Path, **kwargs: Any) -> ExternalCrawlRunner:
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s6")
    return ExternalCrawlRunner(
        spec=_spec(), store=store, run_root=store.run_root,
        fetcher=_FailingFetcher(), **kwargs,
    )


def _read_report(tmp_path: Path) -> dict[str, Any]:
    return json.loads((tmp_path / "run-s6" / "reports" / "run_report.json").read_text())


# Test 1
def test_legacy_mode_unchanged_by_s6(tmp_path: Path) -> None:
    runner = _build(tmp_path)
    runner.run()
    report = _read_report(tmp_path)
    # No s6 mode keys with non-None values
    for key in (
        "plan_decision_2_ref", "plan_decision_2_replay_refs",
        "plan_decision_2_planned_seed_order", "plan_decision_2_adapter_priors",
        "plan_decision_2_frontier_priority_hints",
        "plan_decision_2_extraction_strategy_refs",
        "observation_snapshot_ref", "observation_feedback_ref",
        "utc_clock_ref", "clock_trace",
    ):
        assert report.get(key) is None, f"legacy mode must leave {key} unset"
    assert report.get("replan_invoked", False) is False
    # And no s3 mode keys either
    assert "plan_decision_ref" not in report


# Test 1a
def test_s3_pair_only_mode_unchanged_by_s6(tmp_path: Path) -> None:
    fake_planner = _FakePlanner()
    runner = _build(tmp_path, planner=fake_planner, plan_request_builder=_builder)
    # FakePlanner.plan raises NotImplementedError; we use a real ValueError-raising
    # planner setup so that the runner falls through the catch path. For this
    # regression test, what matters is that no s6 keys are populated.
    # Replace _FakePlanner with a planner that returns a minimal valid decision.
    from veracrawl.contracts.crawl_planner import (
        AdapterPrior,
        PlanDecision,
        PlannedSeed,
    )

    class _MinimalPlanner:
        def plan(self, request: Any) -> PlanDecision:
            return PlanDecision(
                id="plan-decision:s3-only:1", request_ref=request.id,
                planner_adapter_ref="adapter:test-minimal:v1",
                planned_seeds=[PlannedSeed(
                    canonical_url="https://a.example/", priority_score=1.0,
                    adapter_hint=AdapterType.HTTP, rationale_ref="rationale:test",
                )],
                adapter_priors=[AdapterPrior(
                    adapter_type=AdapterType.HTTP, weight=1.0,
                    rationale_ref="rationale:test:http",
                )],
                replay_refs=[request.id, "adapter:test-minimal:v1"],
                policy_decision_refs=["policy-decision:1"],
            )

    runner = _build(tmp_path, planner=_MinimalPlanner(), plan_request_builder=_builder)
    runner.run()
    report = _read_report(tmp_path)
    # s3 keys present (plan ran)
    assert report.get("plan_decision_ref") == "plan-decision:s3-only:1"
    # s6 keys absent or None
    for key in (
        "plan_decision_2_ref", "plan_decision_2_replay_refs",
        "observation_snapshot_ref", "observation_feedback_ref",
        "utc_clock_ref", "clock_trace",
    ):
        assert report.get(key) is None, f"s3 mode must leave {key} unset"
    assert report.get("replan_invoked", False) is False


# Test 2: graph_observer set, factory + utc_clock + utc_clock_ref missing
def test_partial_ctor_args_raise_value_error_observer_only(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"feedback_aware_planner_factory"):
        _build(
            tmp_path,
            planner=_FakePlanner(),
            plan_request_builder=_builder,
            graph_observer=_FakeObserver(),
        )


# Test 3: factory set, others missing
def test_partial_ctor_args_raise_value_error_factory_only(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"graph_observer"):
        _build(
            tmp_path,
            planner=_FakePlanner(),
            plan_request_builder=_builder,
            feedback_aware_planner_factory=_factory,
        )


# Test 4: observer + factory + utc_clock + utc_clock_ref set BUT s3 pair missing
def test_partial_ctor_args_raise_value_error_observer_without_s3_pair(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"require the s3 pair"):
        _build(
            tmp_path,
            utc_clock=_utc, utc_clock_ref="utc-clock:test",
            graph_observer=_FakeObserver(),
            feedback_aware_planner_factory=_factory,
        )


# Test 4a: utc_clock set, others missing (with s3 pair set)
def test_partial_ctor_args_raise_value_error_utc_clock_only(tmp_path: Path) -> None:
    with pytest.raises(
        ValueError,
        match=r"utc_clock.*graph_observer.*feedback_aware_planner_factory",
    ):
        _build(
            tmp_path,
            planner=_FakePlanner(), plan_request_builder=_builder,
            utc_clock=_utc,
        )


# Test 4b: observer + factory set, utc_clock + utc_clock_ref missing
def test_partial_ctor_args_raise_value_error_observer_factory_without_utc_clock(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match=r"utc_clock"):
        _build(
            tmp_path,
            planner=_FakePlanner(), plan_request_builder=_builder,
            graph_observer=_FakeObserver(),
            feedback_aware_planner_factory=_factory,
        )


# Test 4c: utc_clock + observer set, factory + utc_clock_ref missing
def test_partial_ctor_args_raise_value_error_utc_clock_observer_without_factory(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match=r"feedback_aware_planner_factory"):
        _build(
            tmp_path,
            planner=_FakePlanner(), plan_request_builder=_builder,
            utc_clock=_utc,
            graph_observer=_FakeObserver(),
        )


# Test 4d: utc_clock_ref blank or None (with all else legal)
def test_partial_ctor_args_raise_value_error_utc_clock_ref_blank_or_missing(
    tmp_path: Path,
) -> None:
    # (a) blank string
    with pytest.raises(ValueError, match="utc_clock_ref must be non-blank"):
        _build(
            tmp_path,
            planner=_FakePlanner(), plan_request_builder=_builder,
            utc_clock=_utc, utc_clock_ref="",
            graph_observer=_FakeObserver(),
            feedback_aware_planner_factory=_factory,
        )
    # (b) None (with utc_clock set — the partial rule trips first)
    with pytest.raises(ValueError, match="partial s3/s6 ctor args"):
        _build(
            tmp_path,
            planner=_FakePlanner(), plan_request_builder=_builder,
            utc_clock=_utc, utc_clock_ref=None,
            graph_observer=_FakeObserver(),
            feedback_aware_planner_factory=_factory,
        )


# Test 4e: utc_clock_ref set but utc_clock None
def test_partial_ctor_args_raise_value_error_utc_clock_ref_without_utc_clock(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match=r"utc_clock"):
        _build(
            tmp_path,
            planner=_FakePlanner(), plan_request_builder=_builder,
            utc_clock_ref="utc-clock:test",
            graph_observer=_FakeObserver(),
            feedback_aware_planner_factory=_factory,
        )


# s6 mode happy path
def test_s6_mode_accepts_full_arg_set(tmp_path: Path) -> None:
    runner = _build(
        tmp_path,
        planner=_FakePlanner(), plan_request_builder=_builder,
        utc_clock=_utc, utc_clock_ref="utc-clock:test",
        graph_observer=_FakeObserver(),
        feedback_aware_planner_factory=_factory,
    )
    assert runner is not None
