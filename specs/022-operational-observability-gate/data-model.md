# Data Model: Operational Observability Gate

## ObservabilitySignal

Canonical platform signal linking operational context to owner service, severity, source capability, policy, redaction, and replay refs.

Required fields:

- `id`
- `signal_type`
- `owner_service`
- `severity`
- `run_ref`
- `source_ref`
- `metric_refs`
- `trace_refs`
- `alert_refs`
- `policy_decision_refs`
- `redaction_map_refs`
- `replay_bundle_ref`

Validation rules:

- non-informational severities require metric, trace, alert, policy, redaction, and replay refs
- signal payloads must not contain raw secret-like values

## MetricSample

Measurement record for operational SLOs and cost/quality signals.

Required fields:

- `id`
- `metric_name`
- `metric_kind`
- `value`
- `unit`
- `run_ref`
- `owner_service`
- `timestamp_ref`
- `threshold_ref`
- `policy_decision_refs`
- `trace_refs`

Validation rules:

- values must be numeric
- threshold and policy refs are required for alert-driving metrics
- queue lag, retry rate, projection lag, browser minutes, token spend, object-store growth, export lag, error rate, DR duration, and quality/cost SLOs are supported target names

## TraceSpan

Canonical execution span for command, event, adapter, agent, tool, queue, artifact, projection, export, recovery, or observability work.

Required fields:

- `id`
- `span_name`
- `span_kind`
- `run_ref`
- `parent_span_ref`
- `command_ref`
- `event_ref`
- `owner_service`
- `status`
- `duration_ms`
- `redacted_attribute_refs`
- `policy_decision_refs`

Validation rules:

- failed spans require failure refs
- attributes must be redacted by reference
- command/event spans require command or event refs

## AlertRecord

Policy-visible alert tied to metrics, traces, failures, DR status, severity, blast radius, and runbook actions.

Required fields:

- `id`
- `alert_type`
- `severity`
- `status`
- `run_ref`
- `metric_refs`
- `trace_refs`
- `failure_record_refs`
- `dr_restore_report_refs`
- `runbook_action_refs`
- `policy_decision_refs`
- `replay_bundle_ref`

Validation rules:

- open or firing alerts require failure refs and runbook refs
- recovery-related alerts require DR refs
- resolved alerts require resolution refs

## RunbookAction

Replayable operator or automated action recommendation/execution record.

Required fields:

- `id`
- `action_type`
- `status`
- `run_ref`
- `alert_ref`
- `failure_record_refs`
- `recovery_action_refs`
- `approval_decision_refs`
- `policy_decision_refs`
- `command_refs`
- `event_refs`
- `replay_bundle_ref`

Validation rules:

- side-effecting actions require approval refs
- completed actions require command, event, policy, and replay refs
- recommended actions require a failure, alert, or DR ref

## ObservabilityReport

Gate result tying all observability signals into one pass/fail/needs-review record.

Pass requires:

- signal refs
- metric sample refs
- trace span refs
- alert record refs
- runbook action refs
- quality report refs
- cost metric refs
- dashboard snapshot refs
- projection watermark refs
- failure record refs
- recovery action refs
- DR restore report refs
- policy refs
- command refs
- event cursor refs
- outbox refs
- redaction map refs
- collector handoff refs
- telemetry backend refs
- replay bundle ref
- no missing required refs
- no unredacted sensitive fields
- no unsafe runbook actions without approval

Needs-review requires:

- contract-only refs that identify missing telemetry runtime, collector handoff, or backend refs

Fail requires:

- failure refs, missing required refs, stale dashboard watermarks, missing redaction refs, missing replay refs, unsafe runbook without approval, or secret-like payload diagnostics

## ObservabilityFixtureManifest

Declares fixture scenario, expected completion result, expected operator status, and optional expected failure type.

Scenarios:

- `observability-success`
- `observability-runtime-unavailable`
- `observability-data-surface-only`
- `observability-missing-metrics`
- `observability-missing-traces`
- `observability-missing-alerts`
- `observability-missing-runbook`
- `observability-stale-dashboard-watermark`
- `observability-missing-dr-refs`
- `observability-missing-redaction`
- `observability-missing-replay`
- `observability-secret-leak`
- `observability-unsafe-runbook-without-approval`

## FailureRecord

Uses `observability_gap`, `unsafe_runbook_without_review`, or `redaction_violation` failure types for deterministic observability negative cases.

## RecoveryAction

Uses `restore_observability_signal`, `refresh_dashboard_projection`, `redact_sensitive_context`, `request_review`, or `run_observability_runbook` action types depending on failure class. Side-effecting actions require policy and approval refs.
