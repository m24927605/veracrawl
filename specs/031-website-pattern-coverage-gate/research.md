# Research: Target Website Pattern Coverage Gate

## Decision: Website Pattern Coverage Is A Target Benchmark Gate

Each target website pattern must prove source adapter, site model/page type,
source evidence, output/evidence, policy, artifact oracle, and replay refs before
target website pattern coverage can pass.

**Rationale**: Target acceptance requires every website pattern to have a
deterministic benchmark fixture and pass/fail oracle.

## Decision: Single-Site And Scaffold Claims Fail

Coverage records cannot claim target completeness when they are tied to one
specific website, one selector set, one pattern demo, or manifest-only scaffolds.

**Rationale**: VeraCrawl must remain a general-purpose crawler; target pattern
coverage must prove reusable crawler capabilities, not a narrow scraper path.

## Decision: Pattern-Specific Refs Are Explicit

Feeds require freshness/delta refs; listing/detail requires pagination,
deduplication, and canonical refs; search/forms require bounded policy refs;
JavaScript requires browser artifacts; authenticated sources require credential
audit/redaction refs; APIs require payload provenance; documents require
document artifacts and anchor maps; multilingual pages require language metadata;
drifted sites require repair/review refs; high-volume sites require queue,
backpressure, retry, dedup, and fairness refs.

**Rationale**: Generic pattern presence is not strong enough for target website
pattern readiness.

## Decision: Runtime Remains Dependency-Neutral

The gate proves benchmark readiness through deterministic refs. Production
browser fleets, live external sites, concrete HTTP clients, model calls, and
agent framework runtimes remain outside this slice.

**Rationale**: This keeps cohesion high and avoids coupling target coverage to
concrete runtime infrastructure.
