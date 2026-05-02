# Implementation Plan: VeraCrawl Operational Postgres Persistence Adapter

**Branch**: `017-operational-postgres-persistence-adapter` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)

## Summary

Implement a real Postgres persistence adapter under `veracrawl.adapters.persistence` while keeping VeraCrawl core storage-neutral. Add operational Postgres adapter kind, SQL migration descriptors, live fixture execution through explicit DSN/Docker gate, no-runtime `needs_review` reporting, registry/docs/test coverage, and import-boundary enforcement.

## Technical Context

**Language/Version**: Python 3.11+ with Python 3.12 verification
**Primary Dependencies**: Pydantic contracts, optional `psycopg[binary]` extra for live Postgres
**Storage**: Postgres JSONB document table owned by adapter migrations
**Testing**: pytest, ruff, mypy, registry validation, CLI fixtures, Docker-backed live integration gate
**Owner Services**: `ports`, `runtime_events`, `scheduler`, `review_replay`, `tests`
**Canonical Contracts**: Reuse `PersistenceAdapterSpec`, `PersistenceMigrationRecord`, `PersistenceAdapterConformanceReport`, `PersistenceAdapterFixtureManifest`
**Replay/Artifact Impact**: Operational Postgres pass requires transaction, migration, idempotency, event cursor, outbox, artifact, queue, lease, policy, and replay refs.

## Constitution Check

- [x] No single-site scraper assumptions.
- [x] Core remains free of Postgres, psycopg, concrete queue, and cloud imports.
- [x] Concrete Postgres implementation lives in `adapters/`.
- [x] Postgres contract descriptor remains `needs_review`; only live operational adapter can pass.
- [x] Fixture/oracle, live integration, no-runtime report, and negative boundary tests are planned before implementation.
- [x] Target architecture is not weakened for schedule or staffing reasons.

## Project Structure

```text
src/veracrawl/adapters/persistence/json_document.py
src/veracrawl/adapters/persistence/postgres.py
src/veracrawl/persistence/adapter_conformance.py
src/veracrawl/cli/persistence_adapter.py
tests/contract/test_persistence_adapter_import_boundaries.py
tests/unit/test_postgres_persistence_adapter.py
tests/integration/test_postgres_persistence_adapter_fixtures.py
tests/integration/test_postgres_persistence_adapter_live.py
tests/fixtures/<postgres_adapter_fixture_id>/
```
