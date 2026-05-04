from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.production_grade import (
    AcquisitionAttemptRecord,
    AuthorizedSourceAccessRecord,
    CandidateSourceTarget,
    CrawlBound,
    CrawlDiscoveryPlan,
    DiscoveryApprovalDecision,
    DiscoveryEntryPoint,
    FalseReadyGuard,
    ProductionGateReport,
    ProductionGradeCapabilityMatrix,
    ProductionGradeClosureManifest,
    ProductionGradeReleaseReport,
    ProductionSourceProfile,
    ReleaseBlocker,
    ReleaseDecision,
)


def _source(**overrides: object) -> ProductionSourceProfile:
    data: dict[str, object] = {
        "id": "source:example",
        "site_name": "Example",
        "allowed_origin": "https://example.com",
        "entry_point_url": "https://example.com/products/1",
        "discovery_methods": ["direct_product_url"],
        "required_evidence_types": ["identity", "price", "availability"],
        "robots_policy_ref": "policy:robots",
        "scope_policy_ref": "policy:scope",
    }
    data.update(overrides)
    return ProductionSourceProfile(**data)


def _manifest(**overrides: object) -> ProductionGradeClosureManifest:
    data: dict[str, object] = {
        "id": "fixture",
        "scenario": "success",
        "gate_type": "discovery_planning",
        "profile_refs": ["production"],
        "objective": "Plan a generic source-backed crawl.",
        "source_profiles": [_source()],
        "crawl_bound": CrawlBound(id="crawl-bound:fixture"),
        "expected_completion_result": CompletenessResult.PASS,
        "expected_operator_status": "production_discovery_planning_completed",
    }
    data.update(overrides)
    return ProductionGradeClosureManifest(**data)


def _report(**overrides: object) -> ProductionGateReport:
    data: dict[str, object] = {
        "id": "production-gate-report:fixture",
        "fixture_id": "fixture",
        "gate_type": "discovery_planning",
        "run_ref": "run:fixture",
        "capability_refs": ["capability:discovery_planning:objective_interpretation"],
        "source_profile_refs": ["source:example"],
        "model_call_trace_refs": ["model-call:fixture"],
        "agent_action_trace_refs": ["agent-action:fixture"],
        "tool_call_trace_refs": ["tool:fixture"],
        "context_bundle_trace_refs": ["context:fixture"],
        "evidence_packet_refs": ["evidence-packet:fixture"],
        "verification_decision_refs": ["verification:fixture"],
        "publication_gate_refs": ["publication-gate:fixture"],
        "policy_decision_refs": ["policy:fixture"],
        "command_record_refs": ["command:fixture"],
        "event_cursor_refs": ["event:fixture"],
        "outbox_refs": ["outbox:fixture"],
        "replay_bundle_refs": ["replay:fixture"],
        "metrics": {"source_profile_count": 1},
        "operator_status": "production_discovery_planning_completed",
        "completion_result": CompletenessResult.PASS,
    }
    data.update(overrides)
    return ProductionGateReport(**data)


def test_source_profile_requires_in_scope_entry_point() -> None:
    assert _source().entry_point_url == "https://example.com/products/1"
    with pytest.raises(ValidationError):
        _source(entry_point_url="https://other.example.com/products/1")


def test_manifest_requires_production_profile_and_non_release_sources() -> None:
    assert _manifest().profile_refs == ["production"]
    with pytest.raises(ValidationError):
        _manifest(profile_refs=["target"])
    with pytest.raises(ValidationError):
        _manifest(source_profiles=[])


def test_discovery_plan_requires_model_agent_tool_context_and_replay_refs() -> None:
    plan = CrawlDiscoveryPlan(
        id="crawl-discovery-plan:fixture",
        fixture_id="fixture",
        objective_text="Plan a crawl.",
        source_profile_refs=["source:example"],
        entry_point_refs=["entry-point:example"],
        crawl_bound_ref="crawl-bound:fixture",
        evidence_requirement_refs=["evidence-requirement:identity"],
        approval_decision_ref="approval:fixture",
        model_call_trace_refs=["model-call:fixture"],
        agent_action_trace_refs=["agent-action:fixture"],
        tool_call_trace_refs=["tool:fixture"],
        context_bundle_trace_refs=["context:fixture"],
        policy_decision_refs=["policy:fixture"],
        command_record_refs=["command:fixture"],
        event_cursor_refs=["event:fixture"],
        outbox_refs=["outbox:fixture"],
        replay_bundle_ref="replay:fixture",
    )
    assert plan.completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        CrawlDiscoveryPlan(
            **{
                **plan.model_dump(),
                "model_call_trace_refs": [],
            }
        )


