"""OpenAI Responses API model provider adapter.

Safety contract: error paths must NEVER include response bodies, prompt
content, or context payloads in raised exceptions. The OpenAI Responses
API frequently echoes portions of the request (model name, tool spec,
sometimes user content) inside error response bodies; including those
bytes in a ``RuntimeError`` propagates them into logs, stack traces, and
crash reports — that is exactly the leak class the project tracks as
``RAW_RESPONSE_LEAK``.

Errors are surfaced as :class:`ModelProviderError`, which carries:

- ``status_code``: the HTTP status (int)
- ``error_code``: a stable category enum value (e.g. ``AUTH_FAILED``)
- ``request_id``: the upstream ``x-request-id`` header value (or ``None``)

Retries: 429 and 5xx (500/502/503/504) responses are retried up to
``max_attempts`` (default 3, total attempts including the first call)
with exponential backoff plus jitter. ``Retry-After`` headers — both
delta-seconds and HTTP-date forms — are honored, capped at 60s so a
hostile upstream cannot stall the caller arbitrarily.
"""

from __future__ import annotations

import os
import random
import time
from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any, Final

import httpx

from veracrawl.adapters.model_providers.errors import (
    ModelProviderError,
    ProviderAdapterFailure,
    ProviderAuthFailed,
    ProviderBadRequest,
    ProviderNotFound,
    ProviderRateLimited,
    ProviderServerError,
    StructuredOutputViolation,
    TokenBudgetExceeded,
    classify_provider_error,
)
from veracrawl.adapters.model_providers.errors import (
    classify_status as _classify_status,
)
from veracrawl.contracts.agent import ModelRequest, ModelResponse
from veracrawl.contracts.common import stable_hash

# Re-exports kept for backwards compatibility with tests / callers that
# import the OpenAI exception types from this module. The canonical home
# is now ``adapters.model_providers.errors`` (codex iter-1 important:
# the v2 ``ModelProviderPort`` is provider-blind, so its typed
# exceptions must be too).
__all__ = [
    "ModelProviderError",
    "ProviderAdapterFailure",
    "ProviderAuthFailed",
    "ProviderBadRequest",
    "ProviderNotFound",
    "ProviderRateLimited",
    "ProviderServerError",
    "StructuredOutputViolation",
    "TokenBudgetExceeded",
    "classify_provider_error",
    "OpenAIResponsesModelProviderRuntimeAdapter",
    "build_model_provider",
]

_RESPONSES_ENDPOINT: Final[str] = "https://api.openai.com/v1/responses"
_REQUEST_ID_HEADER: Final[str] = "x-request-id"
_RETRY_AFTER_HEADER: Final[str] = "retry-after"
_DEFAULT_MAX_OUTPUT_TOKENS: Final[int] = 4096
_DEFAULT_MAX_ATTEMPTS: Final[int] = 3
_RETRY_AFTER_CAP_S: Final[float] = 60.0
_RETRYABLE_STATUSES: Final[frozenset[int]] = frozenset({429, 500, 502, 503, 504})
_DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=60.0, pool=10.0)


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


