# Quickstart: Graph And Memory Production Runtime

Run focused checks:

```sh
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_graph_memory_production_contracts.py \
  tests/unit/test_graph_memory_production_runtime.py \
  tests/integration/test_graph_memory_production_fixtures.py
```

Run all row 051 fixtures:

```sh
tmpdir=$(mktemp -d)
for fixture in tests/fixtures/graph-memory-*; do
  uv run --python python3.12 --extra dev veracrawl-graph-memory-runtime run \
    "$fixture" \
    --profile target \
    --out "$tmpdir/$(basename "$fixture")"
done
```

Validate the registry:

```sh
uv run --python python3.12 --extra dev python -m veracrawl.cli.contracts validate --format json
```

Expected positive fixtures:

- `graph-memory-production-success`
- `graph-memory-frontier-priority-success`
- `graph-memory-repair-explanation-success`

Expected negative fixtures:

- `graph-memory-missing-live-normalization`
- `graph-memory-missing-live-evidence`
- `graph-memory-missing-multi-agent`
- `graph-memory-graph-as-evidence`
- `graph-memory-memory-as-evidence`
- `graph-memory-stale-memory`
- `graph-memory-missing-invalidation`
- `graph-memory-missing-frontier-explanation`
- `graph-memory-replay-mismatch`
