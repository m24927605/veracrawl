# Implementation Plan: VeraCrawl Export Connectors

**Branch**: `013-export-connectors` | **Date**: 2026-05-02 | **Spec**: [spec.md](spec.md)

## Summary

Implement the target export connector spine as deterministic contracts, ports, runtime, replay validation, CLI fixture runner, registry entries, fixture oracles, docs, and tests. This slice proves dispatch, receipts, withdrawal, correction propagation, idempotency, and destination mapping without coupling core to any concrete export destination.

## Technical Context

**Language/Version**: Python 3.11+ with Python 3.12 verification  
**Primary Dependencies**: Pydantic contracts and standard library only  
**Storage**: In-memory deterministic fixture records only  
**Testing**: pytest, ruff, mypy, registry validation, fixture CLI runs  
**Target Platform**: Python library/CLI foundation  
**Project Type**: Single Python package  
**VeraCrawl Owner Services**: `export`, `publish`, `review_replay`, `ops`, `runtime_events`, `tests`  
**Canonical Contracts**: `ExportTargetSpec`, `ExportJob`, `ExportAttempt`, `ExportDeliveryReceipt`, `ExportWithdrawalJob`, `ExportWithdrawalAttempt`, `ExportCorrectionRecord`, `ExportReconciliationReport`, `ExportFixtureManifest`  
**Replay/Artifact Impact**: Export reports require output refs, destination object mappings, receipts, withdrawal mappings, correction refs, policy refs, command refs, event cursors, outbox refs, and replay bundle refs.  
**Security/Policy Impact**: Dispatch and withdrawal require policy refs and redacted destination auth scope refs.

## Constitution Check

- [x] No site-specific scraper assumptions.
- [x] Python remains the implementation language.
- [x] Core remains framework-neutral and destination-neutral.
- [x] Low coupling/high cohesion is preserved through contracts, ports, runtime, CLI, registry, and fixtures.
- [x] Evidence-backed publication remains upstream of export.
- [x] Export credentials and destination auth remain refs; no raw secrets or concrete clients are introduced.
- [x] Fixture/oracle, negative, replay, and policy tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

```text
src/veracrawl/contracts/export.py
src/veracrawl/ports/export.py
src/veracrawl/export/runtime.py
src/veracrawl/review_replay/export.py
src/veracrawl/cli/export.py
tests/contract/test_export_contract_registry.py
tests/contract/test_export_contracts.py
tests/contract/test_export_import_boundaries.py
tests/unit/test_export_runtime.py
tests/unit/test_export_replay.py
tests/unit/test_export_policy_boundaries.py
tests/integration/test_export_fixtures.py
tests/helpers/export_fixture_assertions.py
tests/fixtures/<export_fixture_id>/
```

**Structure Decision**: Keep export core in contracts, ports, deterministic runtime, replay validation, and CLI. Concrete destination adapters are explicitly out of scope for this slice.
