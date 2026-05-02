from __future__ import annotations

from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_operational_observability_contracts_are_registered() -> None:
    for name in [
        "ObservabilitySignal",
        "MetricSample",
        "TraceSpan",
        "AlertRecord",
        "RunbookAction",
        "ObservabilityReport",
        "ObservabilityFixtureManifest",
        "FailureRecord",
        "RecoveryAction",
    ]:
        assert name in FOUNDATION_CONTRACTS
    assert validate_registry().ok


def test_operational_observability_commands_events_and_fixtures_are_registered() -> None:
    expected_commands = {
        "record_observability_signal": "observability_signal_recorded",
        "record_metric_sample": "metric_sample_recorded",
        "record_trace_span": "trace_span_recorded",
        "record_alert_record": "alert_recorded",
        "record_runbook_action": "runbook_action_recorded",
        "record_observability_report": "observability_reported",
        "record_observability_fixture_manifest": "observability_fixture_manifest_recorded",
    }
    for command_type, emitted_event in expected_commands.items():
        assert command_type in COMMAND_TYPES
        assert emitted_event in COMMAND_TYPES[command_type].emitted_event_types
        assert emitted_event in EVENT_TYPES
    for fixture_id in [
        "observability-success",
        "observability-runtime-unavailable",
        "observability-data-surface-only",
        "observability-missing-metrics",
        "observability-missing-traces",
        "observability-missing-alerts",
        "observability-missing-runbook",
        "observability-stale-dashboard-watermark",
        "observability-missing-dr-refs",
        "observability-missing-redaction",
        "observability-missing-replay",
        "observability-secret-leak",
        "observability-unsafe-runbook-without-approval",
    ]:
        assert fixture_id in FIXTURE_ORACLES


def test_operational_observability_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["operational_observability_gate"]
    assert area.coverage_status == "materialized"
    assert "ObservabilityReport" in area.materialized_contract_refs
    assert "DRRestoreReport" in area.materialized_contract_refs
