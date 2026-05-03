# Implementation Plan: Multi-Page Deep Crawl Frontier Benchmark

**Branch**: `060-multi-page-deep-crawl-frontier-benchmark` | **Date**: 2026-05-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/060-multi-page-deep-crawl-frontier-benchmark/spec.md`

## Summary

Implement the row 060 deep crawl benchmark as a bounded, manifest-driven crawl
frontier runtime. The benchmark crawls fixture/public-style site graphs across
pagination, listing/detail pages, sitemap/feed entries, canonical duplicates,
robots-denied links, off-origin links, and stop conditions. It records frontier
decisions, page observations, graph/link provenance refs, optional AI/graph/
memory priority influence refs, policy refs, command/event/outbox refs, and
replay bundle refs. The runtime must stay general-purpose and may not embed
single-site URL or DOM rules.

## Technical Context

**Language/Version**: Python 3.12 for validation; package supports Python >= 3.11  
**Primary Dependencies**: Pydantic and existing VeraCrawl persistence/runtime contracts  
**Storage**: Reference persistence store for command/event/outbox/canonical refs  
**Testing**: pytest, ruff, mypy, registry validation, focused/full/Docker-backed pytest, CLI validation  
**Target Platform**: CLI/library runtime  
**Project Type**: Python package with contracts, benchmark runtime, replay helpers, CLI, fixtures, tests  
**Performance Goals**: quality fixture covers at least 5 bounded sites and 50 pages in under local fixture budget; no live unbounded discovery  
**Constraints**: no single-site scraper logic; no credentialed crawling; no CAPTCHA, stealth, WAF evasion, unsafe browser actions, or policy bypass; AI traces are decision context only and never source evidence  
**Scale/Scope**: at least 5 bounded sites, 50 required pages, duplicate/off-origin/robots/infinite-pagination/replay negative fixtures  
**VeraCrawl Owner Services**: fetch, graph, memory, agents, policy, runtime_events, review_replay, tests  
**Canonical Contracts**: `DeepCrawlQualityManifest`, `DeepCrawlSiteSpec`, `DeepCrawlPageSpec`, `FrontierDecisionTrace`, `DeepCrawlPageObservation`, `DeepCrawlStopReasonRecord`, `DeepCrawlQualityReport`  
**Replay/Artifact Impact**: passing decisions and pages require command/event/outbox, policy, graph/link provenance, artifact/hash/source anchor, and replay refs  
**Security/Policy Impact**: depth, page count, origin scope, robots, rate budget, private-network denial, browser budget, prompt-taint, and retry boundaries gate frontier expansion

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; the crawl graph is manifest-driven and not tied to a single website.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral; AI/agent influence is represented by VeraCrawl trace refs, not framework SDK state.
- [x] Low coupling/high cohesion boundaries are explicit through contracts, benchmark runtime, replay helpers, CLI, and registry wiring.
- [x] Evidence, verification, publication, replay, and artifact lineage are defined; this benchmark produces crawl quality reports, not extracted publications.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and crawl budget gates are defined.
- [x] Command payload schemas, event payload schemas, fixture/oracle tests, negative tests, replay tests, and import-boundary tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

```text
specs/060-multi-page-deep-crawl-frontier-benchmark/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── multi-page-deep-crawl-frontier-benchmark.md
└── tasks.md

src/veracrawl/
├── benchmarks/
│   └── deep_crawl.py
├── cli/
│   └── deep_crawl.py
├── contracts/
│   ├── deep_crawl.py
│   ├── enums.py
│   ├── registry.py
│   └── __init__.py
└── review_replay/
    └── deep_crawl.py

tests/
├── contract/
│   ├── test_deep_crawl_contracts.py
│   ├── test_deep_crawl_contract_registry.py
│   └── test_deep_crawl_import_boundaries.py
├── unit/
│   ├── test_deep_crawl_runtime.py
│   └── test_deep_crawl_replay.py
├── integration/
│   └── test_deep_crawl_fixtures.py
└── fixtures/
    ├── deep-crawl-quality-corpus/
    ├── deep-crawl-duplicate-loop/
    ├── deep-crawl-off-origin-pollution/
    ├── deep-crawl-robots-denied/
    ├── deep-crawl-budget-exhausted/
    ├── deep-crawl-infinite-pagination/
    └── deep-crawl-replay-mismatch/
```

**Structure Decision**: Keep contracts in `veracrawl.contracts`, deterministic
frontier execution in `veracrawl.benchmarks`, replay inspection in
`veracrawl.review_replay`, and CLI orchestration in `veracrawl.cli`. The core
runtime imports no browser engines, model SDKs, agent frameworks, HTTP clients,
or site-specific scraper modules.

## Complexity Tracking

No constitution violations.
