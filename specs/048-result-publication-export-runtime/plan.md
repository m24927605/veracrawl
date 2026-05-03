# Implementation Plan: Result Publication And Export Runtime

**Branch**: `048-result-publication-export-runtime` | **Date**: 2026-05-03 | **Spec**: `specs/048-result-publication-export-runtime/spec.md`
**Input**: Feature specification from `/specs/048-result-publication-export-runtime/spec.md`

## Summary

Implement the row 048 runtime gate that consumes row 047 live evidence results
and materializes published outputs, output manifests, Result API snapshots,
destination-neutral local export records, delivery receipts, withdrawal refs,
correction refs, and replay refs. The core runtime composes existing
publication/export contracts and helpers behind explicit inputs; concrete live
HTTP/browser/source setup remains in the CLI prerequisite layer.

## Technical Context

**Language/Version**: Python 3.12 validation, package supports Python >=3.11  
**Primary Dependencies**: pydantic, existing VeraCrawl contracts/runtime helpers  
**Storage**: No concrete storage in core; deterministic refs and fixture artifacts  
**Testing**: pytest, ruff, mypy, Spec Kit prerequisite checks, Docker-backed pytest gate  
**Target Platform**: Python CLI/runtime package  
**Project Type**: single Python package  
**Performance Goals**: fixture CLI loop completes under deterministic test thresholds  
**Constraints**: general-purpose AI agent crawler, low coupling/high cohesion, core does not import concrete source/browser/model/agent/storage/export adapters  
**Scale/Scope**: target-architecture slice for publication/export gate, not a single-site scraper  
**VeraCrawl Owner Services**: publish, export, evidence, verify, review_replay, tests  
**Canonical Contracts**: PublishedOutput, OutputManifest, PublicationReport, ResultApiSnapshot, ExportTargetSpec, ExportJob, ExportAttempt, ExportDeliveryReceipt, ExportWithdrawalJob, ExportWithdrawalAttempt, ExportCorrectionRecord, ExportReconciliationReport, ResultPublicationExportRuntimeReport  
**Replay/Artifact Impact**: published result artifacts, Result API response artifact/hash, export receipts, withdrawal/correction refs, command/event/outbox refs, replay bundle refs  
**Security/Policy Impact**: publication policy, export policy, privacy lifecycle propagation, withdrawal/correction propagation

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
specs/048-result-publication-export-runtime/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/result-publication-export-runtime.md
├── quickstart.md
└── tasks.md

src/veracrawl/contracts/{publication.py,enums.py,registry.py}
src/veracrawl/publish/result_runtime.py
src/veracrawl/cli/result_publication.py
tests/contract/test_result_publication_export_contracts.py
tests/unit/test_result_publication_export_runtime.py
tests/integration/test_result_publication_export_fixtures.py
tests/fixtures/result-publication-*/
```

**Structure Decision**: extend existing publication/export owners and add a
small orchestration aggregate under `publish/` because row 048 is a publication
gate that also creates export records.

## Complexity Tracking

No constitution violations.
