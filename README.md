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

This repository uses GitHub Spec Kit for spec-driven development. See [AGENTS.md](AGENTS.md) for agent workflow rules, including when to use Spec Kit, which VeraCrawl V1 constraints must be read before implementation, and how to keep specs, plans, tasks, and code aligned.

## Foundation And Runtime Commands

The current Python foundation implements the target architecture contracts, ports,
framework-neutral adapter boundaries, command/event/replay primitives, policy gates,
deterministic fixture/oracle checks, the first target runtime spine, the durable
runtime/scheduler foundation, the deterministic source acquisition runtime, and
the local network/browser acquisition runtime, the normalize/extract plane, the
evidence/publication spine, the basic site graph spine, the advanced graph
projection spine, the memory kernel spine, the multi-agent repair spine, the
review/replay/ops console spine, the export connector spine, the scale
hardening spine, and the production persistence/queue runtime spine.
The concrete persistence adapter spine adds a standard-library SQLite adapter,
Postgres contract descriptor, operational Postgres JSONB adapter, core adapter
conformance harness, migration records, adapter conformance reports, adapter
fixtures, and dynamic adapter CLI loading without importing concrete storage
into core.
The runtime spine can execute deterministic objective-to-output fixtures, enforce
owner boundaries, block unsafe publication, validate replay refs, and accept
framework-neutral agent recommendations through commands. The durable foundation
adds deterministic unit-of-work, command idempotency, event cursor, outbox,
artifact index, frontier, queue lease, and replay recovery checks behind
replaceable ports. The source acquisition runtime adds framework-neutral source
adapter execution for HTTP, sitemap, RSS, API-like, and document-source families,
with policy, rate-limit, retry, adapter mismatch, malformed response, raw artifact,
and replay lineage reports. The network/browser acquisition runtime adds actual
local HTTP acquisition through a replaceable adapter, redirect metadata,
network/browser replay reports, browser sandbox contracts, and deterministic
browser observation fixtures. The normalize/extract plane adds normalized
document manifests, text anchors, anchor maps, link provenance, page type
classification, site model records, extraction strategies, anchored extraction
candidates, and replay checks from raw snapshot to candidate. It is not a claim
that the full production crawler runtime, production browser rendering fleet,
production persistence adapters, authenticated crawling, graph intelligence,
memory system, export system, or production scale operations are complete. The
evidence/publication spine adds field evidence anchors, evidence manifests,
verification and review decisions, publication policy gates, output manifests,
publication reports, and replay checks that prevent candidates from becoming
outputs without source-backed evidence and accepted gates. It is not a claim that
graph intelligence, memory intelligence, export delivery, distributed
persistence, production browser rendering, or production scale operations are
complete. The basic site graph spine adds deterministic URL, hyperlink,
canonical, redirect, and page-structure graph records with graph manifests, edge
provenance, projection watermarks, replay reports, and graph-as-evidence
boundary checks. It is not a claim that advanced graph intelligence, memory
intelligence, graph store adapters, export delivery, distributed persistence,
production browser rendering, or production scale operations are complete.
The advanced graph projection spine adds projection specs, rebuild jobs,
projection mismatch reports, graph delta reports, graph quality reports, graph
signals, temporal graph projection records, replay reports, and frontier/review
signal contracts while preserving the rule that graph signals cannot satisfy
source evidence. It is not a claim that memory intelligence, export delivery,
distributed persistence, production browser rendering, production graph store
operations, concrete graph-driven scheduling, or production scale operations are
complete.
The memory kernel spine adds memory events, scoped retrieval traces,
cross-scope memory tunnels, operational temporal memory records, invalidation
exclusion, tainted-memory prompt-use blocking, memory replay reports, and
memory-as-evidence boundary checks. It is not a claim that production memory
stores, vector/search retrieval, export delivery, distributed persistence,
production browser rendering, or production scale operations are complete.
The multi-agent repair spine adds framework-neutral workflow, handoff,
coordination decision, drift repair signal, repair replay report, owner-service
boundary, arbitration, and agent-reasoning-as-evidence checks. It is not a claim
that any concrete agent framework, model SDK, review UI, export delivery,
distributed persistence, production browser rendering, or production scale
operations are complete.
The production persistence/queue runtime spine adds persistence adapter specs,
transaction records, durable idempotency records, persistent queue operation
records, a standard-library reference filesystem store, event cursor replay,
outbox dispatch visibility, artifact index refs, queue lease heartbeat, ack,
nack, dead-letter recovery refs, and fixture gates. It is not a claim that concrete
database, queue broker, cloud storage, metrics/tracing backend, production
deployment, production worker fleet, or production observability operations are
complete.
The review/replay/ops console spine adds review items, replay audit views,
failure records, recovery actions, DR restore reports, quality reports,
dashboard snapshots, ops console reports, fixture manifests, policy/review
gates, and replay checks. It is not a claim that a production dashboard
frontend, production observability backend, alerting system, export delivery,
distributed persistence, production browser rendering, or production scale
operations are complete.
The export connector spine adds destination-neutral export targets, export jobs,
attempts, delivery receipts, withdrawal jobs, withdrawal attempts, correction
records, reconciliation reports, idempotency checks, destination object mappings,
and replay fixtures. It is not a claim that concrete export adapters, external
API/database/warehouse/object-store/queue delivery, production export worker
fleets, distributed persistence, production browser rendering, or production
scale operations are complete.
The scale hardening spine adds queue topology specs, deterministic shard keys,
queue items, worker shard leases and heartbeats, backpressure signals,
autoscaling decisions, retry dead-letter records, scale recovery reports,
DR/replay refs, fairness and recovery policy gates, and scale fixtures. It is
not a claim that concrete queue brokers, storage engines, metrics/tracing
backends, cloud autoscaling APIs, production distributed persistence,
production worker fleets, production browser rendering, or production scale
operations are complete.
The concrete persistence adapter spine proves executable SQLite adapter
semantics for transactions, migrations, idempotency, event cursors, outbox,
artifact index, queue leases, and replay refs. The Postgres descriptor is
contract-only and returns `needs_review`; the operational Postgres adapter can
claim `pass` only against an explicit live DSN or Docker-backed live gate. It is
not a claim that external queue brokers, object storage, cloud deployment,
managed Postgres operations, or observability backends are production-ready.

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

