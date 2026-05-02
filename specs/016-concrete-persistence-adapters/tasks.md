# Tasks: VeraCrawl Concrete Persistence Adapter Family

**Input**: Design documents from `/specs/016-concrete-persistence-adapters/`

## Phase 1: Implementation

- [x] T001 Add `veracrawl-persistence-adapter` console script target in `pyproject.toml`
- [x] T002 Extend persistence contracts and enums for adapter migration/conformance
- [x] T003 Create core adapter conformance harness in `src/veracrawl/persistence/adapter_conformance.py`
- [x] T004 Create SQLite adapter in `src/veracrawl/adapters/persistence/sqlite.py`
- [x] T005 Create Postgres contract descriptor in `src/veracrawl/adapters/persistence/postgres_contract.py`
- [x] T006 Create persistence adapter CLI fixture runner
- [x] T007 Extend contract exports and registry coverage
- [x] T008 Add adapter fixtures and fixture assertion helpers
- [x] T009 Add contract, unit, boundary, and integration tests
- [x] T010 Update README, AGENTS, docs/07, docs/10, and docs/11
- [x] T011 Run prerequisite, registry, CLI fixture, ruff, mypy, and full pytest gates
- [x] T012 Verify no false production-readiness claims for Postgres, external queues, cloud, deployment, or observability

## Implementation Verification Record

- Prerequisites: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed for `specs/016-concrete-persistence-adapters`.
- Registry: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`.
- CLI fixtures: all nine adapter fixtures passed through `veracrawl-persistence-adapter run`.
- Quality gate: `uv run --python python3.12 --extra dev ruff check src tests` passed; `uv run --python python3.12 --extra dev mypy src` passed; `uv run --python python3.12 --extra dev pytest tests` passed with 316 tests in 11.69s.
- Non-completion boundary: README, target docs, spec, tasks, code, tests, and CLI output avoid claiming live Postgres, external queue, cloud, deployment, or observability readiness.
