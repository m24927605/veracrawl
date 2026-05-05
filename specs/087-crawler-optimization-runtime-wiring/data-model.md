# Data Model: Crawler Optimization Runtime Wiring

## RuntimeOptimizationSignalSet

- `id`
- `fixture_id`
- `run_ref`
- `objective_ref`
- `candidate_url`
- `source_anchor_ref`
- `source_signal_refs`
- `policy_decision_refs`
- `allowed`
- `blocked_reason_refs`

Validation:

- Candidate URL must be absolute HTTP(S).
- Blocked signal sets must include blocked reason refs.
- Allowed signal sets must include source anchors and policy refs.

## RuntimeFrontierOptimizationDecision

- `id`
- `fixture_id`
- `signal_set_ref`
- `candidate_url`
- `scheduler_action`
- `scheduler_priority`
- `frontier_score_ref`
- `blocked_reason_refs`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `replay_bundle_ref`

Validation:

- `enqueue` decisions require score refs and positive priority.
- `block` decisions require blocked reason refs.
- Every decision requires replay lineage.

## RuntimeDomExtractionContext

- `id`
- `fixture_id`
- `normalized_document_ref`
- `dom_context_ref`
- `extractor_plan_ref`
- `extractor_attempt_refs`
- `field_confidence_refs`
- `abstention_decision_refs`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `replay_bundle_ref`

Validation:

- Passing contexts require DOM, extractor plan, attempts, confidence refs, and
  replay refs.
- Accepted fields cannot rely on LLM output as source evidence.

## RuntimeDedupeRankingDecision

- `id`
- `fixture_id`
- `input_candidate_refs`
- `canonicalization_refs`
- `fingerprint_refs`
- `identity_decision_refs`
- `duplicate_suppression_ref`
- `ranking_score_refs`
- `ranked_output_set_ref`
- `retained_refs`
- `suppressed_refs`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `replay_bundle_ref`

Validation:

- Duplicate suppression must not suppress all candidates.
- Ranking refs must map to retained refs.
- Replay refs are required.

## RuntimeOptimizationAggregate

- `id`
- `fixture_id`
- `lower_decision_refs`
- `metric_slice_refs`
- `optimization_report_ref`
- `completion_result`
- `failure_type`
- `diagnostics`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `replay_bundle_refs`

Validation:

- Passing aggregates require all lower decision refs, metrics, report refs, and
  replay lineage.
- Non-pass aggregates require typed failure and diagnostics.
