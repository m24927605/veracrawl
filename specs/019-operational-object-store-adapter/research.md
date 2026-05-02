# Research: VeraCrawl Operational Object Store Adapter

## Decision: S3-compatible adapter boundary

The operational object store uses an optional `object-s3` extra with `boto3`/`botocore`. Core code never imports these packages; adapter code dynamic-imports them inside `veracrawl.adapters.object_stores.s3`.

## Decision: MinIO live gate

Operational pass requires a live S3-compatible endpoint. Tests can use `VERACRAWL_S3_*` environment variables or `VERACRAWL_S3_DOCKER=1` to provision MinIO. Without a live runtime, the no-runtime fixture returns `needs_review`; pass is forbidden.

## Decision: Digest and lifecycle refs are mandatory

Writes store VeraCrawl artifact metadata as stable S3 object metadata. Read/head validation checks content digest; delete emits a deletion marker ref and lifecycle ref. This keeps object storage replayable and prevents raw SDK state from becoming canonical state.

## Rejected: deterministic fixture store as operational pass

The in-memory fixture artifact store is useful for deterministic runtime tests, but it is not a live object store. It cannot satisfy operational object store conformance.
