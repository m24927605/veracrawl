"""Unit tests for s6 runner-wires-graph-observation (tests 1-1a, 2-4e).

Step-2 scope: ctor validation across three modes (legacy / s3 / s6)
plus the s3-pair-only regression test. Event recording + replan
trigger tests land in step 3 / step 4.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
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
from veracrawl.contracts.crawl_planner import (
    AdapterPrior,
    PlanDecision,
    PlannedSeed,
    PlanRequest,
)
from veracrawl.contracts.enums import AdapterType
from veracrawl.contracts.planner_observation_feedback import PlannerObservationFeedback
from veracrawl.external_crawl.runner import ExternalCrawlRunner
from veracrawl.ports.crawl_http_fetcher import FetchError, FetchOutcome, RedirectHop


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


@dataclass
class _CapturingObserver:
    url_events: list[Any] = field(default_factory=list)
    redirect_events: list[Any] = field(default_factory=list)
    canonical_events: list[Any] = field(default_factory=list)
    page_events: list[Any] = field(default_factory=list)

    def record_url_observed(self, event: Any) -> None:
        self.url_events.append(event)

    def record_redirect_observed(self, event: Any) -> None:
        self.redirect_events.append(event)

    def record_canonical_observed(self, event: Any) -> None:
        self.canonical_events.append(event)

    def record_page_structure_observed(self, event: Any) -> None:
        self.page_events.append(event)

    def snapshot(self, *, id: str, snapshot_at: datetime) -> Any:  # noqa: A002, ARG002
        raise NotImplementedError


# Back-compat alias: prior tests imported _FakeObserver. The capturing
# observer is a drop-in superset (also satisfies the no-op contract).
_FakeObserver = _CapturingObserver


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


_S6_KEYED_ALWAYS = (
    "plan_decision_2_ref", "plan_decision_2_replay_refs",
    "plan_decision_2_planned_seed_order", "plan_decision_2_adapter_priors",
    "plan_decision_2_frontier_priority_hints",
    "plan_decision_2_extraction_strategy_refs",
    "observation_snapshot_ref", "observation_feedback_ref",
    "utc_clock_ref", "clock_trace",
)


# Test 1
def test_legacy_mode_unchanged_by_s6(tmp_path: Path) -> None:
    runner = _build(tmp_path)
    runner.run()
    report = _read_report(tmp_path)
    # Per plan: s6 keys are "keyed always" — present in the JSON shape
    # regardless of mode, with None values in legacy/s3 mode.
    for key in _S6_KEYED_ALWAYS:
        assert key in report, f"key '{key}' must be present in legacy mode"
        assert report[key] is None, f"key '{key}' must be None in legacy mode"
    assert "replan_invoked" in report
    assert report["replan_invoked"] is False
    # And no s3 mode keys either (legacy mode doesn't run the planner)
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
    # All 6 s3 keys present (plan ran)
    for key in (
        "plan_decision_ref", "plan_decision_replay_refs",
        "plan_decision_planned_seed_order", "plan_decision_adapter_priors",
        "plan_decision_frontier_priority_hints",
        "plan_decision_extraction_strategy_refs",
    ):
        assert key in report, f"s3 mode must keep '{key}'"
    assert report["plan_decision_ref"] == "plan-decision:s3-only:1"
    # All s6 keyed-always keys present with None values (no observe / no replan)
    for key in _S6_KEYED_ALWAYS:
        assert key in report, f"s6 keyed-always '{key}' must be present"
        assert report[key] is None, f"s3 mode must leave '{key}' as None"
    assert "replan_invoked" in report
    assert report["replan_invoked"] is False


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


# ── Event-recording tests (5, 6, 7, 8) ──────────────────────────────────────
# These tests run the runner end-to-end with a controlled fetcher so the
# observer captures real events. The fake fetcher returns canned
# FetchOutcome values; the runner's existing fetch loop + link extractor
# drives the discovery / page-structure / redirect call sites.


@dataclass
class _CannedFetcher:
    outcomes: dict[str, FetchOutcome]

    def fetch(self, url: str, *, timeout_seconds: float) -> FetchOutcome:  # noqa: ARG002
        if url in self.outcomes:
            return self.outcomes[url]
        raise FetchError(f"no canned outcome for {url}")


def _outcome(
    *, url: str, body: bytes = b"", content_type: str = "text/html",
    redirect_history: list[RedirectHop] | None = None,
) -> FetchOutcome:
    return FetchOutcome(
        requested_url=url, final_url=url, status_code=200, headers={},
        body=body, content_type=content_type,
        redirect_chain=[], redirect_history=redirect_history or [],
    )


def _minimal_planner_returning(seeds: list[tuple[str, float]]) -> Any:
    class _Planner:
        def plan(self, request: PlanRequest) -> PlanDecision:
            return PlanDecision(
                id="plan-decision:s6-evt:1", request_ref=request.id,
                planner_adapter_ref="adapter:fake-s6:v1",
                planned_seeds=[
                    PlannedSeed(
                        canonical_url=u, priority_score=p,
                        adapter_hint=AdapterType.HTTP,
                        rationale_ref=f"rationale:{u}",
                    )
                    for u, p in seeds
                ],
                adapter_priors=[AdapterPrior(
                    adapter_type=AdapterType.HTTP, weight=1.0,
                    rationale_ref="rationale:test:http",
                )],
                replay_refs=[request.id, "adapter:fake-s6:v1"],
                policy_decision_refs=["policy-decision:1"],
            )

    return _Planner()


def _spec_for_seeds(seed_urls: list[str], allowed_domains: list[str]) -> Any:
    spec = _spec()
    return spec.model_copy(update={
        "seed_urls": seed_urls,
        "allowed_domains": allowed_domains,
        "max_depth": 2,
    })


def _build_s6(tmp_path: Path, *, seeds: list[str], fetcher: Any,
              allowed: list[str]) -> tuple[ExternalCrawlRunner, _CapturingObserver]:
    obs = _CapturingObserver()
    spec = _spec_for_seeds(seeds, allowed)
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s6")
    plan_seeds = [(u, 1.0 / (1 + i)) for i, u in enumerate(seeds)]

    def builder(_s: Any, _r: Any) -> PlanRequest:
        return PlanRequest(
            id="plan-req:s6:1", run_ref="run:s6:test:1",
            objective_ref="objective:1",
            seed_urls=seeds, budget_ref="budget:1",
            policy_snapshot_ref="policy-snap:1",
            policy_decision_refs=["policy-decision:1"],
            replay_config_ref="replay-config:1",
        )

    runner = ExternalCrawlRunner(
        spec=spec, store=store, run_root=store.run_root,
        fetcher=fetcher,
        planner=_minimal_planner_returning(plan_seeds),
        plan_request_builder=builder,
        utc_clock=_utc, utc_clock_ref="utc-clock:fixture:1",
        graph_observer=obs,
        feedback_aware_planner_factory=_factory,
    )
    return runner, obs


# Test 5
def test_observer_records_url_observed_per_admitted_seed(tmp_path: Path) -> None:
    fetcher = _CannedFetcher(outcomes={
        "https://a.example/": _outcome(url="https://a.example/"),
        "https://b.example/": _outcome(url="https://b.example/"),
    })
    runner, obs = _build_s6(
        tmp_path, seeds=["https://a.example/", "https://b.example/"],
        fetcher=fetcher, allowed=["a.example", "b.example"],
    )
    runner.run()
    seed_events = [
        e for e in obs.url_events if e.source_ref == "frontier-admit:seed"
    ]
    assert len(seed_events) == 2
    assert {e.canonical_url for e in seed_events} == {
        "https://a.example/", "https://b.example/",
    }
    for e in seed_events:
        assert e.depth == 0
        assert e.parent_canonical_url is None


# Test 6
def test_observer_records_url_observed_per_admitted_discovery(tmp_path: Path) -> None:
    seed = "https://seed.example/"
    body = (
        b'<html><body>'
        b'<a href="https://seed.example/child-a">a</a>'
        b'<a href="https://seed.example/child-b/?utm=x#frag">b</a>'
        b'</body></html>'
    )
    # The repo's canonicalize_url drops fragments but PRESERVES query
    # strings (utm tracking params are sorted, not stripped — see
    # src/veracrawl/external_crawl/url.py:43). So the expected canonical
    # for `child-b/?utm=x#frag` is `child-b/?utm=x` (fragment-only
    # canonicalization). Plan v6 originally claimed `child-b/`; this
    # test follow-up corrects the expectation to match what the
    # canonicalizer actually does.
    fetcher = _CannedFetcher(outcomes={
        seed: _outcome(url=seed, body=body),
        "https://seed.example/child-a": _outcome(url="https://seed.example/child-a"),
        "https://seed.example/child-b/?utm=x": _outcome(
            url="https://seed.example/child-b/?utm=x",
        ),
    })
    runner, obs = _build_s6(
        tmp_path, seeds=[seed], fetcher=fetcher, allowed=["seed.example"],
    )
    runner.run()
    assert len(obs.url_events) == 3
    assert obs.url_events[0].canonical_url == seed
    assert obs.url_events[0].source_ref == "frontier-admit:seed"
    assert obs.url_events[0].depth == 0
    assert obs.url_events[0].parent_canonical_url is None
    # Children — order preserved per anchor emission
    assert obs.url_events[1].canonical_url == "https://seed.example/child-a"
    assert obs.url_events[1].depth == 1
    assert obs.url_events[1].parent_canonical_url == seed
    assert obs.url_events[1].source_ref == "frontier-admit:discovery"
    # Canonicalized — fragment stripped (utm preserved per the codebase's
    # canonicalize_url rules). The event's canonical_url must come from
    # EnqueueOutcome.canonical_url, NOT the raw href containing the
    # fragment.
    assert obs.url_events[2].canonical_url == "https://seed.example/child-b/?utm=x"
    assert "#" not in obs.url_events[2].canonical_url
    assert obs.url_events[2].depth == 1
    assert obs.url_events[2].parent_canonical_url == seed


# Test 7
def test_observer_records_redirect_observed_per_redirect_hop(tmp_path: Path) -> None:
    seed = "https://a.example/"
    hops = [
        RedirectHop(from_url="https://a.example/", to_url="https://a.example/x", status_code=301),
        RedirectHop(from_url="https://a.example/x", to_url="https://a.example/y", status_code=302),
    ]
    fetcher = _CannedFetcher(outcomes={
        seed: _outcome(url=seed, redirect_history=hops),
    })
    runner, obs = _build_s6(
        tmp_path, seeds=[seed], fetcher=fetcher, allowed=["a.example"],
    )
    runner.run()
    assert len(obs.redirect_events) == 2
    assert obs.redirect_events[0].from_canonical_url == "https://a.example/"
    assert obs.redirect_events[0].to_canonical_url == "https://a.example/x"
    assert obs.redirect_events[0].status_code == 301
    assert obs.redirect_events[1].status_code == 302


# Test 8
def test_observer_records_page_structure_observed_per_fetched_page(tmp_path: Path) -> None:
    seed1 = "https://a.example/"
    seed2 = "https://b.example/"
    body1 = (
        b'<html><body>'
        b'<a href="https://a.example/1">1</a>'
        b'<a href="https://a.example/2">2</a>'
        b'<a href="https://a.example/3">3</a>'
        b'</body></html>'
    )
    body2 = (
        b'<html><body>'
        b'<a href="https://b.example/1">1</a>'
        b'<a href="https://b.example/2">2</a>'
        b'<a href="https://b.example/3">3</a>'
        b'</body></html>'
    )
    fetcher = _CannedFetcher(outcomes={
        seed1: _outcome(url=seed1, body=body1),
        seed2: _outcome(url=seed2, body=body2),
        "https://a.example/1": _outcome(url="https://a.example/1"),
        "https://a.example/2": _outcome(url="https://a.example/2"),
        "https://a.example/3": _outcome(url="https://a.example/3"),
        "https://b.example/1": _outcome(url="https://b.example/1"),
        "https://b.example/2": _outcome(url="https://b.example/2"),
        "https://b.example/3": _outcome(url="https://b.example/3"),
    })
    runner, obs = _build_s6(
        tmp_path, seeds=[seed1, seed2], fetcher=fetcher,
        allowed=["a.example", "b.example"],
    )
    runner.run()
    page_for_seed = {e.page_canonical_url: e for e in obs.page_events}
    assert seed1 in page_for_seed
    assert seed2 in page_for_seed
    assert page_for_seed[seed1].discovered_link_count == 3
    assert page_for_seed[seed2].discovered_link_count == 3
