# Data Model: Production Persistence Runtime Wiring

## ProductionPersistenceRuntimeReport

- `id`
- `fixture_id`
- `run_ref`
- `project_ref`
- `site_scope_ref`
- `objective_ref`
- `plan_ref`
- `run_control_report_ref`
- `status`
- `completion_result`
- `operator_status`
- `adapter_ref`
- `transaction_ref`
- `canonical_state_refs`
- `run_control_command_result_refs`
- `persistence_command_record_refs`
- `idempotency_record_refs`
- `event_refs`
- `event_cursor_ref`
- `outbox_refs`
- `artifact_refs`
- `queue_operation_refs`
- `lease_refs`
- `failure_record_refs`
- `recovery_action_refs`
- `policy_decision_refs`
- `replay_bundle_ref`
- `missing_ref_fields`
- `failure_type`
- `duplicate_deduped`
- `reloaded`
- `diagnostics`

Passing reports require canonical state, adapter, transaction, command,
idempotency, event cursor, outbox, artifact, queue, lease, policy, and replay
refs. Non-pass reports require failure or missing-ref diagnostics.

## ProductionPersistenceFixtureManifest

- `id`
- `scenario`
- `profile_refs`
- `expected_completion_result`
- `expected_operator_status`
- `expected_failure_type`
- `negative_case`
- `required_ref_types`

The fixture manifest declares exact pass/fail expectations for the
`veracrawl-production-persistence` runner.

## Canonical Document Collections

The runtime persists the following typed records through canonical document
ports:

- `ProductionProject`
- `ProductionSiteScope`
- `CrawlObjective`
- `CrawlPlan`
- `RunPlanSnapshot`
- `CrawlRun`
- `RunBudget`
- `RunPolicySnapshot`
- `RunApprovalRecord`
- `PolicyDecision`
- `RunLifecycleRecord`
- `ProductionRunControlReport`

## Persistence Side Effects

- `PersistenceTransactionRecord`
- `DurableCommandRecord`
- `IdempotencyPersistenceRecord`
- `CrawlRunEvent`
- `EventCursorRecord`
- `OutboxRecord`
- `PersistentQueueOperationRecord`
- `ShardLease`
- `RetryDeadLetterRecord`
- artifact index refs
- replay bundle ref
