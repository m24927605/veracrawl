# Data Contracts

This document defines the first production contracts for VeraCrawl. These are conceptual contracts, not implementation code.

The contracts must support an AI-native crawler: user objectives become crawl plans, agent tool calls become replayable events, and AI-generated outputs remain bounded by evidence and verification contracts.

## ID And Immutability Strategy

IDs should be explicit and stable:

- control entities use generated stable IDs
- raw artifacts use content-addressed refs where possible
- events use append-only generated IDs plus per-run sequence
- frontier dedup uses run ID plus canonical URL plus source adapter
- fetch attempts use attempt IDs and idempotency keys
- current factual outputs require uniqueness by `fact_key` and status
- published outputs require immutable versioned manifests
- state transitions require transition version or fencing token

Contracts may show `id: string`, but implementation specs must define the concrete ID type, uniqueness constraint, dedup key, and immutability rule for each entity.

## Target Contract Profile

The target architecture requires the full contract surface needed for a powerful general-purpose AI agent web crawler. V1 restrictions still apply to V1 runtime paths, but target implementation must include explicit contracts for the broader capability.

Target contract manifest:

| Contract area | Target status | Target validation |
| --- | --- | --- |
| Project, Site, SafetyPolicySnapshot | required | customer authorization, policy, retention, privacy, and source scope are versioned and auditable |
| CrawlObjective, CrawlPlan, CrawlJob, CrawlRun, RunPlanSnapshot | required | objective, assumptions, alternatives, adapter choices, evidence requirements, and plan approval are replayable |
| CommandEnvelope, CommandResult, CrawlRunEvent, ReplayBundleManifest | required | every mutating action emits command/result/event records with causation and correlation IDs; replay bundles have manifests and completeness checks |
| AgentRuntimeSpec, AgentToolSpec, ContextRef, ContextBundle, AgentRunRequest, AgentRunResult, ModelRequest, ModelResponse, AgentActionTrace, ModelCallTrace, ToolCallTrace, ContextBundleTrace, MultiAgentWorkflow, AgentHandoff, CoordinationDecision | required | framework-neutral runtime, context, tool calls, model calls, coordination, redaction, prompt versions, and replay refs are durable |
| FrontierRecommendation, MemoryRetrievalTrace | required | agent recommendations and retrieved memories are recorded separately from durable state transitions |
| SourceAdapterSpec, SourceAdapterResult, AuthorizedSessionSpec, BrowserInteractionStep, CredentialUseAudit, DocumentNormalizationArtifact | required | HTTP, sitemap, RSS, browser, authorized session, API source, document source, prior snapshot, and manual seed adapters are contracted |
| FetchAttempt, FetchResult, PageSnapshot, NormalizedDocument, NormalizationManifest | required | raw artifacts, rendered artifacts, documents, and normalized outputs carry replayable transformation refs |
| ExtractionStrategy, ExtractionCandidate, EvidencePacket | required | schema-bound and approved exploratory extraction preserve anchors and source refs |
| VerificationRecommendation, VerificationDecision, ConflictRecord, AdjudicationDecision | required | evidence, contradictions, freshness, and review/adjudication are explicit |
| PublishedOutput, OutputManifest, EvidenceCoverageMap, OutputVerificationAggregate, VerifiedFact | required | immutable publication and fact projection preserve evidence and verification lineage |
| GraphBuildManifest, GraphNode, GraphEdge, GraphSignal, TemporalKGProjectionRecord, TemporalKGEntityIdentity | required | graph projections have input refs, watermarks, quality metrics, and evidence-derived temporal semantics |
| MemoryEvent, CrossScopeMemoryTunnel, OperationalTemporalMemoryRecord | required | memory has scope, trust, taint, promotion policy, freshness, invalidation, cross-scope authorization, operational temporal records, evidence refs, and prompt-use restrictions |
| ExportTargetSpec, ExportJob, ExportAttempt, ExportDeliveryReceipt, ExportWithdrawalJob, ExportWithdrawalAttempt | required | file, API, database, warehouse, object store, and queue targets reconcile delivery, correction, and withdrawal |
| ProjectionSpec, ProjectionWatermark, ProjectionRebuildJob, ProjectionMismatchReport, SchemaMigrationRun, EventMigrationRun, BackfillJob | required | migrations, rebuilds, watermarks, rollback, and deterministic hashes are contracted |
| ServiceOwnershipSpec, StateMachineSpec, FieldPresenceSpec, ReferenceSpec, EventTypeSpec | required | validation, ownership, event taxonomy, migration, projection rebuild, and state transition tests derive from contracts |
| QueueItem, ShardLease, RetryDeadLetterRecord, BackpressureSignal, AutoscalingDecision, ProjectionMismatchReport, DRRestorePlan, DRRestoreRun, DRRestoreReport | required | scale, reliability, queueing, projection mismatch, and DR behavior are contracted |
| FailureRecord, RecoveryAction, DriftEvent, QualityReport | required | failure, repair, drift, recovery, and operations are evented and reviewable |

Target adapter types:

- `http`
- `sitemap`
- `rss`
- `browser_snapshot`
- `authorized_session`
- `api_source`
- `document_source`
- `file_import`
- `manual_seed`
- `prior_snapshot`

Target export target types:

- `file`
- `api`
- `database`
- `warehouse`
- `object_store`
- `queue`

Target graph types:

- `url`
- `hyperlink`
- `redirect_canonical`
- `page_structure`
- `template`
- `entity`
- `source_evidence`
- `task`
- `temporal`

Target completion requires implementation specs to map every target contract to owner service, canonical store, artifact store, event types, projection outputs, replay behavior, privacy lifecycle, tests, and acceptance gates.

## V1 Contract Profile

V1 uses a restricted subset of the broader contracts:

- supported output types: `record | table | document_metadata | fact`
- supported export targets: `file | api`
- supported adapters: `http | sitemap | rss`, with `browser_snapshot` only after explicit approval
- unsupported until later profiles: dataset-scale exports, binary file workflows, arbitrary document understanding, cross-site tunnels, autonomous memory-derived planning

Broad enum values remain in contracts to show the platform direction, but implementation work for V1 must enforce this profile.

V1 contract manifest:

| Contract area | V1 status | V1 validation |
| --- | --- | --- |
| Project, Site, SafetyPolicySnapshot | required | all fields required except optional site-specific overrides |
| SchemaSpec, SchemaSnapshot, PublicationPolicySpec | required | output type limited to `record`, `table`, `document_metadata`, `fact` |
| CrawlObjective, CrawlPlan, CrawlJob, CrawlRun | required | one objective, one approved plan, one run in quickstart |
| CommandEnvelope, CommandResult, CrawlRunEvent | required | all mutating actions emit command and event records |
| PolicyDecision, ApprovalDecision, ReviewItem, ReviewDecision | required | every policy gate that can require review has typed approval/review subject coverage |
| AgentRuntimeSpec, AgentToolSpec | required | framework-neutral runtime and tool contracts; framework-native state forbidden |
| SourceAdapterSpec, FetchAttempt, FetchResult | required | adapter type limited to `http`, `sitemap`, `rss`; browser requires explicit approval |
| PageSnapshot, NormalizedDocument, NormalizationManifest | required | raw-to-normalized anchor maps required for evidence-bearing outputs |
| ExtractionStrategy, ExtractionCandidate, EvidencePacket | required | declared schemas only unless AI draft is approved |
| VerificationRecommendation, VerificationDecision | required | recommendation optional; durable decision required before publication |
| PublishedOutput, OutputManifest, EvidenceCoverageMap, OutputVerificationAggregate | required | output type limited to V1 subset |
| RunDiaryEvent | required | replay diary only; not used as planning memory |
| MemoryEvent | later | forbidden in V1 runtime paths |
| GraphBuildManifest, GraphNode, GraphEdge | optional | only URL/page-structure/template graph types allowed |
| GraphSignal | later | forbidden in V1 acceptance or confidence paths |
| ExportTargetSpec, ExportJob, ExportAttempt, ExportDeliveryReceipt | optional | only local file and Result API targets in V1 |
| ExportWithdrawalJob, ExportWithdrawalAttempt | later | conceptual only unless production export is enabled |
| ConflictRecord, AdjudicationDecision | optional | required only when conflicts occur |
| ProjectionSpec, ServiceOwnershipSpec, StateMachineSpec, FieldPresenceSpec, ReferenceSpec | required | used for validation and implementation tests |

V1 event subset:

| Event type | V1 status |
| --- | --- |
| command_received, command_committed, command_rejected | required |
| objective_created, plan_proposed, plan_approved | required |
| policy_evaluated, approval_decided, tool_called | required |
| frontier_transitioned, fetch_attempted, snapshot_written | required |
| processing_transitioned, candidate_created, evidence_built | required |
| verification_recommended, verification_decided | required |
| output_published, result_materialized, run_diary_written | required |
| review_created, review_decided, error_recorded | required |
| output_withdrawn, export_dispatched, export_delivered | optional only for Result API/file materialization |
| export_withdrawal_attempted, delete_propagated | later |
| conflict_adjudicated, recovery_action_started, recovery_action_completed | optional only when V1 conflict or failure path is triggered |
| memory_written, drift_detected | later; forbidden in V1 runtime paths |

V1 task subset:

| ProcessingTask.task_type | V1 status |
| --- | --- |
| normalize, classify_page, extract, build_evidence, verify, publish | required |
| write_memory | forbidden; use `RunDiaryEvent` |
| index_graph | optional only for URL/page-structure graph |

V1 field-level restrictions:

| Field | V1 rule |
| --- | --- |
| `RunPlanSnapshot.memory_snapshot_refs` | empty list |
| `RunPlanSnapshot.graph_snapshot_refs` | URL/page-structure graph refs only |
| `FrontierItem.memory_refs` | empty list |
| `FrontierItem.graph_refs` | URL/page-structure graph refs only |
| `EvidencePacket.memory_refs` | empty list |
| `EvidencePacket.graph_signal_refs` | empty list |
| `MemoryEvent.*` | forbidden in V1 runtime paths |
| `GraphSignal.*` | forbidden in V1 acceptance/confidence paths |
| `ExportTargetSpec.target_type` | `file | api` only |
| `SourceAdapterSpec.adapter_type` | `http | sitemap | rss`; browser only with explicit approval |

## ReferenceSpec

```yaml
ReferenceSpec:
  id: string
  ref_name: string
  source_entity_type: string
  target_entity_type: string
  cardinality: one | optional_one | many | optional_many
  allowed_scope: same_entity | same_run | same_project | cross_run | cross_project
  dangling_ref_policy: reject | allow_until_reconciled | tombstone
  cascade_policy: restrict | tombstone | delete_projection_only
  projection_rebuild_behavior: preserve_ref | rehydrate | tombstone
  created_at: timestamp
```

## FieldPresenceSpec

```yaml
FieldPresenceSpec:
  id: string
  entity_type: string
  state: string
  required_fields: list
  optional_fields: list
  forbidden_fields: list
  created_at: timestamp
```

## Project

```yaml
Project:
  id: string
  name: string
  owner_id: string
  default_policy_snapshot_id: string
  created_at: timestamp
  updated_at: timestamp
```

## Site

```yaml
Site:
  id: string
  project_id: string
  name: string
  base_urls: list
  allowed_domains: list
  default_source_adapters: list
  policy_snapshot_id: string
  created_at: timestamp
  updated_at: timestamp
```

## SafetyPolicySnapshot

```yaml
SafetyPolicySnapshot:
  id: string
  project_id: string
  site_id: string
  robots_policy: obey | warn | ignore_with_authorization
  terms_policy_ref: string
  authorization_refs: list
  credential_scope_refs: list
  rate_limits: object
  privacy_classification: public | internal | confidential | regulated
  pii_policy: object
  retention_policy: object
  prompt_injection_policy: object
  disallowed_actions: list
  created_at: timestamp
```

## SchemaSpec

```yaml
SchemaSpec:
  id: string
  project_id: string
  name: string
  version: string
  output_type: record | document_metadata | document | table | file | dataset | fact
  fields: list
  validators: list
  evidence_requirements: list
  publication_policy_refs: list
  created_at: timestamp
```

## SchemaSnapshot

```yaml
SchemaSnapshot:
  id: string
  schema_spec_id: string
  version: string
  field_ids: list
  field_paths: list
  validators: list
  evidence_requirements: list
  compatibility_level: backward_compatible | migration_required | breaking
  created_at: timestamp
```

## SchemaMigration

```yaml
SchemaMigration:
  id: string
  from_schema_snapshot_id: string
  to_schema_snapshot_id: string
  field_mappings:
    - from_field_ids: list
      to_field_ids: list
      change_type: unchanged | renamed | split | merged | removed | added
      transform_rule_ref: string
      default_value_policy: string
      null_handling: string
      lossy: boolean
      validators_to_rerun: list
  migration_notes: string
  export_backfill_required: boolean
  created_at: timestamp
```

## ValidatorResult

```yaml
ValidatorResult:
  id: string
  run_id: string
  schema_snapshot_id: string
  target_ref: string
  validator_ref: string
  result: pass | fail | warning | not_applicable
  reasons: list
  created_at: timestamp
```

## PublicationPolicySpec

```yaml
PublicationPolicySpec:
  id: string
  project_id: string
  schema_ref: string
  output_type: record | document_metadata | document | table | file | dataset | fact
  required_evidence_coverage: field | row | cell | section | file | item
  required_verification_methods: list
  allow_model_assisted_accept: boolean
  human_review_required: boolean
  conflict_policy: reject | review | publish_disputed
  freshness_requirements: object
  created_at: timestamp
```

## AgentToolSpec

```yaml
AgentToolSpec:
  id: string
  name: string
  version: string
  tool_type: read | propose | mutate_with_policy | review_only
  allowed_agent_roles: list
  input_schema_ref: string
  output_schema_ref: string
  approval_required: boolean
  policy_refs: list
  created_at: timestamp
```

## AgentRuntimeSpec

Agent runtimes are replaceable Python adapters behind a VeraCrawl-owned port. They must not define canonical domain state.

```yaml
AgentRuntimeSpec:
  id: string
  name: string
  version: string
  implementation_language: python
  runtime_type: native_veracrawl | model_provider_adapter | agent_framework_adapter
  adapter_name: string
  allowed_agent_roles: list
  supported_tool_protocols: list
  context_ref_schema: string
  command_envelope_schema_ref: string
  event_schema_ref: string
  policy_refs: list
  framework_state_persistence: forbidden | diagnostic_only
  replay_contract_ref: string
  created_at: timestamp
```

Rules:

- V1 must use `native_veracrawl` or `model_provider_adapter`.
- `agent_framework_adapter` is a later extension point and must be replaceable.
- Core contracts, events, commands, evidence, review, and publication flows must not depend on framework-native types.
- Any diagnostic framework trace must reference canonical VeraCrawl events rather than replace them.

## ContextRef

```yaml
ContextRef:
  id: string
  ref_type: objective | policy | schema | plan | snapshot | normalized_document | evidence | graph | memory | replay | artifact
  target_ref: string
  trust_level: trusted | untrusted | mixed | derived
  taint_labels: list
  redaction_policy_ref: string
  retention_policy_ref: string
  created_at: timestamp
```

## ContextBundle

```yaml
ContextBundle:
  id: string
  run_id: string
  context_refs: list
  sanitized_context_ref: string
  excluded_context_refs: list
  exclusion_reasons: list
  credential_exposure_check_ref: string
  prompt_injection_policy_ref: string
  created_at: timestamp
```

## AgentRunRequest

```yaml
AgentRunRequest:
  id: string
  run_id: string
  agent_role: planner | site_understanding | frontier | fetch_analysis | extractor | verifier | drift | memory | ops
  runtime_spec_id: string
  objective_ref: string
  context_bundle_id: string
  allowed_tool_spec_refs: list
  required_output_schema_ref: string
  loop_budget_ref: string
  policy_decision_refs: list
  created_at: timestamp
```

## AgentRunResult

```yaml
AgentRunResult:
  id: string
  agent_run_request_id: string
  agent_action_trace_id: string
  output_ref: string
  proposed_tool_call_refs: list
  recommendation_refs: list
  status: completed | failed | escalated | cancelled
  error: object
  created_at: timestamp
```

## ModelRequest

```yaml
ModelRequest:
  id: string
  agent_run_request_id: string
  provider_name: string
  model_id: string
  prompt_template_ref: string
  prompt_template_version: string
  context_bundle_id: string
  tool_schema_refs: list
  response_schema_ref: string
  redaction_policy_ref: string
  created_at: timestamp
```

## ModelResponse

```yaml
ModelResponse:
  id: string
  model_request_id: string
  response_ref: string
  parsed_output_ref: string
  tool_request_refs: list
  safety_filter_result_ref: string
  status: completed | refused | failed | invalid_schema
  created_at: timestamp
```

## AgentActionTrace

```yaml
AgentActionTrace:
  id: string
  run_id: string
  objective_id: string
  agent_id: string
  agent_role: planner | site_understanding | frontier | fetch_analysis | extractor | verifier | drift | memory | ops
  runtime_spec_id: string
  model_call_trace_refs: list
  context_bundle_trace_id: string
  tool_call_trace_refs: list
  command_result_refs: list
  policy_decision_refs: list
  input_refs: list
  output_refs: list
  reasoning_summary_ref: string
  assumptions: list
  alternatives_considered: list
  uncertainty_notes: list
  redaction_policy_ref: string
  retention_policy_ref: string
  replay_required: boolean
  created_at: timestamp
```

## ModelCallTrace

```yaml
ModelCallTrace:
  id: string
  run_id: string
  agent_action_trace_id: string
  provider_name: string
  model_id: string
  model_version: string
  prompt_template_ref: string
  prompt_template_version: string
  context_bundle_trace_id: string
  request_ref: string
  response_ref: string
  token_usage: object
  latency_ms: integer
  safety_filter_result_ref: string
  redaction_policy_ref: string
  raw_prompt_persisted: boolean
  raw_response_persisted: boolean
  replay_mode: exact_refs | summarized_refs | provider_unavailable
  created_at: timestamp
```

Rules:

- raw prompts and raw responses may be retained only if policy permits.
- if raw prompts are not retained, replay must preserve template version, sanitized context refs, model metadata, and output refs.
- provider-native traces are diagnostic only and must not replace this trace.

## ToolCallTrace

```yaml
ToolCallTrace:
  id: string
  run_id: string
  agent_action_trace_id: string
  tool_spec_id: string
  tool_name: string
  tool_version: string
  input_schema_ref: string
  output_schema_ref: string
  input_ref: string
  output_ref: string
  command_envelope_id: string
  command_result_id: string
  policy_decision_refs: list
  approval_decision_refs: list
  status: proposed | rejected | approved | executed | failed
  error: object
  created_at: timestamp
```

## ContextBundleTrace

```yaml
ContextBundleTrace:
  id: string
  run_id: string
  agent_id: string
  context_ref_schema: string
  included_context_refs: list
  excluded_context_refs: list
  taint_labels: list
  sanitized_context_ref: string
  redaction_policy_ref: string
  credential_exposure_check_ref: string
  memory_retrieval_trace_refs: list
  graph_snapshot_refs: list
  evidence_refs: list
  created_at: timestamp
```

## FrontierRecommendation

```yaml
FrontierRecommendation:
  id: string
  run_id: string
  agent_action_trace_id: string
  frontier_item_refs: list
  recommendation_type: prioritize | retire | retry | expand | pause | review
  priority_delta: number
  rationale_ref: string
  graph_signal_refs: list
  memory_retrieval_trace_refs: list
  policy_decision_refs: list
  applied_command_result_id: string
  status: proposed | applied | rejected | superseded
  created_at: timestamp
```

Scheduler-owned frontier transitions must reference the applied recommendation when a recommendation is used. Recommendations do not mutate frontier state by themselves.

## MultiAgentWorkflow

```yaml
MultiAgentWorkflow:
  id: string
  run_id: string
  objective_id: string
  workflow_type: planning | site_understanding | extraction | verification | drift_repair | operations_recovery
  coordinator_service: agents
  agent_role_sequence: list
  workflow_graph_ref: string
  loop_budget:
    max_agent_runs: integer
    max_tool_calls: integer
    max_runtime_seconds: integer
  termination_rules: list
  escalation_rules: list
  arbitration_policy_ref: string
  status: proposed | running | completed | escalated | failed | cancelled
  created_at: timestamp
  updated_at: timestamp
```

## AgentHandoff

```yaml
AgentHandoff:
  id: string
  workflow_id: string
  from_agent_action_trace_id: string
  to_agent_role: planner | site_understanding | frontier | fetch_analysis | extractor | verifier | drift | memory | ops
  handoff_reason: string
  context_bundle_trace_id: string
  required_output_schema_ref: string
  policy_decision_refs: list
  status: proposed | accepted | rejected | completed
  created_at: timestamp
```

## CoordinationDecision

```yaml
CoordinationDecision:
  id: string
  workflow_id: string
  decision_type: choose_plan | resolve_recommendation_conflict | terminate_loop | escalate_to_review | approve_repair_proposal
  candidate_refs: list
  selected_ref: string
  rejected_refs: list
  arbitration_policy_ref: string
  rationale_ref: string
  policy_decision_refs: list
  replay_required: boolean
  created_at: timestamp
```

Multi-agent workflows coordinate recommendations and handoffs. They do not bypass owner services, policy checks, or reviewer gates.

## DriftRepairSignal

```yaml
DriftRepairSignal:
  id: string
  run_ref: string
  workflow_ref: string
  affected_refs: list
  before_evidence_refs: list
  after_evidence_refs: list
  repair_proposal_refs: list
  rollback_ref: string
  policy_decision_refs: list
  status: observed | reviewed | repaired | ignored
  created_at: timestamp
```

## MultiAgentRepairReport

```yaml
MultiAgentRepairReport:
  id: string
  run_ref: string
  workflow_ref: string
  handoff_refs: list
  coordination_decision_refs: list
  repair_signal_refs: list
  agent_action_trace_refs: list
  policy_decision_refs: list
  command_record_refs: list
  event_cursor_refs: list
  outbox_refs: list
  failure_report_refs: list
  missing_ref_fields: list
  operator_status: string
  completion_result: pass | fail | needs_review
  created_at: timestamp
```

Rules:

- pass requires workflow, handoff, coordination, repair, agent trace, policy, command, event cursor, and outbox refs.
- agents cannot bypass owner-service commands for durable mutations.
- before/after evidence and rollback refs are required for repair loops.
- agent reasoning refs must not satisfy publication evidence requirements.

## MemoryRetrievalTrace

```yaml
MemoryRetrievalTrace:
  id: string
  run_id: string
  agent_id: string
  query_ref: string
  scope:
    project_id: string
    site_id: string
    objective_id: string
    schema_ref: string
    page_type: string
  retrieved_memory_refs: list
  excluded_memory_refs: list
  exclusion_reasons: list
  policy_decision_refs: list
  cross_scope_tunnel_ref: string
  taint_labels: list
  freshness_cutoff: timestamp
  retrieval_index_ref: string
  sanitized_context_ref: string
  completion_result: pass | fail | needs_review
  created_at: timestamp
```

Retrieval rules:

