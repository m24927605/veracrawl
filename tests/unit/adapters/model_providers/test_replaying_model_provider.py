"""Unit tests for ``ReplayingModelProviderV2`` (s2 step 3, tests 26-28)."""

from __future__ import annotations

import pytest

from veracrawl.adapters.model_providers.replaying_model_provider import (
    ReplayingModelProviderV2,
)
from veracrawl.contracts.agent import (
    Message,
    ResponseFormat,
    TokenUsage,
)
from veracrawl.contracts.enums import (
    MessageRole,
    ModelCapability,
    ProviderFinishReason,
    ResponseFormatKind,
)
from veracrawl.contracts.errors import ReplayLookupMissError
from veracrawl.contracts.llm_input import ProviderRequest, ProviderResponse
from veracrawl.ports.model_provider_v2 import ModelProviderPortV2


def _request(request_id: str = "provider-request:test:1") -> ProviderRequest:
    return ProviderRequest(
        id=request_id,
        run_ref="run:test:1",
        model_name="gpt-test",
        messages=[Message(role=MessageRole.USER, content="hi")],
        response_format=ResponseFormat(kind=ResponseFormatKind.JSON_OBJECT),
        max_output_tokens=64,
    )


def _canned(request_id: str = "provider-request:test:1") -> ProviderResponse:
    return ProviderResponse(
        id=f"provider-response:{request_id}",
        request_ref=request_id,
        text="canned",
        usage=TokenUsage(prompt_tokens=3, completion_tokens=2, total_tokens=5),
        finish_reason=ProviderFinishReason.STOP,
        parsed_output={"foo": "bar"},
        raw_response_ref=f"raw-response:{request_id}",
    )


# Test 26
def test_replaying_model_provider_returns_canned_response_keyed_by_request_id() -> None:
    canned = _canned()
    provider = ReplayingModelProviderV2({"provider-request:test:1": canned})
    assert provider.complete(_request()) is canned


# Test 27
def test_replaying_model_provider_raises_on_missing_key() -> None:
    provider = ReplayingModelProviderV2({})
    with pytest.raises(ReplayLookupMissError) as excinfo:
        provider.complete(_request("provider-request:test:missing"))
    assert excinfo.value.provider_request_id == "provider-request:test:missing"


# Test 28
def test_replaying_model_provider_implements_model_provider_port() -> None:
    provider = ReplayingModelProviderV2({})
    assert isinstance(provider, ModelProviderPortV2)
    # `supports` exists and returns a bool for every declared capability.
    assert isinstance(provider.supports(ModelCapability.STRUCTURED_OUTPUT_JSON_SCHEMA), bool)
