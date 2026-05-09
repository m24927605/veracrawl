"""Phase 4 step 4.3 — AnthropicMessagesAdapter integration tests.

Mirrors the Phase 4 step 4.2 ``test_step_4_2_openai_responses_v2.py``
test plan one-for-one with Anthropic-specific wire-shape
assertions. The provider-swap acceptance test (same
``ProviderRequest`` against both adapters) lives at
``test_phase_4_provider_swap.py``.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from veracrawl.adapters.model_providers.anthropic_messages import (
    AnthropicMessagesAdapter,
)
from veracrawl.contracts.agent import Message, ResponseFormat, ToolSpec
from veracrawl.contracts.enums import (
    MessageRole,
    ModelCapability,
    ProviderFinishReason,
    ResponseFormatKind,
)
from veracrawl.contracts.errors import (
    ProviderAdapterFailure,
    ProviderAuthFailed,
    ProviderServerError,
    StructuredOutputViolation,
)
from veracrawl.contracts.llm_input import ProviderRequest
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
)

_API_KEY_CANARY = "sk-ant-LIVE-CANARY-DEADBEEF-must-not-leak"


def _build_request(
    *,
    response_format: ResponseFormat | None = None,
    user_text: str = "extract product details",
    system_prompt: str | None = None,
) -> ProviderRequest:
    msgs: list[Message] = []
    if system_prompt is not None:
        msgs.append(Message(role=MessageRole.SYSTEM, content=system_prompt))
    msgs.append(Message(role=MessageRole.USER, content=user_text))
    return ProviderRequest(
        id="provider-request:phase-4-3:1",
        run_ref="run:phase-4-3:1",
        model_name="claude-sonnet-4-6",
        messages=msgs,
        response_format=response_format
        or ResponseFormat(kind=ResponseFormatKind.TEXT),
        max_output_tokens=256,
    )


def _ok_response_body(
    *,
    text: str = "extracted",
    stop_reason: str = "end_turn",
    input_tokens: int = 100,
    output_tokens: int = 50,
) -> dict[str, Any]:
    return {
        "id": "msg_anthropic_abcdef",
        "model": "claude-sonnet-4-6",
        "content": [{"type": "text", "text": text}],
        "stop_reason": stop_reason,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        },
    }


def _build_adapter(
    handler: Any,
    *,
    max_attempts: int = 3,
) -> AnthropicMessagesAdapter:
    return AnthropicMessagesAdapter(
        api_key=_API_KEY_CANARY,
        max_attempts=max_attempts,
        runtime_mode=RuntimeMode.FIXTURE,
        transport=httpx.MockTransport(handler),
        sleep_fn=lambda _: None,
        jitter_fn=lambda: 0.0,
    )


# --- Construction gates -----------------------------------------------------


def test_production_mode_raises_production_runtime_not_implemented() -> None:
    with pytest.raises(ProductionRuntimeNotImplemented):
        AnthropicMessagesAdapter(
            api_key=_API_KEY_CANARY,
            runtime_mode=RuntimeMode.PRODUCTION,
        )


def test_blank_api_key_rejected() -> None:
    with pytest.raises(ValueError, match="non-blank api_key"):
        AnthropicMessagesAdapter(api_key="   ")


def test_zero_max_attempts_rejected() -> None:
    with pytest.raises(ValueError, match="max_attempts must be"):
        AnthropicMessagesAdapter(
            api_key=_API_KEY_CANARY,
            max_attempts=0,
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json={})),
        )


def test_fixture_mode_requires_explicit_transport() -> None:
    with pytest.raises(ValueError, match="explicit httpx.MockTransport"):
        AnthropicMessagesAdapter(api_key=_API_KEY_CANARY)


def test_fixture_mode_refuses_real_network_transport() -> None:
    with pytest.raises(ValueError, match="only accepts httpx.MockTransport"):
        AnthropicMessagesAdapter(
            api_key=_API_KEY_CANARY,
            transport=httpx.HTTPTransport(),
            runtime_mode=RuntimeMode.FIXTURE,
        )


def test_constructor_consults_current_mode_when_runtime_mode_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VERACRAWL_RUNTIME_MODE", "production")
    with pytest.raises(ProductionRuntimeNotImplemented):
        AnthropicMessagesAdapter(
            api_key=_API_KEY_CANARY,
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json=_ok_response_body())
            ),
        )


# --- Capability table -------------------------------------------------------


def test_supports_returns_documented_capabilities() -> None:
    """Every flag returns ``False`` per Phase 4 step 4.2 iter-5
    settled policy: capabilities flip to ``True`` only when the
    backing implementation lands."""

    adapter = _build_adapter(lambda _: httpx.Response(200, json=_ok_response_body()))
    for cap in ModelCapability:
        assert adapter.supports(cap) is False, f"{cap} should be deferred"


# --- Happy path -------------------------------------------------------------


def test_complete_text_response_returns_provider_response() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json=_ok_response_body(text="widget pro"))

    adapter = _build_adapter(handler)
    response = adapter.complete(_build_request())

    assert response.text == "widget pro"
    assert response.finish_reason is ProviderFinishReason.STOP
    assert response.parsed_output is None
    assert response.usage.prompt_tokens == 100
    assert response.usage.completion_tokens == 50
    assert response.usage.total_tokens == 150
    body = json.loads(captured[0].content)
    assert body["model"] == "claude-sonnet-4-6"
    assert body["max_tokens"] == 256
    assert body["temperature"] == 0.0
    assert body["messages"][0]["role"] == "user"
    assert "system" not in body  # no SYSTEM message in this request
    # Anthropic auth header shape (NOT Bearer).
    assert captured[0].headers["x-api-key"] == _API_KEY_CANARY
    assert captured[0].headers["anthropic-version"] == "2023-06-01"


def test_multi_block_text_response_joins_with_newline_separator() -> None:
    """Codex iter-3 critical: joining Anthropic text blocks
    with an empty separator can corrupt content. Block
    boundaries are preserved with ``"\\n"`` so adjacent
    chunks (``"hello"`` + ``"world"``) don't collapse to
    ``"helloworld"``."""

    def handler(_: httpx.Request) -> httpx.Response:
        body = _ok_response_body()
        body["content"] = [
            {"type": "text", "text": "First paragraph."},
            {"type": "text", "text": "Second paragraph."},
        ]
        return httpx.Response(200, json=body)

    adapter = _build_adapter(handler)
    response = adapter.complete(_build_request())
    assert response.text == "First paragraph.\nSecond paragraph."


def test_system_message_hoisted_to_top_level_system_field() -> None:
    """Anthropic dedicates a ``system`` body field; the
    ``messages`` array carries USER/ASSISTANT only."""

    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json=_ok_response_body())

    adapter = _build_adapter(handler)
    adapter.complete(_build_request(system_prompt="You are a careful extractor."))

    body = json.loads(captured[0].content)
    assert body["system"] == "You are a careful extractor."
    # The SYSTEM message must NOT appear in messages[].
    roles_in_messages = [m["role"] for m in body["messages"]]
    assert "system" not in roles_in_messages
    assert roles_in_messages == ["user"]


def test_mid_conversation_system_message_is_refused() -> None:
    """Codex iter-1 important: hoisting ALL SYSTEM messages
    (regardless of position) would silently reorder the
    conversation. Only **leading** SYSTEM messages are
    hoisted; mid-conversation SYSTEM messages are refused
    with ``ProviderAdapterFailure`` so the provider-blind
    contract stays consistent across providers."""

    bad_request = ProviderRequest(
        id="provider-request:phase-4-3:bad",
        run_ref="run:phase-4-3:bad",
        model_name="claude-sonnet-4-6",
        messages=[
            Message(role=MessageRole.USER, content="Hello"),
            # SYSTEM appearing AFTER user — invalid for Anthropic
            Message(role=MessageRole.SYSTEM, content="Be concise"),
            Message(role=MessageRole.USER, content="Now extract"),
        ],
        response_format=ResponseFormat(kind=ResponseFormatKind.TEXT),
        max_output_tokens=128,
    )
    adapter = _build_adapter(lambda _: httpx.Response(200, json=_ok_response_body()))
    with pytest.raises(ProviderAdapterFailure):
        adapter.complete(bad_request)


def test_malformed_response_does_not_leak_via_pydantic_validator() -> None:
    """Codex iter-1 minor: ``ProviderResponse`` Pydantic
    validation can raise ``ValueError`` whose message echoes
    field values (e.g., ``stop_reason=end_turn`` with empty
    text triggers the STOP-requires-text validator). Adapter
    must convert to ``ProviderAdapterFailure`` so callers
    can dispatch on the typed provider hierarchy and the
    validator's message never surfaces raw."""

    body_canary = "VALIDATOR-LEAK-PROBE-canary-XYZZY"

    def handler(_: httpx.Request) -> httpx.Response:
        body = _ok_response_body(stop_reason="end_turn")
        # Force an empty-text + STOP combo, which fails the
        # ``ProviderResponse.text`` validator. Add a canary
        # so we can assert it doesn't escape.
        body["content"] = []
        body["model"] = body_canary  # arbitrary echoable field
        return httpx.Response(200, json=body)

    adapter = _build_adapter(handler)
    with pytest.raises(ProviderAdapterFailure) as exc_info:
        adapter.complete(_build_request())
    assert body_canary not in str(exc_info.value)
    assert body_canary not in repr(exc_info.value)


