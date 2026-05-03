# Implementation Plan: VeraCrawl Target Area Readiness Impact Closure

**Branch**: `033-target-area-readiness-closure` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/033-target-area-readiness-closure/spec.md`

## Summary

Close a registry metadata contradiction: all target areas are materialized, but replay/privacy impact fields still use prerequisite wording. Update materialized target area impact construction and add executable registry tests so materialized areas cannot carry placeholder/follow-up/target-complete prerequisite wording.

## Technical Context

**Language/Version**: Python 3.12 target with Python >=3.11 package support
**Primary Dependencies**: Pydantic v2, pytest, ruff, mypy
**Storage**: Contract registry metadata only
**Testing**: Registry contract tests; full pytest gates
**Target Platform**: Local deterministic registry validation
**Project Type**: Python package / CLI
**Performance Goals**: No measurable runtime impact
**Constraints**: Do not alter target area coverage status, contract registrations, commands, events, fixtures, or runtime behavior
**VeraCrawl Owner Services**: `contracts`
**Canonical Contracts**: `TargetContractAreaCoverageRegistration`
**Replay/Artifact Impact**: Materialized target areas state replay refs are represented by registered contracts and fixture gates
**Security/Policy Impact**: Materialized target areas state privacy/policy lifecycle refs are represented where required

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
src/veracrawl/contracts/registry.py
tests/contract/test_contract_registry.py
specs/033-target-area-readiness-closure/
```

## Phase 0: Research And Design

See [research.md](research.md), [data-model.md](data-model.md), [contracts/target-area-readiness.md](contracts/target-area-readiness.md), and [quickstart.md](quickstart.md).

## Phase 1: Registry And Tests

- Update `_target_area` impact wording for materialized vs non-materialized target areas.
- Add registry tests for materialized target area readiness wording.

## Phase 2: Docs And Verification

- Update active Spec Kit pointer.
- Run prerequisite, lock, lint, type, registry, focused tests, full non-Docker, Docker-backed, and diff checks.

## Complexity Tracking

No constitution deviations are required.
