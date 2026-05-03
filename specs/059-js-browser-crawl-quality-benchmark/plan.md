# Implementation Plan: JavaScript Browser Crawl Quality Benchmark

**Branch**: `059-js-browser-crawl-quality-benchmark` | **Date**: 2026-05-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/059-js-browser-crawl-quality-benchmark/spec.md`

## Summary

Implement the row 059 browser quality benchmark by comparing HTTP-only evidence
against browser-rendered evidence for manifest-declared JS-required targets.
The benchmark records recovered oracle fragments, DOM/screenshot/network/
console/timing artifacts, content hashes, source anchors, browser cost metrics,
policy refs, command/event/outbox refs, and replay refs. Browser engines remain
adapter-owned; the core benchmark depends only on VeraCrawl contracts and the
browser/network ports.

## Technical Context

**Language/Version**: Python 3.12 for validation; package supports Python >= 3.11
**Primary Dependencies**: Pydantic, existing live HTTP/runtime contracts, optional Playwright behind `veracrawl.adapters.browser.playwright`
**Storage**: Reference persistence store for benchmark command/event/outbox refs
**Testing**: pytest, ruff, mypy, registry validation, focused/full/Docker-backed pytest, live browser CLI run
**Target Platform**: CLI/library runtime
**Project Type**: Python package with contracts, browser benchmark runtime, adapter-owned browser engine integration, CLI, fixtures, tests
**Performance Goals**: browser quality fixture runs use one HTTP-only fetch and one read-only browser observation per target; live validation uses conservative timeout and request budgets
**Constraints**: no single-site scraper code; no credentialed browsing; no CAPTCHA, stealth, WAF evasion, arbitrary clicking, form submission, or policy bypass; core imports no Playwright/browser engine
**Scale/Scope**: at least 8 browser-required targets in the quality profile
**VeraCrawl Owner Services**: browser, fetch, ops, runtime_events, review_replay, tests
**Canonical Contracts**: `BrowserQualityCorpusManifest`, `BrowserQualityTargetSpec`, `BrowserQualityObservation`, `BrowserQualityDeltaRecord`, `BrowserQualityReport`, existing `BrowserSandboxPolicy`, `BrowserInteractionStep`, network/source command/event contracts
**Replay/Artifact Impact**: passing observations require DOM, screenshot, network, console, timing, artifact, content hash, source anchor, command/event/outbox, and replay refs
**Security/Policy Impact**: browser sandbox, read-only action class, egress allowlist, prompt-taint boundary refs, budget refs, private-network denial, and replay checks are mandatory

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; browser quality is manifest-driven, not site-specific scraper logic.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral; this spec does not add agent framework or model SDK coupling.
- [x] Low coupling/high cohesion boundaries are explicit through contracts, ports, adapters, commands, events, typed results, and owner services.
- [x] Evidence, verification, publication, replay, and artifact lineage are defined; this benchmark produces quality reports, not published extracted outputs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and browser sandbox gates are defined.
- [x] Command payload schemas, event payload schemas, fixture/oracle tests, negative tests, replay tests, and import-boundary tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

```text
specs/059-js-browser-crawl-quality-benchmark/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── js-browser-crawl-quality-benchmark.md
└── tasks.md

src/veracrawl/
├── adapters/browser/
│   └── playwright.py
├── benchmarks/
│   └── browser_quality.py
├── cli/
│   └── browser_quality.py
├── contracts/
│   ├── browser_quality.py
│   ├── enums.py
│   ├── registry.py
│   └── __init__.py
├── ports/
│   └── browser.py
└── review_replay/
    └── browser_quality.py

tests/
├── contract/
│   ├── test_browser_quality_contracts.py
│   ├── test_browser_quality_contract_registry.py
│   └── test_browser_quality_import_boundaries.py
├── unit/
│   ├── test_browser_quality_runtime.py
│   └── test_browser_quality_replay.py
├── integration/
│   └── test_browser_quality_fixtures.py
└── fixtures/
    ├── browser-quality-corpus/
    ├── browser-quality-unsafe-action/
    ├── browser-quality-prompt-taint/
    ├── browser-quality-missing-artifact/
    ├── browser-quality-budget-exceeded/
    └── browser-quality-replay-mismatch/
```

**Structure Decision**: Keep benchmark composition in `veracrawl.benchmarks`,
contracts in `veracrawl.contracts`, replay checks in `veracrawl.review_replay`,
CLI orchestration in `veracrawl.cli`, and concrete browser engine integration in
`veracrawl.adapters.browser`. Core benchmark modules must not import Playwright
or any other browser engine.

## Complexity Tracking

No constitution violations.
