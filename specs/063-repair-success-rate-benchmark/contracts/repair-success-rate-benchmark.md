# Contract: Repair Success Rate Benchmark

## CLI

```text
veracrawl-repair-quality-benchmark run tests/fixtures/<repair_quality_fixture_id> --profile quality --out <run_dir>
```

The CLI writes:

- `repair_quality_report.json`
- `seeded_repair_cases.json`
- `repair_attempts.json`
- `summary.json`

## Pass Criteria

- At least 30 seeded cases run across crawl planning, fetch/browser,
  normalization, extraction, verification, publication, drift, and replay
  failure families.
- Repairable-case success rate is >= 0.80.
- Unsafe bypass rate is 0.
- Unresolved critical repair rate is 0.
- AI-assisted attempts include model/agent/tool/context traces through
  VeraCrawl framework-neutral abstractions.
- Repairs include owner-service command refs, before/after evidence refs,
  rollback or escalation refs where applicable, policy refs,
  command/event/outbox refs, and replay refs.

## Negative Diagnostics

- `repair_success_rate_below_threshold`
- `repair_unsafe_bypass_detected`
- `repair_owner_service_bypass`
- `repair_model_only_evidence`
- `repair_missing_trace_refs`
- `repair_missing_rollback_refs`
- `repair_unresolved_critical_repair`
- `repair_missing_replay_refs`