def test_candidate_source_target_and_entry_point_require_ai_policy_replay_refs() -> None:
    entry_point = DiscoveryEntryPoint(
        id="discovery-entry-point:fixture:source",
        fixture_id="fixture",
        source_profile_ref="source:example",
        url="https://example.com/products/1",
        discovery_method="direct_product_url",
        policy_decision_refs=["policy:fixture"],
        model_call_trace_refs=["model-call:fixture"],
        agent_action_trace_refs=["agent-action:fixture"],
        tool_call_trace_refs=["tool:fixture"],
        context_bundle_trace_refs=["context:fixture"],
        command_record_refs=["command:fixture"],
        event_cursor_refs=["event:fixture"],
        outbox_refs=["outbox:fixture"],
        replay_bundle_ref="replay:fixture",
    )
    assert entry_point.url.startswith("https://")
    target = CandidateSourceTarget(
        id="candidate-source-target:fixture:source",
        fixture_id="fixture",
        source_profile_ref="source:example",
        site_name="Example",
        allowed_origin="https://example.com",
        entry_point_refs=[entry_point.id],
        discovery_method_refs=["discovery-method:direct_product_url"],
        evidence_requirement_refs=["evidence-requirement:price"],
        crawl_bound_ref="crawl-bound:fixture",
        policy_decision_refs=["policy:fixture"],
        model_call_trace_refs=["model-call:fixture"],
        agent_action_trace_refs=["agent-action:fixture"],
        tool_call_trace_refs=["tool:fixture"],
        context_bundle_trace_refs=["context:fixture"],
        command_record_refs=["command:fixture"],
        event_cursor_refs=["event:fixture"],
        outbox_refs=["outbox:fixture"],
        replay_bundle_ref="replay:fixture",
    )
    assert target.entry_point_refs == [entry_point.id]
    with pytest.raises(ValidationError):
        CandidateSourceTarget(
            **{
                **target.model_dump(),
                "model_call_trace_refs": [],
            }
        )


def test_discovery_approval_requires_candidate_refs_when_approved() -> None:
    decision = DiscoveryApprovalDecision(
        id="discovery-approval:fixture",
        fixture_id="fixture",
        discovery_plan_ref="crawl-discovery-plan:fixture",
        approved=True,
        candidate_source_target_refs=["candidate-source-target:fixture"],
        approval_policy_refs=["policy:fixture"],
        command_record_refs=["command:fixture"],
        event_cursor_refs=["event:fixture"],
        outbox_refs=["outbox:fixture"],
        replay_bundle_ref="replay:fixture",
    )
    assert decision.approved
    with pytest.raises(ValidationError):
        DiscoveryApprovalDecision(
            **{
                **decision.model_dump(),
                "candidate_source_target_refs": [],
            }
        )


def test_acquisition_attempt_requires_source_evidence_or_limitation_ref() -> None:
    attempt = AcquisitionAttemptRecord(
        id="acquisition-attempt:fixture",
        fixture_id="fixture",
        source_profile_ref="source:example",
        acquisition_mode="http",
        evidence_found=True,
        artifact_refs=["artifact:fixture"],
        content_hash_refs=["hash:fixture"],
        source_anchor_refs=["source-anchor:fixture"],
        policy_decision_refs=["policy:fixture"],
        command_record_refs=["command:fixture"],
        event_cursor_refs=["event:fixture"],
        outbox_refs=["outbox:fixture"],
        replay_bundle_ref="replay:fixture",
    )
    assert attempt.evidence_found
    with pytest.raises(ValidationError):
        AcquisitionAttemptRecord(
            **{
                **attempt.model_dump(),
                "evidence_found": False,
                "artifact_refs": [],
                "content_hash_refs": [],
                "source_anchor_refs": [],
                "source_limitation_ref": None,
            }
        )


def test_authorized_source_requires_audit_redacted_artifact_and_replay() -> None:
    record = AuthorizedSourceAccessRecord(
        id="authorized-source-result:fixture",
        fixture_id="fixture",
        source_profile_ref="source:example",
        access_kind="official_api",
        credential_grant_ref="credential-grant:fixture",
        credential_audit_ref="credential-audit:fixture",
        redacted_artifact_refs=["artifact:redacted"],
        source_anchor_refs=["source-anchor:fixture"],
        content_hash_refs=["hash:fixture"],
        policy_decision_refs=["policy:fixture"],
        command_record_refs=["command:fixture"],
        event_cursor_refs=["event:fixture"],
        outbox_refs=["outbox:fixture"],
        replay_bundle_ref="replay:fixture",
    )
    assert record.access_kind == "official_api"
    with pytest.raises(ValidationError):
        AuthorizedSourceAccessRecord(
            **{
                **record.model_dump(),
                "credential_audit_ref": "",
            }
        )


