"""Replay checks for repair success benchmark records."""

from __future__ import annotations

from veracrawl.contracts.repair_success import (
    RepairAttemptTrace,
    RepairQualityReport,
    SeededRepairCase,
)


def missing_seeded_repair_case_replay_refs(case: SeededRepairCase) -> list[str]:
    missing: list[str] = []
    for field_name in [
        "input_artifact_refs",
        "before_evidence_refs",
        "policy_decision_refs",
        "command_record_refs",
        "event_cursor_refs",
        "outbox_refs",
    ]:
        if not getattr(case, field_name):
            missing.append(field_name)
    if not case.replay_bundle_ref:
        missing.append("replay_bundle_ref")
    return missing


def seeded_repair_case_replay_passes(case: SeededRepairCase) -> bool:
    return not missing_seeded_repair_case_replay_refs(case)


def missing_repair_attempt_replay_refs(attempt: RepairAttemptTrace) -> list[str]:
    missing: list[str] = []
    for field_name in [
        "model_call_trace_refs",
        "agent_action_trace_refs",
        "tool_call_trace_refs",
        "context_bundle_trace_refs",
        "owner_service_command_refs",
        "policy_decision_refs",
        "before_evidence_refs",
        "command_record_refs",
        "event_cursor_refs",
        "outbox_refs",
    ]:
        if not getattr(attempt, field_name):
            missing.append(field_name)
    if not attempt.replay_bundle_ref:
        missing.append("replay_bundle_ref")
    return missing


def repair_attempt_replay_passes(attempt: RepairAttemptTrace) -> bool:
    return not missing_repair_attempt_replay_refs(attempt)


def missing_repair_quality_report_replay_refs(report: RepairQualityReport) -> list[str]:
    missing: list[str] = []
    for field_name in [
        "seeded_case_refs",
        "repair_attempt_refs",
        "model_call_trace_refs",
        "agent_action_trace_refs",
        "tool_call_trace_refs",
        "context_bundle_trace_refs",
        "owner_service_command_refs",
        "before_evidence_refs",
        "after_evidence_refs",
        "policy_decision_refs",
        "command_record_refs",
        "event_cursor_refs",
        "outbox_refs",
        "replay_bundle_refs",
    ]:
        if not getattr(report, field_name):
            missing.append(field_name)
    return missing


def repair_quality_report_replay_passes(report: RepairQualityReport) -> bool:
    return not missing_repair_quality_report_replay_refs(report)
