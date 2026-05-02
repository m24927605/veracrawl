"""Scheduler frontier and queue lease contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    FrontierItemStatus,
    QueueLeaseStatus,
)


class FrontierItem(TimestampedModel):
    id: str
    run_ref: Ref
    source_ref: Ref
    priority: int
    status: FrontierItemStatus = FrontierItemStatus.QUEUED
    attempt_count: int = 0
    max_attempts: int = 3
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    lease_ref: Ref | None = None
    result_refs: list[Ref] = Field(default_factory=list)
    last_error_ref: Ref | None = None
    failure_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_frontier_item(self) -> FrontierItem:
        if self.attempt_count < 0 or self.max_attempts < 1:
            raise ValueError("frontier attempts must be valid")
        if self.status == FrontierItemStatus.LEASED and not self.lease_ref:
            raise ValueError("leased frontier item requires lease_ref")
        if self.status == FrontierItemStatus.COMPLETED and not self.result_refs:
            raise ValueError("completed frontier item requires result_refs")
        if self.status == FrontierItemStatus.DEAD_LETTERED and not self.failure_refs:
            raise ValueError("dead-lettered frontier item requires failure_refs")
        return self


class QueueLease(TimestampedModel):
    id: str
    frontier_item_ref: Ref
    run_ref: Ref
    lease_token_ref: Ref
    holder_ref: Ref
    status: QueueLeaseStatus = QueueLeaseStatus.ACTIVE
    expires_at_ref: Ref
    heartbeat_ref: Ref | None = None
    completed_at_ref: Ref | None = None
    released_at_ref: Ref | None = None
    expiry_reason_ref: Ref | None = None
    replaced_by_lease_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_lease(self) -> QueueLease:
        if self.status == QueueLeaseStatus.COMPLETED and not self.completed_at_ref:
            raise ValueError("completed lease requires completed_at_ref")
        if self.status == QueueLeaseStatus.RELEASED and not self.released_at_ref:
            raise ValueError("released lease requires released_at_ref")
        if self.status == QueueLeaseStatus.EXPIRED and not self.expiry_reason_ref:
            raise ValueError("expired lease requires expiry_reason_ref")
        if self.status == QueueLeaseStatus.INVALID and not self.expiry_reason_ref:
            raise ValueError("invalid lease requires reason ref")
        return self


class SchedulerRecoveryReport(TimestampedModel):
    id: str
    run_ref: Ref
    expired_lease_refs: list[Ref] = Field(default_factory=list)
    retry_frontier_item_refs: list[Ref] = Field(default_factory=list)
    dead_letter_refs: list[Ref] = Field(default_factory=list)
    invalid_lease_refs: list[Ref] = Field(default_factory=list)
    operator_status: str
    completeness_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> SchedulerRecoveryReport:
        has_blockers = bool(
            self.expired_lease_refs
            or self.retry_frontier_item_refs
            or self.dead_letter_refs
            or self.invalid_lease_refs
        )
        if self.completeness_result == CompletenessResult.PASS and has_blockers:
            raise ValueError("passing scheduler recovery report cannot contain blockers")
        if self.completeness_result != CompletenessResult.PASS and not has_blockers:
            raise ValueError("non-pass scheduler recovery report requires blockers")
        return self
