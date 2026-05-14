"""Unit tests for ``DeterministicCrawlPlannerV2`` (s5 tests 24-37)."""

from __future__ import annotations

import pytest

from veracrawl.adapters.planning.deterministic_crawl_planner_v2 import (
    ADAPTER_REF,
    DeterministicCrawlPlannerV2,
)
from veracrawl.contracts.common import stable_hash
from veracrawl.contracts.crawl_planner import PlanRequest
from veracrawl.contracts.enums import AdapterType, FrontierMatchKind
from veracrawl.contracts.planner_observation_feedback import PlannerObservationFeedback
from veracrawl.ports.crawl_planner import CrawlPlannerPort

_RUN = "run:s5-test:1"
_FB_ID = "fb:s5-test:1"


def _request(
    *, observed_state_refs: list[str] | None = None,
    seed_urls: list[str] | None = None, run_ref: str = _RUN,
) -> PlanRequest:
    return PlanRequest(
        id="plan-req:1",
        run_ref=run_ref,
        objective_ref="objective:1",
        seed_urls=seed_urls or ["https://a.example/", "https://b.example/"],
        budget_ref="budget:1",
        policy_snapshot_ref="policy-snap:1",
        policy_decision_refs=["policy-dec:1"],
        replay_config_ref="replay-config:1",
        observed_state_refs=observed_state_refs or [],
    )


def _fb(**overrides: object) -> PlannerObservationFeedback:
    base: dict[str, object] = {
        "id": _FB_ID,
        "run_ref": _RUN,
        "redirect_neighbours": [],
        "canonical_targets": [],
        "page_neighbour_count_by_url": {},
    }
    base.update(overrides)
    return PlannerObservationFeedback(**base)  # type: ignore[arg-type]


# Test 24
def test_v2_without_feedback_matches_s1_decision_shape() -> None:
    adapter = DeterministicCrawlPlannerV2()
    decision = adapter.plan(_request())
    assert len(decision.planned_seeds) == 2
    assert all(s.adapter_hint is AdapterType.HTTP for s in decision.planned_seeds)
    assert len(decision.adapter_priors) == 1
    assert decision.adapter_priors[0].adapter_type is AdapterType.HTTP
    assert decision.adapter_priors[0].weight == 1.0
    assert decision.frontier_priority_hints == []


# Test 25
def test_v2_emits_host_glob_hints_for_redirect_neighbours() -> None:
    fb = _fb(redirect_neighbours=["https://a.example/x", "https://b.example/y"])
    decision = DeterministicCrawlPlannerV2(feedback=fb).plan(
        _request(observed_state_refs=[_FB_ID]),
    )
    redirect_hints = [
        h for h in decision.frontier_priority_hints
        if h.match_kind is FrontierMatchKind.HOST_GLOB
    ]
    assert len(redirect_hints) == 2
    assert redirect_hints[0].match_value == "a.example"
    assert redirect_hints[0].priority_delta == 0.6
    assert redirect_hints[1].match_value == "b.example"
    assert redirect_hints[1].priority_delta == 0.6


# Test 26
def test_v2_emits_url_prefix_hints_for_canonical_targets() -> None:
    fb = _fb(canonical_targets=["https://a.example/x", "https://b.example/y"])
    decision = DeterministicCrawlPlannerV2(feedback=fb).plan(
        _request(observed_state_refs=[_FB_ID]),
    )
    canon_hints = [
        h for h in decision.frontier_priority_hints
        if h.match_kind is FrontierMatchKind.URL_PREFIX
        and "canonical" in h.rationale_ref
    ]
    assert len(canon_hints) == 2
    assert canon_hints[0].match_value == "https://a.example/x"
    assert canon_hints[0].priority_delta == 0.4


# Test 27
def test_v2_emits_url_prefix_hints_for_hub_pages() -> None:
    fb = _fb(
        page_neighbour_count_by_url={
            "https://a.example/hub": 5,
            "https://a.example/leaf": 1,
        },
    )
    decision = DeterministicCrawlPlannerV2(feedback=fb).plan(
        _request(observed_state_refs=[_FB_ID]),
    )
    hub_hints = [
        h for h in decision.frontier_priority_hints
        if "hub" in h.rationale_ref
    ]
    assert len(hub_hints) == 1
    assert hub_hints[0].match_value == "https://a.example/hub"
    assert hub_hints[0].priority_delta == 0.2
    assert hub_hints[0].match_kind is FrontierMatchKind.URL_PREFIX


# Test 27a
def test_v2_hub_hint_order_is_url_sorted() -> None:
    fb = _fb(
        page_neighbour_count_by_url={
            "https://z.example/hub": 9,
            "https://a.example/hub": 7,
            "https://m.example/hub": 5,
        },
    )
    decision = DeterministicCrawlPlannerV2(feedback=fb).plan(
        _request(observed_state_refs=[_FB_ID]),
    )
    hub_urls = [
        h.match_value for h in decision.frontier_priority_hints
        if "hub" in h.rationale_ref
    ]
    assert hub_urls == [
        "https://a.example/hub",
        "https://m.example/hub",
        "https://z.example/hub",
    ]


