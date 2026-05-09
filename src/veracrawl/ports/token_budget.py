"""Phase 4 step 4.5 — token-budget enforcement port.

The orchestrator drives ``estimate_charge`` before calling the
provider (refuse early if the estimate alone would exceed
remaining budget) and ``charge`` after the provider returns
(record actual usage; raise ``TokenBudgetExceeded`` if the
cumulative total now breaches the cap).

Two-phase contract:

* ``estimate_charge(request) -> TokenUsageEstimate``: a
  pre-flight check the orchestrator can use to short-circuit
  obviously-doomed calls. Estimates are provider-specific
  (tiktoken-equivalent for OpenAI, anthropic-tokenizer for
  Anthropic). Phase 4 ships fixture-mode stubs; real
  tokenizers wired in Phase 6 step 6.1. ``estimate_charge``
  raises ``TokenBudgetExceeded`` when the estimate alone
  would breach the cap so the call never reaches
  ``ModelProviderPortV2.complete``.

* ``charge(usage, request_ref)``: post-call accounting.
  Persists a durable ``TokenUsageEvent`` via
  ``OutboxRepositoryPort`` (``dispatch_topic="token-usage"``)
  BEFORE updating the in-memory advisory total — same
  durable-audit-authoritative policy as Phase 2 step 2.5b
  ``CredentialUseRecord``. Raises ``TokenBudgetExceeded``
  AFTER the durable persist if the new total breaches the
  cap, so replay can reconstruct the breach moment.

Boundary invariants:

* ``estimate_charge`` and ``charge`` MUST be safe to call
  from concurrent requests on the same run (the adapter
  serialises critical sections internally).
* The advisory in-memory counter is best-effort; the durable
  outbox is the source of truth (Phase 5 step 5.1 will
  derive the counter from the outbox by construction,
  removing the divergence-prone parallel state — same
  resolution as the credential-use lifecycle counter).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from veracrawl.contracts.agent import TokenUsage
from veracrawl.contracts.common import Ref
from veracrawl.contracts.llm_input import ProviderRequest, TokenUsageEstimate


@runtime_checkable
class TokenBudgetPort(Protocol):
    """Per-run token-budget enforcement."""

    def estimate_charge(self, request: ProviderRequest) -> TokenUsageEstimate:
        """Pre-flight estimate. Raises ``TokenBudgetExceeded``
        when the estimate alone would breach the run cap."""

        ...

    def charge(self, usage: TokenUsage, *, request_ref: Ref) -> None:
        """Post-call charge. Persists a durable usage event,
        then updates the advisory in-memory total. Raises
        ``TokenBudgetExceeded`` AFTER the durable persist if
        the cumulative total breaches the cap."""

        ...


__all__ = ["TokenBudgetPort"]
