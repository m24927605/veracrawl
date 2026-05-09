"""Phase 4 step 4.2 — OpenAIResponsesAdapter v2.

Implements ``ModelProviderPortV2`` against the OpenAI Responses
API wire shape (``POST /v1/responses``). v2 supersedes the v1
``OpenAIResponsesModelProviderRuntimeAdapter``: v1 stays operational
during the deprecation window (its constructor emits
``DeprecationWarning``) so existing callers can migrate without
flag-day breakage.

Design boundaries (per Phase 4 design supplement step 4.2):

* **Provider-blind shape**: the adapter consumes
  :class:`ProviderRequest` / produces :class:`ProviderResponse`.
  Provider HTTP shape is contained inside this module.
* **Fixture mode default** (``RuntimeMode.FIXTURE``): callers
  pass an ``httpx.BaseTransport`` (typically
  ``httpx.MockTransport``); production mode raises
  :class:`ProductionRuntimeNotImplemented` until Phase 6 step
  6.1 wires the production deployment.
* **Retry policy**: 429 / 5xx retried up to ``max_attempts``
  with exponential backoff + jitter; ``Retry-After`` honored
  (delta-seconds + HTTP-date), capped at 60s so a hostile
  upstream cannot stall the caller.
* **RAW_RESPONSE_LEAK boundary**: error paths NEVER include
  response bodies, prompt content, or request payloads in
  raised exceptions or structured logs. Sanitized identifiers
  only (``request.id``, ``model_name``, ``request_id`` from
  the upstream ``x-request-id`` header).
* **Structured output**: when
  ``request.response_format.kind == JSON_SCHEMA``, the adapter
  parses the response text as JSON and surfaces a
  :class:`StructuredOutputViolation` for non-decodable JSON or
  non-object roots. **Schema validation is the OpenAI Responses
  API's responsibility** (``response_format.strict=True``);
  the v2 adapter does NOT re-validate against the schema in
  Phase 4 (a Pydantic-class-based round-trip validator is
  scoped to Phase 4 step 4.6 ``schema_runtime`` where the
  caller provides the Pydantic class to validate against).
  Callers that opt out of provider-side strict mode
  (``response_format.strict=False``) accept that the adapter
  will not detect schema violations beyond JSON-decodability.
* **Capability table**: ``supports`` returns ``True`` only for
  capabilities the adapter has implemented and validated.
  Phase 4 step 4.2 ships ``STRUCTURED_OUTPUT_JSON_SCHEMA``;
  tool-call support is **deferred** because the Phase 4 step
  4.1 ``ProviderResponse`` does not yet carry a tool-call
  field (multi-turn tool loops need a provider-blind
  ``ToolCall`` representation). Until that contract surface
  lands (deferred Phase 4 follow-up — sequence TBD), the
  adapter:
  - returns ``False`` from ``supports(TOOL_CALLS)``;
  - refuses ``ProviderRequest`` instances carrying
    ``tools`` or ``MessageRole.TOOL`` messages by raising
    ``NotImplementedError`` at ``complete()``.
  Vision and extended thinking are similarly deferred.
"""

from __future__ import annotations

import json
import random
import time
from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any, Final

import httpx

from veracrawl.contracts.agent import Message, TokenUsage
from veracrawl.contracts.enums import (
    MessageRole,
    ModelCapability,
    ProviderFinishReason,
    ResponseFormatKind,
)
from veracrawl.contracts.errors import (
    ProviderAdapterFailure,
    StructuredOutputViolation,
    classify_provider_error,
    classify_provider_status,
)
from veracrawl.contracts.llm_input import ProviderRequest, ProviderResponse
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
)

_RESPONSES_ENDPOINT: Final[str] = "https://api.openai.com/v1/responses"
_REQUEST_ID_HEADER: Final[str] = "x-request-id"
_RETRY_AFTER_HEADER: Final[str] = "retry-after"
_DEFAULT_MAX_ATTEMPTS: Final[int] = 3
_RETRY_AFTER_CAP_S: Final[float] = 60.0
_RETRYABLE_STATUSES: Final[frozenset[int]] = frozenset({429, 500, 502, 503, 504})
_DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=60.0, pool=10.0)

