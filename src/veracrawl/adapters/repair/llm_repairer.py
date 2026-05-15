"""``LlmRepairer`` — s9 production ``RepairPort`` adapter."""

from __future__ import annotations

from collections.abc import Callable

from pydantic import ValidationError

from veracrawl.adapters._llm_adapter_base import run_llm_adapter_flow
from veracrawl.contracts.common import Ref
from veracrawl.contracts.drift_report import DriftReport
from veracrawl.contracts.errors import StructuredOutputViolation
from veracrawl.contracts.normalized_document_read_model import (
    NormalizedDocumentReadModel,
)
from veracrawl.contracts.repair_proposal import RepairProposal
from veracrawl.ports.model_provider_v2 import ModelProviderPortV2
from veracrawl.ports.prompt_registry import PromptRegistryPort
from veracrawl.ports.token_budget import TokenBudgetPort

_ADAPTER_REF = "adapter:llm-repairer:v1"


def _struct_violation() -> StructuredOutputViolation:
    return StructuredOutputViolation(
        status_code=200,
        error_code="STRUCTURED_OUTPUT_VIOLATION",
        request_id=None,
    )


class LlmRepairer:
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

    def repair(
        self,
        *,
        drift_report: DriftReport,
        document_samples: list[NormalizedDocumentReadModel],
        resolve_text: Callable[[Ref], str],
        run_ref: Ref,
    ) -> RepairProposal:
        del resolve_text  # consumed by future prompt-template expansion; ref-only flow
        response = run_llm_adapter_flow(
            provider=self._provider,
            prompt_registry=self._prompt_registry,
            token_budget=self._token_budget,
            prompt_template_ref=self._prompt_template_ref,
            context={
                "drift_report_ref": drift_report.id,
                "drifted_fields": list(drift_report.drifted_fields),
                "document_sample_refs": [d.id for d in document_samples],
                "run_ref": run_ref,
            },
            request_id=f"provider-request:llm-repair:{drift_report.id}",
            run_ref=run_ref,
            model_name=self._model_name,
            max_output_tokens=self._max_output_tokens,
            temperature=self._temperature,
        )
        parsed = response.parsed_output
        if not isinstance(parsed, dict) or not parsed:
            raise _struct_violation()
        try:
            return RepairProposal(
                id=f"repair:{run_ref}:{response.id}",
                run_ref=run_ref,
                drift_report_ref=drift_report.id,
                field_repairs=parsed.get("field_repairs", []),
                replay_refs=[
                    f"provider-request:llm-repair:{drift_report.id}",
                    _ADAPTER_REF,
                    self._prompt_template_ref,
                    response.id,
                    response.raw_response_ref or "",
                    run_ref,
                    drift_report.id,
                ],
            )
        except ValidationError as exc:
            del exc
            raise _struct_violation() from None


__all__ = ["LlmRepairer"]
