# Tasks: VeraCrawl Operational Runtime Infrastructure Gate

**Input**: Design documents from `/specs/020-operational-runtime-infrastructure-gate/`

## Phase 1: Implementation

- [x] T001 Add `veracrawl-infrastructure` console script target
- [x] T002 Add runtime infrastructure contracts and enums
- [x] T003 Add core runtime infrastructure gate harness
- [x] T004 Implement dynamic CLI runner for Postgres, Redis/Valkey, and S3-compatible live fixtures
- [x] T005 Register contracts, commands, events, fixtures, and target area coverage
- [x] T006 Add success, idempotency, no-runtime, and negative fixtures/oracles
- [x] T007 Add contract, unit, CLI, boundary, and Docker-backed live integration tests
- [x] T008 Update README, AGENTS, docs/07, docs/09, docs/10, and docs/11
- [x] T009 Run prerequisite, registry, CLI fixture, ruff, mypy, full pytest, and live infrastructure gates
- [x] T010 Verify no false production-readiness claims for managed cloud, deployment, observability, worker fleet, browser rendering, model SDK, or agent framework readiness

## Implementation Verification Record

- Prerequisites: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed for `specs/020-operational-runtime-infrastructure-gate`.
- Registry: `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 veracrawl-contracts validate --format json` passed with `ok: true`.
- Static gates: `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 ruff check src tests` passed; `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 mypy src` passed with no issues across 165 source files.
- CLI no-runtime and negative fixtures: `operational-infrastructure-runtime-unavailable` returned `needs_review`; `infrastructure-missing-persistence-refs`, `infrastructure-missing-queue-refs`, `infrastructure-missing-object-refs`, and `infrastructure-missing-replay-refs` returned typed `fail` results.
- CLI live fixtures: `operational-infrastructure-success` and `operational-infrastructure-idempotency-success` passed against temporary Docker Postgres, Redis, and MinIO runtimes; idempotency reported `idempotency_deduped: true`.
- Focused tests: runtime infrastructure contract, registry, boundary, unit, and non-live integration tests passed with `12 passed in 0.56s`.
- Full quality gate: `VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest tests` passed with `370 passed, 3 skipped in 16.47s`.
- Live gate: `VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest tests/integration/test_operational_infrastructure_live.py` passed with `1 passed in 4.23s`.
- Non-completion boundary: README, target docs, spec, tasks, code, tests, and CLI output avoid claiming managed cloud, deployment, production worker fleet, metrics/tracing backend, observability, browser rendering, model SDK, or agent framework readiness.
