# Feature Specification: Objective Discovery And Crawl Planning Runtime

**Feature Branch**: `069-objective-discovery-crawl-planning-runtime`  
**Created**: 2026-05-04  
**Status**: Implemented
**Roadmap Row**: 069  
**Input**: Production-grade closure requirement: VeraCrawl must crawl from high-level objectives, not only declared URLs.

## Summary

Build the production runtime that turns a user objective into an approved,
bounded, replayable discovery plan. The plan must identify candidate sites,
entry points, source adapter strategy, crawl bounds, extraction schemas,
evidence requirements, policy gates, and stop conditions before live crawling.

## User Scenarios

1. Given an objective such as "find the price and stock for a specified product
   across authorized ecommerce sites", VeraCrawl proposes candidate target
   sites, discovery paths, search/listing/detail strategies, and evidence
   requirements without requiring the operator to provide every product URL.
2. Given a broad website extraction objective, VeraCrawl proposes sitemap,
   search, listing/detail, API-like, document, HTTP, and browser acquisition
   strategies with policy-bounded crawl depth and budget.
3. Given ambiguous objectives or unsafe source scope, VeraCrawl records
   clarification or policy-blocked needs-review instead of inventing an unsafe
   crawl.

## Functional Requirements

- **FR-001**: System MUST define `CrawlDiscoveryPlan`,
  `CandidateSourceTarget`, `DiscoveryEntryPoint`, `CrawlBound`, and
  `DiscoveryApprovalDecision` contracts.
- **FR-002**: System MUST use framework-neutral model/agent ports for objective
  interpretation, candidate site selection, search/listing strategy, and plan
  verification.
- **FR-003**: System MUST support discovery methods for sitemap, RSS/feed,
  internal search, listing/category pages, known public entry pages, API-like
  public endpoints, document indexes, and browser-required entry points.
- **FR-004**: System MUST require source scope, robots/terms policy,
  rate/budget, privacy, credential, browser, and publication constraints before
  plan approval.
- **FR-005**: System MUST persist canonical VeraCrawl plan contracts only; no
  framework-native agent state may be canonical.
- **FR-006**: System MUST produce command/event/outbox/replay refs for plan
  creation, approval, rejection, revision, and execution handoff.
- **FR-007**: System MUST reject or mark needs-review when the objective cannot
  be translated into authorized source targets.

## Evidence Rules

- Discovery recommendations are not source evidence.
- Discovered URLs become candidate targets only after policy approval.
- Published extracted values still require later source artifacts, anchors,
  content hashes, and verification decisions.

## Required Tests

- Contract tests for discovery plan, candidate target, bounds, approvals, and
  replay refs.
- Import-boundary tests proving core planning does not import OpenAI SDK,
  LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, Playwright, requests
  clients, or site-specific modules.
- Fixture tests for successful ecommerce product discovery, successful
  non-ecommerce site discovery, ambiguous objective needs-review, unsafe target
  blocked, and missing replay failure.
- Hosted OpenAI validation proving real model traces exist for objective
  interpretation and plan verification.

## Completion Gate

`veracrawl-discovery-planner` can create an approved, replayable crawl discovery
plan from a high-level objective and feed approved targets to later acquisition
without declared product URLs or single-site scraper assumptions.
