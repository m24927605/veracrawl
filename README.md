# VeraCrawl

VeraCrawl is being designed as a production-grade, general-purpose AI agent web crawler that maximizes website crawling capability through AI-assisted understanding, exploration, extraction, verification, repair, and learning.

These documents define target capability and implementation requirements. They do not claim the product has already reached target architecture capability.

VeraCrawl must not become a larger scraper script or a vertical intelligence product. The product goal is a durable, observable, recoverable, evidence-preserving AI crawler that can understand unfamiliar websites, plan crawl strategies, adapt to site structure and drift, extract structured data, verify evidence, remember prior site behavior, and replay its decisions.

## Core Position

VeraCrawl is built around four cooperating systems:

- AI crawler runtime: objective understanding, crawl planning, frontier scheduling, fetching, parsing, extraction, replay, and observability.
- Graphify-style graph intelligence: site graph and page-structure intelligence for crawl planning, with richer graph projections added after the V1 profile.
- Sacie-style evidence intelligence: evidence packets, verification, precision controls, and traceable outputs.
- MemPalace-style memory intelligence: scoped crawl diaries in V1, with long-term site, task, and agent memory added in later phases.

The core architectural rule is:

```text
Raw observations are preserved.
Extracted candidates are not published outputs.
Published records, documents, datasets, and facts must point back to evidence.
AI agent memory is a planning and adaptation aid, not the source of truth.
AI maximizes understanding, exploration, extraction, verification, repair, and learning.
```

## V1 Entry Points

Start with these documents:

1. [docs/01-product-definition.md](docs/01-product-definition.md): positioning, users, and `V1 Product Boundary`.
2. [docs/08-build-roadmap.md](docs/08-build-roadmap.md): `V1 Product Slice`, `V1 Build Packs`, and first build target.
3. [docs/02-production-architecture.md](docs/02-production-architecture.md): `V1 Minimal Deployment` and ownership boundaries.
4. [docs/07-data-contracts.md](docs/07-data-contracts.md): `V1 Contract Profile` before the full contract catalog.
5. [docs/06-agent-system-design.md](docs/06-agent-system-design.md): V1 agents and V1 coordination flow.

V1 is the first production spine, not the product ambition. Do not use V1 boundaries to weaken target architecture or claim target capability before implementation and acceptance tests pass.

## Target Architecture Entry Points

The target architecture documents define what VeraCrawl must become as a powerful general-purpose AI agent web crawler:

1. [docs/09-target-capability-model.md](docs/09-target-capability-model.md): target capability and non-deceptive completion rules.
2. [docs/10-target-implementation-design.md](docs/10-target-implementation-design.md): Python implementation design, package boundaries, ports, adapters, and target architecture.
3. [docs/11-target-testing-and-acceptance.md](docs/11-target-testing-and-acceptance.md): test suites, benchmark fixtures, and acceptance gates.
4. [docs/12-target-readiness-review-log.md](docs/12-target-readiness-review-log.md): Staff review protocol and review outcomes.

## Documentation

The complete document index is in [docs/README.md](docs/README.md).

Key documents:

- [docs/01-product-definition.md](docs/01-product-definition.md): product scope, principles, and system boundaries.
- [docs/02-production-architecture.md](docs/02-production-architecture.md): production AI crawler architecture and major planes.
- [docs/03-graphify-research.md](docs/03-graphify-research.md): graph intelligence research and crawler application.
- [docs/04-sacie-research.md](docs/04-sacie-research.md): evidence and verification research.
- [docs/05-mempalace-research.md](docs/05-mempalace-research.md): memory palace research for AI agent crawling.
- [docs/06-agent-system-design.md](docs/06-agent-system-design.md): agent team, responsibilities, and coordination.
- [docs/07-data-contracts.md](docs/07-data-contracts.md): contracts for objectives, plans, jobs, frontier, snapshots, evidence, memory, outputs, and facts.
- [docs/08-build-roadmap.md](docs/08-build-roadmap.md): build sequence, SLOs, and risk controls.
- [docs/09-target-capability-model.md](docs/09-target-capability-model.md): target capability model and completion rules.
- [docs/10-target-implementation-design.md](docs/10-target-implementation-design.md): target implementation design and package boundaries.
- [docs/11-target-testing-and-acceptance.md](docs/11-target-testing-and-acceptance.md): target testing strategy and acceptance gates.
- [docs/12-target-readiness-review-log.md](docs/12-target-readiness-review-log.md): Staff review protocol and readiness log.

## Development Workflow

This repository uses GitHub Spec Kit for spec-driven development. See [AGENT.md](AGENT.md) for agent workflow rules, including when to use Spec Kit, which VeraCrawl V1 constraints must be read before implementation, and how to keep specs, plans, tasks, and code aligned.

## Foundation Commands

The current Python foundation implements the target architecture contracts, ports,
framework-neutral adapter boundaries, command/event/replay primitives, policy gates,
and deterministic fixture/oracle checks. It is an architecture foundation, not a
claim that the full production crawler runtime is complete.

Run the local foundation gate with Python 3.12:

```sh
uv run --python python3.12 --extra dev ruff check src tests
uv run --python python3.12 --extra dev mypy src
uv run --python python3.12 --extra dev pytest tests/contract tests/unit tests/integration
```

Validate the executable contract registry:

```sh
uv run --python python3.12 --extra dev veracrawl-contracts validate --format json
```

Run a deterministic fixture/oracle scenario:

```sh
uv run --python python3.12 --extra dev veracrawl-fixture run \
  tests/fixtures/foundation-fetch-like \
  --profile target \
  --out .veracrawl-test-runs/foundation-fetch-like
```

## Safety Boundary

VeraCrawl is designed for authorized and controlled data acquisition. AI must improve understanding, planning, adaptation, extraction, verification, and debugging.

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
