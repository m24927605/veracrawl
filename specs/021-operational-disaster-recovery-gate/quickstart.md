# Quickstart: Operational Disaster Recovery Gate

Run no-runtime and negative fixtures:

```sh
for fixture in \
  dr-restore-runtime-unavailable \
  dr-restore-missing-metadata \
  dr-restore-missing-artifact-reachability \
  dr-restore-missing-event-replay \
  dr-restore-missing-projection-rebuild \
  dr-restore-missing-export-reconciliation \
  dr-restore-unresolved-refs \
  dr-restore-data-loss \
  dr-restore-unsafe-recovery-without-approval
do
  uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 veracrawl-dr run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run live fixtures with explicit runtimes:

```sh
uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 veracrawl-dr run \
  tests/fixtures/dr-restore-success \
  --profile target \
  --postgres-dsn "$VERACRAWL_POSTGRES_DSN" \
  --redis-url "$VERACRAWL_REDIS_URL" \
  --s3-endpoint-url "$VERACRAWL_S3_ENDPOINT_URL" \
  --s3-bucket "$VERACRAWL_S3_BUCKET" \
  --s3-access-key-id "$VERACRAWL_S3_ACCESS_KEY_ID" \
  --s3-secret-access-key "$VERACRAWL_S3_SECRET_ACCESS_KEY" \
  --out .veracrawl-test-runs/dr-restore-success
```

Run the Docker-backed live integration gate:

```sh
VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 \
  pytest tests/integration/test_operational_disaster_recovery_live.py
```
