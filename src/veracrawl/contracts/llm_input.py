"""Phase 4 LLM provider port v2 — request/response/anchor contracts.

These shapes live in their own module to keep LLM-specific surface
out of ``contracts/agent.py`` (which already carries Phase 0
v2 contracts: ``Message``, ``ResponseFormat``, ``ToolSpec``,
``TokenUsage``, ``LLMExtractionCandidate`` etc.). The
``ModelProviderPortV2`` (``ports/model_provider_v2.py``) consumes
``ProviderRequest`` and returns ``ProviderResponse``; adapters
(``OpenAIResponsesAdapter`` v2, ``AnthropicMessagesAdapter``)
implement the call path against real provider HTTP shapes.

Boundary invariants (enforced at construction here, not deferred
to the call site):

* All identifier-shaped fields (``id``, ``run_ref``, ``model_name``)
  reject blank / whitespace-only inputs (codex recurring concern
  #6: identifier-shape validation).
* ``temperature`` is bounded to ``[0.0, 2.0]``; production runs
  always default to 0.0 for replay determinism.
* ``max_output_tokens`` must be positive; an unbounded request is
  almost always a wiring bug (no per-run cost cap).
* ``messages`` must be non-empty; an empty conversation is also
  always a wiring bug.
* ``Anchor.excerpt`` rejects blank / whitespace-only — empty
  anchors waste tokens and never ground a citation.
* ``ProviderResponse.usage`` is required; adapters must populate
  ``TokenUsage`` from provider response headers / body before
  constructing the response. ``None`` would let token-budget
  audits silently drift.
"""

from __future__ import annotations

import math
from typing import Any

from pydantic import Field, model_validator

from veracrawl.contracts.agent import (
    Message,
    ResponseFormat,
    TokenUsage,
    ToolCall,
    ToolSpec,
)
from veracrawl.contracts.common import Ref, VeraModel
from veracrawl.contracts.enums import ProviderFinishReason


def _ensure_non_blank_identifier(name: str, value: str) -> None:
    """Codex recurring concern #6 (identifier-shape validation).

    Raised at construction time so a wiring bug surfaces before
    the request reaches a provider HTTP call (where the LLM might
    silently accept blank inputs and burn tokens).
    """

    if not value or not value.strip():
        raise ValueError(f"{name} must be a non-blank identifier")


class Anchor(VeraModel):
    """Pure-data anchor for LLM grounding.

    The LLM uses anchors as evidence for ``LLMFieldCitation`` —
    each citation references one or more anchor IDs. ``selector``
    is an optional CSS / XPath; ``screenshot_region_ref`` ties
    the anchor to a bounding box on the page screenshot when
    Phase 1 supplied one. ``excerpt`` is the text snippet the LLM
    grounds on; it is non-blank by construction.

    Living in ``contracts/llm_input.py`` (not ``contracts/network.py``
    or ``contracts/evidence.py``) keeps the LLM layer decoupled
    from the network attempt-evidence shape — the call site (Phase
    4 step 4.6 ``schema_runtime``) builds ``Anchor`` from
    ``NetworkAttemptEvidence``.
    """

    id: str
    selector: str | None = None
    excerpt: str
    screenshot_region_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_anchor(self) -> Anchor:
        _ensure_non_blank_identifier("anchor.id", self.id)
        if not self.excerpt or not self.excerpt.strip():
            raise ValueError("anchor excerpt must be non-blank")
        if self.selector is not None and not self.selector.strip():
            raise ValueError(
                "anchor selector must be non-blank when present (use None to omit)"
            )
        return self


class ProviderRequest(VeraModel):
    """Provider-blind LLM call envelope.

    The orchestrator builds a ``ProviderRequest``, hands it to
    ``ModelProviderPortV2.complete``; the adapter (OpenAI /
    Anthropic) translates the request to provider HTTP shape,
    issues the call, and returns a ``ProviderResponse``.

    The redaction boundary (Phase 2 step 2.3
    ``RedactedPromptContext``) ran before construction; any
    rendered ``messages[].content`` containing a
    ``CredentialValue`` would have raised
    ``PromptCredentialLeakError`` before reaching this model.
    Adapters must not log raw ``messages`` content.
    """

    id: str
    run_ref: Ref
    model_name: str
    messages: list[Message]
    tools: list[ToolSpec] = Field(default_factory=list)
    response_format: ResponseFormat
    max_output_tokens: int
    temperature: float = 0.0
    anchors: list[Anchor] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_request(self) -> ProviderRequest:
        _ensure_non_blank_identifier("provider request id", self.id)
        _ensure_non_blank_identifier("provider request run_ref", self.run_ref)
        _ensure_non_blank_identifier("provider request model_name", self.model_name)
        if self.max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be positive")
        if not math.isfinite(self.temperature):
            raise ValueError("temperature must be a finite number")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be in [0.0, 2.0]")
        if not self.messages:
            raise ValueError("provider request requires at least one message")
        # Anchor IDs must be unique within a request — duplicate
        # IDs would silently shadow earlier anchors at citation time.
        anchor_ids = [anchor.id for anchor in self.anchors]
        if len(anchor_ids) != len(set(anchor_ids)):
            raise ValueError("anchor IDs must be unique within a provider request")
        return self


