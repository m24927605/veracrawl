# Quickstart: Production Persistence Runtime Wiring

Run the success fixture:

```bash
uv run --python python3.12 --extra dev veracrawl-production-persistence run \
  tests/fixtures/production-persistence-wiring-success \
  --profile target \
  --out .veracrawl-test-runs/production-persistence-wiring-success
```

Run the duplicate replay fixture:

```bash
uv run --python python3.12 --extra dev veracrawl-production-persistence run \
  tests/fixtures/production-persistence-idempotent-replay \
  --profile target \
  --out .veracrawl-test-runs/production-persistence-idempotent-replay
```

Run focused tests:

```bash
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_production_persistence_runtime_contracts.py \
  tests/unit/test_production_persistence_runtime.py \
  tests/integration/test_production_persistence_runtime_fixtures.py
```

Run registry validation:

```bash
uv run --python python3.12 --extra dev veracrawl-contracts validate --format json
```
