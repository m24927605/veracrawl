"""Unit tests for ``ReplayingModelProviderV2`` (s2 step 3, tests 26-28c)."""

from __future__ import annotations

import pytest

from veracrawl.adapters.model_providers.replaying_model_provider import (
    ReplayingModelProviderV2,
)
from veracrawl.contracts.agent import Message, ResponseFormat, TokenUsage, ToolCall
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
        id=request_id, run_ref="run:test:1", model_name="gpt-test",
        messages=[Message(role=MessageRole.USER, content="hi")],
        response_format=ResponseFormat(kind=ResponseFormatKind.JSON_OBJECT),
        max_output_tokens=64,
    )


def _canned(request_id: str = "provider-request:test:1") -> ProviderResponse:
    return ProviderResponse(
        id=f"provider-response:{request_id}", request_ref=request_id, text="canned",
        usage=TokenUsage(prompt_tokens=3, completion_tokens=2, total_tokens=5),
        finish_reason=ProviderFinishReason.STOP, parsed_output={"foo": "bar"},
        raw_response_ref=f"raw-response:{request_id}",
    )


def test_replaying_model_provider_returns_canned_response_keyed_by_request_id() -> None:
    canned = _canned()
    provider = ReplayingModelProviderV2({"provider-request:test:1": canned})
    assert provider.complete(_request()) is canned


def test_replaying_model_provider_raises_on_missing_key() -> None:
    provider = ReplayingModelProviderV2({})
    with pytest.raises(ReplayLookupMissError) as excinfo:
        provider.complete(_request("provider-request:test:missing"))
    assert excinfo.value.provider_request_id == "provider-request:test:missing"


def test_replaying_model_provider_implements_model_provider_port() -> None:
    assert isinstance(ReplayingModelProviderV2({}), ModelProviderPortV2)


def test_supports_structured_output_iff_any_canned_has_parsed_output() -> None:
    cap = ModelCapability.STRUCTURED_OUTPUT_JSON_SCHEMA
    assert ReplayingModelProviderV2({}).supports(cap) is False
    text_only = _canned().model_copy(update={"parsed_output": None})
    assert ReplayingModelProviderV2({"req-x": text_only}).supports(cap) is False
    assert ReplayingModelProviderV2({"req-y": _canned()}).supports(cap) is True


def test_supports_tool_calls_iff_any_canned_has_tool_calls() -> None:
    no_tools = ReplayingModelProviderV2({"req-x": _canned()})
    assert no_tools.supports(ModelCapability.TOOL_CALLS) is False
    with_tools = _canned().model_copy(
        update={"tool_calls": [ToolCall(id="tc-1", name="fn", arguments={})]}
    )
    p = ReplayingModelProviderV2({"req-y": with_tools})
    assert p.supports(ModelCapability.TOOL_CALLS) is True


def test_supports_vision_and_extended_thinking_default_false() -> None:
    p = ReplayingModelProviderV2({"req-x": _canned()})
    assert p.supports(ModelCapability.VISION) is False
    assert p.supports(ModelCapability.EXTENDED_THINKING) is False
