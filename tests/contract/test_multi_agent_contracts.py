from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.agent import (
    CoordinationDecision,
    MultiAgentRepairReport,
    MultiAgentWorkflow,
)
from veracrawl.contracts.enums import (
    AgentRole,
    CompletenessResult,
    CoordinationDecisionStatus,
    CoordinationDecisionType,
    MultiAgentWorkflowStatus,
)


def test_multi_agent_workflow_requires_loop_budget_and_roles() -> None:
    workflow = MultiAgentWorkflow(
        id="multi-agent-workflow:unit",
        run_ref="run:unit",
        workflow_type="drift_repair",
        coordinator_service_ref="owner-service:agents",
        agent_role_sequence=[AgentRole.PLANNER, AgentRole.EXTRACTOR],
        loop_budget_ref="loop-budget:unit",
        termination_rule_ref="termination-rule:unit",
        escalation_rule_ref="escalation-rule:unit",
        arbitration_policy_ref="arbitration-policy:unit",
        context_bundle_ref="context-bundle:unit",
        evidence_refs=["evidence:unit"],
        policy_decision_refs=["policy:unit:agents"],
        status=MultiAgentWorkflowStatus.COMPLETED,
    )
    assert workflow.agent_role_sequence
    with pytest.raises(ValidationError):
        MultiAgentWorkflow(
            id="multi-agent-workflow:bad",
            run_ref="run:bad",
            workflow_type="drift_repair",
            coordinator_service_ref="owner-service:agents",
            agent_role_sequence=[],
            loop_budget_ref="loop-budget:bad",
            termination_rule_ref="termination-rule:bad",
            escalation_rule_ref="escalation-rule:bad",
            arbitration_policy_ref="arbitration-policy:bad",
            context_bundle_ref="context-bundle:bad",
            policy_decision_refs=["policy:bad:agents"],
            status=MultiAgentWorkflowStatus.COMPLETED,
        )


def test_applied_coordination_decision_requires_owner_command() -> None:
    with pytest.raises(ValidationError):
        CoordinationDecision(
            id="coordination-decision:bad",
            run_ref="run:bad",
            workflow_ref="multi-agent-workflow:bad",
            decision_type=CoordinationDecisionType.APPROVE_REPAIR_PROPOSAL,
            candidate_refs=["repair:1", "repair:2"],
            selected_ref="repair:1",
            rationale_ref="rationale:bad",
            arbitration_policy_ref="arbitration-policy:bad",
            policy_decision_refs=["policy:bad:agents"],
            status=CoordinationDecisionStatus.APPLIED,
        )


def test_multi_agent_report_pass_requires_replay_refs() -> None:
    with pytest.raises(ValidationError):
        MultiAgentRepairReport(
            id="multi-agent-repair-report:bad",
            run_ref="run:bad",
            operator_status="multi_agent_repair_completed",
            completion_result=CompletenessResult.PASS,
        )
