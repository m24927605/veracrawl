from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    AgentRecommendationSubject,
    CompletenessResult,
    TargetRuntimeFailureType,
    TargetRuntimeStatus,
    TargetWebsitePattern,
)
from veracrawl.contracts.target_runtime import (
    TARGET_RUNTIME_MINIMUM_PATTERN_COUNT,
    TargetAIRecommendationRecord,
    TargetCrawlPatternRecord,
    TargetRuntimeFixtureManifest,
    TargetRuntimeReport,
)


def _pattern_record(**overrides: object) -> TargetCrawlPatternRecord:
    data: dict[str, object] = {
        "id": "pattern:success:static",
        "run_ref": "run:success",
        "website_pattern": TargetWebsitePattern.STATIC,
        "frontier_item_refs": ["frontier:success:static"],
        "source_observation_refs": ["source-observation:success:static"],
        "source_adapter_result_refs": ["source-result:success:static"],
        "extraction_result_refs": ["extraction:success:static"],
        "accepted_output_refs": ["output:success:static"],
        "evidence_refs": ["evidence:success:static"],
        "verification_refs": ["verification:success:static"],
        "graph_refs": ["graph:success:static"],
        "policy_decision_refs": ["policy:success:source"],
        "command_record_refs": ["command:success"],
        "event_cursor_refs": ["event-cursor:success"],
        "outbox_refs": ["outbox:success"],
        "artifact_refs": ["artifact:success:static"],
        "replay_refs": ["replay:success"],
        "operator_visible_refs": ["operator:success:static"],
        "pattern_specific_refs": {"fixture_ref": "fixture:success:static"},
        "result": CompletenessResult.PASS,
    }
    data.update(overrides)
    return TargetCrawlPatternRecord.model_validate(data)


def test_passing_pattern_record_requires_all_runtime_refs() -> None:
    record = _pattern_record()
    assert record.result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        _pattern_record(evidence_refs=[])


def test_ai_recommendation_rejects_framework_native_state() -> None:
    record = TargetAIRecommendationRecord(
        id="target-ai:success:plan",
        run_ref="run:success",
        subject=AgentRecommendationSubject.CRAWL_PLAN,
        recommendation_ref="agent-recommendation:success:plan",
        accepted=True,
        policy_decision_refs=["policy:success:agent"],
        tool_call_refs=["tool-call:success:plan"],
        trace_refs=["trace:success:plan"],
        result=CompletenessResult.PASS,
    )
    assert record.framework_native_state_refs == []
    with pytest.raises(ValidationError):
        TargetAIRecommendationRecord(
            id="target-ai:bad:plan",
            run_ref="run:bad",
            subject=AgentRecommendationSubject.CRAWL_PLAN,
            recommendation_ref="agent-recommendation:bad:plan",
            accepted=True,
            policy_decision_refs=["policy:bad:agent"],
            tool_call_refs=["tool-call:bad:plan"],
            trace_refs=["trace:bad:plan"],
            framework_native_state_refs=["langgraph-state:bad"],
            result=CompletenessResult.PASS,
        )


def test_complete_runtime_report_requires_pattern_and_replay_refs() -> None:
    patterns = list(TargetWebsitePattern)[:TARGET_RUNTIME_MINIMUM_PATTERN_COUNT]
    report_data: dict[str, object] = {
        "id": "target-runtime-report:success",
        "fixture_id": "target-runtime-success",
        "run_ref": "run:success",
        "objective_ref": "objective:success",
        "plan_ref": "plan:success",
        "status": TargetRuntimeStatus.COMPLETE,
        "completion_result": CompletenessResult.PASS,
        "covered_patterns": patterns,
        "pattern_record_refs": ["pattern:success"],
        "accepted_output_refs": ["output:success"],
        "evidence_refs": ["evidence:success"],
        "verification_refs": ["verification:success"],
        "graph_refs": ["graph:success"],
        "export_receipt_refs": ["export:success"],
        "output_manifest_refs": ["output-manifest:success"],
        "policy_decision_refs": ["policy:success"],
        "command_record_refs": ["command:success"],
        "event_cursor_refs": ["event-cursor:success"],
        "outbox_refs": ["outbox:success"],
        "artifact_refs": ["artifact:success"],
        "ai_recommendation_refs": ["target-ai:success"],
        "privacy_lifecycle_refs": ["privacy:success"],
        "replay_bundle_ref": "replay:success",
        "operator_status": "target_runtime_completed",
    }
    report = TargetRuntimeReport.model_validate(report_data)
    assert report.status == TargetRuntimeStatus.COMPLETE
    report_data["replay_bundle_ref"] = None
    with pytest.raises(ValidationError):
        TargetRuntimeReport.model_validate(report_data)


def test_negative_fixture_manifest_requires_failure_type() -> None:
    with pytest.raises(ValidationError):
        TargetRuntimeFixtureManifest(
            id="target-runtime-policy-denied",
            scenario="target-runtime-policy-denied",
            profile_refs=["target"],
            expected_status=TargetRuntimeStatus.BLOCKED,
            expected_completion_result=CompletenessResult.FAIL,
            expected_operator_status=TargetRuntimeFailureType.POLICY_DENIED.value,
            negative_case=True,
        )
