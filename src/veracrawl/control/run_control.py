"""Production run-control lifecycle fixtures."""

from __future__ import annotations

from typing import Literal

from veracrawl.contracts.command import CommandResult
from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import (
    CommandResultStatus,
    CompletenessResult,
    ObjectiveStatus,
    PlanStatus,
    ProductionRunControlFailureType,
    RunLifecycleAction,
    RunStatus,
)
from veracrawl.contracts.objective import (
    CrawlObjective,
    CrawlPlan,
    CrawlRun,
    ProductionProject,
    ProductionRunControlReport,
    ProductionSiteScope,
    RunApprovalRecord,
    RunBudget,
    RunLifecycleRecord,
    RunPlanSnapshot,
    RunPolicySnapshot,
)
from veracrawl.contracts.policy import PolicyDecision
from veracrawl.control.runtime import command_result, create_runtime_command
from veracrawl.policy.gates import decision_for
from veracrawl.runtime_events.event_store import InMemoryEventStore, append_runtime_event

RunControlScenario = Literal[
    "success",
    "paused-resumed",
    "cancelled",
    "policy-denied",
    "missing-approval",
    "missing-budget",
    "invalid-transition",
    "missing-replay",
]


def _suffix(fixture_id: str) -> str:
    return fixture_id.removeprefix("production-run-control-")


def _policy(
    *,
    fixture_id: str,
    run_ref: Ref,
    objective_ref: Ref,
    decision_type: str,
    subject_ref: Ref,
    allow: bool,
) -> PolicyDecision:
    return decision_for(
        decision_id=f"policy:{fixture_id}:{decision_type}:{subject_ref}",
        run_id=run_ref,
        objective_id=objective_ref,
        decision_type=decision_type,
        subject_ref=subject_ref,
        allow=allow,
        reasons=[] if allow else [f"blocked:{decision_type}:{subject_ref}"],
    )


def _record_command(
    *,
    fixture_id: str,
    event_store: InMemoryEventStore,
    run: CrawlRun,
    objective: CrawlObjective,
    plan: CrawlPlan,
    command_type: str,
    target_type: str,
    target_ref: Ref,
    event_type: str,
    output_refs: list[Ref],
    policy_decision_refs: list[Ref] | None = None,
    actor_ref: Ref = "actor:production-run-control",
) -> tuple[CommandResult, Ref]:
    command = create_runtime_command(
        command_id=f"cmd:{fixture_id}:{command_type}:{len(event_store.stream(run.id)) + 1}",
        command_type=command_type,
        target_aggregate_type=target_type,
        target_aggregate_id=target_ref,
        actor_ref=actor_ref,
        policy_decision_refs=policy_decision_refs,
    )
    event_ref = append_runtime_event(
        event_store,
        run_id=run.id,
        objective_id=objective.id,
        plan_id=plan.id,
        event_type=event_type,
        payload_ref=command.payload_ref,
        causation_id=command.id,
        correlation_id=f"corr:{run.id}",
        output_refs=output_refs,
        policy_decision_refs=policy_decision_refs or [],
        state_before={"target_ref": target_ref},
        state_after={"status": "recorded", "target_ref": target_ref},
        actor=actor_ref,
    )
    return command_result(
        command=command,
        result=CommandResultStatus.COMMITTED,
        emitted_event_refs=[event_ref],
        output_refs=output_refs,
    ), event_ref


