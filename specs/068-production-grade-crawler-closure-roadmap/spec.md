# Feature Specification: Production Grade Crawler Closure Roadmap

**Feature Branch**: `068-production-grade-crawler-closure-roadmap`  
**Created**: 2026-05-04  
**Status**: Planned  
**Input**: User request: "VeraCrawl must reach production-grade web crawler capability; write the required specs first."

## Purpose

This spec fixes the finite production-grade closure roadmap after the 067
Taiwan ecommerce benchmark. It exists to prevent ad hoc expansion while making
the remaining production readiness gaps explicit, implementable, testable, and
release-blocking.

The completion target is not a toy scraper and not a single-site ecommerce
tool. VeraCrawl must become a general-purpose, policy-gated AI agent website
crawler that can discover, plan, acquire, render, extract, verify, replay,
operate, and publish source-backed results across authorized public and
authorized credentialed sources.

## Constitution Alignment

- **General-purpose crawler impact**: Keeps VeraCrawl broad across website
  patterns, domains, schemas, crawl objectives, source adapters, and AI-assisted
  workflows.
- **Target architecture impact**: Does not weaken the target architecture.
  Sequencing is allowed only to control dependencies and validation.
- **Agent/framework impact**: Core remains framework-neutral. Model/agent SDKs
  and frameworks stay behind adapters.
- **Evidence and replay impact**: Every production-grade claim must be backed by
  source artifacts, content hashes, source anchors, evidence packets,
  verification decisions, command/event/outbox refs, and replay refs.
- **Safety and policy impact**: No CAPTCHA solving, WAF evasion, stealth
  bypass, unauthorized credential use, robots/terms bypass, cart/checkout, or
  fabricated evidence.

## Approved Closure Specs

| Spec | Name | Purpose | Blocking Dependencies | Completion Gate |
| --- | --- | --- | --- | --- |
| 069 | Objective Discovery And Crawl Planning Runtime | Turn high-level objectives into approved discovery plans, candidate sites, entry points, query strategies, crawl bounds, and evidence requirements. | 049, 050, 055, 056, 067, 068 | A user objective can produce a replayable, policy-approved crawl plan without declared product URLs. |
| 070 | Unified HTTP Browser Acquisition Escalation Runtime | Escalate from HTTP/structured acquisition to browser rendering when evidence is missing, while preserving sandbox, budget, DOM/network artifacts, and no-bypass policy. | 043, 041, 045, 059, 067, 069 | Product/site flows can recover source-backed DOM evidence when authorized browser rendering is sufficient, and honestly mark source-limited cases when not. |
| 071 | Authorized Source Access And Official API Runtime | Support official APIs and authorized credentialed sessions as first-class source adapters without leaking secrets or bypassing site controls. | 044, 049, 070 | Authorized APIs/sessions can provide evidence-backed source data; unauthorized/login-wall/challenge cases remain needs-review. |
| 072 | Adaptive Frontier Deep Crawl Production Runtime | Execute bounded multi-page crawls with AI-assisted frontier prioritization, pagination/detail traversal, canonicalization, dedupe, rate limits, and replayable stop reasons. | 050, 051, 052, 060, 070 | A declared objective can crawl listings/details across multiple sites under budgets and produce complete page coverage reports. |
| 073 | Production Extraction Quality And Oracle Runtime | Convert field-level oracle, precision/recall, confidence calibration, abstention, and publication gating into release-blocking production quality checks. | 061, 062, 072 | Extraction quality gates block publication/release when precision, recall, anchors, evidence, or abstention thresholds fail. |
| 074 | Production Reliability Operations And Cost Runtime | Prove long-running worker, queue, persistence, object store, retry, recovery, observability, cost, latency, and SLO behavior under production-like runs. | 052, 053, 064, 072, 073 | Multi-run production workloads pass SLO/cost/reliability gates with replayable recovery and operator visibility. |
| 075 | Production Grade Web Crawler Release Gate | Aggregate 069-074 into one release gate that decides whether VeraCrawl may claim production-grade crawler capability. | 069-074 | Production-grade status is blocked unless discovery, browser/API acquisition, deep crawl, extraction quality, operations, and safety gates all pass. |

## Post-Closure Optimization Amendment

Specs 080-086 are approved as post-079 crawler intelligence optimization
follow-ups in `specs/080-crawler-intelligence-optimization-roadmap/spec.md`.
They improve frontier scoring, DOM understanding, extraction fallback and
confidence, canonical dedupe and identity, recommendation ranking, and
cost/recovery/evaluation gates.

These specs are not additional production-grade closure specs. They do not
replace specs 069-075, do not weaken the aggregate 075 release gate, and do not
allow production-grade status to pass without parsed lower `ProductionGateReport`
artifacts from specs 069-074. Future production-grade closure specs beyond
069-075 still require amending this spec and `docs/08-build-roadmap.md` first.

## Roadmap Rules

- **RR-001**: Production-grade closure specs are fixed to 069-075 unless this
  spec and `docs/08-build-roadmap.md` are amended first.
- **RR-002**: No spec may claim production-grade status on benchmark smoke tests
  alone.
- **RR-003**: Blocked sources such as Shopee Taiwan must remain explicit
  `needs_review` unless authorized browser/API/session evidence exists.
- **RR-004**: LLM output cannot be source evidence. It can propose plans,
  candidates, repairs, and verification decisions only through VeraCrawl ports.
- **RR-005**: Every closure spec must create or update contracts, runtime,
  fixtures/oracles, CLI surfaces, negative tests, replay tests, import-boundary
  tests, live validation, and `tasks.md` validation logs.
- **RR-006**: Implementation proceeds in spec order. A later closure spec cannot
  be marked complete while an earlier blocking closure spec is incomplete.
- **RR-007**: Post-closure optimization specs may supplement future quality
  claims, but they must not be used to bypass missing or non-passing 069-075
  lower gates.

## Non-Goals

- Do not implement a single-site scraper.
- Do not bypass robots, login walls, CAPTCHA, WAF, paywalls, or anti-bot
  controls.
- Do not treat search snippets, model output, memory, graph data, or
  framework-native state as source evidence.
- Do not claim every site on the internet is crawlable. Production-grade means
  robust, honest, policy-compliant crawling with explicit blocked-source
  accounting.

## Success Criteria

- **SC-001**: Specs 069-075 exist with purpose, dependencies, requirements, and
  completion gates.
- **SC-002**: `docs/08-build-roadmap.md` and `specs/038-production-runtime-closure/spec.md`
  include the same closure roadmap.
- **SC-003**: Future implementation is constrained to the closure roadmap until
  amended.
- **SC-004**: Specs 080-086 are explicitly documented as post-closure
  optimization follow-ups, not new production-grade closure gates.
