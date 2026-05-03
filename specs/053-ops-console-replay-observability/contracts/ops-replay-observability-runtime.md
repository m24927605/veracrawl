# Contract: Ops Replay Observability Runtime

## CLI

```text
veracrawl-ops-runtime run <fixture_dir> --profile target --out <output_dir>
```

The CLI loads `manifest.yaml`, validates `OpsReplayObservabilityFixtureManifest`,
runs the deterministic row 053 runtime, compares expected completion/status and
typed failure, then writes `run_report.json`.

## Runtime API

```python
run_ops_replay_observability_runtime(
    *,
    fixture_id: str,
    scenario: str,
    telemetry_backend_ref: str | None = None,
    collector_handoff_ref: str | None = None,
) -> OpsReplayObservabilityRuntimeResult
```

The result contains one `OpsReplayObservabilityRuntimeReport` and subordinate
runtime results for result publication/export, worker orchestration, ops console,
and observability when those dependencies are present.

## Commands

- `record_ops_replay_observability_runtime_report`
- `record_ops_replay_observability_fixture_manifest`

## Events

- `ops_replay_observability_runtime_reported`
- `ops_replay_observability_fixture_manifest_recorded`

## Fixture IDs

Success:

- `ops-runtime-review-replay-success`
- `ops-runtime-incident-recovery-success`
- `ops-runtime-cost-alert-success`

Negative:

- `ops-runtime-missing-publication`
- `ops-runtime-missing-worker-orchestration`
- `ops-runtime-missing-ops-console`
- `ops-runtime-missing-observability`
- `ops-runtime-stale-dashboard`
- `ops-runtime-unresolved-recovery`
- `ops-runtime-unsafe-operator-action`
- `ops-runtime-replay-mismatch`
