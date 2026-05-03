# Research: Production Benchmark And Release Gate

## Decision: Implement A Final Aggregate, Not A New Crawler Path

The release gate composes existing reports from specs 039-053 instead of
creating a separate crawl path. This prevents target readiness from being
claimed by a shortcut that bypasses evidence, publication, scale, ops, or safety
contracts.

## Decision: Deterministic Authorized Fixtures

The benchmark uses deterministic local fixtures and canonical refs. It does not
contact public websites or depend on unmanaged external benchmark services. Live
adapter gates remain represented by existing Docker-backed tests and lower-level
runtime reports.

## Decision: Typed Release Failures

The gate introduces `ProductionBenchmarkReleaseFailureType` for missing runtime
gates, SLO violations, release blockers, false-ready status, and replay
mismatch. This prevents vague release failures and makes every negative fixture
assertable.

## Decision: Core Import Neutrality

Core release runtime imports only VeraCrawl contracts and existing core runtime
functions. It does not import concrete storage, queue, telemetry, browser,
model, agent framework, cloud, UI, or site-specific scraper implementations.

## Alternatives Rejected

- Calling every CLI subprocess from the release gate was rejected because it
  would couple core acceptance to CLI behavior and make replay harder to inspect.
- Treating registry validation alone as release readiness was rejected because
  it would be contract-only and could miss runtime wiring gaps.
- Using public websites was rejected because authorization, determinism, and
  replayability are required by the constitution and target acceptance docs.
