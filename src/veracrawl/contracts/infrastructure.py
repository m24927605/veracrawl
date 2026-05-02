"""Integrated operational runtime infrastructure contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    RuntimeInfrastructureAdapterFamily,
    RuntimeInfrastructureFailureType,
)


class RuntimeInfrastructureSpec(TimestampedModel):
    id: str
    persistence_adapter_ref: Ref
    queue_broker_adapter_ref: Ref
    object_store_adapter_ref: Ref
    required_live_adapter_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_spec(self) -> RuntimeInfrastructureSpec:
        required = {
            self.persistence_adapter_ref,
            self.queue_broker_adapter_ref,
            self.object_store_adapter_ref,
        }
        if not required.issubset(set(self.required_live_adapter_refs)):
            raise ValueError("runtime infrastructure spec must require all live adapter refs")
        if not self.policy_decision_refs:
            raise ValueError("runtime infrastructure spec requires policy refs")
        return self


class RuntimeInfrastructureReport(TimestampedModel):
    id: str
    run_ref: Ref
    infrastructure_spec_ref: Ref | None = None
    live_adapter_families: list[RuntimeInfrastructureAdapterFamily] = Field(default_factory=list)
    persistence_report_refs: list[Ref] = Field(default_factory=list)
    queue_broker_report_refs: list[Ref] = Field(default_factory=list)
    object_store_report_refs: list[Ref] = Field(default_factory=list)
    persistence_adapter_refs: list[Ref] = Field(default_factory=list)
    queue_broker_adapter_refs: list[Ref] = Field(default_factory=list)
    object_store_adapter_refs: list[Ref] = Field(default_factory=list)
    transaction_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    idempotency_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    queue_topology_refs: list[Ref] = Field(default_factory=list)
    queue_item_refs: list[Ref] = Field(default_factory=list)
    broker_operation_refs: list[Ref] = Field(default_factory=list)
    queue_operation_refs: list[Ref] = Field(default_factory=list)
    lease_refs: list[Ref] = Field(default_factory=list)
    heartbeat_refs: list[Ref] = Field(default_factory=list)
    ack_refs: list[Ref] = Field(default_factory=list)
    nack_refs: list[Ref] = Field(default_factory=list)
    dead_letter_refs: list[Ref] = Field(default_factory=list)
    fencing_token_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    object_operation_refs: list[Ref] = Field(default_factory=list)
    content_digest_refs: list[Ref] = Field(default_factory=list)
    read_result_refs: list[Ref] = Field(default_factory=list)
    head_refs: list[Ref] = Field(default_factory=list)
    list_refs: list[Ref] = Field(default_factory=list)
    delete_refs: list[Ref] = Field(default_factory=list)
    lifecycle_state_refs: list[Ref] = Field(default_factory=list)
    retention_policy_refs: list[Ref] = Field(default_factory=list)
    privacy_policy_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    contract_only_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    missing_ref_fields: list[str] = Field(default_factory=list)
    idempotency_deduped: bool = False
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> RuntimeInfrastructureReport:
        if self.completion_result == CompletenessResult.PASS:
            required_families = set(RuntimeInfrastructureAdapterFamily)
            if set(self.live_adapter_families) != required_families:
                raise ValueError("passing infrastructure report requires every live adapter family")
            required = {
                "infrastructure_spec_ref": self.infrastructure_spec_ref,
                "persistence_report_refs": self.persistence_report_refs,
                "queue_broker_report_refs": self.queue_broker_report_refs,
                "object_store_report_refs": self.object_store_report_refs,
                "persistence_adapter_refs": self.persistence_adapter_refs,
                "queue_broker_adapter_refs": self.queue_broker_adapter_refs,
                "object_store_adapter_refs": self.object_store_adapter_refs,
                "transaction_refs": self.transaction_refs,
                "command_record_refs": self.command_record_refs,
                "idempotency_record_refs": self.idempotency_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "queue_topology_refs": self.queue_topology_refs,
                "queue_item_refs": self.queue_item_refs,
                "broker_operation_refs": self.broker_operation_refs,
                "queue_operation_refs": self.queue_operation_refs,
                "lease_refs": self.lease_refs,
                "heartbeat_refs": self.heartbeat_refs,
                "ack_refs": self.ack_refs,
                "nack_refs": self.nack_refs,
                "dead_letter_refs": self.dead_letter_refs,
                "artifact_refs": self.artifact_refs,
                "object_operation_refs": self.object_operation_refs,
                "content_digest_refs": self.content_digest_refs,
                "read_result_refs": self.read_result_refs,
                "head_refs": self.head_refs,
                "list_refs": self.list_refs,
                "delete_refs": self.delete_refs,
                "lifecycle_state_refs": self.lifecycle_state_refs,
                "retention_policy_refs": self.retention_policy_refs,
                "privacy_policy_refs": self.privacy_policy_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields or self.contract_only_refs:
                raise ValueError(f"passing infrastructure report missing refs: {missing}")
        elif self.completion_result == CompletenessResult.NEEDS_REVIEW:
            if not (self.contract_only_refs or self.missing_ref_fields):
                raise ValueError("needs_review infrastructure report requires contract-only refs")
        elif not (self.failure_record_refs or self.missing_ref_fields):
            raise ValueError("failed infrastructure report requires failure or missing refs")
        return self


class RuntimeInfrastructureFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: RuntimeInfrastructureFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_manifest(self) -> RuntimeInfrastructureFixtureManifest:
        if not self.profile_refs:
            raise ValueError("runtime infrastructure fixture requires profile refs")
        if self.negative_case and self.expected_completion_result != CompletenessResult.FAIL:
            raise ValueError("negative runtime infrastructure fixture must expect fail")
        if self.expected_failure_type is not None and not self.negative_case:
            raise ValueError("expected failure type requires negative case")
        return self
