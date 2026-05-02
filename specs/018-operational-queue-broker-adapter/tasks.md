# Tasks: VeraCrawl Operational Queue Broker Adapter

**Input**: Design documents from `/specs/018-operational-queue-broker-adapter/`

## Phase 1: Implementation

- [x] T001 Add optional `queue-redis` dependency extra and console script target
- [x] T002 Add queue broker contracts and enums
- [x] T003 Add core queue broker conformance harness
- [x] T004 Implement Redis/Valkey queue broker adapter
- [x] T005 Implement `veracrawl-queue-broker` CLI with `--redis-url` and env URL
- [x] T006 Register queue broker contracts, events, fixtures, and target area coverage
- [x] T007 Add Redis queue broker fixtures and oracles
- [x] T008 Add contract, unit, CLI, boundary, and Docker-backed live integration tests
- [x] T009 Update README, AGENTS, docs/07, docs/09, docs/10, and docs/11
- [x] T010 Run prerequisite, registry, CLI fixture, ruff, mypy, full pytest, and live Redis gates
- [x] T011 Verify no false production-readiness claims for managed Redis, cloud queues, deployment, autoscaling, or observability

## Implementation Verification Record

- Prerequisites: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed for `specs/018-operational-queue-broker-adapter`.
- Registry: `uv run --python python3.12 --extra dev --extra queue-redis veracrawl-contracts validate --format json` passed with `ok: true`.
- CLI fixtures: `redis-broker-runtime-unavailable` passed with `needs_review`; `broker-missing-fencing-token`, `broker-missing-heartbeat`, and `broker-missing-dead-letter` passed with `fail`; all three live Redis operational fixtures passed through `veracrawl-queue-broker run`.
- Quality gate: `uv run --python python3.12 --extra dev --extra queue-redis ruff check src tests` passed; `uv run --python python3.12 --extra dev --extra queue-redis mypy src` passed; `VERACRAWL_REDIS_DOCKER=1 uv run --python python3.12 --extra dev --extra queue-redis pytest tests` passed with 340 passed, 1 skipped in 12.80s.
- Live gate: `VERACRAWL_REDIS_DOCKER=1 uv run --python python3.12 --extra dev --extra queue-redis pytest tests/integration/test_redis_queue_broker_live.py` passed with 1 test in 0.90s.
- Non-completion boundary: README, target docs, spec, tasks, code, tests, and CLI output avoid claiming managed Redis, cloud queue, deployment, autoscaling, production worker fleet, or observability readiness.
