# Implementation Plan: VeraCrawl Operational Queue Broker Adapter

**Branch**: `018-operational-queue-broker-adapter` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)

## Summary

Implement live queue broker execution without coupling VeraCrawl core to broker SDKs. Add queue broker contracts, a core conformance harness, Redis/Valkey adapter, live/no-runtime fixture CLI, registry/docs/test coverage, and Docker-backed Redis integration.

## Technical Context

**Language/Version**: Python 3.11+ with Python 3.12 verification
**Primary Dependencies**: Pydantic contracts, optional `redis` extra for live Redis/Valkey
**Broker**: Redis/Valkey adapter under `veracrawl.adapters.queue_brokers`
**Testing**: pytest, ruff, mypy, registry validation, CLI fixtures, Docker-backed live integration gate
**Owner Services**: `scheduler`, `ops`, `review_replay`, `ports`, `tests`
**Canonical Contracts**: `QueueBrokerAdapterSpec`, `QueueBrokerOperationRecord`, `QueueBrokerConformanceReport`, `QueueBrokerFixtureManifest`
**Replay/Artifact Impact**: Operational queue broker pass requires topology, queue item, broker operation, lease, heartbeat, ack/nack, dead-letter, backpressure/fairness, policy, and replay refs.

## Constitution Check

- [x] No single-site scraper assumptions.
- [x] Core remains free of Redis, broker, storage, and cloud imports.
- [x] Concrete Redis/Valkey implementation lives in `adapters/`.
- [x] Persistence queue operation refs remain canonical state refs, not live broker proof.
- [x] Fixture/oracle, live integration, no-runtime report, and negative boundary tests are planned before implementation.
- [x] Target architecture is not weakened for schedule or staffing reasons.

## Project Structure

```text
src/veracrawl/contracts/scale.py
src/veracrawl/scale/broker_conformance.py
src/veracrawl/adapters/queue_brokers/redis.py
src/veracrawl/cli/queue_broker.py
tests/contract/test_queue_broker_contracts.py
tests/contract/test_queue_broker_contract_registry.py
tests/contract/test_queue_broker_import_boundaries.py
tests/unit/test_redis_queue_broker_adapter.py
tests/integration/test_queue_broker_fixtures.py
tests/integration/test_redis_queue_broker_live.py
tests/fixtures/<queue_broker_fixture_id>/
```
