# Contract: Source Acquisition

Source acquisition starts from a scheduler frontier item and queue lease. It produces:

- `FetchAttempt`
- `FetchResult`
- `PageSnapshot` or `DocumentArtifact`
- `RuntimeArtifactRef`
- `SourceAdapterResult`
- `SourceAcquisitionReport`

Every successful acquisition must include raw artifact refs and stable content digests. Missing artifacts fail replay recovery.

## Success Preconditions

- source policy decision is allow
- lease token is valid
- adapter result type is natural for the adapter family
- raw artifact ref exists
- durable command, event cursor, outbox, and recovery refs exist

## Failure Preconditions

Failure reports are required for:

- blocked source
- rate-limited source
- malformed response
- adapter result mismatch
- retry exhausted
- missing raw artifact
