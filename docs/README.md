# VeraCrawl Docs

VeraCrawl is being designed as a production-grade, general-purpose AI agent web crawler that maximizes website crawling capability through four cooperating systems:

- AI crawler runtime: objective understanding, crawl planning, frontier scheduling, fetching, parsing, extraction, replay, and observability.
- Graphify-style graph intelligence: site graph, page graph, entity graph, task graph, and relationship analysis for crawl planning.
- Sacie-style evidence intelligence: evidence packets, verification, precision controls, and traceable outputs.
- MemPalace-style memory intelligence: long-term site, task, and agent memory with scoped retrieval and crawl diaries.

This directory contains the product, architecture, contract, research, roadmap, target capability, implementation, testing, and review documents for VeraCrawl. It is not code scaffold, and it does not claim target architecture is already complete. It defines target architecture capability and implementation boundaries.

## Start Here For Target Architecture

Read in this order:

1. [09-target-capability-model.md](09-target-capability-model.md): target capability and non-deceptive completion rules.
2. [10-target-implementation-design.md](10-target-implementation-design.md): Python implementation design, package boundaries, ports, adapters, and target architecture.
3. [11-target-testing-and-acceptance.md](11-target-testing-and-acceptance.md): test suites, benchmark fixtures, and acceptance gates.
4. [12-target-readiness-review-log.md](12-target-readiness-review-log.md): Staff review protocol and review outcomes.

## Start Here For V1 Spine

Read in this order:

1. [01-product-definition.md](01-product-definition.md): read the positioning and `V1 Product Boundary`.
2. [08-build-roadmap.md](08-build-roadmap.md): read `V1 Product Slice`, `V1 Build Packs`, and the first build target.
3. [02-production-architecture.md](02-production-architecture.md): read `V1 Minimal Deployment` and ownership boundaries.
4. [07-data-contracts.md](07-data-contracts.md): read `V1 Contract Profile` before the full contract catalog.
5. [06-agent-system-design.md](06-agent-system-design.md): read V1 agents and V1 coordination flow.

Treat V1 as the first production spine, not as the product ambition. Graphify, Sacie, and MemPalace capabilities are target architecture inputs and must not be falsely claimed complete before implementation and acceptance tests pass.

## Documents

- [01-product-definition.md](01-product-definition.md): product name, scope, design principles, and system boundaries.
- [02-production-architecture.md](02-production-architecture.md): production AI crawler architecture and major planes.
- [03-graphify-research.md](03-graphify-research.md): lessons from Graphify and how they apply to crawling.
- [04-sacie-research.md](04-sacie-research.md): lessons from Sacie and how they apply to crawler verification.
- [05-mempalace-research.md](05-mempalace-research.md): lessons from MemPalace and how memory palace applies to AI agent crawling.
- [06-agent-system-design.md](06-agent-system-design.md): professional agent team, responsibilities, and coordination.
- [07-data-contracts.md](07-data-contracts.md): production data contracts for objectives, plans, jobs, frontier, snapshots, evidence, memory, outputs, and facts.
- [08-build-roadmap.md](08-build-roadmap.md): production-first build sequence, SLOs, and risk controls.
- [09-target-capability-model.md](09-target-capability-model.md): target capability model and completion rules.
- [10-target-implementation-design.md](10-target-implementation-design.md): target implementation design and package boundaries.
- [11-target-testing-and-acceptance.md](11-target-testing-and-acceptance.md): target testing strategy and acceptance gates.
- [12-target-readiness-review-log.md](12-target-readiness-review-log.md): Staff review protocol and readiness log.

## Core Position

VeraCrawl must not be a larger scraper script or a vertical intelligence product. It must be a durable, observable, recoverable, evidence-preserving AI crawler that can understand unfamiliar websites, plan crawl strategies, adapt to site structure and drift, extract structured data, verify evidence, remember prior site behavior, and replay its decisions.

The key architectural rule is:

```text
Raw observations are preserved.
Extracted candidates are not published outputs.
Published records, documents, datasets, and facts must point back to evidence.
AI agent memory is a planning and adaptation aid, not the source of truth.
AI maximizes understanding, exploration, extraction, verification, repair, and learning.
```

## Safety Boundary

The platform must be designed for authorized and controlled data acquisition. AI must improve understanding, planning, adaptation, extraction, verification, and debugging.

Safety is part of the crawl contract:

- source scope and rate limits must be explicit
- credential use must be scoped and auditable
- robots, terms, and customer authorization policy must be represented in job policy
- untrusted web content must be treated as prompt-injection-prone input
- raw secrets must not be exposed to agents, model prompts, logs, replay bundles, or untrusted page text
- customer-approved credential presentation to an authorized origin is allowed only through scoped headers, scoped cookies, request signing, or vault-brokered form fill with origin allowlist, policy approval, and `CredentialUseAudit`
- raw artifacts need retention, privacy, and PII handling policy
- unavailable or blocked sources must be reported, not bypassed

These documents intentionally do not specify mechanisms for CAPTCHA solving, paywall bypass, login wall circumvention, WAF evasion, stealth automation, or ban-avoidance proxy tactics.
