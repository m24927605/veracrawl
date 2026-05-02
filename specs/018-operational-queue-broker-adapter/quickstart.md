# Quickstart: VeraCrawl Operational Queue Broker Adapter

Run no-runtime guard fixture:

```sh
uv run --python python3.12 --extra dev --extra queue-redis veracrawl-queue-broker run \
  tests/fixtures/redis-broker-runtime-unavailable \
  --profile target \
  --out .veracrawl-test-runs/redis-broker-runtime-unavailable
```

Run negative broker-contract fixtures:

```sh
for fixture in \
  broker-missing-fencing-token \
  broker-missing-heartbeat \
  broker-missing-dead-letter
do
  uv run --python python3.12 --extra dev --extra queue-redis veracrawl-queue-broker run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run live fixtures with an existing Redis URL:

```sh
for fixture in \
  redis-broker-conformance-success \
  redis-broker-idempotency-success \
  redis-broker-dead-letter-success
do
  uv run --python python3.12 --extra dev --extra queue-redis veracrawl-queue-broker run \
    tests/fixtures/$fixture \
    --profile target \
    --redis-url "$VERACRAWL_REDIS_URL" \
    --out .veracrawl-test-runs/$fixture
done
```

Run Docker-backed live integration tests:

```sh
VERACRAWL_REDIS_DOCKER=1 uv run --python python3.12 --extra dev --extra queue-redis \
  pytest tests/integration/test_redis_queue_broker_live.py
```

Run verification gates:

```sh
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
uv run --python python3.12 --extra dev --extra queue-redis veracrawl-contracts validate --format json
uv run --python python3.12 --extra dev --extra queue-redis ruff check src tests
uv run --python python3.12 --extra dev --extra queue-redis mypy src
uv run --python python3.12 --extra dev --extra queue-redis pytest tests
```
