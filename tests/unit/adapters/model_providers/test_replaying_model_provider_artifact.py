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


# s2.1 R1 — deterministic request→raw_response_ref resolution
def test_replay_request_overrides_routes_request_to_specific_ref() -> None:
    """With a multi-entry ``canned_by_raw_ref`` bundle, the override
    maps each request id to the exact raw_response_ref that should
    answer it. Insertion-order fallback no longer applies.
    """

    store = InMemoryBytesArtifactStore()
    ref_a = store.write(b"bytes-a")
    ref_b = store.write(b"bytes-b")
    response_a = ProviderResponse(
        id="resp:a", request_ref="req:a", text="A",
        usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        finish_reason=ProviderFinishReason.STOP,
        raw_response_ref=ref_a,
    )
    response_b = ProviderResponse(
        id="resp:b", request_ref="req:b", text="B",
        usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        finish_reason=ProviderFinishReason.STOP,
        raw_response_ref=ref_b,
    )
    replay = ReplayingModelProviderV2(
        canned={},
        canned_by_raw_ref={ref_a: response_a, ref_b: response_b},
        artifact_store=store,
        replay_request_overrides={
            "req:from-bundle:1": ref_b,
            "req:from-bundle:2": ref_a,
        },
    )
    # Each request lands on the canned response named in the override
    # — NOT in dict-insertion order.
    out_1 = replay.complete(_request("req:from-bundle:1"))
    out_2 = replay.complete(_request("req:from-bundle:2"))
    assert out_1.text == "B"
    assert out_2.text == "A"


def test_replay_request_overrides_rejects_missing_ref_in_bundle() -> None:
    """If the override points at a ref not present in
    ``canned_by_raw_ref``, the lookup must fail (rather than fall
    back to insertion order — that would mask a bundle-assembly bug).
    """

    store = InMemoryBytesArtifactStore()
    ref_a = store.write(b"only-a")
    response_a = ProviderResponse(
        id="resp:a", request_ref="req:a", text="A",
        usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        finish_reason=ProviderFinishReason.STOP,
        raw_response_ref=ref_a,
    )
    replay = ReplayingModelProviderV2(
        canned={},
        canned_by_raw_ref={ref_a: response_a},
        artifact_store=store,
        replay_request_overrides={
            "req:dangling": "artifact:sha256:not-in-bundle",
        },
    )
    with pytest.raises(ReplayLookupMissError):
        replay.complete(_request("req:dangling"))


def test_replay_request_overrides_falls_back_to_insertion_order_for_unmapped_requests() -> None:
    """When the override mapping doesn't include a request, the
    existing insertion-order fallback still works (backward-compat
    with the s2.1 step-4 single-entry round-trip test).
    """

    store = InMemoryBytesArtifactStore()
    ref_a = store.write(b"single-entry")
    response_a = ProviderResponse(
        id="resp:a", request_ref="req:a", text="A",
        usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        finish_reason=ProviderFinishReason.STOP,
        raw_response_ref=ref_a,
    )
    replay = ReplayingModelProviderV2(
        canned={},
        canned_by_raw_ref={ref_a: response_a},
        artifact_store=store,
        # Override mapping is non-empty but doesn't include the
        # request being made.
        replay_request_overrides={"req:elsewhere": ref_a},
    )
    # request id 'req:other' is unmapped → fall back to insertion
    # order; single-entry bundle → response_a returned.
    out = replay.complete(_request("req:other"))
    assert out is response_a
