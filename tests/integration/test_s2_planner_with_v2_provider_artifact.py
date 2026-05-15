"""Integration test for s2 ``LlmCrawlPlanner`` against the v2 OpenAI
adapter wired with an ``ArtifactStorePort`` (s2.1 step 5).

Proves the production wiring: the v2 adapter populates
``ProviderResponse.raw_response_ref`` (via the artifact-store
persist path s2.1 step 2 added), so the s2 planner's existing
``ProviderTraceMissingError`` guard is satisfied and a real
``PlanDecision`` round-trips out with the raw-response ref as the
7th entry of ``replay_refs``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import httpx

from veracrawl.adapters.model_providers.openai_responses_v2 import (
    OpenAIResponsesAdapterV2,
)
from veracrawl.adapters.object_stores.in_memory_bytes_artifact_store import (
    InMemoryBytesArtifactStore,
)
from veracrawl.adapters.planning.llm_crawl_planner import LlmCrawlPlanner
from veracrawl.contracts.agent import TokenUsage
from veracrawl.contracts.crawl_planner import PlanRequest
from veracrawl.contracts.llm_input import ProviderRequest, TokenUsageEstimate
from veracrawl.runtime_support.runtime_mode import RuntimeMode

_PROMPT_REF = "prompt:llm-crawl-planner:v1"
_ADAPTER_REF = "adapter:llm-crawl-planner:v1"


def _valid_proposal() -> dict[str, Any]:
    return {
        "planned_seeds": [
            {
                "canonical_url": "https://a.example/1",
                "priority_score": 0.9,
                "adapter_hint": "http",
            },
        ],
        "adapter_priors": [{"adapter_type": "http", "weight": 0.8}],
        "frontier_priority_hints": [],
        "extraction_strategy_refs": [],
        "rationale_summary": "test rationale",
    }


def _canned_openai_body() -> bytes:
    parsed_json_text = json.dumps(_valid_proposal())
    return json.dumps({
        "id": "resp_s2_int_1",
        "status": "completed",
        "output": [
            {"content": [{"type": "output_text", "text": parsed_json_text}]},
        ],
        "usage": {"input_tokens": 12, "output_tokens": 8, "total_tokens": 20},
    }).encode()


class _FakePromptRegistry:
    def render(self, ref: str, context: Mapping[str, Any]) -> str:  # noqa: ARG002
        return json.dumps(_valid_proposal())


class _FakeTokenBudget:
    def estimate_charge(self, request: ProviderRequest) -> TokenUsageEstimate:
        return TokenUsageEstimate(
            request_ref=request.id,
            model_name=request.model_name,
            prompt_tokens_estimate=10,
            completion_tokens_estimate=5,
            cost_usd_estimate=0.001,
        )

    def charge(self, usage: TokenUsage, *, request_ref: str) -> None:
        del usage, request_ref  # only the call existence matters


def _request() -> PlanRequest:
    return PlanRequest(
        id="plan-request:s2_1_int:1",
        run_ref="run:s2_1_int:1",
        objective_ref="objective:s2_1_int:1",
        seed_urls=["https://a.example/1"],
        budget_ref="budget:s2_1_int:1",
        policy_snapshot_ref="policy-snapshot:s2_1_int:1",
        policy_decision_refs=["policy:test:allow"],
        replay_config_ref="replay-config:s2_1_int:1",
    )


def _build_planner(
    *, artifact_store: InMemoryBytesArtifactStore,
) -> LlmCrawlPlanner:
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_canned_openai_body())

    provider = OpenAIResponsesAdapterV2(
        api_key="test-key",
        runtime_mode=RuntimeMode.FIXTURE,
        transport=httpx.MockTransport(handler),
        artifact_store=artifact_store,
    )
    return LlmCrawlPlanner(
        model_provider=provider,
        prompt_registry=_FakePromptRegistry(),
        token_budget=_FakeTokenBudget(),
        prompt_template_ref=_PROMPT_REF,
        model_name="gpt-5",
        max_output_tokens=128,
        temperature=0.0,
    )


def test_s2_planner_succeeds_end_to_end_with_v2_provider_and_artifact_store() -> None:
    store = InMemoryBytesArtifactStore()
    planner = _build_planner(artifact_store=store)

    decision = planner.plan(_request())

    assert decision.request_ref == "plan-request:s2_1_int:1"
    # 7-entry replay_refs from s2's _project(): [request.id,
    # adapter_ref, replay_config_ref, objective_ref,
    # prompt_template_ref, response_id, raw_response_ref].
    assert len(decision.replay_refs) == 7
    raw_response_ref = decision.replay_refs[6]
    assert raw_response_ref.startswith("artifact:sha256:")
    assert store.exists(raw_response_ref)


def test_s2_planner_replay_ref_resolves_through_artifact_store_read() -> None:
    """Ties the raw_response_ref to a real round-trippable byte
    record — proves the s2.1 producer/consumer invariant.
    """

    store = InMemoryBytesArtifactStore()
    planner = _build_planner(artifact_store=store)

    decision = planner.plan(_request())

    raw_response_ref = decision.replay_refs[6]
    persisted_bytes = store.read(raw_response_ref)
    assert persisted_bytes == _canned_openai_body()
