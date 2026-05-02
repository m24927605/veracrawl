from __future__ import annotations

import pytest

from veracrawl.adapters.object_stores.s3 import (
    S3ObjectStoreAdapter,
    S3RuntimeUnavailableError,
    s3_object_store_adapter_spec,
)
from veracrawl.artifact_lifecycle.object_store_conformance import (
    run_object_store_conformance,
    run_object_store_runtime_unavailable_conformance,
)
from veracrawl.contracts.enums import (
    CompletenessResult,
    ObjectStoreAdapterKind,
    ObjectStoreCapability,
)


def test_s3_object_store_spec_declares_operational_kind() -> None:
    spec = s3_object_store_adapter_spec("unit", ["policy:unit:object-store"])
    assert spec.adapter_kind == ObjectStoreAdapterKind.S3_COMPATIBLE
    assert set(spec.capability_refs) == set(ObjectStoreCapability)
    assert spec.digest_verification_supported is True
    assert spec.lifecycle_supported is True


def test_s3_object_store_requires_endpoint() -> None:
    with pytest.raises(S3RuntimeUnavailableError):
        S3ObjectStoreAdapter(
            "",
            bucket="veracrawl",
            access_key_id="veracrawl",
            secret_access_key="veracrawl-secret",
        )


def test_s3_object_store_rejects_unsafe_bucket_or_namespace() -> None:
    with pytest.raises(ValueError):
        S3ObjectStoreAdapter(
            "http://example.invalid:9000",
            bucket="bad bucket",
            access_key_id="veracrawl",
            secret_access_key="veracrawl-secret",
        )


def test_s3_runtime_unavailable_reports_needs_review() -> None:
    spec = s3_object_store_adapter_spec(
        "s3-object-store-runtime-unavailable",
        ["policy:unit"],
    )
    result = run_object_store_runtime_unavailable_conformance(
        fixture_id="s3-object-store-runtime-unavailable",
        adapter_spec=spec,
    )
    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.operator_status == "s3_object_store_runtime_unavailable"
    assert result.report.contract_only_refs


def test_object_store_negative_scenarios_emit_failures() -> None:
    expectations = {
        "object-store-missing-digest": "object_store_missing_digest",
        "object-store-missing-read-after-write": "object_store_missing_read_after_write",
        "object-store-missing-delete-marker": "object_store_missing_delete_marker",
    }
    for scenario, operator_status in expectations.items():
        spec = s3_object_store_adapter_spec(scenario, [f"policy:{scenario}:object-store"])
        result = run_object_store_conformance(
            fixture_id=scenario,
            scenario=scenario,
            store=None,
            adapter_spec=spec,
        )
        assert result.report.completion_result == CompletenessResult.FAIL
        assert result.report.operator_status == operator_status
        assert result.report.missing_ref_fields
