from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    RepairCaseType,
    RepairOutcome,
)
from veracrawl.contracts.repair_success import (
    RepairAttemptTrace,
    RepairQualityManifest,
    RepairQualityReport,
    RepairQualityThresholds,
    SeededRepairCase,
)


def _case() -> SeededRepairCase:
    return SeededRepairCase(
        id="repair-case:1",
        failure_family=RepairCaseType.EXTRACTION,
        repairable=True,
        expected_outcome=RepairOutcome.REPAIRED,
        input_artifact_refs=["artifact:1"],
        before_evidence_refs=["evidence:before:1"],
        policy_decision_refs=["policy:1"],
        command_record_refs=["command:1"],
        event_cursor_refs=["event-cursor:1"],
        outbox_refs=["outbox:1"],
        replay_bundle_ref="replay:case:1",
        oracle_ref="oracle:1",
    )


def _attempt() -> RepairAttemptTrace:
    return RepairAttemptTrace(
        id="repair-attempt:1",
        case_ref="repair-case:1",
        outcome=RepairOutcome.REPAIRED,
        model_call_trace_refs=["model:1"],
        agent_action_trace_refs=["agent:1"],
        tool_call_trace_refs=["tool:1"],
        context_bundle_trace_refs=["context:1"],
        owner_service_command_refs=["owner-command:1"],
        policy_decision_refs=["policy:1"],
        before_evidence_refs=["evidence:before:1"],
        after_evidence_refs=["evidence:after:1"],
        command_record_refs=["command:1"],
        event_cursor_refs=["event-cursor:1"],
        outbox_refs=["outbox:1"],
        replay_bundle_ref="replay:attempt:1",
    )


def test_repair_quality_threshold_defaults_are_release_blocking() -> None:
    thresholds = RepairQualityThresholds(id="thresholds:1")

    assert thresholds.min_repair_success_rate == 0.80
    assert thresholds.max_unsafe_bypass_rate == 0.0
    assert thresholds.max_unresolved_critical_rate == 0.0


def test_seeded_repair_case_requires_replayable_refs() -> None:
    case = _case()

    assert case.replay_bundle_ref == "replay:case:1"


def test_repaired_attempt_cannot_use_model_only_evidence() -> None:
    with pytest.raises(ValidationError):
        RepairAttemptTrace(
            id="repair-attempt:1",
            case_ref="repair-case:1",
            outcome=RepairOutcome.REPAIRED,
            model_call_trace_refs=["model:1"],
            agent_action_trace_refs=["agent:1"],
            tool_call_trace_refs=["tool:1"],
            context_bundle_trace_refs=["context:1"],
            owner_service_command_refs=["owner-command:1"],
            policy_decision_refs=["policy:1"],
            before_evidence_refs=["evidence:before:1"],
            after_evidence_refs=["evidence:after:1"],
            command_record_refs=["command:1"],
            event_cursor_refs=["event-cursor:1"],
            outbox_refs=["outbox:1"],
            replay_bundle_ref="replay:attempt:1",
            model_only_evidence=True,
        )


def test_ai_assisted_attempt_requires_framework_neutral_traces() -> None:
    with pytest.raises(ValidationError):
        RepairAttemptTrace(
            id="repair-attempt:1",
            case_ref="repair-case:1",
            outcome=RepairOutcome.FAILED_SAFE,
            model_call_trace_refs=[],
            agent_action_trace_refs=["agent:1"],
            tool_call_trace_refs=["tool:1"],
            context_bundle_trace_refs=["context:1"],
            owner_service_command_refs=["owner-command:1"],
            policy_decision_refs=["policy:1"],
            before_evidence_refs=["evidence:before:1"],
            command_record_refs=["command:1"],
            event_cursor_refs=["event-cursor:1"],
            outbox_refs=["outbox:1"],
            replay_bundle_ref="replay:attempt:1",
        )


def test_repair_quality_report_requires_trace_refs_to_pass() -> None:
    attempt = _attempt()
    report = RepairQualityReport(
        id="report:1",
        fixture_id="repair-success-quality",
        run_ref="run:1",
        thresholds_ref="thresholds:1",
        seeded_case_refs=["repair-case:1"],
        repair_attempt_refs=[attempt.id],
        repairable_case_count=1,
        repaired_case_count=1,
        repair_success_rate=1.0,
        model_call_trace_refs=attempt.model_call_trace_refs,
        agent_action_trace_refs=attempt.agent_action_trace_refs,
        tool_call_trace_refs=attempt.tool_call_trace_refs,
        context_bundle_trace_refs=attempt.context_bundle_trace_refs,
        owner_service_command_refs=attempt.owner_service_command_refs,
        before_evidence_refs=attempt.before_evidence_refs,
        after_evidence_refs=attempt.after_evidence_refs,
        policy_decision_refs=attempt.policy_decision_refs,
        command_record_refs=attempt.command_record_refs,
        event_cursor_refs=attempt.event_cursor_refs,
        outbox_refs=attempt.outbox_refs,
        replay_bundle_refs=["replay:case:1", "replay:attempt:1"],
        operator_status="repair_quality_completed",
        completion_result=CompletenessResult.PASS,
    )

    assert report.repair_success_rate == 1.0


def test_repair_quality_manifest_supports_quality_profile() -> None:
    manifest = RepairQualityManifest(
        id="repair-success-quality",
        scenario="repair-success-quality",
        profile_refs=["quality"],
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="repair_quality_completed",
        required_ref_types=["repair_case", "repair_attempt", "replay"],
    )

    assert manifest.thresholds.min_repair_success_rate == 0.80
