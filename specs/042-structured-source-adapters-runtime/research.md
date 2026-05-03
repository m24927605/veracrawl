# Research: Structured Source Adapters Runtime

## Decision: Core Aggregates Records; Adapters Parse Sources

The core `fetch.structured_source` runtime accepts typed structured adapter
records and builds the aggregate pass/fail report. The concrete fixture adapter
module parses sitemap, RSS, JSON, document, and file-import fixtures.

**Rationale**: This keeps core independent from filesystem/parser details while
still proving adapter-owned structured source semantics through real fixture
content.

## Decision: Reuse Source Acquisition Runtime

Structured fixture adapters execute through `execute_source_acquisition` so each
adapter family produces source adapter result, fetch attempt/result, command,
event cursor, outbox, policy, artifact, and replay-visible refs.

**Rationale**: 042 should extend the source acquisition spine rather than create
a separate path.

## Rejected Alternative: Direct Core Fixture Parsing

Rejected because direct core parsing would bypass source adapter ownership and
would make structured source support look like a single fixture reader instead
of a replaceable adapter runtime.
