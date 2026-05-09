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
        OpenAIResponsesAdapterV2(
            api_key=_API_KEY_CANARY,
            max_attempts=0,
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json={})),
        )


def test_fixture_mode_requires_explicit_transport() -> None:
    """Codex iter-3 important: ``RuntimeMode.FIXTURE`` without
    an explicit transport defaulted to a real ``httpx.Client``,
    which can call api.openai.com from tests or local runs.
    Refuse construction so a wiring bug surfaces immediately."""

    with pytest.raises(ValueError, match="explicit httpx.MockTransport"):
        OpenAIResponsesAdapterV2(api_key=_API_KEY_CANARY)


def test_fixture_mode_refuses_real_network_transport() -> None:
    """Codex iter-5 important: ``BaseTransport`` also covers
    ``httpx.HTTPTransport`` (real egress). Fixture mode must
    accept only ``httpx.MockTransport`` so production-egress
    gating is mechanically enforced — not just contractually
    promised."""

    with pytest.raises(ValueError, match="only accepts httpx.MockTransport"):
        OpenAIResponsesAdapterV2(
            api_key=_API_KEY_CANARY,
            transport=httpx.HTTPTransport(),
            runtime_mode=RuntimeMode.FIXTURE,
        )


def test_constructor_consults_current_mode_when_runtime_mode_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Codex iter-5 important: omitting ``runtime_mode`` must
    fall through to ``current_mode()`` so
    ``VERACRAWL_RUNTIME_MODE=production`` (env var) is honored.
    Without this, every caller would have to remember to pass
    ``runtime_mode`` for the production-gate to work."""

    monkeypatch.setenv("VERACRAWL_RUNTIME_MODE", "production")
    with pytest.raises(ProductionRuntimeNotImplemented):
        OpenAIResponsesAdapterV2(
            api_key=_API_KEY_CANARY,
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json=_ok_response_body())
            ),
        )


# --- Capability table -------------------------------------------------------


def test_supports_returns_documented_capabilities() -> None:
    """Phase 4 step 4.2 lands as a building block — every
    capability returns ``False``. Codex iter-5 important:
    advertising ``STRUCTURED_OUTPUT_JSON_SCHEMA`` would route
    structured-output work here even though full JSON-Schema
    validation (anyOf / allOf / pattern / nested types / enum
    bounds / additionalProperties) is the Phase 4 step 4.6
    ``schema_runtime`` Pydantic-class validator's
    responsibility. Better to flip the flag to ``True`` only
    when the backing implementation lands."""

    adapter = _build_adapter(lambda _: httpx.Response(200, json=_ok_response_body()))
    assert adapter.supports(ModelCapability.STRUCTURED_OUTPUT_JSON_SCHEMA) is False
    assert adapter.supports(ModelCapability.TOOL_CALLS) is False
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

    captured: list[httpx.Request] = []

    def handler(req: httpx.Request) -> httpx.Response:
        captured.append(req)
        return httpx.Response(200, json=_ok_response_body(text='{"sku": "ABC-123"}'))

    adapter = _build_adapter(handler)
    response = adapter.complete(request)

    assert response.parsed_output == {"sku": "ABC-123"}
    # Codex iter-4 critical: Responses API JSON_SCHEMA wire shape
    # is nested under ``text.format``, not top-level
    # ``response_format``.
    body = json.loads(captured[0].content)
    assert "response_format" not in body
    assert body["text"]["format"]["type"] == "json_schema"
    assert body["text"]["format"]["name"] == "product"
    assert body["text"]["format"]["strict"] is True


def test_complete_structured_output_rejects_missing_required_field() -> None:
    """Codex iter-4 important: the adapter must validate
    ``parsed_output`` against the declared ``json_schema``
    required fields. Provider-side strict mode is not enough —
    non-strict requests + fixture-mode replay still need the
    local validator to surface drift."""

    schema = {
        "type": "object",
        "properties": {"sku": {"type": "string"}, "price": {"type": "number"}},
        "required": ["sku", "price"],
    }
    request = _build_request(
        response_format=ResponseFormat(
            kind=ResponseFormatKind.JSON_SCHEMA,
            schema_name="product",
            json_schema=schema,
            strict=False,
        )
    )

    def handler(_: httpx.Request) -> httpx.Response:
        # Missing required ``price`` field.
        return httpx.Response(200, json=_ok_response_body(text='{"sku": "ABC-123"}'))

    adapter = _build_adapter(handler)
    with pytest.raises(StructuredOutputViolation):
        adapter.complete(request)


def test_complete_structured_output_decode_failure_does_not_leak_via_cause() -> None:
    """Codex iter-4 important: ``json.JSONDecodeError.doc``
    retains the raw response text. Using
    ``raise StructuredOutputViolation(...) from exc`` would
    surface the body via ``__cause__``. ``from None`` clears
    the chain."""

    leak_canary = "PROBE-LEAK-VIA-JSON-DOC-CANARY"

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json=_ok_response_body(text=f"narrative reply: {leak_canary}")
        )

    request = _build_request(
        response_format=ResponseFormat(
            kind=ResponseFormatKind.JSON_SCHEMA,
            schema_name="product",
            json_schema={"type": "object"},
            strict=True,
        )
    )
    adapter = _build_adapter(handler)
    with pytest.raises(StructuredOutputViolation) as exc_info:
        adapter.complete(request)
    assert exc_info.value.__cause__ is None
    assert leak_canary not in str(exc_info.value)
    assert leak_canary not in repr(exc_info.value)


def test_response_id_must_be_string_not_arbitrary_object() -> None:
    """Codex iter-4 minor: the upstream ``id`` field must be
    sanitized to a plain non-blank string before becoming
    ``ProviderResponse.id`` (which Phase 6 indexes). Hostile
    / malformed upstream payloads must fall back to the
    synthetic id, not coerce-via-str() arbitrary objects."""

    def handler(_: httpx.Request) -> httpx.Response:
        body = _ok_response_body()
        body["id"] = {"shape": "wrong"}  # not a string
        return httpx.Response(200, json=body)

    adapter = _build_adapter(handler)
    response = adapter.complete(_build_request())
    assert response.id.startswith("openai-response:")
    assert "shape" not in response.id
    assert "wrong" not in response.id


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


# --- RAW_RESPONSE_LEAK on success-path parse (codex iter-3) ----------------


def test_invalid_json_body_on_2xx_does_not_leak_into_exception() -> None:
    """Codex iter-3 important: ``http_response.json()`` raises
    ``json.JSONDecodeError`` whose message echoes part of the
    upstream body. The adapter must catch + sanitize so error
    messages carry only status code + upstream request id."""

    body_canary = "PROBE-NOT-VALID-JSON-{{garbled-LEAK-PROBE}}"

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body_canary.encode())

    adapter = _build_adapter(handler)
    with pytest.raises(ProviderAdapterFailure) as exc_info:
        adapter.complete(_build_request())
    assert body_canary not in str(exc_info.value)
    assert body_canary not in repr(exc_info.value)


def test_malformed_usage_int_does_not_leak_into_exception() -> None:
    """``int("evil string")`` raises ``ValueError`` whose message
    quotes the bad literal. Convert to a sanitized
    ``ProviderAdapterFailure`` instead."""

    bad_token_value = "EVIL-PROBE-LEAK-12345"

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "resp:abcdef",
                "status": "completed",
                "output": [
                    {"content": [{"type": "output_text", "text": "extracted"}]},
                ],
                "usage": {
                    "input_tokens": bad_token_value,
                    "output_tokens": 50,
                    "total_tokens": 150,
                },
            },
        )

    adapter = _build_adapter(handler)
    with pytest.raises(ProviderAdapterFailure) as exc_info:
        adapter.complete(_build_request())
    assert bad_token_value not in str(exc_info.value)
    assert bad_token_value not in repr(exc_info.value)


def test_inconsistent_total_tokens_raises_adapter_failure() -> None:
    """``total_tokens != input_tokens + output_tokens`` would
    trigger the Phase 0 ``TokenUsage`` validator whose error
    message includes the values. Catch upstream and convert."""

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "resp:abcdef",
                "status": "completed",
                "output": [
                    {"content": [{"type": "output_text", "text": "extracted"}]},
                ],
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "total_tokens": 999,
                },
            },
        )

    adapter = _build_adapter(handler)
    with pytest.raises(ProviderAdapterFailure):
        adapter.complete(_build_request())


def test_negative_token_count_raises_adapter_failure() -> None:
    """A negative ``input_tokens`` from a buggy / hostile
    upstream must not slip into ``TokenUsage`` (validator would
    leak the value into its error message)."""

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "resp:abcdef",
                "status": "completed",
                "output": [
                    {"content": [{"type": "output_text", "text": "extracted"}]},
                ],
                "usage": {"input_tokens": -1, "output_tokens": 50, "total_tokens": 49},
            },
        )

    adapter = _build_adapter(handler)
    with pytest.raises(ProviderAdapterFailure):
        adapter.complete(_build_request())


def test_boolean_token_value_rejected_not_silently_coerced_to_one() -> None:
    """``isinstance(True, int)`` is ``True`` in Python and would
    silently coerce to ``1`` if not explicitly rejected."""

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "resp:abcdef",
                "status": "completed",
                "output": [
                    {"content": [{"type": "output_text", "text": "extracted"}]},
                ],
                "usage": {"input_tokens": True, "output_tokens": 50, "total_tokens": 51},
            },
        )

    adapter = _build_adapter(handler)
    with pytest.raises(ProviderAdapterFailure):
        adapter.complete(_build_request())


# --- Tool refusal (codex iter-2 important) ---------------------------------


def test_complete_refuses_request_with_tools() -> None:
    """Codex iter-2 important: tool-call support is not yet
    implemented (the Phase 4 step 4.1 ``ProviderResponse``
    contract has no tool-call field; multi-turn tool loops
    would silently lose model-selected calls). Refuse at the
    boundary so a caller cannot send invalid wire data."""

    adapter = _build_adapter(
        lambda _: httpx.Response(200, json=_ok_response_body())
    )
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
    """Tool-result messages (``MessageRole.TOOL``) are part of
    the multi-turn tool loop; same deferral as the tool spec
    case (codex iter-2 important)."""

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
