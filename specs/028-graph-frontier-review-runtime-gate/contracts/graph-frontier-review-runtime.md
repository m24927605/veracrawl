# Contract: Graph Frontier Review Runtime Gate

## CLI

```text
veracrawl-graph-frontier-review run tests/fixtures/<fixture_id> --profile target --out .veracrawl-test-runs/<fixture_id>
```

## Required Fixtures

- `graph-frontier-review-success`
- `graph-frontier-review-runtime-unavailable`
- `graph-frontier-review-signal-as-evidence`
- `graph-frontier-review-missing-source-graph`
- `graph-frontier-review-missing-explanation`
- `graph-frontier-review-unauthorized-frontier-mutation`
- `graph-frontier-review-missing-review-route`
- `graph-frontier-review-missing-replay`
- `graph-frontier-review-unsupported-signal`

## Boundary

- Graph signals may influence frontier and review decisions.
- Graph signals must not satisfy source evidence, verification, publication, or output manifest requirements.
- Pass requires command, event cursor, outbox, policy, explanation, source graph, and replay refs.
