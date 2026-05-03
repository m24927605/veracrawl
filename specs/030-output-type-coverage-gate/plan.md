# Implementation Plan: VeraCrawl Target Output Type Coverage Gate

**Branch**: `030-output-type-coverage-gate` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/030-output-type-coverage-gate/spec.md`

## Summary

Implement an executable output type coverage gate proving all target output types have evidence-backed verification, publication, manifest, lifecycle, policy, command/event/outbox, and replay refs. The gate rejects derived-context-only evidence and remains independent of external storage/export/runtime dependencies.

## Technical Context

**Language/Version**: Python 3.12 target with Python >=3.11 package support
**Primary Dependencies**: Pydantic v2, pytest, ruff, mypy
**Storage**: Deterministic contract objects and fixture reports only
**Testing**: Unit, contract, integration fixture tests; registry validation; CLI fixture loop; full pytest gates
**Target Platform**: Local deterministic CLI/runtime foundation
**Project Type**: Python package / CLI
**Performance Goals**: Deterministic output coverage fixture loop under 30 seconds
**Constraints**: Core independent of concrete storage, queue, export, browser, model SDK, agent framework, HTTP client, and site-specific scraper dependencies
**Canonical Contracts**: `OutputTypeCoverageRecord`, `OutputTypePublicationGateReport`, `OutputTypeCoverageFixtureManifest`
**Replay/Artifact Impact**: Pass requires source evidence, evidence coverage, verification, publication, manifest, lifecycle, policy, command, event cursor, outbox, and replay refs for every target output type

## Constitution Check

- [x] General-purpose output coverage is explicit across all target output types.
- [x] Evidence boundaries reject candidate, graph, memory, agent reasoning, and temporal KG as source evidence.
- [x] Replay, policy, command, event cursor, and outbox refs are required for pass.
- [x] Core dependency neutrality is preserved.

## Project Structure

```text
src/veracrawl/contracts/enums.py
src/veracrawl/contracts/publication.py
src/veracrawl/contracts/__init__.py
src/veracrawl/contracts/registry.py
src/veracrawl/publish/output_coverage.py
src/veracrawl/cli/output_coverage.py
tests/contract/test_output_type_coverage_contracts.py
tests/contract/test_output_type_coverage_contract_registry.py
tests/contract/test_output_type_coverage_import_boundaries.py
tests/unit/test_output_type_coverage_gate.py
tests/helpers/output_type_coverage_fixture_assertions.py
tests/integration/test_output_type_coverage_fixtures.py
tests/fixtures/output-type-coverage-*/
```

## Phase 0: Research And Design

See [research.md](research.md), [data-model.md](data-model.md), [contracts/output-type-coverage.md](contracts/output-type-coverage.md), [contracts/boundary.md](contracts/boundary.md), and [quickstart.md](quickstart.md).

## Phase 1: Contract And Registry

- Add output coverage enums and contracts.
- Export contracts and register commands, events, fixtures, and target area coverage.
- Add contract, registry, and import-boundary tests.

## Phase 2: Runtime Gate And CLI

- Implement deterministic success, needs-review, and negative scenarios.
- Add `veracrawl-output-coverage run` fixture CLI.
- Add fixture manifests/oracles for all success and negative paths.

## Phase 3: Docs And Verification

- Update README and target docs with usage, contract, and acceptance notes.
- Run prerequisite, lock, lint, type, registry, focused tests, CLI loop, full non-Docker, Docker-backed, and diff checks.

## Complexity Tracking

No constitution deviations are required.
