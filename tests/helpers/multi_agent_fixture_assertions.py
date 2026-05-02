from __future__ import annotations

from veracrawl.cli.agents import MultiAgentFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_multi_agent_success(report: MultiAgentFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "multi_agent_repair_completed"
    assert report.workflow_ref
    assert report.handoff_refs
    assert report.coordination_decision_refs
    assert report.repair_signal_refs
    assert report.agent_action_trace_refs
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs


def assert_multi_agent_negative(
    report: MultiAgentFixtureRunReport,
    *,
    operator_status: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_report_refs
    assert report.missing_ref_fields
    assert not report.workflow_ref
