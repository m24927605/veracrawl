# Implementation Plan: VeraCrawl Target Website Pattern Coverage Gate

**Branch**: `031-website-pattern-coverage-gate` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/031-website-pattern-coverage-gate/spec.md`

## Summary

Implement an executable website pattern coverage gate proving all target website patterns have deterministic benchmark fixture/oracle, source adapter, site model/page type, source evidence, output/evidence, policy, artifact, command/event/outbox, pattern-specific, and replay refs. The gate rejects single-site assumptions, scaffold-only claims, unsupported patterns, unsafe interactions, and missing replay while remaining independent of concrete runtime dependencies.

## Technical Context

**Language/Version**: Python 3.12 target with Python >=3.11 package support
**Primary Dependencies**: Pydantic v2, pytest, ruff, mypy
**Storage**: Deterministic contract objects and fixture reports only
**Testing**: Unit, contract, integration fixture tests; registry validation; CLI fixture loop; full pytest gates
**Target Platform**: Local deterministic CLI/runtime foundation
**Project Type**: Python package / CLI
**Performance Goals**: Deterministic website pattern fixture loop under 30 seconds
**Constraints**: Core independent of concrete storage, queue, browser, HTTP client, model SDK, agent framework, export target, and site-specific scraper dependencies
**Canonical Contracts**: `WebsitePatternCoverageRecord`, `WebsitePatternCoverageReport`, `WebsitePatternCoverageFixtureManifest`
**Replay/Artifact Impact**: Pass requires source adapter, source evidence, site model/page type, output/evidence, policy, artifact oracle, command, event cursor, outbox, pattern-specific, and replay refs for every target pattern

## Constitution Check

- [x] General-purpose website pattern coverage is explicit across all target patterns.
- [x] Single-site scraper assumptions and scaffold-only coverage are rejected.
- [x] Pattern-specific safety, evidence, policy, command/event, outbox, and replay refs are required for pass.
- [x] Core dependency neutrality is preserved.

## Project Structure

```text
src/veracrawl/contracts/enums.py
src/veracrawl/contracts/website_pattern.py
src/veracrawl/contracts/__init__.py
src/veracrawl/contracts/registry.py
src/veracrawl/patterns/coverage.py
src/veracrawl/cli/website_patterns.py
tests/contract/test_website_pattern_coverage_contracts.py
tests/contract/test_website_pattern_coverage_contract_registry.py
tests/contract/test_website_pattern_coverage_import_boundaries.py
tests/unit/test_website_pattern_coverage_gate.py
tests/helpers/website_pattern_fixture_assertions.py
tests/integration/test_website_pattern_coverage_fixtures.py
tests/fixtures/website-pattern-*/
```

## Phase 0: Research And Design

See [research.md](research.md), [data-model.md](data-model.md), [contracts/website-pattern-coverage.md](contracts/website-pattern-coverage.md), [contracts/boundary.md](contracts/boundary.md), and [quickstart.md](quickstart.md).

## Phase 1: Contract And Registry

- Add website pattern enums and contracts.
- Export contracts and register commands, events, fixtures, and target area coverage.
- Add contract, registry, and import-boundary tests.

## Phase 2: Runtime Gate And CLI

- Implement deterministic success, needs-review, and negative scenarios.
- Add `veracrawl-website-patterns run` fixture CLI.
- Add fixture manifests/oracles for all success and negative paths.

## Phase 3: Docs And Verification

- Update README and target docs with usage, contract, and acceptance notes.
- Run prerequisite, lock, lint, type, registry, focused tests, CLI loop, full non-Docker, Docker-backed, and diff checks.

## Complexity Tracking

No constitution deviations are required.
