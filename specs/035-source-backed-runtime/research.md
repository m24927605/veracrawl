# Research: VeraCrawl Source-Backed Target Runtime

## Decision: Use Local Corpus Files As The First Source-Backed Runtime

**Rationale**: Local corpus files are deterministic, safe, and replayable while still forcing the runtime to derive outputs from real content instead of synthetic refs.

**Alternatives considered**:

- Live Internet crawl: rejected for this phase because acceptance must be deterministic and policy-safe.
- Synthetic refs only: rejected because 034 already covers that and does not parse source content.

## Decision: Use Generic Descriptor Matching

**Rationale**: Corpus entries declare expected fields and evidence markers. The runner searches content generically and computes content hashes. This avoids hidden single-site scraper modules while proving source-backed extraction.

**Alternatives considered**:

- Site-specific parser functions: rejected by general-purpose crawler constraint.
- Full browser rendering: rejected for this phase; browser runtime remains a separate adapter gate.

## Decision: Extend Existing Target Runtime Contracts

**Rationale**: Source-backed execution is a target runtime mode. Extending `TargetRuntimeFixtureManifest` and adding source corpus contracts keeps compatibility with 034 fixtures and avoids a second CLI.

**Alternatives considered**:

- New CLI: rejected because it would duplicate fixture validation.
- Separate runtime package: rejected because source-backed behavior should compose into target runtime.
