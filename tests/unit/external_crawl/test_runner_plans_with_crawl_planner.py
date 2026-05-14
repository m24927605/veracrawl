"""Unit tests for s3 runner planning wiring (tests 1-13, 6a, 10a)."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from veracrawl.adapters.model_providers.replaying_model_provider import (
    ReplayingModelProviderV2,
)
from veracrawl.adapters.object_stores.local_fs_crawl_artifact_store import (
    LocalFsCrawlArtifactStore,
)
from veracrawl.adapters.planning.llm_crawl_planner import LlmCrawlPlanner
from veracrawl.contracts.agent import (
    TokenUsage,
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
    ProviderFinishReason,
)
from veracrawl.contracts.llm_input import (
    ProviderRequest,
    ProviderResponse,
    TokenUsageEstimate,
)
from veracrawl.external_crawl.runner import ExternalCrawlRunner
from veracrawl.ports.crawl_http_fetcher import FetchError

_ADAPTER_REF = "adapter:llm-crawl-planner:v1"
_PROMPT_REF = "prompt:llm-crawl-planner:v1"


def _spec(*, seed_urls: list[str], spec_id: str = "spec:test:1") -> CrawlJobSpec:
    return CrawlJobSpec(
        id=spec_id, project_id="project:test",
        objective="unit test",
        seed_urls=seed_urls,
        allowed_domains=["a.example", "b.example", "c.example"],
        denied_domains=[], max_depth=1, max_pages=10, max_runtime_seconds=5,
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


@dataclass
class _FailingFetcher:
    """Every fetch raises so the runner loop drains the queue and writes the report."""

    calls: list[str] = field(default_factory=list)

    def fetch(self, url: str, *, timeout_seconds: float) -> Any:  # noqa: ARG002
        self.calls.append(url)
        raise FetchError(f"fake fetcher refuses to fetch {url}")


@dataclass
class _FakeCrawlPlanner:
    decision: PlanDecision
    recorded: list[PlanRequest] = field(default_factory=list)

    def plan(self, request: PlanRequest) -> PlanDecision:
        self.recorded.append(request)
        return self.decision


def _plan_request(spec_id: str = "spec:test:1") -> PlanRequest:
    return PlanRequest(
        id=f"plan-request:auto:{spec_id}", run_ref=f"run:auto:{spec_id}",
        objective_ref=f"objective:auto:{spec_id}",
        seed_urls=["https://a.example/"],
        budget_ref=f"budget:auto:{spec_id}",
        policy_snapshot_ref=f"policy-snapshot:auto:{spec_id}",
        policy_decision_refs=[f"policy-decision:auto:{spec_id}"],
        replay_config_ref=f"replay-config:auto:{spec_id}",
    )


def _make_decision(
    *,
    request_id: str = "plan-request:auto:spec:test:1",
    seeds: list[tuple[str, float]] | None = None,
    hints: list[FrontierPriorityHint] | None = None,
    extraction_refs: list[str] | None = None,
) -> PlanDecision:
    seed_tuples = seeds if seeds is not None else [("https://a.example/", 1.0)]
    return PlanDecision(
        id="plan-decision:test:1", request_ref=request_id,
        planner_adapter_ref="adapter:fake-planner:v1",
        planned_seeds=[
            PlannedSeed(canonical_url=u, priority_score=p,
                        adapter_hint=AdapterType.HTTP,
                        rationale_ref=f"rationale:test:{u}")
            for u, p in seed_tuples
        ],
        adapter_priors=[
            AdapterPrior(adapter_type=AdapterType.HTTP, weight=1.0,
                         rationale_ref="rationale:test:http")
        ],
        frontier_priority_hints=hints or [],
        extraction_strategy_refs=extraction_refs or [],
        replay_refs=[request_id, "adapter:fake-planner:v1"],
        policy_decision_refs=["policy-decision:test"],
    )


def _build_runner(
    tmp_path: Path,
    *,
    spec: CrawlJobSpec | None = None,
    planner: Any | None = None,
    plan_request_builder: Callable[[CrawlJobSpec, Path], PlanRequest] | None = None,
) -> tuple[ExternalCrawlRunner, _FailingFetcher]:
    spec = spec or _spec(seed_urls=["https://a.example/"])
    fetcher = _FailingFetcher()
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s3")
    return ExternalCrawlRunner(
        spec=spec, store=store, run_root=store.run_root,
        fetcher=fetcher, planner=planner,
        plan_request_builder=plan_request_builder,
    ), fetcher


def _read_report(tmp_path: Path) -> dict[str, Any]:
    return json.loads((tmp_path / "run-s3" / "reports" / "run_report.json").read_text())


# Test 1
def test_runner_skips_planning_when_planner_is_none(tmp_path: Path) -> None:
    runner, _ = _build_runner(tmp_path)
    runner.run()
    report = _read_report(tmp_path)
    assert "plan_decision_ref" not in report


# Test 2
def test_runner_raises_when_planner_provided_without_builder(tmp_path: Path) -> None:
    spec = _spec(seed_urls=["https://a.example/"])
    fetcher = _FailingFetcher()
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s3")
    with pytest.raises(ValueError, match="plan_request_builder"):
        ExternalCrawlRunner(
            spec=spec, store=store, run_root=tmp_path / "r", fetcher=fetcher,
            planner=_FakeCrawlPlanner(decision=_make_decision()),
            plan_request_builder=None,
        )


# Test 3
def test_runner_raises_when_builder_provided_without_planner(tmp_path: Path) -> None:
    spec = _spec(seed_urls=["https://a.example/"])
    fetcher = _FailingFetcher()
    store = LocalFsCrawlArtifactStore(root=tmp_path, run_id="run-s3")
    with pytest.raises(ValueError, match="planner"):
        ExternalCrawlRunner(
            spec=spec, store=store, run_root=tmp_path / "r", fetcher=fetcher,
            planner=None, plan_request_builder=lambda s, p: _plan_request(s.id),
        )


# Test 4
def test_runner_invokes_planner_before_enqueue(tmp_path: Path) -> None:
    fake = _FakeCrawlPlanner(decision=_make_decision())
    runner, _ = _build_runner(
        tmp_path, planner=fake,
        plan_request_builder=lambda s, p: _plan_request(s.id),
    )
    runner.run()
    assert len(fake.recorded) == 1


# Test 5
def test_runner_uses_caller_supplied_plan_request_builder(tmp_path: Path) -> None:
    fake = _FakeCrawlPlanner(decision=_make_decision(request_id="plan-request:custom:1"))
    custom = PlanRequest(
        id="plan-request:custom:1", run_ref="run:custom:1",
        objective_ref="objective:custom:1", seed_urls=["https://a.example/"],
        budget_ref="budget:custom:1", policy_snapshot_ref="policy-snapshot:custom:1",
        policy_decision_refs=["policy-decision:custom:1"],
        replay_config_ref="replay-config:custom:1",
    )
    runner, _ = _build_runner(
        tmp_path, planner=fake, plan_request_builder=lambda s, p: custom,
    )
    runner.run()
    assert fake.recorded == [custom]


# Test 6
def test_runner_enqueues_planned_seeds_in_priority_order(tmp_path: Path) -> None:
    decision = _make_decision(seeds=[
        ("https://a.example/3", 0.3),
        ("https://b.example/9", 0.9),
        ("https://c.example/6", 0.6),
    ])
    fake = _FakeCrawlPlanner(decision=decision)
    runner, fetcher = _build_runner(
        tmp_path, planner=fake,
        plan_request_builder=lambda s, p: _plan_request(s.id),
    )
    runner.run()
    assert fetcher.calls == [
        "https://b.example/9", "https://c.example/6", "https://a.example/3",
    ]


# Test 6a — emission-order stability on ties
def test_runner_preserves_emission_order_on_priority_ties(tmp_path: Path) -> None:
    decision = _make_decision(seeds=[
        ("https://b.example/", 0.5),
        ("https://a.example/", 0.5),
        ("https://c.example/", 0.5),
    ])
    fake = _FakeCrawlPlanner(decision=decision)
    runner, fetcher = _build_runner(
        tmp_path, planner=fake,
        plan_request_builder=lambda s, p: _plan_request(s.id),
    )
    runner.run()
    assert fetcher.calls == [
        "https://b.example/", "https://a.example/", "https://c.example/",
    ]


# Test 7
def test_runner_persists_plan_decision_ref_in_run_report(tmp_path: Path) -> None:
    fake = _FakeCrawlPlanner(decision=_make_decision())
    runner, _ = _build_runner(
        tmp_path, planner=fake,
        plan_request_builder=lambda s, p: _plan_request(s.id),
    )
    runner.run()
    assert _read_report(tmp_path)["plan_decision_ref"] == "plan-decision:test:1"


# Test 8
def test_runner_persists_plan_decision_replay_refs_verbatim(tmp_path: Path) -> None:
    fake = _FakeCrawlPlanner(decision=_make_decision())
    runner, _ = _build_runner(
        tmp_path, planner=fake,
        plan_request_builder=lambda s, p: _plan_request(s.id),
    )
    runner.run()
    report = _read_report(tmp_path)
    assert report["plan_decision_replay_refs"] == [
        "plan-request:auto:spec:test:1", "adapter:fake-planner:v1",
    ]


# Test 9
def test_runner_records_frontier_priority_hints_without_applying(tmp_path: Path) -> None:
    hint = FrontierPriorityHint(
        match_kind=FrontierMatchKind.URL_PREFIX, match_value="https://b.example/",
        priority_delta=0.7, rationale_ref="rationale:test:hint",
    )
    fake = _FakeCrawlPlanner(decision=_make_decision(hints=[hint]))
    runner, _ = _build_runner(
        tmp_path, planner=fake,
        plan_request_builder=lambda s, p: _plan_request(s.id),
    )
    runner.run()
    assert _read_report(tmp_path)["plan_decision_frontier_priority_hints"] == [
        hint.model_dump(mode="json"),
    ]


# Test 10
def test_runner_records_adapter_priors_without_applying(tmp_path: Path) -> None:
    fake = _FakeCrawlPlanner(decision=_make_decision())
    runner, _ = _build_runner(
        tmp_path, planner=fake,
        plan_request_builder=lambda s, p: _plan_request(s.id),
    )
    runner.run()
    priors = _read_report(tmp_path)["plan_decision_adapter_priors"]
    assert priors == [fake.decision.adapter_priors[0].model_dump(mode="json")]


# Test 10a
def test_runner_records_extraction_strategy_refs_without_applying(
    tmp_path: Path,
) -> None:
    fake = _FakeCrawlPlanner(decision=_make_decision(
        extraction_refs=["strategy:a", "strategy:b"],
    ))
    runner, _ = _build_runner(
        tmp_path, planner=fake,
        plan_request_builder=lambda s, p: _plan_request(s.id),
    )
    runner.run()
    assert _read_report(tmp_path)["plan_decision_extraction_strategy_refs"] == [
        "strategy:a", "strategy:b",
    ]


# Test 11
def test_runner_records_planned_seed_order_in_sorted_order(tmp_path: Path) -> None:
    fake = _FakeCrawlPlanner(decision=_make_decision(seeds=[
        ("https://a.example/x", 0.4),
        ("https://b.example/y", 0.9),
    ]))
    runner, _ = _build_runner(
        tmp_path, planner=fake,
        plan_request_builder=lambda s, p: _plan_request(s.id),
    )
    runner.run()
    assert _read_report(tmp_path)["plan_decision_planned_seed_order"] == [
        "https://b.example/y", "https://a.example/x",
    ]


# Test 12
def test_runner_omits_plan_decision_keys_when_planner_is_none(tmp_path: Path) -> None:
    runner, _ = _build_runner(tmp_path)
    runner.run()
    report = _read_report(tmp_path)
    for key in (
        "plan_decision_ref", "plan_decision_replay_refs",
        "plan_decision_frontier_priority_hints", "plan_decision_adapter_priors",
        "plan_decision_planned_seed_order", "plan_decision_extraction_strategy_refs",
    ):
        assert key not in report


# Test 13 — same-slice replay-consumer demonstration (LlmCrawlPlanner + ReplayingModelProviderV2)
class _FakePromptRegistry:
    def render(self, ref: str, context: Any) -> str:  # noqa: ARG002
        return "rendered"


class _FakeTokenBudget:
    def estimate_charge(self, request: ProviderRequest) -> TokenUsageEstimate:
        return TokenUsageEstimate(
            request_ref=request.id, model_name=request.model_name,
            prompt_tokens_estimate=1, completion_tokens_estimate=1,
            cost_usd_estimate=0.001,
        )
    def charge(self, usage: TokenUsage, *, request_ref: str) -> None:
        return None


def _llm_planner(provider: Any) -> LlmCrawlPlanner:
    return LlmCrawlPlanner(
        model_provider=provider, prompt_registry=_FakePromptRegistry(),
        token_budget=_FakeTokenBudget(), prompt_template_ref=_PROMPT_REF,
        model_name="gpt-test", max_output_tokens=64, temperature=0.0,
    )


_DEFAULT_PROVIDER_REQUEST_ID = "provider-request:plan-request:auto:spec:test:1"


def _llm_canned(
    provider_request_id: str = _DEFAULT_PROVIDER_REQUEST_ID,
) -> ProviderResponse:
    return ProviderResponse(
        id=f"provider-response:{provider_request_id}",
        request_ref=provider_request_id, text="x",
        usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        finish_reason=ProviderFinishReason.STOP,
        parsed_output={
            "planned_seeds": [{
                "canonical_url": "https://a.example/", "priority_score": 0.9,
                "adapter_hint": "http",
            }],
            "adapter_priors": [{"adapter_type": "http", "weight": 0.8}],
            "frontier_priority_hints": [],
            "extraction_strategy_refs": ["strategy:replay"],
            "rationale_summary": "replay test rationale",
        },
        raw_response_ref=f"raw-response:{provider_request_id}",
    )


class _RecordingProviderV2:
    def __init__(self, canned: ProviderResponse) -> None:
        self._canned = canned
    def complete(self, request: ProviderRequest) -> ProviderResponse:
        return self._canned
    def supports(self, capability: Any) -> bool:  # noqa: ARG002
        return True


def test_runner_run_report_is_byte_identical_when_planner_uses_replaying_model_provider(
    tmp_path: Path,
) -> None:
    canned = _llm_canned()
    # Run 1: regular fake provider
    runner_1, _ = _build_runner(
        tmp_path / "run1", planner=_llm_planner(_RecordingProviderV2(canned)),
        plan_request_builder=lambda s, p: _plan_request(s.id),
    )
    runner_1.run()
    report_1 = _read_report(tmp_path / "run1")
    # Run 2: ReplayingModelProviderV2 keyed by ProviderRequest.id (real in-product consumer)
    replaying = ReplayingModelProviderV2({canned.request_ref: canned})
    runner_2, _ = _build_runner(
        tmp_path / "run2", planner=_llm_planner(replaying),
        plan_request_builder=lambda s, p: _plan_request(s.id),
    )
    runner_2.run()
    report_2 = _read_report(tmp_path / "run2")
    for key in (
        "plan_decision_ref", "plan_decision_replay_refs",
        "plan_decision_frontier_priority_hints", "plan_decision_adapter_priors",
        "plan_decision_planned_seed_order", "plan_decision_extraction_strategy_refs",
    ):
        assert report_1[key] == report_2[key], f"mismatch on {key}"
