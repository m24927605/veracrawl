# Implementation Plan: Real-World Benchmark Corpus Gate

**Branch**: `055-real-world-benchmark-corpus` | **Date**: 2026-05-03 | **Spec**: `specs/055-real-world-benchmark-corpus/spec.md`
**Input**: Feature specification from `/specs/055-real-world-benchmark-corpus/spec.md`

## Summary

Add a real-world benchmark corpus gate that runs authorized public URLs through
the existing live HTTP acquisition runtime, evaluates coarse external-site
oracles, enforces origin/robots/private-network safety, writes replayable
benchmark reports, and registers the feature as a post-release production
validation spec.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: Pydantic contracts, stdlib HTTP/robots parsing, existing live HTTP runtime  
**Storage**: Reference filesystem store under the selected output directory  
**Testing**: pytest, ruff, mypy, Spec Kit prerequisite checks, CLI live corpus run  
**Target Platform**: Python CLI/library  
**Project Type**: Single Python package with CLI entry point  
**Performance Goals**: one robots preflight and one read-only target GET per public corpus site; positive timeout and size budgets  
**Constraints**: no single-site scraper logic, no credential use, no browser side effects, no raw page bodies in events, no private-network targets  
**Scale/Scope**: first real external corpus gate supplementing 054 release gate  
**VeraCrawl Owner Services**: ops, fetch, policy, review_replay, tests  
**Canonical Contracts**: RealWorldBenchmarkCorpusManifest, RealWorldBenchmarkSiteSpec, RealWorldBenchmarkSiteObservation, RealWorldBenchmarkRunReport, LiveHttpAcquisitionReport  
**Replay/Artifact Impact**: aggregate reports require live HTTP report refs, artifact refs, content hashes, canonical URL refs, command/event/outbox refs, and replay bundle refs  
**Security/Policy Impact**: explicit allowlist, robots preflight, private-network denial, prompt-injection non-execution boundary, no credentials

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; no one-off scraper assumptions are introduced.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral; no model SDK or agent framework dependency is introduced.
- [x] Low coupling/high cohesion boundaries are explicit through contracts, runtime services, adapter ports, commands, events, and typed reports.
- [x] Evidence, verification, replay, and artifact lineage are defined for the benchmark report.
- [x] Security, policy, prompt-injection, privacy, and source scope boundaries are defined; credentials and export are out of scope.
- [x] Command/event payloads, fixture/oracle tests, negative tests, and replay checks are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

### Documentation

```text
specs/055-real-world-benchmark-corpus/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── real-world-benchmark-corpus.md
└── tasks.md
```

### Source Code

```text
src/veracrawl/contracts/real_world_benchmark.py
src/veracrawl/benchmarks/__init__.py
src/veracrawl/benchmarks/real_world.py
src/veracrawl/review_replay/real_world_benchmark.py
src/veracrawl/cli/real_benchmark.py

tests/contract/test_real_world_benchmark_contracts.py
tests/contract/test_real_world_benchmark_contract_registry.py
tests/contract/test_real_world_benchmark_import_boundaries.py
tests/unit/test_real_world_benchmark_runtime.py
tests/unit/test_real_world_benchmark_replay.py
tests/integration/test_real_world_benchmark_fixtures.py
tests/fixtures/real-world-public-corpus/
```

**Structure Decision**: add a benchmark package for real-world validation. The
core runtime composes existing live HTTP acquisition and injected ports; the CLI
owns manifest loading, stdlib adapter construction, live robots preflight, and
output writing.

## Complexity Tracking

No constitution violations.
