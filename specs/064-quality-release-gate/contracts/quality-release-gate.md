# Contract: Cost Latency Stability Release Gate

## CLI

```text
veracrawl-quality-release-gate run tests/fixtures/<quality_release_fixture_id> --profile quality --out <run_dir>
```

The CLI writes:

- `quality_release_report.json`
- `quality_gate_refs.json`
- `stability_runs.json`
- `summary.json`

## Pass Criteria

- Six prior quality gate refs exist for rows 058-063.
- At least three stability runs exist.
- Total cost, p95 latency, throughput, retry rate, token count, model call count,
  and stability variance satisfy thresholds.
- Policy, command/event/outbox, SLO metric, audit, release decision, and replay
  refs exist.

## Negative Diagnostics

- `quality_release_missing_quality_gate_report`
- `quality_release_cost_budget_exceeded`
- `quality_release_latency_slo_violation`
- `quality_release_retry_rate_exceeded`
- `quality_release_stability_regression`
- `quality_release_insufficient_stability_runs`
- `quality_release_replay_gap`
- `quality_release_false_ready_status`
- `quality_release_missing_command_event_refs`