def test_release_report_requires_six_lower_gate_reports() -> None:
    with pytest.raises(ValidationError):
        _report(
            gate_type="production_grade_release",
            source_profile_refs=[],
            lower_gate_report_refs=["production-gate-report:only-one"],
            operator_status="production_grade_release_completed",
        )
    report = _report(
        gate_type="production_grade_release",
        source_profile_refs=[],
        lower_gate_report_refs=[f"production-gate-report:lower:{index}" for index in range(6)],
        operator_status="production_grade_release_completed",
    )
    assert report.completion_result == CompletenessResult.PASS


def test_non_pass_report_requires_blocker_and_diagnostic() -> None:
    with pytest.raises(ValidationError):
        _report(
            completion_result=CompletenessResult.FAIL,
            policy_decision_refs=[],
            release_blocker_refs=[],
            diagnostics=[],
        )
    report = _report(
        completion_result=CompletenessResult.NEEDS_REVIEW,
        release_blocker_refs=["release-blocker:fixture"],
        diagnostics=["blocked source"],
    )
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW


def test_release_artifacts_require_matrix_decision_false_ready_and_replay_refs() -> None:
    blocker = ReleaseBlocker(
        id="release-blocker:fixture:missing-gate",
        fixture_id="fixture",
        blocker_type="missing-gate",
        blocked_ref="production-gate-report:fixture",
        diagnostic="missing gate",
        policy_decision_refs=["policy:fixture"],
        command_record_refs=["command:fixture"],
        event_cursor_refs=["event:fixture"],
        outbox_refs=["outbox:fixture"],
        replay_bundle_ref="replay:fixture",
    )
    guard = FalseReadyGuard(
        id="false-ready-guard:fixture:lower_gate_presence",
        fixture_id="fixture",
        guard_type="lower_gate_presence",
        checked_ref="production-gate-report:fixture",
        triggered=True,
        release_blocker_ref=blocker.id,
        diagnostic_refs=["diagnostic:fixture"],
        policy_decision_refs=["policy:fixture"],
        command_record_refs=["command:fixture"],
        event_cursor_refs=["event:fixture"],
        outbox_refs=["outbox:fixture"],
        replay_bundle_ref="replay:fixture",
    )
    matrix = ProductionGradeCapabilityMatrix(
        id="production-grade-capability-matrix:fixture",
        fixture_id="fixture",
        release_gate_report_ref="production-gate-report:fixture",
        required_gate_types=["discovery_planning"],
        passing_gate_report_refs=[],
        missing_gate_types=["discovery_planning"],
        false_ready_guard_refs=[guard.id],
        policy_decision_refs=["policy:fixture"],
        command_record_refs=["command:fixture"],
        event_cursor_refs=["event:fixture"],
        outbox_refs=["outbox:fixture"],
        replay_bundle_ref="replay:fixture",
        completion_result=CompletenessResult.FAIL,
    )
    decision = ReleaseDecision(
        id="release-decision:fixture",
        fixture_id="fixture",
        release_gate_report_ref="production-gate-report:fixture",
        capability_matrix_ref=matrix.id,
        decision="blocked",
        release_blocker_refs=[blocker.id],
        diagnostics=["missing gate"],
        policy_decision_refs=["policy:fixture"],
        command_record_refs=["command:fixture"],
        event_cursor_refs=["event:fixture"],
        outbox_refs=["outbox:fixture"],
        replay_bundle_ref="replay:fixture",
    )
    report = ProductionGradeReleaseReport(
        id="production-grade-release-report:fixture",
        fixture_id="fixture",
        release_gate_report_ref="production-gate-report:fixture",
        capability_matrix_ref=matrix.id,
        release_decision_ref=decision.id,
        false_ready_guard_refs=[guard.id],
        release_blocker_refs=[blocker.id],
        policy_decision_refs=["policy:fixture"],
        command_record_refs=["command:fixture"],
        event_cursor_refs=["event:fixture"],
        outbox_refs=["outbox:fixture"],
        replay_bundle_refs=["replay:fixture"],
        operator_status="production_grade_release_blocked",
        completion_result=CompletenessResult.FAIL,
        diagnostics=["missing gate"],
    )
    assert report.release_blocker_refs == [blocker.id]