- retrieved memory requires sanitized context refs.
- invalidated, stale, tainted, or prompt-forbidden memory must be excluded unless policy explicitly allows sanitized summary use.
- excluded memory refs and reasons are replay-critical.

## CrossScopeMemoryTunnel

```yaml
CrossScopeMemoryTunnel:
  id: string
  source_scope:
    tenant_id: string
    project_id: string
    site_id: string
  target_scope:
    tenant_id: string
    project_id: string
    site_id: string
  allowed_memory_types: list
  authorization_ref: string
  policy_decision_refs: list
  sanitized_only: boolean
  evidence_ref_required: boolean
  taint_exclusion_rules: list
  status: proposed | approved | revoked | expired
  created_at: timestamp
```

Cross-scope memory tunnels may transfer sanitized patterns, failure lessons, or extraction repair strategies. They must not transfer raw customer data, secrets, untrusted page instructions, or publication evidence across scopes.

Cross-scope tunnel rules:

- approved tunnels require authorization refs and policy refs.
- approved tunnels must be sanitized-only and evidence-anchored.
- source and target scopes must differ.
- taint exclusion rules must be recorded before retrieval.

## SourceAdapterSpec

```yaml
SourceAdapterSpec:
  id: string
  name: string
  version: string
  adapter_type: http | browser_snapshot | sitemap | rss | authorized_session | api_source | document_source | file_import | manual_seed | prior_snapshot
  supported_source_types: list
  metadata_schema_ref: string
  transformation_schema_ref: string
  default_rate_limits: object
  credential_requirements: list
  policy_refs: list
  idempotency_key_template: string
  freshness_semantics: object
  created_at: timestamp
```

Adapter type mapping:

| Target adapter | Contract type | Required companion contracts |
| --- | --- | --- |
| HTTP | `http` | FetchAttempt, FetchResult, PageSnapshot |
| Sitemap | `sitemap` | FetchAttempt, LinkProvenance |
| RSS/feed | `rss` | FetchAttempt, LinkProvenance, freshness semantics |
| Browser | `browser_snapshot` | BrowserInteractionStep, PageSnapshot, ArtifactLifecycleState |
| Authorized session | `authorized_session` | AuthorizedSessionSpec, CredentialUseAudit, PolicyDecision |
| API-like source | `api_source` | FetchAttempt, FetchResult, SourceAdapterSpec transformation schema |
| Document source | `document_source` | DocumentNormalizationArtifact, NormalizationManifest |
| File import | `file_import` | ArtifactLifecycleState, NormalizationManifest |
| Manual seed | `manual_seed` | CrawlObjective, CrawlPlan |
| Prior snapshot | `prior_snapshot` | PageSnapshot, RunPlanSnapshot |

## SourceAdapterResult

Target source adapters return a typed result union instead of pretending every source is an HTTP fetch.

```yaml
SourceAdapterResult:
  id: string
  run_id: string
  adapter_spec_id: string
  adapter_type: http | browser_snapshot | sitemap | rss | authorized_session | api_source | document_source | file_import | manual_seed | prior_snapshot
  result_type: fetch_result | browser_snapshot | discovered_links | session_state | api_payload | document_artifact | file_artifact | seed_plan | prior_snapshot_ref | blocked_source
  output_refs: list
  policy_decision_refs: list
  replay_event_refs: list
  idempotency_key: string
  status: pending | succeeded | blocked | failed | partial
  created_at: timestamp
```

Adapter result mapping:

| Adapter type | Natural result types |
| --- | --- |
| `http` | fetch_result, blocked_source |
| `sitemap` | discovered_links, blocked_source |
| `rss` | discovered_links, blocked_source |
| `browser_snapshot` | browser_snapshot, blocked_source |
| `authorized_session` | session_state, blocked_source |
| `api_source` | api_payload, blocked_source |
| `document_source` | document_artifact, blocked_source |
| `file_import` | file_artifact |
| `manual_seed` | seed_plan |
| `prior_snapshot` | prior_snapshot_ref |

## AuthorizedSessionSpec

```yaml
AuthorizedSessionSpec:
  id: string
  project_id: string
  site_id: string
  adapter_spec_id: string
  customer_authorization_ref: string
  credential_scope_ref: string
  allowed_actions: list
  disallowed_actions: list
  allowed_side_effect_classes: list
  action_policy_refs: list
  session_lifecycle: create_per_run | reuse_until_expiry | operator_managed
  expiry_policy: object
  prompt_exposure_policy: never_raw | redacted_metadata_only
  audit_required: boolean
  created_at: timestamp
```

## CredentialUseAudit

```yaml
CredentialUseAudit:
  id: string
  run_id: string
  session_spec_id: string
  credential_scope_ref: string
  policy_decision_id: string
  adapter_spec_id: string
  action_type: session_create | request_sign | form_fill | cookie_refresh | session_destroy
  credential_delivery_mode: scoped_header | scoped_cookie | request_signing | vault_brokered_form_fill | operator_entered | disallowed_raw_secret_form_fill
  credential_exposure_class: none | vault_internal | origin_visible_token | origin_visible_secret | agent_visible_secret
  target_url: string
  secret_material_exposed_to_agent: boolean
  credential_presented_to_authorized_origin: boolean
  secret_material_captured_in_page_artifact: boolean
  raw_secret_persisted: boolean
  redaction_check_ref: string
  actor: string
  created_at: timestamp
```

Credential exposure rules:

- `agent_visible_secret` is forbidden in target acceptance.
- `disallowed_raw_secret_form_fill` is always blocked.
- `vault_brokered_form_fill` requires explicit approval, origin allowlist, no raw secret persistence, and `secret_material_exposed_to_agent: false`.
- `origin_visible_token` or `origin_visible_secret` means the credential was presented to the authorized remote origin as part of normal authentication. It does not permit the secret to enter agent context, captured page artifacts, model requests, replay bundles, or logs.
- `credential_presented_to_authorized_origin: true` is allowed only for a customer-authorized origin and must reference a policy decision and audit record.
- `secret_material_captured_in_page_artifact: true` fails target acceptance.
- raw secrets must never be serialized into prompts, model requests, replay bundles, logs, or stored browser artifacts.

## BrowserInteractionStep

```yaml
BrowserInteractionStep:
  id: string
  run_id: string
  fetch_attempt_id: string
  step_number: integer
  action_type: navigate | wait_for_selector | click | type | select | submit | scroll | capture | block
  interaction_purpose: discovery | retrieval | authentication | evidence_capture | repair_probe
  side_effect_class: none | read_only_navigation | session_state_change | account_change | purchase_or_cart | message_send | destructive | unknown
  form_method: get | post | put | patch | delete | none
  form_target_url: string
  credential_scope_ref: string
  explicit_approval_refs: list
  selector_ref: string
  input_ref: string
  expected_safe_effect: string
  policy_decision_id: string
  artifact_refs: list
  status: planned | executed | blocked | failed
  blocked_reason: string
  error: object
  created_at: timestamp
```

Browser interaction rules:

- `side_effect_class` must be `none`, `read_only_navigation`, or explicitly approved `session_state_change` for automatic execution.
- `account_change`, `purchase_or_cart`, `message_send`, `destructive`, and `unknown` must be blocked unless a future user-approved policy explicitly permits a narrower audited mode.
- blocked interactions must emit a policy decision, browser step record, and failure or review event.

## DocumentNormalizationArtifact

```yaml
DocumentNormalizationArtifact:
  id: string
  run_id: string
  source_snapshot_id: string
  source_mime_type: string
  parser_version: string
  text_artifact_ref: string
  structure_artifact_ref: string
  page_map_ref: string
  anchor_map_ref: string
  metadata_ref: string
  unsupported_regions: list
  privacy_classification: public | internal | confidential | regulated
  created_at: timestamp
```

## PolicyDecision

```yaml
PolicyDecision:
  id: string
  run_id: string
  objective_id: string
  policy_snapshot_id: string
  decision_type: plan | source_adapter | tool_call | fetch | browser_interaction | authorized_session | credential_use | prompt_context | publication | export_dispatch | export_withdrawal | artifact_lifecycle | retention | memory_retrieval | cross_scope_memory_tunnel | graph_signal_use | recovery_action
  subject_ref: string
  decision: allow | deny | require_review
  reasons: list
  evaluated_rules: list
  input_refs: list
  created_at: timestamp
```

## RuntimeSecurityPolicy

```yaml
RuntimeSecurityPolicy:
  id: string
  project_id: string
  egress_allowlist: list
  private_network_denylist: list
  dns_rebinding_protection: boolean
  file_url_allowed: boolean
  max_response_bytes: integer
  max_download_bytes: integer
  browser_sandbox_profile_ref: string
  credential_injection_mode: none | scoped_header | scoped_cookie | request_signing | vault_brokered
  created_at: timestamp
```

## ResourceBudget

```yaml
ResourceBudget:
  id: string
  project_id: string
  site_id: string
  max_concurrent_fetches: integer
  max_browser_contexts: integer
  max_queue_items: integer
  max_tokens: integer
  max_storage_bytes: integer
  max_runtime_seconds: integer
  enforcement: hard_stop | pause_and_review
  created_at: timestamp
```

## ServiceOwnershipSpec

```yaml
ServiceOwnershipSpec:
  id: string
  aggregate_type: string
  writer_service: control | scheduler | fetch | browser | normalize | extract | evidence | verify | publish | projection | graph | memory | agents | review_replay | export | ops | artifact_lifecycle
  allowed_commands: list
  emitted_events: list
  read_models: list
  created_at: timestamp
```

Target ownership coverage:

| Aggregate or contract | Writer service | Mutation path | Consistency semantics |
| --- | --- | --- | --- |
| Project, Site, SafetyPolicySnapshot, RuntimeSecurityPolicy, ResourceBudget, SchemaSpec, SchemaSnapshot, PublicationPolicySpec | control | command -> policy/approval -> expected version write -> event | policy/schema snapshots are immutable after use |
| PolicyDecision, ApprovalDecision | control | gate evaluation or reviewer authority -> decision record -> event | decisions are append-only and referenced by commands |
| CommandEnvelope, CommandResult | target aggregate owner | proposed command -> owner service validation -> result -> emitted events | idempotency key and expected version prevent duplicate mutation |
| CrawlObjective, CrawlPlan, CrawlJob, CrawlRun, RunPlanSnapshot | control | command -> approval/policy -> state transition -> event | run plan snapshots freeze policy/schema/tool/model refs |
| ProjectionSpec | projection | projection config command -> versioned spec -> event | projection specs are versioned; rebuilds reference spec version |
| ProjectionWatermark, ProjectionRebuildJob, ProjectionMismatchReport | projection | projection/rebuild command -> deterministic input cursors -> watermark/report event | rebuild hash and cursor refs prove projection consistency |
| SchemaMigrationRun, EventMigrationRun | control | migration command -> upcaster/backfill plan -> validation event | migration has rollback plan and replay validation |
| BackfillJob | owning service | idempotent backfill command -> checkpointed work -> completion event | checkpoint ref and idempotency key permit safe retry |
| FrontierItem, QueueItem, ShardLease, RetryDeadLetterRecord | scheduler | queue/frontier command or lease -> fencing token -> event | lease token and transition version fence concurrent workers |
| FetchAttempt, FetchResult, PageSnapshot | fetch | adapter result -> artifact write -> metadata event | artifact hash and attempt ID preserve replay |
| SourceAdapterResult (`http`, `sitemap`, `rss`, `api_source`) | fetch | adapter command -> policy gate -> adapter result -> source_adapter_result_recorded event | fetch-like adapters may reference FetchAttempt/FetchResult but SourceAdapterResult remains the canonical adapter outcome |
| SourceAdapterResult (`browser_snapshot`) | browser | approved browser/source command -> sandbox execution -> adapter result -> source_adapter_result_recorded event | browser artifacts are replayable through PageSnapshot and BrowserInteractionStep refs |
| SourceAdapterResult (`authorized_session`, `manual_seed`, `prior_snapshot`) | control | authorized/session/seed/snapshot command -> policy/approval -> adapter result -> source_adapter_result_recorded event | control records scoped authorization, idempotency, and replay refs |
| SourceAdapterResult (`document_source`) | normalize | document source command -> parser/normalizer -> adapter result -> source_adapter_result_recorded event | result points to DocumentNormalizationArtifact and NormalizationManifest refs |
| SourceAdapterResult (`file_import`) | artifact_lifecycle | file import command -> artifact classification -> adapter result -> source_adapter_result_recorded event | imported file artifacts receive privacy/lifecycle classification before downstream normalization |
| AuthorizedSessionSpec | control | authorized session command -> customer authorization and policy/approval gate -> versioned session spec -> command/source adapter events | session specs are immutable after use; browser/fetch adapters reference them but do not write them |
| CredentialUseAudit | control | adapter credential request -> credential authority/vault decision -> append-only audit record -> credential_used event | credential audit is single-authority append-only; adapters receive ephemeral handles and audit refs only |
| BrowserInteractionStep | browser | approved browser step -> sandbox execution -> artifact/event | side-effect class and policy decision gate execution |
| NormalizedDocument, NormalizationManifest, DocumentNormalizationArtifact | normalize | processing task -> artifact write -> manifest event | manifest version links raw-to-normalized replay |
| PageTypeClassification, ExtractionStrategy, ExtractionCandidate | extract | processing/tool result -> schema validation -> event | candidates are not publishable state |
| EvidencePacket, EvidenceCoverageMap | evidence | candidate + anchors -> coverage validation -> event | required evidence coverage is machine-validated |
| VerificationRecommendation, VerificationDecision, ConflictRecord, AdjudicationDecision | verify | recommendation/review/policy -> decision/conflict event | accept decisions require policy and evidence refs |
| PublishedOutput, OutputManifest, OutputVerificationAggregate, VerifiedFact | publish | accepted verification -> immutable manifest -> publication event | output manifests are versioned and append-only |
| GraphBuildManifest, GraphNode, GraphEdge, GraphSignal, TemporalKGEntityIdentity, TemporalKGProjectionRecord | graph | graph build command -> canonical inputs -> graph event | graph is projection; signals never satisfy source evidence |
| MemoryEvent, MemoryRetrievalTrace, CrossScopeMemoryTunnel, OperationalTemporalMemoryRecord | memory | approved memory write/retrieval/tunnel command -> taint/policy validation -> event/index | memory is planning context and never publication evidence |
| ContextRef, ContextBundle, AgentRunRequest, AgentRunResult, ModelRequest, ModelResponse, AgentActionTrace, ModelCallTrace, ToolCallTrace, ContextBundleTrace, FrontierRecommendation, MultiAgentWorkflow, AgentHandoff, CoordinationDecision | agents | agent runtime request -> context/model/tool/workflow trace -> event | framework-native state is diagnostic only |
| ReviewItem, ReviewDecision | review_replay | review command -> reviewer decision -> event | reviewer authority and separation of duties are recorded |
| ExportTargetSpec, ExportJob, ExportAttempt, ExportDeliveryReceipt, ExportWithdrawalJob, ExportWithdrawalAttempt | export | export/outbox command -> idempotent dispatch -> receipt/withdrawal event | destination object mappings reconcile delivery and withdrawal |
| DRRestorePlan, DRRestoreRun, DRRestoreReport | ops | restore plan/run command -> phase execution -> validation report event | restore phases are ordered, replayable, and validated before pass result |
| FailureRecord, RecoveryAction, QualityReport, BackpressureSignal, AutoscalingDecision | ops | failure/signal/recovery command -> ops record -> event | recovery is replayable and never silently mutates source of truth |
| ArtifactLifecycleState | artifact_lifecycle | classify/redact/tombstone/delete/legal-hold command -> lifecycle event -> projection cleanup | deletion is blocked by legal hold; cleanup is evented |

Agents may initiate or recommend commands through tools, but agents are not writer services for durable aggregates.

## CommandEnvelope

```yaml
CommandEnvelope:
  id: string
  command_type: string
  target_aggregate_type: string
  target_aggregate_id: string
  expected_version: integer
  idempotency_key: string
  actor_ref: string
  precondition_refs: list
  policy_decision_refs: list
  approval_decision_refs: list
  payload_ref: string
  status: proposed | accepted | rejected | committed | failed
  created_at: timestamp
```

## CommandResult

```yaml
CommandResult:
  id: string
  command_id: string
  result: committed | rejected | failed | duplicate
  emitted_event_refs: list
  output_refs: list
  rejection_reasons: list
  error: object
  created_at: timestamp
```

## CommandTypeSpec

```yaml
CommandTypeSpec:
  id: string
  command_type: string
  owner_service: control | scheduler | fetch | browser | normalize | extract | evidence | verify | publish | projection | graph | memory | agents | review_replay | export | ops | artifact_lifecycle
  target_aggregate_type: string
  payload_schema_ref: string
  precondition_refs: list
  required_policy_decision_types: list
  approval_required: boolean
  required_approval_subject_types: list
  expected_version_required: boolean
  lease_required: boolean
  emitted_event_types: list
  failure_record_type: string
  created_at: timestamp
```

Target command taxonomy:

| Command family | Owner | Required gates | Emitted events |
| --- | --- | --- | --- |
| create/update project, site, policy, schema, objective, job, run | control | plan/source/policy approval where configured | objective_created, plan_proposed, plan_approved, policy_evaluated |
| approve/revoke plan, schema, policy, credential, export, lifecycle, recovery | control/review_replay | ApprovalDecision and policy decision | approval_decided, review_decided |
| enqueue/transition frontier or queue item | scheduler | source scope, budget, lease when applicable | queue_item_enqueued, frontier_transitioned |
| acquire/release lease, ack/nack/dead-letter queue item | scheduler | lease token and retry rules | shard_lease_acquired, shard_lease_released, queue_item_acked, queue_item_dead_lettered |
| execute source adapter or fetch | fetch/browser/control/normalize/artifact_lifecycle | source_adapter/fetch/browser/authorized_session policy by adapter type | source_adapter_result_recorded, fetch_attempted, snapshot_written |
| execute browser step | browser | browser_interaction, authorized_session, credential_use when applicable | browser_step_executed, credential_used |
| normalize document or artifact | normalize | artifact lifecycle/privacy policy | processing_transitioned |
| classify/extract/build evidence/verify/publish | extract/evidence/verify/publish | tool/publication/review gates as configured | candidate_created, evidence_built, verification_decided, output_published |
| create graph records or graph signal | graph | graph_signal_use when used by planning/review | graph_projected |
| rebuild generic projection | projection | recovery_action, retention, artifact lifecycle when applicable | projection_rebuilt, projection_mismatch_detected |
| write/retrieve/cross-scope memory | memory | memory_retrieval, cross_scope_memory_tunnel | memory_written, memory_retrieved |
| run agent workflow/handoff/coordination | agents | tool_call, prompt_context, memory/graph gates | agent_action_recorded, multi_agent_workflow_started, coordination_decision_recorded |
| dispatch export or withdrawal | export | export_dispatch/export_withdrawal approval | export_dispatched, export_delivered, export_withdrawal_attempted |
| classify/redact/tombstone/delete/hold artifact | artifact_lifecycle | artifact_lifecycle, retention, approval when configured | artifact_lifecycle_changed, delete_propagated |
| rebuild projection, run migration/backfill, recover failure, DR restore | projection/control/ops/owner service | recovery_action, retention, artifact lifecycle when applicable | projection_rebuilt, migration_started, backfill_started, recovery_action_started, dr_restore_reported |

Minimum target command registry:

Each row below must be materialized as a `CommandTypeSpec` before implementation. A mutating command that is not represented here, or in a later reviewed extension of this table, is invalid for target architecture acceptance.
When a row says `owning service`, the generated `CommandTypeSpec.owner_service` must resolve to the concrete writer service for the target aggregate; `owning service` is not a persisted enum value.

