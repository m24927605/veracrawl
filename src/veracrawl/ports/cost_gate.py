"""Phase 5 step 5.2 — composable cost gate.

The agent runtime composes a per-run + per-objective +
per-host cost gate; ``CostGatePort.check`` runs before any
provider call, ``CostGatePort.charge`` runs after. Repeated-
failure-signature detection sits inside the gate so the
recovery loop can ask "should I keep trying this exact
failure shape?" without re-implementing the counter.

Boundary invariants:

* ``check`` raises ``CostGateExceeded`` (with ``failed_cap``
  identifying the tightest tripped cap) if any composed cap
  is breached. Raises ``RepeatedFailureSignatureExceeded``
  if a non-None ``failure_signature`` has been seen N=2+
  times for the same objective.
* ``charge`` accumulates against all composed caps; raises
  ``CostGateExceeded`` AFTER persisting if the new total
  breaches a cap (mirrors Phase 4 step 4.5
  ``OutboxBackedBudget`` durable-first ordering).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from veracrawl.contracts.agent import TokenUsage
from veracrawl.contracts.common import Ref
from veracrawl.contracts.errors import PolicyViolation, VeraCrawlError


class CostGateExceeded(VeraCrawlError, PolicyViolation):
    """Raised when a composed cap (run / objective / host) is
    breached. ``failed_cap`` identifies the tightest cap that
    tripped — operators can pin alerting on the specific
    cap rather than the generic exception."""

    def __init__(self, *, failed_cap: str, run_ref: Ref) -> None:
        if not failed_cap or not failed_cap.strip():
            raise ValueError("failed_cap must be non-blank")
        if not run_ref or not run_ref.strip():
            raise ValueError("run_ref must be non-blank")
        self.failed_cap = failed_cap
        self.run_ref = run_ref
        super().__init__(
            f"cost gate {failed_cap!r} breached for run {run_ref!r}"
        )


class RepeatedFailureSignatureExceeded(VeraCrawlError, PolicyViolation):
    """Raised when the same ``failure_signature`` recurs N=2+
    times within a single objective. Hard-stop so the
    recovery loop doesn't burn budget on a determined-to-fail
    URL."""

    def __init__(
        self,
        *,
        failure_signature: str,
        objective_ref: Ref,
        recurrence_count: int,
    ) -> None:
        if not failure_signature or not failure_signature.strip():
            raise ValueError("failure_signature must be non-blank")
        if not objective_ref or not objective_ref.strip():
            raise ValueError("objective_ref must be non-blank")
        if recurrence_count < 2:
            raise ValueError("recurrence_count must be >= 2")
        self.failure_signature = failure_signature
        self.objective_ref = objective_ref
        self.recurrence_count = recurrence_count
        super().__init__(
            f"failure signature {failure_signature!r} recurred "
            f"{recurrence_count} times for objective {objective_ref!r}"
        )


@runtime_checkable
class CostGatePort(Protocol):
    """Composable cap-enforcement port."""

    def check(
        self,
        *,
        run_ref: Ref,
        objective_ref: Ref,
        origin: str,
        failure_signature: str | None = None,
    ) -> None:
        ...

    def charge(
        self,
        *,
        usage: TokenUsage,
        cost_usd: float,
        run_ref: Ref,
        objective_ref: Ref,
        origin: str,
    ) -> None:
        ...


__all__ = [
    "CostGatePort",
    "CostGateExceeded",
    "RepeatedFailureSignatureExceeded",
]
