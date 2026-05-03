# Implementation Plan: Field-Level Oracle Extraction Benchmark

**Branch**: `061-field-level-oracle-extraction-benchmark` | **Date**: 2026-05-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/061-field-level-oracle-extraction-benchmark/spec.md`

## Summary

Implement row 061 as a schema-driven field oracle benchmark. The benchmark
evaluates generated or explicit schema/field oracle manifests, records one
field evaluation per expected value, requires source anchors/artifacts/content
hashes/evidence packets/verification refs for every accepted field, rejects
LLM-only evidence, and emits field-level JSON suitable for row 062 precision and
recall metrics. Runtime code must stay general-purpose and cannot become a
single-site extractor.

## Technical Context

**Language/Version**: Python 3.12 for validation; package supports Python >= 3.11  
**Primary Dependencies**: Pydantic and existing VeraCrawl persistence/runtime contracts  
**Storage**: Reference persistence store for command/event/outbox/canonical refs  
**Testing**: pytest, ruff, mypy, registry validation, focused/full/Docker-backed pytest, CLI validation  
**Target Platform**: CLI/library runtime  
**Project Type**: Python package with contracts, benchmark runtime, replay helpers, CLI, fixtures, tests  
**Performance Goals**: quality fixture evaluates at least 8 schemas and 200 expected fields in local test budget  
**Constraints**: no website-specific scraper logic; no LLM output, graph memory, screenshot-only evidence, or framework-native state can satisfy source evidence; no direct publication bypass  
**Scale/Scope**: at least 8 schemas, 200 expected fields, typed negative fixtures for wrong value, missing anchor, schema violation, stale evidence, direct publication, and LLM-as-evidence  
**VeraCrawl Owner Services**: extract, evidence, verify, publish, agents, policy, runtime_events, review_replay, tests  
**Canonical Contracts**: `FieldOracleSchema`, `FieldOracleFieldSpec`, `ExpectedFieldValue`, `FieldEvaluationRecord`, `FieldOracleBenchmarkReport`, `FieldOracleBenchmarkManifest`  
**Replay/Artifact Impact**: accepted field evaluations require normalized value refs, source anchors, artifacts, content hashes, evidence packet refs, verification refs, command/event/outbox refs, and replay refs  
**Security/Policy Impact**: prompt-taint, privacy, retention, stale evidence, publication gate, credential, and source-evidence boundaries are explicit

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; extraction quality is schema-driven, not single-site scraper logic.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral; model refs are proposal context only and never source evidence.
- [x] Low coupling/high cohesion boundaries are explicit through contracts, benchmark runtime, replay helpers, CLI, and registry wiring.
- [x] Evidence, verification, publication, replay, and artifact lineage are defined for field-level outputs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and publication/export gates are defined.
- [x] Command payload schemas, event payload schemas, fixture/oracle tests, negative tests, replay tests, and import-boundary tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

```text
specs/061-field-level-oracle-extraction-benchmark/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── field-level-oracle-extraction-benchmark.md
└── tasks.md

src/veracrawl/
├── benchmarks/
│   └── field_oracle.py
├── cli/
│   └── field_oracle.py
├── contracts/
│   ├── field_oracle.py
│   ├── enums.py
│   ├── registry.py
│   └── __init__.py
└── review_replay/
    └── field_oracle.py

tests/
├── contract/
│   ├── test_field_oracle_contracts.py
│   ├── test_field_oracle_contract_registry.py
│   └── test_field_oracle_import_boundaries.py
├── unit/
│   ├── test_field_oracle_runtime.py
│   └── test_field_oracle_replay.py
├── integration/
│   └── test_field_oracle_fixtures.py
└── fixtures/
    ├── field-oracle-quality-corpus/
    ├── field-oracle-wrong-value/
    ├── field-oracle-missing-anchor/
    ├── field-oracle-schema-violation/
    ├── field-oracle-stale-evidence/
    ├── field-oracle-publication-bypass/
    └── field-oracle-llm-as-evidence/
```

**Structure Decision**: Keep field oracle data contracts in
`veracrawl.contracts`, deterministic benchmark execution in
`veracrawl.benchmarks`, replay checks in `veracrawl.review_replay`, and CLI
orchestration in `veracrawl.cli`. Core field oracle modules import no model SDK,
agent framework, browser engine, HTTP client, or site-specific scraper module.

## Complexity Tracking

No constitution violations.
