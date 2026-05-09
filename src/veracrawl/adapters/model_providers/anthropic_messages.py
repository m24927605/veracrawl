"""Phase 4 step 4.3 — AnthropicMessagesAdapter.

Provider-blind v2 adapter against Anthropic Messages API
(``POST /v1/messages``). Implements ``ModelProviderPortV2``
alongside :class:`OpenAIResponsesAdapterV2` (Phase 4 step 4.2)
to prove the provider-swap contract: callers consume the same
``ProviderRequest`` / ``ProviderResponse`` shapes regardless of
provider.

Phase 4 step 4.2 codex iter-1..5 findings are baked in upfront:

* **Capability table empty by deliberate scope**: full JSON-
  Schema validation deferred to Phase 4 step 4.6
  ``schema_runtime`` (Pydantic-class round-trip); tool-call
  / vision / extended-thinking deferred until
  ``ProviderResponse`` carries the required fields.
* **``current_mode()``-aware production gate**: omitting
  ``runtime_mode`` falls through to the project-wide
  ``current_mode()`` so ``VERACRAWL_RUNTIME_MODE=production``
  triggers the same gate every other adapter respects.
* **``MockTransport``-only fixture mode**: real network
  transports (``httpx.HTTPTransport`` etc.) refused at
  construction so production-egress gating is mechanically
  enforced.
* **RAW_RESPONSE_LEAK boundary**: every error path raises a
  sanitized ``ProviderAdapterFailure`` carrying only status
  code + upstream ``request-id``; ``json.JSONDecodeError`` is
  caught and converted via ``raise … from None``; ``int(...)``
  on usage payload is replaced with a non-coercing
  ``_coerce_non_negative_int`` helper that rejects ``bool``
  (``isinstance(True, int) is True``), non-int, and negative
  values.
* **Retry policy**: 429 / 5xx retried up to ``max_attempts``
  with exponential backoff + jitter; ``Retry-After`` honored
  (delta-seconds + HTTP-date), capped at 60s.
* **Sanitized response id**: ``response_data["id"]`` validated
  as a non-blank string before becoming
  ``ProviderResponse.id``.

Wire shape — Anthropic Messages API:

```
POST /v1/messages
Headers:
  x-api-key: <api_key>
  anthropic-version: 2023-06-01
  content-type: application/json

Body:
  {"model": "...", "messages": [...], "system": "...",
   "max_tokens": N, "temperature": 0.0,
   "stop_sequences": [...]}

Response (success):
  {"id": "msg_...", "model": "...",
   "content": [{"type": "text", "text": "..."}],
   "stop_reason": "end_turn" | "max_tokens" | "stop_sequence" |
                  "tool_use",
   "usage": {"input_tokens": N, "output_tokens": M,
             "cache_read_input_tokens": K}}
```

Mapping ``ProviderRequest`` → Anthropic body:

* ``messages`` translates one-to-one for USER/ASSISTANT roles.
* ``MessageRole.SYSTEM`` is hoisted to the top-level
  ``system`` field (Anthropic dedicates a parameter for it).
* ``MessageRole.TOOL`` is refused (deferred — same as the
  OpenAI v2 adapter; Anthropic tool-result blocks have a
  different wire shape too).
* ``response_format.kind == JSON_SCHEMA`` is **not** emitted
  on the wire (Anthropic Messages API does not support
  per-call JSON-schema enforcement; structured output is a
  prompt-engineering pattern). The adapter still parses the
  text as JSON for callers that opt into that flow, with the
  same minimal-shape check as OpenAI v2 — and the capability
  flag returns ``False`` so callers requiring guaranteed
  structured output do not route here.

Mapping Anthropic ``stop_reason`` → :class:`ProviderFinishReason`:

* ``end_turn`` → ``STOP``
* ``max_tokens`` → ``LENGTH``
* ``stop_sequence`` → ``STOP``
* ``tool_use`` → ``TOOL_CALL``
* unknown values → ``ERROR``
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
    current_mode,
)

_MESSAGES_ENDPOINT: Final[str] = "https://api.anthropic.com/v1/messages"
_API_VERSION_HEADER_VALUE: Final[str] = "2023-06-01"
_REQUEST_ID_HEADER: Final[str] = "request-id"
_RETRY_AFTER_HEADER: Final[str] = "retry-after"
_DEFAULT_MAX_ATTEMPTS: Final[int] = 3
_RETRY_AFTER_CAP_S: Final[float] = 60.0
_RETRYABLE_STATUSES: Final[frozenset[int]] = frozenset({429, 500, 502, 503, 504, 529})
_DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=60.0, pool=10.0)

_FINISH_REASON_MAP: Final[dict[str, ProviderFinishReason]] = {
    "end_turn": ProviderFinishReason.STOP,
    "max_tokens": ProviderFinishReason.LENGTH,
    "stop_sequence": ProviderFinishReason.STOP,
    "tool_use": ProviderFinishReason.TOOL_CALL,
}

_SUPPORTED_CAPABILITIES: Final[frozenset[ModelCapability]] = frozenset()
"""Phase 4 step 4.3 lands as a building block — every
capability is deferred (full JSON-Schema validation is the
``schema_runtime`` step 4.6 Pydantic-class validator; tool-
call / vision / extended-thinking until the
``ProviderResponse`` contract grows the required fields).
Codex iter-5 of step 4.2 settled the policy: flip flags to
``True`` only when the backing implementation lands."""


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


def _coerce_non_negative_int(value: Any) -> int | None:
    """Codex iter-3 of step 4.2: ``int(...)`` on attacker-
    controlled upstream payloads can leak the value via
    exception messages. Return ``None`` for any value that
    is not a plain non-negative integer; ``bool`` is
    explicitly rejected (``isinstance(True, int) is True``)."""

    if isinstance(value, bool):
        return None
    if not isinstance(value, int):
        return None
    if value < 0:
        return None
    return value


def _coerce_optional_subtotal(value: Any) -> int:
    if value is None:
        return 0
    coerced = _coerce_non_negative_int(value)
    return coerced if coerced is not None else 0


def _split_system_messages(messages: list[Message]) -> tuple[str | None, list[Message]]:
    """Anthropic dedicates a ``system`` body field; the
    ``messages`` array carries USER / ASSISTANT only.
    Concatenate any leading SYSTEM messages and return the
    rest unchanged."""

    system_chunks: list[str] = []
    rest: list[Message] = []
    for message in messages:
        if message.role is MessageRole.SYSTEM:
            system_chunks.append(message.content)
        else:
            rest.append(message)
    system_prompt = "\n\n".join(system_chunks) if system_chunks else None
    return system_prompt, rest


def _message_to_anthropic(message: Message) -> dict[str, Any]:
    """Translate USER / ASSISTANT messages to Anthropic body shape."""

    role_map: dict[MessageRole, str] = {
        MessageRole.USER: "user",
        MessageRole.ASSISTANT: "assistant",
    }
    return {"role": role_map[message.role], "content": message.content}


def _extract_output_text(response: dict[str, Any]) -> str:
    chunks: list[str] = []
    content = response.get("content")
    if not isinstance(content, list):
        return ""
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            text = block.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "".join(chunks)


def _extract_usage(response: dict[str, Any]) -> TokenUsage:
    """Build ``TokenUsage`` from the Anthropic ``usage`` block.

    Anthropic does not return ``total_tokens`` — it's computed
    from ``input_tokens + output_tokens``. ``cache_read_input_tokens``
    maps to the v2 ``cached_input_tokens`` subtotal.
    Sanitized ``ProviderAdapterFailure`` on any malformed
    field (RAW_RESPONSE_LEAK boundary)."""

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
    cached_input = _coerce_optional_subtotal(usage_raw.get("cache_read_input_tokens"))
    if cached_input > prompt:
        raise ProviderAdapterFailure(
            status_code=200,
            error_code="ADAPTER_FAILURE",
            request_id=None,
        )
    return TokenUsage(
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=prompt + completion,
        cached_input_tokens=cached_input,
        reasoning_tokens=0,
    )


def _map_finish_reason(stop_reason: Any) -> ProviderFinishReason:
    if not isinstance(stop_reason, str):
        return ProviderFinishReason.ERROR
    return _FINISH_REASON_MAP.get(stop_reason.lower(), ProviderFinishReason.ERROR)


class AnthropicMessagesAdapter:
    """Provider-blind v2 Anthropic Messages adapter."""

    provider_name = "Anthropic Messages API (v2)"

    def __init__(
        self,
        *,
        api_key: str,
        endpoint: str = _MESSAGES_ENDPOINT,
        max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
        runtime_mode: RuntimeMode | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        jitter_fn: Callable[[], float] | None = None,
    ) -> None:
        effective_mode = runtime_mode if runtime_mode is not None else current_mode()
        if effective_mode is RuntimeMode.PRODUCTION:
            raise ProductionRuntimeNotImplemented(
                backend="anthropic_messages",
                gate="phase_4_step_4_3_production_call",
            )
        if not api_key or not api_key.strip():
            raise ValueError("AnthropicMessagesAdapter requires a non-blank api_key")
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if transport is None:
            raise ValueError(
                "AnthropicMessagesAdapter in FIXTURE mode requires an explicit "
                "httpx.MockTransport. The PRODUCTION wiring (real network "
                "egress) is gated until Phase 6 step 6.1."
            )
        if not isinstance(transport, httpx.MockTransport):
            raise ValueError(
                "AnthropicMessagesAdapter in FIXTURE mode only accepts "
                "httpx.MockTransport (real network transports are refused — "
                "they would bypass the production-egress gate)."
            )
        self._api_key = api_key
        self._endpoint = endpoint
        self._max_attempts = max_attempts
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
        # Tool-call refusal mirrors Phase 4 step 4.2 codex iter-2.
        if request.tools:
            raise NotImplementedError(
                "AnthropicMessagesAdapter does not yet support tool calls; "
                "the ProviderResponse contract surface for tool calls is a "
                "deferred Phase 4 follow-up."
            )
        if any(message.role is MessageRole.TOOL for message in request.messages):
            raise NotImplementedError(
                "AnthropicMessagesAdapter does not yet support tool-result "
                "messages (MessageRole.TOOL)."
            )
        body = self._build_request_body(request)
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": _API_VERSION_HEADER_VALUE,
            "content-type": "application/json",
        }
        response_data = self._post_with_retry(body=body, headers=headers)
        text = _extract_output_text(response_data)
        usage = _extract_usage(response_data)
        finish_reason = _map_finish_reason(response_data.get("stop_reason"))
        parsed_output = self._maybe_parse_structured_output(
            request=request, text=text, finish_reason=finish_reason
        )
        upstream_id = response_data.get("id")
        if isinstance(upstream_id, str) and upstream_id.strip():
            response_id = upstream_id.strip()
        else:
            response_id = f"anthropic-msg:{request.id}"
        return ProviderResponse(
            id=response_id,
            request_ref=request.id,
            text=text,
            usage=usage,
            finish_reason=finish_reason,
            parsed_output=parsed_output,
        )

    def _build_request_body(self, request: ProviderRequest) -> dict[str, Any]:
        system_prompt, rest = _split_system_messages(request.messages)
        body: dict[str, Any] = {
            "model": request.model_name,
            "messages": [_message_to_anthropic(m) for m in rest],
            "max_tokens": request.max_output_tokens,
            "temperature": request.temperature,
        }
        if system_prompt is not None:
            body["system"] = system_prompt
        # Anthropic Messages API does not support per-call
        # JSON-schema enforcement; structured output is a
        # prompt-engineering pattern (the caller's prompt asks
        # for JSON; the adapter parses + minimally validates).
        # The wire body therefore omits any
        # ``response_format``-equivalent field.
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
                http_response.read()
                self._sleep(wait)
                continue

            if http_response.is_success:
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

            request_id = _request_id_from(http_response.headers)
            http_response.read()
            raise classify_provider_error(
                status_code=http_response.status_code,
                error_code=classify_provider_status(http_response.status_code),
                request_id=request_id,
            )

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
        """Best-effort JSON parse for ``JSON_SCHEMA`` /
        ``JSON_OBJECT`` requests. Anthropic does not enforce
        the schema upstream, so the adapter's role is to
        catch obvious shape failures (non-JSON, non-object
        root, missing required fields). Full validation is
        Phase 4 step 4.6 ``schema_runtime``."""

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
        except json.JSONDecodeError:
            raise StructuredOutputViolation(
                status_code=200,
                error_code="STRUCTURED_OUTPUT_VIOLATION",
                request_id=None,
            ) from None
        if not isinstance(parsed, dict):
            raise StructuredOutputViolation(
                status_code=200,
                error_code="STRUCTURED_OUTPUT_VIOLATION",
                request_id=None,
            )
        if request.response_format.kind is ResponseFormatKind.JSON_SCHEMA:
            self._validate_minimal_schema(
                parsed=parsed,
                schema=request.response_format.json_schema or {},
            )
        return parsed

    def _validate_minimal_schema(
        self, *, parsed: dict[str, Any], schema: dict[str, Any]
    ) -> None:
        declared_type = schema.get("type")
        if declared_type is not None and declared_type != "object":
            raise StructuredOutputViolation(
                status_code=200,
                error_code="STRUCTURED_OUTPUT_VIOLATION",
                request_id=None,
            )
        required = schema.get("required")
        if isinstance(required, list):
            for field in required:
                if not isinstance(field, str):
                    continue
                if field not in parsed:
                    raise StructuredOutputViolation(
                        status_code=200,
                        error_code="STRUCTURED_OUTPUT_VIOLATION",
                        request_id=None,
                    )


__all__ = ["AnthropicMessagesAdapter"]
