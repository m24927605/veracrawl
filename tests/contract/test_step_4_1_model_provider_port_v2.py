"""Contract tests for Phase 4 step 4.1.

Adds the provider-blind LLM call surface contracts:

* :class:`Anchor` — pure-data anchor for LLM grounding (no
  network coupling).
* :class:`ProviderRequest` — provider-blind request envelope.
* :class:`ProviderResponse` — validated response shape with
  required :class:`TokenUsage`.
* :class:`TokenUsageEstimate` — pre-flight estimate consumed by
  the Phase 4 step 4.5 token-budget port.
* :class:`ProviderFinishReason` — enum mapping provider-specific
  stop reasons to the v2 surface.
* :class:`ModelProviderPortV2` — runtime-checkable Protocol
  implemented by Phase 4 step 4.2 / 4.3 adapters.

The boundary invariants enforced here (per
``contracts/llm_input.py`` validators):

* identifier-shape validation (codex recurring concern #6) for
  ``id`` / ``run_ref`` / ``model_name`` / ``request_ref``;
* ``temperature`` finite and in [0.0, 2.0];
* ``max_output_tokens`` strictly positive;
* ``messages`` non-empty;
* anchor IDs unique within a request (no silent shadowing at
  citation time);
* ``ProviderResponse.usage`` required (no ``None`` token counts);
* ``ProviderResponse.text`` non-empty (and not whitespace-only)
  when ``finish_reason == STOP``; empty text is permitted for
  ``TOOL_CALL`` / ``CONTENT_FILTER`` / ``LENGTH`` / ``ERROR``
  per real-provider behavior;
* ``TokenUsageEstimate.cost_usd_estimate`` rejects non-finite
  values (NaN slips past naive ``< 0`` because NaN comparisons
  are always False) — the budget-enforcement field must always
  trip on overflow.
"""

from __future__ import annotations

import math

import pytest

from veracrawl.contracts.agent import Message, ResponseFormat, TokenUsage
from veracrawl.contracts.enums import (
    MessageRole,
    ModelCapability,
    ProviderFinishReason,
    ResponseFormatKind,
)
from veracrawl.contracts.llm_input import (
    Anchor,
    ProviderRequest,
    ProviderResponse,
    TokenUsageEstimate,
)
from veracrawl.contracts.registry import FOUNDATION_CONTRACTS
from veracrawl.ports.model_provider_v2 import ModelProviderPortV2


def _user_message(text: str = "extract product details") -> Message:
    return Message(role=MessageRole.USER, content=text)


def _text_response_format() -> ResponseFormat:
    return ResponseFormat(kind=ResponseFormatKind.TEXT)


def _make_request(**overrides: object) -> ProviderRequest:
    base: dict[str, object] = {
        "id": "provider-request:phase-4-1:1",
        "run_ref": "run:phase-4-1:1",
        "model_name": "gpt-4o-mini",
        "messages": [_user_message()],
        "response_format": _text_response_format(),
        "max_output_tokens": 256,
    }
    base.update(overrides)
    return ProviderRequest(**base)


def _make_usage(prompt: int = 100, completion: int = 50) -> TokenUsage:
    return TokenUsage(
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=prompt + completion,
    )


# --- Anchor -----------------------------------------------------------------


def test_anchor_round_trips_with_all_fields() -> None:
    anchor = Anchor(
        id="anchor:1",
        selector="div.product-title",
        excerpt="Widget Pro",
        screenshot_region_ref="region:phase-4-1:1",
    )
    assert anchor.id == "anchor:1"
    assert anchor.excerpt == "Widget Pro"


def test_anchor_rejects_blank_id() -> None:
    with pytest.raises(ValueError, match="anchor.id"):
        Anchor(id="   ", excerpt="content")


def test_anchor_rejects_blank_excerpt() -> None:
    with pytest.raises(ValueError, match="excerpt must be non-blank"):
        Anchor(id="anchor:1", excerpt="   ")


