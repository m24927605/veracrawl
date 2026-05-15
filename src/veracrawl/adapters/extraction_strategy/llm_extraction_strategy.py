"""``LlmExtractionStrategy`` — s9 production ``ExtractionStrategyPort`` adapter.

Calls a v2 model provider with a rendered template, validates the
provider response carries a non-blank ``raw_response_ref`` (replay
invariant), and projects ``parsed_output`` into a ``SchemaProposal``.
``replay_refs`` mirror s2's seven-entry shape.

See ``docs/plans/general-purpose-crawler-agentification/
s9-llm-adapters-extraction.md``.
"""

from __future__ import annotations

from pydantic import ValidationError

from veracrawl.adapters._llm_adapter_base import run_llm_adapter_flow
from veracrawl.contracts.common import Ref
from veracrawl.contracts.errors import StructuredOutputViolation
from veracrawl.contracts.normalized_document_read_model import (
    NormalizedDocumentReadModel,
)
from veracrawl.contracts.schema_proposal import SchemaProposal
from veracrawl.ports.model_provider_v2 import ModelProviderPortV2
from veracrawl.ports.prompt_registry import PromptRegistryPort
from veracrawl.ports.token_budget import TokenBudgetPort

_ADAPTER_REF = "adapter:llm-extraction-strategy:v1"


def _struct_violation() -> StructuredOutputViolation:
    return StructuredOutputViolation(
        status_code=200,
        error_code="STRUCTURED_OUTPUT_VIOLATION",
        request_id=None,
    )


class LlmExtractionStrategy:
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

    def propose(
        self,
        *,
        document: NormalizedDocumentReadModel,
        run_ref: Ref,
    ) -> SchemaProposal:
        response = run_llm_adapter_flow(
            provider=self._provider,
            prompt_registry=self._prompt_registry,
            token_budget=self._token_budget,
            prompt_template_ref=self._prompt_template_ref,
            context={
                "document_ref": document.normalized_document_ref,
                "text_sample_refs": list(document.text_sample_refs),
                "run_ref": run_ref,
            },
            request_id=f"provider-request:llm-extraction:{document.id}",
            run_ref=run_ref,
            model_name=self._model_name,
            max_output_tokens=self._max_output_tokens,
            temperature=self._temperature,
        )
        parsed = response.parsed_output
        if not isinstance(parsed, dict) or not parsed:
            raise _struct_violation()
        try:
            proposal = SchemaProposal(
                id=f"schema-proposal:{run_ref}:{document.id}",
                proposal_ref=f"proposal:{run_ref}:{response.id}",
                source_document_ref=document.normalized_document_ref,
                proposed_fields=parsed.get("proposed_fields", []),
                proposal_rationale_refs=[
                    f"rationale:{_ADAPTER_REF}:{self._prompt_template_ref}",
                ],
                replay_refs=[
                    f"provider-request:llm-extraction:{document.id}",
                    _ADAPTER_REF,
                    self._prompt_template_ref,
                    response.id,
                    response.raw_response_ref or "",
                    run_ref,
                    document.normalized_document_ref,
                ],
            )
        except ValidationError as exc:
            del exc
            raise _struct_violation() from None
        return proposal


__all__ = ["LlmExtractionStrategy"]
