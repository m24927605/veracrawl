# Contract: Failure And Policy Gates

Source policy decisions include:

- source scope
- robots/terms/customer authorization
- credential scope
- rate limit
- retry budget

Non-allow decisions must not produce accepted raw artifacts.

## Typed Outcomes

- `source_blocked`
- `source_rate_limited`
- `adapter_mismatch`
- `malformed_response`
- `retry_exhausted`
- `missing_raw_artifact`

Each outcome requires a `SourceFailureReport` and operator-visible diagnostics.
