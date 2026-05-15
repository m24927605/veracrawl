"""Unit tests for AnthropicMessagesAdapter artifact-persist wiring (s2.1 step 3)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import httpx

from veracrawl.adapters.model_providers.anthropic_messages import (
    AnthropicMessagesAdapter,
)
from veracrawl.adapters.object_stores.in_memory_bytes_artifact_store import (
    InMemoryBytesArtifactStore,
)
from veracrawl.contracts.agent import Message, ResponseFormat
from veracrawl.contracts.enums import (
    MessageRole,
    ProviderArtifactPersistencePolicy,
    ResponseFormatKind,
)
from veracrawl.contracts.llm_input import ProviderRequest
from veracrawl.runtime_support.runtime_mode import RuntimeMode


def _canned_body() -> bytes:
    return json.dumps({
        "id": "msg_anthropic_test",
        "model": "claude-sonnet-4-6",
        "content": [{"type": "text", "text": "hello world"}],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 10, "output_tokens": 5},
    }).encode()


def _mock_transport(
    body: bytes, headers: dict[str, str] | None = None,
) -> httpx.MockTransport:
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body, headers=headers or {})

    return httpx.MockTransport(handler)


def _request() -> ProviderRequest:
    return ProviderRequest(
        id="req:test:1",
        run_ref="run:test:1",
        model_name="claude-sonnet-4-6",
        messages=[Message(role=MessageRole.USER, content="hi")],
        max_output_tokens=100,
        temperature=0.0,
        response_format=ResponseFormat(kind=ResponseFormatKind.TEXT),
    )


def _adapter(
    *,
    artifact_store: Any = None,
    persistence_policy: ProviderArtifactPersistencePolicy | None = None,
    transport: httpx.MockTransport | None = None,
    utc_clock: Any = None,
) -> AnthropicMessagesAdapter:
    kwargs: dict[str, Any] = {
        "api_key": "test-key",
        "runtime_mode": RuntimeMode.FIXTURE,
        "transport": transport or _mock_transport(_canned_body()),
    }
    if artifact_store is not None:
        kwargs["artifact_store"] = artifact_store
    if persistence_policy is not None:
        kwargs["persistence_policy"] = persistence_policy
    if utc_clock is not None:
        kwargs["utc_clock"] = utc_clock
    return AnthropicMessagesAdapter(**kwargs)


# Test 17: ctor accepts persistence_policy
def test_anthropic_ctor_accepts_persistence_policy() -> None:
    adapter = _adapter(
        artifact_store=InMemoryBytesArtifactStore(),
        persistence_policy=ProviderArtifactPersistencePolicy.PERSIST_ALL,
    )
    assert adapter is not None


# Test 18: complete populates raw_response_ref
def test_anthropic_complete_populates_raw_response_ref() -> None:
    store = InMemoryBytesArtifactStore()
    adapter = _adapter(artifact_store=store)
    response = adapter.complete(_request())
    assert response.raw_response_ref is not None
    assert response.raw_response_ref.startswith("artifact:sha256:")
    assert store.exists(response.raw_response_ref)


# Test 19: complete persists response content bytes verbatim
def test_anthropic_complete_persists_response_content_bytes_verbatim() -> None:
    body = _canned_body()
    store = InMemoryBytesArtifactStore()
    adapter = _adapter(artifact_store=store, transport=_mock_transport(body))
    response = adapter.complete(_request())
    assert store.read(response.raw_response_ref) == body


# Test 20: metadata provider field is "anthropic-messages-v2"
def test_anthropic_complete_metadata_provider_field_correct() -> None:
    store = InMemoryBytesArtifactStore()
    adapter = _adapter(artifact_store=store)
    response = adapter.complete(_request())
    meta = store.metadata_for(response.raw_response_ref)
    assert meta["provider"] == "anthropic-messages-v2"


# Test 21: metadata request_id matches request
def test_anthropic_complete_metadata_request_id_matches_request() -> None:
    store = InMemoryBytesArtifactStore()
    adapter = _adapter(artifact_store=store)
    req = _request()
    response = adapter.complete(req)
    meta = store.metadata_for(response.raw_response_ref)
    assert meta["request_id"] == req.id


# Test 22: metadata upstream_id matches response_id
def test_anthropic_complete_metadata_upstream_id_matches_response_id() -> None:
    store = InMemoryBytesArtifactStore()
    adapter = _adapter(artifact_store=store)
    response = adapter.complete(_request())
    meta = store.metadata_for(response.raw_response_ref)
    assert meta["upstream_id"] == response.id


# Test 23: uses injected utc_clock for captured_at
def test_anthropic_complete_uses_injected_utc_clock_for_captured_at() -> None:
    store = InMemoryBytesArtifactStore()
    fixed = datetime(2026, 5, 15, 8, 0, tzinfo=UTC)
    adapter = _adapter(artifact_store=store, utc_clock=lambda: fixed)
    response = adapter.complete(_request())
    meta = store.metadata_for(response.raw_response_ref)
    assert meta["captured_at"] == fixed.isoformat()


# Test 24: PERSIST_NONE skips write
def test_anthropic_persistence_policy_persist_none_skips_write() -> None:
    store = InMemoryBytesArtifactStore()
    adapter = _adapter(
        artifact_store=store,
        persistence_policy=ProviderArtifactPersistencePolicy.PERSIST_NONE,
    )
    response = adapter.complete(_request())
    assert response.raw_response_ref is None


# Test 25: PERSIST_NON_SECRET short-circuits for secret responses
def test_anthropic_persistence_policy_persist_non_secret_short_circuits() -> None:
    store = InMemoryBytesArtifactStore()
    adapter = _adapter(
        artifact_store=store,
        persistence_policy=ProviderArtifactPersistencePolicy.PERSIST_NON_SECRET,
        transport=_mock_transport(
            _canned_body(), headers={"X-Veracrawl-Secret": "true"},
        ),
    )
    response = adapter.complete(_request())
    assert response.raw_response_ref is None


# Backward-compat: no artifact_store wired returns None
def test_anthropic_no_artifact_store_returns_none_raw_response_ref() -> None:
    """Backward-compat: existing callers without artifact_store get None ref.
    s2 LlmCrawlPlanner's ProviderTraceMissingError handles fail-fast.
    """

    adapter = _adapter()  # no artifact_store
    response = adapter.complete(_request())
    assert response.raw_response_ref is None
