from __future__ import annotations

from veracrawl.cli.queue_broker import QueueBrokerFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult, QueueBrokerAdapterKind


def assert_queue_broker_success(report: QueueBrokerFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "redis_broker_conformance_completed"
    assert report.adapter_ref
    assert report.adapter_kind == QueueBrokerAdapterKind.REDIS
    assert report.queue_topology_ref
    assert report.queue_item_refs
    assert report.broker_operation_refs
    assert report.lease_refs
    assert report.heartbeat_refs
    assert report.ack_refs
    assert report.nack_refs
    assert report.dead_letter_refs
    assert report.fencing_token_refs
    assert report.retry_refs
    assert report.fairness_scope_refs
    assert report.backpressure_signal_refs
    assert report.policy_decision_refs
    assert report.replay_bundle_ref


def assert_queue_broker_runtime_unavailable(report: QueueBrokerFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.operator_status == "redis_broker_runtime_unavailable"
    assert report.adapter_ref
    assert report.adapter_kind == QueueBrokerAdapterKind.REDIS
    assert report.contract_only_refs
    assert not report.broker_operation_refs
    assert not report.lease_refs


def assert_queue_broker_negative(
    report: QueueBrokerFixtureRunReport,
    *,
    operator_status: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_record_refs
    assert report.missing_ref_fields
