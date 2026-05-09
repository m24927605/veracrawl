"""Phase 3 step 3.2 — policy-driven adapter escalator.

Picks the next adapter type in the chain when a failure
makes retrying the current adapter pointless. Decision
logic:

1. If ``prior_escalation_count >= policy.max_escalations_per_run``
   → return ``None`` (cap reached).
2. If ``policy.allowed_transitions[from_adapter_type]`` is
   empty / missing → return ``None`` (no allowed transition).
3. ``requires_review`` policies refuse to auto-escalate;
   the orchestrator must obtain operator approval and
   re-call with a non-review policy. This adapter does NOT
   ship the operator-review channel — Phase 6 step 6.1 does;
   here we surface ``None`` so the orchestrator can route
   the failure to operator review explicitly.
4. Otherwise pick the first allowed target in the policy
   list and build an ``AdapterEscalationDecision``.
"""

from __future__ import annotations

import hashlib
import uuid

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import AdapterType
from veracrawl.contracts.source_adapter import (
    AdapterEscalationDecision,
    AdapterEscalationPolicy,
)


def _failure_signature(failure: BaseException) -> str:
    """Match the Phase 5 step 5.1 signature shape so the
    same failure produces the same hash across the recovery
    + escalation layers."""

    class_name = type(failure).__name__
    status = getattr(failure, "status_code", "")
    payload = f"{class_name}|{status}".encode()
    return hashlib.sha256(payload).hexdigest()[:16]


class PolicyDrivenEscalator:
    """Picks the next allowed adapter type per policy."""

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
        if not run_ref or not run_ref.strip():
            raise ValueError("run_ref must be non-blank")
        if not triggered_by_ref or not triggered_by_ref.strip():
            raise ValueError("triggered_by_ref must be non-blank")
        if prior_escalation_count < 0:
            raise ValueError("prior_escalation_count must be non-negative")
        if prior_escalation_count >= policy.max_escalations_per_run:
            return None
        if policy.requires_review:
            # Refuse auto-escalation; the orchestrator must
            # route to operator review explicitly. Phase 6
            # step 6.1 ships the review channel.
            return None
        targets = policy.allowed_transitions.get(from_adapter_type)
        if not targets:
            return None
        next_adapter_type = targets[0]
        return AdapterEscalationDecision(
            id=f"escalation-decision:{uuid.uuid4().hex}",
            run_ref=run_ref,
            from_adapter_type=from_adapter_type,
            to_adapter_type=next_adapter_type,
            reason=f"policy-driven:{policy.name}",
            failure_signature=_failure_signature(failure),
            policy_ref=policy.id,
            triggered_by_ref=triggered_by_ref,
        )


__all__ = ["PolicyDrivenEscalator", "_failure_signature"]