# Test 28
def test_v2_emits_hints_in_redirect_canonical_hub_order() -> None:
    fb = _fb(
        redirect_neighbours=["https://r.example/x"],
        canonical_targets=["https://c.example/x"],
        page_neighbour_count_by_url={"https://h.example/x": 9},
    )
    decision = DeterministicCrawlPlannerV2(feedback=fb).plan(
        _request(observed_state_refs=[_FB_ID]),
    )
    rationales = [h.rationale_ref for h in decision.frontier_priority_hints]
    assert "redirect" in rationales[0]
    assert "canonical" in rationales[1]
    assert "hub" in rationales[2]


# Test 28a
def test_v2_decision_is_replay_stable_through_feedback_canonical_json_round_trip() -> None:
    fb_a = _fb(
        redirect_neighbours=["https://r.example/x"],
        canonical_targets=["https://c.example/x"],
        page_neighbour_count_by_url={
            "https://h.example/x": 9,
            "https://h.example/y": 7,
        },
    )
    req = _request(observed_state_refs=[_FB_ID])
    decision_a = DeterministicCrawlPlannerV2(feedback=fb_a).plan(req)
    fb_b = PlannerObservationFeedback.model_validate_json(fb_a.canonical_json())
    decision_b = DeterministicCrawlPlannerV2(feedback=fb_b).plan(req)
    assert decision_a.canonical_json() == decision_b.canonical_json()


# Test 29
def test_v2_rejects_feedback_run_ref_mismatch_with_request() -> None:
    fb = _fb(run_ref="run:a")
    with pytest.raises(ValueError, match="feedback.run_ref must match request.run_ref"):
        DeterministicCrawlPlannerV2(feedback=fb).plan(
            _request(observed_state_refs=[_FB_ID], run_ref="run:b"),
        )


# Test 30
def test_v2_rejects_feedback_id_not_in_request_observed_state_refs() -> None:
    fb = _fb()
    with pytest.raises(ValueError, match="feedback.id must be threaded"):
        DeterministicCrawlPlannerV2(feedback=fb).plan(
            _request(observed_state_refs=["other"]),
        )


# Test 31
def test_v2_records_feedback_id_in_decision_replay_refs() -> None:
    fb = _fb()
    decision = DeterministicCrawlPlannerV2(feedback=fb).plan(
        _request(observed_state_refs=[_FB_ID]),
    )
    assert decision.replay_refs[-1] == _FB_ID


# Test 32
def test_v2_without_feedback_does_not_record_feedback_id_in_replay_refs() -> None:
    decision = DeterministicCrawlPlannerV2().plan(_request())
    assert not any(r.startswith("fb:") for r in decision.replay_refs)
    assert len(decision.replay_refs) == 4


# Test 33
def test_v2_rationale_refs_are_deterministic_from_inputs() -> None:
    fb = _fb(
        redirect_neighbours=["https://r.example/x"],
        canonical_targets=["https://c.example/x"],
        page_neighbour_count_by_url={"https://h.example/x": 9},
    )
    decision = DeterministicCrawlPlannerV2(feedback=fb).plan(
        _request(observed_state_refs=[_FB_ID]),
    )
    rationales = [h.rationale_ref for h in decision.frontier_priority_hints]
    canon_hash = stable_hash("https://c.example/x")[:8]
    hub_hash = stable_hash("https://h.example/x")[:8]
    assert rationales[0] == f"rationale:{ADAPTER_REF}:redirect-r.example"
    assert rationales[1] == f"rationale:{ADAPTER_REF}:canonical-{canon_hash}"
    assert rationales[2] == f"rationale:{ADAPTER_REF}:hub-{hub_hash}"


# Test 34
def test_v2_decision_request_ref_equals_request_id() -> None:
    req = _request()
    decision = DeterministicCrawlPlannerV2().plan(req)
    assert decision.request_ref == req.id
    fb = _fb()
    decision_fb = DeterministicCrawlPlannerV2(feedback=fb).plan(
        _request(observed_state_refs=[_FB_ID]),
    )
    assert decision_fb.request_ref == "plan-req:1"


# Test 35
def test_v2_is_pure_function() -> None:
    fb = _fb(redirect_neighbours=["https://r.example/x"])
    req = _request(observed_state_refs=[_FB_ID])
    adapter = DeterministicCrawlPlannerV2(feedback=fb)
    a = adapter.plan(req).canonical_json()
    b = adapter.plan(req).canonical_json()
    assert a == b


# Test 36
def test_v2_implements_crawl_planner_port() -> None:
    assert isinstance(DeterministicCrawlPlannerV2(), CrawlPlannerPort)


# Test 37
def test_v2_policy_decision_refs_forwarded_verbatim() -> None:
    req = _request()
    decision = DeterministicCrawlPlannerV2().plan(req)
    assert decision.policy_decision_refs == list(req.policy_decision_refs)
