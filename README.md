# VeraCrawl

> **🗄️ Archived (2026-05-17).** This repository is an R&D / learning artifact;
> it is not a shipping product. There is no end-to-end "crawl a website → get
> structured data" path: production fetch, markdown output, browser automation,
> CLI, and Docker deployment are all out of scope. If you need a working AI
> crawler today, use [crawl4ai](https://github.com/unclecode/crawl4ai) (Playwright
> + LLM-ready markdown + 50k+ stars + active maintenance).
>
> What this repo does contain that may be useful as reference:
>
> - A contract-driven Python architecture (~75 typed contracts, ports + adapters,
>   AST import-boundary tests).
> - A replay-invariant skeleton (`ReplayConsumerPort`, `ReplayBundle`,
>   raw-LLM-response persistence, deterministic request→response mapping).
> - A goal-doc workflow with adversarial codex plan-review + retrospective
>   per-commit task-review (see
>   [`docs/plans/general-purpose-crawler-agentification/STATUS.md`](docs/plans/general-purpose-crawler-agentification/STATUS.md)).
> - Deterministic fixture adapters for planner, drift detection, repair,
>   schema extraction, worker pool (sync + multiprocess), event store
>   (in-memory + SQLite), and artifact store (in-memory + hashed-fs).
> - 3708 passing tests across the suite.
>
> The original aspirational README copy below is preserved for context — it
> describes the design intent, not the shipped state. Read it as "what this
> would have been at completion", not as a product claim.
>
> ---

**A general-purpose AI agent web crawler for evidence-backed data extraction.**

VeraCrawl is being built for the hard version of web crawling: unfamiliar
websites, changing page structures, explicit policy boundaries, source-backed
evidence, replayable AI decisions, and production-grade operations.

It is not a single-site scraper, a browser automation demo, or a vertical data
pipeline. The goal is a durable AI crawler that can understand a crawl
objective, plan how to explore many kinds of sites, gather source observations,
extract structured records, verify evidence, repair drift, and explain what
happened after the run.

> Current repository status: this repo contains the Python foundation, contracts,
> runtime gates, deterministic fixtures, and target architecture documents. It
> does not claim every target production capability is complete until the
> documented acceptance gates pass.

## Why VeraCrawl Exists

Most crawlers break when the website stops matching the script.

VeraCrawl is designed around a different premise: a crawler should understand
the site it is crawling, preserve what it saw, and publish only what it can
trace back to source evidence.

That means AI is used for:

- understanding objectives and website structure
- planning crawl paths and frontier priority
- choosing source adapters such as HTTP, sitemap, RSS, API-like, document, or browser snapshot paths
- proposing extraction strategies
- detecting drift and suggesting repair
- routing uncertain outputs to review
- reusing scoped memory without treating memory as truth

And the system remains bounded by:

- explicit source scope, policy, rate, credential, and replay contracts
- raw observation preservation
- evidence-first publication rules
- framework-neutral model and agent adapter boundaries
- typed commands, events, ports, artifacts, and reports

## The Core Rule

```text
Raw observations are preserved.
Candidates are not published outputs.
Published records must point back to evidence.
Memory can guide planning, but evidence remains authoritative.
AI decisions must be observable, policy-bounded, and replayable.
```

## What Is In The Box

VeraCrawl is organized around four cooperating systems:

- **AI crawler runtime**: objectives, planning, frontier scheduling, fetching, parsing, extraction, replay, and observability.
- **Graph intelligence**: URL, hyperlink, canonical, redirect, page-structure, and richer graph projections for crawl planning.
- **Evidence intelligence**: evidence packets, anchors, verification decisions, review gates, and traceable outputs.
- **Memory intelligence**: scoped crawl diaries today, with long-term site, task, and agent memory in the target architecture.

The implementation is Python-first and keeps the core independent from concrete
model SDKs, browser engines, storage clients, queue clients, and agent
frameworks. Those integrations live behind replaceable adapters.

## Start Here

For product and architecture context:

- [docs/README.md](docs/README.md): full documentation index
- [docs/01-product-definition.md](docs/01-product-definition.md): product scope and principles
- [docs/02-production-architecture.md](docs/02-production-architecture.md): production architecture and ownership boundaries
- [docs/06-agent-system-design.md](docs/06-agent-system-design.md): agent responsibilities and coordination
- [docs/07-data-contracts.md](docs/07-data-contracts.md): canonical contracts
- [docs/08-build-roadmap.md](docs/08-build-roadmap.md): build sequence and validation gates

For the target architecture:

- [docs/09-target-capability-model.md](docs/09-target-capability-model.md): what VeraCrawl must become
- [docs/10-target-implementation-design.md](docs/10-target-implementation-design.md): packages, ports, adapters, and runtime design
- [docs/11-target-testing-and-acceptance.md](docs/11-target-testing-and-acceptance.md): acceptance gates and benchmark fixtures
- [docs/12-target-readiness-review-log.md](docs/12-target-readiness-review-log.md): readiness review protocol

## V1 Boundary

V1 proves the production spine without pretending to solve the whole web.

The V1 profile focuses on static or mostly static HTML, sitemap, RSS, document
metadata, listing/detail pages, pagination, canonical URLs, redirects, local
result materialization, run diaries, and URL/page-structure graph signals.

HTTP is first. Browser snapshots require explicit approval. V1 does not rely on
long-term memory, entity/task/temporal graph acceptance paths, production export
connectors, or unrestricted browser automation.

V1 is a validation sequence, not a reduction of product ambition.

## Run The Local Foundation

Use Python 3.12 through `uv`:

```sh
uv run --python python3.12 --extra dev ruff check src tests
uv run --python python3.12 --extra dev mypy src
uv run --python python3.12 --extra dev pytest tests/contract tests/unit tests/integration
```

Validate the executable contract registry:

```sh
uv run --python python3.12 --extra dev veracrawl-contracts validate --format json
```

Run a deterministic fixture:

```sh
uv run --python python3.12 --extra dev veracrawl-runtime run \
  tests/fixtures/runtime-record-success \
  --profile target \
  --out .veracrawl-test-runs/runtime-record-success
```

The full production-grade release gate aggregates lower gate reports from
discovery planning, acquisition escalation, authorized source access, deep
crawl, extraction quality, and operations reliability. See
[docs/11-target-testing-and-acceptance.md](docs/11-target-testing-and-acceptance.md)
for the complete gate matrix and aggregate release command.

## Development Workflow

For non-trivial product, architecture, contract, agent workflow, policy,
crawling, evidence, memory, graph, export, replay, or persistence changes, use
the lightweight plan-driven workflow under [docs/plans](docs/plans).

Small mechanical documentation edits may be made directly. This README rewrite
is one of those direct edits: it changes presentation, not product scope,
architecture, contracts, or runtime behavior.
