# Data Model: VeraCrawl Memory Kernel

## MemoryEvent

- `id`
- `run_ref`
- `scope_ref`
- `memory_type`
- `content_ref`
- `evidence_refs`
- `provenance_refs`
- `trust_level`
- `taint_labels`
- `promotion_policy_ref`
- `poisoning_check_ref`
- `sanitized_context_ref`
- `allowed_prompt_use`
- `freshness_ref`
- `status`
- `invalidated_by_ref`
- `supersedes_memory_ref`
- `policy_decision_refs`

## MemoryRetrievalTrace

- `id`
- `run_ref`
- `query_ref`
- `scope_ref`
- `retrieved_memory_refs`
- `excluded_memory_refs`
- `exclusion_reasons`
- `policy_decision_refs`
- `cross_scope_tunnel_ref`
- `taint_labels`
- `freshness_cutoff_ref`
- `retrieval_index_ref`
- `sanitized_context_ref`
- `completion_result`

## CrossScopeMemoryTunnel

- `id`
- `source_scope_ref`
- `target_scope_ref`
- `allowed_memory_types`
- `authorization_ref`
- `policy_decision_refs`
- `sanitized_only`
- `evidence_ref_required`
- `taint_exclusion_rules`
- `status`

## OperationalTemporalMemoryRecord

- `id`
- `run_ref`
- `scope_ref`
- `memory_type`
- `memory_event_refs`
- `valid_from_ref`
- `valid_to_ref`
- `evidence_refs`
- `status`

## MemoryKernelReport

- `id`
- `run_ref`
- `memory_event_refs`
- `retrieval_trace_ref`
- `tunnel_ref`
- `operational_record_refs`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `failure_report_refs`
- `missing_ref_fields`
- `operator_status`
- `completion_result`