| Command type | Owner | Target aggregate | Payload schema | Preconditions and gates | Version / lease | Emits | Failure and recovery contract |
| --- | --- | --- | --- | --- | --- | --- | --- |
| create_objective | control | CrawlObjective | ObjectiveCommandPayload | project/site/policy snapshot exists | expected_version for update only | objective_created, command_committed | policy or validation rejection emits command_rejected |
| propose_plan | control | CrawlPlan | PlanProposalPayload | objective approved or explicitly draft-plannable; source adapter choices declared | expected_version | plan_proposed, command_committed | missing adapter/evidence requirements creates ReviewItem |
| approve_plan | control | CrawlPlan | ApprovalPayload | ApprovalDecision with authority; policy_evaluated allow | expected_version | approval_decided, plan_approved | rejection preserves proposed plan and reasons |
| start_run | control | CrawlRun | RunLifecyclePayload | approved plan, RunPlanSnapshot, budget, policy snapshot | expected_version | command_committed, processing_transitioned | failed precondition leaves run queued |
| pause_run | control | CrawlRun | RunLifecyclePayload | run is running; actor authorized | expected_version | command_committed, processing_transitioned | workers stop new leases; in-flight work reconciles |
| resume_run | control | CrawlRun | RunLifecyclePayload | run is paused; budget still valid | expected_version | command_committed, processing_transitioned | stale policy forces review before resume |
| cancel_run | control | CrawlRun | RunLifecyclePayload | run not terminal | expected_version | command_committed, processing_transitioned | cancellation emits recovery tasks for owned leases |
| complete_run | control | CrawlRun | RunLifecyclePayload | queues drained or terminal policy satisfied | expected_version | command_committed, processing_transitioned | incomplete artifacts create QualityReport |
| fail_run | control | CrawlRun | RunFailurePayload | terminal failure reason recorded | expected_version | command_committed, error_recorded | FailureRecord and RecoveryAction proposed |
| enqueue | scheduler | QueueItem | QueueCommandPayload | aggregate command exists; queue policy permits | idempotency_key | queue_item_enqueued | duplicate idempotency returns duplicate CommandResult |
| acquire_lease | scheduler | QueueItem, ShardLease | LeaseCommandPayload | item queued or expired; worker identity valid | lease_required after acquire | queue_item_leased, shard_lease_acquired | stale lease rejected by fencing token |
| heartbeat_lease | scheduler | ShardLease | LeaseHeartbeatPayload | active lease token | lease_required | command_committed | missed heartbeat allows expiry |
| release_lease | scheduler | ShardLease | LeaseCommandPayload | active lease token | lease_required | shard_lease_released | stale token rejected |
| revoke_lease | scheduler | ShardLease | LeaseRevokePayload | ops/control authority | expected_version | shard_lease_released | worker must reconcile side effects before retry |
| ack | scheduler | QueueItem | QueueAckPayload | active lease and command result committed | lease_required | queue_item_acked | missing command result rejected |
| nack | scheduler | QueueItem | QueueAckPayload | active lease; retry class present | lease_required | command_committed | retry schedule stored on QueueItem |
| dead_letter | scheduler | QueueItem, RetryDeadLetterRecord | DeadLetterPayload | retry policy exhausted or permanent failure | lease_required | queue_item_dead_lettered, error_recorded | RecoveryAction proposed when configured |
| schedule_frontier | scheduler | FrontierItem | FrontierTransitionPayload | source scope and budget allow | expected_version | frontier_transitioned | duplicate canonical frontier refs are rejected |
| lease_fetch | scheduler | FrontierItem | FrontierTransitionPayload | item scheduled; queue lease active | lease_required | frontier_transitioned | stale lease rejected |
| commit_fetch | scheduler | FrontierItem | FrontierTransitionPayload | SourceAdapterResult succeeded or partial | expected_version | frontier_transitioned | missing adapter result rejected |
| fail_fetch | scheduler | FrontierItem | FrontierFailurePayload | SourceAdapterResult failed or blocked | expected_version | frontier_transitioned, error_recorded | retry/dead-letter policy applied |
| retire_frontier | scheduler | FrontierItem | FrontierTransitionPayload | objective, duplicate, policy, or budget reason recorded | expected_version | frontier_transitioned | retired item cannot be leased |
| execute_http_fetch | fetch | SourceAdapterResult, FetchAttempt | SourceAdapterCommandPayload | source_adapter and fetch policy allow | lease_required | source_adapter_result_recorded, fetch_attempted, snapshot_written | blocked source emits blocked result, not bypass |
| read_sitemap | fetch | SourceAdapterResult | SourceAdapterCommandPayload | sitemap URL in scope; rate policy allow | lease_required | source_adapter_result_recorded, fetch_attempted | parser failure records partial/failed result |
| read_rss | fetch | SourceAdapterResult | SourceAdapterCommandPayload | feed URL in scope; freshness policy loaded | lease_required | source_adapter_result_recorded, fetch_attempted | malformed feed creates FailureRecord |
| read_api_source | fetch | SourceAdapterResult | SourceAdapterCommandPayload | API endpoint approved; auth scope if needed | lease_required | source_adapter_result_recorded, fetch_attempted | schema mismatch routes to review |
| capture_browser_snapshot | browser | SourceAdapterResult, BrowserInteractionStep | BrowserSnapshotCommandPayload | browser policy, budget, sandbox, side-effect class | lease_required | source_adapter_result_recorded, browser_step_executed, snapshot_written | unsafe interaction emits blocked result |
| execute_browser_step | browser | BrowserInteractionStep | BrowserStepCommandPayload | browser_interaction policy; approval for side effects | expected_version, lease_required | browser_step_executed, credential_used when applicable | destructive/unknown actions blocked and reviewed |
| open_authorized_session | control | AuthorizedSessionSpec, SourceAdapterResult, CredentialUseAudit | AuthorizedSessionCommandPayload | customer authorization, origin allowlist, credential_use policy | expected_version | source_adapter_result_recorded, credential_used | raw secret form fill is rejected |
| normalize_document_source | normalize | SourceAdapterResult, DocumentNormalizationArtifact | DocumentSourceCommandPayload | artifact privacy and parser policy allow | lease_required | source_adapter_result_recorded, processing_transitioned | unsupported regions recorded, not hidden |
| import_file | artifact_lifecycle | SourceAdapterResult, ArtifactLifecycleState | FileImportCommandPayload | file source authorized; retention/privacy classified | expected_version | source_adapter_result_recorded, artifact_lifecycle_changed | unsafe file rejected before normalization |
| apply_manual_seed | control | SourceAdapterResult, CrawlPlan | ManualSeedCommandPayload | seed scope approved | expected_version | source_adapter_result_recorded, plan_proposed | out-of-scope seed rejected |
| attach_prior_snapshot | control | SourceAdapterResult, RunPlanSnapshot | PriorSnapshotCommandPayload | snapshot artifact exists and lifecycle allows use | expected_version | source_adapter_result_recorded | tombstoned/deleted artifacts rejected |
| start_task | owning service | ProcessingTask | ProcessingTaskCommandPayload | queue lease or owner command; policy gates satisfied | expected_version, lease_required when queued | processing_transitioned | failed precondition nacks queue item |
| complete_task | owning service | ProcessingTask | ProcessingTaskResultPayload | output refs validate | expected_version, lease_required when queued | processing_transitioned | invalid output creates FailureRecord |
| fail_task | owning service | ProcessingTask | ProcessingTaskFailurePayload | failure type and retry class recorded | expected_version, lease_required when queued | processing_transitioned, error_recorded | retry or dead-letter policy applied |
| request_review | owning service | ReviewItem | ReviewRequestPayload | review subject and evidence refs present | expected_version | review_created | missing evidence rejected |
| propose_strategy | extract | ExtractionStrategy | ExtractionStrategyPayload | schema snapshot exists | expected_version | processing_transitioned | incompatible schema routes to review |
| approve_strategy | extract | ExtractionStrategy | ApprovalPayload | approval authority or policy allow | expected_version | approval_decided, processing_transitioned | rejected strategy cannot extract |
| create_candidate | extract | ExtractionCandidate | CandidatePayload | approved strategy and normalized input refs | expected_version | candidate_created | validator failures mark candidate rejected |
| build_evidence | evidence | EvidencePacket | EvidencePayload | candidate exists; anchors resolvable | expected_version | evidence_built | missing required anchors fail coverage |
| decide_verification | verify | VerificationDecision | VerificationDecisionPayload | evidence packet and publication policy loaded | expected_version | verification_decided | conflict creates ConflictRecord and review item |
| publish_output | publish | PublishedOutput | PublicationPayload | accepted verification and coverage aggregate pass | expected_version | output_published, result_materialized | unresolved conflicts reject publication |
| dispatch_export | export | ExportJob, ExportAttempt | ExportDispatchPayload | export target approved; output manifest immutable | expected_version | export_dispatched | idempotency preserves destination mapping |
| complete_export | export | ExportAttempt, ExportDeliveryReceipt | ExportReceiptPayload | destination receipt validates | expected_version | export_delivered | rejected destination marks attempt failed |
| fail_export | export | ExportAttempt | ExportFailurePayload | retry classification recorded | expected_version | error_recorded | transient retry or permanent failure decision |
| dispatch_withdrawal | export | ExportWithdrawalJob, ExportWithdrawalAttempt | ExportWithdrawalPayload | withdrawal policy allow; object mappings exist | expected_version | export_withdrawal_attempted | unsupported destination records unsupported status |
| complete_withdrawal | export | ExportWithdrawalAttempt | ExportWithdrawalReceiptPayload | propagation receipt validates | expected_version | export_withdrawal_completed | partial propagation creates ReviewItem |
| write_memory | memory | MemoryEvent, OperationalTemporalMemoryRecord | MemoryWritePayload | memory policy, taint, evidence refs validate | expected_version | memory_written | poisoned/tainted content blocked from prompt use |
| retrieve_memory | memory | MemoryRetrievalTrace | MemoryRetrievalPayload | retrieval policy and tunnel policy allow | none | memory_retrieved | excluded memories recorded with reasons |
| approve_cross_scope_memory_tunnel | memory | CrossScopeMemoryTunnel | CrossScopeTunnelPayload | cross_scope_memory_tunnel approval authority | expected_version | approval_decided, memory_retrieved | unauthorized tunnel rejected and audited |
| start_workflow | agents | MultiAgentWorkflow | AgentWorkflowPayload | loop budget, prompt/context policy, tool specs | expected_version | multi_agent_workflow_started | budget exhaustion escalates |
| complete_workflow | agents | MultiAgentWorkflow | AgentWorkflowResultPayload | all handoffs closed or escalated | expected_version | multi_agent_workflow_completed | missing trace refs fail replay |
| escalate_workflow | agents | MultiAgentWorkflow, ReviewItem | AgentWorkflowEscalationPayload | escalation rule matched | expected_version | multi_agent_workflow_escalated, review_created | review item receives trace refs |
| fail_workflow | agents | MultiAgentWorkflow | AgentWorkflowFailurePayload | failure reason recorded | expected_version | multi_agent_workflow_failed, error_recorded | recovery or review command proposed |
| propose_handoff | agents | AgentHandoff | AgentHandoffPayload | workflow running; context bundle trace exists | expected_version | agent_handoff_proposed | missing context rejected |
| accept_handoff | agents | AgentHandoff | AgentHandoffDecisionPayload | target role allowed | expected_version | agent_handoff_accepted | policy denial emits rejected handoff |
| reject_handoff | agents | AgentHandoff | AgentHandoffDecisionPayload | rejection reason recorded | expected_version | agent_handoff_rejected | coordinator chooses alternate path |
| complete_handoff | agents | AgentHandoff | AgentHandoffResultPayload | output schema satisfied | expected_version | agent_handoff_completed | invalid output escalates workflow |
| project_graph | graph | GraphBuildManifest | GraphProjectionPayload | input event/artifact cursors contiguous | expected_version | graph_projected | mismatch creates ProjectionMismatchReport |
| start_rebuild | projection | ProjectionRebuildJob | ProjectionRebuildPayload | projection spec and event cursors fixed | expected_version | projection_rebuilt | rebuild hash mismatch emits projection_mismatch_detected |
| complete_rebuild | projection | ProjectionRebuildJob, ProjectionWatermark | ProjectionRebuildResultPayload | actual hash matches expected or mismatch recorded | expected_version | projection_rebuilt | mismatch blocks watermark current status |
| fail_rebuild | projection | ProjectionRebuildJob | ProjectionRebuildFailurePayload | failure reason and checkpoint recorded | expected_version | projection_mismatch_detected, error_recorded | recovery action proposed |
| start_migration | control | SchemaMigrationRun or EventMigrationRun | MigrationCommandPayload | rollback plan and validation refs present | expected_version | migration_started | missing rollback plan rejected |
| complete_migration | control | SchemaMigrationRun or EventMigrationRun | MigrationResultPayload | validation pass and replay checks pass | expected_version | migration_completed | failed validation rolls back or pauses |
| rerun_backfill | owning service | BackfillJob | BackfillCommandPayload | checkpoint and idempotency key present | expected_version | backfill_started, backfill_completed | repeated work must be idempotent |
| complete_backfill | owning service | BackfillJob | BackfillResultPayload | output refs and checkpoint validate | expected_version | backfill_completed | incomplete validation keeps job running or failed |
| fail_backfill | owning service | BackfillJob | BackfillFailurePayload | failure reason and checkpoint recorded | expected_version | error_recorded | retry policy decides rerun or review |
| propose_recovery | ops | RecoveryAction | RecoveryActionPayload | FailureRecord exists | expected_version | recovery_action_started | unsafe recovery requires review |
| complete_recovery | ops or owner service | RecoveryAction | RecoveryResultPayload | recovery outputs validate | expected_version | recovery_action_completed | failed recovery opens ReviewItem |
| record_backpressure | ops | BackpressureSignal | BackpressureSignalPayload | threshold exceeded | none | backpressure_signal_recorded | autoscaling decision may be proposed |
| decide_autoscaling | ops | AutoscalingDecision | AutoscalingPayload | current budgets and queue metrics loaded | none | autoscaling_decided | budget cap rejection logged |
| create_dr_restore_plan | ops | DRRestorePlan | DRRestorePlanPayload | restore scope, restore point, and backup refs validate | expected_version | command_committed | invalid restore point rejected |
| start_dr_restore | ops | DRRestoreRun | DRRestoreRunPayload | approved restore plan and phase graph present | expected_version | command_committed | phase precondition failure blocks run |
| complete_dr_restore | ops | DRRestoreRun, DRRestoreReport | DRRestoreResultPayload | all validation gates pass or needs_review recorded | expected_version | dr_restore_reported | unresolved refs force fail or needs_review |
| fail_dr_restore | ops | DRRestoreRun, DRRestoreReport | DRRestoreFailurePayload | failed phase and validation refs recorded | expected_version | dr_restore_reported, error_recorded | recovery action or manual review created |
| record_dr_restore | ops | DRRestoreReport | DRRestorePayload | restore validation refs present | expected_version | dr_restore_reported | restore mismatch creates FailureRecord |

Additional transition commands required by `StateMachineSpec`:

| Command type | Owner | Target aggregate | Payload schema | Preconditions and gates | Version / lease | Emits | Failure and recovery contract |
| --- | --- | --- | --- | --- | --- | --- | --- |
| update_objective | control | CrawlObjective | ObjectiveCommandPayload | objective not archived; scope policy allow | expected_version | command_committed | invalid scope emits command_rejected |
| approve_objective | control | CrawlObjective | ApprovalPayload | objective scope and policy validated | expected_version | approval_decided, command_committed | rejected objective remains draft |
| archive_objective | control | CrawlObjective | ObjectiveLifecyclePayload | no active runs or cancellation plan exists | expected_version | command_committed | active work must be cancelled or paused first |
| create_job | control | CrawlJob | JobCommandPayload | objective and policy snapshot exist | expected_version for update only | command_committed | invalid schema/budget rejects job |
| activate_job | control | CrawlJob | JobCommandPayload | approved objective, schema, and budget | expected_version | command_committed | invalid policy snapshot rejects activation |
| pause_job | control | CrawlJob | JobCommandPayload | job active | expected_version | command_committed | scheduler stops new queue items |
| archive_job | control | CrawlJob | JobCommandPayload | no active run or cancellation plan exists | expected_version | command_committed | archived job cannot resume |
| reject_plan | control | CrawlPlan | ApprovalPayload | reviewer or policy rejection reason present | expected_version | approval_decided | rejected plan cannot run |
| supersede_plan | control | CrawlPlan | PlanProposalPayload | replacement plan ref present | expected_version | plan_proposed | old plan preserved for replay |
| retire_strategy | extract | ExtractionStrategy | ExtractionStrategyPayload | replacement or retirement reason recorded | expected_version | processing_transitioned | active candidates keep original strategy refs |
| reject_candidate | extract | ExtractionCandidate | CandidateDecisionPayload | validator, policy, or reviewer reason present | expected_version | processing_transitioned | rejected candidate cannot be published |
| mark_conflict | verify | ConflictRecord | ConflictPayload | counter-evidence or contradiction refs present | expected_version | review_created | conflict blocks publication until resolved |
| verify_evidence | verify | EvidencePacket | EvidenceDecisionPayload | coverage map and policy loaded | expected_version | verification_recommended | missing coverage routes to review |
| supersede_output | publish | PublishedOutput, VerifiedFact | PublicationPayload | replacement output accepted and linked | expected_version | output_published, output_withdrawn | old version remains immutable |
| withdraw_output | publish | PublishedOutput | WithdrawalPayload | withdrawal policy allow and reason recorded | expected_version | output_withdrawn | export withdrawal jobs are enqueued |
| expire_output | publish | PublishedOutput, VerifiedFact | ExpiryPayload | freshness or retention rule triggered | expected_version | output_withdrawn | expired output cannot satisfy current publication |
| fail_withdrawal | export | ExportWithdrawalAttempt | ExportWithdrawalFailurePayload | retry classification recorded | expected_version | export_withdrawal_failed, error_recorded | retry or review item created |
| decide_review | review_replay | ReviewItem, ReviewDecision | ReviewDecisionPayload | reviewer authority and evidence refs validate | expected_version | review_decided | invalid authority rejects decision |
| adjudicate_conflict | review_replay | ConflictRecord, AdjudicationDecision | AdjudicationPayload | conflict open; adjudicator authority valid | expected_version | conflict_adjudicated | unresolved blocking conflicts remain open |
| record_drift | ops | DriftEvent | DriftPayload | affected refs and evidence refs present | expected_version | drift_detected | critical drift pauses unsafe downstream work |
| mark_stale | projection | ProjectionWatermark | ProjectionStalePayload | lag, mismatch, schema, or operator reason recorded | expected_version | projection_mismatch_detected | stale projection cannot serve target reads |
| stale_memory | memory | MemoryEvent, OperationalTemporalMemoryRecord | MemoryLifecyclePayload | freshness policy expired | expected_version | memory_written | stale memory excluded from prompt use unless allowed |
| invalidate_memory | memory | MemoryEvent, OperationalTemporalMemoryRecord | MemoryLifecyclePayload | poisoning, policy, deletion, or correction reason | expected_version | memory_written | invalidated memory removed from retrieval index |
| supersede_memory | memory | MemoryEvent, OperationalTemporalMemoryRecord | MemoryLifecyclePayload | replacement memory refs present | expected_version | memory_written | superseded memory kept for audit only |
| project_fact | graph | TemporalKGProjectionRecord, TemporalKGEntityIdentity | TemporalProjectionPayload | verified fact or published output refs present | expected_version | graph_projected | provisional identities cannot enter temporal KG |
| supersede_projection | graph | TemporalKGProjectionRecord, TemporalKGEntityIdentity | TemporalProjectionPayload | replacement projection ref present | expected_version | graph_projected | prior projection remains bitemporal history |
| expire_projection | graph | TemporalKGProjectionRecord | TemporalProjectionPayload | valid_time or freshness expiry reason | expected_version | graph_projected | expired projection excluded from current reads |
| dispute_projection | graph | TemporalKGProjectionRecord, TemporalKGEntityIdentity | TemporalProjectionPayload | conflict record refs present | expected_version | graph_projected, review_created | disputed records cannot support publication |
| invalidate_projection | graph | TemporalKGProjectionRecord, TemporalKGEntityIdentity | TemporalProjectionPayload | invalidation evidence or adjudication decision | expected_version | graph_projected | invalidated projection triggers rebuild when needed |
| approve_recovery | review_replay | RecoveryAction | ApprovalPayload | recovery_action approval authority valid | expected_version | approval_decided | unsafe recovery remains proposed |
| start_recovery | ops or owner service | RecoveryAction | RecoveryActionPayload | approved or policy-allowed recovery | expected_version | recovery_action_started | failed precondition keeps action approved |
| fail_recovery | ops or owner service | RecoveryAction | RecoveryFailurePayload | failure reason and affected refs recorded | expected_version | error_recorded | new RecoveryAction or ReviewItem proposed |
| fail_migration | control | SchemaMigrationRun or EventMigrationRun | MigrationFailurePayload | failure reason and rollback status recorded | expected_version | error_recorded | rollback or pause is required |
| cancel_task | owning service | ProcessingTask | ProcessingTaskCancelPayload | task not terminal; owner or control authority | expected_version, lease_required when queued | processing_transitioned | in-flight worker must reconcile side effects |
| cancel_workflow | agents | MultiAgentWorkflow, AgentRunResult | AgentWorkflowCancelPayload | workflow not terminal; control authority or loop rule | expected_version | command_committed | open handoffs are rejected or closed with reason |
| revoke_cross_scope_memory_tunnel | memory | CrossScopeMemoryTunnel | CrossScopeTunnelLifecyclePayload | tunnel approved; revocation authority valid | expected_version | command_committed | future retrieval through tunnel is blocked |
| expire_cross_scope_memory_tunnel | memory | CrossScopeMemoryTunnel | CrossScopeTunnelLifecyclePayload | expiry policy or valid_to reached | expected_version | command_committed | expired tunnel is removed from retrieval eligibility |
| cancel_export | export | ExportJob | ExportCancelPayload | export job queued/running; authority valid | expected_version | command_committed | running attempt is reconciled before retry/withdrawal |
| cancel_withdrawal | export | ExportWithdrawalJob | ExportWithdrawalCancelPayload | withdrawal job queued/running; authority valid | expected_version | command_committed | partial propagation remains auditable |
| cancel_rebuild | projection | ProjectionRebuildJob | ProjectionRebuildCancelPayload | rebuild queued/running; authority valid | expected_version | command_committed | watermark cannot become current from cancelled job |
| cancel_backfill | owning service | BackfillJob | BackfillCancelPayload | backfill queued/running; authority valid | expected_version | command_committed | checkpoint preserved for rerun |
| classify_artifact | artifact_lifecycle | ArtifactLifecycleState | ArtifactLifecyclePayload | artifact exists; privacy policy loaded | expected_version | artifact_lifecycle_changed | classification failure blocks downstream use |
| redact_artifact | artifact_lifecycle | ArtifactLifecycleState | ArtifactLifecyclePayload | redaction policy and target refs present | expected_version | artifact_lifecycle_changed | redaction failure leaves prior artifact active with review |
| tombstone_artifact | artifact_lifecycle | ArtifactLifecycleState | ArtifactLifecyclePayload | retention policy allows tombstone | expected_version | artifact_lifecycle_changed | legal hold blocks tombstone when configured |
| delete_artifact | artifact_lifecycle | ArtifactLifecycleState | ArtifactLifecyclePayload | retention allows delete; legal hold is none | expected_version | artifact_lifecycle_changed, delete_propagated | delete blocked by hold emits review item |
| place_legal_hold | artifact_lifecycle | ArtifactLifecycleState | ArtifactHoldPayload | legal hold authority and reason present | expected_version | artifact_lifecycle_changed | hold prevents delete/tombstone commands |
| release_legal_hold | artifact_lifecycle | ArtifactLifecycleState | ArtifactHoldPayload | release authority and reason present | expected_version | artifact_lifecycle_changed | release does not delete by itself |
| propagate_projection_cleanup | projection | ProjectionWatermark, ProjectionRebuildJob | ProjectionCleanupPayload | artifact lifecycle/delete event cursor refs present | expected_version | projection_rebuilt, projection_mismatch_detected when applicable | cleanup gaps create ProjectionMismatchReport |

## Command Payload Schema Registry

Every `CommandTypeSpec.payload_schema_ref` must resolve to one schema in this registry. Generated tests must fail when a command references a missing payload schema, omits required base fields, omits required domain fields, or redacts a replay-critical ref.

```yaml
BaseCommandPayload:
  command_payload_id: string
  target_ref: string
  actor_ref: string
  idempotency_key: string
  expected_version: integer
  lease_token_ref: string
  policy_decision_refs: list
  approval_decision_refs: list
  input_refs: list
  output_refs: list
  reason: string
  redaction_policy_ref: string
  payload_hash: string
```

Command payload schema rows:

