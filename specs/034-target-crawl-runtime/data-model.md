# Data Model: VeraCrawl Target Crawl Runtime

## TargetRuntimeStatus

Run-level status exposed to operators and fixture oracles.

- `complete`: all required objective, plan, pattern, evidence, graph, export, policy, command/event/outbox, artifact, privacy, and replay refs are present.
- `needs_review`: runtime produced useful work but requires review before publication or completion.
- `blocked`: policy or safety blocked an action before trustworthy acquisition or publication.
- `failed`: runtime or oracle mismatch prevents a trustworthy result.

Validation rules:

- `complete` requires `CompletenessResult.PASS`.
- `needs_review` requires review item or recovery refs.
- `blocked` and `failed` require a failure type and failure refs.

## TargetRuntimeFailureType

Stable negative-fixture and operator diagnostic categories.

- `target_runtime_policy_denied`
- `target_runtime_prompt_injection`
- `target_runtime_missing_evidence`
- `target_runtime_replay_mismatch`
- `target_runtime_partial_export`
- `target_runtime_false_complete`
- `target_runtime_drift_repair_required`
- `target_runtime_oracle_mismatch`

Validation rules:

- Failure fixtures expecting `fail` or `blocked` must set one failure type.
- `needs_review` may set a failure type only when it represents a recoverable condition.

## TargetCrawlPatternRecord

Per-pattern proof that one website/source pattern was processed without becoming a single-site special case.

Fields:

- `id`
- `run_ref`
- `website_pattern`
- `frontier_item_refs`
- `source_observation_refs`
- `source_adapter_result_refs`
- `extraction_result_refs`
- `accepted_output_refs`
- `evidence_refs`
- `verification_refs`
- `graph_refs`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `artifact_refs`
- `replay_refs`
- `operator_visible_refs`
- `pattern_specific_refs`
- `result`

Validation rules:

- Passing records require every ref family above.
- Passing records require pattern-specific refs.
- Passing records must not include single-site, scaffold-only, or unsafe-action diagnostics.
- Failed or needs-review records require missing refs or failure refs.

## TargetAIRecommendationRecord

Framework-neutral AI recommendation used by planning, extraction assistance, verification, drift repair, or recovery.

Fields:

- `id`
- `run_ref`
- `subject`
- `recommendation_ref`
- `accepted`
- `policy_decision_refs`
- `tool_call_refs`
- `trace_refs`
- `blocked_action_refs`
- `repair_frontier_refs`
- `result`

Validation rules:

- Accepted recommendations require policy decision refs, tool call refs, and trace refs.
- Blocked recommendations require blocked action refs and policy denial refs.
- Recommendation records must not contain framework-native state refs.

## TargetRuntimeReport

Aggregate operator-visible report and fixture assertion surface.

Fields:

- `id`
- `fixture_id`
- `run_ref`
- `objective_ref`
- `plan_ref`
- `status`
- `completion_result`
- `covered_patterns`
- `pattern_record_refs`
- `accepted_output_refs`
- `evidence_refs`
- `verification_refs`
- `graph_refs`
- `export_receipt_refs`
- `output_manifest_refs`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `artifact_refs`
- `ai_recommendation_refs`
- `repair_action_refs`
- `review_item_refs`
- `recovery_action_refs`
- `privacy_lifecycle_refs`
- `replay_bundle_ref`
- `operator_status`
- `failure_type`
- `failure_report_refs`
- `missing_ref_fields`
- `diagnostics`

Validation rules:

- `complete` requires pass result, at least seven covered patterns, no failure type, no missing refs, and all required ref families.
- `needs_review` requires review or recovery refs and must not publish false completion.
- `blocked` requires policy refs and failure refs.
- `failed` requires failure type and failure refs.

## TargetRuntimeFixtureManifest

Deterministic fixture declaration for target runtime CLI and tests.

Fields:

- `id`
- `scenario`
- `profile_refs`
- `expected_status`
- `expected_completion_result`
- `expected_operator_status`
- `expected_failure_type`
- `expected_pattern_count`
- `negative_case`

Validation rules:

- Must include `target` in profile refs.
- `expected_pattern_count` must be at least 7 for complete fixtures.
- Negative fixtures must expect `fail` or `blocked`.
- Failure type is required for negative fixtures.

## State Transitions

```text
objective_received
  -> plan_approved
  -> frontier_scheduled
  -> sources_acquired
  -> ai_recommendations_recorded
  -> normalized_and_extracted
  -> evidence_verified
  -> graph_projected
  -> outputs_materialized
  -> export_recorded
  -> replay_closed
  -> complete
```

Alternative terminal states:

- `blocked`: policy denial before acquisition, AI tool execution, browser/credential use, publication, export, or replay exposure.
- `needs_review`: missing evidence, contradiction, drift requiring human decision, or partial export.
- `failed`: replay mismatch, oracle mismatch, false-complete attempt, or non-recoverable runtime error.
