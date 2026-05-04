# Implementation Plan: US Top Ecommerce Product Price Availability Benchmark

**Branch**: `066-product-price-availability-benchmark` | **Date**: 2026-05-04 | **Spec**: `specs/066-product-price-availability-benchmark/spec.md`  
**Input**: Feature specification from `specs/066-product-price-availability-benchmark/spec.md`

## Summary

Implement a product-page benchmark for extracting source-backed price and
availability for a specified product on Amazon, Walmart, and eBay. The runtime
will reuse live HTTP adapters and framework-neutral model/agent ports, produce
field evidence contracts, and return `needs_review` when a top ecommerce source
blocks access instead of fabricating values.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: Existing VeraCrawl live HTTP, model/agent ports,
OpenAI Responses adapter, native agent runtime, Pydantic contracts  
**Storage**: Local run artifacts under `.veracrawl-real-runs/`  
**Testing**: pytest, ruff, mypy, registry validation, live CLI validation,
Docker-backed pytest  
**Target Platform**: CLI/library benchmark runner  
**Project Type**: Python package + CLI  
**Performance Goals**: One robots request and one product-page request per site;
four AI decisions per extractable site  
**Constraints**: No login/cart/checkout, no CAPTCHA/WAF bypass, no site-specific
scraper modules, no core model SDK or agent framework coupling  
**Scale/Scope**: Three public product-page targets for one specified product  
**VeraCrawl Owner Services**: fetch, extract, evidence, verify, agents, ops,
policy, review_replay  
**Canonical Contracts**: ProductAvailabilityBenchmarkManifest,
ProductAvailabilityTargetSpec, ProductAvailabilityFieldEvidence,
ProductAvailabilitySiteResult, ProductAvailabilityBenchmarkReport,
ModelCallTrace, AgentActionTrace, ToolCallTrace, ContextBundleTrace  
**Replay/Artifact Impact**: field evidence and site reports require artifact,
content hash, command/event/outbox, and replay refs  
**Security/Policy Impact**: robots, origin scope, private-network denial,
prompt-context redaction, no direct publication

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral.
- [x] Low coupling/high cohesion boundaries use contracts, ports, and adapters.
- [x] Evidence, verification, publication-gate, replay, and artifact lineage are
  defined.
- [x] Security and policy gates are explicit.
- [x] Fixture/oracle, replay, registry, import-boundary, and acceptance tests are
  planned before implementation.
- [x] Target architecture is not weakened due to schedule pressure.

## Project Structure

```text
specs/066-product-price-availability-benchmark/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/product-price-availability-benchmark.md
└── tasks.md

src/veracrawl/contracts/product_availability.py
src/veracrawl/benchmarks/product_availability.py
src/veracrawl/cli/product_availability_benchmark.py
tests/fixtures/us-top-ecommerce-product-availability/
tests/contract/test_product_availability_contracts.py
tests/contract/test_product_availability_contract_registry.py
tests/contract/test_product_availability_import_boundaries.py
tests/unit/test_product_availability_runtime.py
tests/unit/test_product_availability_replay.py
tests/integration/test_product_availability_fixtures.py
```

**Structure Decision**: New contracts/runtime/CLI are needed because row 056 AI
candidate traces do not model field-level price and availability evidence.

## Complexity Tracking

No constitution violations.