| Payload schema | Required domain fields beyond `BaseCommandPayload` | Optional fields | Redaction and validation rules |
| --- | --- | --- | --- |
| ObjectiveCommandPayload | project_id:string, site_refs:list, instruction_ref:string, target_schema_refs:list, constraint_refs:list | ambiguity_refs:list | instruction may be redacted by stable ref; site scope must validate |
| ObjectiveLifecyclePayload | objective_id:string, lifecycle_action:string, reason:string | replacement_objective_ref:string | archived objectives cannot be mutated |
| PlanProposalPayload | objective_id:string, plan_version:string, source_adapter_plan:list, evidence_requirements:list | alternatives_ref:string | adapter choices must map to `SourceAdapterSpec` |
| ApprovalPayload | subject_ref:string, subject_type:string, decision:string, authority_ref:string | valid_from:timestamp, valid_to:timestamp | authority and separation-of-duties checks required |
| JobCommandPayload | objective_id:string, schema_refs:list, budget_ref:string, schedule_ref:string | run_defaults_ref:string | job budget and schema refs must exist |
| RunLifecyclePayload | run_id:string, lifecycle_action:string, run_plan_snapshot_id:string | pause_resume_reason:string | terminal runs cannot resume |
| RunFailurePayload | run_id:string, failure_type:string, failure_record_ref:string | recovery_action_ref:string | failure must create replayable failure refs |
| QueueCommandPayload | queue_name:string, aggregate_type:string, aggregate_id:string, command_ref:string, shard_key:string | priority:number | idempotency key required |
| QueueAckPayload | queue_item_id:string, lease_token_ref:string, ack_action:string | command_result_ref:string | stale lease token rejected |
| DeadLetterPayload | queue_item_id:string, retry_class:string, failure_record_ref:string | recovery_action_refs:list | retry exhaustion required |
| LeaseCommandPayload | queue_name:string, shard_key:string, worker_id:string, lease_token_ref:string | lease_seconds:integer | lease token hash only is persisted |
| LeaseHeartbeatPayload | shard_lease_id:string, worker_id:string, lease_token_ref:string | heartbeat_at:timestamp | expired leases cannot heartbeat |
| LeaseRevokePayload | shard_lease_id:string, revoke_reason:string, authority_ref:string | replacement_worker_ref:string | revoked lease fences workers |
| FrontierTransitionPayload | frontier_item_ref:string, from_state:string, to_state:string, priority:number | recommendation_ref:string | transition version required |
| FrontierFailurePayload | frontier_item_ref:string, source_adapter_result_ref:string, retry_class:string | failure_record_ref:string | retry policy must classify failure |
| SourceAdapterCommandPayload | adapter_spec_id:string, adapter_type:string, source_ref:string, idempotency_key:string | credential_scope_ref:string | non-fetch adapters must emit native refs |
| BrowserSnapshotCommandPayload | adapter_spec_id:string, target_url:string, browser_budget_ref:string, sandbox_profile_ref:string | interaction_plan_ref:string | side-effect policy checked before execution |
| BrowserStepCommandPayload | browser_step_id:string, action_type:string, side_effect_class:string, selector_ref:string | input_ref:string | unsafe side effects require approval |
| AuthorizedSessionCommandPayload | session_spec_ref:string, credential_scope_ref:string, target_origin:string, delivery_mode:string | browser_context_ref:string | raw secrets are never serialized |
| DocumentSourceCommandPayload | source_artifact_ref:string, parser_version:string, mime_type:string | page_map_policy_ref:string | parser output must include anchor map refs |
| FileImportCommandPayload | file_ref:string, privacy_classification:string, retention_policy_ref:string | pii_scan_ref:string | unsafe files rejected before normalization |
| ManualSeedCommandPayload | seed_refs:list, objective_id:string, scope_policy_ref:string | seed_notes_ref:string | out-of-scope seeds rejected |
| PriorSnapshotCommandPayload | prior_snapshot_ref:string, run_plan_snapshot_ref:string, lifecycle_state_ref:string | freshness_policy_ref:string | deleted/tombstoned refs rejected |
| ProcessingTaskCommandPayload | processing_task_id:string, task_type:string, owner_service:string, input_refs:list | queue_item_ref:string | owner must match task type |
| ProcessingTaskResultPayload | processing_task_id:string, output_refs:list, validator_result_refs:list | quality_report_ref:string | output refs must validate |
| ProcessingTaskFailurePayload | processing_task_id:string, failure_type:string, retry_class:string | failure_record_ref:string | retry/dead-letter policy required |
| ProcessingTaskCancelPayload | processing_task_id:string, cancel_reason:string, authority_ref:string | queue_item_ref:string | cancellation must preserve lineage |
| ReviewRequestPayload | item_type:string, subject_ref:string, reason:string, evidence_input_refs:list | priority:string | missing evidence refs rejected |
| ReviewDecisionPayload | review_item_id:string, decision_type:string, authority_ref:string, reason_codes:list | appeal_allowed:boolean | reviewer authority validated |
| ExtractionStrategyPayload | schema_snapshot_id:string, strategy_ref:string, page_type_refs:list | retirement_reason:string | schema compatibility required |
| CandidatePayload | strategy_ref:string, normalized_document_ref:string, schema_snapshot_id:string, candidate_ref:string | validator_result_refs:list | candidate cannot publish directly |
| CandidateDecisionPayload | candidate_ref:string, decision:string, reason:string | conflict_record_ref:string | rejected candidates cannot publish |
| EvidencePayload | candidate_ref:string, source_evidence_refs:list, anchor_refs:list, coverage_map_ref:string | prior_output_refs:list | required anchors must resolve |
| EvidenceDecisionPayload | evidence_packet_ref:string, coverage_result:string, verifier_ref:string | review_item_ref:string | missing coverage routes to review |
| VerificationDecisionPayload | evidence_packet_ref:string, candidate_ref:string, decision:string, authority_ref:string | conflict_record_ref:string | accept requires policy and coverage |
| ConflictPayload | conflict_type:string, candidate_refs:list, evidence_packet_refs:list, severity:string | counter_evidence_refs:list | blocking conflict prevents publication |
| AdjudicationPayload | conflict_record_id:string, decision:string, authority_ref:string, evidence_input_refs:list | resulting_output_refs:list | adjudication preserves prior state |
| PublicationPayload | verification_decision_refs:list, output_manifest_ref:string, evidence_coverage_map_ref:string, schema_snapshot_id:string | supersedes_output_ref:string | immutable manifest required |
| WithdrawalPayload | published_output_ref:string, withdrawal_reason:string, policy_decision_ref:string | export_withdrawal_job_refs:list | withdrawn outputs cannot be current |
| ExpiryPayload | output_ref:string, expiry_reason:string, freshness_policy_ref:string | replacement_output_ref:string | expired facts cannot satisfy current support |
| ExportDispatchPayload | export_job_id:string, target_spec_id:string, output_refs:list, idempotency_key:string | destination_batch_ref:string | destination auth refs redacted |
| ExportReceiptPayload | export_attempt_id:string, delivery_receipt_ref:string, external_object_ids:list | reconciliation_ref:string | receipt must match output refs |
| ExportFailurePayload | export_attempt_id:string, retry_classification:string, error_ref:string | failure_record_ref:string | retry classification required |
| ExportCancelPayload | export_job_id:string, cancel_reason:string, authority_ref:string | in_flight_attempt_ref:string | partial delivery remains auditable |
| ExportWithdrawalPayload | withdrawal_job_id:string, output_version_refs:list, external_object_mappings:list | reason:string | object mappings required |
| ExportWithdrawalReceiptPayload | withdrawal_attempt_id:string, propagation_status:string, delivery_receipt_ref:string | unsupported_reason:string | completion cannot emit artifact delete event |
| ExportWithdrawalFailurePayload | withdrawal_attempt_id:string, retry_classification:string, error_ref:string | review_item_ref:string | failure emits export-owned event |
| ExportWithdrawalCancelPayload | withdrawal_job_id:string, cancel_reason:string, authority_ref:string | partial_mapping_refs:list | partial propagation preserved |
| MemoryWritePayload | memory_scope_ref:string, content_ref:string, taint_labels:list, evidence_refs:list | operational_temporal_record_ref:string | tainted memory prompt use checked |
| MemoryRetrievalPayload | query_ref:string, scope_ref:string, policy_decision_refs:list | tunnel_ref:string | excluded memory reasons recorded |
| MemoryLifecyclePayload | memory_ref:string, lifecycle_action:string, reason:string | replacement_memory_ref:string | invalidated memory removed from retrieval |
| CrossScopeTunnelPayload | source_scope_ref:string, target_scope_ref:string, allowed_memory_types:list, authorization_ref:string | expiry_ref:string | sanitized-only policy enforced |
| CrossScopeTunnelLifecyclePayload | tunnel_ref:string, lifecycle_action:string, reason:string | expiry_timestamp:timestamp | revoked/expired tunnels cannot retrieve |
| AgentWorkflowPayload | workflow_type:string, agent_role_sequence:list, loop_budget_ref:string, context_bundle_ref:string | arbitration_policy_ref:string | loop budget required |
| AgentWorkflowResultPayload | workflow_id:string, terminal_status:string, output_refs:list, trace_refs:list | review_item_ref:string | trace completeness required |
| AgentWorkflowEscalationPayload | workflow_id:string, escalation_rule_ref:string, review_item_ref:string | trace_refs:list | review receives trace refs |
| AgentWorkflowFailurePayload | workflow_id:string, failure_reason:string, failure_record_ref:string | recovery_action_ref:string | failure is replayable |
| AgentWorkflowCancelPayload | workflow_id:string, cancel_reason:string, authority_ref:string | open_handoff_refs:list | open handoffs closed with reason |
| AgentHandoffPayload | workflow_id:string, from_trace_ref:string, to_agent_role:string, context_bundle_trace_id:string | required_output_schema_ref:string | context policy checked |
| AgentHandoffDecisionPayload | handoff_id:string, decision:string, authority_ref:string | rejection_reason:string | target role must be allowed |
| AgentHandoffResultPayload | handoff_id:string, output_ref:string, output_schema_ref:string | validator_result_refs:list | output schema must validate |
| GraphProjectionPayload | input_event_cursor_refs:list, input_artifact_refs:list, projection_spec_id:string | graph_build_manifest_ref:string | cursors must be contiguous |
| TemporalProjectionPayload | verified_fact_refs:list, published_output_refs:list, entity_identity_refs:list | conflict_record_refs:list | provisional identities rejected |
| ProjectionRebuildPayload | projection_spec_id:string, input_event_cursor_refs:list, expected_rebuild_hash:string | input_artifact_refs:list | hash and cursors required |
| ProjectionRebuildResultPayload | projection_rebuild_job_id:string, actual_rebuild_hash:string, validation_result_refs:list | mismatch_report_ref:string | mismatch prevents current watermark |
| ProjectionRebuildFailurePayload | projection_rebuild_job_id:string, failure_record_ref:string, checkpoint_ref:string | retry_policy_ref:string | recovery action proposed |
| ProjectionRebuildCancelPayload | projection_rebuild_job_id:string, cancel_reason:string, authority_ref:string | checkpoint_ref:string | cancelled job cannot advance watermark |
| ProjectionStalePayload | projection_watermark_ref:string, stale_reason:string, event_cursor_refs:list | lag_seconds:integer | stale projection cannot serve target reads |
| ProjectionCleanupPayload | artifact_lifecycle_event_refs:list, delete_event_cursor_refs:list, affected_projection_refs:list | cleanup_policy_ref:string | projection owner mutates watermarks |
| DriftPayload | drift_type:string, affected_refs:list, evidence_refs:list, severity:string | proposed_repair_refs:list | critical drift pauses unsafe downstream work |
| ArtifactLifecyclePayload | artifact_ref:string, lifecycle_action:string, privacy_classification:string, retention_policy_ref:string | pii_scan_result_ref:string | legal hold and retention gates enforced |
| ArtifactHoldPayload | artifact_ref:string, hold_action:string, authority_ref:string, legal_hold_ref:string | release_reason:string | hold authority required and audited |
| MigrationCommandPayload | migration_ref:string, input_event_cursor_refs:list, rollback_plan_ref:string | backfill_job_refs:list | rollback plan required |
| MigrationResultPayload | migration_run_id:string, validator_result_refs:list, replay_validation_ref:string | rollback_status:string | failed validation blocks completion |
| MigrationFailurePayload | migration_run_id:string, failure_record_ref:string, rollback_status:string | review_item_ref:string | rollback or pause required |
| BackfillCommandPayload | backfill_job_id:string, checkpoint_ref:string, input_refs:list | batch_window_ref:string | idempotency required |
| BackfillResultPayload | backfill_job_id:string, checkpoint_ref:string, output_refs:list, validator_result_refs:list | next_checkpoint_ref:string | checkpoint must advance |
| BackfillFailurePayload | backfill_job_id:string, failure_record_ref:string, checkpoint_ref:string | retry_policy_ref:string | rerun must be idempotent |
| BackfillCancelPayload | backfill_job_id:string, cancel_reason:string, checkpoint_ref:string | authority_ref:string | checkpoint preserved |
| RecoveryActionPayload | failure_record_ref:string, action_type:string, affected_refs:list | approval_decision_refs:list | unsafe recovery requires review |
| RecoveryResultPayload | recovery_action_ref:string, output_refs:list, validation_result_refs:list | follow_up_refs:list | recovery cannot silently mutate |
| RecoveryFailurePayload | recovery_action_ref:string, failure_record_ref:string, affected_refs:list | review_item_ref:string | failed recovery opens review |
| BackpressureSignalPayload | signal_type:string, value:number, threshold:number, severity:string | queue_refs:list | thresholds explicit |
| AutoscalingPayload | worker_pool:string, from_capacity:integer, to_capacity:integer, reason_signal_refs:list | cooldown_seconds:integer | budget caps enforced |
| DRRestorePlanPayload | restore_scope_ref:string, restore_point_ref:string, backup_manifest_ref:string, ordered_phase_refs:list | approval_decision_refs:list | restore point must be reachable |
| DRRestoreRunPayload | dr_restore_plan_id:string, first_phase:string, validation_gate_refs:list | deterministic_clock_ref:string | phase graph required |
| DRRestoreResultPayload | dr_restore_run_id:string, phase_results:list, dr_restore_report_ref:string | unresolved_refs:list | pass requires all gates pass |
| DRRestoreFailurePayload | dr_restore_run_id:string, failed_phase:string, failure_record_ref:string | recovery_action_ref:string | failure state required |
| DRRestorePayload | dr_restore_run_id:string, dr_restore_report_ref:string, validation_result_refs:list | unresolved_refs:list | report must match run phase results |

## ApprovalDecision

```yaml
ApprovalDecision:
  id: string
  subject_ref: string
  subject_type: crawl_plan | schema | publication_policy | tool_call | credential_use | source_adapter | browser_interaction | authorized_session | publication | export_target | export_dispatch | export_withdrawal | artifact_lifecycle | retention | memory_retrieval | cross_scope_memory_tunnel | graph_signal_use | recovery_action | multi_agent_workflow
  approver_id: string
  authority_ref: string
  decision: approve | reject | revoke | require_changes
  approval_scope: object
  required_approver_refs: list
  separation_of_duties_checked: boolean
  valid_from: timestamp
  valid_to: timestamp
  resulting_allowed_commands: list
  reasons: list
  created_at: timestamp
```

Commands that require `ApprovalDecision` refs before execution:

- plan approval
- scoped credential use and authorized session changes
- browser interactions with any non-read-only side effect class
- publication policy changes and publication accept actions when human review is required
- export target creation, export dispatch to governed destinations, and export withdrawal
- artifact redaction, tombstone, delete, legal hold placement, legal hold release, and projection cleanup when policy requires review
- cross-scope memory tunnel use
- graph signal use in high-impact planning or review routing when policy requires review
- recovery actions that replay events, rebuild projections, withdraw outputs, or ignore failures

## ProjectionSpec

```yaml
ProjectionSpec:
  id: string
  projection_name: string
  target_store: postgres | search | vector | graph | object_store
  source_event_types: list
  source_of_truth: event_log | postgres | object_store
  replay_watermark_ref: string
  max_allowed_lag_seconds: integer
  rebuild_strategy: full | incremental | from_snapshot
  stale_invalidation_rules: list
  failure_recovery_policy: retry | pause | rebuild
  created_at: timestamp
```

## ProjectionWatermark

```yaml
ProjectionWatermark:
  id: string
  projection_spec_id: string
  projection_name: string
  event_cursor_refs: list
  source_event_timestamp: timestamp
  artifact_snapshot_refs: list
  rebuild_hash: string
  lag_seconds: integer
  status: current | stale | rebuilding | failed
  updated_at: timestamp
```

## ProjectionRebuildJob

```yaml
ProjectionRebuildJob:
  id: string
  run_ref: string
  projection_spec_ref: string
  input_manifest_refs: list
  expected_rebuild_hash: string
  actual_rebuild_hash: string
  watermark_ref: string
  status: planned | rebuilt | mismatch | failed
  policy_decision_refs: list
  created_at: timestamp
```

Rules:

- rebuilt status requires expected and actual rebuild hashes to match.
- mismatch status requires a `ProjectionMismatchReport`.
- rebuild jobs are derived from canonical event/artifact refs and do not own publication truth.

## ProjectionMismatchReport

```yaml
ProjectionMismatchReport:
  id: string
  run_ref: string
  projection_rebuild_job_ref: string
  expected_rebuild_hash: string
  actual_rebuild_hash: string
  mismatch_ref: string
  operator_status: string
  created_at: timestamp
```

Rules:

- expected and actual rebuild hashes must differ.
- mismatch reports block pass claims until the projection is rebuilt or explicitly reviewed by policy.
- mismatch reports are replay-critical.

## EventCursor

```yaml
EventCursor:
  id: string
  ordering_scope: run | project | site | objective | plan | job | source_adapter | frontier_item | processing_task | fetch_attempt | artifact | candidate | evidence_packet | verification_decision | output | export_job | review_item | conflict | recovery_action | memory_event | projection | graph_projection | artifact_lifecycle
  stream_ref: string
  aggregate_type: string
  aggregate_id: string
  from_sequence: integer
  to_sequence: integer
  event_version: string
  event_hash: string
  created_at: timestamp
```

## ProjectionRebuildJob

```yaml
ProjectionRebuildJob:
  id: string
  projection_spec_id: string
  reason: schema_change | event_migration | corruption | stale_lag | operator_request | disaster_recovery
  input_event_cursor_refs: list
  input_artifact_refs: list
  expected_rebuild_hash: string
  actual_rebuild_hash: string
  mismatch_report_ref: string
  status: queued | running | completed | failed | cancelled
  created_at: timestamp
  updated_at: timestamp
```

## SchemaMigrationRun

```yaml
SchemaMigrationRun:
  id: string
  schema_migration_id: string
  run_scope_ref: string
  backfill_job_refs: list
  validator_result_refs: list
  rollback_plan_ref: string
  status: planned | running | completed | failed | rolled_back
  created_at: timestamp
  updated_at: timestamp
```

## EventMigrationRun

```yaml
EventMigrationRun:
  id: string
  from_event_version: string
  to_event_version: string
  upcaster_ref: string
  input_event_cursor_refs: list
  replay_validation_ref: string
  rollback_plan_ref: string
  status: planned | running | completed | failed | rolled_back
  created_at: timestamp
  updated_at: timestamp
```

## BackfillJob

```yaml
BackfillJob:
  id: string
  job_type: projection_rebuild | schema_migration | event_migration | artifact_lifecycle | export_reconciliation
  owner_service: control | scheduler | fetch | browser | normalize | extract | evidence | verify | publish | projection | graph | memory | agents | review_replay | export | ops | artifact_lifecycle
  input_refs: list
  output_refs: list
  checkpoint_ref: string
  idempotency_key: string
  status: queued | running | completed | failed | cancelled
  created_at: timestamp
  updated_at: timestamp
```

## StateMachineSpec

```yaml
StateMachineSpec:
  id: string
  entity_type: CrawlObjective | CrawlPlan | CrawlJob | CrawlRun | SourceAdapterResult | FrontierItem | ProcessingTask | BrowserInteractionStep | AgentRunResult | ToolCallTrace | FrontierRecommendation | MultiAgentWorkflow | AgentHandoff | CrossScopeMemoryTunnel | ExtractionStrategy | ExtractionCandidate | EvidencePacket | VerificationDecision | PublishedOutput | VerifiedFact | ExportJob | ExportAttempt | ExportWithdrawalJob | ExportWithdrawalAttempt | ReviewItem | ConflictRecord | DriftEvent | RecoveryAction | ProjectionWatermark | ProjectionRebuildJob | BackfillJob | SchemaMigrationRun | EventMigrationRun | DRRestoreRun | TemporalKGEntityIdentity | TemporalKGProjectionRecord | MemoryEvent | OperationalTemporalMemoryRecord | QueueItem | ShardLease | ArtifactLifecycleState
  version: string
  states: list
  transitions:
    - from: string
      to: string
      owner: string
      required_policy_decisions: list
      idempotency_key_required: boolean
      lease_required: boolean
      terminal: boolean
  pause_resume_rules: object
  retry_rules: object
  dead_letter_rules: object
  created_at: timestamp
```

Minimum state machine invariants:

- every transition records owner, causation event, idempotency key, and transition version
- leased work requires heartbeat and fencing token before side effects
- retryable failures must set `next_retry_at`; terminal failures must set dead-letter reason
- pause/cancel transitions must stop new work while preserving resumable lineage
- state updates and emitted events must be committed atomically or reconciled through an outbox

Target state transition matrix:

`owning service` and `natural adapter owner` in this table are generation-time aliases. Implementation specs must resolve them to the concrete writer service declared in `ServiceOwnershipSpec`.

