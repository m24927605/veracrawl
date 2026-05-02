# Contract: Operational Disaster Recovery Gate

## CLI

```text
veracrawl-dr run tests/fixtures/<fixture_id> --profile target --out .veracrawl-test-runs/<fixture_id>
```

Live args:

- `--postgres-dsn` or `VERACRAWL_POSTGRES_DSN`
- `--redis-url` or `VERACRAWL_REDIS_URL`
- `--s3-endpoint-url` or `VERACRAWL_S3_ENDPOINT_URL`
- `--s3-bucket` or `VERACRAWL_S3_BUCKET`
- `--s3-access-key-id` or `VERACRAWL_S3_ACCESS_KEY_ID`
- `--s3-secret-access-key` or `VERACRAWL_S3_SECRET_ACCESS_KEY`

## Pass Contract

A passing DR report must include:

- DR restore plan and run refs
- restore point and backup manifest refs
- metadata restore refs from live persistence-backed state
- artifact reachability refs from live object storage
- event replay refs from live persistence/event refs
- queue recovery refs from live broker or persisted queue operation refs
- projection rebuild refs
- export reconciliation refs
- failure and recovery action refs proving recoverability paths are visible
- policy, command, event cursor, outbox, validation, and replay refs
- no unresolved refs
- `data_loss_detected = false`

## No-runtime Contract

`dr-restore-runtime-unavailable` returns `needs_review` and must include contract-only refs for the missing live operational substrate.

## Negative Contract

Negative fixtures must fail deterministically:

- missing metadata restore refs
- missing artifact reachability refs
- missing event replay refs
- missing projection rebuild refs
- missing export reconciliation refs
- unresolved refs
- data loss detected
- unsafe recovery without approval refs

## Boundary Contract

Core DR code must not statically import concrete adapter packages or SDKs, including `psycopg`, `redis`, `boto3`, `botocore`, cloud SDKs, browser libraries, model SDKs, agent frameworks, or site-specific scraper modules.
