"""Unit tests for :class:`ProviderBackedLlmCallable`.

The callable wraps a :class:`ModelProviderPortV2` impl so the
LlmAssistedExtractor can use any structured-output-capable LLM
provider. A stub provider lets these tests exercise the
contract without a real network call.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from veracrawl.adapters.model_providers.llm_assisted_extractor import (
    LlmExtractResponse,
)
from veracrawl.adapters.model_providers.provider_backed_llm_callable import (
    ProviderBackedLlmCallable,
)
from veracrawl.contracts.agent import TokenUsage
from veracrawl.contracts.enums import ModelCapability, ProviderFinishReason
from veracrawl.contracts.llm_input import ProviderRequest, ProviderResponse
from veracrawl.external_crawl.normalize_document import normalize_document
from veracrawl.ports.extractor import ExtractionRequest


@dataclass
class _StubProvider:
    parsed_output: dict[str, Any] | None
    text: str = ""
    finish_reason: ProviderFinishReason = ProviderFinishReason.STOP
    last_request: ProviderRequest | None = None

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        self.last_request = request
        return ProviderResponse(
            id="resp-1",
            request_ref=request.id,
            text=self.text or "ok",
            usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
            ),
            finish_reason=self.finish_reason,
            parsed_output=self.parsed_output,
        )

    def supports(self, capability: ModelCapability) -> bool:
        return True


def _extraction_request() -> ExtractionRequest:
    html = b"<html><body><h1>Hello world</h1></body></html>"
    normalized = normalize_document(
        canonical_url="https://example.com/",
        body=html,
        content_type="text/html",
        raw_artifact_ref="raw-html/abc",
    )
    return ExtractionRequest(
        canonical_url="https://example.com/",
        normalized_text=normalized.text,
        raw_body=html,
        content_type="text/html",
        raw_artifact_ref="raw-html/abc",
        anchors=list(normalized.anchors),
    )


def test_provider_backed_callable_returns_field_guesses_from_parsed_output() -> None:
    provider = _StubProvider(
        parsed_output={
            "field_guesses": [
                {
                    "field_name": "title",
                    "value": "Hello world",
                    "evidence_quote": "Hello world",
                }
            ]
        }
    )
    callable_ = ProviderBackedLlmCallable(
        provider=provider,
        model_name="stub-model",
        system_prompt="extract titles",
    )
    response = callable_(_extraction_request())
    assert isinstance(response, LlmExtractResponse)
    assert len(response.field_guesses) == 1
    assert response.field_guesses[0].value == "Hello world"


def test_provider_backed_callable_builds_json_schema_request() -> None:
    provider = _StubProvider(parsed_output={"field_guesses": []})
    callable_ = ProviderBackedLlmCallable(
        provider=provider,
        model_name="stub-model",
        system_prompt="extract titles",
    )
    callable_(_extraction_request())
    assert provider.last_request is not None
    assert provider.last_request.response_format.kind.value == "json_schema"
    assert provider.last_request.response_format.json_schema is not None
    assert provider.last_request.model_name == "stub-model"


def test_provider_backed_callable_handles_missing_parsed_output() -> None:
    # Provider returned text only (no parsed_output). Callable
    # should return empty guesses rather than crash; the LLM
    # extractor will then emit needs_review.
    provider = _StubProvider(parsed_output=None, text="raw text from provider")
    callable_ = ProviderBackedLlmCallable(
        provider=provider,
        model_name="stub-model",
        system_prompt="extract titles",
    )
    response = callable_(_extraction_request())
    assert response.field_guesses == []


def test_provider_backed_callable_drops_malformed_guess_entries() -> None:
    provider = _StubProvider(
        parsed_output={
            "field_guesses": [
                {"field_name": "title", "value": "X", "evidence_quote": "X"},
                {"field_name": "missing_value"},  # malformed
                {"value": "Y", "evidence_quote": "Y"},  # missing name
                {
                    "field_name": "ok",
                    "value": "Z",
                    "evidence_quote": "Z",
                },
            ]
        }
    )
    callable_ = ProviderBackedLlmCallable(
        provider=provider,
        model_name="stub-model",
        system_prompt="extract",
    )
    response = callable_(_extraction_request())
    # Two valid entries survive; two are dropped.
    assert [g.field_name for g in response.field_guesses] == ["title", "ok"]
