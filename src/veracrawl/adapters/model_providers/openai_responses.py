"""OpenAI Responses API model provider adapter."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from veracrawl.contracts.agent import ModelRequest, ModelResponse
from veracrawl.contracts.common import stable_hash

_DEFAULT_MODEL = "gpt-5.4-mini"
_RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"


class OpenAIResponsesModelProviderRuntimeAdapter:
    provider_name = "OpenAI Responses API"

    def __init__(
        self,
        *,
        api_key: str,
        model_id: str = _DEFAULT_MODEL,
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
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI Responses API failed: {exc.code} {error_body}") from exc
        if not isinstance(data, dict):
            raise RuntimeError("OpenAI Responses API returned a non-object response")
        return data


def build_model_provider(
    *,
    api_key: str | None = None,
    model_id: str | None = None,
) -> OpenAIResponsesModelProviderRuntimeAdapter:
    resolved_key = api_key or os.getenv("OPENAI_API_KEY")
    if not resolved_key:
        raise RuntimeError("OPENAI_API_KEY is required for OpenAI Responses API adapter")
    return OpenAIResponsesModelProviderRuntimeAdapter(
        api_key=resolved_key,
        model_id=model_id or os.getenv("VERACRAWL_OPENAI_MODEL") or _DEFAULT_MODEL,
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