def test_json_schema_request_does_not_populate_parsed_output() -> None:
    """Codex iter-2 important: ``JSON_SCHEMA`` callers must
    go through Phase 4 step 4.6 ``schema_runtime`` for full
    validation; the v2 adapter does not perform full JSON
    Schema validation, so populating ``parsed_output`` would
    let invalid extractions flow downstream as successful
    structured data."""

    schema = {
        "type": "object",
        "properties": {"sku": {"type": "string"}},
        "required": ["sku"],
    }
    request = _build_request(
        response_format=ResponseFormat(
            kind=ResponseFormatKind.JSON_SCHEMA,
            schema_name="product",
            json_schema=schema,
            strict=True,
        )
    )

    captured: list[httpx.Request] = []

    def handler(req: httpx.Request) -> httpx.Response:
        captured.append(req)
        return httpx.Response(200, json=_ok_response_body(text='{"sku": "ABC-123"}'))

    adapter = _build_adapter(handler)
    response = adapter.complete(request)

    assert response.parsed_output is None
    assert response.text == '{"sku": "ABC-123"}'
    # Anthropic does not support per-call JSON-schema
    # enforcement, so the wire body must NOT include any
    # response_format / text.format equivalent.
    body = json.loads(captured[0].content)
    assert "response_format" not in body
    assert "text" not in body or "format" not in body.get("text", {})


