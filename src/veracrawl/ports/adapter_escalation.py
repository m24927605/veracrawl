"""Phase 3 step 3.2 — adapter-escalation port.

Decides whether to transition from one adapter type to
another given a typed failure. Consumes
``AdapterEscalationPolicy`` (Phase 0 contract — declares
which transitions are allowed) and produces
``AdapterEscalationDecision`` (Phase 0 contract — typed
audit trail of one transition).

Charter: the escalator never bypasses access controls. It
*routes* a failure to the next allowed adapter type per the
declared policy. Transitions outside the design-allowed
table (``_ALLOWED_ESCALATION_TRANSITIONS`` in
``contracts/source_adapter``) are refused at the contract
layer regardless of policy.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import AdapterType
from veracrawl.contracts.source_adapter import (
    AdapterEscalationDecision,
    AdapterEscalationPolicy,
)


@runtime_checkable
class AdapterEscalationPort(Protocol):
    """Decide whether to escalate from ``from_adapter_type``."""

    def decide(
        self,
        *,
        from_adapter_type: AdapterType,
        failure: BaseException,
        run_ref: Ref,
        triggered_by_ref: Ref,
        policy: AdapterEscalationPolicy,
        prior_escalation_count: int,
    ) -> AdapterEscalationDecision | None:
        """Return an escalation decision or ``None`` if the
        policy refuses to escalate (no allowed transition,
        ``requires_review`` is set without an explicit
        approval, or ``max_escalations_per_run`` has been
        reached).
        """

        ...


__all__ = ["AdapterEscalationPort"]