def test_anchor_rejects_blank_selector_when_present() -> None:
    with pytest.raises(ValueError, match="selector must be non-blank when present"):
        Anchor(id="anchor:1", selector="   ", excerpt="content")


def test_anchor_allows_omitted_selector() -> None:
    anchor = Anchor(id="anchor:1", excerpt="content")
    assert anchor.selector is None


# --- ProviderRequest --------------------------------------------------------


def test_provider_request_round_trips() -> None:
    request = _make_request()
    assert request.temperature == 0.0
    assert request.max_output_tokens == 256
    assert len(request.messages) == 1


def test_provider_request_rejects_blank_id() -> None:
    with pytest.raises(ValueError, match="provider request id"):
        _make_request(id="   ")


def test_provider_request_rejects_blank_run_ref() -> None:
    with pytest.raises(ValueError, match="provider request run_ref"):
        _make_request(run_ref="")


def test_provider_request_rejects_blank_model_name() -> None:
    with pytest.raises(ValueError, match="provider request model_name"):
        _make_request(model_name=" ")


def test_provider_request_rejects_zero_max_output_tokens() -> None:
    with pytest.raises(ValueError, match="max_output_tokens must be positive"):
        _make_request(max_output_tokens=0)


def test_provider_request_rejects_negative_max_output_tokens() -> None:
    with pytest.raises(ValueError, match="max_output_tokens must be positive"):
        _make_request(max_output_tokens=-1)


def test_provider_request_rejects_temperature_below_range() -> None:
    with pytest.raises(ValueError, match=r"temperature must be in \[0.0, 2.0\]"):
        _make_request(temperature=-0.5)


def test_provider_request_rejects_temperature_above_range() -> None:
    with pytest.raises(ValueError, match=r"temperature must be in \[0.0, 2.0\]"):
        _make_request(temperature=2.5)


def test_provider_request_accepts_temperature_at_bounds() -> None:
    assert _make_request(temperature=0.0).temperature == 0.0
    assert _make_request(temperature=2.0).temperature == 2.0


def test_provider_request_rejects_empty_messages() -> None:
    with pytest.raises(ValueError, match="at least one message"):
        _make_request(messages=[])


def test_provider_request_rejects_duplicate_anchor_ids() -> None:
    anchors = [
        Anchor(id="anchor:1", excerpt="first"),
        Anchor(id="anchor:1", excerpt="second"),
    ]
    with pytest.raises(ValueError, match="anchor IDs must be unique"):
        _make_request(anchors=anchors)


def test_provider_request_accepts_unique_anchor_ids() -> None:
    anchors = [
        Anchor(id="anchor:1", excerpt="first"),
        Anchor(id="anchor:2", excerpt="second"),
    ]
    request = _make_request(anchors=anchors)
    assert len(request.anchors) == 2


# --- ProviderResponse -------------------------------------------------------


def test_provider_response_round_trips() -> None:
    response = ProviderResponse(
        id="provider-response:1",
        request_ref="provider-request:phase-4-1:1",
        text="extracted",
        usage=_make_usage(),
        finish_reason=ProviderFinishReason.STOP,
    )
    assert response.text == "extracted"
    assert response.usage.total_tokens == 150
    assert response.parsed_output is None


def test_provider_response_rejects_blank_id() -> None:
    with pytest.raises(ValueError, match="provider response id"):
        ProviderResponse(
            id="   ",
            request_ref="provider-request:phase-4-1:1",
            text="extracted",
            usage=_make_usage(),
            finish_reason=ProviderFinishReason.STOP,
        )


def test_provider_response_rejects_blank_request_ref() -> None:
    with pytest.raises(ValueError, match="provider response request_ref"):
        ProviderResponse(
            id="provider-response:1",
            request_ref="",
            text="extracted",
            usage=_make_usage(),
            finish_reason=ProviderFinishReason.STOP,
        )


