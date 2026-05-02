"""Durable replay recovery contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult


class DurableReplayRecoveryReport(TimestampedModel):
    id: str
    run_ref: Ref
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    frontier_item_refs: list[Ref] = Field(default_factory=list)
    lease_refs: list[Ref] = Field(default_factory=list)
    scheduler_recovery_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    gap_report_refs: list[Ref] = Field(default_factory=list)
    operator_status: str
    completeness_result: CompletenessResult

    @model_validator(mode="after")
    def validate_recovery(self) -> DurableReplayRecoveryReport:
        if self.completeness_result == CompletenessResult.PASS:
            if self.missing_ref_fields or self.gap_report_refs:
                raise ValueError("passing durable recovery report cannot contain gaps")
        if self.completeness_result != CompletenessResult.PASS:
            if not (self.missing_ref_fields or self.gap_report_refs):
                raise ValueError("non-pass durable recovery report requires gaps or missing refs")
        return self
