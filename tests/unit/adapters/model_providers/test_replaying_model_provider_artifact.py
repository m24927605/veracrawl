"""Unit tests for ``ReplayingModelProviderV2`` raw-response-ref keying (s2.1 step 4)."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from veracrawl.adapters.model_providers.openai_responses_v2 import (
    OpenAIResponsesAdapterV2,
)
from veracrawl.adapters.model_providers.replaying_model_provider import (
    ReplayingModelProviderV2,
)
from veracrawl.adapters.object_stores.in_memory_bytes_artifact_store import (
    InMemoryBytesArtifactStore,
)
from veracrawl.contracts.agent import Message, ResponseFormat, TokenUsage
from veracrawl.contracts.enums import (
    MessageRole,
    ProviderFinishReason,
    ResponseFormatKind,
)
from veracrawl.contracts.errors import ReplayLookupMissError
from veracrawl.contracts.llm_input import ProviderRequest, ProviderResponse
from veracrawl.runtime_support.runtime_mode import RuntimeMode


def _canned_body() -> bytes:
    return json.dumps({
        "id": "resp_repl_test",
        "status": "completed",
        "output": [
            {"content": [{"type": "output_text", "text": "replay-hello"}]},
        ],
        "usage": {
            "input_tokens": 10, "output_tokens": 5, "total_tokens": 15,
        },
    }).encode()


def _request(request_id: str = "req:test:1") -> ProviderRequest:
    return ProviderRequest(
        id=request_id, run_ref="run:test:1", model_name="gpt-5",
        messages=[Message(role=MessageRole.USER, content="hi")],
        max_output_tokens=100, temperature=0.0,
        response_format=ResponseFormat(kind=ResponseFormatKind.TEXT),
    )


def _producer_response_and_store() -> tuple[ProviderResponse, InMemoryBytesArtifactStore]:
    store = InMemoryBytesArtifactStore()

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_canned_body())

    adapter = OpenAIResponsesAdapterV2(
        api_key="test-key",
        runtime_mode=RuntimeMode.FIXTURE,
        transport=httpx.MockTransport(handler),
        artifact_store=store,
    )
    response = adapter.complete(_request("req:producer:1"))
    return response, store


# Test 26a: real producer→consumer round-trip via raw_response_ref
def test_replaying_provider_v2_real_round_trip_via_raw_response_ref() -> None:
    response_a, store = _producer_response_and_store()
    assert response_a.raw_response_ref is not None

    replay = ReplayingModelProviderV2(
        canned={},
        canned_by_raw_ref={response_a.raw_response_ref: response_a},
        artifact_store=store,
    )

    # Different request.id — must not match canned; must fall through to
    # the raw_response_ref path (which proves the store actually has the bytes).
    out = replay.complete(_request("req:replay:elsewhere"))
    assert out.text == response_a.text
    assert out.raw_response_ref == response_a.raw_response_ref


# Test 26b: canned_by_raw_ref set but store empty → ReplayLookupMissError
def test_replaying_provider_v2_rejects_missing_raw_response_ref_when_keyed() -> None:
    empty_store = InMemoryBytesArtifactStore()
    response_a = ProviderResponse(
        id="resp:dangling", request_ref="req:1", text="x",
        usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        finish_reason=ProviderFinishReason.STOP,
        raw_response_ref="artifact:sha256:dangling",
    )

    replay = ReplayingModelProviderV2(
        canned={},
        canned_by_raw_ref={"artifact:sha256:dangling": response_a},
        artifact_store=empty_store,
    )

    with pytest.raises(ReplayLookupMissError):
        replay.complete(_request("req:any"))


# Test 26c: legacy ctor (canned-by-request-id only) still works
def test_replaying_provider_v2_artifact_store_optional_when_no_raw_ref_keying() -> None:
    response = ProviderResponse(
        id="resp:legacy", request_ref="req:legacy", text="legacy",
        usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        finish_reason=ProviderFinishReason.STOP,
        raw_response_ref="artifact:sha256:legacy",
    )
    # No artifact_store, no canned_by_raw_ref — legacy mode.
    replay = ReplayingModelProviderV2(canned={"req:legacy": response})
    out: Any = replay.complete(_request("req:legacy"))
    assert out is response