class ProviderResponse(VeraModel):
    """Result of a single ``ModelProviderPortV2.complete`` call.

    ``parsed_output`` is populated when
    ``request.response_format.kind == JSON_SCHEMA`` AND the
    adapter successfully validated the response payload against
    the schema; otherwise it is ``None`` (and the caller works
    off ``text`` directly). ``raw_response_ref`` is an opaque
    audit ref pointing to a durable copy of the provider's raw
    response body (Phase 6 ships the artifact-store wiring; Phase
    4 fixture mode uses ``None``).
    """

    id: str
    request_ref: Ref
    text: str
    usage: TokenUsage
    finish_reason: ProviderFinishReason
    parsed_output: dict[str, Any] | None = None
    raw_response_ref: Ref | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_response(self) -> ProviderResponse:
        _ensure_non_blank_identifier("provider response id", self.id)
        _ensure_non_blank_identifier(
            "provider response request_ref", self.request_ref
        )
        # Successful text-bearing completions (``STOP``) require
        # non-empty, non-whitespace-only text — empty text on
        # ``STOP`` is a wiring bug. Other finish reasons may
        # legitimately have empty text:
        # * ``TOOL_CALL`` — the model returned only a tool call.
        # * ``CONTENT_FILTER`` — provider blocked generation.
        # * ``LENGTH`` — max tokens reached before any text emitted
        #   (rare but possible with very small caps).
        # * ``ERROR`` — pre-generation error returned at the
        #   response layer (adapters typically ``raise`` for these
        #   per the port's raise-vs-return policy, but a defensive
        #   adapter may return one).
        # Whitespace-only text on ``STOP`` is also refused so the
        # boundary stays consistent with anchor excerpt /
        # identifier validators that ``.strip()``-check.
        if (
            self.finish_reason is ProviderFinishReason.STOP
            and not self.text.strip()
        ):
            raise ValueError(
                "provider response text must be non-empty (and not "
                "whitespace-only) when finish_reason is STOP"
            )
        # ``parsed_output`` must always be backed by provenance
        # (codex iter-4 important): otherwise the audit boundary
        # would accept "structured output succeeded" with no
        # provider transcript and no durable raw-response ref,
        # which Phase 6 replay can never reproduce. Provenance =
        # non-blank ``text`` (the model wrote it down) OR a
        # non-blank ``raw_response_ref`` (durable audit copy of
        # the wire response). Also: ``parsed_output`` is not
        # meaningful for ``CONTENT_FILTER`` (provider blocked
        # generation) or ``ERROR`` (pre-generation failure) —
        # rejecting these structurally prevents an adapter from
        # claiming a successful structured extraction on a
        # blocked / errored response.
        if self.tool_calls:
            # tool_calls + non-TOOL_CALL finish_reason is a
            # contract violation: the adapter would have
            # silently lost the model's tool selection if the
            # finish reason said something else.
            if self.finish_reason is not ProviderFinishReason.TOOL_CALL:
                raise ValueError(
                    f"tool_calls populated but finish_reason is "
                    f"{self.finish_reason.value!r}; expected TOOL_CALL"
                )
            # tool_call ids must be unique within a response.
            ids = [tc.id for tc in self.tool_calls]
            if len(ids) != len(set(ids)):
                raise ValueError("tool_calls ids must be unique within a response")
        if self.parsed_output is not None:
            # ``LENGTH`` (truncated generation) is also refused
            # for ``parsed_output`` (codex iter-5 important):
            # partial JSON can validate against schemas with
            # optional fields and silently look like a complete
            # extraction. Forcing the partial-output case to
            # surface as ``parsed_output=None`` makes the
            # downstream extraction pipeline retry / abstain
            # instead of accepting a truncated value.
            if self.finish_reason in {
                ProviderFinishReason.CONTENT_FILTER,
                ProviderFinishReason.ERROR,
                ProviderFinishReason.LENGTH,
            }:
                raise ValueError(
                    f"parsed_output is not meaningful when finish_reason "
                    f"is {self.finish_reason.value}"
                )
            has_text_provenance = bool(self.text.strip())
            has_raw_provenance = (
                self.raw_response_ref is not None
                and bool(self.raw_response_ref.strip())
            )
            if not has_text_provenance and not has_raw_provenance:
                raise ValueError(
                    "parsed_output requires either non-blank text or a "
                    "non-blank raw_response_ref as provenance"
                )
        return self


class TokenUsageEstimate(VeraModel):
    """Pre-flight estimate for a ``ProviderRequest`` (Phase 4 step 4.5).

    The token-budget port consumes this to decide whether to
    refuse the call before issuing it. Estimates are
    provider-specific (tiktoken-equivalent for OpenAI,
    Anthropic-tokenizer for Anthropic); both ship as fixture-mode
    stubs in Phase 4 — accurate tokenizers wired in Phase 6 step
    6.1.
    """

    request_ref: Ref
    model_name: str
    prompt_tokens_estimate: int
    completion_tokens_estimate: int
    cost_usd_estimate: float

    @model_validator(mode="after")
    def validate_estimate(self) -> TokenUsageEstimate:
        _ensure_non_blank_identifier(
            "token usage estimate request_ref", self.request_ref
        )
        _ensure_non_blank_identifier(
            "token usage estimate model_name", self.model_name
        )
        for name, value in (
            ("prompt_tokens_estimate", self.prompt_tokens_estimate),
            ("completion_tokens_estimate", self.completion_tokens_estimate),
        ):
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        # ``cost_usd_estimate`` is the budget-enforcement field —
        # NaN passes ``< 0`` (NaN comparisons are always False) and
        # would let a cost cap silently never trip. Reject all
        # non-finite values (codex iter-3 important).
        if not math.isfinite(self.cost_usd_estimate):
            raise ValueError("cost_usd_estimate must be a finite number")
        if self.cost_usd_estimate < 0:
            raise ValueError("cost_usd_estimate must be non-negative")
        return self


__all__ = [
    "Anchor",
    "ProviderRequest",
    "ProviderResponse",
    "TokenUsageEstimate",
]
