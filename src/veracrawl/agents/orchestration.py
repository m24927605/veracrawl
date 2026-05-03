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
    agent_model_adapter_runtime_report_ref: Ref | None = None,
    live_evidence_verification_runtime_report_ref: Ref | None = None,
) -> MultiAgentRepairResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:multi-agent"]
    failures = {
        "owner-service-bypass": MultiAgentFailureType.OWNER_SERVICE_BYPASS,
        "unresolved-coordination-conflict": (
            MultiAgentFailureType.UNRESOLVED_COORDINATION_CONFLICT
        ),
        "agent-reasoning-as-evidence": MultiAgentFailureType.AGENT_REASONING_AS_EVIDENCE,
        "loop-budget-exhausted": MultiAgentFailureType.LOOP_BUDGET_EXHAUSTED,
        "multi-agent-missing-agent-model-runtime": (
            MultiAgentFailureType.MISSING_AGENT_MODEL_RUNTIME
        ),
        "multi-agent-missing-live-evidence": MultiAgentFailureType.MISSING_LIVE_EVIDENCE,
        "multi-agent-missing-tool-gate": MultiAgentFailureType.MISSING_TOOL_GATE,
        "multi-agent-missing-owner-command": MultiAgentFailureType.MISSING_OWNER_COMMAND,
        "multi-agent-replay-mismatch": MultiAgentFailureType.MISSING_REPLAY_REFS,
    }
    if scenario in failures:
        return _failure_result(
            fixture_id=fixture_id,
            failure=failures[scenario],
            policy_refs=policy_refs,
        )

    agent_model_ref = (
        agent_model_adapter_runtime_report_ref
        or f"agent-model-adapter-runtime-report:{fixture_id}"
    )
    live_evidence_ref = (
        live_evidence_verification_runtime_report_ref
        or f"live-evidence-verification-runtime-report:{fixture_id}"
    )
    workflow = _workflow_for(fixture_id, scenario, policy_refs, live_evidence_ref)
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
    repair_kind = _repair_kind(scenario)
    repair_signal = DriftRepairSignal(
        id=f"{repair_kind}-repair-signal:{fixture_id}:primary",
        run_ref=f"run:{fixture_id}",
        workflow_ref=workflow.id,
        affected_refs=[f"{repair_kind}-affected-ref:{fixture_id}:before"],
        before_evidence_refs=[
            f"evidence-packet:{fixture_id}:before",
            live_evidence_ref,
        ],
        after_evidence_refs=[f"evidence-packet:{fixture_id}:after"],
        repair_proposal_refs=[decision.selected_ref or f"repair-proposal:{fixture_id}:fallback"],
        rollback_ref=f"rollback:{fixture_id}:{repair_kind}",
        policy_decision_refs=policy_refs,
        status=RepairSignalStatus.REPAIRED,
    )
    controlled_tool_refs = [
        f"tool-call-trace:{fixture_id}:{role.value}:controlled-tool"
        for role in workflow.agent_role_sequence
    ]
    owner_command_refs = [
        decision.owner_command_ref or f"command:{fixture_id}:coordination",
        f"command:{fixture_id}:apply-{repair_kind}-repair",
    ]
    report = MultiAgentRepairReport(
        id=f"multi-agent-repair-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        workflow_ref=workflow.id,
        agent_model_adapter_runtime_report_ref=agent_model_ref,
        live_evidence_verification_runtime_report_ref=live_evidence_ref,
        handoff_refs=[handoff.id for handoff in handoffs],
        coordination_decision_refs=[decision.id],
        repair_signal_refs=[repair_signal.id],
        agent_action_trace_refs=[
            f"agent-trace:{fixture_id}:{role.value}" for role in workflow.agent_role_sequence
        ],
        controlled_tool_call_refs=controlled_tool_refs,
        owner_command_refs=owner_command_refs,
        review_escalation_refs=[f"review-escalation:{fixture_id}:{repair_kind}"],
        policy_decision_refs=policy_refs,
        command_record_refs=[f"command-record:{fixture_id}:multi-agent"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:multi-agent"],
        outbox_refs=[f"outbox:{fixture_id}:multi-agent"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:multi-agent",
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


def _workflow_for(
    fixture_id: str,
    scenario: str,
    policy_refs: list[Ref],
    live_evidence_ref: Ref,
) -> MultiAgentWorkflow:
    repair_kind = _repair_kind(scenario)
    return MultiAgentWorkflow(
        id=f"multi-agent-workflow:{fixture_id}:repair",
        run_ref=f"run:{fixture_id}",
        workflow_type=f"{repair_kind}_repair",
        coordinator_service_ref="owner-service:agents",
        agent_role_sequence=[
            AgentRole.PLANNER,
            AgentRole.SITE_UNDERSTANDING,
            AgentRole.FRONTIER,
            AgentRole.FETCH_ANALYSIS,
            AgentRole.EXTRACTOR,
            AgentRole.VERIFIER,
            AgentRole.DRIFT,
            AgentRole.MEMORY,
            AgentRole.OPS,
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
            live_evidence_ref,
        ],
        policy_decision_refs=policy_refs,
        status=MultiAgentWorkflowStatus.COMPLETED,
    )


def _handoffs_for(fixture_id: str, workflow_ref: Ref, policy_refs: list[Ref]) -> list[AgentHandoff]:
    roles = [
        AgentRole.SITE_UNDERSTANDING,
        AgentRole.FRONTIER,
        AgentRole.FETCH_ANALYSIS,
        AgentRole.EXTRACTOR,
        AgentRole.VERIFIER,
        AgentRole.DRIFT,
        AgentRole.MEMORY,
        AgentRole.OPS,
    ]
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
            failure_type=failure,
            operator_status=failure.value,
            completion_result=CompletenessResult.FAIL,
        ),
    )


def _repair_kind(scenario: str) -> str:
    if scenario == "crawl-repair-success":
        return "crawl"
    if scenario == "extraction-repair-success":
        return "extraction"
    return "drift"
