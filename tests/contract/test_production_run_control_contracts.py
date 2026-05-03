from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    ProductionRunControlFailureType,
    RunLifecycleAction,
    RunStatus,
)
from veracrawl.contracts.objective import (
    ProductionProject,
    ProductionRunControlFixtureManifest,
    ProductionRunControlReport,
    ProductionSiteScope,
    RunApprovalRecord,
    RunBudget,
    RunLifecycleRecord,
    RunPolicySnapshot,
)


def _budget() -> RunBudget:
    return RunBudget(
        id="budget:test",
        project_ref="project:test",
        crawl_limit_refs=["limit:pages"],
        max_pages=10,
        max_depth=2,
        max_runtime_seconds=300,
        policy_decision_refs=["policy:budget"],
    )


def test_project_site_budget_and_policy_snapshot_require_control_refs() -> None:
    assert ProductionProject(
        id="project:test",
        owner_ref="actor:test",
        project_policy_refs=["policy:project"],
        default_budget_ref="budget:test",
    )
    assert ProductionSiteScope(
        id="site:test",
        project_ref="project:test",
        allowed_scope_refs=["scope:authorized"],
        source_policy_refs=["policy:source"],
        robots_policy_ref="policy:robots",
        egress_policy_ref="policy:egress",
    )
    with pytest.raises(ValidationError):
        RunBudget(
            id="budget:bad",
            project_ref="project:test",
            crawl_limit_refs=["limit:pages"],
            max_pages=0,
            max_depth=2,
            max_runtime_seconds=300,
            policy_decision_refs=["policy:budget"],
        )
    with pytest.raises(ValidationError):
        RunPolicySnapshot(
            id="policy-snapshot:test",
            run_ref="run:test",
            project_ref="project:test",
            site_scope_ref="site:test",
            source_policy_refs=[],
            publication_policy_refs=["policy:publication"],
            privacy_policy_ref="policy:privacy",
            egress_policy_ref="policy:egress",
            prompt_taint_policy_ref="policy:prompt",
            budget_ref="budget:test",
            policy_decision_refs=["policy:source"],
        )


def test_approval_and_lifecycle_records_enforce_refs_and_transitions() -> None:
    approved = RunApprovalRecord(
        id="approval:test",
        objective_ref="objective:test",
        plan_ref="plan:test",
        actor_ref="actor:test",
        approved=True,
        approval_decision_ref="approval-decision:test",
        policy_decision_refs=["policy:source"],
    )
    assert approved.approved
    lifecycle = RunLifecycleRecord(
        id="lifecycle:start",
        run_ref="run:test",
        action=RunLifecycleAction.START_RUN,
        status_before=RunStatus.QUEUED,
        status_after=RunStatus.RUNNING,
        command_result_ref="command-result:start",
        event_ref="event:start",
        actor_ref="actor:test",
        policy_snapshot_ref="policy-snapshot:test",
        budget_ref="budget:test",
        approval_record_ref=approved.id,
        replay_refs=["replay:start"],
    )
    assert lifecycle.status_after == RunStatus.RUNNING
    with pytest.raises(ValidationError):
        RunLifecycleRecord(
            id="lifecycle:bad",
            run_ref="run:test",
            action=RunLifecycleAction.PAUSE_RUN,
            status_before=RunStatus.QUEUED,
            status_after=RunStatus.PAUSED,
            command_result_ref="command-result:pause",
            event_ref="event:pause",
            actor_ref="actor:test",
            policy_snapshot_ref="policy-snapshot:test",
            budget_ref="budget:test",
            replay_refs=["replay:pause"],
        )


def test_run_control_report_requires_success_refs_or_typed_failure() -> None:
    passing = ProductionRunControlReport(
        id="report:pass",
        fixture_id="production-run-control-success",
        project_ref="project:test",
        site_scope_ref="site:test",
        objective_ref="objective:test",
        plan_ref="plan:test",
        run_ref="run:test",
        status=RunStatus.COMPLETED,
        completion_result=CompletenessResult.PASS,
        operator_status="production_run_control_completed",
        command_result_refs=["command-result:start"],
        event_refs=["event:start"],
        policy_decision_refs=["policy:source"],
        approval_refs=["approval:test"],
        budget_ref="budget:test",
        policy_snapshot_ref="policy-snapshot:test",
        lifecycle_record_refs=["lifecycle:start"],
        replay_refs=["replay:start"],
    )
    assert passing.completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        ProductionRunControlReport(
            id="report:bad",
            fixture_id="production-run-control-policy-denied",
            project_ref="project:test",
            site_scope_ref="site:test",
            objective_ref="objective:test",
            plan_ref="plan:test",
            run_ref="run:test",
            status=RunStatus.FAILED,
            completion_result=CompletenessResult.FAIL,
            operator_status=ProductionRunControlFailureType.POLICY_DENIED.value,
        )


def test_run_control_fixture_manifest_requires_failure_for_negative_case() -> None:
    with pytest.raises(ValidationError):
        ProductionRunControlFixtureManifest(
            id="production-run-control-policy-denied",
            scenario="policy-denied",
            profile_refs=["target"],
            expected_status=RunStatus.FAILED,
            expected_completion_result=CompletenessResult.FAIL,
            expected_operator_status=ProductionRunControlFailureType.POLICY_DENIED.value,
            negative_case=True,
        )