Run the target runtime spine success fixture:

```sh
uv run --python python3.12 --extra dev veracrawl-runtime run \
  tests/fixtures/runtime-record-success \
  --profile target \
  --out .veracrawl-test-runs/runtime-record-success
```

Run negative runtime publication gates:

```sh
for fixture in \
  runtime-blocked-source \
  runtime-missing-evidence \
  runtime-verification-conflict \
  runtime-adapter-mismatch \
  runtime-replay-gap \
  runtime-boundary-violation
do
  uv run --python python3.12 --extra dev veracrawl-runtime run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run durable runtime and scheduler fixtures:

```sh
uv run --python python3.12 --extra dev veracrawl-durable run \
  tests/fixtures/durable-runtime-success \
  --profile target \
  --out .veracrawl-test-runs/durable-runtime-success

for fixture in \
  durable-duplicate-command \
  durable-event-gap \
  durable-pending-outbox \
  durable-stale-lease \
  durable-invalid-lease \
  durable-missing-artifact
do
  uv run --python python3.12 --extra dev veracrawl-durable run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run source acquisition fixtures:

```sh
for fixture in \
  source-http-success \
  source-sitemap-success \
  source-rss-success \
  source-api-success \
  source-document-success \
  source-blocked \
  source-rate-limited \
  source-adapter-mismatch \
  source-malformed-response \
  source-retry-exhausted \
  source-missing-artifact
do
  uv run --python python3.12 --extra dev veracrawl-source run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run network and browser acquisition fixtures:

```sh
for fixture in \
  network-http-success \
  network-http-redirect \
  network-browser-readonly \
  network-robots-blocked \
  network-private-denied \
  network-egress-denied \
  network-rate-budget \
  network-size-budget \
  network-redirect-denied \
  network-timeout \
  network-browser-unsafe-side-effect
do
  uv run --python python3.12 --extra dev veracrawl-network run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run normalize and extract fixtures:

```sh
for fixture in \
  process-static-basic \
  process-link-provenance \
  process-anchored-candidate \
  process-missing-raw \
  process-empty-content \
  process-anchor-gap
do
  uv run --python python3.12 --extra dev veracrawl-process run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run evidence and publication fixtures:

```sh
for fixture in \
  evidence-field-coverage \
  evidence-verification-review \
  evidence-publication-success \
  evidence-missing-anchor \
  evidence-verification-conflict \
  evidence-policy-denied \
  evidence-replay-gap \
  evidence-candidate-direct-publication
