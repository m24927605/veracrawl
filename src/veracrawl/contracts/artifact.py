"""Runtime artifact reference contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    ArtifactType,
    CompletenessResult,
    ObjectStoreAdapterKind,
    ObjectStoreCapability,
    ObjectStoreConformanceFailureType,
    ObjectStoreOperation,
    OwnerService,
    PrivacyClassification,
)


class RuntimeArtifactRef(TimestampedModel):
    id: str
    artifact_type: ArtifactType
    producer_service: OwnerService
    source_ref: Ref
    content_digest: str
    size_bytes: int
    privacy_classification: PrivacyClassification = PrivacyClassification.INTERNAL
    lifecycle_state_ref: Ref
    retention_policy_ref: Ref

    @model_validator(mode="after")
    def validate_artifact(self) -> RuntimeArtifactRef:
        if not self.content_digest:
            raise ValueError("artifact ref requires content_hash")
        if self.size_bytes < 0:
            raise ValueError("artifact size must be non-negative")
        return self


class ObjectStoreAdapterSpec(TimestampedModel):
    id: str
    adapter_kind: ObjectStoreAdapterKind
    capability_refs: list[ObjectStoreCapability] = Field(default_factory=list)
    bucket_ref: Ref
    namespace_ref: Ref
    content_addressing_supported: bool
    digest_verification_supported: bool
    lifecycle_supported: bool
    retention_policy_refs: list[Ref] = Field(default_factory=list)
    privacy_policy_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_adapter(self) -> ObjectStoreAdapterSpec:
        if set(self.capability_refs) != set(ObjectStoreCapability):
            raise ValueError("object store adapter must declare every target capability")
        if not self.bucket_ref or not self.namespace_ref:
            raise ValueError("object store adapter requires bucket and namespace refs")
        if not (
            self.content_addressing_supported
            and self.digest_verification_supported
            and self.lifecycle_supported
        ):
            raise ValueError("object store adapter requires content, digest, and lifecycle support")
        if not (
            self.retention_policy_refs
            and self.privacy_policy_refs
            and self.policy_decision_refs
        ):
            raise ValueError("object store adapter requires retention, privacy, and policy refs")
        return self


class ObjectStoreOperationRecord(TimestampedModel):
    id: str
    adapter_ref: Ref
    operation: ObjectStoreOperation
    artifact_ref: Ref | None = None
    object_key_ref: Ref | None = None
    content_digest_ref: Ref | None = None
    size_bytes: int | None = None
    etag_ref: Ref | None = None
    read_result_ref: Ref | None = None
    duplicate_of_ref: Ref | None = None
    deletion_marker_ref: Ref | None = None
    lifecycle_state_ref: Ref | None = None
    retention_policy_ref: Ref | None = None
    privacy_policy_ref: Ref | None = None
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_operation(self) -> ObjectStoreOperationRecord:
        if self.operation in {
            ObjectStoreOperation.PUT,
            ObjectStoreOperation.GET,
            ObjectStoreOperation.HEAD,
            ObjectStoreOperation.DELETE,
            ObjectStoreOperation.DUPLICATE_PUT,
        } and not (self.artifact_ref and self.object_key_ref):
            raise ValueError("object store operation requires artifact and object key refs")
        if self.operation in {
            ObjectStoreOperation.PUT,
            ObjectStoreOperation.GET,
            ObjectStoreOperation.HEAD,
        } and not (self.content_digest_ref and self.etag_ref and self.size_bytes is not None):
            raise ValueError("object store read/write operation requires digest, etag, and size")
        if self.operation == ObjectStoreOperation.GET and not self.read_result_ref:
            raise ValueError("object store get operation requires read result ref")
        if self.operation == ObjectStoreOperation.DUPLICATE_PUT and not self.duplicate_of_ref:
            raise ValueError("object store duplicate put requires duplicate_of_ref")
        if self.operation == ObjectStoreOperation.DELETE and not (
            self.deletion_marker_ref and self.lifecycle_state_ref
        ):
            raise ValueError("object store delete operation requires deletion and lifecycle refs")
        if not (
            self.lifecycle_state_ref
            and self.retention_policy_ref
            and self.privacy_policy_ref
            and self.policy_decision_refs
        ):
            raise ValueError(
                "object store operation requires lifecycle, retention, privacy, policy"
            )
        return self


class ObjectStoreConformanceReport(TimestampedModel):
    id: str
    adapter_ref: Ref | None = None
    adapter_kind: ObjectStoreAdapterKind | None = None
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
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> ObjectStoreConformanceReport:
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "adapter_ref": self.adapter_ref,
                "adapter_kind": self.adapter_kind,
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
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing object store conformance missing refs: {missing}")
        elif self.completion_result == CompletenessResult.NEEDS_REVIEW:
            if not self.contract_only_refs:
                raise ValueError("needs-review object store conformance requires contract refs")
        elif not (self.failure_record_refs or self.missing_ref_fields):
            raise ValueError("failing object store conformance requires failures")
        return self


class ObjectStoreFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: str
    expected_operator_status: str
    expected_failure_type: ObjectStoreConformanceFailureType | None = None
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> ObjectStoreFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("object store fixture must support target profile")
        if self.negative_case and self.expected_completion_result == "pass":
            raise ValueError("negative object store fixture must not expect pass")
        if self.negative_case and self.expected_failure_type is None:
            raise ValueError("negative object store fixture requires expected failure type")
        return self
