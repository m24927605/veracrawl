# Implementation Plan: VeraCrawl Normalize and Extract Plane

**Branch**: `006-normalize-extract-plane` | **Date**: 2026-05-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-normalize-extract-plane/spec.md`

## Summary

Implement deterministic raw HTML normalization, anchor mapping, link provenance, page type classification, site model, extraction strategy, and anchored candidate creation on top of the completed network acquisition runtime. The implementation preserves raw-to-normalized-to-candidate replay lineage and does not allow candidates to become published outputs.

## Technical Context

**Language/Version**: Python 3.11+; local validation uses Python 3.12.  
**Primary Dependencies**: Existing dependencies only: Pydantic v2, pytest, ruff, mypy, and Python standard-library HTML parsing.  
**Storage**: Artifact refs and deterministic fixture reports only. Production storage remains out of scope.  
**Testing**: pytest contract, unit, integration, replay, fixture/oracle, negative, registry, import-boundary, and CLI validation.  
**Target Platform**: Python package and deterministic CLI/test harness.  
**Project Type**: Python library plus deterministic fixture runner.  
**Performance Goals**: Full local normalize/extract gate completes within 30 seconds; success fixtures report zero missing process replay refs.  
**Constraints**: No site-specific selectors; no publication from candidates; no model SDK or agent framework coupling.  
**Scale/Scope**: Static HTML normalization, link provenance, page classification, site model, heuristic anchored candidate fixtures, and negative fixtures for missing raw, empty content, and missing anchor.  
**VeraCrawl Owner Services**: `normalize`, `extract`, `fetch`, `review_replay`, `policy`, `contracts`, and `tests` are directly affected.  
**Canonical Contracts**: NormalizedDocument, NormalizationManifest, TextAnchor, AnchorMap, LinkProvenance, PageTypeClassification, SiteModel, ExtractionStrategy, ExtractionCandidate, NormalizeExtractReport, NetworkAcquisitionReport.  
**Replay/Artifact Impact**: Replay requires network acquisition refs, raw artifact refs, normalized artifact refs, anchor map refs, manifest refs, link refs, classification refs, site model refs, strategy refs, candidate refs, policy refs, and command/event/outbox refs.  
**Security/Policy Impact**: Untrusted source HTML remains untrusted; candidates are not evidence or published outputs; prompt injection text is not sent to models in this slice.

## Constitution Check

*GATE: Passed before Phase 0 research. Re-check after Phase 1 design.*

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
specs/006-normalize-extract-plane/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── normalization.md
│   ├── link-site-model.md
│   ├── extraction-candidate.md
│   └── fixture-oracle.md
└── tasks.md

src/veracrawl/
├── contracts/processing.py
├── normalize/pipeline.py
├── extract/candidates.py
├── review_replay/processing.py
└── cli/process.py

tests/
├── contract/test_process_contract_registry.py
├── contract/test_process_contracts.py
├── contract/test_process_import_boundaries.py
├── unit/test_normalization_pipeline.py
├── unit/test_extraction_candidate_guards.py
├── unit/test_process_replay.py
└── integration/test_process_fixtures.py
```

**Structure Decision**: Extend existing `processing.py` contracts and add cohesive normalize/extract/replay/CLI modules. Local network acquisition remains in the previous slice and is reused through its public runtime/CLI boundaries.

## Phase 0: Research

See [research.md](research.md).

## Phase 1: Design And Contracts

See [data-model.md](data-model.md), [contracts/](contracts/), and [quickstart.md](quickstart.md).

## Post-Design Constitution Check

- [x] Normalization and extraction are generic and do not encode a site.
- [x] Candidates remain unpublished and are not evidence.
- [x] Replay refs are required for raw, normalized, anchors, links, strategy, and candidate records.
- [x] Negative fixture/oracle coverage is defined before implementation.
- [x] No constitution violation or justified complexity exception is present.

## Complexity Tracking

No constitution violations are introduced. No complexity exception is required.
