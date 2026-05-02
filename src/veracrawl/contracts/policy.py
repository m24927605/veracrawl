"""Policy contract models."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import PolicyDecisionValue


class PolicyDecision(TimestampedModel):
    id: str
    run_id: str
    objective_id: str
    policy_snapshot_id: str
    decision_type: str
    subject_ref: Ref
    decision: PolicyDecisionValue
    reasons: list[str] = Field(default_factory=list)
    evaluated_rules: list[str] = Field(default_factory=list)
    input_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_denial_reason(self) -> PolicyDecision:
        if self.decision != PolicyDecisionValue.ALLOW and not self.reasons:
            raise ValueError("deny and require_review policy decisions require reasons")
        return self


class BlockedActionReport(TimestampedModel):
    id: str
    subject_ref: Ref
    decision_ref: Ref
    blocked_reason: str
    visible_to_operator: bool = True
