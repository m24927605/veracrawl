"""Runtime verification contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import VerificationDecisionValue


class VerificationDecision(TimestampedModel):
    id: str
    candidate_ref: Ref
    evidence_packet_ref: Ref
    decision: VerificationDecisionValue
    authority_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    conflict_record_refs: list[Ref] = Field(default_factory=list)
    freshness_ref: Ref

    @model_validator(mode="after")
    def validate_decision(self) -> VerificationDecision:
        if self.decision == VerificationDecisionValue.ACCEPT and not self.policy_decision_refs:
            raise ValueError("accepted verification requires policy_decision_refs")
        if self.decision == VerificationDecisionValue.CONFLICT and not self.conflict_record_refs:
            raise ValueError("conflict verification requires conflict_record_refs")
        return self


class ReviewDecision(TimestampedModel):
    id: str
    run_ref: Ref
    verification_decision_ref: Ref
    evidence_packet_ref: Ref
    decision: VerificationDecisionValue
    reviewer_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    rationale_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_review(self) -> ReviewDecision:
        if self.decision == VerificationDecisionValue.ACCEPT and not self.policy_decision_refs:
            raise ValueError("accepted review requires policy decision refs")
        if not self.reviewer_ref or not self.rationale_refs:
            raise ValueError("review decision requires reviewer and rationale refs")
        return self