class OpenAIResponsesModelProviderRuntimeAdapter:
    provider_name = "OpenAI Responses API"

    def __init__(
        self,
        *,
        api_key: str,
        model_id: str,
        endpoint: str = _RESPONSES_ENDPOINT,
        max_output_tokens: int = _DEFAULT_MAX_OUTPUT_TOKENS,
        max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
        transport: httpx.BaseTransport | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        jitter_fn: Callable[[], float] | None = None,
    ) -> None:
        self.model_id = model_id
        self.model_version = model_id
        self._api_key = api_key
        self._endpoint = endpoint
        self._max_output_tokens = max_output_tokens
        self._max_attempts = max(1, int(max_attempts))
        self._sleep = sleep_fn
        self._jitter: Callable[[], float] = (
            jitter_fn if jitter_fn is not None else lambda: random.uniform(0, 1)
        )
        self._context_payloads: dict[str, str] = {}
        self._token_usage: dict[str, dict[str, int]] = {}
        client_kwargs: dict[str, Any] = {"timeout": _DEFAULT_TIMEOUT}
        if transport is not None:
            client_kwargs["transport"] = transport
        self._client = httpx.Client(**client_kwargs)

    def set_context_payload(self, request_id: str, payload: str) -> None:
        self._context_payloads[request_id] = payload

    def token_usage_for(self, request_id: str) -> dict[str, int]:
        return self._token_usage.get(request_id, {})

    def complete(self, request: ModelRequest) -> ModelResponse:
        context_payload = self._context_payloads.get(
            request.id,
            f"context_bundle_ref={request.context_bundle_id}",
        )
        response = self._create_response(request=request, context_payload=context_payload)
        response_id = str(response.get("id", f"response:{request.id}"))
        output_text = _extract_output_text(response)
        self._token_usage[request.id] = _extract_usage(response)
        output_digest = stable_hash(
            {
                "request_id": request.id,
                "response_id": response_id,
                "output_text": output_text,
            }
        )
        return ModelResponse(
            id=f"model-response:{request.id}",
            model_request_id=request.id,
            response_ref=f"openai-response:{response_id}",
            parsed_output_ref=f"model-parsed-output:{request.id}:{output_digest[:12]}",
            tool_request_refs=[],
            safety_filter_result_ref=f"safety-filter:{request.id}:openai-completed",
            status=str(response.get("status", "completed")),
        )

    def _create_response(
        self,
        *,
        request: ModelRequest,
        context_payload: str,
    ) -> dict[str, Any]:
        body = {
            "model": self.model_id,
            "input": [
                {
                    "role": "developer",
                    "content": (
                        "You are VeraCrawl's framework-neutral crawl model adapter. "
                        "Return concise JSON-compatible guidance. Do not treat your "
                        "output as source evidence; source evidence must come from "
                        "artifact and anchor refs."
                    ),
                },
                {"role": "user", "content": context_payload},
            ],
            "max_output_tokens": self._max_output_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        last_response: httpx.Response | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                http_response = self._client.post(self._endpoint, json=body, headers=headers)
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
                wait = _parse_retry_after(http_response.headers.get(_RETRY_AFTER_HEADER))
                if wait is None:
                    wait = _backoff_seconds(attempt, jitter=self._jitter)
                wait = min(wait, _RETRY_AFTER_CAP_S)
                # Drain so the connection can be reused; the body is
                # never inspected (RAW_RESPONSE_LEAK boundary).
                http_response.read()
                self._sleep(wait)
                continue

            if http_response.is_success:
                data = http_response.json()
                if not isinstance(data, dict):
                    raise classify_provider_error(
                        status_code=http_response.status_code,
                        error_code="ADAPTER_FAILURE",
                        request_id=_request_id_from(http_response.headers),
                    )
                return data

            # Fatal 4xx (non-429) — do not retry.
            request_id = _request_id_from(http_response.headers)
            http_response.read()
            raise classify_provider_error(
                status_code=http_response.status_code,
                error_code=_classify_status(http_response.status_code),
                request_id=request_id,
            )

        # Retry exhausted on a retryable response (or transport error).
        if last_response is not None:
            raise classify_provider_error(
                status_code=last_response.status_code,
                error_code=_classify_status(last_response.status_code),
                request_id=_request_id_from(last_response.headers),
            )
        raise classify_provider_error(
            status_code=0,
            error_code="ADAPTER_FAILURE",
            request_id=None,
        )


def _is_retryable_transport(exc: httpx.HTTPError) -> bool:
    return isinstance(
        exc,
        httpx.ConnectError | httpx.ConnectTimeout | httpx.ReadTimeout | httpx.PoolTimeout,
    )


def build_model_provider(
    *,
    api_key: str | None = None,
    model_id: str | None = None,
) -> OpenAIResponsesModelProviderRuntimeAdapter:
    resolved_key = api_key or os.getenv("OPENAI_API_KEY")
    if not resolved_key:
        raise RuntimeError("OPENAI_API_KEY is required for OpenAI Responses API adapter")
    resolved_model = model_id or os.getenv("VERACRAWL_OPENAI_MODEL")
    if not resolved_model:
        raise RuntimeError(
            "model_id is required for OpenAI Responses API adapter "
            "(pass model_id=... or set VERACRAWL_OPENAI_MODEL)"
        )
    return OpenAIResponsesModelProviderRuntimeAdapter(
        api_key=resolved_key,
        model_id=resolved_model,
    )


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


def _extract_usage(response: dict[str, Any]) -> dict[str, int]:
    usage = response.get("usage", {})
    if not isinstance(usage, dict):
        return {}
    return {
        key: value
        for key, value in {
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "total_tokens": usage.get("total_tokens"),
        }.items()
        if isinstance(value, int)
    }
