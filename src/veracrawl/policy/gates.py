"""Policy gate helpers used by commands, adapters, and fixtures."""

from __future__ import annotations

from veracrawl.contracts.enums import PolicyDecisionValue
from veracrawl.contracts.errors import PolicyViolationError
from veracrawl.contracts.policy import BlockedActionReport, PolicyDecision

RUNTIME_POLICY_DECISION_TYPES = {
    "runtime_source",
    "runtime_evidence",
    "runtime_verification",
    "runtime_publication",
    "artifact_lifecycle",
    "retention",
    "recovery",
    "prompt_context",
}


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


def require_runtime_policy(decision: PolicyDecision, *, expected_type: str) -> None:
    if expected_type not in RUNTIME_POLICY_DECISION_TYPES:
        raise PolicyViolationError(f"unknown runtime policy decision type: {expected_type}")
    if decision.decision_type != expected_type:
        raise PolicyViolationError(
            f"policy decision type mismatch: expected {expected_type}, got {decision.decision_type}"
        )
    require_allowed(decision)


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
