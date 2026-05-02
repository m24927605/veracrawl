from __future__ import annotations

from veracrawl.cli.persistence_adapter import PersistenceAdapterFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult, PersistenceAdapterKind


def assert_sqlite_adapter_success(report: PersistenceAdapterFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "sqlite_adapter_conformance_completed"
    assert report.adapter_ref
    assert report.adapter_kind == PersistenceAdapterKind.SQLITE
    assert report.transaction_refs
    assert report.migration_record_refs
    assert report.command_record_refs
    assert report.idempotency_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.artifact_refs
    assert report.queue_operation_refs
    assert report.lease_refs
    assert report.policy_decision_refs
    assert report.replay_bundle_ref


def assert_postgres_contract_only(report: PersistenceAdapterFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.operator_status == "postgres_contract_declared"
    assert report.adapter_ref
    assert report.adapter_kind == PersistenceAdapterKind.POSTGRES_CONTRACT
    assert report.contract_only_refs
    assert not report.transaction_refs
    assert not report.migration_record_refs
    assert not report.event_cursor_refs
    assert not report.outbox_refs


def assert_postgres_adapter_success(report: PersistenceAdapterFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "postgres_adapter_conformance_completed"
    assert report.adapter_ref
    assert report.adapter_kind == PersistenceAdapterKind.POSTGRES
    assert report.transaction_refs
    assert report.migration_record_refs
    assert report.command_record_refs
    assert report.idempotency_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.artifact_refs
    assert report.queue_operation_refs
    assert report.lease_refs
    assert report.policy_decision_refs
    assert report.replay_bundle_ref


def assert_postgres_runtime_unavailable(report: PersistenceAdapterFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.operator_status == "postgres_runtime_unavailable"
    assert report.adapter_ref
    assert report.adapter_kind == PersistenceAdapterKind.POSTGRES
    assert report.contract_only_refs
    assert not report.transaction_refs
    assert not report.migration_record_refs


def assert_persistence_adapter_negative(
    report: PersistenceAdapterFixtureRunReport,
    *,
    operator_status: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_record_refs
    assert report.missing_ref_fields