def test_json_object_request_populates_parsed_output() -> None:
    request = _build_request(
        response_format=ResponseFormat(kind=ResponseFormatKind.JSON_OBJECT)
    )

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json=_ok_response_body(text='{"sku": "ABC-123"}')
        )

    adapter = _build_adapter(handler)
    response = adapter.complete(request)

    assert response.parsed_output == {"sku": "ABC-123"}


def test_json_object_decode_failure_does_not_leak_via_cause() -> None:
    leak_canary = "PROBE-LEAK-VIA-JSON-DOC-CANARY"

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json=_ok_response_body(text=f"narrative: {leak_canary}")
        )

    request = _build_request(
        response_format=ResponseFormat(kind=ResponseFormatKind.JSON_OBJECT)
    )
    adapter = _build_adapter(handler)
    with pytest.raises(StructuredOutputViolation) as exc_info:
        adapter.complete(request)
    assert exc_info.value.__cause__ is None
    assert leak_canary not in str(exc_info.value)
    assert leak_canary not in repr(exc_info.value)


# --- Retry policy -----------------------------------------------------------


def test_429_with_retry_after_triggers_single_retry_then_succeeds() -> None:
    call_count = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(429, headers={"retry-after": "0"}, json={})
        return httpx.Response(200, json=_ok_response_body())

    adapter = _build_adapter(handler)
    response = adapter.complete(_build_request())
    assert call_count == 2
    assert response.finish_reason is ProviderFinishReason.STOP


