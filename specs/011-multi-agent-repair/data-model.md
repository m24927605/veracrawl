# Data Model: VeraCrawl Multi-Agent Repair

## MultiAgentWorkflow

`id`, `run_ref`, `workflow_type`, `coordinator_service_ref`, `agent_role_sequence`, `loop_budget_ref`, `termination_rule_ref`, `escalation_rule_ref`, `arbitration_policy_ref`, `context_bundle_ref`, `graph_signal_refs`, `memory_retrieval_trace_refs`, `evidence_refs`, `policy_decision_refs`, `status`.

## AgentHandoff

`id`, `run_ref`, `workflow_ref`, `from_agent_action_trace_ref`, `to_agent_role`, `context_bundle_trace_ref`, `required_output_schema_ref`, `policy_decision_refs`, `status`, `output_ref`, `rejection_reasons`.

## CoordinationDecision

`id`, `run_ref`, `workflow_ref`, `decision_type`, `candidate_refs`, `selected_ref`, `rationale_ref`, `arbitration_policy_ref`, `policy_decision_refs`, `owner_command_ref`, `status`.

## DriftRepairSignal

`id`, `run_ref`, `workflow_ref`, `affected_refs`, `before_evidence_refs`, `after_evidence_refs`, `repair_proposal_refs`, `rollback_ref`, `policy_decision_refs`, `status`.

## MultiAgentRepairReport

`id`, `run_ref`, `workflow_ref`, `handoff_refs`, `coordination_decision_refs`, `repair_signal_refs`, `agent_action_trace_refs`, `policy_decision_refs`, `command_record_refs`, `event_cursor_refs`, `outbox_refs`, `failure_report_refs`, `missing_ref_fields`, `operator_status`, `completion_result`.
