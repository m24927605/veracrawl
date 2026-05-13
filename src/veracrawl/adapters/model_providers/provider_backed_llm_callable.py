"""Wraps :class:`ModelProviderPortV2` as an :class:`LlmExtractCallable`.

Lets :class:`LlmAssistedExtractor` use any structured-output-capable
provider (OpenAI Responses, Anthropic Messages, fixture replay …)
without leaking provider-specific types into the extractor.

Contract:

* The callable builds a JSON-schema-bound :class:`ProviderRequest`,
  hands it to ``provider.complete``, and parses ``parsed_output``
  into :class:`LlmFieldGuess` records.
* Entries missing ``field_name`` / ``value`` / ``evidence_quote``
  are dropped (rather than raising) so a partially-malformed
  response does not lose the well-formed entries.
* If ``parsed_output`` is absent (provider declined structured
  output), the callable returns an empty :class:`LlmExtractResponse`;
  :class:`LlmAssistedExtractor` then routes the document to
  ``needs_review``.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from veracrawl.adapters.model_providers.llm_assisted_extractor import (
    LlmExtractResponse,
    LlmFieldGuess,
)
from veracrawl.contracts.agent import Message, ResponseFormat
from veracrawl.contracts.enums import MessageRole, ResponseFormatKind
from veracrawl.contracts.llm_input import ProviderRequest
from veracrawl.ports.extractor import ExtractionRequest
from veracrawl.ports.model_provider_v2 import ModelProviderPortV2

_FIELD_GUESS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "field_guesses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field_name": {"type": "string"},
                    "value": {"type": "string"},
                    "evidence_quote": {"type": "string"},
                },
                "required": ["field_name", "value", "evidence_quote"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["field_guesses"],
    "additionalProperties": False,
}


def _build_user_message(request: ExtractionRequest) -> str:
    # Provider sees only the normalised text + content type. The raw
    # body is *not* forwarded — we don't want the model citing tag
    # text it can't anchor against the normalised string.
    return (
        f"Source URL: {request.canonical_url}\n"
        f"Content type: {request.content_type}\n"
        f"---BEGIN NORMALISED TEXT---\n"
        f"{request.normalized_text}\n"
        f"---END NORMALISED TEXT---\n"
        "Return a structured extraction. Every field guess must include "
        "an evidence_quote that appears verbatim in the text above."
    )


@dataclass(slots=True)
class ProviderBackedLlmCallable:
    provider: ModelProviderPortV2
    model_name: str
    system_prompt: str
    max_output_tokens: int = 1024

    def __call__(self, request: ExtractionRequest) -> LlmExtractResponse:
        provider_request = ProviderRequest(
            id=f"req-{uuid.uuid4().hex}",
            run_ref=f"run:{request.canonical_url}",
            model_name=self.model_name,
            messages=[
                Message(role=MessageRole.SYSTEM, content=self.system_prompt),
                Message(role=MessageRole.USER, content=_build_user_message(request)),
            ],
            response_format=ResponseFormat(
                kind=ResponseFormatKind.JSON_SCHEMA,
                schema_name="veracrawl.extraction.field_guesses.v1",
                json_schema=_FIELD_GUESS_SCHEMA,
                strict=True,
            ),
            max_output_tokens=self.max_output_tokens,
            temperature=0.0,
        )
        response = self.provider.complete(provider_request)
        parsed = response.parsed_output
        if not isinstance(parsed, dict):
            return LlmExtractResponse(field_guesses=[])
        raw_guesses = parsed.get("field_guesses")
        if not isinstance(raw_guesses, list):
            return LlmExtractResponse(field_guesses=[])
        guesses: list[LlmFieldGuess] = []
        for entry in raw_guesses:
            if not isinstance(entry, dict):
                continue
            field_name = entry.get("field_name")
            value = entry.get("value")
            quote = entry.get("evidence_quote")
            if (
                isinstance(field_name, str)
                and isinstance(value, str)
                and isinstance(quote, str)
                and field_name.strip()
                and quote.strip()
            ):
                guesses.append(
                    LlmFieldGuess(
                        field_name=field_name,
                        value=value,
                        evidence_quote=quote,
                    )
                )
        return LlmExtractResponse(field_guesses=guesses)


__all__ = ["ProviderBackedLlmCallable"]