def _base_records(
    *,
    fixture_id: str,
    allow_policy: bool = True,
    approved: bool = True,
    include_budget: bool = True,
) -> tuple[
    ProductionProject,
    ProductionSiteScope,
    CrawlObjective,
    CrawlPlan,
    RunPlanSnapshot,
    CrawlRun,
    RunBudget | None,
    RunPolicySnapshot | None,
    RunApprovalRecord | None,
    list[PolicyDecision],
]:
    suffix = _suffix(fixture_id)
    project = ProductionProject(
        id=f"project:{suffix}",
        owner_ref="actor:production-run-control",
        project_policy_refs=[f"policy:{suffix}:project"],
        default_budget_ref=f"budget:{suffix}",
    )
    site_scope = ProductionSiteScope(
        id=f"site-scope:{suffix}",
        project_ref=project.id,
        allowed_scope_refs=[f"scope:{suffix}:authorized"],
        source_policy_refs=[f"policy:{suffix}:source"],
        robots_policy_ref=f"policy:{suffix}:robots",
        egress_policy_ref=f"policy:{suffix}:egress",
        credential_policy_ref=f"policy:{suffix}:credential",
    )
    objective = CrawlObjective(
        id=f"objective:{suffix}",
        project_ref=project.id,
        site_scope_refs=[site_scope.id],
        objective_text_ref=f"objective-text:{suffix}",
        target_schema_refs=[f"schema:{suffix}:record"],
        evidence_requirement_refs=[f"evidence-requirement:{suffix}:source-anchor"],
        freshness_policy_ref=f"policy:{suffix}:freshness",
        source_policy_refs=site_scope.source_policy_refs,
        publication_policy_refs=[f"policy:{suffix}:publication"],
        status=ObjectiveStatus.APPROVED if approved else ObjectiveStatus.DRAFT,
        created_by_ref="actor:production-run-control",
    )
    plan = CrawlPlan(
        id=f"plan:{suffix}",
        objective_ref=objective.id,
        plan_version="1",
        adapter_plan=[{"adapter_spec_ref": f"adapter:{suffix}:http"}] if approved else [],
        seed_refs=[f"seed:{suffix}:home"],
        evidence_requirement_refs=objective.evidence_requirement_refs,
        budget_ref=f"budget:{suffix}",
        approval_decision_ref=f"approval:{suffix}" if approved else None,
        status=PlanStatus.APPROVED if approved else PlanStatus.PROPOSED,
    )
    snapshot = RunPlanSnapshot(
        id=f"run-plan-snapshot:{suffix}",
        objective_ref=objective.id,
        plan_ref=plan.id,
        plan_hash=stable_hash(plan),
        policy_refs=objective.source_policy_refs + objective.publication_policy_refs,
        schema_refs=objective.target_schema_refs,
        adapter_spec_refs=[f"adapter:{suffix}:http"],
        tool_refs=[f"tool:{suffix}:run-control"],
        model_refs=["model:structural-none"],
        evidence_requirement_refs=objective.evidence_requirement_refs,
        replay_config_ref=f"replay-config:{suffix}",
    )
    budget = (
        RunBudget(
            id=f"budget:{suffix}",
            project_ref=project.id,
            crawl_limit_refs=[f"crawl-limit:{suffix}:pages"],
            max_pages=25,
            max_depth=3,
            max_runtime_seconds=600,
            max_browser_minutes=0,
            max_model_tokens=10_000,
            policy_decision_refs=[f"policy-decision:{suffix}:budget"],
        )
        if include_budget
        else None
    )
    run = CrawlRun(
        id=f"run:{suffix}",
        objective_ref=objective.id,
        plan_ref=plan.id,
        run_plan_snapshot_ref=snapshot.id,
        status=RunStatus.QUEUED,
        policy_snapshot_ref=f"policy-snapshot:{suffix}",
        budget_ref=budget.id if budget is not None else "",
    )
    policies = [
        _policy(
            fixture_id=fixture_id,
            run_ref=run.id,
            objective_ref=objective.id,
            decision_type="runtime_source",
            subject_ref=site_scope.id,
            allow=allow_policy,
        ),
        _policy(
            fixture_id=fixture_id,
            run_ref=run.id,
            objective_ref=objective.id,
            decision_type="runtime_publication",
            subject_ref=plan.id,
            allow=allow_policy,
        ),
    ]
    policy_snapshot = (
        RunPolicySnapshot(
            id=f"policy-snapshot:{suffix}",
            run_ref=run.id,
            project_ref=project.id,
            site_scope_ref=site_scope.id,
            source_policy_refs=objective.source_policy_refs,
            publication_policy_refs=objective.publication_policy_refs,
            privacy_policy_ref=f"policy:{suffix}:privacy",
            egress_policy_ref=site_scope.egress_policy_ref,
            credential_policy_ref=site_scope.credential_policy_ref,
            prompt_taint_policy_ref=f"policy:{suffix}:prompt-taint",
            budget_ref=budget.id,
            policy_decision_refs=[policy.id for policy in policies],
        )
        if budget is not None
        else None
    )
    approval = (
        RunApprovalRecord(
            id=f"approval-record:{suffix}",
            objective_ref=objective.id,
            plan_ref=plan.id,
            actor_ref="actor:production-run-control",
            approved=True,
            approval_decision_ref=f"approval:{suffix}",
            policy_decision_refs=[policy.id for policy in policies],
        )
        if approved
        else None
    )
    return (
        project,
        site_scope,
        objective,
        plan,
        snapshot,
        run,
        budget,
        policy_snapshot,
        approval,
        policies,
    )


