# Implementation Plan: Crawler Intelligence Optimization Roadmap

**Branch**: `080-crawler-intelligence-optimization` | **Date**: 2026-05-05 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/080-crawler-intelligence-optimization-roadmap/spec.md`

## Summary

Define and implement a finite post-079 optimization roadmap for crawler
intelligence. The roadmap establishes the activation sequence, contract
families, owner-service boundaries, and acceptance gates for specs 081-086; the
implementation materializes those gates through shared contracts, deterministic
runtime checks, CLI reports, fixtures, registry entries, and replay helpers.

## Technical Context

**Language/Version**: Python 3.x for implemented optimization specs  
**Primary Dependencies**: Existing VeraCrawl contracts, Pydantic models, ports,
runtime events, pytest, and Spec Kit artifacts  
**Storage**: Existing Postgres/object/queue/search/vector/graph abstractions
behind ports when activated by downstream specs  
**Testing**: pytest, contract tests, fixture/oracle tests, replay tests,
import-boundary tests, live/fixture benchmark gates  
**Target Platform**: VeraCrawl Python crawler runtime and CLI/benchmark gates  
**Project Type**: Python package with CLI benchmark/runtime surfaces  
**Performance Goals**: Future specs must reduce duplicate fetches, model tokens,
browser usage, and cost per successful result without reducing required
coverage or source-backed precision  
**Constraints**: General-purpose crawler only; no single-site scraper;
framework-neutral agents; source-backed evidence; no unsafe source access  
**Scale/Scope**: Optimization specs cover scheduler, normalize/browser,
extract/evidence/verify, graph/dedupe, publish/ranking, and ops/quality gates  
**VeraCrawl Owner Services**: scheduler, fetch, browser, normalize, extract,
evidence, verify, publish, graph, memory, agents, review_replay, ops,
artifact_lifecycle  
**Canonical Contracts**: Frontier score/priority/stop records, DOM intelligence
records, extractor attempt/confidence records, canonicalization/dedupe/identity
records, ranking records, optimization metric/release reports  
**Replay/Artifact Impact**: Every downstream optimization signal that affects
state or publication must include command/event/outbox refs, artifact refs,
content hashes, policy refs, trace refs when AI is used, and replay refs  
**Security/Policy Impact**: Preserve source scope, robots/terms, private-network
denial, credential isolation, prompt-taint labels, privacy lifecycle, retention,
and no-bypass controls

## Constitution Check

*GATE: Passed for roadmap planning. Re-check required when each downstream spec
is activated.*

- [x] General-purpose AI agent crawler capability is preserved; no one-off
  scraper assumptions are introduced.
- [x] Python remains the implementation language unless a constitution
  amendment changes it.
- [x] Agent runtime remains framework-neutral; model SDKs and agent frameworks
  are isolated behind replaceable adapters.
- [x] Low coupling/high cohesion boundaries are explicit through ports,
  commands, events, typed results, and owner services.
- [x] Evidence, verification, publication, replay, and artifact lineage are
  defined for affected outputs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle,
  retention, and export/withdrawal gates are defined where applicable.
- [x] Command payload schemas, event payload schemas, state transitions,
  fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint
  pressure, or delivery speed.

## Project Structure

### Documentation

```text
specs/080-crawler-intelligence-optimization-roadmap/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
└── contracts/
    └── crawler-intelligence-optimization-roadmap.md

specs/081-focused-frontier-scoring/
└── spec.md
specs/082-dom-page-understanding/
└── spec.md
specs/083-extractor-fallback-confidence/
└── spec.md
specs/084-canonical-dedupe-identity/
└── spec.md
specs/085-recommendation-ranking-runtime/
└── spec.md
specs/086-cost-recovery-evaluation-gates/
└── spec.md
```

### Source Code

The implementation uses the existing package map:

```text
src/veracrawl/contracts/
src/veracrawl/scheduler/
src/veracrawl/fetch/
src/veracrawl/browser/
src/veracrawl/normalize/
src/veracrawl/extract/
src/veracrawl/evidence/
src/veracrawl/verify/
src/veracrawl/publish/
src/veracrawl/graph/
src/veracrawl/memory/
src/veracrawl/agents/
src/veracrawl/ops/
src/veracrawl/benchmarks/
src/veracrawl/cli/
tests/contract/
tests/unit/
tests/integration/
tests/fixtures/
```

## Implementation Closure

- `src/veracrawl/contracts/crawler_optimization.py` defines all 081-086 data
  contracts.
- `src/veracrawl/benchmarks/crawler_optimization.py` implements focused
  frontier scoring, DOM pruning/ranking, extractor fallback, canonicalization,
  SimHash/MinHash identity, duplicate suppression, recommendation ranking, and
  optimization metrics.
- `src/veracrawl/cli/crawler_optimization.py` exposes
  `veracrawl-crawler-optimization`.
- `src/veracrawl/review_replay/crawler_optimization.py` implements replay gap
  detection.
- `tests/fixtures/crawler-optimization-*` cover success and required negative
  cases.

**Structure Decision**: Spec 080 remains the roadmap/control artifact. Specs
081-086 are implemented through shared contracts, runtime gate, CLI, fixtures,
and tests; future extensions should keep their own plan/tasks artifacts before
additional runtime changes.

## Complexity Tracking

No constitution violations are introduced by this roadmap.
