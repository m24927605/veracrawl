# Operational Object Store Adapter Boundary

- Core packages must not import `boto3`, `botocore`, S3 clients, cloud SDKs, or `veracrawl.adapters`.
- S3-compatible client imports are allowed only inside `veracrawl.adapters.object_stores.s3`.
- `veracrawl-object-store` must load concrete adapters dynamically.
- Deterministic fixture artifact storage can only prove fixture behavior; operational `pass` requires live object store execution.
- Missing live endpoint/runtime must report `needs_review`, not pass.
