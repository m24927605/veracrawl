"""Phase 4 provider-swap acceptance test (fixture-mode).

Per ``phase-4-design.md`` (`Provider-swap test`): the same
``ProviderRequest`` issued through ``OpenAIResponsesAdapterV2``
and ``AnthropicMessagesAdapter`` must produce
**structurally-identical** ``ProviderResponse`` shapes — same
contract field set, both pass Pydantic validation, both
populate ``TokenUsage`` consistently. This is the
``ModelProviderPortV2`` provider-blind invariant: callers
build one ``ProviderRequest`` and don't branch on provider.

The live (real-API) provider-swap test is deferred to Phase 6
step 6.5 (real OpenAI / Anthropic credentials + cost
regression). Phase 4 ships the fixture-mode equivalent that
proves the contract surface.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from veracrawl.adapters.model_providers.anthropic_messages import (
    AnthropicMessagesAdapter,
)
from veracrawl.adapters.model_providers.openai_responses_v2 import (
    OpenAIResponsesAdapterV2,
)
from veracrawl.contracts.agent import Message, ResponseFormat
from veracrawl.contracts.enums import (
    MessageRole,
    ProviderFinishReason,
    ResponseFormatKind,
)
from veracrawl.contracts.llm_input import ProviderRequest, ProviderResponse
from veracrawl.runtime_support.runtime_mode import RuntimeMode

_OPENAI_API_KEY = "sk-PROVIDER-SWAP-CANARY-OPENAI"
_ANTHROPIC_API_KEY = "sk-ant-PROVIDER-SWAP-CANARY-ANTHROPIC"
_EXTRACTION_TEXT = '{"sku": "ABC-123", "title": "Widget Pro"}'


def _logical_request(model_name: str) -> ProviderRequest:
    """Build the same logical request adapted to each provider's
    model name. Everything else (messages, response_format,
    max_output_tokens, temperature) is identical.

    Uses ``JSON_OBJECT`` (not ``JSON_SCHEMA``) so both adapters
    populate ``parsed_output`` symmetrically — step 4.3 codex
    iter-2 settled the policy that ``JSON_SCHEMA`` requests
    must route through step 4.6 ``schema_runtime``, not the
    adapter directly."""

    return ProviderRequest(
        id=f"provider-swap:{model_name}:1",
        run_ref="run:provider-swap:1",
        model_name=model_name,
        messages=[
            Message(role=MessageRole.SYSTEM, content="You are a careful extractor."),
            Message(role=MessageRole.USER, content="Extract product details."),
        ],
        response_format=ResponseFormat(kind=ResponseFormatKind.JSON_OBJECT),
        max_output_tokens=256,
    )


def _openai_response_body() -> dict[str, Any]:
    return {
        "id": "resp:openai_swap_abcdef",
        "status": "completed",
        "output": [{"content": [{"type": "output_text", "text": _EXTRACTION_TEXT}]}],
        "usage": {
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150,
        },
    }


def _anthropic_response_body() -> dict[str, Any]:
    return {
        "id": "msg_anthropic_swap_abcdef",
        "model": "claude-sonnet-4-6",
        "content": [{"type": "text", "text": _EXTRACTION_TEXT}],
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": 100,
            "output_tokens": 50,
        },
    }


def _build_openai_adapter() -> OpenAIResponsesAdapterV2:
    return OpenAIResponsesAdapterV2(
        api_key=_OPENAI_API_KEY,
        runtime_mode=RuntimeMode.FIXTURE,
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json=_openai_response_body())
        ),
        sleep_fn=lambda _: None,
        jitter_fn=lambda: 0.0,
    )


def _build_anthropic_adapter() -> AnthropicMessagesAdapter:
    return AnthropicMessagesAdapter(
        api_key=_ANTHROPIC_API_KEY,
        runtime_mode=RuntimeMode.FIXTURE,
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json=_anthropic_response_body())
        ),
        sleep_fn=lambda _: None,
        jitter_fn=lambda: 0.0,
    )


def _assert_provider_response_shape(response: ProviderResponse) -> None:
    """Both adapters must populate the same ``ProviderResponse``
    contract surface — Pydantic validation already enforces
    field types; this asserts the semantic invariants the
    provider-blind contract claims."""

    assert response.id and response.id.strip()
    assert response.request_ref and response.request_ref.strip()
    assert response.text == _EXTRACTION_TEXT
    assert response.finish_reason is ProviderFinishReason.STOP
    # ``parsed_output`` is populated for both because the
    # logical request uses ``JSON_OBJECT`` (any-JSON-object
    # contract — JSON-decode + dict root fully satisfies).
    # ``JSON_SCHEMA`` requests would route through Phase 4
    # step 4.6 ``schema_runtime`` for full Pydantic-class
    # validation; the v2 adapters do not populate
    # ``parsed_output`` on ``JSON_SCHEMA`` (codex iter-2
    # settled policy).
    assert response.parsed_output == {"sku": "ABC-123", "title": "Widget Pro"}
    # Token usage shape is identical (the values come from the
    # different mocked bodies, but the contract is the same).
    assert response.usage.prompt_tokens == 100
    assert response.usage.completion_tokens == 50
    assert response.usage.total_tokens == 150
    assert response.usage.cached_input_tokens == 0


def test_provider_swap_produces_structurally_identical_response_shape() -> None:
    openai_adapter = _build_openai_adapter()
    anthropic_adapter = _build_anthropic_adapter()

    openai_response = openai_adapter.complete(
        _logical_request(model_name="gpt-4o-mini")
    )
    anthropic_response = anthropic_adapter.complete(
        _logical_request(model_name="claude-sonnet-4-6")
    )

    _assert_provider_response_shape(openai_response)
    _assert_provider_response_shape(anthropic_response)

    # The provider-blind contract: both responses are
    # ``ProviderResponse`` instances with the same field set
    # and types. Pydantic validation already proves this; the
    # test makes the invariant explicit so a future contract
    # change must update both adapters together.
    assert isinstance(openai_response, ProviderResponse)
    assert isinstance(anthropic_response, ProviderResponse)
    assert (
        type(openai_response).__name__ == type(anthropic_response).__name__
    )


def test_provider_swap_text_payload_matches_across_providers() -> None:
    """Both adapters extract the same ``text`` from their
    provider-specific response bodies. (The OpenAI body wraps
    text inside ``output[].content[].text``; Anthropic uses
    ``content[].text``. The provider-blind extraction must
    yield the same string.)"""

    openai_adapter = _build_openai_adapter()
    anthropic_adapter = _build_anthropic_adapter()

    openai_response = openai_adapter.complete(
        _logical_request(model_name="gpt-4o-mini")
    )
    anthropic_response = anthropic_adapter.complete(
        _logical_request(model_name="claude-sonnet-4-6")
    )

    assert openai_response.text == anthropic_response.text == _EXTRACTION_TEXT


def test_provider_swap_handles_provider_specific_finish_reason_mapping() -> None:
    """OpenAI ``status="completed"`` and Anthropic
    ``stop_reason="end_turn"`` both map to
    ``ProviderFinishReason.STOP`` — the v2 enum is the
    provider-blind shape callers reason about."""

    openai_adapter = _build_openai_adapter()
    anthropic_adapter = _build_anthropic_adapter()

    openai_response = openai_adapter.complete(
        _logical_request(model_name="gpt-4o-mini")
    )
    anthropic_response = anthropic_adapter.complete(
        _logical_request(model_name="claude-sonnet-4-6")
    )

    assert openai_response.finish_reason is ProviderFinishReason.STOP
    assert anthropic_response.finish_reason is ProviderFinishReason.STOP


def test_provider_swap_multi_turn_request_succeeds_on_both_providers() -> None:
    """Codex iter-5 minor: a provider-blind acceptance test
    must cover multi-turn conversations, not just a single
    system+user turn. Anthropic-specific normalization
    (alternating turns) is exercised here so a future
    refactor that breaks it surfaces in this test."""

    multi_turn_request_openai = ProviderRequest(
        id="provider-swap:multi:openai",
        run_ref="run:provider-swap:multi",
        model_name="gpt-4o-mini",
        messages=[
            Message(role=MessageRole.SYSTEM, content="You are a careful extractor."),
            Message(role=MessageRole.USER, content="Context chunk A"),
            Message(role=MessageRole.USER, content="Context chunk B"),
            Message(role=MessageRole.ASSISTANT, content="Acknowledged"),
            Message(role=MessageRole.USER, content="Now extract."),
        ],
        response_format=ResponseFormat(kind=ResponseFormatKind.TEXT),
        max_output_tokens=128,
    )
    multi_turn_request_anthropic = ProviderRequest(
        id="provider-swap:multi:anthropic",
        run_ref="run:provider-swap:multi",
        model_name="claude-sonnet-4-6",
        messages=multi_turn_request_openai.messages,
        response_format=ResponseFormat(kind=ResponseFormatKind.TEXT),
        max_output_tokens=128,
    )

    openai_adapter = OpenAIResponsesAdapterV2(
        api_key=_OPENAI_API_KEY,
        runtime_mode=RuntimeMode.FIXTURE,
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json=_openai_response_body())
        ),
        sleep_fn=lambda _: None,
        jitter_fn=lambda: 0.0,
    )
    anthropic_adapter = AnthropicMessagesAdapter(
        api_key=_ANTHROPIC_API_KEY,
        runtime_mode=RuntimeMode.FIXTURE,
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json=_anthropic_response_body())
        ),
        sleep_fn=lambda _: None,
        jitter_fn=lambda: 0.0,
    )

    openai_response = openai_adapter.complete(multi_turn_request_openai)
    anthropic_response = anthropic_adapter.complete(multi_turn_request_anthropic)

    # Both adapters complete the multi-turn request without
    # raising; the provider-specific shaping (Anthropic
    # alternating-turn normalization, OpenAI developer-role
    # mapping) is the adapter's job and must not surface as
    # a wire-shape failure to the caller.
    assert openai_response.finish_reason is ProviderFinishReason.STOP
    assert anthropic_response.finish_reason is ProviderFinishReason.STOP


def test_provider_swap_json_schema_refused_at_adapter_boundary_both_sides() -> None:
    """Codex iter-4 critical: refuse ``JSON_SCHEMA`` at the
    adapter boundary symmetrically across both providers.
    Full JSON Schema validation is Phase 4 step 4.6
    ``schema_runtime`` (Pydantic-class round-trip); routing
    ``JSON_SCHEMA`` to either v2 adapter directly bypasses
    the validator and lets unvalidated extractions claim
    contract conformance. Refusal at the adapter is the
    documented migration boundary."""

    schema_request_openai = ProviderRequest(
        id="provider-swap:json_schema:openai",
        run_ref="run:provider-swap:json_schema",
        model_name="gpt-4o-mini",
        messages=[Message(role=MessageRole.USER, content="extract")],
        response_format=ResponseFormat(
            kind=ResponseFormatKind.JSON_SCHEMA,
            schema_name="product",
            json_schema={
                "type": "object",
                "properties": {"sku": {"type": "string"}},
                "required": ["sku"],
            },
            strict=True,
        ),
        max_output_tokens=128,
    )
    schema_request_anthropic = ProviderRequest(
        id="provider-swap:json_schema:anthropic",
        run_ref="run:provider-swap:json_schema",
        model_name="claude-sonnet-4-6",
        messages=[Message(role=MessageRole.USER, content="extract")],
        response_format=ResponseFormat(
            kind=ResponseFormatKind.JSON_SCHEMA,
            schema_name="product",
            json_schema={
                "type": "object",
                "properties": {"sku": {"type": "string"}},
                "required": ["sku"],
            },
            strict=True,
        ),
        max_output_tokens=128,
    )

    openai_adapter = _build_openai_adapter()
    anthropic_adapter = _build_anthropic_adapter()
    with pytest.raises(NotImplementedError, match="schema_runtime"):
        openai_adapter.complete(schema_request_openai)
    with pytest.raises(NotImplementedError, match="schema_runtime"):
        anthropic_adapter.complete(schema_request_anthropic)


@pytest.mark.parametrize(
    ("openai_status", "anthropic_stop_reason"),
    [
        ("max_output_tokens", "max_tokens"),
    ],
)
def test_provider_swap_length_finish_reason_maps_consistently(
    openai_status: str, anthropic_stop_reason: str
) -> None:
    """Provider-specific length-stop signals must map to the
    same ``ProviderFinishReason.LENGTH`` value."""

    def openai_body() -> dict[str, Any]:
        body = _openai_response_body()
        body["status"] = openai_status
        body["output"] = []  # plausible: hit cap before any text
        return body

    def anthropic_body() -> dict[str, Any]:
        body = _anthropic_response_body()
        body["stop_reason"] = anthropic_stop_reason
        body["content"] = []
        return body

    openai_adapter = OpenAIResponsesAdapterV2(
        api_key=_OPENAI_API_KEY,
        runtime_mode=RuntimeMode.FIXTURE,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=openai_body())),
        sleep_fn=lambda _: None,
        jitter_fn=lambda: 0.0,
    )
    anthropic_adapter = AnthropicMessagesAdapter(
        api_key=_ANTHROPIC_API_KEY,
        runtime_mode=RuntimeMode.FIXTURE,
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json=anthropic_body())
        ),
        sleep_fn=lambda _: None,
        jitter_fn=lambda: 0.0,
    )

    openai_response = openai_adapter.complete(
        _logical_request(model_name="gpt-4o-mini")
    )
    anthropic_response = anthropic_adapter.complete(
        _logical_request(model_name="claude-sonnet-4-6")
    )

    assert openai_response.finish_reason is ProviderFinishReason.LENGTH
    assert anthropic_response.finish_reason is ProviderFinishReason.LENGTH
