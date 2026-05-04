# Feature Specification: Production Grade Web Crawler Release Gate

**Feature Branch**: `075-production-grade-web-crawler-release-gate`  
**Created**: 2026-05-04  
**Status**: Implemented
**Roadmap Row**: 075  
**Input**: Production-grade closure requirement: VeraCrawl may claim production-grade only after aggregate release validation passes.

## Summary

Create the final aggregate release gate for production-grade web crawler status.
This gate composes specs 069-074 and decides whether VeraCrawl may honestly
claim production-grade, general-purpose AI agent web crawler capability.

## Release Definition

VeraCrawl is production-grade only when it can:

- turn high-level objectives into approved crawl plans;
- discover candidate sources and entry points without predeclared URLs;
- acquire evidence through HTTP, structured sources, browser rendering,
  official APIs, or authorized sessions;
- execute bounded multi-page crawls with adaptive frontier and replayable stop
  reasons;
- extract and verify source-backed fields across schemas and site patterns;
- publish only when evidence, quality, policy, replay, and review gates pass;
- operate under durable infrastructure, SLOs, cost controls, recovery, and
  observability;
- explicitly report blocked/source-limited sites without bypass or fabrication.

## Functional Requirements

- **FR-001**: System MUST define `ProductionGradeReleaseReport`,
  `ProductionGradeCapabilityMatrix`, `ReleaseBlocker`, `ReleaseDecision`, and
  `FalseReadyGuard` contracts.
- **FR-002**: System MUST ingest validation reports from specs 069-074 and fail
  if any required gate is missing, stale, failed, or needs-review without an
  accepted waiver.
- **FR-003**: System MUST include public corpus, JS/browser corpus,
  multi-page/deep crawl corpus, field oracle corpus, ecommerce corpus,
  authorized API/session corpus, and operational workload corpus.
- **FR-004**: System MUST require hosted model/agent traces through
  framework-neutral ports where AI decisions are part of the acceptance path.
- **FR-005**: System MUST block release for LLM-as-evidence,
  framework-native canonical state, missing source anchors, missing replay,
  publication bypass, unsafe browser interaction, unauthorized credential use,
  robots bypass, source-limited fabrication, low quality metrics, or SLO/cost
  violations.
- **FR-006**: System MUST produce a human-readable production readiness report
  that distinguishes production-ready capabilities from known limitations.

## Required Tests

- Aggregate contract and registry tests.
- Negative aggregate fixtures for each missing lower gate and each false-ready
  condition.
- Full focused validation for specs 069-074.
- Full pytest and Docker-backed pytest.
- Live public and authorized corpora validation with actual model/agent traces.

## Completion Gate

`veracrawl-production-grade-release-gate` returns `pass` only when every
production-grade crawler capability is implemented, tested, replayable,
source-backed, policy-compliant, and operationally validated. Until then,
VeraCrawl must describe itself as a production-grade foundation or partial
production capability, not a fully production-grade crawler.
