"""Source acquisition runtime contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    RateLimitDecisionValue,
    SourceFailureType,
)


class RateLimitDecision(TimestampedModel):
    id: str
    run_ref: Ref
    source_ref: Ref
    decision: RateLimitDecisionValue
    rate_limit_policy_ref: Ref
    retry_after_ref: Ref | None = None
    reason_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_rate_limit(self) -> RateLimitDecision:
        if self.decision == RateLimitDecisionValue.RATE_LIMIT:
            if not self.retry_after_ref or not self.reason_refs:
                raise ValueError("rate-limited decision requires retry_after and reasons")
        return self


class SourceFailureReport(TimestampedModel):
    id: str
    run_ref: Ref
    source_ref: Ref
    failure_type: SourceFailureType
    operator_status: str
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    retry_refs: list[Ref] = Field(default_factory=list)
    diagnostic_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_failure(self) -> SourceFailureReport:
        if not self.operator_status or not self.diagnostic_refs:
            raise ValueError("source failure report requires operator status and diagnostics")
        return self


class SourceAcquisitionReport(TimestampedModel):
    id: str
    run_ref: Ref
    source_adapter_result_ref: Ref | None = None
    fetch_attempt_refs: list[Ref] = Field(default_factory=list)
    fetch_result_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    frontier_item_ref: Ref
    lease_ref: Ref
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    recovery_report_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> SourceAcquisitionReport:
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "source_adapter_result_ref": self.source_adapter_result_ref,
                "fetch_attempt_refs": self.fetch_attempt_refs,
                "fetch_result_refs": self.fetch_result_refs,
                "artifact_refs": self.artifact_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "recovery_report_refs": self.recovery_report_refs,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing source acquisition report missing refs: {missing}")
        if self.completion_result != CompletenessResult.PASS and not (
            self.failure_report_refs or self.missing_ref_fields
        ):
            raise ValueError("non-pass source acquisition report requires failures or missing refs")
        return self


class SourceFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    adapter_type: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: str
    expected_operator_status: str
    expected_result_type: str | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> SourceFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("source fixture must support target profile")
        if self.negative_case and self.expected_completion_result == "pass":
            raise ValueError("negative source fixture must not expect pass")
        return self
