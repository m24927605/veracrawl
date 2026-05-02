# Quickstart: VeraCrawl Concrete Persistence Adapter Family

Run adapter fixtures:

```sh
for fixture in \
  sqlite-adapter-conformance-success \
  sqlite-reopen-idempotency-success \
  sqlite-queue-recovery-success \
  postgres-adapter-contract-harness \
  adapter-missing-capability \
  sqlite-idempotency-gap \
  sqlite-event-cursor-gap \
  sqlite-outbox-gap \
  sqlite-migration-missing
do
  uv run --python python3.12 --extra dev veracrawl-persistence-adapter run \
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
