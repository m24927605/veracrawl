"""Phase 4 step 4.5 — durable token-usage event contract.

A ``TokenUsageEvent`` is the per-call durable record that
``OutboxBackedBudget`` persists via ``OutboxRepositoryPort``
on every ``charge``. Phase 5 step 5.1's recovery layer will
read the outbox topic ``token-usage`` to reconstruct the
canonical run cost without trusting the adapter's in-memory
counter.
"""

from __future__ import annotations

import math

from pydantic import model_validator

from veracrawl.contracts.agent import TokenUsage
from veracrawl.contracts.common import Ref, TimestampedModel


def _ensure_non_blank_identifier(name: str, value: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} must be a non-blank identifier")


class TokenUsageEvent(TimestampedModel):
    """Durable record of one ``ModelProviderPortV2.complete``
    call's token consumption, persisted to the outbox.

    Fields:

    * ``id`` — opaque event id (``token-usage:{uuid}``).
    * ``run_ref`` — the run this charge belongs to.
    * ``request_ref`` — the ``ProviderRequest.id`` that
      produced this usage. ``request_ref`` + ``run_ref``
      together let Phase 5 / 6 reconcile a use record with
      the LLM-call trace.
    * ``model_name`` — pinned at the moment of the call (price
      tables move; the model name is the joinable key).
    * ``usage`` — the Phase 0 ``TokenUsage`` record.
    * ``cost_usd`` — computed from the provider price table
      at charge time (price-table version is pinned in the
      event for replay determinism).
    * ``price_table_version`` — version of the table consulted.
    """

    id: str
    run_ref: Ref
    request_ref: Ref
    model_name: str
    usage: TokenUsage
    cost_usd: float
    price_table_version: str

    @model_validator(mode="after")
    def validate_event(self) -> TokenUsageEvent:
        _ensure_non_blank_identifier("token usage event id", self.id)
        _ensure_non_blank_identifier("run_ref", self.run_ref)
        _ensure_non_blank_identifier("request_ref", self.request_ref)
        _ensure_non_blank_identifier("model_name", self.model_name)
        _ensure_non_blank_identifier(
            "price_table_version", self.price_table_version
        )
        if not math.isfinite(self.cost_usd):
            raise ValueError("cost_usd must be a finite number")
        if self.cost_usd < 0:
            raise ValueError("cost_usd must be non-negative")
        return self


__all__ = ["TokenUsageEvent"]