| Entity | Allowed transitions | Triggering command | Owner | Required gates | Required tests |
| --- | --- | --- | --- | --- | --- |
| CrawlObjective | draft -> approved/active/paused/archived; active -> paused/archived; paused -> active/archived | create_objective, update_objective, approve_objective, archive_objective | control | project/site policy, objective scope | objective lifecycle and archived immutability tests |
| CrawlPlan | proposed -> approved/rejected/superseded | propose_plan, approve_plan, reject_plan, supersede_plan | control | plan approval, adapter/evidence completeness | cannot run unapproved plan tests |
| CrawlJob | draft -> active/paused/archived; active -> paused/archived; paused -> active/archived | create_job, activate_job, pause_job, archive_job | control | policy snapshot, budget, schema refs | archived job cannot enqueue tests |
| CrawlRun | queued -> running -> completed/failed/cancelled/paused; paused -> running/cancelled | start_run, pause_run, resume_run, cancel_run, complete_run, fail_run | control | plan approval, policy snapshot, budget | illegal transition, resume, cancel tests |
| SourceAdapterResult | pending -> succeeded/blocked/failed/partial | execute_http_fetch, read_sitemap, read_rss, read_api_source, capture_browser_snapshot, open_authorized_session, normalize_document_source, import_file, apply_manual_seed, attach_prior_snapshot | natural adapter owner | source_adapter policy, adapter-specific approvals | blocked-source, adapter-result replay, natural-owner tests |
| FrontierItem | discovered -> eligible -> scheduled -> fetching -> fetched/failed/retired; failed -> eligible/retired | schedule_frontier, lease_fetch, commit_fetch, fail_fetch, retire_frontier | scheduler | source scope, budget, lease | duplicate lease, retry, retire tests |
| QueueItem | queued -> leased -> acked/nacked/dead_lettered | enqueue, acquire_lease, ack, nack, dead_letter | scheduler | lease token | lease expiry, duplicate ack tests |
| ShardLease | active -> released/expired/revoked | acquire_lease, heartbeat_lease, release_lease, revoke_lease | scheduler | worker identity | heartbeat and fencing tests |
| ProcessingTask | queued -> running -> completed/failed/cancelled/waiting_review | start_task, complete_task, fail_task, cancel_task, request_review | task owner | task policy, lease | retry, cancel, and review tests |
| BrowserInteractionStep | planned -> executed/blocked/failed | execute_browser_step | browser | browser_interaction, credential_use, approval for side effects | destructive action block tests |
| AgentRunResult | created as completed/failed/escalated/cancelled; immutable after create | complete_workflow, fail_workflow, escalate_workflow, cancel_workflow | agents | context, model, tool trace completeness | immutable terminal trace tests |
| ToolCallTrace | proposed -> rejected/approved/executed/failed | execute_browser_step, execute_http_fetch, start_task, publish_output, dispatch_export | agents plus target owner | tool_call policy and approval subject coverage | tool call replay and denied-tool tests |
| FrontierRecommendation | proposed -> applied/rejected/superseded | schedule_frontier, retire_frontier, request_review | agents/scheduler | source scope, graph/memory policy when referenced | recommendation cannot mutate frontier directly tests |
| MultiAgentWorkflow | proposed -> running -> completed/escalated/failed/cancelled | start_workflow, complete_workflow, escalate_workflow, fail_workflow, cancel_workflow | agents | tool/prompt/memory/graph policy | loop budget, arbitration, and cancellation tests |
| AgentHandoff | proposed -> accepted/rejected/completed | propose_handoff, accept_handoff, reject_handoff, complete_handoff | agents | context policy | handoff replay tests |
| CrossScopeMemoryTunnel | proposed -> approved/revoked/expired | approve_cross_scope_memory_tunnel, revoke_cross_scope_memory_tunnel, expire_cross_scope_memory_tunnel | memory | cross_scope_memory_tunnel policy and approval | unauthorized tunnel, revocation, and expiry tests |
| ExtractionStrategy | proposed -> approved -> retired/superseded | propose_strategy, approve_strategy, retire_strategy | extract | schema/review gates | schema migration tests |
| ExtractionCandidate | candidate -> evidence_built -> rejected/conflicted/superseded/published | create_candidate, build_evidence, reject_candidate, mark_conflict, publish_output | extract/evidence/publish | evidence/publication policy | no direct publish tests |
| EvidencePacket | built -> accepted_for_verification/rejected/superseded | build_evidence, verify_evidence | evidence/verify | coverage policy | missing coverage tests |
| VerificationDecision | review -> accept/reject/conflict | decide_verification | verify | publication policy, review when required | conflict and authority tests |
| PublishedOutput | published -> superseded/withdrawn/expired | publish_output, supersede_output, withdraw_output, expire_output | publish | accepted verification, export/withdraw policy | immutable manifest tests |
| VerifiedFact | current -> superseded/expired/disputed | publish_output, supersede_output, expire_output | publish | accepted verification and fact key uniqueness | fact uniqueness and bitemporal freshness tests |
| ExportJob | queued -> running -> completed/failed/cancelled | dispatch_export, complete_export, fail_export, cancel_export | export | export_dispatch approval | idempotent delivery and cancellation tests |
| ExportAttempt | running -> completed/failed | dispatch_export, complete_export, fail_export | export | idempotency key and target auth | delivery receipt and retry classification tests |
| ExportWithdrawalJob | queued -> running -> completed/failed/cancelled | dispatch_withdrawal, complete_withdrawal, fail_withdrawal, cancel_withdrawal | export | export_withdrawal approval | withdrawal propagation and cancellation tests |
| ExportWithdrawalAttempt | pending -> propagated/failed/destination_unsupported | dispatch_withdrawal, complete_withdrawal, fail_withdrawal | export | destination mapping and withdrawal policy | partial propagation and unsupported destination tests |
| ReviewItem | open -> accepted/rejected/needs_more_evidence/resolved; resolved -> open only through reopen review decision | request_review, decide_review | review_replay | reviewer authority and evidence refs | review authority and reopen tests |
| ConflictRecord | open -> adjudicated/superseded/disputed/ignored | decide_verification, adjudicate_conflict | verify/review_replay | conflict policy and adjudication authority | blocking conflict prevents publication tests |
| DriftEvent | observed -> reviewed/repaired/ignored | record_drift, propose_recovery, complete_recovery | ops/extract/graph | drift policy and affected refs | repair without silent corruption tests |
| ArtifactLifecycleState | active -> redacted/tombstoned/deleted; hold_status none <-> legal_hold | classify_artifact, redact_artifact, tombstone_artifact, delete_artifact, place_legal_hold, release_legal_hold | artifact_lifecycle | artifact_lifecycle, retention, approval | legal-hold/delete conflict tests |
| ProjectionWatermark | current -> stale/rebuilding/failed/current | mark_stale, start_rebuild, complete_rebuild, fail_rebuild, propagate_projection_cleanup | projection | recovery/projection policy | rebuild and cleanup hash tests |
| ProjectionRebuildJob | queued -> running -> completed/failed/cancelled | start_rebuild, complete_rebuild, fail_rebuild, cancel_rebuild, propagate_projection_cleanup | projection | fixed event cursors and expected hash | deterministic rebuild, cleanup, mismatch, and cancellation tests |
| BackfillJob | queued -> running -> completed/failed/cancelled | rerun_backfill, complete_backfill, fail_backfill, cancel_backfill | owning service | checkpoint and idempotency key | idempotent retry, cancellation, and checkpoint tests |
| SchemaMigrationRun | planned -> running -> completed/failed/rolled_back | start_migration, complete_migration, fail_migration | control | rollback plan and validator refs | schema rollback and replay tests |
| EventMigrationRun | planned -> running -> completed/failed/rolled_back | start_migration, complete_migration, fail_migration | control | upcaster, rollback plan, replay validation | event upcaster and downgrade tests |
| DRRestoreRun | planned -> running -> completed/failed/needs_review | create_dr_restore_plan, start_dr_restore, complete_dr_restore, fail_dr_restore | ops | restore plan approval, backup refs, validation gates | DR phase ordering, validation, and failure tests |
| MemoryEvent | active -> stale/invalidated/superseded | write_memory, stale_memory, invalidate_memory, supersede_memory | memory | memory policy | taint/invalidation tests |
| OperationalTemporalMemoryRecord | current -> superseded/stale/invalidated | write_memory, stale_memory, invalidate_memory, supersede_memory | memory | memory policy and prompt-use policy | operational temporal memory invalidation tests |
| TemporalKGEntityIdentity | current -> superseded/disputed/invalidated | project_graph, adjudicate_conflict | graph/review_replay | verified identity evidence and conflict policy | false-merge and false-split tests |
| TemporalKGProjectionRecord | current -> superseded/expired/disputed/invalidated | project_fact, supersede_projection, expire_projection, dispute_projection, invalidate_projection | graph | verified output and conflict policy | bitemporal tests |
| RecoveryAction | proposed -> approved -> running -> completed/failed | propose_recovery, approve_recovery, start_recovery, complete_recovery, fail_recovery | ops/owner service | recovery_action approval when required | failure injection tests |

## TransitionSpec Registry

`StateMachineSpec` compact rows are not enough for implementation. Each lifecycle command must expand into generated-test-ready `TransitionSpec` rows.

```yaml
TransitionSpec:
  id: string
  entity_type: string
  command_type: string
  from_state: string
  to_state: string
  owner_service: string
  emitted_event_types: list
  state_before_required: boolean
  state_after_required: boolean
  idempotency_key_required: boolean
  lease_required: boolean
  terminal: boolean
  negative_transition_tests:
    - from_state: string
      command_type: string
      expected_rejection: string
```

Target transition rows:

| Entity | Command | From | To | Events | Idempotency / lease | Terminal | Negative transition test |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CrawlRun | start_run | queued | running | command_committed, processing_transitioned | idempotency yes, lease no | no | start from running rejects |
| CrawlRun | pause_run | running | paused | command_committed, processing_transitioned | idempotency yes, lease no | no | pause terminal run rejects |
| CrawlRun | resume_run | paused | running | command_committed, processing_transitioned | idempotency yes, lease no | no | resume non-paused run rejects |
| CrawlRun | cancel_run | queued/running/paused | cancelled | command_committed, processing_transitioned | idempotency yes, lease no | yes | cancel completed run rejects |
| CrawlRun | complete_run | running | completed | command_committed, processing_transitioned | idempotency yes, lease no | yes | complete with open required queues rejects |
| CrawlRun | fail_run | running | failed | command_committed, error_recorded | idempotency yes, lease no | yes | fail without FailureRecord rejects |
| SourceAdapterResult | execute_http_fetch | pending | succeeded/blocked/failed/partial | source_adapter_result_recorded, fetch_attempted, snapshot_written when applicable | idempotency yes, lease yes | yes | missing policy decision rejects |
| SourceAdapterResult | read_sitemap | pending | succeeded/blocked/failed/partial | source_adapter_result_recorded, fetch_attempted | idempotency yes, lease yes | yes | out-of-scope sitemap rejects |
| SourceAdapterResult | read_rss | pending | succeeded/blocked/failed/partial | source_adapter_result_recorded, fetch_attempted | idempotency yes, lease yes | yes | malformed feed without failure record rejects |
| SourceAdapterResult | read_api_source | pending | succeeded/blocked/failed/partial | source_adapter_result_recorded, fetch_attempted | idempotency yes, lease yes | yes | unapproved endpoint rejects |
| SourceAdapterResult | capture_browser_snapshot | pending | succeeded/blocked/failed/partial | source_adapter_result_recorded, browser_step_executed, snapshot_written | idempotency yes, lease yes | yes | unsafe side effect rejects |
| SourceAdapterResult | open_authorized_session | pending | succeeded/blocked/failed/partial | source_adapter_result_recorded, credential_used | idempotency yes, lease no | yes | raw secret form fill rejects |
| SourceAdapterResult | normalize_document_source | pending | succeeded/blocked/failed/partial | source_adapter_result_recorded, processing_transitioned | idempotency yes, lease yes | yes | unsupported parser without partial result rejects |
| SourceAdapterResult | import_file | pending | succeeded/blocked/failed/partial | source_adapter_result_recorded, artifact_lifecycle_changed | idempotency yes, lease no | yes | unclassified file rejects |
| SourceAdapterResult | apply_manual_seed | pending | succeeded/blocked/failed | source_adapter_result_recorded, plan_proposed | idempotency yes, lease no | yes | out-of-scope seed rejects |
| SourceAdapterResult | attach_prior_snapshot | pending | succeeded/blocked/failed | source_adapter_result_recorded | idempotency yes, lease no | yes | deleted prior artifact rejects |
| QueueItem | enqueue | none | queued | queue_item_enqueued | idempotency yes, lease no | no | duplicate non-idempotent enqueue rejects |
| QueueItem | acquire_lease | queued | leased | queue_item_leased, shard_lease_acquired | idempotency yes, lease no | no | acquire already leased item rejects |
| QueueItem | ack | leased | acked | queue_item_acked | idempotency yes, lease yes | yes | ack without command result rejects |
| QueueItem | nack | leased | nacked | command_committed | idempotency yes, lease yes | no | nack without retry class rejects |
| QueueItem | dead_letter | leased/nacked | dead_lettered | queue_item_dead_lettered, error_recorded | idempotency yes, lease yes | yes | dead-letter before retry policy exhausted rejects |
| ShardLease | heartbeat_lease | active | active | command_committed | idempotency yes, lease yes | no | heartbeat expired lease rejects |
| ShardLease | release_lease | active | released | shard_lease_released | idempotency yes, lease yes | yes | release stale token rejects |
| ShardLease | revoke_lease | active | revoked | shard_lease_released | idempotency yes, lease no | yes | revoke without authority rejects |
| ProcessingTask | start_task | queued | running | processing_transitioned | idempotency yes, lease conditional | no | start without owner rejects |
| ProcessingTask | complete_task | running | completed | processing_transitioned | idempotency yes, lease conditional | yes | complete missing output refs rejects |
| ProcessingTask | fail_task | running | failed | processing_transitioned, error_recorded | idempotency yes, lease conditional | yes | fail without retry class rejects |
| ProcessingTask | cancel_task | queued/running | cancelled | processing_transitioned | idempotency yes, lease conditional | yes | cancel terminal task rejects |
| ProcessingTask | request_review | running | waiting_review | review_created, processing_transitioned | idempotency yes, lease conditional | no | review without subject refs rejects |
| MultiAgentWorkflow | start_workflow | proposed | running | multi_agent_workflow_started | idempotency yes, lease no | no | start without loop budget rejects |
| MultiAgentWorkflow | complete_workflow | running | completed | multi_agent_workflow_completed | idempotency yes, lease no | yes | complete with open handoff rejects |
| MultiAgentWorkflow | escalate_workflow | running | escalated | multi_agent_workflow_escalated, review_created | idempotency yes, lease no | yes | escalate without rule rejects |
| MultiAgentWorkflow | fail_workflow | running | failed | multi_agent_workflow_failed, error_recorded | idempotency yes, lease no | yes | fail without trace refs rejects |
| MultiAgentWorkflow | cancel_workflow | proposed/running | cancelled | command_committed | idempotency yes, lease no | yes | cancel completed workflow rejects |
| CrossScopeMemoryTunnel | approve_cross_scope_memory_tunnel | proposed | approved | approval_decided | idempotency yes, lease no | no | approve without authorization rejects |
| CrossScopeMemoryTunnel | revoke_cross_scope_memory_tunnel | approved | revoked | command_committed | idempotency yes, lease no | yes | retrieval after revoke rejects |
| CrossScopeMemoryTunnel | expire_cross_scope_memory_tunnel | approved | expired | command_committed | idempotency yes, lease no | yes | retrieval after expiry rejects |
| PublishedOutput | publish_output | none | published | output_published, result_materialized | idempotency yes, lease no | no | publish without accepted coverage rejects |
| PublishedOutput | supersede_output | published | superseded | output_published, output_withdrawn | idempotency yes, lease no | yes | supersede without replacement rejects |
| PublishedOutput | withdraw_output | published | withdrawn | output_withdrawn | idempotency yes, lease no | yes | withdraw without policy rejects |
| PublishedOutput | expire_output | published | expired | output_withdrawn | idempotency yes, lease no | yes | expired output used as current rejects |
| ExportJob | dispatch_export | queued | running | export_dispatched | idempotency yes, lease no | no | dispatch unapproved target rejects |
| ExportJob | complete_export | running | completed | export_delivered | idempotency yes, lease no | yes | complete without receipt rejects |
| ExportJob | fail_export | running | failed | error_recorded | idempotency yes, lease no | yes | fail without retry classification rejects |
| ExportJob | cancel_export | queued/running | cancelled | command_committed | idempotency yes, lease no | yes | cancel completed export rejects |
| ExportWithdrawalJob | dispatch_withdrawal | queued | running | export_withdrawal_attempted | idempotency yes, lease no | no | dispatch without mappings rejects |
| ExportWithdrawalJob | complete_withdrawal | running | completed | export_withdrawal_completed | idempotency yes, lease no | yes | completion cannot emit delete_propagated |
| ExportWithdrawalJob | fail_withdrawal | running | failed | export_withdrawal_failed, error_recorded | idempotency yes, lease no | yes | fail without retry classification rejects |
| ExportWithdrawalJob | cancel_withdrawal | queued/running | cancelled | command_committed | idempotency yes, lease no | yes | cancel completed withdrawal rejects |
| ArtifactLifecycleState | classify_artifact | none/active | active | artifact_lifecycle_changed | idempotency yes, lease no | no | classify without privacy policy rejects |
| ArtifactLifecycleState | redact_artifact | active | redacted | artifact_lifecycle_changed | idempotency yes, lease no | yes | redact without policy rejects |
| ArtifactLifecycleState | tombstone_artifact | active/redacted | tombstoned | artifact_lifecycle_changed | idempotency yes, lease no | yes | tombstone under legal hold rejects |
| ArtifactLifecycleState | delete_artifact | active/redacted/tombstoned | deleted | artifact_lifecycle_changed, delete_propagated | idempotency yes, lease no | yes | delete under legal hold rejects |
| ArtifactLifecycleState | place_legal_hold | any non-deleted | legal_hold | artifact_lifecycle_changed | idempotency yes, lease no | no | duplicate hold idempotent only |
| ArtifactLifecycleState | release_legal_hold | legal_hold | none | artifact_lifecycle_changed | idempotency yes, lease no | no | release without authority rejects |
| ProjectionWatermark | mark_stale | current | stale | projection_mismatch_detected | idempotency yes, lease no | no | stale without reason rejects |
| ProjectionRebuildJob | start_rebuild | queued | running | projection_rebuilt | idempotency yes, lease no | no | start without cursor refs rejects |
| ProjectionRebuildJob | complete_rebuild | running | completed | projection_rebuilt | idempotency yes, lease no | yes | hash mismatch blocks completion |
| ProjectionRebuildJob | fail_rebuild | running | failed | projection_mismatch_detected, error_recorded | idempotency yes, lease no | yes | fail without failure record rejects |
| ProjectionRebuildJob | cancel_rebuild | queued/running | cancelled | command_committed | idempotency yes, lease no | yes | cancel completed rebuild rejects |
| ProjectionRebuildJob | propagate_projection_cleanup | queued/running | completed/failed | projection_rebuilt, projection_mismatch_detected when applicable | idempotency yes, lease no | yes | artifact_lifecycle owner mutation rejects |
| BackfillJob | rerun_backfill | queued | running | backfill_started | idempotency yes, lease no | no | rerun without checkpoint rejects |
| BackfillJob | complete_backfill | running | completed | backfill_completed | idempotency yes, lease no | yes | complete invalid checkpoint rejects |
| BackfillJob | fail_backfill | running | failed | error_recorded | idempotency yes, lease no | yes | fail without checkpoint rejects |
| BackfillJob | cancel_backfill | queued/running | cancelled | command_committed | idempotency yes, lease no | yes | cancel completed backfill rejects |
| DRRestoreRun | start_dr_restore | planned | running | command_committed | idempotency yes, lease no | no | start without approved plan rejects |
| DRRestoreRun | complete_dr_restore | running | completed/needs_review | dr_restore_reported | idempotency yes, lease no | yes | pass with unresolved refs rejects |
| DRRestoreRun | fail_dr_restore | running | failed | dr_restore_reported, error_recorded | idempotency yes, lease no | yes | fail without failed phase rejects |
| MemoryEvent | stale_memory | active | stale | memory_written | idempotency yes, lease no | no | stale without freshness rule rejects |
| MemoryEvent | invalidate_memory | active/stale | invalidated | memory_written | idempotency yes, lease no | yes | invalidated memory retrieval rejects |
| MemoryEvent | supersede_memory | active/stale | superseded | memory_written | idempotency yes, lease no | yes | supersede without replacement rejects |
| RecoveryAction | propose_recovery | none | proposed | recovery_action_started | idempotency yes, lease no | no | propose without FailureRecord rejects |
| RecoveryAction | approve_recovery | proposed | approved | approval_decided | idempotency yes, lease no | no | approve without authority rejects |
| RecoveryAction | start_recovery | approved | running | recovery_action_started | idempotency yes, lease no | no | start unsafe unapproved recovery rejects |
| RecoveryAction | complete_recovery | running | completed | recovery_action_completed | idempotency yes, lease no | yes | complete without validation rejects |
| RecoveryAction | fail_recovery | running | failed | error_recorded | idempotency yes, lease no | yes | fail without FailureRecord rejects |
| CrawlObjective | create_objective | none | draft/approved | objective_created | idempotency yes, lease no | no | create without scope policy rejects |
| CrawlObjective | update_objective | draft/approved/active/paused | draft/approved/active/paused | command_committed | idempotency yes, lease no | no | update archived objective rejects |
| CrawlObjective | approve_objective | draft | approved | approval_decided, command_committed | idempotency yes, lease no | no | approve invalid scope rejects |
| CrawlObjective | archive_objective | draft/approved/active/paused | archived | command_committed | idempotency yes, lease no | yes | archive with active run rejects |
| CrawlPlan | propose_plan | none | proposed | plan_proposed | idempotency yes, lease no | no | propose without adapter plan rejects |
| CrawlPlan | approve_plan | proposed | approved | approval_decided, plan_approved | idempotency yes, lease no | no | approve without authority rejects |
| CrawlPlan | reject_plan | proposed | rejected | approval_decided | idempotency yes, lease no | yes | rejected plan cannot start run |
| CrawlPlan | supersede_plan | proposed/approved | superseded | plan_proposed | idempotency yes, lease no | yes | supersede without replacement rejects |
| CrawlJob | create_job | none | draft | command_committed | idempotency yes, lease no | no | create without schema refs rejects |
| CrawlJob | activate_job | draft/paused | active | command_committed | idempotency yes, lease no | no | activate without approved objective rejects |
| CrawlJob | pause_job | active | paused | command_committed | idempotency yes, lease no | no | pause archived job rejects |
| CrawlJob | archive_job | draft/active/paused | archived | command_committed | idempotency yes, lease no | yes | archive with active run rejects |
| FrontierItem | schedule_frontier | eligible | scheduled | frontier_transitioned | idempotency yes, lease no | no | schedule out-of-scope item rejects |
| FrontierItem | lease_fetch | scheduled | fetching | frontier_transitioned | idempotency yes, lease yes | no | lease retired item rejects |
| FrontierItem | commit_fetch | fetching | fetched | frontier_transitioned | idempotency yes, lease yes | yes | commit without adapter result rejects |
| FrontierItem | fail_fetch | fetching | failed | frontier_transitioned, error_recorded | idempotency yes, lease yes | no | fail without retry class rejects |
| FrontierItem | retire_frontier | discovered/eligible/scheduled/failed | retired | frontier_transitioned | idempotency yes, lease no | yes | retire without reason rejects |
| BrowserInteractionStep | execute_browser_step | planned | executed/blocked/failed | browser_step_executed, credential_used when applicable | idempotency yes, lease conditional | yes | destructive action without approval rejects |
| AgentRunResult | complete_workflow | none | completed | multi_agent_workflow_completed | idempotency yes, lease no | yes | result without trace refs rejects |
| AgentRunResult | fail_workflow | none | failed | multi_agent_workflow_failed, error_recorded | idempotency yes, lease no | yes | failed result without failure ref rejects |
| AgentRunResult | escalate_workflow | none | escalated | multi_agent_workflow_escalated, review_created | idempotency yes, lease no | yes | escalation without review item rejects |
| AgentRunResult | cancel_workflow | none | cancelled | command_committed | idempotency yes, lease no | yes | cancelled result without reason rejects |
| ToolCallTrace | execute_browser_step | approved | executed/failed | tool_called, browser_step_executed | idempotency yes, lease conditional | yes | tool call without policy refs rejects |
| ToolCallTrace | execute_http_fetch | approved | executed/failed | tool_called, source_adapter_result_recorded | idempotency yes, lease yes | yes | tool call without command result rejects |
| ToolCallTrace | start_task | approved | executed/failed | tool_called, processing_transitioned | idempotency yes, lease conditional | yes | tool call wrong owner rejects |
| ToolCallTrace | publish_output | approved | executed/failed | tool_called, output_published | idempotency yes, lease no | yes | publish tool without verification rejects |
| ToolCallTrace | dispatch_export | approved | executed/failed | tool_called, export_dispatched | idempotency yes, lease no | yes | export tool without target approval rejects |
| FrontierRecommendation | schedule_frontier | proposed | applied | frontier_recommended, frontier_transitioned | idempotency yes, lease no | yes | recommendation cannot mutate without scheduler command |
| FrontierRecommendation | retire_frontier | proposed | applied | frontier_recommended, frontier_transitioned | idempotency yes, lease no | yes | retire recommendation without reason rejects |
| FrontierRecommendation | request_review | proposed | rejected/superseded | frontier_recommended, review_created | idempotency yes, lease no | yes | recommendation review without input refs rejects |
| AgentHandoff | propose_handoff | none | proposed | agent_handoff_proposed | idempotency yes, lease no | no | propose without context trace rejects |
| AgentHandoff | accept_handoff | proposed | accepted | agent_handoff_accepted | idempotency yes, lease no | no | accept disallowed role rejects |
| AgentHandoff | reject_handoff | proposed | rejected | agent_handoff_rejected | idempotency yes, lease no | yes | reject without reason rejects |
| AgentHandoff | complete_handoff | accepted | completed | agent_handoff_completed | idempotency yes, lease no | yes | complete invalid output rejects |
| ExtractionStrategy | propose_strategy | none | proposed | processing_transitioned | idempotency yes, lease no | no | propose incompatible schema rejects |
| ExtractionStrategy | approve_strategy | proposed | approved | approval_decided, processing_transitioned | idempotency yes, lease no | no | approve without authority rejects |
| ExtractionStrategy | retire_strategy | approved/proposed | retired/superseded | processing_transitioned | idempotency yes, lease no | yes | retire without reason rejects |
| ExtractionCandidate | create_candidate | none | candidate | candidate_created | idempotency yes, lease no | no | create without strategy rejects |
| ExtractionCandidate | build_evidence | candidate | evidence_built | evidence_built | idempotency yes, lease no | no | build evidence without anchors rejects |
| ExtractionCandidate | reject_candidate | candidate/evidence_built | rejected | processing_transitioned | idempotency yes, lease no | yes | reject without reason rejects |
| ExtractionCandidate | mark_conflict | evidence_built | conflicted | review_created | idempotency yes, lease no | yes | conflict without counter refs rejects |
| ExtractionCandidate | publish_output | evidence_built | published | output_published | idempotency yes, lease no | yes | publish without accepted verification rejects |
| EvidencePacket | build_evidence | none | built | evidence_built | idempotency yes, lease no | no | build without source evidence rejects |
| EvidencePacket | verify_evidence | built | accepted_for_verification/rejected/superseded | verification_recommended | idempotency yes, lease no | yes | verification missing coverage rejects |
| VerificationDecision | decide_verification | review | accept/reject/conflict | verification_decided | idempotency yes, lease no | yes | accept without policy rejects |
| VerifiedFact | publish_output | none | current | output_published | idempotency yes, lease no | no | fact duplicate key rejects |
| VerifiedFact | supersede_output | current | superseded | output_published, output_withdrawn | idempotency yes, lease no | yes | supersede without replacement rejects |
| VerifiedFact | expire_output | current | expired | output_withdrawn | idempotency yes, lease no | yes | expired fact used as current rejects |
| ExportAttempt | dispatch_export | none | running | export_dispatched | idempotency yes, lease no | no | dispatch without job rejects |
| ExportAttempt | complete_export | running | completed | export_delivered | idempotency yes, lease no | yes | complete without receipt rejects |
| ExportAttempt | fail_export | running | failed | error_recorded | idempotency yes, lease no | yes | fail without retry classification rejects |
| ExportWithdrawalAttempt | dispatch_withdrawal | none | pending | export_withdrawal_attempted | idempotency yes, lease no | no | dispatch without mappings rejects |
| ExportWithdrawalAttempt | complete_withdrawal | pending | propagated/destination_unsupported | export_withdrawal_completed | idempotency yes, lease no | yes | propagated without receipt rejects |
| ExportWithdrawalAttempt | fail_withdrawal | pending | failed | export_withdrawal_failed, error_recorded | idempotency yes, lease no | yes | fail without retry classification rejects |
| ReviewItem | request_review | none | open | review_created | idempotency yes, lease no | no | review without subject rejects |
| ReviewItem | decide_review | open | accepted/rejected/needs_more_evidence/resolved | review_decided | idempotency yes, lease no | yes | decision without authority rejects |
| ConflictRecord | decide_verification | none | open | verification_decided, review_created | idempotency yes, lease no | no | conflict without evidence refs rejects |
| ConflictRecord | adjudicate_conflict | open | adjudicated/superseded/disputed/ignored | conflict_adjudicated | idempotency yes, lease no | yes | adjudicate without authority rejects |
| DriftEvent | record_drift | none | observed | drift_detected | idempotency yes, lease no | no | drift without affected refs rejects |
| DriftEvent | propose_recovery | observed/reviewed | reviewed | recovery_action_started | idempotency yes, lease no | no | repair without drift evidence rejects |
| DriftEvent | complete_recovery | reviewed | repaired/ignored | recovery_action_completed | idempotency yes, lease no | yes | complete repair without validation rejects |
| ProjectionWatermark | start_rebuild | stale/current | rebuilding | projection_rebuilt | idempotency yes, lease no | no | start without spec rejects |
| ProjectionWatermark | complete_rebuild | rebuilding | current | projection_rebuilt | idempotency yes, lease no | no | current with hash mismatch rejects |
| ProjectionWatermark | fail_rebuild | rebuilding | failed | projection_mismatch_detected, error_recorded | idempotency yes, lease no | yes | fail without mismatch/failure refs rejects |
| ProjectionWatermark | propagate_projection_cleanup | stale/rebuilding | current/failed | projection_rebuilt, projection_mismatch_detected when applicable | idempotency yes, lease no | no | cleanup from artifact_lifecycle rejects |
| SchemaMigrationRun | start_migration | planned | running | migration_started | idempotency yes, lease no | no | start without rollback plan rejects |
| SchemaMigrationRun | complete_migration | running | completed | migration_completed | idempotency yes, lease no | yes | complete with validator failure rejects |
| SchemaMigrationRun | fail_migration | running | failed/rolled_back | error_recorded | idempotency yes, lease no | yes | fail without rollback status rejects |
| EventMigrationRun | start_migration | planned | running | migration_started | idempotency yes, lease no | no | start without upcaster rejects |
| EventMigrationRun | complete_migration | running | completed | migration_completed | idempotency yes, lease no | yes | complete with replay validation failure rejects |
| EventMigrationRun | fail_migration | running | failed/rolled_back | error_recorded | idempotency yes, lease no | yes | fail without rollback status rejects |
| DRRestoreRun | create_dr_restore_plan | none | planned | command_committed | idempotency yes, lease no | no | plan without restore point rejects |
| MemoryEvent | write_memory | none | active | memory_written | idempotency yes, lease no | no | write tainted prompt-use memory rejects |
| OperationalTemporalMemoryRecord | write_memory | none | current | memory_written | idempotency yes, lease no | no | write without memory event rejects |
| OperationalTemporalMemoryRecord | stale_memory | current | stale | memory_written | idempotency yes, lease no | no | stale without freshness rule rejects |
| OperationalTemporalMemoryRecord | invalidate_memory | current/stale | invalidated | memory_written | idempotency yes, lease no | yes | invalidated record retrieval rejects |
| OperationalTemporalMemoryRecord | supersede_memory | current/stale | superseded | memory_written | idempotency yes, lease no | yes | supersede without replacement rejects |
| ShardLease | acquire_lease | none | active | shard_lease_acquired | idempotency yes, lease no | no | acquire without worker identity rejects |
| TemporalKGEntityIdentity | project_graph | none/current | current/superseded | graph_projected | idempotency yes, lease no | no | project provisional identity rejects |
| TemporalKGEntityIdentity | adjudicate_conflict | current/disputed | superseded/disputed/invalidated | conflict_adjudicated, graph_projected | idempotency yes, lease no | yes | invalidation without adjudication rejects |
| TemporalKGProjectionRecord | project_fact | none | current | graph_projected | idempotency yes, lease no | no | project unverified fact rejects |
| TemporalKGProjectionRecord | supersede_projection | current | superseded | graph_projected | idempotency yes, lease no | yes | supersede without replacement rejects |
| TemporalKGProjectionRecord | expire_projection | current | expired | graph_projected | idempotency yes, lease no | yes | expired projection used as current rejects |
| TemporalKGProjectionRecord | dispute_projection | current | disputed | graph_projected, review_created | idempotency yes, lease no | no | dispute without conflict refs rejects |
| TemporalKGProjectionRecord | invalidate_projection | current/disputed | invalidated | graph_projected | idempotency yes, lease no | yes | invalidate without evidence rejects |