def test_provider_response_rejects_empty_text_when_finish_reason_is_stop() -> None:
    with pytest.raises(ValueError, match="text must be non-empty"):
        ProviderResponse(
            id="provider-response:1",
            request_ref="provider-request:phase-4-1:1",
            text="",
            usage=_make_usage(),
            finish_reason=ProviderFinishReason.STOP,
        )


def test_provider_response_rejects_whitespace_only_text_when_finish_reason_is_stop() -> (
    None
):
    """Codex iter-2 important: whitespace-only text on STOP is the
    same wiring bug as empty text — match the rest of the boundary
    that uses ``.strip()`` checks."""

    with pytest.raises(ValueError, match="text must be non-empty"):
        ProviderResponse(
            id="provider-response:1",
            request_ref="provider-request:phase-4-1:1",
            text="   \t\n",
            usage=_make_usage(),
            finish_reason=ProviderFinishReason.STOP,
        )


def test_provider_response_parsed_output_with_text_provenance_is_valid() -> None:
    response = ProviderResponse(
        id="provider-response:1",
        request_ref="provider-request:phase-4-1:1",
        text='{"sku": "ABC"}',
        usage=_make_usage(),
        finish_reason=ProviderFinishReason.STOP,
        parsed_output={"sku": "ABC"},
    )
    assert response.parsed_output == {"sku": "ABC"}


def test_provider_response_parsed_output_with_raw_ref_provenance_is_valid() -> None:
    """Codex iter-4 important: parsed_output is allowed with no
    text when ``raw_response_ref`` carries the audit-copy provenance.
    Plausible on TOOL_CALL where the model returned only a tool
    call but the structured output was reconstructed from the
    raw provider transcript."""

    response = ProviderResponse(
        id="provider-response:1",
        request_ref="provider-request:phase-4-1:1",
        text="",
        usage=_make_usage(),
        finish_reason=ProviderFinishReason.TOOL_CALL,
        parsed_output={"tool": "lookup"},
        raw_response_ref="artifact:provider-raw:1",
    )
    assert response.parsed_output == {"tool": "lookup"}


def test_provider_response_rejects_parsed_output_without_provenance() -> None:
    """Codex iter-4 important: parsed_output without text AND
    without raw_response_ref means the structured extraction
    has no provider transcript — replay can never reproduce
    it. Refuse at construction."""

    with pytest.raises(
        ValueError, match="parsed_output requires either non-blank text"
    ):
        ProviderResponse(
            id="provider-response:1",
            request_ref="provider-request:phase-4-1:1",
            text="",
            usage=_make_usage(),
            finish_reason=ProviderFinishReason.TOOL_CALL,
            parsed_output={"sku": "ABC"},
        )


def test_provider_response_rejects_parsed_output_with_blank_raw_ref() -> None:
    with pytest.raises(
        ValueError, match="parsed_output requires either non-blank text"
    ):
        ProviderResponse(
            id="provider-response:1",
            request_ref="provider-request:phase-4-1:1",
            text="",
            usage=_make_usage(),
            finish_reason=ProviderFinishReason.TOOL_CALL,
            parsed_output={"sku": "ABC"},
            raw_response_ref="   ",
        )


@pytest.mark.parametrize(
    "blocked_reason",
    [
        ProviderFinishReason.CONTENT_FILTER,
        ProviderFinishReason.ERROR,
        ProviderFinishReason.LENGTH,
    ],
)
def test_provider_response_rejects_parsed_output_for_blocked_finish_reasons(
    blocked_reason: ProviderFinishReason,
) -> None:
    """Codex iter-4 + iter-5 important: ``CONTENT_FILTER``
    (provider blocked generation), ``ERROR`` (pre-generation
    failure), and ``LENGTH`` (truncated generation — partial
    JSON can validate against schemas with optional fields and
    silently look like a complete extraction) are all states
    where structured output is not meaningful. Refuse
    ``parsed_output`` structurally so an adapter cannot claim
    a successful extraction in any of these cases."""

    with pytest.raises(
        ValueError, match="parsed_output is not meaningful when finish_reason"
    ):
        ProviderResponse(
            id="provider-response:1",
            request_ref="provider-request:phase-4-1:1",
            text="",
            usage=_make_usage(),
            finish_reason=blocked_reason,
            parsed_output={"sku": "ABC"},
            raw_response_ref="artifact:provider-raw:1",
        )


