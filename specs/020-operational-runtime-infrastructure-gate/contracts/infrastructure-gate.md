# Contract: Operational Runtime Infrastructure Gate

## CLI

```text
veracrawl-infrastructure run tests/fixtures/<fixture_id> --profile target --out .veracrawl-test-runs/<fixture_id>
```

Live args:

- `--postgres-dsn` or `VERACRAWL_POSTGRES_DSN`
- `--redis-url` or `VERACRAWL_REDIS_URL`
- `--s3-endpoint-url` or `VERACRAWL_S3_ENDPOINT_URL`
- `--s3-bucket` or `VERACRAWL_S3_BUCKET`
- `--s3-access-key-id` or `VERACRAWL_S3_ACCESS_KEY_ID`
- `--s3-secret-access-key` or `VERACRAWL_S3_SECRET_ACCESS_KEY`

## Pass Contract

A passing report must include live refs from:

- Postgres persistence adapter conformance
- Redis/Valkey queue broker conformance
- S3-compatible object store conformance

The report must fail if one adapter family is missing or contract-only.

## No-runtime Contract

`operational-infrastructure-runtime-unavailable` returns `needs_review` and must include contract-only refs for Postgres, Redis/Valkey, and S3-compatible object store runtimes.

## Negative Contract

Negative fixtures must fail deterministically:

- missing persistence refs
- missing queue refs
- missing object refs
- missing replay refs
