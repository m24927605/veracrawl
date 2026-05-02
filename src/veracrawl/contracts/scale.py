"""Scale and reliability contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel, utc_now
from veracrawl.contracts.enums import (
    BackpressureSignalType,
    CompletenessResult,
    OpsSeverity,
    QueueBrokerAdapterKind,
    QueueBrokerCapability,
    QueueBrokerConformanceFailureType,
    QueueBrokerOperation,
    ScaleQueueItemStatus,
    ScaleQueueName,
    ScaleRetryClass,
    ScaleShardLeaseStatus,
    WorkerPool,
)


def _require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value


class QueueTopologySpec(TimestampedModel):
    id: str
    project_id: str
    queue_names: list[ScaleQueueName] = Field(default_factory=list)
    shard_key_parts: list[str] = Field(default_factory=list)
    fairness_scope_refs: list[Ref] = Field(default_factory=list)
    per_project_concurrency_limit: int
    per_site_concurrency_limit: int
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_topology(self) -> QueueTopologySpec:
        required_queues = set(ScaleQueueName)
        if set(self.queue_names) != required_queues:
            raise ValueError("queue topology must declare every target queue")
        required_parts = {"project_id", "site_id", "adapter_type", "priority_band"}
        if not required_parts.issubset(set(self.shard_key_parts)):
            raise ValueError("queue topology missing required shard key parts")
        if self.per_project_concurrency_limit < 1 or self.per_site_concurrency_limit < 1:
            raise ValueError("concurrency limits must be positive")
        if self.per_site_concurrency_limit > self.per_project_concurrency_limit:
            raise ValueError("site concurrency cannot exceed project concurrency")
        if not self.fairness_scope_refs or not self.policy_decision_refs:
            raise ValueError("queue topology requires fairness and policy refs")
        return self


class QueueItem(TimestampedModel):
    id: str
    queue_name: ScaleQueueName
    shard_key: str
    run_id: str
    aggregate_type: str
    aggregate_id: str
    command_ref: Ref
    priority: int
    retry_class: ScaleRetryClass
    idempotency_key: str
    expected_version_ref: Ref
    lease_token: str | None = None
    lease_expires_at: datetime | None = None
    attempts: int
    deadline_at: datetime
    status: ScaleQueueItemStatus
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("lease_expires_at", "deadline_at", "updated_at")
    @classmethod
    def require_timestamp_utc(cls, value: datetime | None) -> datetime | None:
        return _require_utc(value) if value is not None else None

    @model_validator(mode="after")
    def validate_item(self) -> QueueItem:
        if not self.shard_key or not self.command_ref:
            raise ValueError("queue item requires shard key and command ref")
        if self.priority < 0 or self.attempts < 0:
            raise ValueError("priority and attempts must be non-negative")
        if not self.idempotency_key or not self.expected_version_ref:
            raise ValueError("queue item requires idempotency and expected version refs")
        if self.status == ScaleQueueItemStatus.LEASED:
            if not self.lease_token or not self.lease_expires_at:
                raise ValueError("leased queue item requires lease token and expiry")
        if self.status == ScaleQueueItemStatus.DEAD_LETTERED and self.attempts < 1:
            raise ValueError("dead-letter queue item requires attempts")
        return self


class ShardLease(TimestampedModel):
    id: str
    queue_name: ScaleQueueName
    shard_key: str
    worker_id: str
    lease_token: str
    acquired_at: datetime
    heartbeat_at: datetime
    expires_at: datetime
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    status: ScaleShardLeaseStatus

    @field_validator("acquired_at", "heartbeat_at", "expires_at")
    @classmethod
    def require_timestamp_utc(cls, value: datetime) -> datetime:
        return _require_utc(value)

    @model_validator(mode="after")
    def validate_lease(self) -> ShardLease:
        if self.expires_at <= self.acquired_at:
            raise ValueError("lease expiry must be after acquisition")
        if self.heartbeat_at < self.acquired_at:
            raise ValueError("lease heartbeat cannot predate acquisition")
        if self.status == ScaleShardLeaseStatus.ACTIVE and not self.policy_decision_refs:
            raise ValueError("active shard lease requires policy refs")
        return self


class RetryDeadLetterRecord(TimestampedModel):
    id: str
    queue_item_id: str
    run_id: str
    retry_class: ScaleRetryClass
    attempts: int
    final_reason: str
    failure_record_id: Ref
    recovery_action_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_dead_letter(self) -> RetryDeadLetterRecord:
        if self.attempts < 1:
            raise ValueError("dead-letter record requires attempts")
        if not self.final_reason or not self.failure_record_id:
            raise ValueError("dead-letter record requires reason and failure record")
        if not self.recovery_action_refs:
            raise ValueError("dead-letter record requires recovery action refs")
        return self


class BackpressureSignal(TimestampedModel):
    id: str
    project_id: str
    site_id: str
    signal_type: BackpressureSignalType
    value: float
    threshold: float
    severity: OpsSeverity
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_signal(self) -> BackpressureSignal:
        if self.threshold <= 0:
            raise ValueError("backpressure threshold must be positive")
        if self.value < 0:
            raise ValueError("backpressure value must be non-negative")
        if self.value >= self.threshold and not self.policy_decision_refs:
            raise ValueError("threshold breach requires policy refs")
        return self


class AutoscalingDecision(TimestampedModel):
    id: str
    worker_pool: WorkerPool
    reason_signal_refs: list[Ref] = Field(default_factory=list)
    from_capacity: int
    to_capacity: int
    cooldown_seconds: int
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_decision(self) -> AutoscalingDecision:
        if not self.reason_signal_refs:
            raise ValueError("autoscaling decision requires reason signal refs")
        if self.from_capacity < 0 or self.to_capacity < 0:
            raise ValueError("autoscaling capacities must be non-negative")
        if self.cooldown_seconds < 0:
            raise ValueError("autoscaling cooldown must be non-negative")
        if self.from_capacity != self.to_capacity and not self.policy_decision_refs:
            raise ValueError("capacity-changing autoscaling requires policy refs")
        return self


class ScaleRecoveryReport(TimestampedModel):
    id: str
    run_ref: Ref
    queue_topology_ref: Ref | None = None
    queue_item_refs: list[Ref] = Field(default_factory=list)
    shard_lease_refs: list[Ref] = Field(default_factory=list)
    backpressure_signal_refs: list[Ref] = Field(default_factory=list)
    autoscaling_decision_refs: list[Ref] = Field(default_factory=list)
    dead_letter_record_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    dr_restore_report_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> ScaleRecoveryReport:
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "queue_topology_ref": self.queue_topology_ref,
                "queue_item_refs": self.queue_item_refs,
                "shard_lease_refs": self.shard_lease_refs,
                "backpressure_signal_refs": self.backpressure_signal_refs,
                "autoscaling_decision_refs": self.autoscaling_decision_refs,
                "dead_letter_record_refs": self.dead_letter_record_refs,
                "failure_record_refs": self.failure_record_refs,
                "recovery_action_refs": self.recovery_action_refs,
                "dr_restore_report_refs": self.dr_restore_report_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing scale recovery report missing refs: {missing}")
        elif not (self.failure_record_refs or self.missing_ref_fields):
            raise ValueError("non-pass scale recovery report requires failures")
        return self


class QueueBrokerAdapterSpec(TimestampedModel):
    id: str
    adapter_kind: QueueBrokerAdapterKind
    queue_names: list[ScaleQueueName] = Field(default_factory=list)
    capability_refs: list[QueueBrokerCapability] = Field(default_factory=list)
    visibility_timeout_seconds: int
    fencing_token_supported: bool
    idempotency_supported: bool
    fairness_scope_refs: list[Ref] = Field(default_factory=list)
    backpressure_signal_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_adapter(self) -> QueueBrokerAdapterSpec:
        if set(self.queue_names) != set(ScaleQueueName):
            raise ValueError("queue broker adapter must declare every target queue")
        if set(self.capability_refs) != set(QueueBrokerCapability):
            raise ValueError("queue broker adapter must declare every target capability")
        if self.visibility_timeout_seconds < 1:
            raise ValueError("queue broker visibility timeout must be positive")
        if not (self.fencing_token_supported and self.idempotency_supported):
            raise ValueError("queue broker adapter requires fencing tokens and idempotency")
        if not (
            self.fairness_scope_refs
            and self.backpressure_signal_refs
            and self.policy_decision_refs
        ):
            raise ValueError(
                "queue broker adapter requires fairness, backpressure, and policy refs"
            )
        return self


class QueueBrokerOperationRecord(TimestampedModel):
    id: str
    adapter_ref: Ref
    queue_name: ScaleQueueName
    operation: QueueBrokerOperation
    queue_item_ref: Ref
    lease_ref: Ref | None = None
    fencing_token_ref: Ref | None = None
    visibility_timeout_ref: Ref | None = None
    heartbeat_ref: Ref | None = None
    retry_ref: Ref | None = None
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    dead_letter_ref: Ref | None = None
    duplicate_of_ref: Ref | None = None
    fairness_scope_refs: list[Ref] = Field(default_factory=list)
    backpressure_signal_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_operation(self) -> QueueBrokerOperationRecord:
        if self.operation in {
            QueueBrokerOperation.LEASE,
            QueueBrokerOperation.HEARTBEAT,
            QueueBrokerOperation.ACK,
            QueueBrokerOperation.NACK,
            QueueBrokerOperation.DEAD_LETTER,
        } and not (self.lease_ref and self.fencing_token_ref and self.visibility_timeout_ref):
            raise ValueError("leased broker operation requires lease, fencing, and visibility refs")
        if self.operation == QueueBrokerOperation.HEARTBEAT and not self.heartbeat_ref:
            raise ValueError("broker heartbeat operation requires heartbeat ref")
        if self.operation == QueueBrokerOperation.NACK and not (
            self.failure_record_refs and self.recovery_action_refs and self.retry_ref
        ):
            raise ValueError("broker nack operation requires failure, recovery, and retry refs")
        if self.operation == QueueBrokerOperation.DEAD_LETTER and not (
            self.dead_letter_ref and self.failure_record_refs and self.recovery_action_refs
        ):
            raise ValueError("broker dead-letter operation requires dead-letter and recovery refs")
        if self.operation == QueueBrokerOperation.DUPLICATE_ENQUEUE and not self.duplicate_of_ref:
            raise ValueError("broker duplicate enqueue requires duplicate_of_ref")
        if not (
            self.fairness_scope_refs
            and self.backpressure_signal_refs
            and self.policy_decision_refs
        ):
            raise ValueError("broker operation requires fairness, backpressure, and policy refs")
        return self


class QueueBrokerConformanceReport(TimestampedModel):
    id: str
    adapter_ref: Ref | None = None
    adapter_kind: QueueBrokerAdapterKind | None = None
    queue_topology_ref: Ref | None = None
    queue_item_refs: list[Ref] = Field(default_factory=list)
    broker_operation_refs: list[Ref] = Field(default_factory=list)
    lease_refs: list[Ref] = Field(default_factory=list)
    heartbeat_refs: list[Ref] = Field(default_factory=list)
    ack_refs: list[Ref] = Field(default_factory=list)
    nack_refs: list[Ref] = Field(default_factory=list)
    dead_letter_refs: list[Ref] = Field(default_factory=list)
    fencing_token_refs: list[Ref] = Field(default_factory=list)
    retry_refs: list[Ref] = Field(default_factory=list)
    fairness_scope_refs: list[Ref] = Field(default_factory=list)
    backpressure_signal_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    contract_only_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> QueueBrokerConformanceReport:
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "adapter_ref": self.adapter_ref,
                "adapter_kind": self.adapter_kind,
                "queue_topology_ref": self.queue_topology_ref,
                "queue_item_refs": self.queue_item_refs,
                "broker_operation_refs": self.broker_operation_refs,
                "lease_refs": self.lease_refs,
                "heartbeat_refs": self.heartbeat_refs,
                "ack_refs": self.ack_refs,
                "dead_letter_refs": self.dead_letter_refs,
                "fencing_token_refs": self.fencing_token_refs,
                "retry_refs": self.retry_refs,
                "fairness_scope_refs": self.fairness_scope_refs,
                "backpressure_signal_refs": self.backpressure_signal_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing queue broker conformance missing refs: {missing}")
        elif self.completion_result == CompletenessResult.NEEDS_REVIEW:
            if not self.contract_only_refs:
                raise ValueError("needs-review queue broker conformance requires contract refs")
        elif not (self.failure_record_refs or self.missing_ref_fields):
            raise ValueError("failing queue broker conformance requires failures")
        return self


class ScaleFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: str
    expected_operator_status: str
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> ScaleFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("scale fixture must support target profile")
        if self.negative_case and self.expected_completion_result == "pass":
            raise ValueError("negative scale fixture must not expect pass")
        return self


class QueueBrokerFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: str
    expected_operator_status: str
    expected_failure_type: QueueBrokerConformanceFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> QueueBrokerFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("queue broker fixture must support target profile")
        if self.negative_case and self.expected_completion_result == "pass":
            raise ValueError("negative queue broker fixture must not expect pass")
        if self.negative_case and self.expected_failure_type is None:
            raise ValueError("negative queue broker fixture requires expected failure type")
        return self