## EventTypeSpec

```yaml
EventTypeSpec:
  id: string
  event_type: string
  version: string
  payload_schema_ref: string
  ordering_scope: run | project | site | objective | plan | job | source_adapter | frontier_item | processing_task | fetch_attempt | artifact | candidate | evidence_packet | verification_decision | output | export_job | review_item | conflict | recovery_action | memory_event | projection | graph_projection | artifact_lifecycle
  redaction_policy_ref: string
  retention_policy_ref: string
  replay_required: boolean
  created_at: timestamp
```

## CrawlObjective

```yaml
CrawlObjective:
  id: string
  project_id: string
  site_ids: list
  instruction: string
  target_outputs: list
  target_schemas: list
  constraints:
    allowed_sources: list
    disallowed_actions: list
    max_depth: integer
    freshness_requirement: object
    budget: object
    policy_snapshot_id: string
  status: draft | approved | active | paused | archived
  created_by: string
  created_at: timestamp
  updated_at: timestamp
```

## CrawlPlan

```yaml
CrawlPlan:
  id: string
  objective_id: string
  planner_agent_id: string
  plan_version: string
  lifecycle_stage: proposed | approved | superseded
  source_adapter_plan: list
  frontier_seed_plan: list
  expected_page_types: list
  extraction_strategy_refs: list
  evidence_requirements: list
  risk_notes: list
  approval_status: proposed | approved | rejected | superseded
  approved_by: string
  created_at: timestamp
```

## CrawlJob

```yaml
CrawlJob:
  id: string
  project_id: string
  objective_id: string
  name: string
  status: draft | active | paused | archived
  scope:
    allowed_sources: list
    seed_urls: list
    source_adapters: list
  schema_refs: list
  freshness_policy: object
  budget:
    max_pages: integer
    max_browser_minutes: number
    max_tokens: integer
    max_runtime_seconds: integer
  created_at: timestamp
  updated_at: timestamp
```

## CrawlRun

```yaml
CrawlRun:
  id: string
  job_id: string
  objective_id: string
  crawl_plan_id: string
  run_plan_snapshot_id: string
  status: queued | running | completed | failed | cancelled | paused
  started_at: timestamp
  ended_at: timestamp
  config_snapshot_id: string
  policy_snapshot_id: string
  metrics_summary: object
  output_report_id: string
```

## RunPlanSnapshot

```yaml
RunPlanSnapshot:
  id: string
  run_id: string
  objective_id: string
  crawl_plan_id: string
  config_snapshot_id: string
  policy_snapshot_id: string
  schema_snapshot_refs: list
  tool_snapshot_refs: list
  model_snapshot_refs: list
  memory_snapshot_refs: list
  graph_snapshot_refs: list
  created_at: timestamp
```

## FrontierItem

```yaml
FrontierItem:
  id: string
  run_id: string
  objective_id: string
  crawl_plan_id: string
  url: string
  canonical_url: string
  discovered_from: string
  source_adapter: string
  page_type_guess: string
  entity_candidates: list
  priority: number
  priority_reasons: list
  freshness_due_at: timestamp
  state: discovered | eligible | scheduled | fetching | fetched | failed | retired
  attempts: integer
  next_retry_at: timestamp
  lease_owner: string
  lease_expires_at: timestamp
  heartbeat_at: timestamp
  transition_version: integer
  dead_letter_reason: string
  policy_decision_refs: list
  content_hash: string
  memory_refs: list
  graph_refs: list
  agent_decision_refs: list
```

## FetchResult

```yaml
FetchResult:
  id: string
  frontier_item_id: string
  run_id: string
  requested_url: string
  final_url: string
  status_code: integer
  content_type: string
  response_headers_ref: string
  fetched_at: timestamp
  fetch_adapter: string
  fetch_duration_ms: integer
  policy_decision_refs: list
  error: object
  snapshot_id: string
```

## FetchAttempt

```yaml
FetchAttempt:
  id: string
  frontier_item_id: string
  run_id: string
  attempt_number: integer
  source_adapter_spec_id: string
  requested_url: string
  canonicalization_version: string
  request_metadata_ref: string
  policy_decision_refs: list
  credential_use_decision_refs: list
  worker_id: string
  lease_owner: string
  lease_expires_at: timestamp
  idempotency_key: string
  retry_classification: transient | permanent | policy_denied | unavailable
  cost_summary: object
  started_at: timestamp
  ended_at: timestamp
```

## ContentTrustMetadata

```yaml
ContentTrustMetadata:
  id: string
  artifact_ref: string
  source_url: string
  trust_level: trusted_config | customer_input | public_web | untrusted_web
  taint_labels: list
  sanitized_context_ref: string
  secret_exposure_checked: boolean
  prompt_injection_policy_ref: string
  created_at: timestamp
```

## ProcessingTask

```yaml
ProcessingTask:
  id: string
  run_id: string
  objective_id: string
  task_type: normalize | classify_page | extract | build_evidence | verify | publish | index_graph | write_memory
  input_refs: list
  output_refs: list
  state: queued | running | completed | failed | cancelled | waiting_review
  owner_service: normalize | extract | evidence | verify | publish | graph | memory | review_replay
  initiator_actor: user | agent | system | reviewer
  attempts: integer
  lease_owner: string
  lease_expires_at: timestamp
  heartbeat_at: timestamp
  transition_version: integer
  idempotency_key: string
  policy_decision_refs: list
  dead_letter_reason: string
  error: object
  created_at: timestamp
  updated_at: timestamp
```

Processing tasks may be initiated by agents, but agents must not own durable tasks or directly mutate durable stores. Publication tasks must be owned by `publish` after an accepted `VerificationDecision` or reviewer action.

## PageSnapshot

```yaml
PageSnapshot:
  id: string
  fetch_result_id: string
  run_id: string
  url: string
  canonical_url: string
  raw_artifact_ref: string
  text_artifact_ref: string
  dom_artifact_ref: string
  screenshot_ref: string
  content_hash: string
  captured_at: timestamp
  privacy_classification: string
  pii_scan_result_ref: string
  retention_policy_ref: string
  lifecycle_state_ref: string
  transformations: list
  metadata: object
```

## NormalizedDocument

```yaml
NormalizedDocument:
  id: string
  snapshot_id: string
  normalizer_version: string
  language: string
  title: string
  headings: list
  text_ref: string
  sections: list
  structured_blocks: list
  links: list
  entities: list
  page_type_hypotheses: list
  normalized_artifact_hash: string
  normalization_manifest_id: string
  created_at: timestamp
```

## NormalizationManifest

```yaml
NormalizationManifest:
  id: string
  snapshot_id: string
  normalizer_version: string
  input_artifact_refs: list
  output_artifact_refs: list
  normalized_artifact_hash: string
  raw_to_text_anchor_map_ref: string
  dom_to_text_anchor_map_ref: string
  section_id_strategy: string
  block_id_strategy: string
  transformation_steps: list
  created_at: timestamp
```

## LinkProvenance

```yaml
LinkProvenance:
  id: string
  normalized_document_id: string
  source_url: string
  target_url: string
  canonical_target_url: string
  anchor_text: string
  dom_path: string
  text_offset_range: object
  discovered_by: parser | model | heuristic
  created_at: timestamp
```

## ArtifactLifecycleState

```yaml
ArtifactLifecycleState:
  id: string
  artifact_ref: string
  privacy_classification: public | internal | confidential | regulated
  pii_scan_result_ref: string
  retention_policy_ref: string
  lifecycle_status: active | redacted | tombstoned | deleted
  hold_status: none | legal_hold
  legal_hold_refs: list
  delete_blocked_by_hold: boolean
  redaction_artifact_ref: string
  tombstone_ref: string
  delete_propagation_refs: list
  updated_at: timestamp
```

Artifact lifecycle commands:

- classify_artifact
- redact_artifact
- tombstone_artifact
- delete_artifact
- place_legal_hold
- release_legal_hold

Projection cleanup is not an artifact-lifecycle mutation. `artifact_lifecycle` emits lifecycle and delete events; `projection` owns `propagate_projection_cleanup` and any resulting `ProjectionWatermark`, `ProjectionRebuildJob`, or `ProjectionMismatchReport` mutations.

Artifact lifecycle events:

- artifact_lifecycle_changed
- delete_propagated

The `artifact_lifecycle` owner emits cleanup commands for search, vector, graph, memory, export, and analytics projections when redaction, tombstone, delete, or retention changes occur.

Artifact lifecycle invariants:

- legal hold is orthogonal to lifecycle status.
- an artifact can be redacted or tombstoned while under legal hold.
- deletion is blocked while `hold_status` is `legal_hold`.
- release of legal hold does not delete an artifact by itself; deletion still requires a separate policy decision and command.

## SiteModel

```yaml
SiteModel:
  id: string
  run_id: string
  site_id: string
  objective_id: string
  discovered_page_types: list
  template_clusters: list
  crawl_paths: list
  low_value_zones: list
  uncertainty_notes: list
  graph_refs: list
  agent_decision_refs: list
  created_at: timestamp
```

## GraphBuildManifest

```yaml
GraphBuildManifest:
  id: string
  run_id: string
  graph_type: url | hyperlink | redirect_canonical | page_structure | template | entity | source_evidence | task | temporal
  build_version: string
  input_refs: list
  algorithm_refs: list
  output_graph_ref: string
  projection_spec_id: string
  watermark_ref: string
  quality_report_ref: string
  created_at: timestamp
```

V1 graph profile:

- allowed graph types: `url`, `page_structure`
- allowed node types: `url`, `page`, `section`
- allowed edge types: `links_to`, `redirects_to`, `canonical_of`, `contains`
- forbidden in V1: `entity`, `task`, `temporal` graph types; `supports_output`, `conflicts_with`, `supersedes` graph edges; clustering and graph quality signals
- V1 graph may guide discovery, dedup, and review routing only

## GraphNode

```yaml
GraphNode:
  id: string
  graph_build_manifest_id: string
  node_type: url | page | section | entity | task | candidate | evidence | output | fact
  key: string
  observed_state: observed | inferred | ambiguous
  source_refs: list
  evidence_refs: list
  created_at: timestamp
```

## GraphEdge

```yaml
GraphEdge:
  id: string
  graph_build_manifest_id: string
  from_node_id: string
  to_node_id: string
  edge_type: links_to | redirects_to | canonical_of | contains | mentions | supports_output | conflicts_with | derived_from | supersedes
  observed_state: observed | inferred | ambiguous
  source_refs: list
  evidence_refs: list
  confidence: number
  created_at: timestamp
```

## GraphSignal

```yaml
GraphSignal:
  id: string
  graph_build_manifest_id: string
  run_id: string
  signal_type: hub_score | duplicate_cluster | bridge_score | freshness_debt | conflict_cluster | orphan_page | crawl_priority
  target_ref: string
  value: any
  confidence: number
  explanation: string
  input_refs: list
  created_at: timestamp
```

Graph signals can guide planning, prioritization, and review. They are never source evidence and cannot satisfy required evidence coverage. Only underlying source artifacts and source anchors referenced through `source_evidence_refs` can support publication.

## GraphDeltaReport

```yaml
GraphDeltaReport:
  id: string
  run_ref: string
  previous_manifest_ref: string
  current_manifest_ref: string
  added_node_refs: list
  removed_node_refs: list
  added_edge_refs: list
  removed_edge_refs: list
  changed_signal_refs: list
  rebuild_hash: string
  created_at: timestamp
```

Graph deltas are derived projection records. They can trigger drift or review workflows but cannot replace source evidence.

## GraphQualityReport

```yaml
GraphQualityReport:
  id: string
  run_ref: string
  graph_manifest_ref: string
  metric_refs: list
  score_refs: list
  warning_refs: list
  policy_decision_refs: list
  created_at: timestamp
```

Quality reports explain projection quality, coverage, staleness, and rebuild risk. They are replay inputs for operators and agents, not publication evidence.

## TemporalKGEntityIdentity

```yaml
TemporalKGEntityIdentity:
  id: string
  entity_key: string
  entity_type: person | organization | product | article | event | location | document | claim | other
  canonical_label: string
  alias_refs: list
  identity_evidence_refs: list
  confidence: number
  valid_from: timestamp
  valid_to: timestamp
  transaction_time: timestamp
  status: current | superseded | disputed | invalidated
  created_at: timestamp
```

Temporal KG identity rules:

- identities used by current temporal KG projection records must derive from verified facts, accepted published outputs, or canonical verification/publication events.
- provisional entity identities from entity graph clustering stay in the entity graph until verified and must not become authoritative temporal KG identities.
- false-merge and false-split handling must produce conflict, adjudication, supersession, or invalidation records.

## TemporalKGProjectionRecord

Temporal KG records are projections derived from verified outputs and append-only events. They are never source evidence for publication.

```yaml
TemporalKGProjectionRecord:
  id: string
  projection_version: string
  entity_identity_id: string
  subject_entity_key: string
  predicate: string
  object_value: any
  object_entity_key: string
  value_type: string
  valid_time:
    valid_from: timestamp
    valid_to: timestamp
  transaction_time:
    observed_at: timestamp
    projected_at: timestamp
    superseded_at: timestamp
  source_verified_fact_refs: list
  source_published_output_refs: list
  source_event_refs: list
  evidence_packet_refs: list
  conflict_record_refs: list
  supersedes_projection_record_id: string
  status: current | superseded | expired | disputed | invalidated
  projection_watermark_ref: string
  created_at: timestamp
```

Rules:

- temporal KG records derive only from verified facts, published outputs, and canonical events.
- valid time describes the fact's real-world interval; transaction time describes when VeraCrawl observed, projected, superseded, or invalidated it.
- temporal KG reads may inform planning, review, contradiction detection, and repair.
- temporal KG reads must not satisfy publication evidence requirements.
- rebuilds must reproduce records from canonical inputs or emit a projection mismatch report.

## TemporalGraphProjectionRecord

`TemporalGraphProjectionRecord` is the executable foundation contract used by the
advanced graph projection slice. It is a narrower implementation-ready subset of
the conceptual `TemporalKGProjectionRecord` above.

```yaml
TemporalGraphProjectionRecord:
  id: string
  run_ref: string
  source_output_refs: list
  valid_from_ref: string
  valid_to_ref: string
  entity_identity_ref: string
  evidence_packet_refs: list
  projection_watermark_ref: string
  created_at: timestamp
```

Rules:

- source output refs and evidence packet refs are required.
- valid-time, identity, and projection watermark refs are required.
- temporal graph projection records can inform planning, review, contradiction detection, and repair.
- temporal graph projection records must not satisfy publication evidence requirements.

## AdvancedGraphProjectionReport

```yaml
AdvancedGraphProjectionReport:
  id: string
  run_ref: string
  projection_spec_ref: string
  rebuild_job_ref: string
  delta_report_ref: string
  quality_report_ref: string
  signal_refs: list
  temporal_record_refs: list
  mismatch_report_ref: string
  watermark_ref: string
  policy_decision_refs: list
  command_record_refs: list
  event_cursor_refs: list
  outbox_refs: list
  failure_report_refs: list
  missing_ref_fields: list
  operator_status: string
  completion_result: pass | fail | needs_review
  created_at: timestamp
```

Rules:

- pass requires projection, rebuild, delta, quality, signal, temporal, watermark, policy, command, event, and outbox refs.
- non-pass requires failure refs, missing refs, or a mismatch report ref.
- graph signals referenced by the report remain planning/review signals only.

## OperationalTemporalMemoryRecord

Operational temporal records describe crawler operations, selectors, page types, failures, repairs, and site behavior. They are separate from publication temporal KG records.

