from __future__ import annotations

from veracrawl.cli.object_store import ObjectStoreFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult, ObjectStoreAdapterKind


def assert_object_store_success(report: ObjectStoreFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "s3_object_store_conformance_completed"
    assert report.adapter_ref
    assert report.adapter_kind == ObjectStoreAdapterKind.S3_COMPATIBLE
    assert report.artifact_refs
    assert report.object_operation_refs
    assert report.content_digest_refs
    assert report.read_result_refs
    assert report.head_refs
    assert report.list_refs
    assert report.delete_refs
    assert report.lifecycle_state_refs
    assert report.retention_policy_refs
    assert report.privacy_policy_refs
    assert report.policy_decision_refs
    assert report.replay_bundle_ref
    assert report.object_count == 0


def assert_object_store_runtime_unavailable(report: ObjectStoreFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.operator_status == "s3_object_store_runtime_unavailable"
    assert report.adapter_ref
    assert report.adapter_kind == ObjectStoreAdapterKind.S3_COMPATIBLE
    assert report.contract_only_refs
    assert not report.object_operation_refs


def assert_object_store_negative(
    report: ObjectStoreFixtureRunReport,
    *,
    operator_status: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_record_refs
    assert report.missing_ref_fields
