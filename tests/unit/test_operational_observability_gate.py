from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult, ObservabilityFailureType
from veracrawl.runtime_support.observability import (
    run_operational_observability_data_surface_only_gate,
    run_operational_observability_gate,
    run_operational_observability_runtime_unavailable_gate,
)


def test_operational_observability_gate_success_requires_canonical_refs() -> None:
    result = run_operational_observability_gate(
        fixture_id="unit",
        scenario="observability-success",
        telemetry_backend_ref="telemetry-backend:unit",
        collector_handoff_ref="collector-handoff:unit",
    )
    assert result.report.result == CompletenessResult.PASS
    assert result.report.metric_sample_refs
    assert result.report.trace_span_refs
    assert result.report.alert_record_refs
    assert result.report.runbook_action_refs
    assert result.report.telemetry_backend_refs
    assert result.report.collector_handoff_refs
    assert result.report.redaction_map_refs


def test_operational_observability_runtime_unavailable_needs_review() -> None:
    result = run_operational_observability_runtime_unavailable_gate(
        fixture_id="unit-no-runtime"
    )
    assert result.report.result == CompletenessResult.NEEDS_REVIEW
    assert result.report.contract_only_refs
    assert "telemetry_backend_refs" in result.report.missing_ref_fields


def test_operational_observability_data_surface_only_needs_review() -> None:
    result = run_operational_observability_data_surface_only_gate(
        fixture_id="unit-data-surface"
    )
    assert result.report.result == CompletenessResult.NEEDS_REVIEW
    assert result.report.dashboard_snapshot_refs
    assert "metric_sample_refs" in result.report.missing_ref_fields
    assert not result.report.telemetry_backend_refs


def test_operational_observability_negative_scenarios_fail_with_recovery_refs() -> None:
    expectations = {
        "observability-missing-metrics": ObservabilityFailureType.MISSING_METRIC_REFS,
        "observability-missing-traces": ObservabilityFailureType.MISSING_TRACE_REFS,
        "observability-missing-alerts": ObservabilityFailureType.MISSING_ALERT_REFS,
        "observability-missing-runbook": ObservabilityFailureType.MISSING_RUNBOOK_REFS,
        "observability-stale-dashboard-watermark": (
            ObservabilityFailureType.STALE_DASHBOARD_WATERMARK
        ),
        "observability-missing-dr-refs": ObservabilityFailureType.MISSING_DR_REFS,
        "observability-missing-redaction": ObservabilityFailureType.MISSING_REDACTION_REFS,
        "observability-missing-replay": ObservabilityFailureType.MISSING_REPLAY_REFS,
        "observability-secret-leak": ObservabilityFailureType.SECRET_LEAK_DETECTED,
        "observability-unsafe-runbook-without-approval": (
            ObservabilityFailureType.UNSAFE_RUNBOOK_WITHOUT_APPROVAL
        ),
    }
    for scenario, failure in expectations.items():
        result = run_operational_observability_gate(
            fixture_id=scenario,
            scenario=scenario,
            telemetry_backend_ref=None,
            collector_handoff_ref=None,
        )
        assert result.report.result == CompletenessResult.FAIL
        assert result.report.operator_status == failure.value
        assert result.failure_records
        assert result.recovery_actions
