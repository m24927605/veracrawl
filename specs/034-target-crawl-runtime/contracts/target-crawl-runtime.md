# Contract: VeraCrawl Target Crawl Runtime

## Owner Service Boundary

- `control`: objective, plan, run status, aggregate target runtime report
- `scheduler`: frontier scheduling and lease refs
- `fetch`: source observations and source adapter results
- `normalize` and `extract`: normalized observations and extraction results
- `evidence` and `verify`: evidence packets and verification decisions
- `graph`: graph projection refs
- `agents`: framework-neutral recommendation refs and traces
- `publish` and `export`: output manifests and export receipts
- `review_replay`: replay bundle, replay audit, review diagnostics
- `policy`: source, browser, credential, prompt-injection, tool-call, publication, export, retention, and replay decisions
- `ops`: operator-visible reports and recovery actions
- `tests`: fixture manifests and oracle refs

## Contracts

### TargetCrawlPatternRecord

Contract model: `veracrawl.contracts.target_runtime.TargetCrawlPatternRecord`

Required for pass:

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

### TargetAIRecommendationRecord

Contract model: `veracrawl.contracts.target_runtime.TargetAIRecommendationRecord`

Required for accepted recommendations:

- `policy_decision_refs`
- `tool_call_refs`
- `trace_refs`
- no `framework_native_state_refs`

Required for blocked recommendations:

- `blocked_action_refs`
- `policy_decision_refs`

### TargetRuntimeReport

Contract model: `veracrawl.contracts.target_runtime.TargetRuntimeReport`

Required for complete:

- at least seven `covered_patterns`
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
- `privacy_lifecycle_refs`
- `replay_bundle_ref`
- no `failure_type`
- no `missing_ref_fields`

### TargetRuntimeFixtureManifest

Contract model: `veracrawl.contracts.target_runtime.TargetRuntimeFixtureManifest`

Required:

- `profile_refs` includes `target`
- negative fixtures declare `expected_failure_type`
- complete fixtures expect at least seven website patterns

## Commands

- `execute_target_crawl`
- `record_target_pattern_result`
- `record_target_ai_recommendation`
- `complete_target_runtime_report`

## Events

- `target_crawl_executed`
- `target_pattern_result_recorded`
- `target_ai_recommendation_recorded`
- `target_runtime_report_completed`

## Fixture Scenarios

- `target-runtime-success`
- `target-runtime-drift-repair`
- `target-runtime-needs-review`
- `target-runtime-policy-denied`
- `target-runtime-prompt-injection`
- `target-runtime-missing-evidence`
- `target-runtime-replay-mismatch`
- `target-runtime-partial-export`
- `target-runtime-false-complete`

## Replay Requirements

Every report must expose:

- objective and plan refs
- command result refs
- event cursor refs
- outbox refs
- policy decision refs
- source observation refs through pattern records
- artifact refs
- AI trace refs
- graph refs
- output manifest refs
- export receipt refs
- privacy lifecycle refs
- replay bundle ref or missing replay diagnostics

## Safety Requirements

The runtime must fail or block before completion for:

- out-of-scope source
- robots/terms denial
- credential use without approval
- browser action without approval
- unsafe AI tool call
- prompt-injection taint crossing trusted context
- missing replay refs
- missing evidence refs
- partial export mislabeled complete
- false complete or degraded operational claim
