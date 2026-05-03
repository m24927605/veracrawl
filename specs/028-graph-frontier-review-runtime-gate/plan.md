# Implementation Plan: VeraCrawl Graph-Driven Frontier And Review Runtime Gate

**Branch**: `028-graph-frontier-review-runtime-gate`
**Spec**: `specs/028-graph-frontier-review-runtime-gate/spec.md`

## Summary

Implement a graph-driven frontier/review runtime gate that consumes `GraphSignal` records into typed frontier and review route decision records. The gate keeps graph signals non-authoritative for evidence/publication, requires policy/command/event/outbox/replay refs, and returns `needs_review` when live graph/scheduler/review runtime refs are absent.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Pydantic, argparse, pytest, ruff, mypy
**Storage**: deterministic fixture run reports under `.veracrawl-test-runs/`
**Testing**: pytest contract/unit/integration, CLI fixture loop, registry validation, ruff, mypy, Docker-backed full suite
**Target Platform**: local deterministic graph-driven frontier/review runtime gate
**Project Type**: Python library/CLI
**Constraints**: no core static imports of graph stores, agent frameworks, model SDKs, browser libraries, storage clients, queue clients, or concrete HTTP clients; graph signals cannot be source evidence or publication truth
**Canonical Contracts**: GraphSignal, FrontierItem, ReviewItem, GraphFrontierDecisionRecord, GraphReviewRouteDecisionRecord, GraphFrontierReviewRuntimeReport

## Constitution Check

- General-purpose crawler scope preserved: no site-specific or schema-specific logic.
- Python remains the implementation language.
- Agent/model frameworks remain isolated; this slice adds no framework dependency.
- Low coupling/high cohesion: contracts in `contracts.graph`, runtime in `graph.frontier_review`, CLI in `cli.graph_frontier_review`.
- Evidence/publication boundary is explicit: graph signals cannot satisfy source evidence.
- Security/policy/replay refs are required for pass.
- Command, event, fixture, oracle, negative, and replay tests are planned before implementation.
- Target architecture is not weakened for schedule or staffing reasons.

## Project Structure

```text
src/veracrawl/contracts/enums.py
src/veracrawl/contracts/graph.py
src/veracrawl/graph/frontier_review.py
src/veracrawl/cli/graph_frontier_review.py
tests/contract/test_graph_frontier_review_contracts.py
tests/contract/test_graph_frontier_review_contract_registry.py
tests/contract/test_graph_frontier_review_import_boundaries.py
tests/unit/test_graph_frontier_review_gate.py
tests/integration/test_graph_frontier_review_fixtures.py
tests/fixtures/graph-frontier-review-*/
```

## Implementation Phases

1. Add enums, contracts, exports, registry entries, and target area.
2. Add deterministic runtime gate and CLI.
3. Add fixtures and tests for success, needs_review, and negative cases.
4. Update docs and active Spec Kit pointer.
5. Run full verification and commit.

## Acceptance

- Registry validation passes.
- Focused graph frontier/review tests pass.
- All CLI fixtures pass.
- Full non-Docker and Docker-backed suites pass.
