# Implementation Plan: Browser Snapshot Runtime

**Branch**: `043-browser-snapshot-runtime` | **Date**: 2026-05-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/043-browser-snapshot-runtime/spec.md`

## Summary

Add a browser snapshot runtime aggregate that captures JavaScript-required page
observations through `BrowserSourceAdapterPort`, records DOM/screenshot/network
trace/console/timing/budget refs, preserves upstream 041/042 refs, and fails
typed negative cases for policy, egress, unsafe interaction, budget,
prompt-taint, missing artifact, and replay mismatch.

## Technical Context

**Language/Version**: Python 3.11+ with tests run on Python 3.12  
**Primary Dependencies**: Pydantic; existing browser/network/source ports; pytest/ruff/mypy  
**Storage**: Fixture output reports; no new database coupling  
**Testing**: Contract, unit, integration fixture tests, registry validation, CLI loop, full gates  
**Target Platform**: Python package and CLI  
**Project Type**: Library/CLI  
**Performance Goals**: Deterministic fixture snapshot execution with bounded local artifacts  
**Constraints**: Core cannot import concrete browser/network/source adapters, browser engines, storage clients, model SDKs, or agent frameworks  
**Scale/Scope**: Browser snapshot aggregate plus seven fixtures  
**VeraCrawl Owner Services**: browser, fetch, ports, runtime_events, review_replay, tests  
**Canonical Contracts**: BrowserSnapshotRuntimeReport, BrowserSnapshotFixtureManifest, BrowserSandboxPolicy, BrowserInteractionStep, NetworkAcquisitionReport  
**Replay/Artifact Impact**: DOM, screenshot, network trace, console, timing, budget, command, event cursor, outbox, upstream report, and replay refs required for pass  
**Security/Policy Impact**: sandbox, egress, side-effect, budget, and prompt-taint gates are typed and deterministic

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; no one-off scraper assumptions are introduced.
- [x] Python remains the implementation language unless a constitution amendment changes it.
- [x] Agent runtime remains framework-neutral; model SDKs and agent frameworks are isolated behind replaceable adapters.
- [x] Low coupling/high cohesion boundaries are explicit through ports, commands, events, typed results, and owner services.
- [x] Evidence, verification, publication, replay, and artifact lineage are defined for affected outputs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and export/withdrawal gates are defined where applicable.
- [x] Command payload schemas, event payload schemas, state transitions, fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Structure

```text
specs/043-browser-snapshot-runtime/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/browser-snapshot-runtime.md
├── quickstart.md
└── tasks.md

src/veracrawl/contracts/enums.py
src/veracrawl/contracts/browser.py
src/veracrawl/browser/snapshot_runtime.py
src/veracrawl/adapters/browser/deterministic.py
src/veracrawl/cli/browser_snapshot.py
tests/fixtures/browser-snapshot-*/
```

## Complexity Tracking

No constitution violations are introduced.