_FINISH_REASON_MAP: Final[dict[str, ProviderFinishReason]] = {
    # OpenAI Responses ``status``-like values; the ``incomplete_details.reason``
    # field is the more detailed signal but is not always populated.
    "completed": ProviderFinishReason.STOP,
    "stop": ProviderFinishReason.STOP,
    "max_output_tokens": ProviderFinishReason.LENGTH,
    "length": ProviderFinishReason.LENGTH,
    "tool_calls": ProviderFinishReason.TOOL_CALL,
    "tool_use": ProviderFinishReason.TOOL_CALL,
    "content_filter": ProviderFinishReason.CONTENT_FILTER,
    "incomplete": ProviderFinishReason.LENGTH,
    "failed": ProviderFinishReason.ERROR,
}

_SUPPORTED_CAPABILITIES: Final[frozenset[ModelCapability]] = frozenset(
    {
        ModelCapability.STRUCTURED_OUTPUT_JSON_SCHEMA,
    }
)


def _request_id_from(headers: Any) -> str | None:
    if headers is None:
        return None
    getter = getattr(headers, "get", None)
    if callable(getter):
        value = getter(_REQUEST_ID_HEADER)
        if isinstance(value, str) and value:
            return value
    return None


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    raw = value.strip()
    if raw.isdigit():
        return float(raw)
    try:
        when = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    delta = (when - datetime.now(UTC)).total_seconds()
    return max(delta, 0.0)


def _backoff_seconds(attempt: int, *, jitter: Callable[[], float]) -> float:
    base: float = min(2 ** (attempt - 1), 30.0)
    return base + float(jitter())


def _is_retryable_transport(exc: httpx.HTTPError) -> bool:
    return isinstance(
        exc,
        httpx.ConnectError | httpx.ConnectTimeout | httpx.ReadTimeout | httpx.PoolTimeout,
    )


def _message_to_input(message: Message) -> dict[str, Any]:
    """Translate a ``Message`` to the OpenAI Responses input shape."""

    role_map: dict[MessageRole, str] = {
        MessageRole.SYSTEM: "developer",  # OpenAI Responses uses developer role
        MessageRole.USER: "user",
        MessageRole.ASSISTANT: "assistant",
        MessageRole.TOOL: "tool",
    }
    body: dict[str, Any] = {
        "role": role_map[message.role],
        "content": message.content,
    }
    if message.tool_call_id is not None:
        body["tool_call_id"] = message.tool_call_id
    return body


def _extract_output_text(response: dict[str, Any]) -> str:
    texts: list[str] = []
    for item in response.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") == "output_text":
                text = content.get("text")
                if isinstance(text, str):
                    texts.append(text)
    return "\n".join(texts)


def _coerce_non_negative_int(value: Any) -> int | None:
    """Codex iter-3 important: ``int(...)`` on attacker-controlled
    upstream payload can raise ``TypeError`` / ``ValueError``
    whose message echoes the value (RAW_RESPONSE_LEAK
    boundary). Return ``None`` for any value that is not a
    plain non-negative integer; callers convert ``None`` into
    a sanitized ``ProviderAdapterFailure``. ``bool`` is
    explicitly rejected because ``isinstance(True, int)`` is
    ``True`` in Python and would silently coerce to ``1``."""

    if isinstance(value, bool):
        return None
    if not isinstance(value, int):
        return None
    if value < 0:
        return None
    return value


def _coerce_optional_subtotal(value: Any) -> int:
    """Optional subtotals (``cached_tokens``, ``reasoning_tokens``)
    that may be absent. Absent → 0; malformed → 0 (silently treat
    as no info rather than failing the whole call)."""

    coerced = _coerce_non_negative_int(value) if value is not None else 0
    return coerced if coerced is not None else 0