do
  uv run --python python3.12 --extra dev veracrawl-evidence run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run basic site graph fixtures:

```sh
for fixture in \
  graph-url-hyperlink \
  graph-canonical-redirect \
  graph-page-structure \
  graph-missing-input \
  graph-rebuild-mismatch \
  graph-as-evidence
do
  uv run --python python3.12 --extra dev veracrawl-graph run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run advanced graph projection fixtures:

```sh
for fixture in \
  projection-rebuild-success \
  graph-signal-frontier-review \
  temporal-graph-foundation \
  projection-missing-watermark \
  projection-mismatch \
  graph-signal-as-evidence
do
  uv run --python python3.12 --extra dev veracrawl-projection run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run memory kernel fixtures:

```sh
for fixture in \
  memory-write-retrieve-success \
  memory-invalidation-exclusion \
  cross-scope-sanitized-memory \
  poisoned-memory-blocked \
  unauthorized-cross-scope-memory \
  memory-as-evidence
do
  uv run --python python3.12 --extra dev veracrawl-memory run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run multi-agent repair fixtures:

```sh
for fixture in \
  multi-agent-repair-success \
  coordination-arbitration-success \
  repair-loop-evidence-success \
  owner-service-bypass \
  unresolved-coordination-conflict \
  agent-reasoning-as-evidence
do
  uv run --python python3.12 --extra dev veracrawl-agent-workflow run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run review/replay/ops console fixtures:

```sh
for fixture in \
  review-console-success \
  replay-audit-success \
  quality-dashboard-success \
  missing-review-evidence \
  unresolved-failure-without-recovery \
  stale-dashboard-projection \
  unsafe-recovery-without-review
do
  uv run --python python3.12 --extra dev veracrawl-ops run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run export connector fixtures:

```sh
for fixture in \
  export-file-success \
  export-api-success \
  export-correction-withdrawal-success \
  export-missing-receipt \
  duplicate-export-idempotency \
  withdrawal-missing-mapping \
  destination-unsupported-withdrawal \
  correction-without-withdrawal
do
  uv run --python python3.12 --extra dev veracrawl-export run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run scale hardening fixtures:

```sh
for fixture in \
  scale-sharding-success \
  backpressure-autoscale-success \
  dead-letter-recovery-success \
  stale-lease-without-recovery \
  unfair-site-starvation \
  autoscale-without-policy \
  dead-letter-missing-failure-record \
  replay-missing-scale-refs
do
  uv run --python python3.12 --extra dev veracrawl-scale run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run persistence and queue runtime fixtures:

```sh
for fixture in \
  persistence-transaction-success \
  idempotent-replay-success \
  queue-lease-recovery-success \
  non-atomic-commit \
  idempotency-not-persisted \
  event-log-gap \
  outbox-dispatch-missing \
  artifact-index-missing \
  lease-heartbeat-missing
do
  uv run --python python3.12 --extra dev veracrawl-persistence run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run concrete persistence adapter fixtures:

```sh
for fixture in \
  sqlite-adapter-conformance-success \
  sqlite-reopen-idempotency-success \
  sqlite-queue-recovery-success \
  postgres-adapter-contract-harness \
  postgres-runtime-unavailable \
  adapter-missing-capability \
  sqlite-idempotency-gap \
  sqlite-event-cursor-gap \
  sqlite-outbox-gap \
  sqlite-migration-missing
do
  uv run --python python3.12 --extra dev veracrawl-persistence-adapter run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run operational Postgres adapter fixtures with a live DSN:

```sh
for fixture in \
  postgres-adapter-conformance-success \
  postgres-reopen-idempotency-success \
  postgres-queue-recovery-success
do
  uv run --python python3.12 --extra dev --extra postgres veracrawl-persistence-adapter run \
    tests/fixtures/$fixture \
    --profile target \
    --postgres-dsn "$VERACRAWL_POSTGRES_DSN" \
    --out .veracrawl-test-runs/$fixture
done
```

Run the Docker-backed live Postgres integration gate:

```sh
VERACRAWL_POSTGRES_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres \
  pytest tests/integration/test_postgres_persistence_adapter_live.py
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