@pytest.mark.parametrize(
    "finish_reason",
    [
        ProviderFinishReason.TOOL_CALL,
        ProviderFinishReason.CONTENT_FILTER,
        ProviderFinishReason.LENGTH,
        ProviderFinishReason.ERROR,
    ],
)
def test_provider_response_allows_empty_text_for_non_stop_finish_reasons(
    finish_reason: ProviderFinishReason,
) -> None:
    """Codex iter-2 important: real providers can return no
    output for ``CONTENT_FILTER`` (blocked content), ``LENGTH``
    (max tokens reached before any text), ``ERROR`` (pre-
    generation failure surfaced at the response layer), and
    ``TOOL_CALL`` (model returned only a tool call). Forcing
    text on these reasons would push adapters to fabricate it
    or fail to construct a typed response."""

    response = ProviderResponse(
        id="provider-response:1",
        request_ref="provider-request:phase-4-1:1",
        text="",
        usage=_make_usage(),
        finish_reason=finish_reason,
    )
    assert response.text == ""
    assert response.finish_reason is finish_reason


def test_provider_response_requires_usage() -> None:
    # mypy/Pydantic both refuse to construct without usage.
    with pytest.raises((ValueError, TypeError)):
        ProviderResponse(  # type: ignore[call-arg]
            id="provider-response:1",
            request_ref="provider-request:phase-4-1:1",
            text="extracted",
            finish_reason=ProviderFinishReason.STOP,
        )


# --- TokenUsageEstimate -----------------------------------------------------


def test_token_usage_estimate_round_trips() -> None:
    estimate = TokenUsageEstimate(
        request_ref="provider-request:phase-4-1:1",
        model_name="gpt-4o-mini",
        prompt_tokens_estimate=100,
        completion_tokens_estimate=50,
        cost_usd_estimate=0.0015,
    )
    assert estimate.cost_usd_estimate == 0.0015


def test_token_usage_estimate_rejects_blank_request_ref() -> None:
    with pytest.raises(ValueError, match="request_ref"):
        TokenUsageEstimate(
            request_ref="",
            model_name="gpt-4o-mini",
            prompt_tokens_estimate=100,
            completion_tokens_estimate=50,
            cost_usd_estimate=0.0015,
        )


def test_token_usage_estimate_rejects_negative_tokens() -> None:
    with pytest.raises(ValueError, match="prompt_tokens_estimate"):
        TokenUsageEstimate(
            request_ref="provider-request:phase-4-1:1",
            model_name="gpt-4o-mini",
            prompt_tokens_estimate=-1,
            completion_tokens_estimate=50,
            cost_usd_estimate=0.0015,
        )


def test_token_usage_estimate_rejects_negative_cost() -> None:
    with pytest.raises(ValueError, match="cost_usd_estimate"):
        TokenUsageEstimate(
            request_ref="provider-request:phase-4-1:1",
            model_name="gpt-4o-mini",
            prompt_tokens_estimate=100,
            completion_tokens_estimate=50,
            cost_usd_estimate=-0.01,
        )


@pytest.mark.parametrize("bad_cost", [float("nan"), float("inf"), float("-inf")])
def test_token_usage_estimate_rejects_non_finite_cost(bad_cost: float) -> None:
    """Codex iter-3 important: NaN slips past ``< 0`` because
    NaN comparisons are always False. The cost cap is the
    budget-enforcement field — non-finite values must be
    rejected so the cap can never silently fail to trip."""

    with pytest.raises(ValueError, match="cost_usd_estimate must be a finite number"):
        TokenUsageEstimate(
            request_ref="provider-request:phase-4-1:1",
            model_name="gpt-4o-mini",
            prompt_tokens_estimate=100,
            completion_tokens_estimate=50,
            cost_usd_estimate=bad_cost,
        )


