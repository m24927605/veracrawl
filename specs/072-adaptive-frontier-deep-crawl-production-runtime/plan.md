# Implementation Plan: Adaptive Frontier Deep Crawl Production Runtime

## Scope

Implement row 072 as the production deep crawl gate. The slice records bounded
multi-page crawl capability, adaptive frontier capability refs, source-backed
artifact/hash/anchor refs, policy refs, command/event/outbox refs, replay refs,
and coverage metrics.

## Technical Plan

- Reuse production-grade gate contracts and existing deep crawl contract refs.
- Implement `deep_crawl_production` metrics and evidence refs in the shared
  production-grade runtime.
- Expose `veracrawl-deep-crawl-production`.
- Add deterministic fixture/oracle corpus for bounded deep crawl coverage.

## Validation Plan

- Positive fixture: `tests/fixtures/production-deep-crawl-success`.
- Contract, registry, runtime, fixture, and import-boundary tests under the
  production-grade test set.
