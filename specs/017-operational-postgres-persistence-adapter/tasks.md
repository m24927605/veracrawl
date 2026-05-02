# Tasks: VeraCrawl Operational Postgres Persistence Adapter

**Input**: Design documents from `/specs/017-operational-postgres-persistence-adapter/`

## Phase 1: Implementation

- [x] T001 Add optional `postgres` dependency extra in `pyproject.toml`
- [x] T002 Add operational `postgres` adapter kind and forbid core psycopg imports
- [x] T003 Add reusable JSON document persistence adapter mixin
- [x] T004 Implement `PostgresPersistenceAdapter` and operational Postgres adapter spec
- [x] T005 Extend adapter conformance harness for operational Postgres and no-runtime report
- [x] T006 Extend persistence adapter CLI for `--postgres-dsn` and env DSN
- [x] T007 Register Postgres operational fixtures and target area coverage
- [x] T008 Add Postgres adapter fixtures and oracles
- [x] T009 Add unit, contract, CLI, and Docker-backed live integration tests
- [x] T010 Update README, AGENTS, docs/07, docs/10, and docs/11
- [x] T011 Run prerequisite, registry, CLI fixture, ruff, mypy, full pytest, and live Postgres gates
- [x] T012 Verify no false production-readiness claims for managed Postgres, external queues, object storage, cloud, deployment, or observability

## Implementation Verification Record

- Prerequisites: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed for `specs/017-operational-postgres-persistence-adapter`.
- Registry: `uv run --python python3.12 --extra dev --extra postgres veracrawl-contracts validate --format json` passed with `ok: true`.
- CLI fixtures: `postgres-runtime-unavailable` passed with `needs_review`; all three live Postgres operational fixtures passed through `veracrawl-persistence-adapter run`.
- Quality gate: `uv run --python python3.12 --extra dev --extra postgres ruff check src tests` passed; `uv run --python python3.12 --extra dev --extra postgres mypy src` passed; `VERACRAWL_POSTGRES_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres pytest tests` passed with 322 tests in 14.70s.
- Live gate: `VERACRAWL_POSTGRES_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres pytest tests/integration/test_postgres_persistence_adapter_live.py` passed in 11.35s.
- Non-completion boundary: README, target docs, spec, tasks, code, tests, and CLI output avoid claiming managed Postgres, external queue, object storage, cloud, deployment, or observability readiness.
