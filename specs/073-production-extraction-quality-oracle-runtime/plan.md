# Implementation Plan: Production Extraction Quality And Oracle Runtime

## Scope

Implement row 073 as the production extraction quality gate. The slice records
field oracle, precision/recall, publication readiness, evidence packet,
verification, publication gate, policy, command/event/outbox, and replay refs.

## Technical Plan

- Reuse existing field oracle, quality metrics, repair quality, and quality
  release contract refs.
- Implement `extraction_quality` metrics in the shared production-grade runtime.
- Expose `veracrawl-production-quality-gate`.
- Add deterministic fixture/oracle corpus for production extraction quality.

## Validation Plan

- Positive fixture: `tests/fixtures/production-extraction-quality-success`.
- Contract, registry, runtime, fixture, and import-boundary tests under the
  production-grade test set.
