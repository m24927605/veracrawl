from __future__ import annotations

from veracrawl.contracts.enums import OwnerService
from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_ops_contracts_are_registered() -> None:
    expected = {
        "ReviewItem",
        "ReplayAuditView",
        "FailureRecord",
        "RecoveryAction",
        "DRRestorePlan",
        "DRRestoreRun",
        "DRRestoreReport",
        "ObservabilitySignal",
        "MetricSample",
        "TraceSpan",
        "AlertRecord",
        "RunbookAction",
        "ObservabilityReport",
        "QualityReport",
        "OpsDashboardSnapshot",
        "OpsConsoleReport",
        "OpsFixtureManifest",
        "DRRestoreFixtureManifest",
        "ObservabilityFixtureManifest",
    }
    assert expected.issubset(FOUNDATION_CONTRACTS)
    assert validate_registry().ok


def test_ops_commands_and_events_are_registered() -> None:
    expected_commands = {
        "record_review_item": "review_item_recorded",
        "record_replay_audit_view": "replay_audit_view_recorded",
        "record_failure_record": "failure_recorded",
        "record_recovery_action": "recovery_action_recorded",
        "record_dr_restore_plan": "dr_restore_plan_recorded",
        "record_dr_restore_run": "dr_restore_run_recorded",
        "record_dr_restore_report": "dr_restore_reported",
        "record_dr_restore_fixture_manifest": "dr_restore_fixture_manifest_recorded",
        "record_observability_signal": "observability_signal_recorded",
        "record_metric_sample": "metric_sample_recorded",
        "record_trace_span": "trace_span_recorded",
        "record_alert_record": "alert_recorded",
        "record_runbook_action": "runbook_action_recorded",
        "record_observability_report": "observability_reported",
        "record_observability_fixture_manifest": "observability_fixture_manifest_recorded",
        "record_quality_report": "quality_report_recorded",
        "record_ops_dashboard_snapshot": "ops_dashboard_snapshot_recorded",
        "record_ops_console_report": "ops_console_reported",
    }
    for command_type, emitted_event in expected_commands.items():
        assert command_type in COMMAND_TYPES
        assert emitted_event in COMMAND_TYPES[command_type].emitted_event_types
        assert emitted_event in EVENT_TYPES


def test_ops_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["ops"]
    assert area.owner_service == OwnerService.OPS
    assert area.coverage_status == "materialized"
    assert "FailureRecord" in area.materialized_contract_refs
    assert "DRRestoreReport" in area.materialized_contract_refs
    assert "ObservabilityReport" in area.materialized_contract_refs
    assert not area.placeholder_contract_refs
    assert area.followup_spec_gate is None


def test_ops_fixtures_are_registered() -> None:
    expected = {
        "review-console-success",
        "replay-audit-success",
        "quality-dashboard-success",
        "missing-review-evidence",
        "unresolved-failure-without-recovery",
        "stale-dashboard-projection",
        "unsafe-recovery-without-review",
        "observability-success",
        "observability-runtime-unavailable",
        "observability-missing-metrics",
    }
    assert expected.issubset(FIXTURE_ORACLES)
    assert not FIXTURE_ORACLES["review-console-success"].negative_case
    assert FIXTURE_ORACLES["unsafe-recovery-without-review"].negative_case
