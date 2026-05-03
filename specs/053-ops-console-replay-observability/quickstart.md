# Quickstart: Ops Console, Replay, And Observability Runtime

Run focused tests:

```sh
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_ops_replay_observability_contracts.py \
  tests/contract/test_ops_replay_observability_contract_registry.py \
  tests/unit/test_ops_replay_observability_runtime.py \
  tests/unit/test_ops_replay_observability_replay.py \
  tests/integration/test_ops_replay_observability_fixtures.py
```

Run fixture loop:

```sh
for fixture in tests/fixtures/ops-runtime-*; do
  uv run --python python3.12 --extra dev veracrawl-ops-runtime run \
    "$fixture" \
    --profile target \
    --telemetry-backend-ref telemetry-backend:target \
    --collector-handoff-ref collector-handoff:target \
    --out ".veracrawl-test-runs/$(basename "$fixture")"
done
```
