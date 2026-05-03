# Data Model: Graph And Memory Production Runtime

## GraphMemoryProductionRuntimeReport

Fields:

- `id`, `fixture_id`, `run_ref`
- dependency refs:
  - `live_normalization_runtime_report_ref`
  - `live_evidence_verification_runtime_report_ref`
  - `multi_agent_repair_report_ref`
  - `advanced_graph_projection_report_ref`
  - `graph_frontier_review_runtime_report_ref`
  - `temporal_kg_runtime_report_ref`
  - `memory_kernel_report_ref`
- graph refs:
  - `url_graph_refs`, `redirect_graph_refs`, `canonical_graph_refs`
  - `page_structure_graph_refs`, `entity_graph_refs`, `task_graph_refs`
  - `temporal_graph_refs`, `graph_signal_refs`
  - `projection_watermark_refs`
- memory refs:
  - `site_memory_event_refs`, `task_memory_event_refs`
  - `repair_memory_event_refs`, `run_diary_memory_event_refs`
  - `memory_retrieval_trace_refs`, `memory_write_refs`
  - `memory_freshness_refs`, `memory_invalidation_refs`
- decision/explanation refs:
  - `frontier_decision_refs`
  - `repair_explanation_refs`
  - `operator_explanation_refs`
  - `owner_command_refs`
  - `review_escalation_refs`
- publication boundary refs:
  - `source_evidence_refs`
  - `verification_decision_refs`
  - `policy_decision_refs`
  - `privacy_lifecycle_refs`
  - `command_record_refs`, `event_cursor_refs`, `outbox_refs`
  - `replay_bundle_ref`
- failure diagnostics:
  - `failure_type`
  - `failure_report_refs`
  - `missing_ref_fields`
  - `graph_as_evidence_refs`
  - `memory_as_evidence_refs`
  - `stale_memory_refs`
  - `diagnostics`
- result:
  - `operator_status`
  - `completion_result`

Validation:

- `pass` requires every dependency group, graph group, memory group,
  explanation group, publication-boundary group, command/event/outbox group, and
  replay refs.
- `pass` rejects any failure type, graph-as-evidence refs, memory-as-evidence
  refs, stale memory refs, failure refs, or missing ref fields.
- non-pass requires a typed `failure_type` plus failure refs, missing refs, or
  boundary violation refs.

## GraphMemoryProductionFixtureManifest

Fields:

- `id`
- `scenario`
- `profile_refs`
- `expected_completion_result`
- `expected_operator_status`
- `expected_failure_type`
- `negative_case`
- `required_ref_types`

Validation:

- target profile is required.
- required ref types are explicit.
- negative fixtures must not expect pass and must include an expected failure
  type.

## State Transitions

```text
planned -> dependency_checked -> graph_memory_projected -> decisions_explained -> replay_checked -> pass
planned -> dependency_checked -> fail(reason)
planned -> graph_memory_projected -> boundary_violation(reason) -> fail(reason)
planned -> decisions_explained -> replay_mismatch -> fail(replay_mismatch)
```
