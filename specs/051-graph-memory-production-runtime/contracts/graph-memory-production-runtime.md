# Contract: Graph Memory Production Runtime

## CLI

```text
veracrawl-graph-memory-runtime run <fixture_dir> --profile target --out <output_dir>
```

Inputs:

- `fixture_dir/manifest.yaml`: JSON object validated as
  `GraphMemoryProductionFixtureManifest`.
- `--profile`: profile to validate, default `target`.
- `--out`: directory receiving `run_report.json`.

Output:

```json
{
  "ok": true,
  "fixture_id": "graph-memory-production-success",
  "completion_result": "pass",
  "operator_status": "graph_memory_production_completed"
}
```

Failure output:

```json
{
  "ok": false,
  "error": "fixture graph-memory-replay-mismatch completion mismatch"
}
```

## Runtime Function

```python
run_graph_memory_production_runtime(
    *,
    fixture_id: str,
    scenario: str,
    policy_decision_refs: list[Ref] | None = None,
) -> GraphMemoryProductionRuntimeResult
```

The result contains one `GraphMemoryProductionRuntimeReport`. Passing reports
also include subordinate deterministic reports from graph frontier/review,
temporal KG, memory kernel, and multi-agent repair through refs.

## Commands And Events

Commands:

- `record_graph_memory_production_runtime_report`
- `record_graph_memory_production_fixture_manifest`

Events:

- `graph_memory_production_runtime_reported`
- `graph_memory_production_fixture_manifest_recorded`

Replay-critical refs:

- dependency report refs
- graph projection and watermark refs
- memory event, retrieval, freshness, and invalidation refs
- source evidence and verification refs
- policy, command, event cursor, outbox, and replay bundle refs
