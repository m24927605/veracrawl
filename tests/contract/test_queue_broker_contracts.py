from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    QueueBrokerAdapterKind,
    QueueBrokerCapability,
    QueueBrokerConformanceFailureType,
    QueueBrokerOperation,
    ScaleQueueName,
)
from veracrawl.contracts.scale import (
    QueueBrokerAdapterSpec,
    QueueBrokerConformanceReport,
    QueueBrokerFixtureManifest,
    QueueBrokerOperationRecord,
)


def test_queue_broker_adapter_requires_all_capabilities() -> None:
    spec = QueueBrokerAdapterSpec(
        id="queue-broker-adapter:unit:redis",
        adapter_kind=QueueBrokerAdapterKind.REDIS,
        queue_names=list(ScaleQueueName),
        capability_refs=list(QueueBrokerCapability),
        visibility_timeout_seconds=30,
        fencing_token_supported=True,
        idempotency_supported=True,
        fairness_scope_refs=["fairness:unit"],
        backpressure_signal_refs=["backpressure:unit"],
        policy_decision_refs=["policy:unit"],
    )
    assert spec.adapter_kind == QueueBrokerAdapterKind.REDIS
    with pytest.raises(ValidationError):
        QueueBrokerAdapterSpec(
            id="queue-broker-adapter:bad:redis",
            adapter_kind=QueueBrokerAdapterKind.REDIS,
            queue_names=[ScaleQueueName.FRONTIER],
            capability_refs=[QueueBrokerCapability.ENQUEUE],
            visibility_timeout_seconds=0,
            fencing_token_supported=False,
            idempotency_supported=True,
            fairness_scope_refs=["fairness:bad"],
            backpressure_signal_refs=["backpressure:bad"],
            policy_decision_refs=["policy:bad"],
        )


def test_leased_broker_operation_requires_fencing_and_visibility_refs() -> None:
    with pytest.raises(ValidationError):
        QueueBrokerOperationRecord(
            id="queue-broker-operation:bad",
            adapter_ref="queue-broker-adapter:unit:redis",
            queue_name=ScaleQueueName.FRONTIER,
            operation=QueueBrokerOperation.ACK,
            queue_item_ref="queue-item:bad",
            lease_ref="lease:bad",
            fairness_scope_refs=["fairness:unit"],
            backpressure_signal_refs=["backpressure:unit"],
            policy_decision_refs=["policy:unit"],
        )


def test_pass_queue_broker_report_requires_operational_refs() -> None:
    with pytest.raises(ValidationError):
        QueueBrokerConformanceReport(
            id="queue-broker-conformance-report:bad",
            adapter_ref="queue-broker-adapter:unit:redis",
            adapter_kind=QueueBrokerAdapterKind.REDIS,
            operator_status="redis_broker_conformance_completed",
            completion_result=CompletenessResult.PASS,
        )


def test_runtime_unavailable_queue_broker_report_requires_contract_refs() -> None:
    report = QueueBrokerConformanceReport(
        id="queue-broker-conformance-report:runtime",
        adapter_ref="queue-broker-adapter:unit:redis",
        adapter_kind=QueueBrokerAdapterKind.REDIS,
        contract_only_refs=["runtime:queue-broker:url-required"],
        operator_status="redis_broker_runtime_unavailable",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    with pytest.raises(ValidationError):
        QueueBrokerConformanceReport(
            id="queue-broker-conformance-report:runtime-bad",
            adapter_ref="queue-broker-adapter:unit:redis",
            adapter_kind=QueueBrokerAdapterKind.REDIS,
            operator_status="redis_broker_runtime_unavailable",
            completion_result=CompletenessResult.NEEDS_REVIEW,
        )


def test_negative_queue_broker_fixture_requires_failure_type() -> None:
    with pytest.raises(ValidationError):
        QueueBrokerFixtureManifest(
            id="broker-missing-heartbeat",
            scenario="broker-missing-heartbeat",
            profile_refs=["target"],
            expected_completion_result="fail",
            expected_operator_status="broker_missing_heartbeat",
            negative_case=True,
        )
    manifest = QueueBrokerFixtureManifest(
        id="broker-missing-heartbeat",
        scenario="broker-missing-heartbeat",
        profile_refs=["target"],
        expected_completion_result="fail",
        expected_operator_status="broker_missing_heartbeat",
        expected_failure_type=QueueBrokerConformanceFailureType.BROKER_MISSING_HEARTBEAT,
        negative_case=True,
    )
    assert manifest.expected_failure_type == (
        QueueBrokerConformanceFailureType.BROKER_MISSING_HEARTBEAT
    )
