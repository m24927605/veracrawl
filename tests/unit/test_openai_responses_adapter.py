"""Tests for veracrawl.adapters.model_providers.openai_responses.

Covers the safety contract (no body / prompt content leaks into errors),
the retry/backoff behavior on 429 and 5xx, and the basic happy-path
shape. Uses ``httpx.MockTransport`` for deterministic in-process
verification — no real network and no real sleeps.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest

from veracrawl.adapters.model_providers.openai_responses import (
    ModelProviderError,
    OpenAIResponsesModelProviderRuntimeAdapter,
    _parse_retry_after,
    build_model_provider,
)
from veracrawl.contracts.agent import ModelRequest


def _make_request(request_id: str = "model-request:test-001") -> ModelRequest:
    return ModelRequest(
        id=request_id,
        agent_run_request_id="agent-run-request:test-001",
        provider_name="OpenAI Responses API",
        model_id="gpt-4.1-mini",
        prompt_template_ref="prompt-template:test:guidance",
        prompt_template_version="v1",
        context_bundle_id="context-bundle:test-001",
        tool_schema_refs=["tool-schema:test:summarize"],
        response_schema_ref="response-schema:test:guidance",
        redaction_policy_ref="redaction-policy:test:default",
    )


def _success_payload(text: str = "ok") -> dict[str, Any]:
    return {
        "id": "resp_test_ok",
        "status": "completed",
        "output": [{"content": [{"type": "output_text", "text": text}]}],
        "usage": {"input_tokens": 10, "output_tokens": 2, "total_tokens": 12},
    }


def _build_adapter(
    *,
    handler: Any,
    sleep_calls: list[float] | None = None,
    max_attempts: int = 3,
) -> OpenAIResponsesModelProviderRuntimeAdapter:
    transport = httpx.MockTransport(handler)
    sleep_log = sleep_calls if sleep_calls is not None else []

    def fake_sleep(seconds: float) -> None:
        sleep_log.append(seconds)

    return OpenAIResponsesModelProviderRuntimeAdapter(
        api_key="sk-test-fake",
        model_id="gpt-4.1-mini",
        max_attempts=max_attempts,
        transport=transport,
        sleep_fn=fake_sleep,
        jitter_fn=lambda: 0.0,  # deterministic backoff for tests
    )


# Module-level constants must remove the bogus default and use httpx.


def test_default_model_constant_removed() -> None:
    import veracrawl.adapters.model_providers.openai_responses as module

    source = module.__file__
    assert source is not None
    with open(source, encoding="utf-8") as fh:
        content = fh.read()
    assert "gpt-5.4-mini" not in content
    assert "_DEFAULT_MODEL" not in content


def test_module_no_longer_uses_urllib() -> None:
    import veracrawl.adapters.model_providers.openai_responses as module

    source = module.__file__
    assert source is not None
    with open(source, encoding="utf-8") as fh:
        content = fh.read()
    assert "import urllib" not in content


# Constructor / factory contract.


def test_constructor_requires_model_id() -> None:
    adapter = OpenAIResponsesModelProviderRuntimeAdapter(
        api_key="sk-test", model_id="gpt-4.1-mini"
    )
    assert adapter.model_id == "gpt-4.1-mini"
    with pytest.raises(TypeError):
        OpenAIResponsesModelProviderRuntimeAdapter(api_key="sk-test")  # type: ignore[call-arg]


def test_build_model_provider_requires_model_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("VERACRAWL_OPENAI_MODEL", raising=False)
    with pytest.raises(RuntimeError, match=r"model_id.*required"):
        build_model_provider(api_key="sk-test")


def test_build_model_provider_uses_env_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("VERACRAWL_OPENAI_MODEL", "gpt-4.1")
    adapter = build_model_provider(api_key="sk-test")
    assert adapter.model_id == "gpt-4.1"


# Error path safety: never leak body or prompt content.


def test_http_error_does_not_leak_response_body() -> None:
    secret = "system-prompt-leak-canary-12345"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"error": {"message": f"Invalid prompt format. Got: {secret}"}},
            headers={"x-request-id": "req_test_xyz"},
        )

    adapter = _build_adapter(handler=handler)
    with pytest.raises(ModelProviderError) as exc_info:
        adapter.complete(_make_request())

    err = exc_info.value
    assert err.status_code == 400
    assert err.error_code == "BAD_REQUEST"
    assert secret not in str(err)
    assert "Invalid prompt format" not in str(err)


def test_http_error_does_not_leak_request_prompt() -> None:
    request = _make_request()
    secret_prompt = "user-was-asking-about-credit-card-1234-5678-9012"

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"error": {"message": f"Cannot process: {secret_prompt}"}},
        )

    adapter = _build_adapter(handler=handler)
    adapter.set_context_payload(request.id, secret_prompt)

    with pytest.raises(ModelProviderError) as exc_info:
        adapter.complete(request)

    assert secret_prompt not in str(exc_info.value)
    assert "credit-card" not in str(exc_info.value)


def test_http_error_preserves_request_id() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            500,
            json={"error": {"message": "internal"}},
            headers={"x-request-id": "req_abc123def456"},
        )

    adapter = _build_adapter(handler=handler, max_attempts=1)
    with pytest.raises(ModelProviderError) as exc_info:
        adapter.complete(_make_request())
    assert exc_info.value.request_id == "req_abc123def456"


def test_http_error_when_no_request_id_header() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={})

    adapter = _build_adapter(handler=handler, max_attempts=1)
    with pytest.raises(ModelProviderError) as exc_info:
        adapter.complete(_make_request())
    assert exc_info.value.request_id is None
    assert exc_info.value.status_code == 503


def test_status_classification_table() -> None:
    cases = [
        (401, "AUTH_FAILED"),
        (403, "AUTH_FAILED"),
        (429, "RATE_LIMITED"),
        (500, "SERVER_ERROR"),
        (502, "SERVER_ERROR"),
        (503, "SERVER_ERROR"),
        (504, "SERVER_ERROR"),
        (400, "BAD_REQUEST"),
        (404, "NOT_FOUND"),
        (422, "BAD_REQUEST"),
    ]
    for status, expected_code in cases:

        def handler(_: httpx.Request, status: int = status) -> httpx.Response:
            return httpx.Response(status, json={"error": {"message": "x"}})

        adapter = _build_adapter(handler=handler, max_attempts=1)
        with pytest.raises(ModelProviderError) as exc_info:
            adapter.complete(_make_request())
        assert exc_info.value.error_code == expected_code, (
            f"status {status} should classify as {expected_code}"
        )


# Happy path.


def test_successful_completion_returns_response() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_success_payload())

    adapter = _build_adapter(handler=handler)
    response = adapter.complete(_make_request())
    assert response.status == "completed"
    assert adapter.token_usage_for(_make_request().id) == {
        "input_tokens": 10,
        "output_tokens": 2,
        "total_tokens": 12,
    }


def test_max_output_tokens_default_raised_to_4096() -> None:
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_body.update(json.loads(request.content))
        return httpx.Response(200, json=_success_payload())

    adapter = _build_adapter(handler=handler)
    adapter.complete(_make_request())
    assert captured_body["max_output_tokens"] == 4096


def test_max_output_tokens_can_be_overridden() -> None:
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_body.update(json.loads(request.content))
        return httpx.Response(200, json=_success_payload())

    adapter = OpenAIResponsesModelProviderRuntimeAdapter(
        api_key="sk-test",
        model_id="gpt-4.1-mini",
        max_output_tokens=128,
        transport=httpx.MockTransport(handler),
    )
    adapter.complete(_make_request())
    assert captured_body["max_output_tokens"] == 128


# Retry behavior.


def test_retries_on_429_then_succeeds() -> None:
    sleep_log: list[float] = []
    state = {"calls": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        state["calls"] += 1
        if state["calls"] == 1:
            return httpx.Response(429, json={}, headers={"retry-after": "2"})
        return httpx.Response(200, json=_success_payload())

    adapter = _build_adapter(handler=handler, sleep_calls=sleep_log)
    response = adapter.complete(_make_request())
    assert response.status == "completed"
    assert state["calls"] == 2
    assert sleep_log == [2.0]


def test_retries_on_5xx_then_succeeds() -> None:
    sleep_log: list[float] = []
    state = {"calls": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        state["calls"] += 1
        if state["calls"] < 3:
            return httpx.Response(503, json={})
        return httpx.Response(200, json=_success_payload())

    adapter = _build_adapter(handler=handler, sleep_calls=sleep_log)
    response = adapter.complete(_make_request())
    assert response.status == "completed"
    assert state["calls"] == 3
    # Two backoff sleeps before final success: attempt 1 wait 1s, attempt 2 wait 2s.
    assert sleep_log == [1.0, 2.0]


def test_retry_after_cap_60s() -> None:
    sleep_log: list[float] = []
    state = {"calls": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        state["calls"] += 1
        if state["calls"] == 1:
            return httpx.Response(429, json={}, headers={"retry-after": "3600"})
        return httpx.Response(200, json=_success_payload())

    adapter = _build_adapter(handler=handler, sleep_calls=sleep_log)
    adapter.complete(_make_request())
    assert sleep_log == [60.0]  # capped at 60s


def test_retry_exhaustion_raises_with_last_status() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={})

    adapter = _build_adapter(handler=handler, max_attempts=3)
    with pytest.raises(ModelProviderError) as exc_info:
        adapter.complete(_make_request())
    assert exc_info.value.status_code == 503
    assert exc_info.value.error_code == "SERVER_ERROR"


def test_fatal_4xx_does_not_retry() -> None:
    sleep_log: list[float] = []
    state = {"calls": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        state["calls"] += 1
        return httpx.Response(403, json={})

    adapter = _build_adapter(handler=handler, sleep_calls=sleep_log)
    with pytest.raises(ModelProviderError):
        adapter.complete(_make_request())
    assert state["calls"] == 1
    assert sleep_log == []


# Retry-After parser.


def test_parse_retry_after_seconds() -> None:
    assert _parse_retry_after("5") == 5.0
    assert _parse_retry_after("0") == 0.0


def test_parse_retry_after_http_date() -> None:
    when = datetime.now(UTC) + timedelta(seconds=10)
    raw = when.strftime("%a, %d %b %Y %H:%M:%S GMT")
    parsed = _parse_retry_after(raw)
    assert parsed is not None
    assert 5.0 <= parsed <= 15.0  # allow for clock skew between calls


def test_parse_retry_after_invalid_returns_none() -> None:
    assert _parse_retry_after("not a date") is None
    assert _parse_retry_after("") is None
    assert _parse_retry_after(None) is None


# Backwards-compat for catch sites that catch RuntimeError.


def test_model_provider_error_is_runtime_error_subclass() -> None:
    err = ModelProviderError(status_code=401, error_code="AUTH_FAILED", request_id=None)
    assert isinstance(err, RuntimeError)