```yaml
OperationalTemporalMemoryRecord:
  id: string
  run_id: string
  project_id: string
  site_id: string
  record_type: selector_behavior | page_type_behavior | adapter_behavior | failure_pattern | repair_strategy | site_structure
  subject_ref: string
  observation_ref: string
  evidence_refs: list
  memory_event_refs: list
  valid_time:
    valid_from: timestamp
    valid_to: timestamp
  transaction_time:
    observed_at: timestamp
    recorded_at: timestamp
    invalidated_at: timestamp
  taint_labels: list
  trust_level: trusted | untrusted | mixed | derived
  allowed_prompt_use: forbidden | sanitized_summary | scoped_context_ref
  status: current | superseded | stale | invalidated
  created_at: timestamp
```

Rules:

- operational temporal records may guide planning, repair, and site understanding.
- operational temporal records cannot create publication temporal KG state.
- operational temporal records cannot support publication evidence or authoritative entity identity.
- promotion into publication outputs requires current or selected historical source evidence, verification, and publication policy.

## PageTypeClassification

```yaml
PageTypeClassification:
  id: string
  run_id: string
  site_model_id: string
  normalized_document_id: string
  page_type: string
  confidence: number
  classifier: rule | heuristic | model | hybrid
  classifier_version: string
  evidence_anchors: list
  created_at: timestamp
```

## ExtractionStrategy

```yaml
ExtractionStrategy:
  id: string
  objective_id: string
  schema_ref: string
  page_type: string
  strategy_type: rule | heuristic | model | hybrid
  instructions_ref: string
  selector_refs: list
  model_refs: list
  evidence_requirements: list
  agent_decision_refs: list
  status: proposed | approved | retired | superseded
  created_at: timestamp
```

## ExtractionCandidate

```yaml
ExtractionCandidate:
  id: string
  run_id: string
  objective_id: string
  snapshot_id: string
  normalized_document_id: string
  schema_ref: string
  schema_snapshot_id: string
  field_id: string
  field_path: string
  value: any
  value_type: string
  extraction_method: rule | heuristic | model | hybrid
  extractor_version: string
  extraction_strategy_id: string
  agent_decision_id: string
  confidence: number
  evidence_anchor_candidates: list
  status: candidate | evidence_built | rejected | conflicted | superseded | published
```

## EvidencePacket

```yaml
EvidencePacket:
  id: string
  candidate_id: string
  run_id: string
  source_url: string
  snapshot_id: string
  normalized_document_id: string
  objective_id: string
  anchors:
    text_offsets: list
    dom_paths: list
    json_paths: list
    table_cells: list
    screenshot_regions: list
    anchor_coordinate_system: string
    normalization_manifest_id: string
  source_evidence_refs: list
  prior_verified_output_refs: list
  graph_signal_refs: list
  memory_refs: list
  counter_source_evidence_refs: list
  agent_reasoning_refs: list
  freshness:
    captured_at: timestamp
    ttl_seconds: integer
    stale: boolean
  built_at: timestamp
```

Only `source_evidence_refs` and accepted `prior_verified_output_refs` can support publication. `graph_signal_refs`, `memory_refs`, and `agent_reasoning_refs` may explain why the crawler looked somewhere or recommended a decision, but they are not source evidence.

Prior verified outputs may support publication only when their transitive source evidence is available, their temporal validity and freshness satisfy the current publication policy, and the evidence packet declares whether the prior output is being used as historical context or current support.

## VerificationRecommendation

```yaml
VerificationRecommendation:
  id: string
  evidence_packet_id: string
  candidate_id: string
  run_id: string
  objective_id: string
  recommending_agent_id: string
  recommended_decision: accept | reject | review | conflict
  reasons: list
  confidence: number
  model_refs: list
  input_refs: list
  created_at: timestamp
```

## VerificationDecision

```yaml
VerificationDecision:
  id: string
  evidence_packet_id: string
  candidate_id: string
  run_id: string
  objective_id: string
  crawl_plan_id: string
  decision: accept | reject | review | conflict
  verifier: string
  verifier_version: string
  verification_method: rule | model_assisted | human | hybrid
  decision_authority: policy_engine | human_reviewer | verification_service
  agent_recommendation_refs: list
  policy_refs: list
  reasons: list
  confidence: number
  compared_output_ids: list
  created_at: timestamp
```

An AI agent may create `VerificationRecommendation`. A durable `VerificationDecision`, especially `accept`, must come from a policy engine, human reviewer, or verification service that enforces the configured publication policy.

## PublishedOutput

```yaml
PublishedOutput:
  id: string
  run_id: string
  objective_id: string
  schema_ref: string
  schema_snapshot_ref: string
  output_type: record | document_metadata | document | table | file | dataset | fact
  output_ref: string
  output_manifest_ref: string
  output_version: string
  evidence_coverage_map_ref: string
  source_snapshot_refs: list
  evidence_packet_refs: list
  verification_decision_refs: list
  publication_decision_refs: list
  export_target_refs: list
  supersedes_output_id: string
  withdraws_output_id: string
  status: current | superseded | expired | disputed | withdrawn
  created_at: timestamp
```

`evidence_coverage_map_ref` must describe evidence coverage at the correct granularity for the output type: field-level for records, row/cell-level for tables, chunk/section-level for documents, file-level for binary artifacts, and item-level for datasets.

Publication invariant:

- at least one `VerificationDecision.decision = accept`
- publication `PolicyDecision.decision = allow`
- required `PublicationPolicySpec` evidence coverage is satisfied
- no unresolved blocking `ConflictRecord`
- every required coverage entry is backed by an accepted verification decision or an accepted prior verified output allowed by policy
- output manifest and evidence coverage map validate against their schemas

## OutputManifest

```yaml
OutputManifest:
  id: string
  published_output_id: string
  schema_snapshot_id: string
  output_type: record | document_metadata | document | table | file | dataset | fact
  item_refs: list
  field_ids: list
  row_ids: list
  cell_ids: list
  content_hash: string
  created_at: timestamp
```

## EvidenceCoverageMap

```yaml
EvidenceCoverageMap:
  id: string
  published_output_id: string
  schema_snapshot_id: string
  coverage_entries:
    - target_id: string
      target_type: field | row | cell | section | file | item
      required: boolean
      status: covered | missing | not_applicable | covered_by_prior_output
      evidence_packet_refs: list
      source_evidence_refs: list
      prior_verified_output_refs: list
      accepted_verification_decision_refs: list
      accepted_prior_output_support_refs: list
      validator_result_refs: list
  created_at: timestamp
```

## OutputVerificationAggregate

```yaml
OutputVerificationAggregate:
  id: string
  published_output_id: string
  evidence_coverage_map_id: string
  required_entry_count: integer
  accepted_entry_count: integer
  missing_required_entry_count: integer
  conflict_count: integer
  verification_decision_refs: list
  prior_output_support_refs: list
  entry_validation_results: list
  result: pass | fail | needs_review
  created_at: timestamp
```

`OutputVerificationAggregate` must validate every required `coverage_entries` item. A required entry is accepted only when it has either accepted verification decision refs tied to its evidence packets or publication-policy-allowed prior output support refs. Output-level decisions cannot satisfy unrelated coverage entries.

## VerifiedFact

```yaml
VerifiedFact:
  id: string
  published_output_id: string
  run_id: string
  objective_id: string
  schema_ref: string
  schema_snapshot_id: string
  field_id: string
  field_path: string
  fact_key: string
  entity_id: string
  subject: string
  predicate: string
  object: any
  object_type: string
  valid_from: timestamp
  valid_to: timestamp
  confidence: number
  evidence_packet_id: string
  verification_decision_id: string
  source_snapshot_id: string
  supersedes_fact_id: string
  status: current | superseded | expired | disputed
  created_at: timestamp
```

## ExportTargetSpec

```yaml
ExportTargetSpec:
  id: string
  project_id: string
  target_type: database | warehouse | file | api | object_store | queue
  destination_ref: string
  destination_schema_ref: string
  auth_scope_ref: string
  delivery_mode: batch | streaming | manual
  idempotency_key_template: string
  created_at: timestamp
```

## ExportJob

```yaml
ExportJob:
  id: string
  run_id: string
  export_target_spec_id: string
  output_refs: list
  destination_schema_version: string
  status: queued | running | completed | failed | cancelled
  created_at: timestamp
```

## ExportAttempt

```yaml
ExportAttempt:
  id: string
  export_job_id: string
  attempt_number: integer
  idempotency_key: string
  output_refs: list
  external_object_ids: list
  delivery_receipt_ref: string
  retry_classification: transient | permanent | destination_rejected
  status: running | completed | failed
  error: object
  started_at: timestamp
  ended_at: timestamp
```

## ExportDeliveryReceipt

```yaml
ExportDeliveryReceipt:
  id: string
  export_attempt_id: string
  destination_ref: string
  external_object_ids: list
  delivered_output_refs: list
  withdrawn_output_refs: list
  delete_propagation_refs: list
  acknowledged_at: timestamp
```

## ExportWithdrawalJob

```yaml
ExportWithdrawalJob:
  id: string
  project_id: string
  export_target_spec_id: string
  output_version_refs: list
  reason: superseded | disputed | retention_delete | schema_migration | operator_withdrawal
  status: queued | running | completed | failed | cancelled
  created_at: timestamp
```

## ExportWithdrawalAttempt

```yaml
ExportWithdrawalAttempt:
  id: string
  export_withdrawal_job_id: string
  attempt_number: integer
  idempotency_key: string
  external_object_mappings: list
  propagation_status: pending | propagated | failed | destination_unsupported
  delivery_receipt_ref: string
  error: object
  started_at: timestamp
  ended_at: timestamp
```

## RunDiaryEvent

```yaml
RunDiaryEvent:
  id: string
  run_id: string
  objective_id: string
  actor: string
  summary: string
  related_event_refs: list
  related_output_refs: list
  replay_only: boolean
  promoted_to_memory_event_id: string
  created_at: timestamp
```

`RunDiaryEvent` is V1 replay context. It is not a planning prior unless a later Memory Kernel workflow promotes it into `MemoryEvent`.

## MemoryEvent

```yaml
MemoryEvent:
  id: string
  run_id: string
  objective_id: string
  project_id: string
  site_id: string
  agent_id: string
  wing: string
  room: string
  hall: fact_refs | events | discoveries | problems | preferences | advice
  drawer_refs: list
  closet_refs: list
  kg_refs: list
  diary_text: string
  evidence_refs: list
  content_trust_refs: list
  taint_labels: list
  trust_level: trusted | untrusted | mixed | derived
  promotion_policy_ref: string
  poisoning_check_ref: string
  sanitized_context_ref: string
  allowed_prompt_use: forbidden | sanitized_summary | scoped_context_ref
  freshness:
    observed_at: timestamp
    ttl_seconds: integer
    stale: boolean
  status: active | stale | invalidated | superseded
  invalidated_by_ref: string
  retention_policy_ref: string
  created_at: timestamp
```

Executable memory event rules:

- memory writes require scope, content, provenance, promotion policy, poisoning check, freshness, and policy refs.
- prompt-eligible memory requires a sanitized context ref.
- invalidated memory requires an invalidation ref and must be excluded from retrieval.
- superseded memory requires a replacement memory ref.
- memory refs must not satisfy publication evidence coverage.

## MemoryKernelReport

```yaml
MemoryKernelReport:
  id: string
  run_ref: string
  memory_event_refs: list
  retrieval_trace_ref: string
  tunnel_ref: string
  operational_record_refs: list
  policy_decision_refs: list
  command_record_refs: list
  event_cursor_refs: list
  outbox_refs: list
  failure_report_refs: list
  missing_ref_fields: list
  operator_status: string
  completion_result: pass | fail | needs_review
  created_at: timestamp
```

Rules:

- pass requires memory event, retrieval trace, operational temporal record, policy, command, event cursor, and outbox refs.
- non-pass requires typed failure refs or missing refs.
- memory-as-evidence produces `memory_as_evidence` and `missing_reanchor_evidence`.

## CrawlRunEvent

```yaml
CrawlRunEvent:
  id: string
  run_id: string
  objective_id: string
  crawl_plan_id: string
  event_version: string
  sequence: integer
  event_type: command_received | command_committed | command_rejected | objective_created | plan_proposed | plan_approved | policy_evaluated | approval_decided | agent_action_recorded | model_called | tool_called | memory_retrieved | multi_agent_workflow_started | multi_agent_workflow_completed | multi_agent_workflow_escalated | multi_agent_workflow_failed | agent_handoff_proposed | agent_handoff_accepted | agent_handoff_rejected | agent_handoff_completed | coordination_decision_recorded | coordination_decision_applied | frontier_recommended | frontier_transitioned | queue_item_enqueued | queue_item_leased | queue_item_acked | queue_item_dead_lettered | shard_lease_acquired | shard_lease_released | source_adapter_result_recorded | fetch_attempted | browser_step_executed | credential_used | snapshot_written | processing_transitioned | candidate_created | evidence_built | verification_recommended | verification_decided | output_published | output_withdrawn | result_materialized | export_dispatched | export_delivered | export_withdrawal_attempted | export_withdrawal_completed | export_withdrawal_failed | delete_propagated | artifact_lifecycle_changed | graph_projected | projection_rebuilt | projection_mismatch_detected | migration_started | migration_completed | backfill_started | backfill_completed | run_diary_written | memory_written | drift_detected | review_created | review_decided | conflict_adjudicated | backpressure_signal_recorded | autoscaling_decided | dr_restore_reported | recovery_action_started | recovery_action_completed | error_recorded
  event_type_spec_id: string
  payload_ref: string
  actor: string
  agent_id: string
  model_id: string
  prompt_version: string
  prompt_ref: string
  tool_name: string
  tool_version: string
  tool_input_schema_ref: string
  tool_output_schema_ref: string
  input_refs: list
  output_refs: list
  decision: string
  reason: string
  confidence: number
  state_before: object
  state_after: object
  causation_id: string
  correlation_id: string
  trace_id: string
  run_plan_snapshot_id: string
  policy_snapshot_id: string
  policy_decision_refs: list
  memory_snapshot_refs: list
  graph_snapshot_refs: list
  idempotency_key: string
  error: object
  timestamp: timestamp
```

`CrawlRunEvent` is append-only. `sequence` is ordered within `run_id`, and event-specific payloads must validate against `event_type_spec_id`. Replay-critical events cannot be redacted in a way that removes lineage; sensitive fields should be replaced with stable redacted refs.

## ReplayBundleManifest

```yaml
ReplayBundleManifest:
  id: string
  run_id: string
  objective_id: string
  crawl_plan_id: string
  event_cursor_refs: list
  event_schema_versions: list
  contract_schema_versions: list
  artifact_hash_refs: list
  source_adapter_result_refs: list
  command_result_refs: list
  agent_action_trace_refs: list
  model_call_trace_refs: list
  tool_call_trace_refs: list
  context_bundle_trace_refs: list
  policy_decision_refs: list
  projection_watermark_refs: list
  memory_retrieval_trace_refs: list
  graph_build_manifest_refs: list
  export_receipt_refs: list
  deterministic_clock_ref: string
  randomness_seed_ref: string
  redaction_map_ref: string
  missing_ref_behavior: fail_replay | allow_with_gap_report
  replay_mode: full | redacted | structural
  completeness_result: pass | fail | needs_review
  created_at: timestamp
```

Replay completeness checks:

- required event cursors must be contiguous per ordering scope and stream.
- every mutating command must have a command result and emitted event refs.
- every source adapter command must have a `SourceAdapterResult` and a `source_adapter_result_recorded` event, including blocked or partial adapter outcomes.
- every persisted artifact ref must have a hash or lifecycle tombstone.
- redacted replay must explain redaction without hiding state transitions.
- missing required refs fail replay unless the run is explicitly marked structurally replayable with a gap report.

## Target Event Taxonomy Matrix

Every event type must have an `EventTypeSpec` row. This matrix defines the required owner, aggregate, ordering scope, replay status, and primary consumers for target events.

| Event types | Owner | Aggregate scope | Ordering scope | Replay required | Primary consumers |
| --- | --- | --- | --- | --- | --- |
| command_received, command_committed, command_rejected | control or owner service | command target aggregate | run | yes | replay, ops, recovery |
| objective_created, plan_proposed, plan_approved | control | objective/plan/job/run | objective, plan | yes | scheduler, agents, replay |
| policy_evaluated, approval_decided | control | policy/approval subject | run | yes | tool gateway, publication, audit |
| agent_action_recorded, model_called, tool_called, memory_retrieved, frontier_recommended | agents | agent trace/workflow | run | yes | replay, review, ops |
| multi_agent_workflow_started, multi_agent_workflow_completed, multi_agent_workflow_escalated, multi_agent_workflow_failed | agents | MultiAgentWorkflow | run | yes | replay, review, ops |
| agent_handoff_proposed, agent_handoff_accepted, agent_handoff_rejected, agent_handoff_completed | agents | AgentHandoff | run | yes | replay, coordination |
| coordination_decision_recorded, coordination_decision_applied | agents | CoordinationDecision | run | yes | replay, owner services |
| frontier_transitioned | scheduler | FrontierItem | frontier_item | yes | fetch, graph, replay |
| queue_item_enqueued, queue_item_leased, queue_item_acked, queue_item_dead_lettered, shard_lease_acquired, shard_lease_released | scheduler | QueueItem/ShardLease/RetryDeadLetterRecord | frontier_item, processing_task, export_job, graph_projection | yes | workers, ops, replay |
| source_adapter_result_recorded | natural adapter owner | SourceAdapterResult | source_adapter | yes | scheduler, normalize, evidence, replay |
| fetch_attempted, snapshot_written | fetch/browser | FetchAttempt/PageSnapshot | fetch_attempt, artifact | yes | normalize, evidence, replay |
| browser_step_executed | browser | BrowserInteractionStep | artifact, run | yes | security, replay, review |
| credential_used | control | CredentialUseAudit | run | yes | security, replay, review |
| processing_transitioned | normalize/extract/evidence/verify/publish/graph/memory | ProcessingTask | processing_task | yes | ops, replay |
| candidate_created | extract | ExtractionCandidate | candidate | yes | evidence, review |
| evidence_built | evidence | EvidencePacket | evidence_packet | yes | verify, review, publish |
| verification_recommended, verification_decided | verify | VerificationRecommendation/Decision | verification_decision | yes | publish, review, graph |
| output_published, output_withdrawn, result_materialized | publish | PublishedOutput/OutputManifest | output | yes | export, replay, result API |
| export_dispatched, export_delivered, export_withdrawal_attempted, export_withdrawal_completed, export_withdrawal_failed | export | ExportJob/Receipt/Withdrawal | export_job | yes | ops, audit, reconciliation |
| delete_propagated, artifact_lifecycle_changed | artifact_lifecycle | ArtifactLifecycleState | artifact_lifecycle | yes | projections, privacy, replay |
| graph_projected | graph | GraphBuildManifest | graph_projection | yes | agents, ops, replay |
| projection_rebuilt | projection | ProjectionWatermark/ProjectionRebuildJob | projection | yes | agents, ops, replay |
| projection_mismatch_detected | projection | ProjectionMismatchReport | projection | yes | ops, recovery, replay |
| migration_started, migration_completed, backfill_started, backfill_completed | owner service | SchemaMigrationRun/EventMigrationRun/BackfillJob | run, graph_projection, artifact_lifecycle | yes | ops, replay |
| memory_written | memory | MemoryEvent | memory_event | yes | agents, replay |
| run_diary_written | control/agents | RunDiaryEvent | run | yes | replay |
| drift_detected | graph/extract/ops | DriftEvent | run | yes | repair, review |
| review_created, review_decided, conflict_adjudicated | review_replay/verify | ReviewItem/ConflictRecord | review_item, conflict | yes | publish, ops, replay |
| backpressure_signal_recorded, autoscaling_decided | ops | BackpressureSignal/AutoscalingDecision | run | yes | ops, scheduler |
| dr_restore_reported | ops | DRRestoreReport | run | yes | ops, audit |
| recovery_action_started, recovery_action_completed, error_recorded | ops or owner service | FailureRecord/RecoveryAction | recovery_action | yes | ops, replay |

## Event Payload Registry

Every `EventTypeSpec.payload_schema_ref` must resolve to a payload schema with required refs, state requirements, redaction behavior, and replay-critical fields.

| Event family | Payload schema | Required refs | State fields | Redaction behavior |
| --- | --- | --- | --- | --- |
| command events | CommandEventPayload | CommandEnvelope, CommandResult when committed/rejected | status before/after | payload may be redacted, command IDs remain |
| objective/plan events | PlanEventPayload | CrawlObjective, CrawlPlan, RunPlanSnapshot | lifecycle/approval status | user text can be redacted with stable ref |
| policy/approval/review events | DecisionEventPayload | PolicyDecision, ApprovalDecision, ReviewDecision | decision before/after | reviewer identity follows audit policy |
| agent/model/tool events | AgentTraceEventPayload | AgentActionTrace, ModelCallTrace, ToolCallTrace, ContextBundleTrace | trace status | raw prompt/response may be redacted, trace refs remain |
| workflow/handoff/coordination events | MultiAgentWorkflowEventPayload | MultiAgentWorkflow, AgentHandoff, CoordinationDecision | workflow/handoff status | context refs may be redacted, decisions remain |
| queue/lease/frontier events | QueueFrontierEventPayload | QueueItem, ShardLease, FrontierItem | queue/frontier state before/after | no replay-critical redaction |
| fetch/browser/session events | FetchBrowserEventPayload | FetchAttempt, SourceAdapterResult, BrowserInteractionStep, CredentialUseAudit | attempt/step status | raw secret material is never serialized; audit refs remain |
| processing/extraction/evidence events | ProcessingEvidenceEventPayload | ProcessingTask, ExtractionCandidate, EvidencePacket | task/candidate status | source snippets may be redacted with artifact refs |
| verification/publication events | PublicationEventPayload | VerificationDecision, PublishedOutput, OutputManifest, EvidenceCoverageMap | decision/output status | output values follow publication privacy policy |
| graph/projection events | ProjectionEventPayload | ProjectionWatermark, ProjectionRebuildJob, GraphBuildManifest, ProjectionMismatchReport | projection status | projection refs remain |
| memory events | MemoryEventPayload | MemoryEvent, MemoryRetrievalTrace, CrossScopeMemoryTunnel | memory/tunnel status | memory content may be summarized or redacted |
| export events | ExportEventPayload | ExportJob, ExportAttempt, ExportDeliveryReceipt, ExportWithdrawalJob | export status | destination auth refs redacted |
| artifact lifecycle events | ArtifactLifecycleEventPayload | ArtifactLifecycleState | lifecycle/hold status | redaction/tombstone refs remain |
| failure/recovery/ops events | OpsEventPayload | FailureRecord, RecoveryAction, BackpressureSignal, AutoscalingDecision, DRRestoreReport | recovery/status fields | incident details follow audit policy |

Event payload schema definitions:

```yaml
BaseEventPayload:
  event_id: string
  event_type: string
  aggregate_ref: string
  command_id: string
  command_result_id: string
  causation_id: string
  correlation_id: string
  state_before: object
  state_after: object
  required_ref_hashes: list
  replay_critical_fields: list
  redaction_policy_ref: string
```