@pytest.mark.parametrize("bad_temp", [float("nan"), float("inf"), float("-inf")])
def test_provider_request_rejects_non_finite_temperature(bad_temp: float) -> None:
    """Companion to the NaN check on cost_usd_estimate: any
    non-finite temperature is also a wiring bug (real APIs
    reject it; replay determinism breaks)."""

    with pytest.raises(ValueError, match="temperature must be a finite number"):
        _make_request(temperature=bad_temp)
    # Sanity: ensures the parametrize value is actually non-finite.
    assert not math.isfinite(bad_temp)


# --- Port -------------------------------------------------------------------


def test_model_provider_port_v2_is_runtime_checkable() -> None:
    class _StubAdapter:
        def complete(self, request: ProviderRequest) -> ProviderResponse:
            return ProviderResponse(
                id="provider-response:1",
                request_ref=request.id,
                text="stub",
                usage=_make_usage(),
                finish_reason=ProviderFinishReason.STOP,
            )

        def supports(self, capability: ModelCapability) -> bool:
            return capability is ModelCapability.STRUCTURED_OUTPUT_JSON_SCHEMA

    adapter = _StubAdapter()
    assert isinstance(adapter, ModelProviderPortV2)
    assert adapter.supports(ModelCapability.STRUCTURED_OUTPUT_JSON_SCHEMA) is True
    assert adapter.supports(ModelCapability.VISION) is False


def test_model_provider_port_v2_rejects_missing_complete() -> None:
    class _MissingComplete:
        def supports(self, capability: ModelCapability) -> bool:
            del capability
            return False

    assert not isinstance(_MissingComplete(), ModelProviderPortV2)


def test_model_provider_port_v2_rejects_missing_supports() -> None:
    """Codex iter-5 important: ``supports`` is part of the
    Phase 4 v2 contract (design.md §6 risk-mitigation —
    capability negotiation lets the runtime route around
    adapters that lack a feature instead of hard-failing).
    A class implementing only ``complete`` is not the v2
    contract."""

    class _MissingSupports:
        def complete(self, request: ProviderRequest) -> ProviderResponse:
            del request
            raise NotImplementedError

    assert not isinstance(_MissingSupports(), ModelProviderPortV2)


def test_model_capability_enum_exposed_at_package_root() -> None:
    import veracrawl.contracts as contracts_pkg

    assert hasattr(contracts_pkg, "ModelCapability")
    assert "ModelCapability" in contracts_pkg.__all__


# --- Foundation registry ----------------------------------------------------


def test_phase_4_1_contracts_registered() -> None:
    for name in ("Anchor", "ProviderRequest", "ProviderResponse", "TokenUsageEstimate"):
        assert name in FOUNDATION_CONTRACTS, (
            f"{name} must be registered in FOUNDATION_CONTRACTS"
        )
        registration = FOUNDATION_CONTRACTS[name]
        assert registration.python_model == f"veracrawl.contracts.llm_input.{name}"


def test_provider_finish_reason_exposed_on_enums_module() -> None:
    # Sanity: enum is importable from the canonical enums module.
    from veracrawl.contracts import enums as enums_module

    assert hasattr(enums_module, "ProviderFinishReason")
    assert enums_module.ProviderFinishReason.STOP is ProviderFinishReason.STOP


def test_phase_4_1_contracts_and_enum_exposed_at_package_root() -> None:
    """Codex iter-1 important: foundation contracts must be
    importable from ``veracrawl.contracts`` (the project's
    public surface), not only from their submodule."""

    import veracrawl.contracts as contracts_pkg

    for name in (
        "Anchor",
        "ProviderRequest",
        "ProviderResponse",
        "TokenUsageEstimate",
        "ProviderFinishReason",
    ):
        assert hasattr(contracts_pkg, name), (
            f"{name} must be re-exported from veracrawl.contracts"
        )
        assert name in contracts_pkg.__all__, (
            f"{name} must appear in veracrawl.contracts.__all__"
        )
