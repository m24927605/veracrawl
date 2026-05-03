from __future__ import annotations

from pathlib import Path

from veracrawl.contracts.enums import (
    CompletenessResult,
    ProductionPersistenceFailureType,
)
from veracrawl.control.production_persistence import run_production_persistence_runtime_fixture
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


def test_production_persistence_success_survives_reopen(tmp_path: Path) -> None:
    result = run_production_persistence_runtime_fixture(
        fixture_id="production-persistence-wiring-success",
        scenario="success",
        profile="target",
        store=ReferencePersistenceStore(tmp_path),
    )

    report = result.report
    assert report.completion_result == CompletenessResult.PASS
    assert report.reloaded is True
    assert report.canonical_state_refs
    assert report.event_cursor_ref
    assert report.outbox_refs
    assert report.artifact_refs
    assert report.queue_operation_refs
    assert report.lease_refs
    assert result.event_count == len(report.event_refs)


def test_production_persistence_duplicate_replay_does_not_duplicate_events_or_outbox(
    tmp_path: Path,
) -> None:
    result = run_production_persistence_runtime_fixture(
        fixture_id="production-persistence-idempotent-replay",
        scenario="idempotent-replay",
        profile="target",
        store=ReferencePersistenceStore(tmp_path),
    )

    assert result.report.completion_result == CompletenessResult.PASS
    assert result.report.duplicate_deduped is True
    assert result.event_count == result.pre_duplicate_event_count
    assert result.outbox_count == result.pre_duplicate_outbox_count


def test_production_persistence_queue_recovery_records_failure_and_recovery(
    tmp_path: Path,
) -> None:
    result = run_production_persistence_runtime_fixture(
        fixture_id="production-persistence-queue-recovery",
        scenario="queue-recovery",
        profile="target",
        store=ReferencePersistenceStore(tmp_path),
    )

    report = result.report
    assert report.completion_result == CompletenessResult.PASS
    assert report.failure_record_refs
    assert report.recovery_action_refs
    assert any(":dead_letter:" in ref for ref in report.queue_operation_refs)


def test_production_persistence_negative_scenarios_return_typed_failures(
    tmp_path: Path,
) -> None:
    result = run_production_persistence_runtime_fixture(
        fixture_id="production-persistence-event-gap",
        scenario="event-gap",
        profile="target",
        store=ReferencePersistenceStore(tmp_path),
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == ProductionPersistenceFailureType.EVENT_GAP
    assert result.report.missing_ref_fields == ["event_cursor_ref"]
