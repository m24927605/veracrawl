# Data Model: Optimization Objective Gate

## OptimizationObjectiveScore

- **Purpose**: Records the weighted optimization objective for one run slice,
  validation corpus, or release profile.
- **Fields**:
  - `id`
  - `fixture_id`
  - `run_ref`
  - `profile_ref`
  - `score_formula_ref`
  - `score_threshold`
  - `extraction_accuracy`
  - `intent_match_precision`
  - `crawl_success_rate`
  - `dedupe_quality`
  - `freshness`
  - `normalized_latency`
  - `normalized_cost`
  - `optimization_score`
  - `metric_slice_refs`
  - `algorithm_recommendation_refs`
  - `policy_decision_refs`
  - `command_record_refs`
  - `event_cursor_refs`
  - `outbox_refs`
  - `artifact_refs`
  - `replay_bundle_ref`
  - `diagnostics`
  - `completion_result`
  - `failure_type`
- **Validation Rules**:
  - Component scores and penalty values must be within 0.0 and 1.0.
  - `optimization_score` must match the approved formula within tolerance.
  - Passing reports require score >= threshold.
  - Passing reports require formula, metric, algorithm, policy, command,
    event, outbox, artifact, and replay refs.
  - Failing reports require diagnostics and failure type.

## AgentDecisionLoopEvidence

- **Purpose**: Records replayable observe/think/act/verify evidence for an
  optimization-affecting agent decision.
- **Fields**:
  - `id`
  - `fixture_id`
  - `run_ref`
  - `objective_score_ref`
  - `observe_ref`
  - `think_ref`
  - `act_ref`
  - `verify_ref`
  - `confidence`
  - `confidence_threshold`
  - `stop_condition_ref`
  - `deterministic_decision_refs`
  - `llm_fallback_used`
  - `llm_fallback_reason_refs`
  - `llm_output_evidence_refs`
  - `model_trace_refs`
  - `tool_trace_refs`
  - `policy_decision_refs`
  - `command_record_refs`
  - `event_cursor_refs`
  - `outbox_refs`
  - `artifact_refs`
  - `replay_bundle_ref`
  - `diagnostics`
  - `completion_result`
  - `failure_type`
- **Validation Rules**:
  - Passing evidence requires observe, think, act, verify, stop condition,
    confidence >= threshold, deterministic decision refs, policy refs,
    command/event/outbox refs, artifact refs, and replay refs.
  - LLM fallback requires fallback reason refs and model trace refs.
  - `llm_output_evidence_refs` must be empty for pass.
  - Failing evidence requires diagnostics and failure type.

## OptimizationObjectiveReleaseGate

- **Purpose**: Aggregates lower optimization evidence into a release-blocking
  claim for the recorded corpus.
- **Fields**:
  - `id`
  - `fixture_id`
  - `claim_scope_ref`
  - `required_lower_gate_refs`
  - `present_lower_gate_refs`
  - `failed_lower_gate_refs`
  - `objective_score_refs`
  - `failed_objective_score_refs`
  - `agent_decision_loop_refs`
  - `failed_agent_decision_loop_refs`
  - `metric_slice_refs`
  - `algorithm_recommendation_refs`
  - `policy_decision_refs`
  - `command_record_refs`
  - `event_cursor_refs`
  - `outbox_refs`
  - `artifact_refs`
  - `replay_bundle_ref`
  - `diagnostics`
  - `completion_result`
  - `failure_type`
- **Validation Rules**:
  - Passing gates require all required lower gates present and no failed lower
    gates.
  - Passing gates require at least one passing objective score and at least one
    passing agent decision loop evidence record.
  - Passing gates require metric, algorithm, policy, command, event, outbox,
    artifact, and replay refs.
  - Any failed objective score, failed agent loop, missing replay refs, missing
    policy refs, or missing lower gate refs blocks pass.
  - Failing gates require diagnostics and failure type.

## State Transitions

```text
objective_planned -> objective_scored
objective_scored -> agent_loop_verified
agent_loop_verified -> objective_release_ready

objective_scored -> objective_failed
agent_loop_verified -> agent_loop_failed
objective_release_ready -> release_blocked
```

- `objective_scored` requires `OptimizationObjectiveScore`.
- `agent_loop_verified` requires `AgentDecisionLoopEvidence`.
- `objective_release_ready` requires `OptimizationObjectiveReleaseGate` pass
  plus lower 096 regression gate evidence.
