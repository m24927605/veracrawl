"""Multi-agent replay validation."""

from __future__ import annotations

from veracrawl.contracts.agent import MultiAgentRepairReport
from veracrawl.contracts.enums import CompletenessResult


def missing_multi_agent_replay_refs(report: MultiAgentRepairReport) -> list[str]:
    required = {
        "workflow_ref": report.workflow_ref,
        "agent_model_adapter_runtime_report_ref": (
            report.agent_model_adapter_runtime_report_ref
        ),
        "live_evidence_verification_runtime_report_ref": (
            report.live_evidence_verification_runtime_report_ref
        ),
        "handoff_refs": report.handoff_refs,
        "coordination_decision_refs": report.coordination_decision_refs,
        "repair_signal_refs": report.repair_signal_refs,
        "agent_action_trace_refs": report.agent_action_trace_refs,
        "controlled_tool_call_refs": report.controlled_tool_call_refs,
        "owner_command_refs": report.owner_command_refs,
        "policy_decision_refs": report.policy_decision_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
        "replay_bundle_ref": report.replay_bundle_ref,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def multi_agent_replay_passes(report: MultiAgentRepairReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_multi_agent_replay_refs(report)
    )
