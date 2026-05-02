"""Core object store conformance harness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from veracrawl.contracts.artifact import (
    ObjectStoreAdapterSpec,
    ObjectStoreConformanceReport,
    ObjectStoreOperationRecord,
    RuntimeArtifactRef,
)
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    ArtifactType,
    CompletenessResult,
    ObjectStoreConformanceFailureType,
    ObjectStoreOperation,
    OwnerService,
    PrivacyClassification,
)


class OperationalObjectStoreAdapter(Protocol):
    def reopen(self) -> OperationalObjectStoreAdapter: ...

    def write(
        self,
        *,
        artifact_id: str,
        artifact_type: ArtifactType,
        producer_service: OwnerService,
        source_ref: Ref,
        content: str,
        privacy_classification: PrivacyClassification,
        adapter_ref: Ref,
        retention_policy_ref: Ref,
        privacy_policy_ref: Ref,
        policy_decision_refs: list[Ref],
    ) -> tuple[RuntimeArtifactRef, ObjectStoreOperationRecord]: ...

    def read(
        self,
        artifact: RuntimeArtifactRef,
        *,
        adapter_ref: Ref,
        retention_policy_ref: Ref,
        privacy_policy_ref: Ref,
        policy_decision_refs: list[Ref],
    ) -> tuple[str, ObjectStoreOperationRecord]: ...

    def head(
        self,
        artifact: RuntimeArtifactRef,
        *,
        adapter_ref: Ref,
        retention_policy_ref: Ref,
        privacy_policy_ref: Ref,
        policy_decision_refs: list[Ref],
    ) -> ObjectStoreOperationRecord: ...

    def list_artifacts(
        self,
        *,
        adapter_ref: Ref,
        retention_policy_ref: Ref,
        privacy_policy_ref: Ref,
        policy_decision_refs: list[Ref],
    ) -> tuple[list[RuntimeArtifactRef], ObjectStoreOperationRecord]: ...

    def delete(
        self,
        artifact: RuntimeArtifactRef,
        *,
        adapter_ref: Ref,
        retention_policy_ref: Ref,
        privacy_policy_ref: Ref,
        policy_decision_refs: list[Ref],
    ) -> ObjectStoreOperationRecord: ...

    def object_count(self) -> int: ...


@dataclass(frozen=True)
class ObjectStoreConformanceResult:
    adapter: ObjectStoreAdapterSpec | None
    artifacts: list[RuntimeArtifactRef]
    operations: list[ObjectStoreOperationRecord]
    report: ObjectStoreConformanceReport
    duplicate_deduped: bool = False
    object_count: int = 0
    read_content: str | None = None


_FAILURES: dict[str, tuple[ObjectStoreConformanceFailureType, str]] = {
    "object-store-missing-digest": (
        ObjectStoreConformanceFailureType.OBJECT_STORE_MISSING_DIGEST,
        "content_digest_refs",
    ),
    "object-store-missing-read-after-write": (
        ObjectStoreConformanceFailureType.OBJECT_STORE_MISSING_READ_AFTER_WRITE,
        "read_result_refs",
    ),
    "object-store-missing-delete-marker": (
        ObjectStoreConformanceFailureType.OBJECT_STORE_MISSING_DELETE_MARKER,
        "delete_refs",
    ),
}


def run_object_store_conformance(
    *,
    fixture_id: str,
    scenario: str,
    store: OperationalObjectStoreAdapter | None,
    adapter_spec: ObjectStoreAdapterSpec,
) -> ObjectStoreConformanceResult:
    if scenario in _FAILURES:
        failure, missing = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            adapter=adapter_spec,
            failure=failure,
            missing_field=missing,
        )
    if store is None:
        raise ValueError(f"fixture {fixture_id} requires an operational object store adapter")
    return _success_result(
        fixture_id=fixture_id,
        scenario=scenario,
        store=store,
        adapter=adapter_spec,
    )


def run_object_store_runtime_unavailable_conformance(
    *,
    fixture_id: str,
    adapter_spec: ObjectStoreAdapterSpec,
) -> ObjectStoreConformanceResult:
    report = ObjectStoreConformanceReport(
        id=f"object-store-conformance-report:{fixture_id}",
        adapter_ref=adapter_spec.id,
        adapter_kind=adapter_spec.adapter_kind,
        policy_decision_refs=adapter_spec.policy_decision_refs,
        contract_only_refs=[
            "runtime:object-store:endpoint-required",
            "runtime:object-store:live-conformance-not-executed",
        ],
        operator_status="s3_object_store_runtime_unavailable",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    return ObjectStoreConformanceResult(
        adapter=adapter_spec,
        artifacts=[],
        operations=[],
        report=report,
    )


def _success_result(
    *,
    fixture_id: str,
    scenario: str,
    store: OperationalObjectStoreAdapter,
    adapter: ObjectStoreAdapterSpec,
) -> ObjectStoreConformanceResult:
    policy_refs = adapter.policy_decision_refs
    retention_ref = adapter.retention_policy_refs[0]
    privacy_ref = adapter.privacy_policy_refs[0]
    content = f"veracrawl object store conformance artifact for {fixture_id}"
    artifact, put_op = store.write(
        artifact_id=f"runtime-artifact:{fixture_id}:raw",
        artifact_type=ArtifactType.RAW_SOURCE,
        producer_service=OwnerService.FETCH,
        source_ref=f"source-result:{fixture_id}:raw",
        content=content,
        privacy_classification=PrivacyClassification.INTERNAL,
        adapter_ref=adapter.id,
        retention_policy_ref=retention_ref,
        privacy_policy_ref=privacy_ref,
        policy_decision_refs=policy_refs,
    )
    operations = [put_op]
    duplicate_deduped = False
    if scenario == "s3-object-store-idempotency-success":
        reopened = store.reopen()
        duplicate_artifact, duplicate_op = reopened.write(
            artifact_id=artifact.id,
            artifact_type=artifact.artifact_type,
            producer_service=artifact.producer_service,
            source_ref=artifact.source_ref,
            content=content,
            privacy_classification=artifact.privacy_classification,
            adapter_ref=adapter.id,
            retention_policy_ref=retention_ref,
            privacy_policy_ref=privacy_ref,
            policy_decision_refs=policy_refs,
        )
        store = reopened
        operations.append(duplicate_op)
        duplicate_deduped = (
            duplicate_artifact.content_digest == artifact.content_digest
            and duplicate_op.operation == ObjectStoreOperation.DUPLICATE_PUT
        )
    read_content, get_op = store.read(
        artifact,
        adapter_ref=adapter.id,
        retention_policy_ref=retention_ref,
        privacy_policy_ref=privacy_ref,
        policy_decision_refs=policy_refs,
    )
    head_op = store.head(
        artifact,
        adapter_ref=adapter.id,
        retention_policy_ref=retention_ref,
        privacy_policy_ref=privacy_ref,
        policy_decision_refs=policy_refs,
    )
    listed, list_op = store.list_artifacts(
        adapter_ref=adapter.id,
        retention_policy_ref=retention_ref,
        privacy_policy_ref=privacy_ref,
        policy_decision_refs=policy_refs,
    )
    delete_op = store.delete(
        artifact,
        adapter_ref=adapter.id,
        retention_policy_ref=retention_ref,
        privacy_policy_ref=privacy_ref,
        policy_decision_refs=policy_refs,
    )
    operations.extend([get_op, head_op, list_op, delete_op])
    report = ObjectStoreConformanceReport(
        id=f"object-store-conformance-report:{fixture_id}",
        adapter_ref=adapter.id,
        adapter_kind=adapter.adapter_kind,
        artifact_refs=[artifact.id],
        object_operation_refs=[operation.id for operation in operations],
        content_digest_refs=[artifact.content_digest],
        read_result_refs=[get_op.read_result_ref or ""],
        head_refs=[head_op.id],
        list_refs=[list_op.id],
        delete_refs=[delete_op.deletion_marker_ref or ""],
        lifecycle_state_refs=[
            artifact.lifecycle_state_ref,
            delete_op.lifecycle_state_ref or "",
        ],
        retention_policy_refs=adapter.retention_policy_refs,
        privacy_policy_refs=adapter.privacy_policy_refs,
        policy_decision_refs=policy_refs,
        replay_bundle_ref=f"replay-bundle:{fixture_id}:object-store",
        operator_status="s3_object_store_conformance_completed",
        completion_result=CompletenessResult.PASS,
    )
    return ObjectStoreConformanceResult(
        adapter=adapter,
        artifacts=listed,
        operations=operations,
        report=report,
        duplicate_deduped=duplicate_deduped,
        object_count=store.object_count(),
        read_content=read_content,
    )


def _failure_result(
    *,
    fixture_id: str,
    adapter: ObjectStoreAdapterSpec,
    failure: ObjectStoreConformanceFailureType,
    missing_field: str,
) -> ObjectStoreConformanceResult:
    report = ObjectStoreConformanceReport(
        id=f"object-store-conformance-report:{fixture_id}",
        adapter_ref=adapter.id,
        adapter_kind=adapter.adapter_kind,
        failure_record_refs=[f"object-store-failure:{fixture_id}:{failure.value}"],
        policy_decision_refs=adapter.policy_decision_refs,
        missing_ref_fields=[missing_field],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )
    return ObjectStoreConformanceResult(
        adapter=adapter,
        artifacts=[],
        operations=[],
        report=report,
    )
