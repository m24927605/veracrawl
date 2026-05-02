# Quickstart: VeraCrawl Production Persistence And Queue Runtime

Run persistence success fixtures:

```sh
for fixture in \
  persistence-transaction-success \
  idempotent-replay-success \
  queue-lease-recovery-success
do
  uv run --python python3.12 --extra dev veracrawl-persistence run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run negative persistence fixtures:

```sh
for fixture in \
  non-atomic-commit \
  idempotency-not-persisted \
  event-log-gap \
  outbox-dispatch-missing \
  artifact-index-missing \
  lease-heartbeat-missing
do
  uv run --python python3.12 --extra dev veracrawl-persistence run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run verification gates:

```sh
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
uv run --python python3.12 --extra dev veracrawl-contracts validate --format json
uv run --python python3.12 --extra dev ruff check src tests
uv run --python python3.12 --extra dev mypy src
uv run --python python3.12 --extra dev pytest tests
```
