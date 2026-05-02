from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.artifact import (
    ObjectStoreAdapterSpec,
    ObjectStoreConformanceReport,
    ObjectStoreFixtureManifest,
    ObjectStoreOperationRecord,
)
from veracrawl.contracts.enums import (
    CompletenessResult,
    ObjectStoreAdapterKind,
    ObjectStoreCapability,
    ObjectStoreConformanceFailureType,
    ObjectStoreOperation,
)


def test_object_store_adapter_requires_all_capabilities() -> None:
    spec = ObjectStoreAdapterSpec(
        id="object-store-adapter:unit:s3",
        adapter_kind=ObjectStoreAdapterKind.S3_COMPATIBLE,
        capability_refs=list(ObjectStoreCapability),
        bucket_ref="bucket:unit",
        namespace_ref="prefix:unit",
        content_addressing_supported=True,
        digest_verification_supported=True,
        lifecycle_supported=True,
        retention_policy_refs=["retention:unit"],
        privacy_policy_refs=["privacy:unit"],
        policy_decision_refs=["policy:unit"],
    )
    assert spec.adapter_kind == ObjectStoreAdapterKind.S3_COMPATIBLE
    with pytest.raises(ValidationError):
        ObjectStoreAdapterSpec(
            id="object-store-adapter:bad:s3",
            adapter_kind=ObjectStoreAdapterKind.S3_COMPATIBLE,
            capability_refs=[ObjectStoreCapability.PUT],
            bucket_ref="bucket:bad",
            namespace_ref="prefix:bad",
            content_addressing_supported=True,
            digest_verification_supported=False,
            lifecycle_supported=True,
            retention_policy_refs=["retention:bad"],
            privacy_policy_refs=["privacy:bad"],
            policy_decision_refs=["policy:bad"],
        )


def test_object_store_get_requires_read_result_ref() -> None:
    with pytest.raises(ValidationError):
        ObjectStoreOperationRecord(
            id="object-store-operation:bad",
            adapter_ref="object-store-adapter:unit:s3",
            operation=ObjectStoreOperation.GET,
            artifact_ref="runtime-artifact:bad",
            object_key_ref="object-key:bad",
            content_digest_ref="digest:bad",
            size_bytes=10,
            etag_ref="etag:bad",
            lifecycle_state_ref="lifecycle:bad:active",
            retention_policy_ref="retention:unit",
            privacy_policy_ref="privacy:unit",
            policy_decision_refs=["policy:unit"],
        )


def test_pass_object_store_report_requires_operational_refs() -> None:
    with pytest.raises(ValidationError):
        ObjectStoreConformanceReport(
            id="object-store-conformance-report:bad",
            adapter_ref="object-store-adapter:unit:s3",
            adapter_kind=ObjectStoreAdapterKind.S3_COMPATIBLE,
            operator_status="s3_object_store_conformance_completed",
            completion_result=CompletenessResult.PASS,
        )


def test_runtime_unavailable_object_store_report_requires_contract_refs() -> None:
    report = ObjectStoreConformanceReport(
        id="object-store-conformance-report:runtime",
        adapter_ref="object-store-adapter:unit:s3",
        adapter_kind=ObjectStoreAdapterKind.S3_COMPATIBLE,
        contract_only_refs=["runtime:object-store:endpoint-required"],
        operator_status="s3_object_store_runtime_unavailable",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    with pytest.raises(ValidationError):
        ObjectStoreConformanceReport(
            id="object-store-conformance-report:runtime-bad",
            adapter_ref="object-store-adapter:unit:s3",
            adapter_kind=ObjectStoreAdapterKind.S3_COMPATIBLE,
            operator_status="s3_object_store_runtime_unavailable",
            completion_result=CompletenessResult.NEEDS_REVIEW,
        )


def test_negative_object_store_fixture_requires_failure_type() -> None:
    with pytest.raises(ValidationError):
        ObjectStoreFixtureManifest(
            id="object-store-missing-digest",
            scenario="object-store-missing-digest",
            profile_refs=["target"],
            expected_completion_result="fail",
            expected_operator_status="object_store_missing_digest",
            negative_case=True,
        )
    manifest = ObjectStoreFixtureManifest(
        id="object-store-missing-digest",
        scenario="object-store-missing-digest",
        profile_refs=["target"],
        expected_completion_result="fail",
        expected_operator_status="object_store_missing_digest",
        expected_failure_type=ObjectStoreConformanceFailureType.OBJECT_STORE_MISSING_DIGEST,
        negative_case=True,
    )
    assert manifest.expected_failure_type == (
        ObjectStoreConformanceFailureType.OBJECT_STORE_MISSING_DIGEST
    )
