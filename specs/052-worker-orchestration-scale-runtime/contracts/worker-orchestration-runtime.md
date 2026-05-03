# Contract: Worker Orchestration Runtime

## CLI

```text
veracrawl-worker-orchestration run <fixture_dir> --profile target --out <output_dir>
```

Inputs:

- `fixture_dir/manifest.yaml`: JSON object validated as
  `WorkerOrchestrationFixtureManifest`.
- `--profile`: profile to validate, default `target`.
- `--out`: directory receiving `run_report.json`.

Output:

```json
{
  "ok": true,
  "fixture_id": "worker-orchestration-production-success",
  "completion_result": "pass",
  "operator_status": "worker_orchestration_completed"
}
```

## Runtime Function

```python
run_worker_orchestration_runtime(
    *,
    fixture_id: str,
    scenario: str,
    policy_decision_refs: list[Ref] | None = None,
) -> WorkerOrchestrationRuntimeResult
```

The result contains one `WorkerOrchestrationRuntimeReport` and subordinate
`ScaleHardeningResult` refs. It is deterministic and does not require concrete
database, queue, object store, browser, model, or agent framework clients.

## Commands And Events

Commands:

- `record_worker_orchestration_runtime_report`
- `record_worker_orchestration_fixture_manifest`

Events:

- `worker_orchestration_runtime_reported`
- `worker_orchestration_fixture_manifest_recorded`

Replay-critical refs:

- dependency report refs
- worker pool, queue item, lease, heartbeat, fencing, retry, dead-letter,
  backpressure, autoscaling, failure, and recovery refs
- command/event/outbox refs
- replay bundle refs
