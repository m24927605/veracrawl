"""Unit tests for s6 runner-wires-graph-observation (tests 1-1a, 2-4e).

Step-2 scope: ctor validation across three modes (legacy / s3 / s6)
plus the s3-pair-only regression test. Event recording + replan
trigger tests land in step 3 / step 4.
"""

from __future__ import annotations

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


# Test 1
def test_legacy_mode_accepts_no_s3_or_s6_args(tmp_path: Path) -> None:
    runner = _build(tmp_path)
    assert runner is not None


# Test 1a
def test_s3_pair_only_mode_accepts_s3_args_without_s6(tmp_path: Path) -> None:
    runner = _build(tmp_path, planner=_FakePlanner(), plan_request_builder=_builder)
    assert runner is not None


# Test 2: graph_observer set, factory + utc_clock + utc_clock_ref missing
def test_partial_ctor_args_raise_value_error_observer_only(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="partial s3/s6 ctor args"):
        _build(
            tmp_path,
            planner=_FakePlanner(),
            plan_request_builder=_builder,
            graph_observer=_FakeObserver(),
        )


# Test 3: factory set, others missing
def test_partial_ctor_args_raise_value_error_factory_only(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="partial s3/s6 ctor args"):
        _build(
            tmp_path,
            planner=_FakePlanner(),
            plan_request_builder=_builder,
            feedback_aware_planner_factory=_factory,
        )


# Test 4: observer + factory + utc_clock + utc_clock_ref set BUT s3 pair missing
def test_partial_ctor_args_raise_value_error_observer_without_s3_pair(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="require the s3 pair"):
        _build(
            tmp_path,
            utc_clock=_utc, utc_clock_ref="utc-clock:test",
            graph_observer=_FakeObserver(),
            feedback_aware_planner_factory=_factory,
        )


# Test 4a: utc_clock set, others missing (with s3 pair set)
def test_partial_ctor_args_raise_value_error_utc_clock_only(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="partial s3/s6 ctor args"):
        _build(
            tmp_path,
            planner=_FakePlanner(), plan_request_builder=_builder,
            utc_clock=_utc,
        )


# Test 4b: observer + factory set, utc_clock + utc_clock_ref missing
def test_partial_ctor_args_raise_value_error_observer_factory_without_utc_clock(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="partial s3/s6 ctor args"):
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
    with pytest.raises(ValueError, match="partial s3/s6 ctor args"):
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
    with pytest.raises(ValueError, match="partial s3/s6 ctor args"):
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
