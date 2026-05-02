"""Destination-neutral export contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel, utc_now
from veracrawl.contracts.enums import (
    CompletenessResult,
    ExportAttemptStatus,
    ExportCorrectionStatus,
    ExportDeliveryMode,
    ExportJobStatus,
    ExportPropagationStatus,
    ExportRetryClassification,
    ExportTargetType,
    ExportWithdrawalReason,
    ExportWithdrawalStatus,
)


def _require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value


class ExportTargetSpec(TimestampedModel):
    id: str
    project_id: str
    target_type: ExportTargetType
    destination_ref: Ref
    destination_schema_ref: Ref
    auth_scope_ref: Ref
    delivery_mode: ExportDeliveryMode
    idempotency_key_template: str
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_target(self) -> ExportTargetSpec:
        if not self.destination_ref or not self.destination_schema_ref:
            raise ValueError("export target requires destination and schema refs")
        if not self.auth_scope_ref:
            raise ValueError("export target requires auth scope ref")
        if "{output_manifest_hash}" not in self.idempotency_key_template:
            raise ValueError("idempotency template must include output_manifest_hash")
        if not self.policy_decision_refs:
            raise ValueError("export target requires policy refs")
        return self


class ExportJob(TimestampedModel):
    id: str
    run_id: str
    export_target_spec_id: str
    output_refs: list[Ref] = Field(default_factory=list)
    destination_schema_version: str
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    attempt_refs: list[Ref] = Field(default_factory=list)
    delivery_receipt_refs: list[Ref] = Field(default_factory=list)
    idempotency_key_refs: list[Ref] = Field(default_factory=list)
    status: ExportJobStatus

    @model_validator(mode="after")
    def validate_job(self) -> ExportJob:
        if not self.output_refs:
            raise ValueError("export job requires output refs")
        if not self.policy_decision_refs:
            raise ValueError("export job requires policy refs")
        if not self.idempotency_key_refs:
            raise ValueError("export job requires idempotency key refs")
        if self.status == ExportJobStatus.COMPLETED:
            if not self.attempt_refs or not self.delivery_receipt_refs:
                raise ValueError("completed export job requires attempts and receipts")
        if self.status == ExportJobStatus.FAILED and not self.attempt_refs:
            raise ValueError("failed export job requires attempt refs")
        return self


class ExportAttempt(TimestampedModel):
    id: str
    export_job_id: str
    attempt_number: int
    idempotency_key: str
    output_refs: list[Ref] = Field(default_factory=list)
    external_object_ids: list[str] = Field(default_factory=list)
    delivery_receipt_ref: Ref | None = None
    retry_classification: ExportRetryClassification | None = None
    status: ExportAttemptStatus
    error: dict[str, object] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=utc_now)
    ended_at: datetime | None = None

    @field_validator("started_at", "ended_at")
    @classmethod
    def require_timestamp_utc(cls, value: datetime | None) -> datetime | None:
        return _require_utc(value) if value is not None else None

    @model_validator(mode="after")
    def validate_attempt(self) -> ExportAttempt:
        if self.attempt_number < 1:
            raise ValueError("export attempt number must be positive")
        if not self.idempotency_key or not self.output_refs:
            raise ValueError("export attempt requires idempotency key and output refs")
        if self.status == ExportAttemptStatus.COMPLETED:
            if not self.external_object_ids or not self.delivery_receipt_ref:
                raise ValueError("completed export attempt requires external ids and receipt")
            if self.error:
                raise ValueError("completed export attempt cannot include error")
        if self.status == ExportAttemptStatus.FAILED:
            if not self.retry_classification or not self.error:
                raise ValueError("failed export attempt requires retry classification and error")
        return self


class ExportDeliveryReceipt(TimestampedModel):
    id: str
    export_attempt_id: str
    destination_ref: Ref
    external_object_ids: list[str] = Field(default_factory=list)
    delivered_output_refs: list[Ref] = Field(default_factory=list)
    withdrawn_output_refs: list[Ref] = Field(default_factory=list)
    delete_propagation_refs: list[Ref] = Field(default_factory=list)
    receipt_hash: str
    acknowledged_at: datetime = Field(default_factory=utc_now)

    @field_validator("acknowledged_at")
    @classmethod
    def require_ack_utc(cls, value: datetime) -> datetime:
        return _require_utc(value)

    @model_validator(mode="after")
    def validate_receipt(self) -> ExportDeliveryReceipt:
        if not self.destination_ref or not self.external_object_ids:
            raise ValueError("export receipt requires destination and external ids")
        if not (self.delivered_output_refs or self.withdrawn_output_refs):
            raise ValueError("export receipt requires delivered or withdrawn output refs")
        if self.withdrawn_output_refs and not self.delete_propagation_refs:
            raise ValueError("withdrawal receipt requires propagation refs")
        if not self.receipt_hash:
            raise ValueError("export receipt requires receipt hash")
        return self


class ExportWithdrawalJob(TimestampedModel):
    id: str
    project_id: str
    export_target_spec_id: str
    output_version_refs: list[Ref] = Field(default_factory=list)
    reason: ExportWithdrawalReason
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    withdrawal_attempt_refs: list[Ref] = Field(default_factory=list)
    review_item_refs: list[Ref] = Field(default_factory=list)
    status: ExportWithdrawalStatus

    @model_validator(mode="after")
    def validate_withdrawal_job(self) -> ExportWithdrawalJob:
        if not self.output_version_refs:
            raise ValueError("export withdrawal job requires output version refs")
        if not self.policy_decision_refs:
            raise ValueError("export withdrawal job requires policy refs")
        if self.status == ExportWithdrawalStatus.COMPLETED and not self.withdrawal_attempt_refs:
            raise ValueError("completed withdrawal job requires attempt refs")
        if self.status == ExportWithdrawalStatus.FAILED and not (
            self.withdrawal_attempt_refs or self.review_item_refs
        ):
            raise ValueError("failed withdrawal job requires attempts or review refs")
        return self


class ExportWithdrawalAttempt(TimestampedModel):
    id: str
    export_withdrawal_job_id: str
    attempt_number: int
    idempotency_key: str
    external_object_mappings: dict[Ref, list[str]] = Field(default_factory=dict)
    propagation_status: ExportPropagationStatus
    delivery_receipt_ref: Ref | None = None
    unsupported_reason: str = ""
    error: dict[str, object] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=utc_now)
    ended_at: datetime | None = None

    @field_validator("started_at", "ended_at")
    @classmethod
    def require_timestamp_utc(cls, value: datetime | None) -> datetime | None:
        return _require_utc(value) if value is not None else None

    @model_validator(mode="after")
    def validate_withdrawal_attempt(self) -> ExportWithdrawalAttempt:
        if self.attempt_number < 1:
            raise ValueError("withdrawal attempt number must be positive")
        if not self.idempotency_key:
            raise ValueError("withdrawal attempt requires idempotency key")
        if self.propagation_status == ExportPropagationStatus.PROPAGATED:
            if not self.external_object_mappings or not self.delivery_receipt_ref:
                raise ValueError("propagated withdrawal requires mappings and receipt")
        if self.propagation_status == ExportPropagationStatus.DESTINATION_UNSUPPORTED:
            if not self.unsupported_reason:
                raise ValueError("unsupported withdrawal requires reason")
        if self.propagation_status == ExportPropagationStatus.FAILED and not self.error:
            raise ValueError("failed withdrawal requires error")
        return self


class ExportCorrectionRecord(TimestampedModel):
    id: str
    project_id: str
    superseded_output_ref: Ref
    replacement_output_ref: Ref
    withdrawal_job_ref: Ref | None = None
    replacement_export_job_ref: Ref | None = None
    destination_object_mappings: dict[Ref, list[str]] = Field(default_factory=dict)
    receipt_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    status: ExportCorrectionStatus

    @model_validator(mode="after")
    def validate_correction(self) -> ExportCorrectionRecord:
        if self.superseded_output_ref == self.replacement_output_ref:
            raise ValueError("correction requires distinct superseded and replacement outputs")
        if not self.policy_decision_refs:
            raise ValueError("correction record requires policy refs")
        if self.status == ExportCorrectionStatus.PROPAGATED:
            required = [
                self.withdrawal_job_ref,
                self.replacement_export_job_ref,
                self.destination_object_mappings,
                self.receipt_refs,
            ]
            if not all(required):
                raise ValueError(
                    "propagated correction requires withdrawal, export, mappings, receipts"
                )
        if self.status == ExportCorrectionStatus.FAILED and not self.receipt_refs:
            raise ValueError("failed correction requires diagnostic receipt refs")
        return self


class ExportReconciliationReport(TimestampedModel):
    id: str
    run_ref: Ref
    export_target_spec_refs: list[Ref] = Field(default_factory=list)
    export_job_refs: list[Ref] = Field(default_factory=list)
    export_attempt_refs: list[Ref] = Field(default_factory=list)
    delivery_receipt_refs: list[Ref] = Field(default_factory=list)
    withdrawal_job_refs: list[Ref] = Field(default_factory=list)
    withdrawal_attempt_refs: list[Ref] = Field(default_factory=list)
    correction_record_refs: list[Ref] = Field(default_factory=list)
    destination_object_mapping_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_reconciliation(self) -> ExportReconciliationReport:
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "export_target_spec_refs": self.export_target_spec_refs,
                "export_job_refs": self.export_job_refs,
                "export_attempt_refs": self.export_attempt_refs,
                "delivery_receipt_refs": self.delivery_receipt_refs,
                "destination_object_mapping_refs": self.destination_object_mapping_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing export reconciliation missing refs: {missing}")
        elif not (self.failure_report_refs or self.missing_ref_fields):
            raise ValueError("non-pass export reconciliation requires failures")
        return self


class ExportFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: str
    expected_operator_status: str
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> ExportFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("export fixture must support target profile")
        if self.negative_case and self.expected_completion_result == "pass":
            raise ValueError("negative export fixture must not expect pass")
        return self
