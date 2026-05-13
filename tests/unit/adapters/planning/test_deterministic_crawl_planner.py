"""Unit tests for ``DeterministicCrawlPlanner`` (s1 step 4)."""

from __future__ import annotations

import math

from veracrawl.adapters.planning.deterministic_crawl_planner import (
    DeterministicCrawlPlanner,
)
from veracrawl.contracts.crawl_planner import AdapterPrior, PlanRequest
from veracrawl.contracts.enums import AdapterType
from veracrawl.ports.crawl_planner import CrawlPlannerPort

_ADAPTER_REF = "adapter:deterministic-crawl-planner:v1"
_HTTP_PRIOR_REF = "rationale:deterministic-crawl-planner:http-only"


def _request(**overrides: object) -> PlanRequest:
    payload: dict[str, object] = {
        "id": "plan-request:test:1",
        "run_ref": "run:test:1",
        "objective_ref": "objective:test:1",
        "seed_urls": ["https://a.example/1"],
        "budget_ref": "budget:test:1",
        "policy_snapshot_ref": "policy-snapshot:test:1",
        "policy_decision_refs": ["policy:test:allow"],
        "replay_config_ref": "replay-config:test:1",
    }
    payload.update(overrides)
    return PlanRequest(**payload)


# Test 23
def test_emits_one_planned_seed_per_seed_url_in_order() -> None:
    request = _request(seed_urls=[
        "https://a.example/1",
        "https://a.example/2",
        "https://a.example/3",
    ])
    decision = DeterministicCrawlPlanner().plan(request)
    assert [s.canonical_url for s in decision.planned_seeds] == request.seed_urls
    assert decision.planned_seeds[0].priority_score == 1.0
    assert decision.planned_seeds[1].priority_score == 0.5
    assert math.isclose(decision.planned_seeds[2].priority_score, 1 / 3)


# Test 24
def test_adapter_hint_defaults_to_http_for_every_seed() -> None:
    request = _request(seed_urls=["https://a.example/1", "https://b.example/2"])
    decision = DeterministicCrawlPlanner().plan(request)
    assert all(s.adapter_hint is AdapterType.HTTP for s in decision.planned_seeds)


# Test 25
def test_adapter_priors_fixed_http_only_regardless_of_observed_state() -> None:
    expected = [
        AdapterPrior(
            adapter_type=AdapterType.HTTP,
            weight=1.0,
            rationale_ref=_HTTP_PRIOR_REF,
        ).model_dump(),
    ]
    for observed in ([], ["graph-snapshot:ignored"]):
        decision = DeterministicCrawlPlanner().plan(_request(observed_state_refs=observed))
        assert [p.model_dump() for p in decision.adapter_priors] == expected


# Test 26
def test_replay_refs_match_declared_emission_order() -> None:
    request = _request()
    decision = DeterministicCrawlPlanner().plan(request)
    assert decision.replay_refs == [
        request.id,
        _ADAPTER_REF,
        request.replay_config_ref,
        request.objective_ref,
    ]


# Test 27
def test_policy_decision_refs_forwarded_verbatim() -> None:
    refs = ["policy:test:a", "policy:test:b"]
    request = _request(policy_decision_refs=refs)
    decision = DeterministicCrawlPlanner().plan(request)
    assert decision.policy_decision_refs == refs
    # Defensive copy: mutating the request's list must not change the decision.
    request.policy_decision_refs.append("policy:test:tampered")
    assert decision.policy_decision_refs == refs


# Test 27a
def test_request_ref_equals_request_id() -> None:
    request = _request(id="plan-request:test:request-ref-equals")
    decision = DeterministicCrawlPlanner().plan(request)
    assert decision.request_ref == request.id


# Test 28
def test_planner_is_pure_function_via_canonical_json() -> None:
    request = _request()
    adapter = DeterministicCrawlPlanner()
    first = adapter.plan(request).canonical_json()
    second = adapter.plan(request).canonical_json()
    assert first == second


# Test 29
def test_planner_implements_crawl_planner_port() -> None:
    assert isinstance(DeterministicCrawlPlanner(), CrawlPlannerPort)
