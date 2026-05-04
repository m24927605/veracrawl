# Implementation Plan: Query Product Discovery And Offer Ranking

**Branch**: `079-query-product-discovery` | **Date**: 2026-05-04 |
**Spec**: `specs/079-query-product-discovery/spec.md`

## Summary

Add a query-driven discovery benchmark that starts from search/listing entry
pages, discovers product candidate URLs from source-backed artifacts, composes
those URLs into the existing product availability runtime, and writes ranked
offer artifacts. This closes the manual product URL seed gap without adding
site-specific scraper code.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Pydantic, pytest, existing VeraCrawl ports/adapters
**Storage**: Local JSON artifacts through `ReferencePersistenceStore`
**Testing**: pytest, ruff, mypy, registry validation
**Target Platform**: CLI/library runtime
**Project Type**: Python package + CLI
**Performance Goals**: Bounded by manifest candidate limits; no unbounded crawl
**Constraints**: No manual product target URLs, no framework coupling, no
LLM-as-evidence, no bypass behavior
**Scale/Scope**: Initial query runs over declared search/listing entry pages
and bounded candidate pages
**VeraCrawl Owner Services**: fetch, agents, extract, evidence, projection,
ops, tests
**Canonical Contracts**: Product discovery contracts, product availability
contracts, offer projection contracts, model/agent/tool/context traces,
command/event/outbox refs, replay refs
**Replay/Artifact Impact**: Search page artifacts/content hashes and candidate
source anchors are replay-critical; composed product availability/offer
projection refs are retained.
**Security/Policy Impact**: Robots, origin scope, prompt taint, private-network
denial, and no-bypass source policy apply.

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; no one-off
  scraper assumptions are introduced.
- [x] Python remains the implementation language.
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

```text
specs/079-query-product-discovery/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md

src/veracrawl/contracts/product_discovery.py
src/veracrawl/benchmarks/product_discovery.py
src/veracrawl/cli/product_discovery.py

tests/contract/test_product_discovery_contracts.py
tests/contract/test_product_discovery_contract_registry.py
tests/contract/test_product_discovery_import_boundaries.py
tests/unit/test_product_discovery_runtime.py
tests/integration/test_product_discovery_fixtures.py
tests/fixtures/query-product-discovery-success/
tests/fixtures/query-product-discovery-no-candidates/
```

**Structure Decision**: Keep contracts, runtime, and CLI separate. Concrete
network/model/agent/browser dependencies remain adapter-owned or dynamically
loaded by CLI code.

## Complexity Tracking

No constitution violations.
