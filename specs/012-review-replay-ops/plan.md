# Implementation Plan: VeraCrawl Review Replay Ops Console

**Branch**: `012-review-replay-ops` | **Date**: 2026-05-02 | **Spec**: [spec.md](spec.md)

## Summary

Implement the target review/replay/ops console spine as deterministic contracts, runtime, replay validation, CLI fixture runner, fixture oracles, registry entries, docs, and tests. This slice makes review queue state, replay audit status, operational failures, recovery decisions, DR restore reports, and quality dashboard snapshots replay-visible without claiming a production UI or monitoring backend.

## Technical Context

**Language/Version**: Python 3.11+ with Python 3.12 verification  
**Primary Dependencies**: Pydantic contracts and standard library only  
**Storage**: In-memory deterministic fixture records only; production stores remain behind later ports/adapters  
**Testing**: pytest, ruff, mypy, registry validation, fixture CLI runs  
**Target Platform**: Python library/CLI foundation  
**Project Type**: Single Python package  
**VeraCrawl Owner Services**: `review_replay`, `ops`, `verify`, `runtime_events`, `tests`  
**Canonical Contracts**: `ReviewItem`, `ReplayAuditView`, `FailureRecord`, `RecoveryAction`, `DRRestoreReport`, `QualityReport`, `OpsDashboardSnapshot`, `OpsConsoleReport`, `OpsFixtureManifest`  
**Replay/Artifact Impact**: Ops reports require review refs, replay audit refs, quality refs, dashboard refs, policy refs, command refs, event cursor refs, outbox refs, projection watermarks, artifact hashes, and failure/recovery refs.  
**Security/Policy Impact**: Recovery actions with destructive or external side effects require policy and approval refs; unsafe recovery attempts are reported as failures.

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; no one-off scraper assumptions are introduced.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral; this slice adds no agent framework dependencies.
- [x] Low coupling/high cohesion boundaries are explicit through contracts, runtime, CLI, replay validation, registry, and fixtures.
- [x] Evidence, verification, publication, replay, and artifact lineage are represented through refs rather than hidden state.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and export boundaries are not weakened.
- [x] Command payload schemas, event payload schemas, state transitions, fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

```text
src/veracrawl/contracts/ops.py
src/veracrawl/ops/console.py
src/veracrawl/review_replay/ops.py
src/veracrawl/cli/ops.py
tests/contract/test_ops_contract_registry.py
tests/contract/test_ops_contracts.py
tests/contract/test_ops_import_boundaries.py
tests/unit/test_ops_console.py
tests/unit/test_ops_replay.py
tests/unit/test_ops_review_recovery_boundary.py
tests/integration/test_ops_fixtures.py
tests/helpers/ops_fixture_assertions.py
tests/fixtures/<ops_fixture_id>/
```

**Structure Decision**: Keep the slice inside existing package boundaries. Contracts live in `contracts`, deterministic orchestration in `ops`, replay checks in `review_replay`, CLI in `cli`, fixtures under `tests/fixtures`, and registry wiring in `contracts/registry.py`.
