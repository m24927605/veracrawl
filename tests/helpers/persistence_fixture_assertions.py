from __future__ import annotations

from veracrawl.cli.persistence import PersistenceFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_persistence_success(report: PersistenceFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "persistence_queue_runtime_completed"
    assert report.adapter_ref
    assert report.transaction_ref
    assert report.command_record_refs
    assert report.idempotency_record_refs
    assert report.event_cursor_ref
    assert report.outbox_refs
    assert report.artifact_refs
    assert report.queue_operation_refs
    assert report.lease_refs
    assert report.policy_decision_refs
    assert report.replay_bundle_ref


def assert_persistence_negative(
    report: PersistenceFixtureRunReport,
    *,
    operator_status: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_record_refs
    assert report.missing_ref_fields