def test_5xx_exhausts_retries_then_raises_provider_server_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={})

    adapter = _build_adapter(handler, max_attempts=2)
    with pytest.raises(ProviderServerError):
        adapter.complete(_build_request())


def test_overloaded_529_triggers_retry() -> None:
    """Anthropic returns 529 (Overloaded) under heavy load —
    in addition to the standard 429/5xx, this should be
    retryable per the project's retry policy."""

    call_count = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(529, json={})
        return httpx.Response(200, json=_ok_response_body())

    adapter = _build_adapter(handler)
    response = adapter.complete(_build_request())
    assert call_count == 2
    assert response.finish_reason is ProviderFinishReason.STOP


def test_401_raises_provider_auth_failed_without_retry() -> None:
    call_count = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(401, json={})

    adapter = _build_adapter(handler)
    with pytest.raises(ProviderAuthFailed):
        adapter.complete(_build_request())
    assert call_count == 1


# --- Finish-reason mapping --------------------------------------------------


@pytest.mark.parametrize(
    ("stop_reason", "expected"),
    [
        ("end_turn", ProviderFinishReason.STOP),
        ("max_tokens", ProviderFinishReason.LENGTH),
        ("stop_sequence", ProviderFinishReason.STOP),
        ("tool_use", ProviderFinishReason.TOOL_CALL),
        ("unknown_reason", ProviderFinishReason.ERROR),
    ],
)
def test_finish_reason_mapping(
    stop_reason: str, expected: ProviderFinishReason
) -> None:
    body = _ok_response_body(stop_reason=stop_reason)
    if expected is ProviderFinishReason.LENGTH:
        body["content"] = []  # plausible: hit max before any text
    if expected is ProviderFinishReason.ERROR:
        body["content"] = []
    if expected is ProviderFinishReason.TOOL_CALL:
        body["content"] = []  # tool-only response
    adapter = _build_adapter(lambda _: httpx.Response(200, json=body))
    response = adapter.complete(_build_request())
    assert response.finish_reason is expected


# --- RAW_RESPONSE_LEAK boundary --------------------------------------------


def test_api_key_never_leaks_into_exception_messages() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, content=f"echoed: {_API_KEY_CANARY}".encode())

    adapter = _build_adapter(handler)
    with pytest.raises(ProviderAuthFailed) as exc_info:
        adapter.complete(_build_request())
    assert _API_KEY_CANARY not in str(exc_info.value)
    assert _API_KEY_CANARY not in repr(exc_info.value)


def test_invalid_json_body_on_2xx_does_not_leak_into_exception() -> None:
    body_canary = "PROBE-NOT-VALID-JSON-{{garbled-LEAK-PROBE}}"

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body_canary.encode())

    adapter = _build_adapter(handler)
    with pytest.raises(ProviderAdapterFailure) as exc_info:
        adapter.complete(_build_request())
    assert body_canary not in str(exc_info.value)
    assert body_canary not in repr(exc_info.value)


def test_malformed_usage_int_does_not_leak_into_exception() -> None:
    bad_token_value = "EVIL-PROBE-LEAK-12345"

    def handler(_: httpx.Request) -> httpx.Response:
        body = _ok_response_body()
        body["usage"]["input_tokens"] = bad_token_value
        return httpx.Response(200, json=body)

    adapter = _build_adapter(handler)
    with pytest.raises(ProviderAdapterFailure) as exc_info:
        adapter.complete(_build_request())
    assert bad_token_value not in str(exc_info.value)
    assert bad_token_value not in repr(exc_info.value)


