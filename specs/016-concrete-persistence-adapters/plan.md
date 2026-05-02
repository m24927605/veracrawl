# Implementation Plan: VeraCrawl Concrete Persistence Adapter Family

**Branch**: `016-concrete-persistence-adapters` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)

## Summary

Implement concrete persistence adapter conformance without coupling VeraCrawl core to concrete infrastructure. Add adapter conformance contracts and core harness, a real SQLite adapter in `adapters/`, a Postgres contract descriptor, adapter fixtures, docs, tests, and CLI.

## Technical Context

**Language/Version**: Python 3.11+ with Python 3.12 verification
**Primary Dependencies**: Pydantic contracts and Python standard library `sqlite3`
**Storage**: SQLite adapter under `veracrawl.adapters.persistence`; Postgres contract descriptor only
**Testing**: pytest, ruff, mypy, registry validation, fixture CLI runs
**Owner Services**: `ports`, `runtime_events`, `scheduler`, `review_replay`, `tests`
**Canonical Contracts**: `PersistenceMigrationRecord`, `PersistenceAdapterConformanceReport`, `PersistenceAdapterFixtureManifest`
**Replay/Artifact Impact**: Adapter conformance requires transaction, migration, idempotency, event cursor, outbox, artifact index, queue operation, lease, policy, and replay refs.

## Constitution Check

- [x] No single-site scraper assumptions.
- [x] Core remains storage/queue/cloud neutral.
- [x] Concrete SQLite implementation lives in `adapters/`.
- [x] Postgres is represented by contract harness only; no fake operational completion.
- [x] Fixture/oracle and negative conformance tests are planned before implementation.
- [x] Target architecture is not weakened for schedule or staffing reasons.

## Project Structure

```text
src/veracrawl/persistence/adapter_conformance.py
src/veracrawl/adapters/persistence/sqlite.py
src/veracrawl/adapters/persistence/postgres_contract.py
src/veracrawl/cli/persistence_adapter.py
tests/contract/test_persistence_adapter_contract_registry.py
tests/contract/test_persistence_adapter_contracts.py
tests/contract/test_persistence_adapter_import_boundaries.py
tests/unit/test_sqlite_persistence_adapter.py
tests/unit/test_postgres_contract_descriptor.py
tests/unit/test_persistence_adapter_conformance.py
tests/integration/test_persistence_adapter_fixtures.py
tests/fixtures/<adapter_fixture_id>/
```
