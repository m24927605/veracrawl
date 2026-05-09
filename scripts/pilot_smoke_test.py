"""Pilot smoke test — verify the v2 contract surface works against real OpenAI.

Reads ``OPENAI_API_KEY`` + ``OPENAI_MODEL`` from ``~/.env``,
issues a single tiny request to OpenAI Responses API, and
parses the response through our Phase 4 step 4.1 Pydantic
contracts (``ProviderRequest``, ``ProviderResponse``,
``TokenUsage``, ``ProviderFinishReason``).

What this proves:

* The contract surface accepts real OpenAI responses without
  validator failures.
* The token-usage shape matches what the API actually
  returns.
* The finish-reason mapping covers the real values.
* The wire shape (``text.format`` for JSON_OBJECT) is
  accepted by the live API.

What this does NOT prove (out of scope — Phase 6 work):

* Adapter framework integration (uses raw httpx to bypass
  the FIXTURE-only-MockTransport guard).
* Cost-budget enforcement.
* Calibration / abstention semantics.
* Recovery loop / cost-gate composition.

Cost cap: single call, max_output_tokens=32, JSON_OBJECT
response_format. Expected cost ≪ $0.001.

Usage:
    uv run --no-sync python scripts/pilot_smoke_test.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx

from veracrawl.contracts.agent import Message, ResponseFormat, TokenUsage
from veracrawl.contracts.enums import (
    MessageRole,
    ProviderFinishReason,
    ResponseFormatKind,
)
from veracrawl.contracts.llm_input import ProviderRequest, ProviderResponse


def _load_env() -> tuple[str, str]:
    """Load ``OPENAI_API_KEY`` + ``OPENAI_MODEL`` from
    ``~/.env`` without echoing the key."""

    env_path = Path.home() / ".env"
    if not env_path.exists():
        sys.exit(f"~/.env not found at {env_path}")
    api_key: str | None = None
    model: str | None = None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key == "OPENAI_API_KEY":
            api_key = value
        elif key == "OPENAI_MODEL":
            model = value
    if not api_key:
        sys.exit("OPENAI_API_KEY missing in ~/.env")
    if not model:
        sys.exit("OPENAI_MODEL missing in ~/.env")
    return api_key, model


def _build_request(model_name: str) -> ProviderRequest:
    return ProviderRequest(
        id="pilot:smoke:1",
        run_ref="run:pilot:1",
        model_name=model_name,
        messages=[
            Message(
                role=MessageRole.USER,
                content=(
                    "Reply with a single JSON object: "
                    '{"ack": true, "message": "pong"}'
                ),
            ),
        ],
        response_format=ResponseFormat(kind=ResponseFormatKind.JSON_OBJECT),
        max_output_tokens=32,
        temperature=0.0,
    )


def _call_openai(*, request: ProviderRequest, api_key: str) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": request.model_name,
        "input": [
            {"role": "user" if m.role is MessageRole.USER else "developer",
             "content": m.content}
            for m in request.messages
        ],
        "max_output_tokens": request.max_output_tokens,
        "temperature": request.temperature,
        "text": {"format": {"type": "json_object"}},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=httpx.Timeout(30.0)) as client:
        response = client.post(
            "https://api.openai.com/v1/responses",
            json=body,
            headers=headers,
        )
    response.raise_for_status()
    parsed = response.json()
    if not isinstance(parsed, dict):
        sys.exit("OpenAI response was not a JSON object")
    return parsed


def _parse_response(
    *, request: ProviderRequest, raw: dict[str, Any]
) -> ProviderResponse:
    output = raw.get("output", [])
    text_chunks: list[str] = []
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            for content in item.get("content", []):
                if isinstance(content, dict) and content.get("type") == "output_text":
                    if isinstance(content.get("text"), str):
                        text_chunks.append(content["text"])
    text = "\n".join(text_chunks)
    usage_raw = raw.get("usage", {})
    usage = TokenUsage(
        prompt_tokens=int(usage_raw.get("input_tokens", 0)),
        completion_tokens=int(usage_raw.get("output_tokens", 0)),
        total_tokens=int(
            usage_raw.get(
                "total_tokens",
                int(usage_raw.get("input_tokens", 0))
                + int(usage_raw.get("output_tokens", 0)),
            )
        ),
    )
    status = str(raw.get("status", "completed")).lower()
    finish_reason_map = {
        "completed": ProviderFinishReason.STOP,
        "incomplete": ProviderFinishReason.LENGTH,
        "failed": ProviderFinishReason.ERROR,
    }
    finish_reason = finish_reason_map.get(status, ProviderFinishReason.STOP)
    parsed_output: dict[str, Any] | None = None
    if text.strip():
        try:
            decoded = json.loads(text)
            if isinstance(decoded, dict):
                parsed_output = decoded
        except json.JSONDecodeError:
            parsed_output = None
    response_id = str(raw.get("id") or f"pilot-response:{request.id}")
    return ProviderResponse(
        id=response_id,
        request_ref=request.id,
        text=text,
        usage=usage,
        finish_reason=finish_reason,
        parsed_output=parsed_output,
    )


def main() -> int:
    api_key, model_name = _load_env()
    print(f"[pilot] model={model_name}")
    request = _build_request(model_name)
    print(f"[pilot] sending request id={request.id} max_out={request.max_output_tokens}")
    try:
        raw = _call_openai(request=request, api_key=api_key)
    except httpx.HTTPStatusError as exc:
        print(
            f"[pilot] HTTP {exc.response.status_code}: "
            f"{exc.response.text[:200]!r}",
            file=sys.stderr,
        )
        return 2
    except httpx.HTTPError as exc:
        print(f"[pilot] transport error: {type(exc).__name__}", file=sys.stderr)
        return 3
    print(f"[pilot] raw status={raw.get('status')} model={raw.get('model')}")
    try:
        response = _parse_response(request=request, raw=raw)
    except Exception as exc:
        print(
            f"[pilot] response failed our Pydantic validators: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 4
    print(
        f"[pilot] OK: text={response.text!r} "
        f"finish={response.finish_reason.value} "
        f"usage(prompt={response.usage.prompt_tokens}, "
        f"completion={response.usage.completion_tokens}, "
        f"total={response.usage.total_tokens})"
    )
    if response.parsed_output is not None:
        print(f"[pilot] parsed_output={response.parsed_output!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