def test_boolean_token_value_rejected_not_silently_coerced_to_one() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        body = _ok_response_body()
        body["usage"] = {"input_tokens": True, "output_tokens": 50}
        return httpx.Response(200, json=body)

    adapter = _build_adapter(handler)
    with pytest.raises(ProviderAdapterFailure):
        adapter.complete(_build_request())


def test_negative_token_count_raises_adapter_failure() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        body = _ok_response_body()
        body["usage"] = {"input_tokens": -1, "output_tokens": 50}
        return httpx.Response(200, json=body)

    adapter = _build_adapter(handler)
    with pytest.raises(ProviderAdapterFailure):
        adapter.complete(_build_request())


def test_response_id_must_be_string_not_arbitrary_object() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        body = _ok_response_body()
        body["id"] = {"shape": "wrong"}
        return httpx.Response(200, json=body)

    adapter = _build_adapter(handler)
    response = adapter.complete(_build_request())
    assert response.id.startswith("anthropic-msg:")


# --- Tool refusal -----------------------------------------------------------


def test_complete_refuses_request_with_tools() -> None:
    adapter = _build_adapter(
        lambda _: httpx.Response(200, json=_ok_response_body())
    )
    tool = ToolSpec(
        name="lookup_product",
        description="Lookup a product by SKU",
        parameters_schema={"type": "object"},
        strict=True,
    )
    base = _build_request()
    request_with_tool = ProviderRequest(
        id=base.id,
        run_ref=base.run_ref,
        model_name=base.model_name,
        messages=base.messages,
        tools=[tool],
        response_format=base.response_format,
        max_output_tokens=base.max_output_tokens,
    )
    with pytest.raises(NotImplementedError, match="does not yet support tool calls"):
        adapter.complete(request_with_tool)


def test_complete_refuses_request_with_tool_role_message() -> None:
    adapter = _build_adapter(
        lambda _: httpx.Response(200, json=_ok_response_body())
    )
    tool_msg = Message(
        role=MessageRole.TOOL,
        content='{"result": "ok"}',
        name="lookup_product",
        tool_call_id="call:1",
    )
    base = _build_request()
    request_with_tool_msg = ProviderRequest(
        id=base.id,
        run_ref=base.run_ref,
        model_name=base.model_name,
        messages=[*base.messages, tool_msg],
        response_format=base.response_format,
        max_output_tokens=base.max_output_tokens,
    )
    with pytest.raises(
        NotImplementedError, match="does not yet support tool-result messages"
    ):
        adapter.complete(request_with_tool_msg)


# --- Cached tokens (Anthropic-specific) ------------------------------------


def test_cache_read_input_tokens_populates_cached_input_subtotal() -> None:
    """Anthropic returns ``cache_read_input_tokens`` for prompt-
    cache hits — the v2 ``TokenUsage.cached_input_tokens``
    subtotal must reflect it."""

    body = _ok_response_body(input_tokens=200, output_tokens=50)
    body["usage"]["cache_read_input_tokens"] = 150
    adapter = _build_adapter(lambda _: httpx.Response(200, json=body))
    response = adapter.complete(_build_request())
    assert response.usage.prompt_tokens == 200
    assert response.usage.cached_input_tokens == 150


def test_cache_read_input_tokens_exceeding_input_tokens_rejected() -> None:
    """The Phase 0 ``TokenUsage`` validator enforces
    ``cached_input_tokens <= prompt_tokens``. Catch upstream
    so the validator's error message never leaks the values."""

    body = _ok_response_body(input_tokens=100, output_tokens=50)
    body["usage"]["cache_read_input_tokens"] = 999
    adapter = _build_adapter(lambda _: httpx.Response(200, json=body))
    with pytest.raises(ProviderAdapterFailure):
        adapter.complete(_build_request())
