# Implementation Plan: Credentialed Session Runtime

**Branch**: `044-credentialed-session-runtime` | **Date**: 2026-05-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/044-credentialed-session-runtime/spec.md`

## Summary

Add a credentialed session runtime aggregate behind a session adapter port. The
slice composes live HTTP and browser snapshot prerequisite refs, credential use
audit refs, redacted session artifacts, redacted replay refs, and typed failure
gates for missing authorization, out-of-scope use, unsafe credential handling,
raw secret leakage, missing audit, missing redacted replay, and replay mismatch.

## Technical Context

**Language/Version**: Python 3.11+ with tests run on Python 3.12
**Primary Dependencies**: Pydantic; existing security/privacy contracts; pytest/ruff/mypy
**Storage**: Fixture output reports; no new database coupling
**Testing**: Contract, unit, integration fixture tests, registry validation, CLI loop, full gates
**Target Platform**: Python package and CLI
**Project Type**: Library/CLI
**Performance Goals**: Deterministic local fixture execution with bounded refs
**Constraints**: Core cannot import concrete session/browser/network/source adapters, browser engines, storage clients, model SDKs, or agent frameworks
**Scale/Scope**: Credentialed session aggregate plus seven fixtures
**VeraCrawl Owner Services**: fetch, policy, ports, runtime_events, review_replay, tests
**Canonical Contracts**: CredentialedSessionRuntimeReport, CredentialedSessionFixtureManifest, CredentialUseAudit
**Replay/Artifact Impact**: redacted artifacts, redacted replay, command/event/outbox, upstream report, and session adapter refs required for pass
**Security/Policy Impact**: authorization, credential scope, origin scope, redaction, raw secret, and replay gates are typed

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral.
- [x] Low coupling/high cohesion boundaries are explicit through ports and contracts.
- [x] Evidence/replay/artifact lineage is defined.
- [x] Security and credential gates are defined for unsafe session cases.
- [x] Fixtures and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Structure

```text
specs/044-credentialed-session-runtime/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/credentialed-session-runtime.md
├── quickstart.md
└── tasks.md

src/veracrawl/contracts/enums.py
src/veracrawl/contracts/security_privacy.py
src/veracrawl/ports/session.py
src/veracrawl/adapters/session/deterministic.py
src/veracrawl/fetch/credentialed_session.py
src/veracrawl/cli/credentialed_session.py
tests/fixtures/credentialed-session-*/
```

## Complexity Tracking

No constitution violations are introduced.
