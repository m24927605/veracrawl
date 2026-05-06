"""Tests for veracrawl.adapters.model_providers.openai_responses.

These tests focus on the adapter's safety contract: error paths must not
leak prompt content, response bodies, or any other secret-bearing material
into exception messages or strings.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from io import BytesIO
from typing import Any
from unittest.mock import patch

import pytest

from veracrawl.adapters.model_providers.openai_responses import (
    ModelProviderError,
    OpenAIResponsesModelProviderRuntimeAdapter,
    build_model_provider,
)
from veracrawl.contracts.agent import ModelRequest


def _make_request() -> ModelRequest:
    return ModelRequest(
        id="model-request:test-001",
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


class _FakeHTTPError(Exception):
    """Mimics urllib.error.HTTPError minimal surface (code, headers, .read())."""

    def __init__(
        self,
        *,
        code: int,
        body: bytes,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.code = code
        self._body = body
        self.headers = headers or {}
        super().__init__(f"HTTP {code}")

    def read(self) -> bytes:
        return self._body


@pytest.fixture
def adapter() -> OpenAIResponsesModelProviderRuntimeAdapter:
    return OpenAIResponsesModelProviderRuntimeAdapter(
        api_key="sk-test-fake",
        model_id="gpt-4.1-mini",
    )


@pytest.fixture
def _patched_urlopen() -> Iterator[Any]:
    """Patch urllib.request.urlopen at the adapter module level."""
    with patch(
        "veracrawl.adapters.model_providers.openai_responses.urllib.request.urlopen"
    ) as mock:
        yield mock


def _http_error_response(
    code: int,
    body: dict[str, Any],
    headers: dict[str, str] | None = None,
) -> Any:
    """Build a urllib.error.HTTPError stand-in that the adapter catches."""
    import urllib.error

    body_bytes = json.dumps(body).encode("utf-8")
    return urllib.error.HTTPError(
        url="https://api.openai.com/v1/responses",
        code=code,
        msg="Test Error",
        hdrs=headers or {},  # type: ignore[arg-type]
        fp=BytesIO(body_bytes),
    )


def test_default_model_constant_removed() -> None:
    """The bogus _DEFAULT_MODEL = 'gpt-5.4-mini' must not exist anywhere."""
    import veracrawl.adapters.model_providers.openai_responses as module

    source = module.__file__
    assert source is not None
    with open(source, encoding="utf-8") as fh:
        content = fh.read()
    assert "gpt-5.4-mini" not in content
    # The named constant should not exist anymore (forces explicit model_id).
    assert "_DEFAULT_MODEL" not in content


def test_constructor_requires_model_id() -> None:
    """No default model: callers must specify which model they want."""
    # Sanity: passing model_id works.
    adapter = OpenAIResponsesModelProviderRuntimeAdapter(
        api_key="sk-test", model_id="gpt-4.1-mini"
    )
    assert adapter.model_id == "gpt-4.1-mini"

    # Omitting model_id must fail (it's a keyword-only required arg).
    with pytest.raises(TypeError):
        OpenAIResponsesModelProviderRuntimeAdapter(api_key="sk-test")  # type: ignore[call-arg]


def test_build_model_provider_requires_model_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Top-level factory must not silently fall back to a non-existent model."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("VERACRAWL_OPENAI_MODEL", raising=False)
    with pytest.raises(RuntimeError, match=r"model_id.*required"):
        build_model_provider(api_key="sk-test")


def test_build_model_provider_with_explicit_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    adapter = build_model_provider(api_key="sk-test", model_id="gpt-4.1-mini")
    assert adapter.model_id == "gpt-4.1-mini"


def test_build_model_provider_uses_env_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("VERACRAWL_OPENAI_MODEL", "gpt-4.1")
    adapter = build_model_provider(api_key="sk-test")
    assert adapter.model_id == "gpt-4.1"


def test_http_error_does_not_leak_response_body(
    adapter: OpenAIResponsesModelProviderRuntimeAdapter,
    _patched_urlopen: Any,
) -> None:
    """Critical: response body bytes must not appear in the raised exception.

    OpenAI 4xx error bodies frequently echo back portions of the request
    (model name, tool spec, even prompt text). A naive RuntimeError that
    stringifies the body propagates that content into logs and stack traces.
    """
    secret_in_body = "system-prompt-leak-canary-12345"
    error = _http_error_response(
        code=400,
        body={
            "error": {
                "message": f"Invalid prompt format. Got: {secret_in_body}",
                "type": "invalid_request_error",
            }
        },
        headers={"x-request-id": "req_test_xyz"},
    )
    _patched_urlopen.side_effect = error

    request = _make_request()
    with pytest.raises(ModelProviderError) as exc_info:
        adapter.complete(request)

    err = exc_info.value
    # Status code preserved.
    assert err.status_code == 400
    # Stringified exception must not contain the body.
    assert secret_in_body not in str(err)
    assert "Invalid prompt format" not in str(err)


def test_http_error_does_not_leak_request_prompt(
    adapter: OpenAIResponsesModelProviderRuntimeAdapter,
    _patched_urlopen: Any,
) -> None:
    """Even if upstream echoes our context payload back, it must not leak."""
    secret_prompt = "user-was-asking-about-credit-card-1234-5678-9012"
    adapter.set_context_payload(_make_request().id, secret_prompt)

    error = _http_error_response(
        code=400,
        body={"error": {"message": f"Cannot process: {secret_prompt}"}},
    )
    _patched_urlopen.side_effect = error

    with pytest.raises(ModelProviderError) as exc_info:
        adapter.complete(_make_request())

    assert secret_prompt not in str(exc_info.value)
    assert "credit-card" not in str(exc_info.value)


def test_http_error_preserves_request_id(
    adapter: OpenAIResponsesModelProviderRuntimeAdapter,
    _patched_urlopen: Any,
) -> None:
    """Request ID from x-request-id header is the safe debugging anchor."""
    error = _http_error_response(
        code=500,
        body={"error": {"message": "internal"}},
        headers={"x-request-id": "req_abc123def456"},
    )
    _patched_urlopen.side_effect = error

    with pytest.raises(ModelProviderError) as exc_info:
        adapter.complete(_make_request())

    assert exc_info.value.request_id == "req_abc123def456"


def test_http_error_when_no_request_id_header(
    adapter: OpenAIResponsesModelProviderRuntimeAdapter,
    _patched_urlopen: Any,
) -> None:
    error = _http_error_response(code=503, body={}, headers={})
    _patched_urlopen.side_effect = error

    with pytest.raises(ModelProviderError) as exc_info:
        adapter.complete(_make_request())

    assert exc_info.value.request_id is None
    assert exc_info.value.status_code == 503


def test_model_provider_error_classifies_status(
    adapter: OpenAIResponsesModelProviderRuntimeAdapter,
    _patched_urlopen: Any,
) -> None:
    """The error_code field gives callers a stable enum to dispatch on."""
    test_cases = [
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
    for status, expected_code in test_cases:
        error = _http_error_response(code=status, body={"error": {"message": "x"}})
        _patched_urlopen.side_effect = error
        with pytest.raises(ModelProviderError) as exc_info:
            adapter.complete(_make_request())
        assert exc_info.value.error_code == expected_code, (
            f"status {status} should classify as {expected_code}"
        )


def test_successful_completion_returns_response(
    adapter: OpenAIResponsesModelProviderRuntimeAdapter,
    _patched_urlopen: Any,
) -> None:
    """Sanity: happy path still works after the error-path refactor."""

    class _FakeContextManager:
        def __init__(self, payload: bytes) -> None:
            self._payload = payload

        def __enter__(self) -> Any:
            class _FakeResponse:
                def __init__(self, payload: bytes) -> None:
                    self._payload = payload

                def read(self) -> bytes:
                    return self._payload

            return _FakeResponse(self._payload)

        def __exit__(self, *_args: Any) -> None:
            pass

    payload = json.dumps(
        {
            "id": "resp_test_ok",
            "status": "completed",
            "output": [
                {
                    "content": [
                        {"type": "output_text", "text": "ok"},
                    ],
                },
            ],
            "usage": {
                "input_tokens": 10,
                "output_tokens": 2,
                "total_tokens": 12,
            },
        }
    ).encode()
    _patched_urlopen.return_value = _FakeContextManager(payload)

    response = adapter.complete(_make_request())
    assert response.status == "completed"
    assert adapter.token_usage_for(_make_request().id) == {
        "input_tokens": 10,
        "output_tokens": 2,
        "total_tokens": 12,
    }


def test_model_provider_error_is_runtime_error_subclass() -> None:
    """Backwards compat: existing callers catching RuntimeError still match."""
    err = ModelProviderError(status_code=401, error_code="AUTH_FAILED", request_id=None)
    assert isinstance(err, RuntimeError)
