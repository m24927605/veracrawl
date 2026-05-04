# Feature Specification: Adaptive Frontier Deep Crawl Production Runtime

**Feature Branch**: `072-adaptive-frontier-deep-crawl-production-runtime`  
**Created**: 2026-05-04  
**Status**: Planned  
**Roadmap Row**: 072  
**Input**: Production-grade closure requirement: VeraCrawl must execute bounded multi-page crawls, not only single declared pages.

## Summary

Build the production deep crawl runtime that executes approved discovery plans
across listing/detail, pagination, document, sitemap, API-like, and
browser-required paths. The runtime must use AI-assisted frontier prioritization
without letting model output become source evidence.

## User Scenarios

1. Given an approved product search objective, VeraCrawl crawls search/listing
   pages, identifies candidate detail pages, deduplicates variants, follows
   pagination within bounds, and extracts source-backed product fields.
2. Given a documentation or content site objective, VeraCrawl follows sitemap
   and internal links while respecting robots, scope, canonical URLs, and stop
   conditions.
3. Given loops, duplicate URLs, parameter explosions, off-origin links, or
   exhausted budgets, VeraCrawl stops with replayable stop reasons instead of
   silently losing coverage.

## Functional Requirements

- **FR-001**: System MUST define `FrontierItem`, `FrontierDecision`,
  `DeepCrawlRun`, `PageCoverageRecord`, `CanonicalizationDecision`,
  `DuplicateSuppressionRecord`, and `StopReason` contracts.
- **FR-002**: System MUST support bounded depth, page count, per-origin rate,
  browser budget, token budget, retry budget, and wall-clock budget.
- **FR-003**: System MUST support listing/detail, pagination, sitemap, RSS/feed,
  document index, API-like, and browser-rendered page traversal.
- **FR-004**: System MUST use framework-neutral model/agent ports for frontier
  prioritization and repair decisions when AI is involved.
- **FR-005**: System MUST record command/event/outbox/replay refs for every
  frontier mutation and page acquisition decision.
- **FR-006**: System MUST produce coverage reports with required page counts,
  discovered candidate counts, extracted candidate counts, rejected candidate
  counts, blocked source counts, and stop reasons.
- **FR-007**: System MUST prevent off-origin pollution, robots bypass,
  infinite pagination, duplicate pollution, and unbounded parameter expansion.

## Required Tests

- Fixture tests for listing/detail traversal, pagination, sitemap traversal,
  browser-required detail recovery, canonicalization, duplicate suppression,
  and bounded stop.
- Negative tests for robots bypass, off-origin pollution, infinite pagination,
  budget exhaustion, duplicate loops, missing replay, missing frontier refs, and
  model-only evidence.
- Live public corpus with at least five sites and at least 50 required pages.

## Completion Gate

`veracrawl-deep-crawl-production` can execute a bounded, replayable multi-page
crawl from an approved objective and produce source-backed coverage and
extraction results.
