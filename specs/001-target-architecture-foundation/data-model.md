# Data Model: VeraCrawl Target Architecture Foundation

This model materializes the foundation subset clarified for `001-target-architecture-foundation`. Field names follow `docs/07-data-contracts.md`; implementation may add narrow helper fields only when they preserve canonical semantics and appear in schema export tests.

## Ownership Rules

| Entity group | Owner service/package | Mutation rule |
| --- | --- | --- |
| CommandEnvelope, CommandResult | target aggregate owner | Only the owner service for the target aggregate may commit or reject the command. |
| CrawlRunEvent | `runtime_events` append path plus originating owner | Events are append-only and ordered by `(run_id, sequence)`. |
| PolicyDecision | `control` / `policy` | Decisions are append-only and referenced by commands, adapter results, traces, and replay manifests. |
| SourceAdapterResult | owner by adapter type | Fetch-like adapters: `fetch`; browser: `browser`; authorized session/manual seed/prior snapshot: `control`; document source: `normalize`; file import: `artifact_lifecycle`. |
| Agent runtime contracts and traces | `agents` | Agent framework adapters may emit diagnostic refs, but canonical state is VeraCrawl-owned. |
| ReplayBundleManifest | `review_replay` with `runtime_events` inputs | Completeness checks must fail or return needs-review when required refs are missing. |
| Fixture/oracle contracts | `tests` / foundation fixture runner | Fixture definitions are immutable test inputs and must declare all tolerances explicitly. |
| TargetContractAreaCoverage | `contracts` / target owner services | Broader `docs/07` target areas outside the materialized subset are explicitly registered with owner, status, follow-up gate, replay impact, privacy impact, and required tests before target-complete claims. |

Agents may initiate tool commands, but agents are not owner services for durable aggregates outside `agents`.

## Foundation Entities

### CommandEnvelope

Fields:

- `id`
- `command_type`
- `target_aggregate_type`
- `target_aggregate_id`
- `expected_version`
- `idempotency_key`
- `actor_ref`
- `precondition_refs`
- `policy_decision_refs`
- `approval_decision_refs`
- `payload_ref`
- `status`
- `created_at`

Validation:

- `command_type` must resolve to a `CommandTypeSpec`.
- `payload_ref` must resolve to a registered payload schema.
- `expected_version` is required when the referenced `CommandTypeSpec` requires it.
- `status` transitions only through `proposed -> accepted|rejected -> committed|failed`.
- `policy_decision_refs` must include every required decision type declared by the command type.

Relationships:

- Has one `CommandResult`.
- May emit many `CrawlRunEvent` records.
- May be referenced by `ToolCallTrace`.

### CommandResult

Fields:

- `id`
- `command_id`
- `result`
- `emitted_event_refs`
- `output_refs`
- `rejection_reasons`
- `error`
- `created_at`

Validation:

- `command_id` must resolve to an existing `CommandEnvelope`.
- `result=committed` requires at least one emitted event for mutating commands.
- `result=rejected` requires at least one rejection reason.
- `result=duplicate` must preserve the original command result ref.

### CommandTypeSpec

Fields:

- `id`
- `command_type`
- `owner_service`
- `target_aggregate_type`
- `payload_schema_ref`
- `precondition_refs`
- `required_policy_decision_types`
- `approval_required`
- `required_approval_subject_types`
- `expected_version_required`
- `lease_required`
- `emitted_event_types`
- `failure_record_type`
- `created_at`

Validation:

- `owner_service` must be one of the owner services defined by `docs/07-data-contracts.md`.
- `emitted_event_types` must resolve to event specs.
- A command that mutates a foundation entity must appear in the registry before implementation can claim success.

### CrawlRunEvent

Fields:

- `id`
- `run_id`
- `objective_id`
- `crawl_plan_id`
- `event_version`
- `sequence`
- `event_type`
- `event_type_spec_id`
- `payload_ref`
- `actor`
- `agent_id`
- `model_id`
- `prompt_version`
- `prompt_ref`
- `tool_name`
- `tool_version`
- `tool_input_schema_ref`
- `tool_output_schema_ref`
- `input_refs`
- `output_refs`
- `decision`
- `reason`
- `confidence`
- `state_before`
- `state_after`
- `causation_id`
- `correlation_id`
- `trace_id`
- `run_plan_snapshot_id`
- `policy_snapshot_id`
- `policy_decision_refs`
- `memory_snapshot_refs`
- `graph_snapshot_refs`
- `idempotency_key`
- `error`
- `timestamp`

Validation:

- `(run_id, sequence)` must be unique and contiguous for replay.
- `event_type_spec_id` must validate `payload_ref`.
- Replay-critical lineage refs may be redacted only to stable redacted refs, not removed.
- `state_before` and `state_after` are required for state transition events.

### PolicyDecision

Fields:

- `id`
- `run_id`
- `objective_id`
- `policy_snapshot_id`
- `decision_type`
- `subject_ref`
- `decision`
- `reasons`
- `evaluated_rules`
- `input_refs`
- `created_at`

Validation:

- `decision` is `allow`, `deny`, or `require_review`.
- `deny` and `require_review` require non-empty reasons.
- Commands, source adapters, agent context assembly, browser steps, credentials, export, memory, graph signal use, artifact lifecycle, retention, and recovery actions must not proceed when the relevant decision is `deny`.

### SourceAdapterSpec

Fields:

- `id`
- `name`
- `version`
- `adapter_type`
- `supported_source_types`
- `metadata_schema_ref`
- `transformation_schema_ref`
- `default_rate_limits`
- `credential_requirements`
- `policy_refs`
- `idempotency_key_template`
- `freshness_semantics`
- `created_at`

Validation:

- `adapter_type` must be one of `http`, `browser_snapshot`, `sitemap`, `rss`, `authorized_session`, `api_source`, `document_source`, `file_import`, `manual_seed`, or `prior_snapshot`.
- `policy_refs` must cover source scope, rate/budget, credential, and adapter-specific safety gates.

### SourceAdapterResult

Fields:

- `id`
- `run_id`
- `adapter_spec_id`
- `adapter_type`
- `result_type`
- `output_refs`
- `policy_decision_refs`
- `replay_event_refs`
- `idempotency_key`
- `status`
- `created_at`

Validation:

- `adapter_type` and `result_type` must match the allowed result mapping from `docs/07-data-contracts.md`.
- `status=blocked` requires a deny or require-review `PolicyDecision`.
- Non-fetch adapters must not emit `FetchResult` or `PageSnapshot` refs unless their natural result mapping permits them.
- `replay_event_refs` must include `source_adapter_result_recorded` for completed adapter invocations.

### AgentRuntimeSpec

Fields:

- `id`
- `name`
- `version`
- `implementation_language`
- `runtime_type`
- `adapter_name`
- `allowed_agent_roles`
- `supported_tool_protocols`
- `context_ref_schema`
- `command_envelope_schema_ref`
- `event_schema_ref`
- `policy_refs`
- `framework_state_persistence`
- `replay_contract_ref`
- `created_at`

Validation:

- `implementation_language` is `python`.
- `runtime_type=agent_framework_adapter` is allowed only behind the adapter contract.
- `framework_state_persistence` must be `forbidden` or `diagnostic_only`.
- Core packages must not import concrete framework adapter modules.

### AgentToolSpec

Fields:

- `id`
- `name`
- `version`
- `tool_type`
- `allowed_agent_roles`
- `input_schema_ref`
- `output_schema_ref`
- `approval_required`
- `policy_refs`
- `created_at`

Validation:

- Mutating tools must use `tool_type=mutate_with_policy`.
- Mutating tools must produce a `CommandEnvelope`, `CommandResult`, `ToolCallTrace`, and relevant event refs.

### ContextRef

Fields:

- `id`
- `ref_type`
- `target_ref`
- `trust_level`
- `taint_labels`
- `redaction_policy_ref`
- `retention_policy_ref`
- `created_at`

Validation:

- Web-derived content must have untrusted or mixed trust labeling before prompt assembly.
- Credential material must not be represented as raw prompt-visible context.

### ContextBundle

Fields:

- `id`
- `run_id`
- `context_refs`
- `sanitized_context_ref`
- `excluded_context_refs`
- `exclusion_reasons`
- `credential_exposure_check_ref`
- `prompt_injection_policy_ref`
- `created_at`

Validation:

- Excluded refs require reasons.
- Sanitized context must be referenced by stable artifact/ref IDs.

### AgentRunRequest

Fields:

- `id`
- `run_id`
- `agent_role`
- `runtime_spec_id`
- `objective_ref`
- `context_bundle_id`
- `allowed_tool_spec_refs`
- `required_output_schema_ref`
- `loop_budget_ref`
- `policy_decision_refs`
- `created_at`

Validation:

- `agent_role` must be a target role from docs.
- `runtime_spec_id` must resolve to an `AgentRuntimeSpec`.
- Allowed tools must be compatible with the agent role and policy decisions.

### AgentRunResult

Fields:

- `id`
- `agent_run_request_id`
- `agent_action_trace_id`
- `output_ref`
- `proposed_tool_call_refs`
- `recommendation_refs`
- `status`
- `error`
- `created_at`

Validation:

- `status=completed` requires an `AgentActionTrace`.
- Failed/escalated/cancelled runs must preserve error or review refs.

### ModelRequest

Fields:

- `id`
- `agent_run_request_id`
- `provider_name`
- `model_id`
- `prompt_template_ref`
- `prompt_template_version`
- `context_bundle_id`
- `tool_schema_refs`
- `response_schema_ref`
- `redaction_policy_ref`
- `created_at`

Validation:

- Must reference sanitized context, not raw credential or untrusted unsanitized page text.

### ModelResponse

Fields:

- `id`
- `model_request_id`
- `response_ref`
- `parsed_output_ref`
- `tool_request_refs`
- `safety_filter_result_ref`
- `status`
- `created_at`

Validation:

- `status=invalid_schema` blocks tool execution until repaired or reviewed.

### AgentActionTrace

Fields:

- `id`
- `run_id`
- `objective_id`
- `agent_id`
- `agent_role`
- `runtime_spec_id`
- `model_call_trace_refs`
- `context_bundle_trace_id`
- `tool_call_trace_refs`
- `command_result_refs`
- `policy_decision_refs`
- `input_refs`
- `output_refs`
- `reasoning_summary_ref`
- `assumptions`
- `alternatives_considered`
- `uncertainty_notes`
- `redaction_policy_ref`
- `retention_policy_ref`
- `replay_required`
- `created_at`

Validation:

- Structured reasoning summaries are stored as auditable summaries, assumptions, alternatives, rationale refs, and uncertainty notes, not hidden chain-of-thought.
- `replay_required=true` for foundation conformance fixtures.

### ModelCallTrace

Fields:

- `id`
- `run_id`
- `agent_action_trace_id`
- `provider_name`
- `model_id`
- `model_version`
- `prompt_template_ref`
- `prompt_template_version`
- `context_bundle_trace_id`
- `request_ref`
- `response_ref`
- `token_usage`
- `latency_ms`
- `safety_filter_result_ref`
- `redaction_policy_ref`
- `raw_prompt_persisted`
- `raw_response_persisted`
- `replay_mode`
- `created_at`

Validation:

- Raw prompt/response persistence must follow policy.
- Provider-native traces are diagnostic and cannot replace this trace.

### ToolCallTrace

Fields:

- `id`
- `run_id`
- `agent_action_trace_id`
- `tool_spec_id`
- `tool_name`
- `tool_version`
- `input_schema_ref`
- `output_schema_ref`
- `input_ref`
- `output_ref`
- `command_envelope_id`
- `command_result_id`
- `policy_decision_refs`
- `approval_decision_refs`
- `status`
- `error`
- `created_at`

Validation:

- `status=executed` requires a committed or rejected `CommandResult`.
- Policy-denied tool calls must be recorded as rejected or failed, never silently dropped.

### ContextBundleTrace

Fields:

- `id`
- `run_id`
- `agent_id`
- `context_ref_schema`
- `included_context_refs`
- `excluded_context_refs`
- `taint_labels`
- `sanitized_context_ref`
- `redaction_policy_ref`
- `credential_exposure_check_ref`
- `memory_retrieval_trace_refs`
- `graph_snapshot_refs`
- `evidence_refs`
- `created_at`

Validation:

- Included and excluded refs must be reconstructable during replay.

### ReplayBundleManifest

Fields:

- `id`
- `run_id`
- `objective_id`
- `crawl_plan_id`
- `event_cursor_refs`
- `event_schema_versions`
- `contract_schema_versions`
- `artifact_hash_refs`
- `source_adapter_result_refs`
- `command_result_refs`
- `agent_action_trace_refs`
- `model_call_trace_refs`
- `tool_call_trace_refs`
- `context_bundle_trace_refs`
- `policy_decision_refs`
- `projection_watermark_refs`
- `memory_retrieval_trace_refs`
- `graph_build_manifest_refs`
- `export_receipt_refs`
- `deterministic_clock_ref`
- `randomness_seed_ref`
- `redaction_map_ref`
- `missing_ref_behavior`
- `replay_mode`
- `completeness_result`
- `created_at`

Validation:

- `missing_ref_behavior=fail_replay` must set `completeness_result=fail` when required refs are missing.
- `allow_with_gap_report` may set `needs_review` but cannot set `pass` if required refs are missing.

### BenchmarkFixtureManifest

Fields:

- `id`
- `name`
- `profile_refs`
- `source_server_ref`
- `seed_urls`
- `source_adapter_refs`
- `auth_fixture_ref`
- `expected_crawl_graph_ref`
- `expected_page_type_ref`
- `expected_output_ref`
- `expected_evidence_coverage_ref`
- `expected_event_sequence_ref`
- `expected_replay_bundle_ref`
- `expected_artifact_hashes_ref`
- `failure_injection_ref`
- `thresholds_ref`

Validation:

- Foundation fixtures must include explicit event, replay, artifact hash, and failure injection refs even when the fixture is intentionally small.
- Missing oracle files fail the fixture run.

### ExpectedOutputOracle

Fields:

- `id`
- `fixture_id`
- `expected_output_type`
- `expected_items`
- `required_field_coverage`
- `required_evidence_level`
- `allowed_optional_misses`
- `forbidden_outputs`
- `comparison_mode`

Validation:

- `comparison_mode=tolerance` requires explicit threshold refs.
- Expected outputs must not publish without evidence coverage refs.

### ExpectedEvidenceCoverageOracle

Fields:

- `id`
- `fixture_id`
- `required_anchor_refs`
- `required_artifact_refs`
- `privacy_classification_expectations`
- `missing_evidence_behavior`
- `accepted_verification_required`

Validation:

- Required evidence anchors must resolve.
- Missing evidence must fail or route to needs-review, never publication.

### ExpectedGraphOracle

Fields:

- `id`
- `fixture_id`
- `expected_nodes`
- `expected_edges`
- `forbidden_edges`
- `expected_projection_watermarks`
- `false_merge_cases`
- `false_split_cases`

Validation:

- Graph expectations are fixture/oracle checks only in this foundation.
- Graph signals must not satisfy evidence requirements.

### FailureInjectionPlan

Fields:

- `id`
- `fixture_id`
- `injected_failures`
- `expected_failure_records`
- `expected_recovery_actions`
- `expected_dead_letters`
- `expected_events`
- `expected_operator_visible_status`

Validation:

- Each injected failure must map to an expected event, failure record, or blocked/needs-review result.

### DRRestoreOracle

Fields:

- `id`
- `fixture_id`
- `required_restore_phase_refs`
- `required_backup_manifest_refs`
- `required_validation_gate_refs`
- `expected_report_status`
- `unresolved_ref_behavior`

Validation:

- Missing restore phase, backup manifest, or validation gate refs must fail or return needs-review.
- This foundation defines oracle shape only and does not implement production DR restore.

### TargetContractAreaCoverage

Fields:

- `id`
- `contract_area`
- `owner_service`
- `coverage_status`
- `materialized_contract_refs`
- `placeholder_contract_refs`
- `canonical_store_impact`
- `artifact_store_impact`
- `event_refs`
- `projection_refs`
- `replay_impact`
- `privacy_lifecycle_impact`
- `required_test_refs`
- `followup_spec_gate`

Validation:

- `contract_area` must map to a target area in `docs/07-data-contracts.md`.
- `coverage_status` is `materialized`, `foundation_placeholder`, or `deferred_with_gate`.
- Deferred target areas require a follow-up spec gate and cannot be claimed target-complete.

## Foundation State Transitions

### CommandEnvelope

```text
proposed -> accepted -> committed
proposed -> rejected
accepted -> failed
accepted -> committed
```

Rules:

- `committed` requires a `CommandResult` with emitted event refs.
- `rejected` requires policy or validation reasons.
- `failed` requires an error object and failure/recovery visibility where applicable.

### SourceAdapterResult

```text
pending -> succeeded
pending -> blocked
pending -> failed
pending -> partial
```

Rules:

- `blocked` requires policy decision refs.
- `succeeded` requires at least one output ref unless the adapter result type is a valid no-output control result.
- `partial` requires explicit output and missing-output refs.

### ReplayBundleManifest

```text
draft -> pass
draft -> fail
draft -> needs_review
```

Rules:

- Missing required refs route to `fail` or `needs_review`, never `pass`.
- Redacted replay may pass only when stable redacted refs preserve lineage.

## Registry Consistency Requirements

The implementation must include a machine-readable registry that maps:

- every foundation contract to owner service, Python model, schema ref, and tests
- every command type to payload schema, required policy gates, emitted events, and owner service
- every event type to payload schema, replay-critical refs, and state transition requirements
- every source adapter type to natural result types and owner service
- every agent adapter conformance fixture to expected canonical traces and command results
- every fixture to expected event, replay, artifact, policy, and failure oracles
