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
  that callers can dispatch on without parsing prose
- ``request_id``: the upstream ``x-request-id`` header value (or
  ``None`` if missing) — the safe debugging anchor for cross-referencing
  with OpenAI dashboards
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Final

from veracrawl.contracts.agent import ModelRequest, ModelResponse
from veracrawl.contracts.common import stable_hash

_RESPONSES_ENDPOINT: Final[str] = "https://api.openai.com/v1/responses"
_REQUEST_ID_HEADER: Final[str] = "x-request-id"


class ModelProviderError(RuntimeError):
    """Adapter-level failure with structured fields and no body content.

    Subclasses ``RuntimeError`` so existing callers that catch
    ``RuntimeError`` continue to work, but the exception's string form
    deliberately contains only the status code, error category, and
    upstream request id. It never embeds the response body, the request
    prompt, or the context payload.
    """

    def __init__(
        self,
        *,
        status_code: int,
        error_code: str,
        request_id: str | None,
    ) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.request_id = request_id
        request_id_repr = request_id if request_id is not None else "<none>"
        super().__init__(
            f"OpenAI Responses API error: status={status_code} "
            f"code={error_code} request_id={request_id_repr}"
        )


def _classify_status(status: int) -> str:
    if status in (401, 403):
        return "AUTH_FAILED"
    if status == 429:
        return "RATE_LIMITED"
    if status == 404:
        return "NOT_FOUND"
    if status in (400, 422):
        return "BAD_REQUEST"
    if 500 <= status < 600:
        return "SERVER_ERROR"
    return "ADAPTER_FAILURE"


def _request_id_from_headers(headers: Any) -> str | None:
    """Read x-request-id from the various header objects urllib may surface."""
    if headers is None:
        return None
    # urllib.error.HTTPError.headers is an HTTPMessage; supports .get().
    getter = getattr(headers, "get", None)
    if callable(getter):
        value = getter(_REQUEST_ID_HEADER)
        if isinstance(value, str):
            return value
        # HTTPMessage returns None for missing keys; some test fakes return ''.
        if value:
            return str(value)
    # Fallback: dict-style access.
    if isinstance(headers, dict):
        value = headers.get(_REQUEST_ID_HEADER) or headers.get(
            _REQUEST_ID_HEADER.title()
        )
        if isinstance(value, str):
            return value
    return None


class OpenAIResponsesModelProviderRuntimeAdapter:
    provider_name = "OpenAI Responses API"

    def __init__(
        self,
        *,
        api_key: str,
        model_id: str,
        endpoint: str = _RESPONSES_ENDPOINT,
    ) -> None:
        self.model_id = model_id
        self.model_version = model_id
        self._api_key = api_key
        self._endpoint = endpoint
        self._context_payloads: dict[str, str] = {}
        self._token_usage: dict[str, dict[str, int]] = {}

    def set_context_payload(self, request_id: str, payload: str) -> None:
        self._context_payloads[request_id] = payload

    def token_usage_for(self, request_id: str) -> dict[str, int]:
        return self._token_usage.get(request_id, {})

    def complete(self, request: ModelRequest) -> ModelResponse:
        context_payload = self._context_payloads.get(
            request.id,
            f"context_bundle_ref={request.context_bundle_id}",
        )
        response = self._create_response(
            request=request, context_payload=context_payload
        )
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
                {
                    "role": "user",
                    "content": context_payload,
                },
            ],
            "max_output_tokens": 256,
        }
        http_request = urllib.request.Request(
            self._endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # Drain and discard the response body. We deliberately do NOT
            # parse, log, or stringify it — see module docstring.
            try:
                exc.read()
            except Exception:  # noqa: BLE001
                pass
            request_id = _request_id_from_headers(getattr(exc, "headers", None))
            raise ModelProviderError(
                status_code=int(exc.code),
                error_code=_classify_status(int(exc.code)),
                request_id=request_id,
            ) from None
        if not isinstance(data, dict):
            raise ModelProviderError(
                status_code=200,
                error_code="ADAPTER_FAILURE",
                request_id=None,
            )
        return data


def build_model_provider(
    *,
    api_key: str | None = None,
    model_id: str | None = None,
) -> OpenAIResponsesModelProviderRuntimeAdapter:
    resolved_key = api_key or os.getenv("OPENAI_API_KEY")
    if not resolved_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required for OpenAI Responses API adapter"
        )
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
