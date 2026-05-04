# Implementation Plan: Taiwan Top Ecommerce Product Price Availability Benchmark

**Branch**: `067-taiwan-product-availability-benchmark` | **Date**: 2026-05-04 | **Spec**: `specs/067-taiwan-product-availability-benchmark/spec.md`  
**Input**: Feature specification from `specs/067-taiwan-product-availability-benchmark/spec.md`

## Summary

Add a Taiwan-targeted product availability fixture and locale extraction support
to the existing product availability benchmark. The implementation reuses spec
066 contracts/runtime/CLI, adds generic meta-tag and Chinese availability
patterns, records Shopee Taiwan as needs-review when only a JavaScript shell or
403 API response is available, and validates through local and hosted OpenAI
live runs.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: Existing product availability runtime, live HTTP,
model/agent ports, OpenAI Responses adapter, native agent runtime, Pydantic  
**Storage**: Local run artifacts under `.veracrawl-real-runs/`  
**Testing**: pytest, ruff, mypy, registry validation, live CLI validation  
**Target Platform**: CLI/library benchmark runner  
**Project Type**: Python package + CLI fixture/docs update  
**Performance Goals**: One robots request and one product-page request per site;
four AI decisions per extractable site  
**Constraints**: No login/cart/checkout, no CAPTCHA/WAF bypass, no site-specific
scraper modules, no direct model SDK or agent framework coupling in core  
**Scale/Scope**: Three Taiwan public product targets for one product family  
**VeraCrawl Owner Services**: fetch, extract, evidence, verify, agents, policy,
review_replay  
**Canonical Contracts**: ProductAvailabilityBenchmarkManifest,
ProductAvailabilityTargetSpec, ProductAvailabilityFieldEvidence,
ProductAvailabilitySiteResult, ProductAvailabilityBenchmarkReport  
**Replay/Artifact Impact**: Reuse spec 066 field/site/report replay refs  
**Security/Policy Impact**: robots, origin scope, private-network denial,
prompt-context redaction, no direct publication

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral.
- [x] Low coupling/high cohesion boundaries use contracts, ports, and adapters.
- [x] Evidence, verification, publication-gate, replay, and artifact lineage are
  defined by the existing product availability contracts.
- [x] Security and policy gates are explicit.
- [x] Fixture/oracle, replay, registry, import-boundary, and acceptance tests are
  planned before implementation.
- [x] Target architecture is not weakened due to schedule pressure.

## Project Structure

```text
specs/067-taiwan-product-availability-benchmark/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/taiwan-product-availability-benchmark.md
└── tasks.md

src/veracrawl/benchmarks/product_availability.py
src/veracrawl/contracts/registry.py
tests/fixtures/taiwan-top-ecommerce-product-availability/
tests/unit/test_product_availability_runtime.py
tests/integration/test_product_availability_fixtures.py
```

**Structure Decision**: Reuse spec 066 runtime/contracts and add only generic
locale support plus a Taiwan fixture.

## Complexity Tracking

No constitution violations.
