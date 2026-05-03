# Implementation Plan: VeraCrawl Target Product Acceptance Gate

**Branch**: `032-product-acceptance-gate` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/032-product-acceptance-gate/spec.md`

## Summary

Implement an executable product acceptance gate proving all target buyer-value workflows and minimum product gates have deterministic fixture/oracle, evidence, replay, operator-visible result, policy, command/event/outbox, artifact, workflow-specific, and status-accuracy refs. The gate rejects missing workflows, missing minimum gates, missing evidence/replay/operator visibility/policy, scaffold-only or contract-only claims, false completion labels, degraded-operational labels, and missing export reconciliation while remaining independent of concrete runtime dependencies and UI frameworks.

## Technical Context

**Language/Version**: Python 3.12 target with Python >=3.11 package support
**Primary Dependencies**: Pydantic v2, pytest, ruff, mypy
**Storage**: Deterministic contract objects and fixture reports only
**Testing**: Unit, contract, integration fixture tests; registry validation; CLI fixture loop; full pytest gates
**Target Platform**: Local deterministic CLI/runtime foundation
**Project Type**: Python package / CLI
**Performance Goals**: Deterministic product acceptance fixture loop under 30 seconds
**Constraints**: Core independent of concrete storage, queue, browser, HTTP client, model SDK, agent framework, export target, UI framework, and site-specific scraper dependencies
**VeraCrawl Owner Services**: `review_replay`, `ops`, `control`, `agents`, `evidence`, `export`, `policy`, and `tests`
**Canonical Contracts**: `ProductWorkflowReadinessRecord`, `ProductAcceptanceGateReport`, `ProductAcceptanceFixtureManifest`
**Replay/Artifact Impact**: Pass requires evidence, replay, operator-visible result, policy, artifact, command, event cursor, outbox, workflow-specific, status-accuracy, and minimum product gate refs for every target workflow
**Security/Policy Impact**: Product readiness must reject unsafe dynamic/auth workflows, missing credential/privacy/recovery/export refs, and false capability state labels

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; no one-off scraper assumptions are introduced.
- [x] Python remains the implementation language unless a constitution amendment changes it.
- [x] Agent runtime remains framework-neutral; model SDKs and agent frameworks are isolated behind replaceable adapters.
- [x] Low coupling/high cohesion boundaries are explicit through ports, commands, events, typed results, and owner services.
- [x] Evidence, verification, publication, replay, and artifact lineage are defined for affected outputs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and export/withdrawal gates are defined where applicable.
- [x] Command payload schemas, event payload schemas, state transitions, fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

```text
src/veracrawl/contracts/enums.py
src/veracrawl/contracts/product_acceptance.py
src/veracrawl/contracts/__init__.py
src/veracrawl/contracts/registry.py
src/veracrawl/product_acceptance/__init__.py
src/veracrawl/product_acceptance/gate.py
src/veracrawl/cli/product_acceptance.py
tests/contract/test_product_acceptance_contracts.py
tests/contract/test_product_acceptance_contract_registry.py
tests/contract/test_product_acceptance_import_boundaries.py
tests/unit/test_product_acceptance_gate.py
tests/helpers/product_acceptance_fixture_assertions.py
tests/integration/test_product_acceptance_fixtures.py
tests/fixtures/product-acceptance-*/
```

## Phase 0: Research And Design

See [research.md](research.md), [data-model.md](data-model.md), [contracts/product-acceptance.md](contracts/product-acceptance.md), [contracts/boundary.md](contracts/boundary.md), and [quickstart.md](quickstart.md).

## Phase 1: Contract And Registry

- Add product acceptance enums and contracts.
- Export contracts and register commands, events, fixtures, and target area coverage.
- Add contract, registry, and import-boundary tests.

## Phase 2: Runtime Gate And CLI

- Implement deterministic success, needs-review, and negative scenarios.
- Add `veracrawl-product-acceptance run` fixture CLI.
- Add fixture manifests/oracles for all success and negative paths.

## Phase 3: Docs And Verification

- Update README and target docs with usage, contract, and acceptance notes.
- Run prerequisite, lock, lint, type, registry, focused tests, CLI loop, full non-Docker, Docker-backed, and diff checks.

## Complexity Tracking

No constitution deviations are required.
