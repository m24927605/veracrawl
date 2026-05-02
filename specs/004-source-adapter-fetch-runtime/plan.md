# Implementation Plan: VeraCrawl Source Adapter and Fetch Runtime

**Branch**: `004-source-adapter-fetch-runtime` | **Date**: 2026-05-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-source-adapter-fetch-runtime/spec.md`

## Summary

Implement a deterministic source acquisition runtime on top of the durable scheduler foundation. The feature adds typed source acquisition contracts, deterministic source adapter fixtures for HTTP, sitemap, RSS, API-like, and document-source families, source policy gates, raw artifact preservation, scheduler frontier-to-source command flow, retry/rate-limit/failure handling, and durable replay recovery validation.

The implementation remains adapter-neutral: no production network client, browser, storage, queue, model SDK, agent framework, or site-specific scraper enters core packages.

## Technical Context

**Language/Version**: Python 3.11+; local validation uses Python 3.12.  
**Primary Dependencies**: Existing dependencies only: Pydantic v2, pytest, ruff, mypy, and standard-library protocols/data structures.  
**Storage**: Existing deterministic durable fixture store and artifact refs behind ports. Production storage and network adapters remain out of scope.  
**Testing**: pytest contract, unit, integration, replay, fixture/oracle, negative, registry, import-boundary, and CLI validation.  
**Target Platform**: Python package and deterministic CLI/test harness.  
**Project Type**: Python library plus deterministic fixture runner.  
**Performance Goals**: Full local source-adapter gate completes within 30 seconds; successful source fixtures report zero missing source replay refs.  
**Constraints**: Core must not import concrete browser, storage, queue, model SDK, agent framework, network client, or site-specific modules. Source mutations require source policy refs, scheduler lease refs, durable command/event/outbox refs, and raw artifact refs.  
**Scale/Scope**: Deterministic adapters for HTTP, sitemap, RSS, API-like, and document-source families; negative fixtures for blocked source, rate-limited, adapter mismatch, malformed response, retry exhausted, and missing raw artifact. Production HTTP/browser adapters, JS rendering, auth flows, graph/memory/export intelligence, and production scale are not implemented.  
**VeraCrawl Owner Services**: `fetch`, `scheduler`, `runtime_events`, `artifact_lifecycle`, `review_replay`, `policy`, `ports`, `contracts`, and `ops` are directly affected.  
**Canonical Contracts**: FetchAttempt, FetchResult, PageSnapshot, DocumentArtifact, RateLimitDecision, SourceFailureReport, SourceAcquisitionReport, SourceAdapterCommand, SourceAdapterResult, RuntimeArtifactRef, DurableCommandRecord, OutboxRecord, EventCursorRecord, FrontierItem, QueueLease, DurableReplayRecoveryReport.  
**Replay/Artifact Impact**: Source replay requires source adapter result refs, fetch attempt/result refs, raw artifact refs, artifact hash/digest refs, command records, command results, event cursors, outbox refs, policy decisions, frontier item refs, lease refs, deterministic clock refs, and recovery report refs.  
**Security/Policy Impact**: Source scope, robots/terms/customer authorization, credential scope, rate limit, retry budget, malformed response, blocked-source, artifact privacy lifecycle, and retention gates must be typed and operator-visible.

## Constitution Check

*GATE: Passed before Phase 0 research. Re-checked after Phase 1 design.*

- [x] General-purpose AI agent crawler capability is preserved; no one-off scraper assumptions are introduced.
- [x] Python remains the implementation language unless a constitution amendment changes it.
- [x] Agent runtime remains framework-neutral; model SDKs and agent frameworks are isolated behind replaceable adapters.
- [x] Low coupling/high cohesion boundaries are explicit through ports, commands, events, typed results, and owner services.
- [x] Evidence, verification, publication, replay, and artifact lineage are defined for affected outputs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and export/withdrawal gates are defined where applicable.
- [x] Command payload schemas, event payload schemas, state transitions, fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

### Documentation (this feature)

```text
specs/004-source-adapter-fetch-runtime/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── source-acquisition.md
│   ├── adapter-runtime.md
│   ├── failure-policy.md
│   └── fixture-oracle.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
└── veracrawl/
    ├── contracts/
    │   ├── fetch.py              # FetchAttempt, FetchResult, PageSnapshot, DocumentArtifact
    │   ├── source_runtime.py     # RateLimitDecision, SourceFailureReport, SourceAcquisitionReport
    │   └── registry.py
    ├── ports/
    │   └── source_adapter.py     # Existing SourceAdapterPort remains the boundary
    ├── fetch/
    │   └── acquisition.py        # Generic source acquisition runtime
    ├── adapters/
    │   └── sources/
    │       └── deterministic.py  # Deterministic source adapter fixtures
    ├── review_replay/
    │   └── source.py             # Source acquisition replay validation
    └── cli/
        └── source.py             # Deterministic source fixture runner

tests/
├── contract/
│   ├── test_source_acquisition_contract_registry.py
│   ├── test_source_adapter_runtime_contracts.py
│   └── test_source_adapter_import_boundaries.py
├── unit/
│   ├── test_source_policy_and_retry_gates.py
│   └── test_source_replay_recovery.py
├── integration/
│   ├── test_source_acquisition_runtime.py
│   └── test_source_negative_fixtures.py
└── fixtures/
    ├── source-http-success/
    ├── source-sitemap-success/
    ├── source-rss-success/
    ├── source-api-success/
    ├── source-document-success/
    ├── source-blocked/
    ├── source-rate-limited/
    ├── source-adapter-mismatch/
    ├── source-malformed-response/
    ├── source-retry-exhausted/
    └── source-missing-artifact/
```

**Structure Decision**: Extend the existing single Python package. Core source acquisition behavior lives in `fetch/acquisition.py`; deterministic fixtures live under `adapters/sources` and test fixtures; replay validation lives under `review_replay`. Concrete production adapters remain future work.

## Phase 0: Research

Phase 0 decisions are captured in [research.md](research.md). The core choices are:

- Use deterministic source adapters to prove source family semantics.
- Preserve raw artifacts through `RuntimeArtifactRef` rather than adapter-native objects.
- Use source acquisition reports to connect source, scheduler, durable, policy, and replay refs.
- Treat blocked source, rate limit, malformed response, adapter mismatch, retry exhausted, and missing artifact as typed non-success outcomes.

## Phase 1: Design And Contracts

Phase 1 design artifacts are:

- [data-model.md](data-model.md): source acquisition entities, validation rules, and transitions.
- [contracts/source-acquisition.md](contracts/source-acquisition.md): fetch attempt/result, page snapshot, document artifact, raw artifact behavior.
- [contracts/adapter-runtime.md](contracts/adapter-runtime.md): source adapter execution and natural result type validation.
- [contracts/failure-policy.md](contracts/failure-policy.md): source policy, rate limit, retry, malformed response, blocked source, and mismatch behavior.
- [contracts/fixture-oracle.md](contracts/fixture-oracle.md): success and negative fixture/oracle requirements.
- [quickstart.md](quickstart.md): expected validation flow.

## Post-Design Constitution Check

- [x] Deterministic adapters are general source-family fixtures, not single-site scrapers.
- [x] Core depends only on contracts, ports, commands, events, policy, scheduler refs, artifact refs, and replay.
- [x] Source policy and replay failure gates are blocking.
- [x] Negative fixture/oracle coverage is defined before implementation.
- [x] No constitution violation or justified complexity exception is present.

## Complexity Tracking

No constitution violations are introduced. No complexity exception is required.
