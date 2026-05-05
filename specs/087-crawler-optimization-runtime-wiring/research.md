# Research: Crawler Optimization Runtime Wiring

## Decision: Add Runtime Wiring Contracts Instead Of Reusing Benchmark Result Types

**Rationale**: Benchmark result dataclasses are useful for gate execution but
are not owner-service decisions. Runtime flows need typed, replayable decisions
with policy status and lower refs.

**Alternatives considered**:

- Reuse `CrawlerOptimizationBenchmarkResult`: rejected because it couples
  runtime consumers to benchmark orchestration.
- Add untyped dictionaries: rejected because replay and registry validation need
  JSON schema-bearing contracts.

## Decision: Keep Runtime Service Adapter-Free

**Rationale**: Core runtime wiring must not depend on model SDKs, browser
engines, queue clients, storage clients, or framework-native agent state. The
service consumes refs and deterministic signal values.

**Alternatives considered**:

- Call source adapters from optimization runtime: rejected because fetch/browser
  owner services already own acquisition and policy preflight.
- Import benchmark helpers directly: rejected because production runtime should
  not depend on fixture-only modules.

## Decision: Use Deterministic Fixture Services First

**Rationale**: The repo already validates production spine changes through
deterministic fixtures before live corpus evidence. This keeps runtime wiring
testable without network access and avoids unsafe source access.

**Alternatives considered**:

- Start with live web integration: rejected because policy, robots, auth, and
  replay paths must be validated before live claims.
- Add learning-to-rank: rejected because spec 085 keeps heuristic ranking active
  until labels and privacy readiness exist.

## Decision: Runtime Aggregation Composes Lower Decisions

**Rationale**: Ops reports must prove that frontier, DOM/extraction, dedupe,
ranking, and replay refs are present. Aggregation should fail on missing lower
refs rather than claiming success from aggregate strings.

**Alternatives considered**:

- Allow aggregate-only success: rejected as a false-ready risk.
- Treat metric calculation as publication verification: rejected because ranking
  and optimization scores are advisory quality signals, not source evidence.
