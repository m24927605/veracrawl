"""Policy gate helpers used by commands, adapters, and fixtures."""

from __future__ import annotations

from veracrawl.contracts.enums import PolicyDecisionValue
from veracrawl.contracts.errors import PolicyViolationError
from veracrawl.contracts.policy import BlockedActionReport, PolicyDecision


def is_allowed(decision: PolicyDecision) -> bool:
    return decision.decision == PolicyDecisionValue.ALLOW


def blocked_action_report(decision: PolicyDecision) -> BlockedActionReport:
    reason = "; ".join(decision.reasons) if decision.reasons else "policy denied"
    return BlockedActionReport(
        id=f"blocked:{decision.id}",
        subject_ref=decision.subject_ref,
        decision_ref=decision.id,
        blocked_reason=reason,
    )


def require_allowed(decision: PolicyDecision) -> None:
    if not is_allowed(decision):
        report = blocked_action_report(decision)
        raise PolicyViolationError(report.blocked_reason)


def decision_for(
    *,
    decision_id: str,
    run_id: str,
    objective_id: str,
    decision_type: str,
    subject_ref: str,
    allow: bool,
    reasons: list[str] | None = None,
) -> PolicyDecision:
    decision = PolicyDecisionValue.ALLOW if allow else PolicyDecisionValue.DENY
    return PolicyDecision(
        id=decision_id,
        run_id=run_id,
        objective_id=objective_id,
        policy_snapshot_id="policy:foundation",
        decision_type=decision_type,
        subject_ref=subject_ref,
        decision=decision,
        reasons=[] if allow else (reasons or ["blocked by foundation policy"]),
        evaluated_rules=[f"{decision_type}:foundation"],
        input_refs=[subject_ref],
    )
