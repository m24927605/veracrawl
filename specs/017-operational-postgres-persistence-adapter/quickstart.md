# Quickstart: VeraCrawl Operational Postgres Persistence Adapter

Run no-runtime guard fixture:

```sh
uv run --python python3.12 --extra dev --extra postgres veracrawl-persistence-adapter run \
  tests/fixtures/postgres-runtime-unavailable \
  --profile target \
  --out .veracrawl-test-runs/postgres-runtime-unavailable
```

Run live fixtures with an existing DSN:

```sh
for fixture in \
  postgres-adapter-conformance-success \
  postgres-reopen-idempotency-success \
  postgres-queue-recovery-success
do
  uv run --python python3.12 --extra dev --extra postgres veracrawl-persistence-adapter run \
    tests/fixtures/$fixture \
    --profile target \
    --postgres-dsn "$VERACRAWL_POSTGRES_DSN" \
    --out .veracrawl-test-runs/$fixture
done
```

Run Docker-backed live integration tests:

```sh
VERACRAWL_POSTGRES_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres \
  pytest tests/integration/test_postgres_persistence_adapter_live.py
```

Run verification gates:

```sh
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
uv run --python python3.12 --extra dev --extra postgres veracrawl-contracts validate --format json
uv run --python python3.12 --extra dev --extra postgres ruff check src tests
uv run --python python3.12 --extra dev --extra postgres mypy src
uv run --python python3.12 --extra dev --extra postgres pytest tests
```