def _failure_report(
    *,
    fixture_id: str,
    run: CrawlRun,
    project: ProductionProject,
    site_scope: ProductionSiteScope,
    objective: CrawlObjective,
    plan: CrawlPlan,
    failure_type: ProductionRunControlFailureType,
    diagnostics: list[str],
    command_result_refs: list[Ref],
    event_refs: list[Ref],
    policy_refs: list[Ref],
    approval_ref: Ref | None,
    budget_ref: Ref | None,
    policy_snapshot_ref: Ref | None,
    lifecycle_refs: list[Ref],
    replay_refs: list[Ref],
    status: RunStatus = RunStatus.FAILED,
) -> ProductionRunControlReport:
    return ProductionRunControlReport(
        id=f"production-run-control-report:{fixture_id}",
        fixture_id=fixture_id,
        project_ref=project.id,
        site_scope_ref=site_scope.id,
        objective_ref=objective.id,
        plan_ref=plan.id,
        run_ref=run.id,
        status=status,
        completion_result=CompletenessResult.FAIL,
        operator_status=failure_type.value,
        command_result_refs=command_result_refs,
        event_refs=event_refs,
        policy_decision_refs=policy_refs,
        approval_refs=[approval_ref] if approval_ref else [],
        budget_ref=budget_ref,
        policy_snapshot_ref=policy_snapshot_ref,
        lifecycle_record_refs=lifecycle_refs,
        replay_refs=replay_refs,
        failure_type=failure_type,
        failure_report_refs=[f"failure:{fixture_id}:{failure_type.value}"],
        diagnostics=diagnostics,
    )


def _lifecycle(
    *,
    fixture_id: str,
    event_store: InMemoryEventStore,
    run: CrawlRun,
    objective: CrawlObjective,
    plan: CrawlPlan,
    action: RunLifecycleAction,
    status_after: RunStatus,
    policy_snapshot: RunPolicySnapshot,
    budget: RunBudget,
    approval: RunApprovalRecord,
    replay: bool = True,
    failure_refs: list[Ref] | None = None,
) -> tuple[RunLifecycleRecord, CommandResult, Ref, CrawlRun]:
    status_before = run.status
    command_name = action.value
    event_name = {
        RunLifecycleAction.START_RUN: "run_started",
        RunLifecycleAction.PAUSE_RUN: "run_paused",
        RunLifecycleAction.RESUME_RUN: "run_resumed",
        RunLifecycleAction.CANCEL_RUN: "run_cancelled",
        RunLifecycleAction.FAIL_RUN: "run_failed",
        RunLifecycleAction.COMPLETE_RUN: "run_completed",
    }[action]
    result, event_ref = _record_command(
        fixture_id=fixture_id,
        event_store=event_store,
        run=run,
        objective=objective,
        plan=plan,
        command_type=command_name,
        target_type="CrawlRun",
        target_ref=run.id,
        event_type=event_name,
        output_refs=[run.id],
        policy_decision_refs=policy_snapshot.policy_decision_refs,
    )
    next_run = run.model_copy(update={"status": status_after})
    lifecycle = RunLifecycleRecord(
        id=f"run-lifecycle:{fixture_id}:{action.value}:{len(event_store.stream(run.id))}",
        run_ref=run.id,
        action=action,
        status_before=status_before,
        status_after=status_after,
        command_result_ref=result.id,
        event_ref=event_ref,
        actor_ref="actor:production-run-control",
        policy_snapshot_ref=policy_snapshot.id,
        budget_ref=budget.id,
        approval_record_ref=approval.id,
        failure_record_refs=failure_refs or [],
        replay_refs=[f"replay:{fixture_id}:{action.value}"] if replay else [],
    )
    return lifecycle, result, event_ref, next_run


def _scenario_from_fixture(fixture_id: str, scenario: str | None) -> RunControlScenario:
    if scenario:
        return scenario  # type: ignore[return-value]
    return _suffix(fixture_id)  # type: ignore[return-value]


