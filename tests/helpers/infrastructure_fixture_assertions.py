from __future__ import annotations

from veracrawl.cli.infrastructure import RuntimeInfrastructureFixtureRunReport
from veracrawl.contracts.enums import (
    CompletenessResult,
    RuntimeInfrastructureAdapterFamily,
)


def assert_infrastructure_success(report: RuntimeInfrastructureFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "operational_infrastructure_completed"
    assert set(report.live_adapter_families) == set(RuntimeInfrastructureAdapterFamily)
    assert report.persistence_report_refs
    assert report.queue_broker_report_refs
    assert report.object_store_report_refs
    assert report.persistence_adapter_refs
    assert report.queue_broker_adapter_refs
    assert report.object_store_adapter_refs
    assert report.transaction_refs
    assert report.command_record_refs
    assert report.idempotency_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.queue_topology_refs
    assert report.queue_item_refs
    assert report.broker_operation_refs
    assert report.queue_operation_refs
    assert report.lease_refs
    assert report.heartbeat_refs
    assert report.ack_refs
    assert report.nack_refs
    assert report.dead_letter_refs
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


def assert_infrastructure_runtime_unavailable(
    report: RuntimeInfrastructureFixtureRunReport,
) -> None:
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.operator_status == "operational_infrastructure_runtime_unavailable"
    assert report.contract_only_refs
    assert not report.persistence_report_refs


def assert_infrastructure_negative(
    report: RuntimeInfrastructureFixtureRunReport,
    *,
    operator_status: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_record_refs
    assert report.missing_ref_fields
