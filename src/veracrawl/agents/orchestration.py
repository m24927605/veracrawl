"""Deterministic multi-agent repair orchestration runtime."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.agent import (
    AgentHandoff,
    CoordinationDecision,
    DriftRepairSignal,
    MultiAgentRepairReport,
    MultiAgentWorkflow,
)
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    AgentHandoffStatus,
    AgentRole,
    CompletenessResult,
    CoordinationDecisionStatus,
    CoordinationDecisionType,
    MultiAgentFailureType,
    MultiAgentWorkflowStatus,
    RepairSignalStatus,
)


@dataclass(frozen=True)
class MultiAgentRepairResult:
    workflow: MultiAgentWorkflow | None
    handoffs: list[AgentHandoff]
    coordination_decisions: list[CoordinationDecision]
    repair_signals: list[DriftRepairSignal]
    report: MultiAgentRepairReport


def run_multi_agent_repair(
    *,
    fixture_id: str,
    scenario: str,
    policy_decision_refs: list[Ref] | None = None,
) -> MultiAgentRepairResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:multi-agent"]
    failures = {
        "owner-service-bypass": MultiAgentFailureType.OWNER_SERVICE_BYPASS,
        "unresolved-coordination-conflict": (
            MultiAgentFailureType.UNRESOLVED_COORDINATION_CONFLICT
        ),
        "agent-reasoning-as-evidence": MultiAgentFailureType.AGENT_REASONING_AS_EVIDENCE,
        "loop-budget-exhausted": MultiAgentFailureType.LOOP_BUDGET_EXHAUSTED,
    }
    if scenario in failures:
        return _failure_result(
            fixture_id=fixture_id,
            failure=failures[scenario],
            policy_refs=policy_refs,
        )

    workflow = _workflow_for(fixture_id, policy_refs)
    handoffs = _handoffs_for(fixture_id, workflow.id, policy_refs)
    decision = CoordinationDecision(
        id=f"coordination-decision:{fixture_id}:repair",
        run_ref=f"run:{fixture_id}",
        workflow_ref=workflow.id,
        decision_type=(
            CoordinationDecisionType.RESOLVE_RECOMMENDATION_CONFLICT
            if scenario == "coordination-arbitration-success"
            else CoordinationDecisionType.APPROVE_REPAIR_PROPOSAL
        ),
        candidate_refs=[
            f"repair-proposal:{fixture_id}:conservative",
            f"repair-proposal:{fixture_id}:aggressive",
        ],
        selected_ref=f"repair-proposal:{fixture_id}:conservative",
        rationale_ref=f"rationale:{fixture_id}:coordination",
        arbitration_policy_ref=workflow.arbitration_policy_ref,
        policy_decision_refs=policy_refs,
        owner_command_ref=f"command:{fixture_id}:record-review-decision",
        status=CoordinationDecisionStatus.APPLIED,
    )
    repair_signal = DriftRepairSignal(
        id=f"drift-repair-signal:{fixture_id}:template",
        run_ref=f"run:{fixture_id}",
        workflow_ref=workflow.id,
        affected_refs=[f"normalized-document:{fixture_id}:before"],
        before_evidence_refs=[f"evidence-packet:{fixture_id}:before"],
        after_evidence_refs=[f"evidence-packet:{fixture_id}:after"],
        repair_proposal_refs=[decision.selected_ref or f"repair-proposal:{fixture_id}:fallback"],
        rollback_ref=f"rollback:{fixture_id}:selector",
        policy_decision_refs=policy_refs,
        status=RepairSignalStatus.REPAIRED,
    )
    report = MultiAgentRepairReport(
        id=f"multi-agent-repair-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        workflow_ref=workflow.id,
        handoff_refs=[handoff.id for handoff in handoffs],
        coordination_decision_refs=[decision.id],
        repair_signal_refs=[repair_signal.id],
        agent_action_trace_refs=[
            f"agent-trace:{fixture_id}:{role.value}" for role in workflow.agent_role_sequence
        ],
        policy_decision_refs=policy_refs,
        command_record_refs=[f"command-record:{fixture_id}:multi-agent"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:multi-agent"],
        outbox_refs=[f"outbox:{fixture_id}:multi-agent"],
        operator_status="multi_agent_repair_completed",
        completion_result=CompletenessResult.PASS,
    )
    return MultiAgentRepairResult(
        workflow=workflow,
        handoffs=handoffs,
        coordination_decisions=[decision],
        repair_signals=[repair_signal],
        report=report,
    )


def _workflow_for(fixture_id: str, policy_refs: list[Ref]) -> MultiAgentWorkflow:
    return MultiAgentWorkflow(
        id=f"multi-agent-workflow:{fixture_id}:repair",
        run_ref=f"run:{fixture_id}",
        workflow_type="drift_repair",
        coordinator_service_ref="owner-service:agents",
        agent_role_sequence=[
            AgentRole.PLANNER,
            AgentRole.SITE_UNDERSTANDING,
            AgentRole.EXTRACTOR,
            AgentRole.VERIFIER,
            AgentRole.DRIFT,
        ],
        loop_budget_ref=f"loop-budget:{fixture_id}:repair",
        termination_rule_ref=f"termination-rule:{fixture_id}:repair",
        escalation_rule_ref=f"escalation-rule:{fixture_id}:review",
        arbitration_policy_ref=f"arbitration-policy:{fixture_id}:repair",
        context_bundle_ref=f"context-bundle:{fixture_id}:repair",
        graph_signal_refs=[f"graph-signal:{fixture_id}:drift_risk"],
        memory_retrieval_trace_refs=[f"memory-retrieval-trace:{fixture_id}"],
        evidence_refs=[
            f"evidence-packet:{fixture_id}:before",
            f"evidence-packet:{fixture_id}:after",
        ],
        policy_decision_refs=policy_refs,
        status=MultiAgentWorkflowStatus.COMPLETED,
    )


def _handoffs_for(fixture_id: str, workflow_ref: Ref, policy_refs: list[Ref]) -> list[AgentHandoff]:
    roles = [AgentRole.SITE_UNDERSTANDING, AgentRole.EXTRACTOR, AgentRole.VERIFIER]
    return [
        AgentHandoff(
            id=f"agent-handoff:{fixture_id}:{role.value}",
            run_ref=f"run:{fixture_id}",
            workflow_ref=workflow_ref,
            from_agent_action_trace_ref=f"agent-trace:{fixture_id}:planner",
            to_agent_role=role,
            context_bundle_trace_ref=f"context-trace:{fixture_id}:{role.value}",
            required_output_schema_ref=f"schema:{fixture_id}:{role.value}:output",
            policy_decision_refs=policy_refs,
            status=AgentHandoffStatus.COMPLETED,
            output_ref=f"agent-output:{fixture_id}:{role.value}",
        )
        for role in roles
    ]


def _failure_result(
    *,
    fixture_id: str,
    failure: MultiAgentFailureType,
    policy_refs: list[Ref],
) -> MultiAgentRepairResult:
    return MultiAgentRepairResult(
        workflow=None,
        handoffs=[],
        coordination_decisions=[],
        repair_signals=[],
        report=MultiAgentRepairReport(
            id=f"multi-agent-repair-report:{fixture_id}",
            run_ref=f"run:{fixture_id}",
            policy_decision_refs=policy_refs,
            failure_report_refs=[f"multi-agent-failure:{fixture_id}:{failure.value}"],
            missing_ref_fields=[failure.value],
            operator_status=failure.value,
            completion_result=CompletenessResult.FAIL,
        ),
    )
