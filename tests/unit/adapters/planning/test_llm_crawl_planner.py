"""Unit tests for ``LlmCrawlPlanner`` (s2 step 4, tests 14-25)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from veracrawl.adapters.model_providers.replaying_model_provider import (
    ReplayingModelProviderV2,
)
from veracrawl.adapters.planning.llm_crawl_planner import LlmCrawlPlanner
from veracrawl.contracts.agent import Message, ResponseFormat, TokenUsage
from veracrawl.contracts.crawl_planner import AdapterPrior, PlanRequest
from veracrawl.contracts.enums import (
    AdapterType,
    MessageRole,
    ProviderFinishReason,
    ResponseFormatKind,
)
from veracrawl.contracts.errors import (
    ProviderTraceMissingError,
    StructuredOutputViolation,
    TokenBudgetExceeded,
)
from veracrawl.contracts.llm_input import (
    ProviderRequest,
    ProviderResponse,
    TokenUsageEstimate,
)
from veracrawl.ports.crawl_planner import CrawlPlannerPort

_PROMPT_REF = "prompt:llm-crawl-planner:v1"
_ADAPTER_REF = "adapter:llm-crawl-planner:v1"


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


def _valid_proposal() -> dict[str, Any]:
    return {
        "planned_seeds": [
            {"canonical_url": "https://a.example/1", "priority_score": 0.9,
             "adapter_hint": "http"},
        ],
        "adapter_priors": [{"adapter_type": "http", "weight": 0.8}],
        "frontier_priority_hints": [],
        "extraction_strategy_refs": [],
        "rationale_summary": "test rationale",
    }


def _canned_response(
    request_id: str = "provider-request:plan-request:test:1",
    parsed_output: dict[str, Any] | None = None,
    raw_response_ref: str | None = "raw-response:test:1",
) -> ProviderResponse:
    return ProviderResponse(
        id=f"provider-response:{request_id}",
        request_ref=request_id,
        text="canned",
        usage=TokenUsage(prompt_tokens=12, completion_tokens=8, total_tokens=20),
        finish_reason=ProviderFinishReason.STOP,
        parsed_output=parsed_output if parsed_output is not None else _valid_proposal(),
        raw_response_ref=raw_response_ref,
    )


class _FakePromptRegistry:
    def __init__(self, rendered: str = "rendered prompt text") -> None:
        self._rendered = rendered
        self.recorded_calls: list[tuple[str, dict[str, Any]]] = []

    def render(self, ref: str, context: Mapping[str, Any]) -> str:
        self.recorded_calls.append((ref, dict(context)))
        return self._rendered


class _FakeModelProviderV2:
    def __init__(self, response: ProviderResponse) -> None:
        self._response = response
        self.recorded_request: ProviderRequest | None = None

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        self.recorded_request = request
        return self._response

    def supports(self, capability: Any) -> bool:  # noqa: ARG002
        return True


class _FakeTokenBudget:
    def __init__(self, *, raise_on_estimate: bool = False) -> None:
        self._raise = raise_on_estimate
        self.recorded_calls: list[tuple[str, Any, Any]] = []

    def estimate_charge(self, request: ProviderRequest) -> TokenUsageEstimate:
        self.recorded_calls.append(("estimate_charge", request, None))
        if self._raise:
            raise TokenBudgetExceeded(
                status_code=400, error_code="TOKEN_BUDGET_EXCEEDED", request_id=None,
            )
        return TokenUsageEstimate(
            request_ref=request.id, model_name=request.model_name,
            prompt_tokens_estimate=10, completion_tokens_estimate=5,
            cost_usd_estimate=0.001,
        )

    def charge(self, usage: TokenUsage, *, request_ref: str) -> None:
        self.recorded_calls.append(("charge", usage, request_ref))


def _planner(
    response: ProviderResponse | None = None,
    *,
    raise_on_estimate: bool = False,
) -> tuple[LlmCrawlPlanner, _FakePromptRegistry, _FakeModelProviderV2, _FakeTokenBudget]:
    registry = _FakePromptRegistry()
    provider = _FakeModelProviderV2(response if response is not None else _canned_response())
    budget = _FakeTokenBudget(raise_on_estimate=raise_on_estimate)
    adapter = LlmCrawlPlanner(
        model_provider=provider, prompt_registry=registry, token_budget=budget,
        prompt_template_ref=_PROMPT_REF, model_name="gpt-test",
        max_output_tokens=128, temperature=0.0,
    )
    return adapter, registry, provider, budget


# Test 14
def test_plan_returns_plan_decision_carrying_request_ref() -> None:
    adapter, _, _, _ = _planner()
    decision = adapter.plan(_request())
    assert decision.request_ref == "plan-request:test:1"


# Test 14a
def test_plan_renders_prompt_template_with_request_context() -> None:
    adapter, registry, _, _ = _planner()
    req = _request()
    adapter.plan(req)
    assert registry.recorded_calls == [(_PROMPT_REF, {
        "objective_ref": req.objective_ref,
        "seed_urls": list(req.seed_urls),
        "budget_ref": req.budget_ref,
        "policy_snapshot_ref": req.policy_snapshot_ref,
        "run_ref": req.run_ref,
    })]


# Test 15
def test_plan_planned_seeds_preserve_proposal_order() -> None:
    proposal = _valid_proposal()
    proposal["planned_seeds"] = [
        {"canonical_url": "https://a.example/1", "priority_score": 0.9, "adapter_hint": "http"},
        {"canonical_url": "https://a.example/2", "priority_score": 0.7, "adapter_hint": "http"},
        {"canonical_url": "https://a.example/3", "priority_score": 0.5, "adapter_hint": "http"},
    ]
    proposal["adapter_priors"] = [{"adapter_type": "http", "weight": 0.6}]
    adapter, _, _, _ = _planner(response=_canned_response(parsed_output=proposal))
    decision = adapter.plan(_request(seed_urls=[
        "https://a.example/1", "https://a.example/2", "https://a.example/3",
    ]))
    assert [s.canonical_url for s in decision.planned_seeds] == [
        "https://a.example/1", "https://a.example/2", "https://a.example/3",
    ]


# Test 15a
def test_plan_builds_provider_request_with_expected_fields() -> None:
    adapter, _, provider, _ = _planner()
    req = _request()
    adapter.plan(req)
    pr = provider.recorded_request
    assert pr is not None
    assert pr.id == "provider-request:plan-request:test:1"
    assert pr.run_ref == req.run_ref
    assert pr.model_name == "gpt-test"
    assert pr.messages == [Message(role=MessageRole.USER, content="rendered prompt text")]
    assert pr.response_format == ResponseFormat(kind=ResponseFormatKind.JSON_OBJECT)
    assert pr.max_output_tokens == 128
    assert pr.temperature == 0.0
    assert pr.tools == []
    assert pr.anchors == []


# Test 16
def test_plan_adapter_priors_round_trip_from_proposal() -> None:
    proposal = _valid_proposal()
    proposal["adapter_priors"] = [
        {"adapter_type": "http", "weight": 0.5},
        {"adapter_type": "sitemap", "weight": 0.3},
    ]
    adapter, _, _, _ = _planner(response=_canned_response(parsed_output=proposal))
    decision = adapter.plan(_request())
    expected = [
        AdapterPrior(
            adapter_type=AdapterType.HTTP, weight=0.5,
            rationale_ref=f"rationale:{_ADAPTER_REF}:{_PROMPT_REF}:prior-http",
        ),
        AdapterPrior(
            adapter_type=AdapterType.SITEMAP, weight=0.3,
            rationale_ref=f"rationale:{_ADAPTER_REF}:{_PROMPT_REF}:prior-sitemap",
        ),
    ]
    assert [p.model_dump() for p in decision.adapter_priors] == [
        p.model_dump() for p in expected
    ]


# Test 17
def test_plan_replay_refs_emission_order() -> None:
    adapter, _, _, _ = _planner()
    req = _request()
    decision = adapter.plan(req)
    assert decision.replay_refs == [
        req.id, _ADAPTER_REF, req.replay_config_ref, req.objective_ref,
        _PROMPT_REF, "provider-response:provider-request:plan-request:test:1",
        "raw-response:test:1",
    ]


# Test 18
def test_plan_raises_provider_trace_missing_when_raw_response_ref_none() -> None:
    adapter, _, _, _ = _planner(response=_canned_response(raw_response_ref=None))
    with pytest.raises(ProviderTraceMissingError):
        adapter.plan(_request())
    blank_adapter, _, _, _ = _planner(response=_canned_response(raw_response_ref="   "))
    with pytest.raises(ProviderTraceMissingError):
        blank_adapter.plan(_request())


# Test 19
def test_plan_policy_decision_refs_forwarded_verbatim() -> None:
    refs = ["policy:test:a", "policy:test:b"]
    adapter, _, _, _ = _planner()
    req = _request(policy_decision_refs=list(refs))
    decision = adapter.plan(req)
    assert decision.policy_decision_refs == refs
    req.policy_decision_refs.append("policy:test:tampered")
    assert decision.policy_decision_refs == refs


# Test 20
def test_plan_calls_token_budget_estimate_then_charge_in_order() -> None:
    adapter, _, _, budget = _planner()
    adapter.plan(_request())
    kinds = [call[0] for call in budget.recorded_calls]
    assert kinds == ["estimate_charge", "charge"]


# Test 20a — covers BOTH parsed_output=None and parsed_output={"foo": "bar"}
# paths per the plan's test 20a spec.
def test_plan_charges_token_budget_before_structured_output_validation() -> None:
    # Path 1: parsed_output = None
    none_resp = _canned_response().model_copy(update={"parsed_output": None})
    adapter, _, _, budget = _planner(response=none_resp)
    with pytest.raises(StructuredOutputViolation):
        adapter.plan(_request())
    assert "charge" in [c[0] for c in budget.recorded_calls]
    # Path 2: parsed_output = {"foo": "bar"} (validation failure)
    bad_resp = _canned_response(parsed_output={"foo": "bar"})
    adapter, _, _, budget = _planner(response=bad_resp)
    with pytest.raises(StructuredOutputViolation):
        adapter.plan(_request())
    assert "charge" in [c[0] for c in budget.recorded_calls]


# Test 21
def test_plan_refuses_when_token_budget_estimate_raises() -> None:
    adapter, _, provider, _ = _planner(raise_on_estimate=True)
    with pytest.raises(TokenBudgetExceeded):
        adapter.plan(_request())
    assert provider.recorded_request is None


# Test 22
def test_plan_raises_structured_output_violation_on_none_parsed_output() -> None:
    canned = _canned_response().model_copy(update={"parsed_output": None})
    adapter, _, _, _ = _planner(response=canned)
    with pytest.raises(StructuredOutputViolation):
        adapter.plan(_request())


# Test 23
def test_plan_raises_structured_output_violation_on_invalid_json() -> None:
    adapter, _, _, _ = _planner(response=_canned_response(parsed_output={"foo": "bar"}))
    with pytest.raises(StructuredOutputViolation):
        adapter.plan(_request())


# Test 24
def test_planner_implements_crawl_planner_port() -> None:
    adapter, _, _, _ = _planner()
    assert isinstance(adapter, CrawlPlannerPort)


# Test 15-detail — step-4 iter 1 finding: seed details projected.
def test_plan_planned_seed_fields_round_trip_from_proposal() -> None:
    adapter, _, _, _ = _planner()
    decision = adapter.plan(_request())
    seed = decision.planned_seeds[0]
    assert seed.canonical_url == "https://a.example/1"
    assert seed.priority_score == 0.9
    assert seed.adapter_hint is AdapterType.HTTP
    assert seed.rationale_ref == (
        f"rationale:{_ADAPTER_REF}:{_PROMPT_REF}:seed-0"
    )


# Test 16-hints — step-4 iter 1 finding: frontier_priority_hints projected.
def test_plan_frontier_priority_hints_round_trip_from_proposal() -> None:
    proposal = _valid_proposal()
    proposal["frontier_priority_hints"] = [
        {"match_kind": "url_prefix", "match_value": "https://a.example/",
         "priority_delta": 0.4},
    ]
    adapter, _, _, _ = _planner(response=_canned_response(parsed_output=proposal))
    decision = adapter.plan(_request())
    assert len(decision.frontier_priority_hints) == 1
    hint = decision.frontier_priority_hints[0]
    assert hint.match_value == "https://a.example/"
    assert hint.priority_delta == 0.4
    assert hint.rationale_ref == (
        f"rationale:{_ADAPTER_REF}:{_PROMPT_REF}:hint-url_prefix"
    )


# Test 16-extraction — step-4 iter 1 finding: extraction_strategy_refs forwarded.
def test_plan_extraction_strategy_refs_forwarded_verbatim() -> None:
    proposal = _valid_proposal()
    proposal["extraction_strategy_refs"] = ["strategy:a", "strategy:b"]
    adapter, _, _, _ = _planner(response=_canned_response(parsed_output=proposal))
    decision = adapter.plan(_request())
    assert decision.extraction_strategy_refs == ["strategy:a", "strategy:b"]


# Test 25
def test_replay_refs_enable_byte_identical_plan_decision() -> None:
    canned = _canned_response()
    adapter_1, _, _, _ = _planner(response=canned)
    decision_1 = adapter_1.plan(_request())
    replaying = ReplayingModelProviderV2({"provider-request:plan-request:test:1": canned})
    adapter_2 = LlmCrawlPlanner(
        model_provider=replaying, prompt_registry=_FakePromptRegistry(),
        token_budget=_FakeTokenBudget(),
        prompt_template_ref=_PROMPT_REF, model_name="gpt-test",
        max_output_tokens=128, temperature=0.0,
    )
    decision_2 = adapter_2.plan(_request())
    assert decision_2.canonical_json() == decision_1.canonical_json()
