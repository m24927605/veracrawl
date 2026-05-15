"""Unit tests for ``LlmExtractionStrategy`` (s9)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import pytest

from veracrawl.adapters.extraction_strategy.llm_extraction_strategy import (
    LlmExtractionStrategy,
)
from veracrawl.contracts.agent import TokenUsage
from veracrawl.contracts.enums import ProviderFinishReason
from veracrawl.contracts.errors import (
    ProviderTraceMissingError,
    StructuredOutputViolation,
)
from veracrawl.contracts.llm_input import (
    ProviderRequest,
    ProviderResponse,
    TokenUsageEstimate,
)
from veracrawl.contracts.normalized_document_read_model import (
    NormalizedDocumentReadModel,
)
from veracrawl.ports.extraction_strategy import ExtractionStrategyPort

_PROMPT_REF = "prompt:llm-extraction:v1"
_VALID_FIELDS = [
    {"name": "title", "xpath": "//h1", "confidence": 0.9,
     "evidence_anchor_count": 3, "proposed_type": "string"},
]


def _document() -> NormalizedDocumentReadModel:
    return NormalizedDocumentReadModel(
        id="doc:test:1",
        normalized_document_ref="normalized:test:1",
        text_sample_refs=["sample:test:1"],
    )


def _response(
    *,
    raw_response_ref: str | None = "artifact:sha256:abc",
    parsed_output: dict[str, Any] | None = None,
    response_id: str = "provider-response:llm-extraction:1",
    request_id: str = "provider-request:llm-extraction:doc:test:1",
) -> ProviderResponse:
    return ProviderResponse(
        id=response_id,
        request_ref=request_id,
        text="canned",
        usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        finish_reason=ProviderFinishReason.STOP,
        parsed_output=parsed_output if parsed_output is not None else {
            "proposed_fields": _VALID_FIELDS,
        },
        raw_response_ref=raw_response_ref,
    )


class _FakeRegistry:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def resolve(self, ref: str) -> Any:  # noqa: ARG002
        return None

    def render(self, ref: str, context: Mapping[str, Any]) -> str:
        self.calls.append((ref, dict(context)))
        return "rendered"


class _FakeProvider:
    def __init__(self, response: ProviderResponse) -> None:
        self._response = response
        self.recorded: list[ProviderRequest] = []

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        self.recorded.append(request)
        return self._response

    def supports(self, capability: Any) -> bool:  # noqa: ARG002
        return True


@dataclass
class _FakeBudget:
    estimates: list[ProviderRequest] = field(default_factory=list)
    charges: list[tuple[TokenUsage, str]] = field(default_factory=list)

    def estimate_charge(self, request: ProviderRequest) -> TokenUsageEstimate:
        self.estimates.append(request)
        return TokenUsageEstimate(
            request_ref=request.id, model_name=request.model_name,
            prompt_tokens_estimate=10, completion_tokens_estimate=5,
            cost_usd_estimate=0.001,
        )

    def charge(self, usage: TokenUsage, *, request_ref: str) -> None:
        self.charges.append((usage, request_ref))


def _adapter(
    response: ProviderResponse | None = None,
) -> tuple[LlmExtractionStrategy, _FakeRegistry, _FakeProvider, _FakeBudget]:
    registry = _FakeRegistry()
    provider = _FakeProvider(response or _response())
    budget = _FakeBudget()
    adapter = LlmExtractionStrategy(
        provider=provider, prompt_registry=registry, token_budget=budget,
        prompt_template_ref=_PROMPT_REF, model_name="gpt-test",
        max_output_tokens=256, temperature=0.0,
    )
    return adapter, registry, provider, budget


# Test 1
def test_propose_renders_prompt_via_registry() -> None:
    adapter, registry, _, _ = _adapter()
    adapter.propose(document=_document(), run_ref="run:test:1")
    assert registry.calls
    template, context = registry.calls[0]
    assert template == _PROMPT_REF
    assert context["run_ref"] == "run:test:1"


# Test 2
def test_propose_charges_token_budget_before_provider_call() -> None:
    adapter, _, provider, budget = _adapter()
    adapter.propose(document=_document(), run_ref="run:test:1")
    assert budget.estimates  # estimate ran
    assert provider.recorded  # provider got the request
    assert budget.charges  # charge ran with actual usage


# Test 3
def test_propose_raises_provider_trace_missing_when_raw_response_ref_blank() -> None:
    adapter, _, _, _ = _adapter(response=_response(raw_response_ref="   "))
    with pytest.raises(ProviderTraceMissingError):
        adapter.propose(document=_document(), run_ref="run:test:1")


# Test 4
def test_propose_projects_parsed_output_to_schema_proposal() -> None:
    adapter, _, _, _ = _adapter()
    proposal = adapter.propose(document=_document(), run_ref="run:test:1")
    assert proposal.proposed_fields[0].name == "title"


# Test 5
def test_propose_replay_refs_contain_all_seven_entries() -> None:
    adapter, _, _, _ = _adapter()
    proposal = adapter.propose(document=_document(), run_ref="run:test:1")
    assert len(proposal.replay_refs) == 7


# Test 6
def test_propose_rejects_provider_response_with_blank_parsed_output() -> None:
    adapter, _, _, _ = _adapter(response=_response(parsed_output={}))
    with pytest.raises(StructuredOutputViolation):
        adapter.propose(document=_document(), run_ref="run:test:1")


# Test 7 — implements port
def test_propose_implements_extraction_strategy_port() -> None:
    adapter, _, _, _ = _adapter()
    assert isinstance(adapter, ExtractionStrategyPort)


# Test 8 — pure for same canned response
def test_propose_is_pure_function_for_same_canned_response() -> None:
    adapter_a, _, _, _ = _adapter()
    adapter_b, _, _, _ = _adapter()
    proposal_a = adapter_a.propose(document=_document(), run_ref="run:test:1")
    proposal_b = adapter_b.propose(document=_document(), run_ref="run:test:1")
    assert proposal_a.canonical_json() == proposal_b.canonical_json()


# Test 9 — token charge happens before parsed-output validation
def test_propose_token_budget_charged_before_validation() -> None:
    adapter, _, _, budget = _adapter(response=_response(parsed_output={}))
    with pytest.raises(StructuredOutputViolation):
        adapter.propose(document=_document(), run_ref="run:test:1")
    assert budget.charges, "token budget must be charged before validation"


# Test 10 — replay_refs canonical order
def test_propose_replay_refs_canonical_order_pinned() -> None:
    adapter, _, _, _ = _adapter()
    proposal = adapter.propose(document=_document(), run_ref="run:test:1")
    refs = proposal.replay_refs
    # entries: [request_id, adapter_ref, prompt_template_ref,
    #          response_id, raw_response_ref, run_ref, doc_ref]
    assert refs[1] == "adapter:llm-extraction-strategy:v1"
    assert refs[2] == _PROMPT_REF
    assert refs[5] == "run:test:1"
    assert refs[6] == "normalized:test:1"


# Test 11 — provider request carries model_name + max_output_tokens (R7)
def test_propose_provider_request_includes_model_and_token_cap() -> None:
    adapter, _, provider, _ = _adapter()
    adapter.propose(document=_document(), run_ref="run:test:1")
    req = provider.recorded[0]
    assert req.model_name == "gpt-test"
    assert req.max_output_tokens == 256
