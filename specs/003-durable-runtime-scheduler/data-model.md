# Data Model: Durable Runtime Persistence and Scheduler Foundation

## UnitOfWorkRecord

- **Owner**: `runtime_events`
- **Fields**: `id`, `run_ref`, `status`, `command_record_refs`, `event_refs`, `outbox_refs`, `artifact_refs`, `committed_at_ref`, `recovery_report_refs`
- **Validation**: committed records require at least one command record or event ref; failed records require failure refs.

## DurableCommandRecord

- **Owner**: target aggregate owner service
- **Fields**: `id`, `command_ref`, `command_type`, `target_aggregate_type`, `target_aggregate_id`, `idempotency_key`, `command_result_ref`, `event_refs`, `outbox_refs`, `status`
- **Validation**: committed records require command result and event refs; duplicate records reference the original command result.
- **Identity**: `command_type + target_aggregate_type + target_aggregate_id + idempotency_key`

## OutboxRecord

- **Owner**: `runtime_events`
- **Fields**: `id`, `run_ref`, `command_result_ref`, `event_ref`, `dispatch_topic`, `payload_ref`, `status`, `attempt_count`, `last_error_ref`, `idempotency_key`
- **Validation**: dispatched records require `dispatched_at_ref`; failed records require `last_error_ref`.
- **Transitions**: pending -> dispatched; pending -> failed; failed -> pending.

## EventCursorRecord

- **Owner**: `runtime_events`
- **Fields**: `id`, `run_ref`, `from_sequence`, `to_sequence`, `event_refs`, `contiguous`
- **Validation**: contiguous cursors require sequence coverage for every integer in the range.

## FrontierItem

- **Owner**: `scheduler`
- **Fields**: `id`, `run_ref`, `source_ref`, `priority`, `status`, `attempt_count`, `max_attempts`, `policy_decision_refs`, `lease_ref`, `last_error_ref`
- **Validation**: leased items require a lease ref; completed items require result refs; dead-lettered items require failure refs.
- **Transitions**: queued -> leased -> completed; leased -> queued; leased -> retrying -> queued; retrying -> dead_lettered.

## QueueLease

- **Owner**: `scheduler`
- **Fields**: `id`, `frontier_item_ref`, `run_ref`, `lease_token_ref`, `holder_ref`, `status`, `expires_at_ref`, `heartbeat_ref`, `completed_at_ref`, `released_at_ref`
- **Validation**: active leases require token and expiry refs; completed leases require completion refs; expired leases require expiry reason refs.
- **Transitions**: active -> completed; active -> released; active -> expired; expired -> replaced.

## SchedulerRecoveryReport

- **Owner**: `scheduler`
- **Fields**: `id`, `run_ref`, `expired_lease_refs`, `retry_frontier_item_refs`, `dead_letter_refs`, `invalid_lease_refs`, `operator_status`, `completeness_result`
- **Validation**: pass requires no expired, invalid, or dead-letter refs.

## DurableReplayRecoveryReport

- **Owner**: `review_replay`
- **Fields**: `id`, `run_ref`, `command_record_refs`, `event_cursor_refs`, `outbox_refs`, `artifact_refs`, `lease_refs`, `missing_ref_fields`, `gap_report_refs`, `completeness_result`
- **Validation**: pass requires no missing refs and no gap refs. Fail blocks completion/publication.

## DurableFixtureManifest

- **Owner**: `tests`
- **Fields**: `id`, `scenario`, `profile_refs`, `expected_completion_result`, `expected_operator_status`, `expected_publication`, `required_ref_types`
- **Validation**: negative fixtures must expect no publication and must identify a blocking ref type.
