"""``LlmDriftDetector`` — s9 production ``DriftDetectionPort`` adapter."""

from __future__ import annotations

from pydantic import ValidationError

from veracrawl.adapters._llm_adapter_base import run_llm_adapter_flow
from veracrawl.contracts.common import Ref
from veracrawl.contracts.drift_report import DriftReport
from veracrawl.contracts.errors import StructuredOutputViolation
from veracrawl.contracts.extraction_outcome import ExtractionOutcome
from veracrawl.contracts.schema_proposal import SchemaProposal
from veracrawl.ports.model_provider_v2 import ModelProviderPortV2
from veracrawl.ports.prompt_registry import PromptRegistryPort
from veracrawl.ports.token_budget import TokenBudgetPort

_ADAPTER_REF = "adapter:llm-drift-detector:v1"


def _struct_violation() -> StructuredOutputViolation:
    return StructuredOutputViolation(
        status_code=200,
        error_code="STRUCTURED_OUTPUT_VIOLATION",
        request_id=None,
    )


class LlmDriftDetector:
    def __init__(
        self,
        *,
        provider: ModelProviderPortV2,
        prompt_registry: PromptRegistryPort,
        token_budget: TokenBudgetPort,
        prompt_template_ref: Ref,
        model_name: str,
        max_output_tokens: int,
        temperature: float = 0.0,
    ) -> None:
        self._provider = provider
        self._prompt_registry = prompt_registry
        self._token_budget = token_budget
        self._prompt_template_ref = prompt_template_ref
        self._model_name = model_name
        self._max_output_tokens = max_output_tokens
        self._temperature = temperature

    def detect(
        self,
        *,
        proposal: SchemaProposal,
        extraction_outcomes: list[ExtractionOutcome],
        run_ref: Ref,
    ) -> DriftReport:
        response = run_llm_adapter_flow(
            provider=self._provider,
            prompt_registry=self._prompt_registry,
            token_budget=self._token_budget,
            prompt_template_ref=self._prompt_template_ref,
            context={
                "proposal_ref": proposal.proposal_ref,
                "outcome_refs": [o.id for o in extraction_outcomes],
                "run_ref": run_ref,
            },
            request_id=f"provider-request:llm-drift:{proposal.id}",
            run_ref=run_ref,
            model_name=self._model_name,
            max_output_tokens=self._max_output_tokens,
            temperature=self._temperature,
        )
        parsed = response.parsed_output
        if not isinstance(parsed, dict) or not parsed:
            raise _struct_violation()
        try:
            return DriftReport(
                id=f"drift-report:{run_ref}:{response.id}",
                run_ref=run_ref,
                proposal_ref=proposal.proposal_ref,
                pages_evaluated=len(extraction_outcomes),
                field_missing_rates=parsed.get("field_missing_rates", {}),
                drifted_fields=parsed.get("drifted_fields", []),
                drift_threshold=parsed.get("drift_threshold", 0.30),
                replay_refs=[
                    f"provider-request:llm-drift:{proposal.id}",
                    _ADAPTER_REF,
                    self._prompt_template_ref,
                    response.id,
                    response.raw_response_ref or "",
                    run_ref,
                    proposal.proposal_ref,
                ],
            )
        except ValidationError as exc:
            del exc
            raise _struct_violation() from None


__all__ = ["LlmDriftDetector"]
