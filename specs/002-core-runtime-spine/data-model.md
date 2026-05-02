# Data Model: VeraCrawl Target Core Runtime Spine

## Ownership Summary

| Entity | Owner service | Mutation path | Replay requirement |
| --- | --- | --- | --- |
| CrawlObjective | control | command -> policy -> control aggregate -> event | objective refs, policy refs, command result |
| CrawlPlan | control | command -> plan proposal/approval -> event | assumptions, adapter choices, evidence requirements |
| CrawlRun | control | command -> run lifecycle -> gate events | run status, gate refs, event cursors |
| RunPlanSnapshot | control | start run -> immutable snapshot | snapshot hash and policy/schema/tool refs |
| RuntimeCompletionGate | control/review_replay | owner gate evaluation -> event | gate status and blocking refs |
| SourceAdapterResult | natural adapter owner | source adapter command -> policy -> result -> event | adapter command/result/event refs |
| RuntimeArtifactRef | artifact_lifecycle plus producing owner | artifact write/classify -> lifecycle refs | content hash, privacy, redaction, retention refs |
| NormalizedDocument | normalize | processing command -> normalized artifact -> event | raw artifact, transform, anchor map refs |
| ExtractionCandidate | extract | extraction command/proposal -> candidate event | schema, artifact, anchor, confidence refs |
| EvidencePacket | evidence | build evidence -> coverage validation -> event | source evidence refs and coverage refs |
| VerificationDecision | verify | decide verification -> policy/review -> event | decision, authority, evidence refs |
| PublishedOutput | publish | publish output -> manifest -> event | immutable output and publication refs |
| OutputManifest | publish | publish output -> manifest hash -> event | evidence, verification, output, artifact refs |
| ReplayBundleManifest | review_replay | build replay bundle -> completeness check | command/event/artifact/trace/redaction refs |

## Entity Details

### CrawlObjective

- `id`
- `project_ref`
- `site_scope_refs`
- `objective_text_ref`
- `target_schema_refs`
- `evidence_requirement_refs`
- `freshness_policy_ref`
- `source_policy_refs`
- `publication_policy_refs`
- `status`: draft, approved, active, paused, archived
- `created_by_ref`
- `created_at`

Validation rules:

- Scope and source policy refs are required before approval.
- At least one target schema and evidence requirement is required for runtime execution.
- Archived objectives cannot start new runs.

### CrawlPlan

- `id`
- `objective_ref`
- `plan_version`
- `adapter_plan`
- `seed_refs`
- `assumption_refs`
- `alternative_refs`
- `risk_refs`
- `evidence_requirement_refs`
- `budget_ref`
- `approval_decision_ref`
- `status`: proposed, approved, rejected, superseded

Validation rules:

- Approved plans require an approval decision and at least one source adapter choice.
- Rejected and superseded plans cannot start runs.
- Adapter choices must resolve to registered source adapter specs.

### CrawlRun

- `id`
- `objective_ref`
- `plan_ref`
- `run_plan_snapshot_ref`
- `status`: queued, running, paused, completed, failed, cancelled
- `completion_gate_refs`
- `policy_snapshot_ref`
- `budget_ref`
- `event_cursor_refs`
- `failure_record_refs`
- `created_at`
- `updated_at`

Validation rules:

- A run can start only from an approved plan.
- Completion requires gate-specific checks; `completed` does not imply publication-complete unless publication and replay gates pass.
- Terminal runs reject pause, resume, and new processing commands.

### RunPlanSnapshot

- `id`
- `objective_ref`
- `plan_ref`
- `plan_hash`
- `policy_refs`
- `schema_refs`
- `adapter_spec_refs`
- `tool_refs`
- `model_refs`
- `evidence_requirement_refs`
- `replay_config_ref`
- `created_at`

Validation rules:

- Snapshot is immutable after run start.
- Snapshot hash must be included in replay bundle.

### RuntimeCompletionGate

- `id`
- `run_ref`
- `gate_type`: objective, plan, source, normalization, extraction, evidence, verification, publication, replay
- `status`: pending, pass, fail, needs_review, blocked, conflict
- `required_ref_fields`
- `present_ref_fields`
- `missing_ref_fields`
- `blocking_reason_refs`
- `evaluated_at`

Validation rules:

- Publication gate requires objective, plan, source, normalization, extraction, evidence, and verification gates to pass.
- Replay gate requires all replay-critical refs or returns fail/needs_review according to missing-ref behavior.

### RuntimeArtifactRef

- `id`
- `artifact_type`: raw_source, normalized_document, anchor_map, candidate_payload, evidence_bundle, output_manifest, replay_bundle, redaction_map
- `producer_service`
- `source_ref`
- `content_hash`
- `size_bytes`
- `privacy_classification`
- `lifecycle_state_ref`
- `retention_policy_ref`
- `created_at`

Validation rules:

- Content hash is required.
- Raw secrets must never be serialized into artifact refs, logs, replay bundles, or agent-visible state.
- Deleted, tombstoned, or legally held artifacts cannot support current publication unless policy explicitly allows the historical use case.

### NormalizedDocument

