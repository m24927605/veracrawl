from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult, OpsDashboardType
from veracrawl.ops.console import run_ops_console


def test_ops_console_success_scenarios_emit_replayable_refs() -> None:
    expected_dashboard_types = {
        "review-console-success": OpsDashboardType.REVIEW,
        "replay-audit-success": OpsDashboardType.REPLAY,
        "quality-dashboard-success": OpsDashboardType.QUALITY,
    }
    for scenario, dashboard_type in expected_dashboard_types.items():
        result = run_ops_console(
            fixture_id=f"unit-{scenario}",
            scenario=scenario,
            policy_decision_refs=["policy:unit:ops"],
        )
        assert result.report.completion_result == CompletenessResult.PASS
        assert result.report.operator_status == "ops_console_completed"
        assert result.review_items
        assert result.replay_audit_views
        assert result.quality_reports
        assert result.dashboard_snapshots[0].dashboard_type == dashboard_type
        assert result.failure_records[0].recovery_action_refs == [result.recovery_actions[0].id]


def test_ops_console_negative_scenarios_emit_failures() -> None:
    expectations = {
        "missing-review-evidence": "missing_review_evidence",
        "unresolved-failure-without-recovery": "unresolved_failure_without_recovery",
        "stale-dashboard-projection": "stale_dashboard_projection",
        "unsafe-recovery-without-review": "unsafe_recovery_without_review",
    }
    for scenario, operator_status in expectations.items():
        result = run_ops_console(
            fixture_id=f"unit-{scenario}",
            scenario=scenario,
            policy_decision_refs=["policy:unit:ops"],
        )
        assert result.report.completion_result == CompletenessResult.FAIL
        assert result.report.operator_status == operator_status
        assert result.failure_records
        assert result.report.missing_ref_fields
