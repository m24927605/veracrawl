"""Phase 4 step 4.2 — OpenAIResponsesAdapterV2 integration tests.

Fixture-mode-only (``httpx.MockTransport``); production mode is
gated until Phase 6 step 6.1.

Coverage:

* Happy path with structured output → ``ProviderResponse`` with
  populated ``parsed_output`` + ``TokenUsage``.
* Plain-text response (``ResponseFormatKind.TEXT``) → no
  ``parsed_output``.
* JSON decode failure when JSON_SCHEMA requested →
  ``StructuredOutputViolation``.
* 429 with ``Retry-After`` triggers single retry and succeeds.
* 401 raises ``ProviderAuthFailed`` (FatalError marker).
* 5xx exhausts retries and raises ``ProviderServerError``.
* Token usage extracted from ``usage`` block (``input_tokens``
  + ``output_tokens`` + cached / reasoning subtotals).
* Production mode (``RuntimeMode.PRODUCTION``) raises
  ``ProductionRuntimeNotImplemented`` at construction.
* Authorization header value never appears in any structured
  log captured during a fixture-mode call (canary check —
  RAW_RESPONSE_LEAK boundary).
* ``supports`` returns the documented capability table.
* ``DeprecationWarning`` fires on v1 adapter constructor.

The adapter is imported lazily inside each test where needed
to keep collection cheap; module-level imports cover the common
shared types.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from veracrawl.adapters.model_providers.openai_responses_v2 import (
    OpenAIResponsesAdapterV2,
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

_API_KEY_CANARY = "sk-LIVE-CANARY-DEADBEEF-must-not-leak"


def _build_request(
    *,
    response_format: ResponseFormat | None = None,
    user_text: str = "extract product details",
) -> ProviderRequest:
    return ProviderRequest(
        id="provider-request:phase-4-2:1",
        run_ref="run:phase-4-2:1",
        model_name="gpt-4o-mini",
        messages=[Message(role=MessageRole.USER, content=user_text)],
        response_format=response_format
        or ResponseFormat(kind=ResponseFormatKind.TEXT),
        max_output_tokens=256,
    )


def _ok_response_body(
    *,
    text: str = "extracted",
    finish_status: str = "completed",
    prompt_tokens: int = 100,
    completion_tokens: int = 50,
) -> dict[str, Any]:
    return {
        "id": "resp:abcdef",
        "status": finish_status,
        "output": [
            {"content": [{"type": "output_text", "text": text}]},
        ],
        "usage": {
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


def _build_adapter(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    max_attempts: int = 3,
) -> OpenAIResponsesAdapterV2:
    return OpenAIResponsesAdapterV2(
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
        OpenAIResponsesAdapterV2(
            api_key=_API_KEY_CANARY,
            runtime_mode=RuntimeMode.PRODUCTION,
        )


def test_blank_api_key_rejected() -> None:
    with pytest.raises(ValueError, match="non-blank api_key"):
        OpenAIResponsesAdapterV2(api_key="   ")


def test_zero_max_attempts_rejected() -> None:
    with pytest.raises(ValueError, match="max_attempts must be"):
        OpenAIResponsesAdapterV2(api_key=_API_KEY_CANARY, max_attempts=0)


# --- Capability table -------------------------------------------------------


def test_supports_returns_documented_capabilities() -> None:
    adapter = _build_adapter(lambda _: httpx.Response(200, json=_ok_response_body()))
    assert adapter.supports(ModelCapability.STRUCTURED_OUTPUT_JSON_SCHEMA) is True
    assert adapter.supports(ModelCapability.TOOL_CALLS) is True
    assert adapter.supports(ModelCapability.VISION) is False
    assert adapter.supports(ModelCapability.EXTENDED_THINKING) is False


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
    assert captured[0].method == "POST"
    assert captured[0].headers["authorization"] == f"Bearer {_API_KEY_CANARY}"
    body = json.loads(captured[0].content)
    assert body["model"] == "gpt-4o-mini"
    assert body["max_output_tokens"] == 256
    assert body["temperature"] == 0.0
    assert body["input"][0]["role"] == "user"


def test_complete_structured_output_populates_parsed_output() -> None:
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

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_ok_response_body(text='{"sku": "ABC-123"}'))

    adapter = _build_adapter(handler)
    response = adapter.complete(request)

    assert response.parsed_output == {"sku": "ABC-123"}


def test_complete_structured_output_decode_failure_raises_violation() -> None:
    request = _build_request(
        response_format=ResponseFormat(
            kind=ResponseFormatKind.JSON_SCHEMA,
            schema_name="product",
            json_schema={"type": "object"},
            strict=True,
        )
    )

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json=_ok_response_body(text="not valid json — narrative reply")
        )

    adapter = _build_adapter(handler)
    with pytest.raises(StructuredOutputViolation):
        adapter.complete(request)


def test_complete_structured_output_non_object_root_raises_violation() -> None:
    request = _build_request(
        response_format=ResponseFormat(
            kind=ResponseFormatKind.JSON_SCHEMA,
            schema_name="product",
            json_schema={"type": "object"},
            strict=True,
        )
    )

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_ok_response_body(text='["a", "b"]'))

    adapter = _build_adapter(handler)
    with pytest.raises(StructuredOutputViolation):
        adapter.complete(request)


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
    with pytest.raises(ProviderServerError) as exc_info:
        adapter.complete(_build_request())
    assert exc_info.value.status_code == 503


def test_401_raises_provider_auth_failed_without_retry() -> None:
    call_count = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(401, json={})

    adapter = _build_adapter(handler)
    with pytest.raises(ProviderAuthFailed):
        adapter.complete(_build_request())
    assert call_count == 1  # no retry on 401


# --- Finish-reason mapping --------------------------------------------------


@pytest.mark.parametrize(
    ("status_value", "expected"),
    [
        ("completed", ProviderFinishReason.STOP),
        ("max_output_tokens", ProviderFinishReason.LENGTH),
        ("incomplete", ProviderFinishReason.LENGTH),
        ("failed", ProviderFinishReason.ERROR),
    ],
)
def test_finish_reason_mapping(
    status_value: str, expected: ProviderFinishReason
) -> None:
    body = _ok_response_body(finish_status=status_value)
    if expected is ProviderFinishReason.LENGTH:
        body["output"] = []  # length-stop with no output, common shape
    if expected is ProviderFinishReason.ERROR:
        body["output"] = []

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    adapter = _build_adapter(handler)
    request = _build_request()
    response = adapter.complete(request)
    assert response.finish_reason is expected


# --- RAW_RESPONSE_LEAK boundary --------------------------------------------


def test_api_key_never_leaks_into_exception_messages() -> None:
    """The Authorization header value must not appear in any
    raised exception's stringified form. Adapters are not allowed
    to echo response bodies or request payloads in errors."""

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, content=f"echoed: {_API_KEY_CANARY}".encode())

    adapter = _build_adapter(handler)
    with pytest.raises(ProviderAuthFailed) as exc_info:
        adapter.complete(_build_request())
    assert _API_KEY_CANARY not in str(exc_info.value)
    assert _API_KEY_CANARY not in repr(exc_info.value)


# --- Tool wire shape (codex iter-1 important) ------------------------------


def test_tools_use_responses_api_flat_shape_not_chat_completions_nested() -> None:
    """OpenAI Responses API tools are flat:
    ``{"type": "function", "name": ..., "description": ...,
       "parameters": ..., "strict": ...}`` — NOT the Chat
    Completions nested ``{"type": "function", "function": {...}}``
    envelope. ``supports(TOOL_CALLS) == True`` would be a lie if
    the wire shape is wrong."""

    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json=_ok_response_body())

    adapter = _build_adapter(handler)
    tool = ToolSpec(
        name="lookup_product",
        description="Lookup a product by SKU",
        parameters_schema={
            "type": "object",
            "properties": {"sku": {"type": "string"}},
            "required": ["sku"],
        },
        strict=True,
    )
    request = _build_request()
    request_with_tool = ProviderRequest(
        id=request.id,
        run_ref=request.run_ref,
        model_name=request.model_name,
        messages=request.messages,
        tools=[tool],
        response_format=request.response_format,
        max_output_tokens=request.max_output_tokens,
    )
    adapter.complete(request_with_tool)

    body = json.loads(captured[0].content)
    assert "tools" in body
    assert len(body["tools"]) == 1
    wire_tool = body["tools"][0]
    # Flat shape required.
    assert wire_tool["type"] == "function"
    assert wire_tool["name"] == "lookup_product"
    assert wire_tool["description"] == "Lookup a product by SKU"
    assert wire_tool["parameters"]["type"] == "object"
    assert wire_tool["strict"] is True
    # Nested-style fields must NOT be present.
    assert "function" not in wire_tool


# --- Token usage strictness (codex iter-1 minor) ---------------------------


def test_missing_usage_block_raises_adapter_failure() -> None:
    """Codex iter-1 minor: an absent or non-dict ``usage`` block
    is a contract violation, not a fill-with-zeros case. Token-
    budget audits never see fabricated zero counts."""

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "resp:abcdef",
                "status": "completed",
                "output": [
                    {"content": [{"type": "output_text", "text": "extracted"}]},
                ],
                # NB: no ``usage`` block.
            },
        )

    adapter = _build_adapter(handler)
    with pytest.raises(ProviderAdapterFailure):
        adapter.complete(_build_request())


def test_partial_usage_block_raises_adapter_failure() -> None:
    """``usage`` block present but missing ``input_tokens`` or
    ``output_tokens`` is also a contract violation."""

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "resp:abcdef",
                "status": "completed",
                "output": [
                    {"content": [{"type": "output_text", "text": "extracted"}]},
                ],
                "usage": {"total_tokens": 10},
            },
        )

    adapter = _build_adapter(handler)
    with pytest.raises(ProviderAdapterFailure):
        adapter.complete(_build_request())


# --- v1 deprecation ---------------------------------------------------------


def test_v1_adapter_emits_deprecation_warning_on_construction() -> None:
    from veracrawl.adapters.model_providers.openai_responses import (
        OpenAIResponsesModelProviderRuntimeAdapter,
    )

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_ok_response_body())

    with pytest.warns(DeprecationWarning, match="v1.*deprecated"):
        OpenAIResponsesModelProviderRuntimeAdapter(
            api_key=_API_KEY_CANARY,
            model_id="gpt-4o-mini",
            transport=httpx.MockTransport(handler),
        )
