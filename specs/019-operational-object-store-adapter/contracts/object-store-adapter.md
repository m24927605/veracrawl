# Operational Object Store Adapter Contracts

## Adapter

- `veracrawl.adapters.object_stores.s3.S3ObjectStoreAdapter`

## Operational Kind

- `s3_compatible`

## Required Fixtures

- `s3-object-store-conformance-success`
- `s3-object-store-idempotency-success`
- `s3-object-store-delete-success`
- `s3-object-store-runtime-unavailable`
- `object-store-missing-digest`
- `object-store-missing-read-after-write`
- `object-store-missing-delete-marker`

## CLI

- `veracrawl-object-store run ... --endpoint-url <url> --bucket <bucket> --access-key-id <key> --secret-access-key <secret>` executes operational S3-compatible fixtures.
- Runtime-unavailable and negative fixtures do not require live credentials.
