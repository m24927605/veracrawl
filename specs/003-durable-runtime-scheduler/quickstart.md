# Quickstart: Durable Runtime Persistence and Scheduler Foundation

This quickstart validates the deterministic durable runtime and scheduler foundation. It does not claim production persistence, distributed queueing, full browser crawling, graph/memory intelligence, export capability, or production scale readiness.

## Validate Registry And Contracts

```bash
uv run --python python3.12 --extra dev veracrawl-contracts validate --format json
uv run --python python3.12 --extra dev pytest tests/contract/test_durable_contract_registry.py
uv run --python python3.12 --extra dev pytest tests/contract/test_durable_ports_and_boundaries.py
uv run --python python3.12 --extra dev pytest tests/contract/test_scheduler_contracts.py
```

## Run Durable Success Fixture

```bash
uv run --python python3.12 --extra dev veracrawl-durable run \
  tests/fixtures/durable-runtime-success \
  --profile target \
  --out .veracrawl-test-runs/durable-runtime-success
```

Expected:

- durable command, event cursor, outbox, artifact, frontier item, lease, and recovery refs are present
- reloading from the deterministic durable backing store preserves refs
- recovery result is `pass`

## Run Durable Negative Fixtures

```bash
for fixture in \
  durable-duplicate-command \
  durable-event-gap \
  durable-pending-outbox \
  durable-stale-lease \
  durable-invalid-lease \
  durable-missing-artifact
do
  uv run --python python3.12 --extra dev veracrawl-durable run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Expected:

- duplicate command does not duplicate event/outbox records
- event gap, invalid lease, and missing artifact fail
- pending outbox and stale lease require review
- no negative fixture falsely reports production crawler completion

## Run Full Durable Scheduler Gate

```bash
uv run --python python3.12 --extra dev ruff check src tests
uv run --python python3.12 --extra dev mypy src
uv run --python python3.12 --extra dev pytest tests/contract tests/unit tests/integration
```

The local gate should complete within 30 seconds or emit a timing report explaining why deterministic fixture complexity, not architecture drift, caused the slower run.
