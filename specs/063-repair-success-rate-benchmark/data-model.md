# Data Model: Repair Success Rate Benchmark

## RepairQualityThresholds

Defines `min_repair_success_rate`, `max_unsafe_bypass_rate`, and
`max_unresolved_critical_rate`.

## SeededRepairCase

Declares a failure family, repairability, criticality, expected outcome, input
artifact refs, before-evidence refs, policy refs, command/event/outbox refs,
oracle refs, and replay refs.

## RepairAttemptTrace

Captures one AI-assisted repair attempt with framework-neutral model call, agent
action, tool call, context bundle, owner-service command, policy, before/after
evidence, rollback, escalation, command/event/outbox, replay, cost, token, and
latency refs.

## RepairQualityReport

Aggregates seeded case refs and attempt refs into repair success rate, unsafe
bypass rate, unresolved critical repair rate, count metrics, cost/token/latency
metrics, diagnostics, and typed failure state.

## RepairQualityManifest

Declares fixture scenario, generated case counts, thresholds, expected result,
expected failure type, and required ref families.
