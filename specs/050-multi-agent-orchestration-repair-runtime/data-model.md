# Data Model: Multi-Agent Orchestration And Repair Runtime

## MultiAgentRepairReport Additions

Existing fields remain:

- `id`, `run_ref`, `workflow_ref`
- `handoff_refs`, `coordination_decision_refs`, `repair_signal_refs`
- `agent_action_trace_refs`
- `policy_decision_refs`
- `command_record_refs`, `event_cursor_refs`, `outbox_refs`
- `failure_report_refs`, `missing_ref_fields`
- `operator_status`, `completion_result`

Row 050 adds:

- `agent_model_adapter_runtime_report_ref`
- `live_evidence_verification_runtime_report_ref`
- `controlled_tool_call_refs`
- `owner_command_refs`
- `review_escalation_refs`
- `replay_bundle_ref`
- `failure_type`

Validation:

- `pass` requires workflow, handoff, coordination, repair, agent trace, row 049,
  row 047, controlled tool, owner command, policy, command/event/outbox, and
  replay refs.
- non-pass reports require `failure_type` plus failure refs or missing fields.

## MultiAgentWorkflow

The existing workflow contract remains the workflow graph and policy boundary:

- role sequence
- loop budget
- termination and escalation rules
- arbitration policy
- context bundle
- graph, memory, evidence, and policy refs

Row 050 success workflows must include planner, frontier, fetch-analysis,
extractor, verifier, drift, memory, and ops roles where relevant.

## AgentHandoff

Handoffs remain explicit transitions between agent roles. Passing row 050
reports require replayable handoff refs and output refs; rejected handoffs must
carry rejection reasons.

## CoordinationDecision

Coordination decisions arbitrate plans, repair proposals, termination, and
escalation. Applied decisions require owner command refs.

## DriftRepairSignal

Repair signals must keep affected refs, before/after evidence refs,
repair proposal refs, rollback refs, policy refs, and status.
