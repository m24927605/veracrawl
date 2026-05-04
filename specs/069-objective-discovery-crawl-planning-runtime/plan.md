# Implementation Plan: Objective Discovery And Crawl Planning Runtime

## Scope

Implement row 069 as the production-grade discovery planning slice. The runtime
turns a high-level objective and source profiles into replayable candidate
targets, entry points, approved crawl discovery plans, policy refs, model/agent
trace refs, command/event/outbox refs, and replay refs.

## Technical Plan

- Add production-grade closure contracts in `src/veracrawl/contracts/production_grade.py`.
- Register `DiscoveryEntryPoint`, `CandidateSourceTarget`,
  `DiscoveryApprovalDecision`, and `CrawlDiscoveryPlan` in the executable
  contract registry.
- Implement deterministic fixture runtime in
  `src/veracrawl/benchmarks/production_grade.py`.
- Expose `veracrawl-discovery-planner` through
  `src/veracrawl/cli/production_grade.py`.
- Prove framework neutrality with import-boundary tests.

## Validation Plan

- Contract tests: `tests/contract/test_production_grade_contracts.py`.
- Registry tests: `tests/contract/test_production_grade_contract_registry.py`.
- Runtime tests: `tests/unit/test_production_grade_runtime.py`.
- Fixture test: `tests/integration/test_production_grade_fixtures.py`.
- Fixture corpus: `tests/fixtures/production-discovery-planning-success`.
