# Implementation Plan: VeraCrawl Production Persistence And Queue Runtime

**Branch**: `015-production-persistence-queue-runtime` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)

## Summary

Implement production-facing persistence and queue runtime semantics as executable contracts, ports, a standard-library reference store, runtime orchestration, replay validation, CLI fixture runner, registry entries, fixture oracles, docs, and tests. Core remains storage/queue/cloud neutral; concrete infrastructure stays behind replaceable ports/adapters.

## Technical Context

**Language/Version**: Python 3.11+ with Python 3.12 verification
**Primary Dependencies**: Pydantic contracts and Python standard library
**Storage**: Reference filesystem-backed store for fixture proof only; no production vendor lock-in
**Testing**: pytest, ruff, mypy, registry validation, fixture CLI runs
**Target Platform**: Python package and CLI foundation
**Owner Services**: `runtime_events`, `scheduler`, `review_replay`, `ports`, `tests`
**Canonical Contracts**: `PersistenceAdapterSpec`, `PersistenceTransactionRecord`, `IdempotencyPersistenceRecord`, `PersistentQueueOperationRecord`, `PersistenceRuntimeReport`, `PersistenceFixtureManifest`
**Replay/Artifact Impact**: Reports require transaction, durable command, idempotency, event cursor, outbox, artifact, queue operation, lease, policy, failure/recovery, and replay refs.
**Security/Policy Impact**: Persistence cannot hide policy, queue, outbox, artifact, or replay failures.

## Constitution Check

- [x] No site-specific scraper assumptions.
- [x] Python remains the implementation language.
- [x] Core remains storage, queue, cloud, metrics, tracing, HTTP, browser, and agent-framework neutral.
- [x] Low coupling/high cohesion is preserved through contracts, ports, runtime, reference store, CLI, registry, and fixtures.
- [x] The reference filesystem store is an adapter proof for tests, not a target architecture narrowing.
- [x] Negative replay, idempotency, queue, outbox, artifact, and transaction tests are planned before implementation.
- [x] Target architecture is not weakened for schedule or staffing reasons.

## Project Structure

```text
src/veracrawl/contracts/persistence.py
src/veracrawl/ports/persistence.py
src/veracrawl/runtime_support/persistence_store.py
src/veracrawl/persistence/runtime.py
src/veracrawl/review_replay/persistence.py
src/veracrawl/cli/persistence.py
tests/contract/test_persistence_contract_registry.py
tests/contract/test_persistence_contracts.py
tests/contract/test_persistence_import_boundaries.py
tests/unit/test_persistence_reference_store.py
tests/unit/test_persistence_runtime.py
tests/unit/test_persistence_replay.py
tests/integration/test_persistence_fixtures.py
tests/helpers/persistence_fixture_assertions.py
tests/fixtures/<persistence_fixture_id>/
```

**Structure Decision**: Keep canonical contracts and runtime in core packages, reference persistence implementation in `runtime_support`, and vendor integrations outside core behind ports.
