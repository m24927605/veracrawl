"""Production-facing persistence and queue runtime contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    DurableCommandRecordStatus,
    PersistenceAdapterConformanceFailureType,
    PersistenceAdapterKind,
    PersistenceCapability,
    PersistenceFailureType,
    PersistenceMigrationStatus,
    PersistentQueueOperation,
    ScaleQueueName,
    UnitOfWorkStatus,
)


class PersistenceAdapterSpec(TimestampedModel):
    id: str
    adapter_kind: PersistenceAdapterKind
    capability_refs: list[PersistenceCapability] = Field(default_factory=list)
    port_refs: list[Ref] = Field(default_factory=list)
    transaction_supported: bool
    idempotency_supported: bool
    lease_supported: bool
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_adapter(self) -> PersistenceAdapterSpec:
        required = set(PersistenceCapability)
        if set(self.capability_refs) != required:
            raise ValueError("persistence adapter must declare every target capability")
        if not self.port_refs:
            raise ValueError("persistence adapter requires port refs")
        if not (
            self.transaction_supported
            and self.idempotency_supported
            and self.lease_supported
        ):
            raise ValueError("target adapter must support transactions, idempotency, and leases")
        if not self.policy_decision_refs:
            raise ValueError("persistence adapter requires policy refs")
        return self


class PersistenceTransactionRecord(TimestampedModel):
    id: str
    adapter_ref: Ref
    run_ref: Ref
    unit_of_work_ref: Ref
    status: UnitOfWorkStatus = UnitOfWorkStatus.OPEN
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    idempotency_record_refs: list[Ref] = Field(default_factory=list)
    queue_operation_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    committed_at_ref: Ref | None = None
    rollback_reason_refs: list[Ref] = Field(default_factory=list)
    failure_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_transaction(self) -> PersistenceTransactionRecord:
        if self.status == UnitOfWorkStatus.COMMITTED:
            required = {
                "command_record_refs": self.command_record_refs,
                "event_refs": self.event_refs,
                "outbox_refs": self.outbox_refs,
                "artifact_refs": self.artifact_refs,
                "idempotency_record_refs": self.idempotency_record_refs,
                "queue_operation_refs": self.queue_operation_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "committed_at_ref": self.committed_at_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise ValueError(f"committed persistence transaction missing refs: {missing}")
        if self.status == UnitOfWorkStatus.ROLLED_BACK and not self.rollback_reason_refs:
            raise ValueError("rolled back persistence transaction requires rollback reason refs")
        if self.status == UnitOfWorkStatus.FAILED and not self.failure_refs:
            raise ValueError("failed persistence transaction requires failure refs")
        return self


class IdempotencyPersistenceRecord(TimestampedModel):
    id: str
    idempotency_key: str
    command_identity: str
    command_record_ref: Ref
    command_result_ref: Ref | None = None
    event_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    duplicate_of_ref: Ref | None = None
    status: DurableCommandRecordStatus

    @model_validator(mode="after")
    def validate_idempotency(self) -> IdempotencyPersistenceRecord:
        if not self.idempotency_key or not self.command_identity:
            raise ValueError("idempotency record requires key and command identity")
        if self.status == DurableCommandRecordStatus.COMMITTED:
            if not self.command_result_ref or not self.event_refs or not self.outbox_refs:
                raise ValueError(
                    "committed idempotency record requires result, event, and outbox refs"
                )
        if self.status == DurableCommandRecordStatus.DUPLICATE and not self.duplicate_of_ref:
            raise ValueError("duplicate idempotency record requires duplicate_of_ref")
        return self


class PersistentQueueOperationRecord(TimestampedModel):
    id: str
    queue_name: ScaleQueueName
    operation: PersistentQueueOperation
    queue_item_ref: Ref
    lease_ref: Ref | None = None
    lease_token_ref: Ref | None = None
    heartbeat_ref: Ref | None = None
    command_result_ref: Ref | None = None
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    dead_letter_ref: Ref | None = None
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_operation(self) -> PersistentQueueOperationRecord:
        if self.operation in {
            PersistentQueueOperation.LEASE,
            PersistentQueueOperation.HEARTBEAT,
            PersistentQueueOperation.ACK,
            PersistentQueueOperation.NACK,
            PersistentQueueOperation.DEAD_LETTER,
        } and not (self.lease_ref and self.lease_token_ref):
            raise ValueError("leased queue operation requires lease and token refs")
        if self.operation == PersistentQueueOperation.HEARTBEAT and not self.heartbeat_ref:
            raise ValueError("heartbeat queue operation requires heartbeat ref")
        if self.operation == PersistentQueueOperation.ACK and not self.command_result_ref:
            raise ValueError("ack queue operation requires command result ref")
        if self.operation in {
            PersistentQueueOperation.NACK,
            PersistentQueueOperation.DEAD_LETTER,
        } and not (self.failure_record_refs and self.recovery_action_refs):
            raise ValueError("nack/dead-letter operation requires failure and recovery refs")
        if self.operation == PersistentQueueOperation.DEAD_LETTER and not self.dead_letter_ref:
            raise ValueError("dead-letter operation requires dead letter ref")
        return self


class PersistenceMigrationRecord(TimestampedModel):
    id: str
    adapter_ref: Ref
    migration_name: str
    from_version: str
    to_version: str
    status: PersistenceMigrationStatus
    applied_at_ref: Ref | None = None
    rollback_plan_ref: Ref | None = None
    validation_event_cursor_ref: Ref | None = None
    failure_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_migration(self) -> PersistenceMigrationRecord:
        if not self.migration_name or self.from_version == self.to_version:
            raise ValueError("persistence migration requires a named version transition")
        if self.status == PersistenceMigrationStatus.APPLIED:
            required = {
                "applied_at_ref": self.applied_at_ref,
                "rollback_plan_ref": self.rollback_plan_ref,
                "validation_event_cursor_ref": self.validation_event_cursor_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise ValueError(f"applied persistence migration missing refs: {missing}")
        if self.status == PersistenceMigrationStatus.ROLLED_BACK and not self.rollback_plan_ref:
            raise ValueError("rolled back persistence migration requires rollback plan ref")
        if self.status == PersistenceMigrationStatus.FAILED and not self.failure_refs:
            raise ValueError("failed persistence migration requires failure refs")
        return self


class PersistenceRuntimeReport(TimestampedModel):
    id: str
    run_ref: Ref
    adapter_ref: Ref | None = None
    transaction_ref: Ref | None = None
    command_record_refs: list[Ref] = Field(default_factory=list)
    idempotency_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_ref: Ref | None = None
    outbox_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    queue_operation_refs: list[Ref] = Field(default_factory=list)
    lease_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> PersistenceRuntimeReport:
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "adapter_ref": self.adapter_ref,
                "transaction_ref": self.transaction_ref,
                "command_record_refs": self.command_record_refs,
                "idempotency_record_refs": self.idempotency_record_refs,
                "event_cursor_ref": self.event_cursor_ref,
                "outbox_refs": self.outbox_refs,
                "artifact_refs": self.artifact_refs,
                "queue_operation_refs": self.queue_operation_refs,
                "lease_refs": self.lease_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing persistence report missing refs: {missing}")
        elif not (self.failure_record_refs or self.missing_ref_fields):
            raise ValueError("non-pass persistence report requires failures")
        return self


class PersistenceAdapterConformanceReport(TimestampedModel):
    id: str
    adapter_ref: Ref | None = None
    adapter_kind: PersistenceAdapterKind | None = None
    transaction_refs: list[Ref] = Field(default_factory=list)
    migration_record_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    idempotency_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    queue_operation_refs: list[Ref] = Field(default_factory=list)
    lease_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    contract_only_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_conformance_report(self) -> PersistenceAdapterConformanceReport:
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "adapter_ref": self.adapter_ref,
                "adapter_kind": self.adapter_kind,
                "transaction_refs": self.transaction_refs,
                "migration_record_refs": self.migration_record_refs,
                "command_record_refs": self.command_record_refs,
                "idempotency_record_refs": self.idempotency_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "artifact_refs": self.artifact_refs,
                "queue_operation_refs": self.queue_operation_refs,
                "lease_refs": self.lease_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing persistence adapter conformance missing refs: {missing}")
        elif self.completion_result == CompletenessResult.NEEDS_REVIEW:
            if not self.contract_only_refs:
                raise ValueError(
                    "needs-review persistence adapter conformance requires contract refs"
                )
        elif not (self.failure_record_refs or self.missing_ref_fields):
            raise ValueError("failing persistence adapter conformance requires failures")
        return self


class PersistenceFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: str
    expected_operator_status: str
    expected_failure_type: PersistenceFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> PersistenceFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("persistence fixture must support target profile")
        if self.negative_case and self.expected_completion_result == "pass":
            raise ValueError("negative persistence fixture must not expect pass")
        if self.negative_case and self.expected_failure_type is None:
            raise ValueError("negative persistence fixture requires expected failure type")
        return self


class PersistenceAdapterFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: str
    expected_operator_status: str
    expected_failure_type: PersistenceAdapterConformanceFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> PersistenceAdapterFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("persistence adapter fixture must support target profile")
        if self.negative_case and self.expected_completion_result == "pass":
            raise ValueError("negative persistence adapter fixture must not expect pass")
        if self.negative_case and self.expected_failure_type is None:
            raise ValueError("negative persistence adapter fixture requires expected failure type")
        return self
