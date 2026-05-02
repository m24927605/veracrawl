# Research: Source Adapter and Fetch Runtime

## Decision: Deterministic source adapters for source-family semantics

**Rationale**: The feature must prove source acquisition contracts without adding production network dependencies. Deterministic adapters can represent HTTP, sitemap, RSS, API-like, and document-source semantics while staying replaceable.

**Alternatives considered**:

- Production HTTP client now: rejected because this slice defines runtime contracts and policy/replay behavior before production adapter hardening.
- Single fixture adapter only: rejected because it would not prove natural result type semantics across source families.

## Decision: Raw artifacts are canonical refs, not adapter-native payloads

**Rationale**: Replay and downstream normalization need stable artifact refs, digests, lifecycle refs, and retention refs. Adapter-native payload objects are not canonical.

**Alternatives considered**:

- Store raw content directly in source result: rejected because it weakens artifact lifecycle and privacy controls.
- Skip artifact persistence for non-fetch sources: rejected because document and API sources also need replay lineage.

## Decision: Source acquisition report joins scheduler, source, durable, policy, and replay refs

**Rationale**: Operators need one typed report that proves lease, command, event, outbox, policy, artifact, and source result refs are present.

**Alternatives considered**:

- Use only `SourceAdapterResult`: rejected because it does not carry all durable scheduler and recovery refs.

## Decision: Negative outcomes are typed and non-successful

**Rationale**: Blocked, rate-limited, malformed, mismatched, retry-exhausted, and missing-artifact cases must not look like accepted source results.

**Alternatives considered**:

- Best-effort warnings: rejected because warnings can allow unsafe source acquisition to proceed.
