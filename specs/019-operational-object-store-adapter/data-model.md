# Data Model: VeraCrawl Operational Object Store Adapter

## ObjectStoreAdapterSpec

Declares S3-compatible operational adapter kind, capability refs, bucket ref, namespace ref, content addressing support, digest verification support, lifecycle support, retention policy refs, privacy policy refs, and policy decision refs.

## ObjectStoreOperationRecord

Records put, duplicate put, get, head, list, and delete operations with artifact ref, object key ref, digest ref, size, etag, read result, duplicate ref, deletion marker, lifecycle state, retention policy, privacy policy, policy refs, failure refs, and recovery refs.

## ObjectStoreConformanceReport

Operational pass requires adapter, artifact, operation, digest, read, head, list, delete, lifecycle, retention, privacy, policy, and replay refs. No-runtime reports use `contract_only_refs` and `needs_review`.

## ObjectStoreFixtureManifest

Required fixtures:

- `s3-object-store-conformance-success`
- `s3-object-store-idempotency-success`
- `s3-object-store-delete-success`
- `s3-object-store-runtime-unavailable`
- `object-store-missing-digest`
- `object-store-missing-read-after-write`
- `object-store-missing-delete-marker`
