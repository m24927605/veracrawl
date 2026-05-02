# Implementation Plan: VeraCrawl Security Privacy Lifecycle Gate

**Branch**: `023-security-privacy-lifecycle-gate` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/023-security-privacy-lifecycle-gate/spec.md`

## Summary

Implement a backend/vendor-neutral target security/privacy lifecycle gate. The gate adds canonical contracts, validation runtime, CLI fixtures, registry entries, docs, and tests proving unsafe access paths are blocked, raw secrets never serialize, lifecycle changes propagate to projections, redacted replay remains complete, and policy refs alone cannot claim target security readiness.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: existing project dependencies only
**Storage**: deterministic fixture reports and existing `.veracrawl-test-runs/`; production stores remain adapter-owned
**Testing**: pytest, ruff, mypy, registry validation, CLI fixtures, import-boundary tests, full pytest
**Target Platform**: local/CI Python runtime
**Project Type**: Python package and CLI
**Performance Goals**: deterministic fixture evaluation inside normal integration test timeouts
**Constraints**: core imports no browser/model/agent framework/cloud/security vendor SDKs; pass requires canonical refs and zero leakage; policy-only cannot pass
**Scale/Scope**: success, policy-only, and negative fixtures for unsafe network, prompt injection, credential leakage, lifecycle, legal hold, projection cleanup, replay, and observability gaps
**VeraCrawl Owner Services**: `policy`, `artifact_lifecycle`, `ops`, `review_replay`, `runtime_support`, `contracts`, `tests`
**Canonical Contracts**: `SecurityPolicyCheck`, `CredentialUseAudit`, `PromptTaintBoundary`, `ArtifactLifecycleAction`, `ProjectionCleanupRecord`, `SecurityPrivacyReport`, `SecurityPrivacyFixtureManifest`, `FailureRecord`, `RecoveryAction`, `ObservabilityReport`
**Replay/Artifact Impact**: passing reports require lifecycle action refs, projection cleanup refs, redaction refs, replay bundle refs, command/event/outbox refs, and observability refs
**Security/Policy Impact**: all security/privacy surfaces are blocking acceptance gates; raw secret leakage is a fail

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
specs/023-security-privacy-lifecycle-gate/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
├── checklists/
└── tasks.md

src/veracrawl/
├── cli/security_privacy.py
├── contracts/security_privacy.py
├── contracts/enums.py
├── contracts/registry.py
└── runtime_support/security_privacy.py

tests/
├── contract/
├── fixtures/
├── helpers/
├── integration/
└── unit/
```

**Structure Decision**: Add cohesive security/privacy contracts in a new `contracts.security_privacy` module, keep gate logic in `runtime_support.security_privacy`, and expose deterministic fixture execution through `veracrawl-security-privacy`.

## Complexity Tracking

No constitution violations.