- `id`
- `run_ref`
- `source_adapter_result_ref`
- `raw_artifact_ref`
- `normalized_artifact_ref`
- `anchor_map_ref`
- `normalization_manifest_ref`
- `language_refs`
- `created_at`

Validation rules:

- Raw artifact, normalized artifact, and anchor map refs are required.
- Normalized document cannot be produced from a blocked source adapter result.

### ExtractionCandidate

- `id`
- `run_ref`
- `schema_ref`
- `normalized_document_refs`
- `field_values`
- `field_anchor_refs`
- `confidence_refs`
- `strategy_ref`
- `agent_recommendation_ref`
- `status`: candidate, evidence_built, rejected, conflicted, superseded, published

Validation rules:

- Required fields must have source anchor refs before evidence can pass.
- Agent recommendation refs are optional and cannot mutate candidate state directly.

### EvidencePacket

- `id`
- `candidate_ref`
- `source_evidence_refs`
- `anchor_refs`
- `coverage_result_ref`
- `prior_verified_output_refs`
- `graph_signal_refs`
- `memory_refs`
- `agent_reasoning_refs`
- `status`: built, accepted_for_verification, rejected, superseded

Validation rules:

- Required coverage can be satisfied only by source evidence refs or policy-allowed prior verified outputs.
- Graph, memory, and agent reasoning refs may explain decisions but cannot satisfy source evidence coverage.

### VerificationDecision

- `id`
- `candidate_ref`
- `evidence_packet_ref`
- `decision`: accept, reject, review, conflict
- `authority_ref`
- `policy_decision_refs`
- `conflict_record_refs`
- `freshness_ref`
- `created_at`

Validation rules:

- Accept requires evidence coverage pass and publication policy allow.
- Conflict prevents publication until adjudicated or superseded.

### PublishedOutput

- `id`
- `run_ref`
- `candidate_ref`
- `verification_decision_ref`
- `output_manifest_ref`
- `status`: published, superseded, withdrawn, expired
- `published_at`

Validation rules:

- Published output is immutable.
- Only accepted verification decisions can publish.

### OutputManifest

- `id`
- `published_output_ref`
- `output_version`
- `schema_refs`
- `field_evidence_refs`
- `evidence_coverage_ref`
- `verification_decision_refs`
- `publication_policy_decision_refs`
- `artifact_refs`
- `privacy_lifecycle_refs`
- `export_lifecycle_refs`
- `replay_bundle_ref`
- `manifest_hash`

Validation rules:

- Manifest hash is required and append-only.
- Every required field/item must map to evidence and accepted verification.

### ReplayBundleManifest

- `id`
- `run_ref`
- `command_result_refs`
- `event_cursor_refs`
- `source_adapter_result_refs`
- `artifact_hash_refs`
- `normalized_document_refs`
- `extraction_candidate_refs`
- `evidence_packet_refs`
- `verification_decision_refs`
- `output_manifest_refs`
- `agent_trace_refs`
- `policy_decision_refs`
- `redaction_map_ref`
- `deterministic_clock_ref`
- `randomness_seed_ref`
- `missing_ref_behavior`
- `completeness_result`

Validation rules:

- Missing required refs cannot return pass.
- Redacted replay must remain structurally complete with stable redacted refs.

## State Transitions

### CrawlRun

| From | Command | To | Required gates/events |
| --- | --- | --- | --- |
| queued | start_run | running | plan approved, RunPlanSnapshot created |
| running | pause_run | paused | command_committed, processing stops new work |
| paused | resume_run | running | policy still valid |
| running/paused | cancel_run | cancelled | in-flight work reconciled |
| running | complete_run | completed | required gates pass or explicit non-publication completion |
| running | fail_run | failed | failure record and replay-visible reason |

### RuntimeCompletionGate

| Gate | Pass condition | Failing outcomes |
| --- | --- | --- |
| objective | approved objective with scope/schema/evidence refs | fail, needs_review |
| plan | approved plan and immutable snapshot | fail, needs_review |
| source | adapter result succeeded/partial with policy refs | blocked, fail |
| normalization | normalized artifact and anchors exist | fail |
| extraction | candidate has schema and required anchors | fail, needs_review |
| evidence | coverage requirements pass | fail, needs_review |
| verification | accept decision or explicit review/conflict state | reject, conflict, needs_review |
| publication | accepted verification, policy allow, output manifest | fail, blocked |
| replay | required refs complete | fail, needs_review |

## Relationships

- `CrawlObjective` has many `CrawlPlan`.
- `CrawlPlan` has many `CrawlRun`.
- `CrawlRun` has one `RunPlanSnapshot` and many `RuntimeCompletionGate`.
- `CrawlRun` has many `SourceAdapterResult`, `RuntimeArtifactRef`, `NormalizedDocument`, `ExtractionCandidate`, `EvidencePacket`, `VerificationDecision`, and `PublishedOutput`.
- `PublishedOutput` has one `OutputManifest`.
- `ReplayBundleManifest` references all replay-critical runtime outputs.
- Agent recommendations may reference plan/candidate/verification/repair subjects but do not own durable mutations.
