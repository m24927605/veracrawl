"""Shared LLM-adapter flow used by s9.

Factors out the prompt-render → token-budget-estimate →
provider-complete → token-budget-charge → raw-response-ref guard
flow that all three s9 adapters (extraction strategy, drift
detector, repairer) share. Adapter-specific projection of
``ProviderResponse.parsed_output`` into the typed result contract
remains in the caller.

See ``docs/plans/general-purpose-crawler-agentification/
s9-llm-adapters-extraction.md``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from veracrawl.contracts.agent import Message, ResponseFormat
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import MessageRole, ResponseFormatKind
from veracrawl.contracts.errors import ProviderTraceMissingError
from veracrawl.contracts.llm_input import (
    ProviderRequest,
    ProviderResponse,
)
from veracrawl.ports.model_provider_v2 import ModelProviderPortV2
from veracrawl.ports.prompt_registry import PromptRegistryPort
from veracrawl.ports.token_budget import TokenBudgetPort


def run_llm_adapter_flow(
    *,
    provider: ModelProviderPortV2,
    prompt_registry: PromptRegistryPort,
    token_budget: TokenBudgetPort,
    prompt_template_ref: Ref,
    context: Mapping[str, Any],
    request_id: str,
    run_ref: Ref,
    model_name: str,
    max_output_tokens: int,
    temperature: float = 0.0,
) -> ProviderResponse:
    """Execute the s9-shared LLM-adapter flow.

    Raises:
        ProviderTraceMissingError: if ``raw_response_ref`` is blank.
    """

    rendered = prompt_registry.render(prompt_template_ref, context)
    provider_request = ProviderRequest(
        id=request_id,
        run_ref=run_ref,
        model_name=model_name,
        messages=[Message(role=MessageRole.USER, content=rendered)],
        response_format=ResponseFormat(kind=ResponseFormatKind.JSON_OBJECT),
        max_output_tokens=max_output_tokens,
        temperature=temperature,
    )
    token_budget.estimate_charge(provider_request)
    response = provider.complete(provider_request)
    # Charge BEFORE downstream projection so malformed-output paths
    # still account for the tokens the provider billed (mirrors s2).
    token_budget.charge(response.usage, request_ref=provider_request.id)
    if response.raw_response_ref is None or not response.raw_response_ref.strip():
        raise ProviderTraceMissingError(provider_request_id=provider_request.id)
    return response


__all__ = ["run_llm_adapter_flow"]
