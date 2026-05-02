# Quickstart: VeraCrawl Operational Object Store Adapter

Run no-runtime guard fixture:

```sh
uv run --python python3.12 --extra dev --extra object-s3 veracrawl-object-store run \
  tests/fixtures/s3-object-store-runtime-unavailable \
  --profile target \
  --out .veracrawl-test-runs/s3-object-store-runtime-unavailable
```

Run negative fixtures:

```sh
for fixture in \
  object-store-missing-digest \
  object-store-missing-read-after-write \
  object-store-missing-delete-marker
do
  uv run --python python3.12 --extra dev --extra object-s3 veracrawl-object-store run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run live fixtures with an existing S3-compatible endpoint:

```sh
for fixture in \
  s3-object-store-conformance-success \
  s3-object-store-idempotency-success \
  s3-object-store-delete-success
do
  uv run --python python3.12 --extra dev --extra object-s3 veracrawl-object-store run \
    tests/fixtures/$fixture \
    --profile target \
    --endpoint-url "$VERACRAWL_S3_ENDPOINT_URL" \
    --bucket "$VERACRAWL_S3_BUCKET" \
    --access-key-id "$VERACRAWL_S3_ACCESS_KEY_ID" \
    --secret-access-key "$VERACRAWL_S3_SECRET_ACCESS_KEY" \
    --out .veracrawl-test-runs/$fixture
done
```

Run Docker-backed live integration tests:

```sh
VERACRAWL_S3_DOCKER=1 uv run --python python3.12 --extra dev --extra object-s3 \
  pytest tests/integration/test_s3_object_store_live.py
```

Run verification gates:

```sh
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
uv run --python python3.12 --extra dev --extra object-s3 veracrawl-contracts validate --format json
uv run --python python3.12 --extra dev --extra object-s3 ruff check src tests
uv run --python python3.12 --extra dev --extra object-s3 mypy src
uv run --python python3.12 --extra dev --extra object-s3 pytest tests
```