| Payload schema | Required typed fields | Required refs | State shape | Replay and redaction rules |
| --- | --- | --- | --- | --- |
| CommandEventPayload | command_type:string, target_aggregate_type:string, target_aggregate_id:string, command_status:string | CommandEnvelope, CommandResult when terminal | `state_before.status`, `state_after.status` | command metadata and idempotency key hash are never redacted |
| PlanEventPayload | objective_id:string, plan_id:string, plan_version:string, approval_status:string | CrawlObjective, CrawlPlan, RunPlanSnapshot when approved | lifecycle/approval fields | user instruction can be redacted by stable ref |
| DecisionEventPayload | subject_ref:string, subject_type:string, decision:string, authority_ref:string | PolicyDecision, ApprovalDecision, ReviewDecision, AdjudicationDecision when applicable | decision/status fields | authority refs remain; reviewer identity follows audit policy |
| AgentTraceEventPayload | agent_role:string, runtime_spec_id:string, trace_status:string | AgentActionTrace, ModelCallTrace, ToolCallTrace, ContextBundleTrace | trace/tool status fields | raw prompt/response redacted unless policy permits |
| MultiAgentWorkflowEventPayload | workflow_id:string, workflow_status:string, handoff_status:string, selected_ref:string | MultiAgentWorkflow, AgentHandoff, CoordinationDecision | workflow/handoff status | context refs remain stable under redaction |
| QueueFrontierEventPayload | queue_name:string, shard_key:string, aggregate_id:string, transition_version:integer | QueueItem, ShardLease, FrontierItem | queue/frontier/lease status | lease token secret material redacted, token hash remains |
| FetchBrowserEventPayload | adapter_type:string, result_type:string, artifact_refs:list, side_effect_class:string | SourceAdapterResult, FetchAttempt, BrowserInteractionStep, CredentialUseAudit when applicable | adapter/attempt/step status | raw secrets never serialized; artifact refs remain |
| ProcessingEvidenceEventPayload | task_type:string, owner_service:string, candidate_ref:string, coverage_result:string | ProcessingTask, ExtractionCandidate, EvidencePacket, EvidenceCoverageMap when applicable | task/candidate/evidence status | source snippets redacted by artifact refs |
| PublicationEventPayload | output_type:string, output_version:string, decision:string, manifest_hash:string | VerificationDecision, PublishedOutput, OutputManifest, OutputVerificationAggregate | decision/output/fact status | output values follow publication privacy policy |
| ProjectionEventPayload | projection_name:string, projection_status:string, event_cursor_refs:list, expected_hash:string, actual_hash:string | ProjectionWatermark, ProjectionRebuildJob, GraphBuildManifest, ProjectionMismatchReport | projection/rebuild status | cursor refs and hashes remain replay-critical |
| MemoryEventPayload | memory_scope_ref:string, trust_level:string, taint_labels:list, allowed_prompt_use:string | MemoryEvent, MemoryRetrievalTrace, CrossScopeMemoryTunnel, OperationalTemporalMemoryRecord | memory/tunnel status | memory content may be summarized; policy refs remain |
| ExportEventPayload | export_target_ref:string, external_object_ids:list, propagation_status:string, receipt_ref:string | ExportJob, ExportAttempt, ExportDeliveryReceipt, ExportWithdrawalJob, ExportWithdrawalAttempt | export/withdrawal status | destination auth refs redacted |
| ArtifactLifecycleEventPayload | artifact_ref:string, lifecycle_status:string, hold_status:string, delete_propagation_refs:list | ArtifactLifecycleState | lifecycle and hold fields | deleted content never serialized; tombstone refs remain |
| OpsEventPayload | failure_type:string, severity:string, recovery_status:string, validation_result:string | FailureRecord, RecoveryAction, BackpressureSignal, AutoscalingDecision, DRRestoreRun, DRRestoreReport when applicable | ops/recovery/DR status | stack traces and incident details follow audit policy |

Per-event payload field registry:

Generated contract tests must compare `CrawlRunEvent.event_type` to this registry. Any missing row, unresolved `payload_schema_ref`, missing required ref, or missing replay-critical field fails target acceptance.

| Event type | Payload schema | Required payload refs | State before/after | Replay-critical fields | Redaction policy |
| --- | --- | --- | --- | --- | --- |
| command_received | CommandEventPayload | CommandEnvelope | before optional, after required | command id, command type, target aggregate, idempotency key | payload may be redacted; command metadata remains |
| command_committed | CommandEventPayload | CommandEnvelope, CommandResult | before and after required | command/result ids, emitted events, expected version | payload may be redacted; transition refs remain |
| command_rejected | CommandEventPayload | CommandEnvelope, CommandResult | before and after required | rejection reasons, policy/approval refs | rejected payload may be redacted |
| objective_created | PlanEventPayload | CrawlObjective | after required | objective id, policy snapshot, target schemas | instruction may use stable redacted ref |
| plan_proposed | PlanEventPayload | CrawlPlan, RunPlanSnapshot when available | after required | plan version, adapter plan, evidence requirements | user text may be redacted |
| plan_approved | PlanEventPayload | CrawlPlan, ApprovalDecision, RunPlanSnapshot | before and after required | approver authority, approved version, policy refs | reviewer identity follows audit policy |
| policy_evaluated | DecisionEventPayload | PolicyDecision | after required | decision type, subject ref, evaluated rules | sensitive policy inputs redacted by ref |
| approval_decided | DecisionEventPayload | ApprovalDecision | before optional, after required | authority, decision, resulting allowed commands | reviewer identity follows audit policy |
| agent_action_recorded | AgentTraceEventPayload | AgentActionTrace | after required | runtime spec, context trace, command results | reasoning summary can be redacted by ref |
| model_called | AgentTraceEventPayload | ModelCallTrace, ModelRequest, ModelResponse | after required | model id/version, prompt template, context bundle | raw prompt/response redacted unless policy allows |
| tool_called | AgentTraceEventPayload | ToolCallTrace | before and after required | tool spec, command/result refs, policy refs | tool input/output may be redacted by schema |
| memory_retrieved | MemoryEventPayload | MemoryRetrievalTrace | after required | scope, included/excluded memory refs, tunnel ref | memory content may be summarized |
| multi_agent_workflow_started | MultiAgentWorkflowEventPayload | MultiAgentWorkflow | before and after required | workflow id, loop budget, agent roles | context refs may be redacted |
| multi_agent_workflow_completed | MultiAgentWorkflowEventPayload | MultiAgentWorkflow | before and after required | terminal status, output refs, trace refs | context refs may be redacted |
| multi_agent_workflow_escalated | MultiAgentWorkflowEventPayload | MultiAgentWorkflow, ReviewItem | before and after required | escalation rule, review item, trace refs | context refs may be redacted |
| multi_agent_workflow_failed | MultiAgentWorkflowEventPayload | MultiAgentWorkflow, FailureRecord when available | before and after required | failure reason, recovery refs | incident details follow audit policy |
| agent_handoff_proposed | MultiAgentWorkflowEventPayload | AgentHandoff | after required | from trace, target role, context bundle trace | context refs may be redacted |
| agent_handoff_accepted | MultiAgentWorkflowEventPayload | AgentHandoff | before and after required | accepting role, policy refs | context refs may be redacted |
| agent_handoff_rejected | MultiAgentWorkflowEventPayload | AgentHandoff | before and after required | rejection reason, policy refs | context refs may be redacted |
| agent_handoff_completed | MultiAgentWorkflowEventPayload | AgentHandoff | before and after required | output schema refs, output refs | output refs remain stable |
| coordination_decision_recorded | MultiAgentWorkflowEventPayload | CoordinationDecision | after required | candidates, selected ref, arbitration policy | rationale may be redacted by ref |
| coordination_decision_applied | MultiAgentWorkflowEventPayload | CoordinationDecision, CommandResult | before and after required | applied command result, selected ref | rationale may be redacted by ref |
| frontier_recommended | AgentTraceEventPayload | FrontierRecommendation | after required | recommendation type, priority delta, input refs | rationale may be redacted by ref |
| frontier_transitioned | QueueFrontierEventPayload | FrontierItem | before and after required | canonical URL/source key, transition version | no replay-critical redaction |
| queue_item_enqueued | QueueFrontierEventPayload | QueueItem | after required | queue, shard key, command ref, idempotency key | no replay-critical redaction |
| queue_item_leased | QueueFrontierEventPayload | QueueItem, ShardLease | before and after required | lease token hash, worker id, expiry | lease token secret material redacted |
| queue_item_acked | QueueFrontierEventPayload | QueueItem, CommandResult | before and after required | lease token hash, command result refs | lease token secret material redacted |
| queue_item_dead_lettered | QueueFrontierEventPayload | QueueItem, RetryDeadLetterRecord | before and after required | retry class, attempts, failure record | incident details follow audit policy |
| shard_lease_acquired | QueueFrontierEventPayload | ShardLease | after required | shard key, worker id, lease token hash | lease token secret material redacted |
| shard_lease_released | QueueFrontierEventPayload | ShardLease | before and after required | release reason, lease token hash | lease token secret material redacted |
| source_adapter_result_recorded | FetchBrowserEventPayload | SourceAdapterResult | before optional, after required | adapter type, result type, output refs, policy refs | blocked reasons remain; secrets redacted |
| fetch_attempted | FetchBrowserEventPayload | FetchAttempt, SourceAdapterResult when applicable | after required | attempt id, URL/source ref, idempotency key | request auth material redacted |
| browser_step_executed | FetchBrowserEventPayload | BrowserInteractionStep | before and after required | step number, side-effect class, artifact refs | inputs redacted by policy |
| credential_used | FetchBrowserEventPayload | CredentialUseAudit | after required | delivery mode, exposure class, origin, policy refs | raw secrets never serialized |
| snapshot_written | FetchBrowserEventPayload | PageSnapshot or artifact ref | after required | content hash, artifact refs, source adapter result | artifact body redacted by lifecycle policy |
| processing_transitioned | ProcessingEvidenceEventPayload | ProcessingTask | before and after required | task type, owner service, output refs | source snippets redacted by artifact ref |
| candidate_created | ProcessingEvidenceEventPayload | ExtractionCandidate | after required | strategy ref, schema snapshot, source refs | candidate values follow privacy policy |
| evidence_built | ProcessingEvidenceEventPayload | EvidencePacket, EvidenceCoverageMap when available | after required | anchors, source evidence refs, coverage refs | source snippets may be redacted by artifact ref |
| verification_recommended | PublicationEventPayload | VerificationRecommendation | after required | candidate, evidence packet, recommended decision | rationale may be redacted by ref |
| verification_decided | PublicationEventPayload | VerificationDecision | before optional, after required | decision authority, method, evidence packet | reviewer identity follows audit policy |
| output_published | PublicationEventPayload | PublishedOutput, OutputManifest, OutputVerificationAggregate | before and after required | output version, manifest hash, verification refs | output values follow publication policy |
| output_withdrawn | PublicationEventPayload | PublishedOutput | before and after required | withdrawn output, reason, withdrawal refs | output values follow publication policy |
| result_materialized | PublicationEventPayload | PublishedOutput, OutputManifest | after required | result API/file/object refs, manifest hash | materialized value policy applies |
| export_dispatched | ExportEventPayload | ExportJob, ExportAttempt | before and after required | target spec, idempotency key, output refs | destination auth refs redacted |
| export_delivered | ExportEventPayload | ExportAttempt, ExportDeliveryReceipt | before and after required | external object ids, receipt ref | destination auth refs redacted |
| export_withdrawal_attempted | ExportEventPayload | ExportWithdrawalJob, ExportWithdrawalAttempt | before and after required | external object mappings, propagation status | destination auth refs redacted |
| export_withdrawal_completed | ExportEventPayload | ExportWithdrawalAttempt, ExportDeliveryReceipt | before and after required | external object mappings, propagation status, receipt ref | destination auth refs redacted |
| export_withdrawal_failed | ExportEventPayload | ExportWithdrawalAttempt, FailureRecord when available | before and after required | external object mappings, retry classification, error ref | destination auth refs redacted |
| delete_propagated | ArtifactLifecycleEventPayload | ArtifactLifecycleState | before and after required | deletion/tombstone refs, projection cleanup refs | deleted content not serialized |
| artifact_lifecycle_changed | ArtifactLifecycleEventPayload | ArtifactLifecycleState | before and after required | lifecycle status, hold status, retention policy | redaction/tombstone refs remain |
| graph_projected | ProjectionEventPayload | GraphBuildManifest or TemporalKGProjectionRecord | before optional, after required | input cursors, projection watermark, hash | graph payload follows privacy projection policy |
| projection_rebuilt | ProjectionEventPayload | ProjectionRebuildJob, ProjectionWatermark | before and after required | event cursor refs, expected/actual hashes | projection refs remain |
| projection_mismatch_detected | ProjectionEventPayload | ProjectionMismatchReport | after required | projection spec, expected/actual hash, cursor refs | mismatch details follow audit policy |
| migration_started | ProjectionEventPayload | SchemaMigrationRun or EventMigrationRun | before and after required | migration id/version, rollback plan | migration refs remain |
| migration_completed | ProjectionEventPayload | SchemaMigrationRun or EventMigrationRun | before and after required | validation refs, replay result, rollback status | migration refs remain |
| backfill_started | ProjectionEventPayload | BackfillJob | before and after required | checkpoint, idempotency key, owner service | backfill refs remain |
| backfill_completed | ProjectionEventPayload | BackfillJob | before and after required | checkpoint, output refs, validation refs | backfill refs remain |
| run_diary_written | AgentTraceEventPayload | RunDiaryEvent | after required | related events and outputs | diary text may be summarized |
| memory_written | MemoryEventPayload | MemoryEvent or OperationalTemporalMemoryRecord | before optional, after required | taint labels, trust level, evidence refs | memory content may be redacted |
| drift_detected | OpsEventPayload | DriftEvent | after required | affected refs, drift type, evidence refs | source snippets redacted by artifact ref |
| review_created | DecisionEventPayload | ReviewItem | after required | item type, subject refs, priority | reviewer queue metadata remains |
| review_decided | DecisionEventPayload | ReviewItem, ReviewDecision | before and after required | authority, decision type, resulting transitions | reviewer identity follows audit policy |
| conflict_adjudicated | DecisionEventPayload | ConflictRecord, AdjudicationDecision | before and after required | conflict id, decision, resulting outputs | evidence refs remain |
| backpressure_signal_recorded | OpsEventPayload | BackpressureSignal | after required | signal type, threshold, measured value | operational metrics remain |
| autoscaling_decided | OpsEventPayload | AutoscalingDecision | after required | scaling action, budget refs, decision reason | operational metrics remain |
| dr_restore_reported | OpsEventPayload | DRRestoreReport | after required | restore point, validation result, missing refs | incident details follow audit policy |
| recovery_action_started | OpsEventPayload | RecoveryAction | before and after required | recovery action id, affected refs, approval refs | incident details follow audit policy |
| recovery_action_completed | OpsEventPayload | RecoveryAction | before and after required | output refs, validation result | incident details follow audit policy |
| error_recorded | OpsEventPayload | FailureRecord | after required | failure type, owner, correlation id, recovery refs | stack traces redacted by audit policy |

## ReviewItem

```yaml
ReviewItem:
  id: string
  run_id: string
  objective_id: string
  item_type: crawl_plan | schema | publication_policy | source_adapter | browser_interaction | authorized_session | credential_use | extraction_candidate | evidence_packet | verification_recommendation | publication | export_dispatch | export_withdrawal | artifact_lifecycle | retention | memory_retrieval | cross_scope_memory_tunnel | graph_signal_use | recovery_action | multi_agent_workflow | conflict | drift | safety_policy
  input_refs: list
  reason: string
  priority: low | normal | high | urgent
  status: open | accepted | rejected | needs_more_evidence | resolved
  reviewer_id: string
  decision_refs: list
  created_at: timestamp
  updated_at: timestamp
```

## ReviewDecision

```yaml
ReviewDecision:
  id: string
  review_item_id: string
  reviewer_id: string
  authority_ref: string
  decision_type: approve | reject | request_more_evidence | reopen | escalate
  reason_codes: list
  evidence_input_refs: list
  resulting_transition_refs: list
  follow_up_task_refs: list
  appeal_allowed: boolean
  created_at: timestamp
```

## ConflictRecord

```yaml
ConflictRecord:
  id: string
  run_id: string
  objective_id: string
  conflict_type: value | identity | temporal | source | schema | policy
  candidate_refs: list
  output_refs: list
  evidence_packet_refs: list
  counter_evidence_refs: list
  temporal_context: object
  severity: low | medium | high | blocking
  status: open | adjudicated | superseded | disputed | ignored
  adjudication_decision_ref: string
  resulting_output_refs: list
  created_at: timestamp
  updated_at: timestamp
```

## AdjudicationDecision

```yaml
AdjudicationDecision:
  id: string
  conflict_record_id: string
  reviewer_id: string
  authority_ref: string
  decision: accept_new | keep_existing | mark_disputed | supersede | reject_all
  reason_codes: list
  evidence_input_refs: list
  resulting_output_refs: list
  resulting_state_transitions: list
  reopen_policy_ref: string
  created_at: timestamp
```

## DriftEvent

```yaml
DriftEvent:
  id: string
  run_id: string
  site_id: string
  objective_id: string
  drift_type: template | selector | content_distribution | entity_graph | source_policy
  severity: low | medium | high | critical
  affected_refs: list
  evidence_refs: list
  proposed_repair_refs: list
  status: observed | reviewed | repaired | ignored
  created_at: timestamp
```

## QueueItem

```yaml
QueueItem:
  id: string
  queue_name: frontier | processing | verification_review | export_outbox | projection | recovery
  shard_key: string
  run_id: string
  aggregate_type: string
  aggregate_id: string
  command_ref: string
  priority: number
  retry_class: transient | rate_limited | policy_blocked | permanent_source_failure | adapter_bug | worker_crash | projection_mismatch | destination_rejected
  lease_token: string
  lease_expires_at: timestamp
  attempts: integer
  deadline_at: timestamp
  status: queued | leased | acked | nacked | dead_lettered
  created_at: timestamp
  updated_at: timestamp
```

## ShardLease

```yaml
ShardLease:
  id: string
  queue_name: string
  shard_key: string
  worker_id: string
  lease_token: string
  acquired_at: timestamp
  heartbeat_at: timestamp
  expires_at: timestamp
  status: active | expired | released | revoked
```

## RetryDeadLetterRecord

```yaml
RetryDeadLetterRecord:
  id: string
  queue_item_id: string
  run_id: string
  retry_class: transient | rate_limited | policy_blocked | permanent_source_failure | adapter_bug | worker_crash | projection_mismatch | destination_rejected
  attempts: integer
  final_reason: string
  failure_record_id: string
  recovery_action_refs: list
  created_at: timestamp
```

## BackpressureSignal

```yaml
BackpressureSignal:
  id: string
  project_id: string
  site_id: string
  signal_type: queue_lag | retry_rate | browser_minutes | token_spend | object_store_growth | projection_lag | export_lag | error_rate
  value: number
  threshold: number
  severity: low | medium | high | critical
  policy_decision_refs: list
  created_at: timestamp
```

## AutoscalingDecision

```yaml
AutoscalingDecision:
  id: string
  worker_pool: fetch | browser | processing | export | projection
  reason_signal_refs: list
  from_capacity: integer
  to_capacity: integer
  cooldown_seconds: integer
  policy_decision_refs: list
  created_at: timestamp
```

## ProjectionMismatchReport

```yaml
ProjectionMismatchReport:
  id: string
  projection_rebuild_job_id: string
  expected_hash: string
  actual_hash: string
  differing_refs: list
  severity: low | medium | high | critical
  recovery_action_refs: list
  created_at: timestamp
```

## DRRestorePlan

```yaml
DRRestorePlan:
  id: string
  restore_scope_ref: string
  restore_point:
    event_cursor_refs: list
    metadata_snapshot_ref: string
    artifact_snapshot_refs: list
    backup_manifest_ref: string
  ordered_phases:
    - phase_name: restore_metadata | restore_artifacts | replay_events | rebuild_projections | reconcile_exports | validate_references | publish_report
      phase_order: integer
      input_refs: list
      output_contract_refs: list
      validation_gate_refs: list
      rollback_behavior: retry | pause | rollback | manual_review
  required_validation_gates: list
  approval_decision_refs: list
  created_at: timestamp
```

## DRRestoreRun

```yaml
DRRestoreRun:
  id: string
  dr_restore_plan_id: string
  restore_scope_ref: string
  phase_results:
    - phase_name: restore_metadata | restore_artifacts | replay_events | rebuild_projections | reconcile_exports | validate_references | publish_report
      status: pending | running | completed | failed | skipped
      started_at: timestamp
      ended_at: timestamp
      input_refs: list
      output_refs: list
      validation_result_refs: list
      failure_record_ref: string
  current_phase: string
  status: planned | running | completed | failed | needs_review
  emitted_event_refs: list
  created_at: timestamp
  updated_at: timestamp
```

DR restore rules:

- restore phases must run in `phase_order` unless a skipped phase is explicitly allowed by the plan.
- `completed` requires all required validation gates to pass and `DRRestoreReport.result = pass`.
- `needs_review` requires unresolved refs or validation warnings to be visible in the report.
- `failed` requires a `FailureRecord` and recovery or review action.

## DRRestoreReport

```yaml
DRRestoreReport:
  id: string
  restore_scope_ref: string
  dr_restore_plan_id: string
  dr_restore_run_id: string
  metadata_restore_ref: string
  artifact_reachability_report_ref: string
  event_replay_report_ref: string
  projection_rebuild_job_refs: list
  export_reconciliation_refs: list
  data_loss_detected: boolean
  unresolved_refs: list
  result: pass | fail | needs_review
  created_at: timestamp
```

## FailureRecord

```yaml
FailureRecord:
  id: string
  run_id: string
  failure_type: fetch | browser | session | credential | model | agent | tool | queue | lease | dead_letter | processing | verification | publication | export | projection | projection_mismatch | memory | migration | backfill | artifact_lifecycle | retention | policy | autoscaling | backpressure | disaster_recovery
  failed_ref: string
  severity: low | medium | high | critical
  retryable: boolean
  orphan_artifact_refs: list
  partial_side_effect_refs: list
  dead_letter_reason: string
  created_at: timestamp
```

## RecoveryAction

```yaml
RecoveryAction:
  id: string
  failure_record_id: string
  action_type: retry_command | retry_queue_item | renew_lease | replay_events | tombstone_artifact | redact_artifact | delete_artifact | release_legal_hold | withdraw_output | reconcile_export | rebuild_projection | rerun_migration | rerun_backfill | invalidate_memory | quarantine_tainted_context | pause_site | scale_worker_pool | restore_from_backup | request_review | ignore
  command_refs: list
  policy_decision_refs: list
  approval_decision_refs: list
  status: proposed | approved | running | completed | failed
  result_refs: list
  created_at: timestamp
  updated_at: timestamp
```

## QualityReport

```yaml
QualityReport:
  id: string
  run_id: string
  pages_fetched: integer
  candidates_created: integer
  outputs_published: integer
  verification_decisions_accepted: integer
  verification_decisions_rejected: integer
  factual_outputs_published: integer
  conflicts_detected: integer
  drift_events: integer
  freshness_lag_seconds: integer
  extraction_success_rate: number
  verification_acceptance_rate: number
  cost_summary: object
  open_review_items: list
  created_at: timestamp
```
