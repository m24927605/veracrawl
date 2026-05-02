from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    RuntimeInfrastructureAdapterFamily,
    RuntimeInfrastructureFailureType,
)
from veracrawl.contracts.infrastructure import (
    RuntimeInfrastructureFixtureManifest,
    RuntimeInfrastructureReport,
    RuntimeInfrastructureSpec,
)


def _spec() -> RuntimeInfrastructureSpec:
    return RuntimeInfrastructureSpec(
        id="runtime-infrastructure-spec:unit",
        persistence_adapter_ref="persistence-adapter:unit:postgres",
        queue_broker_adapter_ref="queue-broker-adapter:unit:redis",
        object_store_adapter_ref="object-store-adapter:unit:s3",
        required_live_adapter_refs=[
            "persistence-adapter:unit:postgres",
            "queue-broker-adapter:unit:redis",
            "object-store-adapter:unit:s3",
        ],
        policy_decision_refs=["policy:unit:infrastructure"],
    )


def _passing_report() -> RuntimeInfrastructureReport:
    spec = _spec()
    return RuntimeInfrastructureReport(
        id="runtime-infrastructure-report:unit",
        run_ref="run:unit",
        infrastructure_spec_ref=spec.id,
        live_adapter_families=list(RuntimeInfrastructureAdapterFamily),
        persistence_report_refs=["persistence-report:unit"],
        queue_broker_report_refs=["queue-report:unit"],
        object_store_report_refs=["object-report:unit"],
        persistence_adapter_refs=[spec.persistence_adapter_ref],
        queue_broker_adapter_refs=[spec.queue_broker_adapter_ref],
        object_store_adapter_refs=[spec.object_store_adapter_ref],
        transaction_refs=["transaction:unit"],
        command_record_refs=["command-record:unit"],
        idempotency_record_refs=["idempotency:unit"],
        event_cursor_refs=["event-cursor:unit"],
        outbox_refs=["outbox:unit"],
        queue_topology_refs=["queue-topology:unit"],
        queue_item_refs=["queue-item:unit"],
        broker_operation_refs=["broker-operation:unit"],
        queue_operation_refs=["persistent-queue-operation:unit"],
        lease_refs=["lease:unit"],
        heartbeat_refs=["heartbeat:unit"],
        ack_refs=["ack:unit"],
        nack_refs=["nack:unit"],
        dead_letter_refs=["dead-letter:unit"],
        artifact_refs=["artifact:unit"],
        object_operation_refs=["object-operation:unit"],
        content_digest_refs=["digest:unit"],
        read_result_refs=["read:unit"],
        head_refs=["head:unit"],
        list_refs=["list:unit"],
        delete_refs=["delete:unit"],
        lifecycle_state_refs=["lifecycle:unit"],
        retention_policy_refs=["retention:unit"],
        privacy_policy_refs=["privacy:unit"],
        policy_decision_refs=spec.policy_decision_refs,
        replay_bundle_ref="replay-bundle:unit",
        operator_status="operational_infrastructure_completed",
        completion_result=CompletenessResult.PASS,
    )


def test_runtime_infrastructure_spec_requires_all_live_adapter_refs() -> None:
    spec = _spec()
    assert spec.required_live_adapter_refs == [
        "persistence-adapter:unit:postgres",
        "queue-broker-adapter:unit:redis",
        "object-store-adapter:unit:s3",
    ]


def test_passing_runtime_infrastructure_report_requires_cross_adapter_refs() -> None:
    report = _passing_report()
    assert report.completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        RuntimeInfrastructureReport.model_validate(
            report.model_copy(update={"queue_broker_report_refs": []}).model_dump(mode="json")
        )


def test_no_runtime_and_negative_reports_validate() -> None:
    spec = _spec()
    needs_review = RuntimeInfrastructureReport(
        id="runtime-infrastructure-report:no-runtime",
        run_ref="run:no-runtime",
        infrastructure_spec_ref=spec.id,
        policy_decision_refs=spec.policy_decision_refs,
        contract_only_refs=["runtime:infrastructure:live-conformance-not-executed"],
        operator_status="operational_infrastructure_runtime_unavailable",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    assert needs_review.completion_result == CompletenessResult.NEEDS_REVIEW
    failed = RuntimeInfrastructureReport(
        id="runtime-infrastructure-report:missing",
        run_ref="run:missing",
        infrastructure_spec_ref=spec.id,
        failure_record_refs=[
            "runtime-infrastructure-failure:missing:infrastructure_missing_queue_refs"
        ],
        missing_ref_fields=["queue_broker_report_refs"],
        operator_status=RuntimeInfrastructureFailureType.INFRASTRUCTURE_MISSING_QUEUE_REFS.value,
        completion_result=CompletenessResult.FAIL,
    )
    assert failed.missing_ref_fields == ["queue_broker_report_refs"]


def test_fixture_manifest_validates_negative_expectations() -> None:
    manifest = RuntimeInfrastructureFixtureManifest(
        id="infrastructure-missing-object-refs",
        scenario="infrastructure-missing-object-refs",
        profile_refs=["target"],
        expected_completion_result=CompletenessResult.FAIL,
        expected_operator_status="infrastructure_missing_object_refs",
        expected_failure_type=RuntimeInfrastructureFailureType.INFRASTRUCTURE_MISSING_OBJECT_REFS,
        negative_case=True,
    )
    assert manifest.negative_case is True
