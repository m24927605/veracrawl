"""Phase 4 step 4.1 — provider-blind LLM call surface.

Adapters implement this port against OpenAI Responses, Anthropic
Messages, etc. (Phase 4 step 4.2 / 4.3). The orchestrator picks
the adapter via config; the call site is provider-agnostic.

This is the v2 surface — it replaces the single-adapter v1
``OpenAIResponsesModelProviderRuntimeAdapter`` (still operational
during the deprecation window). The port shape:

* Takes a Pydantic-validated :class:`ProviderRequest` (the
  redaction boundary from Phase 2 step 2.3 ran before construction).
* Returns a Pydantic-validated :class:`ProviderResponse` whose
  ``usage`` is always populated (no ``None`` token counts can
  silently drift past the budget audit).
* Adapter implementations are responsible for:
  - Mapping provider-specific HTTP shapes to the port shape.
  - Validating structured-output responses against
    ``request.response_format.json_schema`` when
    ``response_format.kind == JSON_SCHEMA``; mismatches raise
    :class:`StructuredOutputViolation`.
  - Mapping provider-specific finish reasons to
    :class:`ProviderFinishReason`.
  - Raising the typed retryable / fatal hierarchy from
    ``contracts/errors`` for HTTP failures.

Boundary invariants (these are the adapter contract, not
port-level enforceable Python — listed here so future adapter
authors see the full surface):

1. **Credential leak**: Phase 2 step 2.3 boundary already
   refused any rendered ``messages[].content`` carrying a
   ``CredentialValue``; the adapter must not re-introduce one
   via header injection that the structured-log would capture.
   Adapter logs sanitized identifiers only (``id``,
   ``model_name``, ``run_ref``, ``usage``).
2. **Replay determinism**: For the same
   ``(request, model_name, temperature=0.0)`` triple, fixture-
   mode adapters MUST be byte-identical. Live adapters honor
   ``temperature=0.0`` only as a best-effort (provider-side
   stochasticity) — replay is on the recorded
   ``(request, response)`` pair, not the live API call.
3. **Production gate**: Adapter ``_production_call`` raises
   :class:`ProductionRuntimeNotImplemented` until Phase 6 step
   6.1 wires the production deployment.

Port is ``@runtime_checkable`` per the project's port
convention (data contracts go in ``FOUNDATION_CONTRACTS``;
ports are typed Protocols with ``isinstance`` discoverability
via ``@runtime_checkable``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from veracrawl.contracts.enums import ModelCapability
from veracrawl.contracts.llm_input import ProviderRequest, ProviderResponse


@runtime_checkable
class ModelProviderPortV2(Protocol):
    """Provider-blind LLM call surface (Phase 4)."""

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        """Issue the LLM call and return a validated response.

        Implementations must:

        * Translate ``request`` to the provider HTTP shape.
        * Issue the call honoring ``request.max_output_tokens`` /
          ``request.temperature`` / ``request.response_format``.
        * Populate :class:`TokenUsage` from the provider's usage
          counters before constructing the response. Never
          return a response with ``usage=None``.
        * Validate :class:`StructuredOutputViolation` for
          ``response_format.kind == JSON_SCHEMA`` mismatches.
        * Map provider stop reasons to :class:`ProviderFinishReason`.
        * Surface HTTP failures via the typed retryable / fatal
          hierarchy (do not return error responses; raise instead).
        """

        ...

    def supports(self, capability: ModelCapability) -> bool:
        """Capability negotiation hook (``design.md`` §6).

        The agent runtime calls ``supports`` before routing work
        that requires a particular capability (structured output,
        tool calls, vision, extended thinking). Adapters that
        lack the capability return ``False`` and the runtime
        selects a different provider rather than hard-failing
        the call.

        Implementations must return ``True`` only for
        capabilities they actually implement and have validated.
        Returning ``True`` for a feature the adapter does not
        exercise correctly is a contract violation — the
        orchestrator will route work to the adapter on the
        strength of that flag.
        """

        ...


__all__ = ["ModelProviderPortV2"]
