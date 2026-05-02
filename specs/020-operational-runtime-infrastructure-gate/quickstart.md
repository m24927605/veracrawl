# Quickstart: Operational Runtime Infrastructure Gate

Run no-runtime and negative fixtures:

```sh
for fixture in \
  operational-infrastructure-runtime-unavailable \
  infrastructure-missing-persistence-refs \
  infrastructure-missing-queue-refs \
  infrastructure-missing-object-refs \
  infrastructure-missing-replay-refs
do
  uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 veracrawl-infrastructure run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run live fixtures with explicit runtimes:

```sh
for fixture in \
  operational-infrastructure-success \
  operational-infrastructure-idempotency-success
do
  uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 veracrawl-infrastructure run \
    tests/fixtures/$fixture \
    --profile target \
    --postgres-dsn "$VERACRAWL_POSTGRES_DSN" \
    --redis-url "$VERACRAWL_REDIS_URL" \
    --s3-endpoint-url "$VERACRAWL_S3_ENDPOINT_URL" \
    --s3-bucket "$VERACRAWL_S3_BUCKET" \
    --s3-access-key-id "$VERACRAWL_S3_ACCESS_KEY_ID" \
    --s3-secret-access-key "$VERACRAWL_S3_SECRET_ACCESS_KEY" \
    --out .veracrawl-test-runs/$fixture
done
```

Run the Docker-backed live integration gate:

```sh
VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 \
  pytest tests/integration/test_operational_infrastructure_live.py
```
