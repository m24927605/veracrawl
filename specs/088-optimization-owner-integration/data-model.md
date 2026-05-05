# Data Model: Optimization Owner-Service Integration Roadmap

## OptimizationOwnerIntegrationRoadmap

- **Purpose**: Records the approved specs 089-096, dependency order, and
  non-goal boundaries.
- **Fields**:
  - `id`
  - `spec_refs`
  - `dependency_refs`
  - `policy_decision_refs`
  - `command_record_refs`
  - `event_cursor_refs`
  - `outbox_refs`
  - `replay_bundle_ref`
- **Validation Rules**:
  - Must include specs 089-096.
  - Must state that specs 089-096 do not replace or weaken specs 069-075.
  - Must reject missing command/event/outbox/replay refs.

## SchedulerOptimizationIntegration

- **Purpose**: Scheduler-owned adoption of runtime frontier decisions.
- **Fields**:
  - `id`
  - `fixture_id`
  - `run_ref`
  - `frontier_decision_refs`
  - `enqueue_refs`
  - `blocked_refs`
  - `retired_refs`
  - `stop_reason_refs`
  - `scheduler_priority_refs`
  - `policy_decision_refs`
  - `command_record_refs`
  - `event_cursor_refs`
  - `outbox_refs`
  - `replay_bundle_ref`
- **Validation Rules**:
  - At least one enqueue, block, retire, or stop outcome is required.
  - Enqueued refs require corresponding frontier decision refs.
  - Blocked/retired refs require stop reason or policy refs.
  - Replay refs are mandatory.

## NormalizeOptimizationIntegration

- **Purpose**: Normalize/browser-owned adoption of DOM context.
- **Fields**:
  - `id`
  - `fixture_id`
  - `normalized_document_ref`
  - `dom_context_ref`
  - `retained_node_refs`
  - `page_zone_refs`
  - `interactive_element_refs`
  - `context_reduction_ratio`
  - `artifact_refs`
  - `policy_decision_refs`
  - `command_record_refs`
  - `event_cursor_refs`
  - `outbox_refs`
  - `replay_bundle_ref`
- **Validation Rules**:
  - DOM context and normalized document refs are required.
  - Retained node refs and artifact refs are required.
  - Context reduction ratio must be between 0 and 1.

## ExtractVerifyOptimizationIntegration

- **Purpose**: Extract/verify-owned adoption of fallback attempts and field
  confidence.
- **Fields**:
  - `id`
  - `fixture_id`
  - `normalized_document_ref`
  - `extractor_plan_ref`
  - `accepted_attempt_refs`
  - `rejected_attempt_refs`
  - `field_confidence_refs`
  - `abstention_refs`
  - `review_refs`
  - `publication_eligible_field_refs`
  - `policy_decision_refs`
  - `command_record_refs`
  - `event_cursor_refs`
  - `outbox_refs`
  - `replay_bundle_ref`
- **Validation Rules**:
  - LLM-only, graph-only, memory-only, and ranking-only refs must not be accepted.
  - Accepted attempts require field confidence refs.
  - Low-confidence fields require abstention or review refs.

## DedupeIdentityOptimizationIntegration

- **Purpose**: Scheduler/normalize/graph-owned adoption of canonicalization,
  fingerprints, identity decisions, and duplicate suppression.
- **Fields**:
  - `id`
  - `fixture_id`
  - `canonicalization_refs`
  - `fingerprint_refs`
  - `identity_decision_refs`
  - `duplicate_suppression_ref`
  - `retained_refs`
  - `suppressed_refs`
  - `variant_refs`
  - `policy_decision_refs`
  - `command_record_refs`
  - `event_cursor_refs`
  - `outbox_refs`
  - `replay_bundle_ref`
- **Validation Rules**:
  - Canonicalization, fingerprint, and identity refs are required.
  - Suppressed refs must not overlap retained refs.
  - Variant refs must be retained or routed to review.

## RankingPublicationOptimizationIntegration

- **Purpose**: Publish/projection-owned adoption of ranking outputs.
- **Fields**:
  - `id`
  - `fixture_id`
  - `ranked_output_set_ref`
  - `ranking_score_refs`
  - `retained_output_refs`
  - `verification_status_refs`
  - `publication_gate_refs`
  - `missing_optional_feature_refs`
  - `policy_decision_refs`
  - `command_record_refs`
  - `event_cursor_refs`
  - `outbox_refs`
  - `replay_bundle_ref`
- **Validation Rules**:
  - Ranked output set and ranking score refs are required.
  - Ranking must not change verification status refs.
  - Missing optional feature refs must remain absent, not fabricated.

## CostCacheBudgetOptimizationIntegration

- **Purpose**: Ops-owned cost, cache, metric, and budget integration.
- **Fields**:
  - `id`
  - `fixture_id`
  - `fetch_cost`
  - `browser_cost`
  - `token_cost`
  - `cache_hit_refs`
  - `stale_cache_refs`
  - `metric_slice_refs`
  - `budget_exhausted`
  - `diagnostics`
  - `completion_result`
  - `policy_decision_refs`
  - `command_record_refs`
  - `event_cursor_refs`
  - `outbox_refs`
  - `replay_bundle_ref`
- **Validation Rules**:
  - Cost values must be non-negative.
  - Stale cache refs or budget exhaustion fail the integration.
  - Metric and replay refs are mandatory for pass.

## DriftRecoveryFeedbackIntegration

- **Purpose**: Review/replay and ops-owned drift and recovery feedback.
- **Fields**:
  - `id`
  - `fixture_id`
  - `drift_type`
  - `affected_ref`
  - `retry_class`
  - `repair_outcome`
  - `memory_advisory_refs`
  - `unsafe_recovery_refs`
  - `diagnostics`
  - `completion_result`
  - `policy_decision_refs`
  - `command_record_refs`
  - `event_cursor_refs`
  - `outbox_refs`
  - `replay_bundle_ref`
- **Validation Rules**:
  - Unsafe recovery fails the integration.
  - Memory refs are advisory only.
  - Drift type and affected refs are required.

## OptimizationRegressionReleaseGate

- **Purpose**: Aggregate release-blocking gate over specs 089-095.
- **Fields**:
  - `id`
  - `fixture_id`
  - `lower_integration_refs`
  - `missing_lower_integration_refs`
  - `metric_slice_refs`
  - `false_ready_guard_refs`
  - `diagnostics`
  - `completion_result`
  - `policy_decision_refs`
  - `command_record_refs`
  - `event_cursor_refs`
  - `outbox_refs`
  - `replay_bundle_ref`
- **Validation Rules**:
  - Passing gates require all lower integration refs.
  - Missing replay, stale cache, unsafe recovery, quality regression, duplicate
    regression, ranking regression, cost regression, and missing metrics fail.

## State Transitions

```text
planned -> integrated -> release_ready
planned -> blocked
integrated -> regression_failed
regression_failed -> repaired -> integrated
```

- `integrated` requires typed owner-service integration refs.
- `release_ready` requires spec 096 pass.
- `regression_failed` requires typed diagnostics and replay refs.