def run_production_run_control_fixture(
    *,
    fixture_id: str,
    scenario: str | None,
    profile: str,
) -> ProductionRunControlReport:
    runtime_scenario = _scenario_from_fixture(fixture_id, scenario)
    allow_policy = runtime_scenario != "policy-denied"
    approved = runtime_scenario != "missing-approval"
    include_budget = runtime_scenario != "missing-budget"
    (
        project,
        site_scope,
        objective,
        plan,
        _snapshot,
        run,
        budget,
        policy_snapshot,
        approval,
        policies,
    ) = _base_records(
        fixture_id=fixture_id,
        allow_policy=allow_policy,
        approved=approved,
        include_budget=include_budget,
    )
    event_store = InMemoryEventStore()
    command_refs: list[Ref] = []
    event_refs: list[Ref] = []
    lifecycle_refs: list[Ref] = []
    replay_refs: list[Ref] = []
    policy_refs = [policy.id for policy in policies]

    for command_type, target_type, target_ref, event_type in [
        (
            "record_production_project",
            "ProductionProject",
            project.id,
            "production_project_recorded",
        ),
        (
            "record_production_site_scope",
            "ProductionSiteScope",
            site_scope.id,
            "production_site_scope_recorded",
        ),
    ]:
        result, event_ref = _record_command(
            fixture_id=fixture_id,
            event_store=event_store,
            run=run,
            objective=objective,
            plan=plan,
            command_type=command_type,
            target_type=target_type,
            target_ref=target_ref,
            event_type=event_type,
            output_refs=[target_ref],
        )
        command_refs.append(result.id)
        event_refs.append(event_ref)

    if not allow_policy:
        return _failure_report(
            fixture_id=fixture_id,
            run=run,
            project=project,
            site_scope=site_scope,
            objective=objective,
            plan=plan,
            failure_type=ProductionRunControlFailureType.POLICY_DENIED,
            diagnostics=["production run-control blocked by policy decision"],
            command_result_refs=command_refs,
            event_refs=event_refs,
            policy_refs=policy_refs,
            approval_ref=approval.id if approval else None,
            budget_ref=budget.id if budget else None,
            policy_snapshot_ref=policy_snapshot.id if policy_snapshot else None,
            lifecycle_refs=lifecycle_refs,
            replay_refs=replay_refs,
        )
    if approval is None:
        return _failure_report(
            fixture_id=fixture_id,
            run=run,
            project=project,
            site_scope=site_scope,
            objective=objective,
            plan=plan,
            failure_type=ProductionRunControlFailureType.MISSING_APPROVAL,
            diagnostics=["production run-control requires approved objective and plan"],
            command_result_refs=command_refs,
            event_refs=event_refs,
            policy_refs=policy_refs,
            approval_ref=None,
            budget_ref=budget.id if budget else None,
            policy_snapshot_ref=policy_snapshot.id if policy_snapshot else None,
            lifecycle_refs=lifecycle_refs,
            replay_refs=replay_refs,
        )
    if budget is None or policy_snapshot is None:
        return _failure_report(
            fixture_id=fixture_id,
            run=run,
            project=project,
            site_scope=site_scope,
            objective=objective,
            plan=plan,
            failure_type=ProductionRunControlFailureType.MISSING_BUDGET,
            diagnostics=["production run-control requires budget and policy snapshot refs"],
            command_result_refs=command_refs,
            event_refs=event_refs,
            policy_refs=policy_refs,
            approval_ref=approval.id,
            budget_ref=None,
            policy_snapshot_ref=None,
            lifecycle_refs=lifecycle_refs,
            replay_refs=replay_refs,
        )

    for command_type, target_type, target_ref, event_type, output_refs, policy_decisions in [
        (
            "record_run_budget",
            "RunBudget",
            budget.id,
            "run_budget_recorded",
            [budget.id],
            budget.policy_decision_refs,
        ),
        (
            "record_run_policy_snapshot",
            "RunPolicySnapshot",
            policy_snapshot.id,
            "run_policy_snapshot_recorded",
            [policy_snapshot.id],
            policy_snapshot.policy_decision_refs,
        ),
        (
            "record_run_approval",
            "RunApprovalRecord",
            approval.id,
            "run_approval_recorded",
            [approval.id],
            approval.policy_decision_refs,
        ),
    ]:
        result, event_ref = _record_command(
            fixture_id=fixture_id,
            event_store=event_store,
            run=run,
            objective=objective,
            plan=plan,
            command_type=command_type,
            target_type=target_type,
            target_ref=target_ref,
            event_type=event_type,
            output_refs=output_refs,
            policy_decision_refs=policy_decisions,
        )
        command_refs.append(result.id)
        event_refs.append(event_ref)

    if runtime_scenario == "invalid-transition":
        return _failure_report(
            fixture_id=fixture_id,
            run=run,
            project=project,
            site_scope=site_scope,
            objective=objective,
            plan=plan,
            failure_type=ProductionRunControlFailureType.INVALID_TRANSITION,
            diagnostics=["cannot pause queued production run"],
            command_result_refs=command_refs,
            event_refs=event_refs,
            policy_refs=policy_refs,
            approval_ref=approval.id,
            budget_ref=budget.id,
            policy_snapshot_ref=policy_snapshot.id,
            lifecycle_refs=lifecycle_refs,
            replay_refs=replay_refs,
        )

    if runtime_scenario == "missing-replay":
        result, event_ref = _record_command(
            fixture_id=fixture_id,
            event_store=event_store,
            run=run,
            objective=objective,
            plan=plan,
            command_type=RunLifecycleAction.START_RUN.value,
            target_type="CrawlRun",
            target_ref=run.id,
            event_type="run_started",
            output_refs=[run.id],
            policy_decision_refs=policy_snapshot.policy_decision_refs,
        )
        command_refs.append(result.id)
        event_refs.append(event_ref)
        run = run.model_copy(update={"status": RunStatus.RUNNING})
        return _failure_report(
            fixture_id=fixture_id,
            run=run,
            project=project,
            site_scope=site_scope,
            objective=objective,
            plan=plan,
            failure_type=ProductionRunControlFailureType.MISSING_REPLAY,
            diagnostics=["production run-control lifecycle missing replay refs"],
            command_result_refs=command_refs,
            event_refs=event_refs,
            policy_refs=policy_refs,
            approval_ref=approval.id,
            budget_ref=budget.id,
            policy_snapshot_ref=policy_snapshot.id,
            lifecycle_refs=[],
            replay_refs=[],
            status=RunStatus.FAILED,
        )

    lifecycle, result, event_ref, run = _lifecycle(
        fixture_id=fixture_id,
        event_store=event_store,
        run=run,
        objective=objective,
        plan=plan,
        action=RunLifecycleAction.START_RUN,
        status_after=RunStatus.RUNNING,
        policy_snapshot=policy_snapshot,
        budget=budget,
        approval=approval,
    )
    command_refs.append(result.id)
    event_refs.append(event_ref)
    lifecycle_refs.append(lifecycle.id)
    replay_refs.extend(lifecycle.replay_refs)

    if runtime_scenario == "paused-resumed":
        for action, status_after in [
            (RunLifecycleAction.PAUSE_RUN, RunStatus.PAUSED),
            (RunLifecycleAction.RESUME_RUN, RunStatus.RUNNING),
        ]:
            lifecycle, result, event_ref, run = _lifecycle(
                fixture_id=fixture_id,
                event_store=event_store,
                run=run,
                objective=objective,
                plan=plan,
                action=action,
                status_after=status_after,
                policy_snapshot=policy_snapshot,
                budget=budget,
                approval=approval,
            )
            command_refs.append(result.id)
            event_refs.append(event_ref)
            lifecycle_refs.append(lifecycle.id)
            replay_refs.extend(lifecycle.replay_refs)

    if runtime_scenario == "cancelled":
        lifecycle, result, event_ref, run = _lifecycle(
            fixture_id=fixture_id,
            event_store=event_store,
            run=run,
            objective=objective,
            plan=plan,
            action=RunLifecycleAction.CANCEL_RUN,
            status_after=RunStatus.CANCELLED,
            policy_snapshot=policy_snapshot,
            budget=budget,
            approval=approval,
        )
        command_refs.append(result.id)
        event_refs.append(event_ref)
        lifecycle_refs.append(lifecycle.id)
        replay_refs.extend(lifecycle.replay_refs)
    else:
        lifecycle, result, event_ref, run = _lifecycle(
            fixture_id=fixture_id,
            event_store=event_store,
            run=run,
            objective=objective,
            plan=plan,
            action=RunLifecycleAction.COMPLETE_RUN,
            status_after=RunStatus.COMPLETED,
            policy_snapshot=policy_snapshot,
            budget=budget,
            approval=approval,
        )
        command_refs.append(result.id)
        event_refs.append(event_ref)
        lifecycle_refs.append(lifecycle.id)
        replay_refs.extend(lifecycle.replay_refs)

    return ProductionRunControlReport(
        id=f"production-run-control-report:{fixture_id}",
        fixture_id=fixture_id,
        project_ref=project.id,
        site_scope_ref=site_scope.id,
        objective_ref=objective.id,
        plan_ref=plan.id,
        run_ref=run.id,
        status=run.status,
        completion_result=CompletenessResult.PASS,
        operator_status="production_run_control_completed",
        command_result_refs=command_refs,
        event_refs=event_refs,
        policy_decision_refs=policy_refs,
        approval_refs=[approval.id],
        budget_ref=budget.id,
        policy_snapshot_ref=policy_snapshot.id,
        lifecycle_record_refs=lifecycle_refs,
        replay_refs=replay_refs,
    )
