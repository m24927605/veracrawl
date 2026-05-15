"""Unit tests for OpenAIResponsesAdapterV2 artifact-persist wiring (s2.1 step 2)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import httpx

from veracrawl.adapters.model_providers.openai_responses_v2 import (
    OpenAIResponsesAdapterV2,
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

_T = datetime(2026, 5, 15, 12, 0, tzinfo=UTC)


def _canned_body() -> bytes:
    return json.dumps({
        "id": "resp_test_1",
        "status": "completed",
        "output": [
            {"content": [{"type": "output_text", "text": "hello world"}]},
        ],
        "usage": {
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
        },
    }).encode()


def _mock_transport(body: bytes, headers: dict[str, str] | None = None) -> httpx.MockTransport:
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body, headers=headers or {})

    return httpx.MockTransport(handler)


def _request() -> ProviderRequest:
    return ProviderRequest(
        id="req:test:1", run_ref="run:test:1", model_name="gpt-5",
        messages=[Message(role=MessageRole.USER, content="hi")],
        max_output_tokens=100, temperature=0.0,
        response_format=ResponseFormat(kind=ResponseFormatKind.TEXT),
    )


def _adapter(
    *, artifact_store: Any = None,
    persistence_policy: ProviderArtifactPersistencePolicy | None = None,
    transport: httpx.MockTransport | None = None,
    utc_clock: Any = None,
) -> OpenAIResponsesAdapterV2:
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
    return OpenAIResponsesAdapterV2(**kwargs)


# Test 9
def test_v2_complete_populates_raw_response_ref() -> None:
    store = InMemoryBytesArtifactStore()
    adapter = _adapter(artifact_store=store)
    response = adapter.complete(_request())
    assert response.raw_response_ref is not None
    assert response.raw_response_ref.startswith("artifact:sha256:")
    assert store.exists(response.raw_response_ref)


# Test 10
def test_v2_complete_persists_response_content_bytes_verbatim() -> None:
    body = _canned_body()
    store = InMemoryBytesArtifactStore()
    adapter = _adapter(artifact_store=store, transport=_mock_transport(body))
    response = adapter.complete(_request())
    assert store.read(response.raw_response_ref) == body


# Test 11
def test_v2_complete_metadata_provider_field_correct() -> None:
    store = InMemoryBytesArtifactStore()
    adapter = _adapter(artifact_store=store)
    response = adapter.complete(_request())
    meta = store.metadata_for(response.raw_response_ref)
    assert meta["provider"] == "openai-responses-v2"


# Test 12
def test_v2_complete_metadata_request_id_matches_request() -> None:
    store = InMemoryBytesArtifactStore()
    adapter = _adapter(artifact_store=store)
    req = _request()
    response = adapter.complete(req)
    meta = store.metadata_for(response.raw_response_ref)
    assert meta["request_id"] == req.id


# Test 13
def test_v2_complete_metadata_upstream_id_matches_response_id() -> None:
    store = InMemoryBytesArtifactStore()
    adapter = _adapter(artifact_store=store)
    response = adapter.complete(_request())
    meta = store.metadata_for(response.raw_response_ref)
    assert meta["upstream_id"] == response.id


# Test 14
def test_v2_complete_uses_injected_utc_clock_for_captured_at() -> None:
    store = InMemoryBytesArtifactStore()
    fixed = datetime(2026, 5, 15, 8, 0, tzinfo=UTC)
    adapter = _adapter(artifact_store=store, utc_clock=lambda: fixed)
    response = adapter.complete(_request())
    meta = store.metadata_for(response.raw_response_ref)
    assert meta["captured_at"] == fixed.isoformat()


# Test 16
def test_v2_artifact_ref_resolves_via_store_exists() -> None:
    store = InMemoryBytesArtifactStore()
    adapter = _adapter(artifact_store=store)
    response = adapter.complete(_request())
    assert store.exists(response.raw_response_ref) is True


# Persistence policy tests
# Test 26ca
def test_persistence_policy_persist_none_skips_write() -> None:
    store = InMemoryBytesArtifactStore()
    adapter = _adapter(
        artifact_store=store,
        persistence_policy=ProviderArtifactPersistencePolicy.PERSIST_NONE,
    )
    response = adapter.complete(_request())
    assert response.raw_response_ref is None


# Test 26cc
def test_persistence_policy_persist_non_secret_short_circuits_for_secret_responses() -> None:
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


def test_v2_no_artifact_store_returns_none_raw_response_ref() -> None:
    """Backward-compat: existing callers without artifact_store get None ref.
    s2 LlmCrawlPlanner's ProviderTraceMissingError handles fail-fast.
    """

    adapter = _adapter()  # no artifact_store
    response = adapter.complete(_request())
    assert response.raw_response_ref is None
