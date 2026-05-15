"""Unit tests for ``LlmRepairer`` (s9)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import pytest

from veracrawl.adapters.repair.llm_repairer import LlmRepairer
from veracrawl.contracts.agent import TokenUsage
from veracrawl.contracts.drift_report import DriftReport
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
from veracrawl.ports.repair import RepairPort

_PROMPT_REF = "prompt:llm-repair:v1"


def _drift_report() -> DriftReport:
    return DriftReport(
        id="drift:run-1:1", run_ref="run:1",
        proposal_ref="proposal:run-1:hash",
        pages_evaluated=5,
        field_missing_rates={"price": 0.6},
        drifted_fields=["price"],
        drift_threshold=0.30,
        replay_refs=["run:1"],
    )


def _document() -> NormalizedDocumentReadModel:
    return NormalizedDocumentReadModel(
        id="doc:1",
        normalized_document_ref="normalized:1",
        text_sample_refs=["sample:1"],
    )


def _response(
    *, raw_response_ref: str | None = "artifact:sha256:repair",
    parsed_output: dict[str, Any] | None = None,
) -> ProviderResponse:
    return ProviderResponse(
        id="provider-response:llm-repair:1",
        request_ref="provider-request:llm-repair:drift:run-1:1",
        text="canned",
        usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        finish_reason=ProviderFinishReason.STOP,
        parsed_output=parsed_output if parsed_output is not None else {
            "field_repairs": [{
                "field_name": "price",
                "original_xpath": "//span[@class='price']",
                "proposed_xpath": "//div[@class='product']//span",
                "confidence": 0.8,
                "repair_kind": "anchor_reselect",
            }],
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
) -> tuple[LlmRepairer, _FakeRegistry, _FakeProvider, _FakeBudget]:
    registry = _FakeRegistry()
    provider = _FakeProvider(response or _response())
    budget = _FakeBudget()
    adapter = LlmRepairer(
        provider=provider, prompt_registry=registry, token_budget=budget,
        prompt_template_ref=_PROMPT_REF, model_name="gpt-test",
        max_output_tokens=512,
    )
    return adapter, registry, provider, budget


def test_repair_renders_prompt_via_registry() -> None:
    adapter, registry, _, _ = _adapter()
    adapter.repair(
        drift_report=_drift_report(), document_samples=[_document()],
        resolve_text=lambda _ref: "", run_ref="run:1",
    )
    assert registry.calls[0][0] == _PROMPT_REF


def test_repair_charges_token_budget() -> None:
    adapter, _, _, budget = _adapter()
    adapter.repair(
        drift_report=_drift_report(), document_samples=[_document()],
        resolve_text=lambda _ref: "", run_ref="run:1",
    )
    assert budget.estimates
    assert budget.charges


def test_repair_raises_provider_trace_missing_when_blank() -> None:
    adapter, _, _, _ = _adapter(response=_response(raw_response_ref=""))
    with pytest.raises(ProviderTraceMissingError):
        adapter.repair(
            drift_report=_drift_report(), document_samples=[_document()],
            resolve_text=lambda _ref: "", run_ref="run:1",
        )


def test_repair_projects_parsed_output_to_repair_proposal() -> None:
    adapter, _, _, _ = _adapter()
    proposal = adapter.repair(
        drift_report=_drift_report(), document_samples=[_document()],
        resolve_text=lambda _ref: "", run_ref="run:1",
    )
    assert proposal.field_repairs[0].field_name == "price"


def test_repair_replay_refs_contain_seven_entries() -> None:
    adapter, _, _, _ = _adapter()
    proposal = adapter.repair(
        drift_report=_drift_report(), document_samples=[_document()],
        resolve_text=lambda _ref: "", run_ref="run:1",
    )
    assert len(proposal.replay_refs) == 7


def test_repair_rejects_empty_parsed_output() -> None:
    adapter, _, _, _ = _adapter(response=_response(parsed_output={}))
    with pytest.raises(StructuredOutputViolation):
        adapter.repair(
            drift_report=_drift_report(), document_samples=[_document()],
            resolve_text=lambda _ref: "", run_ref="run:1",
        )


def test_repair_implements_repair_port() -> None:
    adapter, _, _, _ = _adapter()
    assert isinstance(adapter, RepairPort)


def test_repair_is_pure_function_for_same_canned_response() -> None:
    adapter_a, _, _, _ = _adapter()
    adapter_b, _, _, _ = _adapter()
    a = adapter_a.repair(
        drift_report=_drift_report(), document_samples=[_document()],
        resolve_text=lambda _ref: "", run_ref="run:1",
    )
    b = adapter_b.repair(
        drift_report=_drift_report(), document_samples=[_document()],
        resolve_text=lambda _ref: "", run_ref="run:1",
    )
    assert a.canonical_json() == b.canonical_json()


def test_repair_token_charge_before_validation() -> None:
    adapter, _, _, budget = _adapter(response=_response(parsed_output={}))
    with pytest.raises(StructuredOutputViolation):
        adapter.repair(
            drift_report=_drift_report(), document_samples=[_document()],
            resolve_text=lambda _ref: "", run_ref="run:1",
        )
    assert budget.charges


def test_repair_replay_refs_pin_adapter_ref() -> None:
    adapter, _, _, _ = _adapter()
    proposal = adapter.repair(
        drift_report=_drift_report(), document_samples=[_document()],
        resolve_text=lambda _ref: "", run_ref="run:1",
    )
    assert "adapter:llm-repairer:v1" in proposal.replay_refs


def test_repair_provider_request_includes_model_and_token_cap() -> None:
    adapter, _, provider, _ = _adapter()
    adapter.repair(
        drift_report=_drift_report(), document_samples=[_document()],
        resolve_text=lambda _ref: "", run_ref="run:1",
    )
    req = provider.recorded[0]
    assert req.model_name == "gpt-test"
    assert req.max_output_tokens == 512
