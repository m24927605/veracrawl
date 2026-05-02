# Implementation Plan: VeraCrawl Scale Hardening

**Branch**: `014-scale-hardening` | **Date**: 2026-05-02 | **Spec**: [spec.md](spec.md)

## Summary

Implement the target scale/reliability spine as deterministic contracts, ports, runtime, replay validation, CLI fixture runner, registry entries, fixture oracles, docs, and tests. This slice proves sharding, leases, backpressure, autoscaling, dead-letter recovery, and replay refs without coupling core to concrete infrastructure.

## Technical Context

**Language/Version**: Python 3.11+ with Python 3.12 verification
**Primary Dependencies**: Pydantic contracts and standard library only
**Storage**: In-memory deterministic fixture records only
**Testing**: pytest, ruff, mypy, registry validation, fixture CLI runs
**Target Platform**: Python library/CLI foundation
**Project Type**: Single Python package
**VeraCrawl Owner Services**: `scheduler`, `ops`, `runtime_events`, `review_replay`, `tests`
**Canonical Contracts**: `QueueTopologySpec`, `QueueItem`, `ShardLease`, `RetryDeadLetterRecord`, `BackpressureSignal`, `AutoscalingDecision`, `ScaleRecoveryReport`, `ScaleFixtureManifest`
**Replay/Artifact Impact**: Scale reports require queue, lease, dead-letter, failure/recovery, backpressure, autoscaling, policy, command, event cursor, outbox, and replay refs.
**Security/Policy Impact**: Backpressure, pause, and autoscaling decisions are policy-visible and must not alter correctness.

## Constitution Check

- [x] No site-specific scraper assumptions.
- [x] Python remains the implementation language.
- [x] Core remains infrastructure-neutral.
- [x] Low coupling/high cohesion is preserved through contracts, ports, runtime, CLI, registry, and fixtures.
- [x] Scale decisions are throughput controls only and do not replace owner-service correctness.
- [x] Fixture/oracle, negative, replay, and policy tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

```text
src/veracrawl/contracts/scale.py
src/veracrawl/ports/scale.py
src/veracrawl/scale/hardening.py
src/veracrawl/review_replay/scale.py
src/veracrawl/cli/scale.py
tests/contract/test_scale_contract_registry.py
tests/contract/test_scale_contracts.py
tests/contract/test_scale_import_boundaries.py
tests/unit/test_scale_hardening.py
tests/unit/test_scale_replay.py
tests/unit/test_scale_policy_boundaries.py
tests/integration/test_scale_fixtures.py
tests/helpers/scale_fixture_assertions.py
tests/fixtures/<scale_fixture_id>/
```

**Structure Decision**: Keep scale core in contracts, ports, deterministic runtime, replay validation, and CLI. Concrete infrastructure adapters are explicitly out of scope.
