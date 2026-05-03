from __future__ import annotations

from veracrawl.contracts.enums import (
    CompletenessResult,
    OpsReplayObservabilityFailureType,
)
from veracrawl.ops.replay_observability_runtime import (
    run_ops_replay_observability_runtime,
)


def test_ops_runtime_success_connects_publication_worker_ops_and_observability() -> None:
    result = run_ops_replay_observability_runtime(
        fixture_id="unit-ops-runtime",
        scenario="ops-runtime-review-replay-success",
    )
    report = result.report
    assert report.completion_result == CompletenessResult.PASS
    assert result.publication is not None
    assert result.worker_orchestration is not None
    assert result.ops_console is not None
    assert result.observability is not None
    assert report.result_publication_export_report_ref
    assert report.worker_orchestration_runtime_report_ref
    assert report.ops_console_report_ref
    assert report.observability_report_ref
    assert report.run_control_action_refs
    assert report.review_item_refs
    assert report.evidence_review_refs
    assert report.replay_audit_view_refs
    assert report.graph_debug_refs
    assert report.export_status_refs
    assert report.withdrawal_status_refs
    assert report.recovery_action_refs
    assert report.failure_record_refs
    assert report.dr_restore_report_refs
    assert report.quality_report_refs
    assert report.dashboard_snapshot_refs
    assert report.alert_record_refs
    assert report.runbook_action_refs
    assert report.cost_metric_refs
    assert report.observability_signal_refs
    assert report.metric_sample_refs
    assert report.trace_span_refs
    assert report.redaction_map_refs
    assert report.replay_bundle_ref


def test_ops_runtime_success_variants_have_operator_statuses() -> None:
    incident = run_ops_replay_observability_runtime(
        fixture_id="unit-incident",
        scenario="ops-runtime-incident-recovery-success",
    ).report
    cost = run_ops_replay_observability_runtime(
        fixture_id="unit-cost",
        scenario="ops-runtime-cost-alert-success",
    ).report
    assert incident.operator_status == "ops_replay_observability_incident_recovered"
    assert cost.operator_status == "ops_replay_observability_cost_alert_completed"


def test_ops_runtime_dependency_failures_are_typed() -> None:
    expectations = {
        "ops-runtime-missing-publication": (
            OpsReplayObservabilityFailureType.MISSING_PUBLICATION,
            "result_publication_export_report_ref",
        ),
        "ops-runtime-missing-worker-orchestration": (
            OpsReplayObservabilityFailureType.MISSING_WORKER_ORCHESTRATION,
            "worker_orchestration_runtime_report_ref",
        ),
        "ops-runtime-missing-ops-console": (
            OpsReplayObservabilityFailureType.MISSING_OPS_CONSOLE,
            "ops_console_report_ref",
        ),
        "ops-runtime-missing-observability": (
            OpsReplayObservabilityFailureType.MISSING_OBSERVABILITY,
            "observability_report_ref",
        ),
    }
    for scenario, (failure, missing) in expectations.items():
        report = run_ops_replay_observability_runtime(
            fixture_id=scenario,
            scenario=scenario,
        ).report
        assert report.completion_result == CompletenessResult.FAIL
        assert report.failure_type == failure
        assert missing in report.missing_ref_fields


def test_ops_runtime_operator_boundary_failures_are_typed() -> None:
    expectations = {
        "ops-runtime-stale-dashboard": (
            OpsReplayObservabilityFailureType.STALE_DASHBOARD,
            "stale_dashboard_refs",
        ),
        "ops-runtime-unresolved-recovery": (
            OpsReplayObservabilityFailureType.UNRESOLVED_RECOVERY,
            "unresolved_recovery_refs",
        ),
        "ops-runtime-unsafe-operator-action": (
            OpsReplayObservabilityFailureType.UNSAFE_OPERATOR_ACTION,
            "unsafe_operator_action_refs",
        ),
        "ops-runtime-replay-mismatch": (
            OpsReplayObservabilityFailureType.REPLAY_MISMATCH,
            "replay_gap_refs",
        ),
    }
    for scenario, (failure, attr) in expectations.items():
        report = run_ops_replay_observability_runtime(
            fixture_id=scenario,
            scenario=scenario,
        ).report
        assert report.completion_result == CompletenessResult.FAIL
        assert report.failure_type == failure
        assert getattr(report, attr)