def _extract_usage(response: dict[str, Any]) -> TokenUsage:
    """Build ``TokenUsage`` from the Responses API ``usage`` block.

    Boundary invariant (Phase 4 step 4.1): ``ProviderResponse``
    requires non-``None`` ``usage``. If the API omits ``usage``
    OR returns malformed integer fields, raise a sanitized
    ``ProviderAdapterFailure`` — silently filling with zeros
    or coercing arbitrary upstream text via ``int(...)`` would
    leak response content into the exception message
    (RAW_RESPONSE_LEAK boundary, codex iter-3 important).
    """

    usage_raw = response.get("usage")
    if not isinstance(usage_raw, dict):
        raise ProviderAdapterFailure(
            status_code=200,
            error_code="ADAPTER_FAILURE",
            request_id=None,
        )
    prompt = _coerce_non_negative_int(usage_raw.get("input_tokens"))
    completion = _coerce_non_negative_int(usage_raw.get("output_tokens"))
    if prompt is None or completion is None:
        raise ProviderAdapterFailure(
            status_code=200,
            error_code="ADAPTER_FAILURE",
            request_id=None,
        )
    total_raw = usage_raw.get("total_tokens", prompt + completion)
    total = _coerce_non_negative_int(total_raw)
    if total is None:
        raise ProviderAdapterFailure(
            status_code=200,
            error_code="ADAPTER_FAILURE",
            request_id=None,
        )
    input_details = usage_raw.get("input_tokens_details")
    cached_input = (
        _coerce_optional_subtotal(input_details.get("cached_tokens"))
        if isinstance(input_details, dict)
        else 0
    )
    output_details = usage_raw.get("output_tokens_details")
    reasoning = (
        _coerce_optional_subtotal(output_details.get("reasoning_tokens"))
        if isinstance(output_details, dict)
        else 0
    )
    # The Phase 0 ``TokenUsage`` validator enforces
    # ``total_tokens == prompt + completion`` — if the upstream
    # ``total_tokens`` disagrees, surface as a sanitized
    # adapter failure rather than letting the validator's
    # error message leak the upstream values.
    if total != prompt + completion:
        raise ProviderAdapterFailure(
            status_code=200,
            error_code="ADAPTER_FAILURE",
            request_id=None,
        )
    if cached_input > prompt or reasoning > completion:
        raise ProviderAdapterFailure(
            status_code=200,
            error_code="ADAPTER_FAILURE",
            request_id=None,
        )
    return TokenUsage(
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=total,
        cached_input_tokens=cached_input,
        reasoning_tokens=reasoning,
    )


def _map_finish_reason(response: dict[str, Any]) -> ProviderFinishReason:
    raw = str(response.get("status", "completed")).lower()
    incomplete_details = response.get("incomplete_details")
    if isinstance(incomplete_details, dict):
        detail_reason = incomplete_details.get("reason")
        if isinstance(detail_reason, str):
            mapped = _FINISH_REASON_MAP.get(detail_reason.lower())
            if mapped is not None:
                return mapped
    return _FINISH_REASON_MAP.get(raw, ProviderFinishReason.STOP)


