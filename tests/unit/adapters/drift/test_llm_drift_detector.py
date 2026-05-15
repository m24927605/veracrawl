"""Unit tests for ``LlmDriftDetector`` (s9)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import pytest

from veracrawl.adapters.drift.llm_drift_detector import LlmDriftDetector
from veracrawl.contracts.agent import TokenUsage
from veracrawl.contracts.enums import ProviderFinishReason
from veracrawl.contracts.errors import (
    ProviderTraceMissingError,
    StructuredOutputViolation,
)
from veracrawl.contracts.extraction_outcome import ExtractionOutcome
from veracrawl.contracts.llm_input import (
    ProviderRequest,
    ProviderResponse,
    TokenUsageEstimate,
)
from veracrawl.contracts.schema_proposal import ProposedField, SchemaProposal
from veracrawl.ports.drift_detection import DriftDetectionPort

_PROMPT_REF = "prompt:llm-drift:v1"


def _proposal() -> SchemaProposal:
    return SchemaProposal(
        id="schema-proposal:1",
        proposal_ref="proposal:run-1:hash",
        source_document_ref="normalized-doc:1",
        proposed_fields=[
            ProposedField(name="title", xpath="//h1", confidence=0.9,
                          evidence_anchor_count=3, proposed_type="string"),
        ],
        proposal_rationale_refs=["rationale:1"],
        replay_refs=["run:1"],
    )


def _outcomes() -> list[ExtractionOutcome]:
    return [
        ExtractionOutcome(
            id="outcome:1", run_ref="run:1",
            page_canonical_url="https://a.example/1",
            field_outcomes={"title": True}, replay_refs=["run:1"],
        ),
    ]


def _response(
    *, raw_response_ref: str | None = "artifact:sha256:def",
    parsed_output: dict[str, Any] | None = None,
) -> ProviderResponse:
    return ProviderResponse(
        id="provider-response:llm-drift:1",
        request_ref="provider-request:llm-drift:schema-proposal:1",
        text="canned",
        usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        finish_reason=ProviderFinishReason.STOP,
        parsed_output=parsed_output if parsed_output is not None else {
            "field_missing_rates": {"title": 0.4},
            "drifted_fields": ["title"],
            "drift_threshold": 0.30,
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
) -> tuple[LlmDriftDetector, _FakeRegistry, _FakeProvider, _FakeBudget]:
    registry = _FakeRegistry()
    provider = _FakeProvider(response or _response())
    budget = _FakeBudget()
    adapter = LlmDriftDetector(
        provider=provider, prompt_registry=registry, token_budget=budget,
        prompt_template_ref=_PROMPT_REF, model_name="gpt-test",
        max_output_tokens=512,
    )
    return adapter, registry, provider, budget


def test_detect_renders_prompt_via_registry() -> None:
    adapter, registry, _, _ = _adapter()
    adapter.detect(
        proposal=_proposal(), extraction_outcomes=_outcomes(), run_ref="run:1",
    )
    assert registry.calls[0][0] == _PROMPT_REF


def test_detect_charges_token_budget() -> None:
    adapter, _, _, budget = _adapter()
    adapter.detect(
        proposal=_proposal(), extraction_outcomes=_outcomes(), run_ref="run:1",
    )
    assert budget.estimates
    assert budget.charges


def test_detect_raises_provider_trace_missing_when_blank() -> None:
    adapter, _, _, _ = _adapter(response=_response(raw_response_ref=" "))
    with pytest.raises(ProviderTraceMissingError):
        adapter.detect(
            proposal=_proposal(), extraction_outcomes=_outcomes(), run_ref="run:1",
        )


def test_detect_projects_parsed_output_to_drift_report() -> None:
    adapter, _, _, _ = _adapter()
    report = adapter.detect(
        proposal=_proposal(), extraction_outcomes=_outcomes(), run_ref="run:1",
    )
    assert report.drifted_fields == ["title"]
    assert report.field_missing_rates["title"] == 0.4


def test_detect_replay_refs_contain_seven_entries() -> None:
    adapter, _, _, _ = _adapter()
    report = adapter.detect(
        proposal=_proposal(), extraction_outcomes=_outcomes(), run_ref="run:1",
    )
    assert len(report.replay_refs) == 7


def test_detect_rejects_empty_parsed_output() -> None:
    adapter, _, _, _ = _adapter(response=_response(parsed_output={}))
    with pytest.raises(StructuredOutputViolation):
        adapter.detect(
            proposal=_proposal(), extraction_outcomes=_outcomes(), run_ref="run:1",
        )


def test_detect_implements_drift_detection_port() -> None:
    adapter, _, _, _ = _adapter()
    assert isinstance(adapter, DriftDetectionPort)


def test_detect_is_pure_function_for_same_canned_response() -> None:
    adapter_a, _, _, _ = _adapter()
    adapter_b, _, _, _ = _adapter()
    report_a = adapter_a.detect(
        proposal=_proposal(), extraction_outcomes=_outcomes(), run_ref="run:1",
    )
    report_b = adapter_b.detect(
        proposal=_proposal(), extraction_outcomes=_outcomes(), run_ref="run:1",
    )
    assert report_a.canonical_json() == report_b.canonical_json()


def test_detect_token_charge_before_validation() -> None:
    adapter, _, _, budget = _adapter(response=_response(parsed_output={}))
    with pytest.raises(StructuredOutputViolation):
        adapter.detect(
            proposal=_proposal(), extraction_outcomes=_outcomes(), run_ref="run:1",
        )
    assert budget.charges


def test_detect_replay_refs_pin_adapter_ref() -> None:
    adapter, _, _, _ = _adapter()
    report = adapter.detect(
        proposal=_proposal(), extraction_outcomes=_outcomes(), run_ref="run:1",
    )
    assert "adapter:llm-drift-detector:v1" in report.replay_refs


def test_detect_provider_request_includes_model_and_token_cap() -> None:
    adapter, _, provider, _ = _adapter()
    adapter.detect(
        proposal=_proposal(), extraction_outcomes=_outcomes(), run_ref="run:1",
    )
    req = provider.recorded[0]
    assert req.model_name == "gpt-test"
    assert req.max_output_tokens == 512