class OpenAIResponsesAdapterV2:
    """Provider-blind v2 OpenAI Responses adapter.

    Construct with ``runtime_mode=RuntimeMode.FIXTURE`` and an
    ``httpx.MockTransport`` for deterministic tests. Production
    construction (``RuntimeMode.PRODUCTION``) is gated until
    Phase 6 step 6.1.
    """

    provider_name = "OpenAI Responses API (v2)"

    def __init__(
        self,
        *,
        api_key: str,
        endpoint: str = _RESPONSES_ENDPOINT,
        max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
        runtime_mode: RuntimeMode = RuntimeMode.FIXTURE,
        transport: httpx.BaseTransport | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        jitter_fn: Callable[[], float] | None = None,
    ) -> None:
        if runtime_mode is RuntimeMode.PRODUCTION:
            raise ProductionRuntimeNotImplemented(
                backend="openai_responses_v2",
                gate="phase_4_step_4_2_production_call",
            )
        if not api_key or not api_key.strip():
            raise ValueError("OpenAIResponsesAdapterV2 requires a non-blank api_key")
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        # Codex iter-3 important: FIXTURE mode without an
        # explicit transport defaults to a real httpx.Client,
        # which can reach api.openai.com from tests or local
        # runs. Refuse construction so a wiring bug surfaces
        # immediately instead of as an accidental live call
        # (which would also burn API credits).
        if transport is None:
            raise ValueError(
                "OpenAIResponsesAdapterV2 in FIXTURE mode requires an explicit "
                "httpx.BaseTransport (e.g. httpx.MockTransport). The PRODUCTION "
                "wiring (real network egress) is gated until Phase 6 step 6.1."
            )
        self._api_key = api_key
        self._endpoint = endpoint
        self._max_attempts = max_attempts
        self._runtime_mode = runtime_mode
        self._sleep = sleep_fn
        self._jitter: Callable[[], float] = (
            jitter_fn if jitter_fn is not None else lambda: random.uniform(0, 1)
        )
        client_kwargs: dict[str, Any] = {"timeout": _DEFAULT_TIMEOUT}
        if transport is not None:
            client_kwargs["transport"] = transport
        self._client = httpx.Client(**client_kwargs)

    def supports(self, capability: ModelCapability) -> bool:
        return capability in _SUPPORTED_CAPABILITIES

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        # Codex iter-2 important: tool-call support is not yet
        # implemented in v2 (the ``ProviderResponse`` contract does
        # not yet carry a tool-call field, and the Responses API
        # tool-result wire shape differs from the chat-completions
        # ``role:"tool"`` envelope). Refuse at the boundary so a
        # caller cannot silently lose a model-selected tool call
        # OR send invalid wire data on multi-turn tool loops.
        if request.tools:
            raise NotImplementedError(
                "OpenAIResponsesAdapterV2 does not yet support tool calls; "
                "the ProviderResponse contract surface for tool calls is a "
                "deferred Phase 4 follow-up. Build a ProviderRequest with "
                "no tools, or wait for tool-call support to land."
            )
        if any(message.role is MessageRole.TOOL for message in request.messages):
            raise NotImplementedError(
                "OpenAIResponsesAdapterV2 does not yet support tool-result "
                "messages (MessageRole.TOOL); see ``complete`` docstring."
            )
        body = self._build_request_body(request)
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        response_data = self._post_with_retry(body=body, headers=headers)
        text = _extract_output_text(response_data)
        usage = _extract_usage(response_data)
        finish_reason = _map_finish_reason(response_data)
        parsed_output = self._maybe_parse_structured_output(
            request=request, text=text, finish_reason=finish_reason
        )
        response_id = str(response_data.get("id") or f"openai-response:{request.id}")
        return ProviderResponse(
            id=response_id,
            request_ref=request.id,
            text=text,
            usage=usage,
            finish_reason=finish_reason,
            parsed_output=parsed_output,
        )

    def _build_request_body(self, request: ProviderRequest) -> dict[str, Any]:
        # Tool-call paths are refused at ``complete()`` (codex
        # iter-2 important — tool-call support deferred until
        # the ``ProviderResponse`` contract carries a tool-call
        # field). This function therefore never sees
        # ``request.tools`` populated.
        body: dict[str, Any] = {
            "model": request.model_name,
            "input": [_message_to_input(m) for m in request.messages],
            "max_output_tokens": request.max_output_tokens,
            "temperature": request.temperature,
        }
        if request.response_format.kind is ResponseFormatKind.JSON_SCHEMA:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": request.response_format.schema_name,
                    "schema": request.response_format.json_schema,
                    "strict": request.response_format.strict,
                },
            }
        elif request.response_format.kind is ResponseFormatKind.JSON_OBJECT:
            body["response_format"] = {"type": "json_object"}
        return body

    def _post_with_retry(
        self,
        *,
        body: dict[str, Any],
        headers: dict[str, str],
    ) -> dict[str, Any]:
        last_response: httpx.Response | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                http_response = self._client.post(
                    self._endpoint, json=body, headers=headers
                )
            except httpx.HTTPError as exc:
                if attempt >= self._max_attempts or not _is_retryable_transport(exc):
                    raise classify_provider_error(
                        status_code=0,
                        error_code="ADAPTER_FAILURE",
                        request_id=None,
                    ) from None
                self._sleep(_backoff_seconds(attempt, jitter=self._jitter))
                continue

            if http_response.status_code in _RETRYABLE_STATUSES:
                last_response = http_response
                if attempt >= self._max_attempts:
                    break
                wait = _parse_retry_after(
                    http_response.headers.get(_RETRY_AFTER_HEADER)
                )
                if wait is None:
                    wait = _backoff_seconds(attempt, jitter=self._jitter)
                wait = min(wait, _RETRY_AFTER_CAP_S)
                # Drain the body so the connection can be reused; the
                # body is never inspected (RAW_RESPONSE_LEAK boundary).
                http_response.read()
                self._sleep(wait)
                continue

            if http_response.is_success:
                # Codex iter-3 important: ``http_response.json()``
                # raises ``json.JSONDecodeError`` whose message
                # echoes part of the upstream body
                # (RAW_RESPONSE_LEAK boundary). Catch and convert
                # to a sanitized ``ProviderAdapterFailure``
                # carrying only the status code + upstream
                # request id — never the body.
                request_id = _request_id_from(http_response.headers)
                try:
                    data = http_response.json()
                except json.JSONDecodeError:
                    raise classify_provider_error(
                        status_code=http_response.status_code,
                        error_code="ADAPTER_FAILURE",
                        request_id=request_id,
                    ) from None
                if not isinstance(data, dict):
                    raise classify_provider_error(
                        status_code=http_response.status_code,
                        error_code="ADAPTER_FAILURE",
                        request_id=request_id,
                    )
                return data

            # Fatal 4xx (non-429) — do not retry.
            request_id = _request_id_from(http_response.headers)
            http_response.read()
            raise classify_provider_error(
                status_code=http_response.status_code,
                error_code=classify_provider_status(http_response.status_code),
                request_id=request_id,
            )

        # Retry exhausted on a retryable response (or transport error).
        if last_response is not None:
            raise classify_provider_error(
                status_code=last_response.status_code,
                error_code=classify_provider_status(last_response.status_code),
                request_id=_request_id_from(last_response.headers),
            )
        raise classify_provider_error(
            status_code=0,
            error_code="ADAPTER_FAILURE",
            request_id=None,
        )

    def _maybe_parse_structured_output(
        self,
        *,
        request: ProviderRequest,
        text: str,
        finish_reason: ProviderFinishReason,
    ) -> dict[str, Any] | None:
        """Parse JSON when the request asked for JSON.

        Scope (codex iter-1 important): the v2 adapter checks
        only JSON decodability + object-root shape. Schema
        validation against ``response_format.json_schema`` is
        the OpenAI Responses API's responsibility under
        ``strict=True``. Phase 4 step 4.6 ``schema_runtime``
        owns the Pydantic-class-based round-trip validator
        once the caller supplies the target class.

        ``ProviderResponse.parsed_output`` is rejected for
        ``CONTENT_FILTER`` / ``ERROR`` / ``LENGTH`` at the
        contract layer; we don't try to parse for those cases.
        """

        if request.response_format.kind not in (
            ResponseFormatKind.JSON_SCHEMA,
            ResponseFormatKind.JSON_OBJECT,
        ):
            return None
        if finish_reason in {
            ProviderFinishReason.CONTENT_FILTER,
            ProviderFinishReason.ERROR,
            ProviderFinishReason.LENGTH,
        }:
            return None
        if not text.strip():
            return None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            structured_decode_violation = StructuredOutputViolation(
                status_code=200,
                error_code="STRUCTURED_OUTPUT_VIOLATION",
                request_id=None,
            )
            raise structured_decode_violation from exc
        if not isinstance(parsed, dict):
            raise StructuredOutputViolation(
                status_code=200,
                error_code="STRUCTURED_OUTPUT_VIOLATION",
                request_id=None,
            )
        return parsed


__all__ = ["OpenAIResponsesAdapterV2"]
