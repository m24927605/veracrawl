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
the local network/browser acquisition runtime, the live HTTP acquisition runtime,
the structured source adapters runtime, the browser snapshot runtime, the
normalize/extract plane, the
evidence/publication spine, the basic site graph spine, the advanced graph
projection spine, the memory kernel spine, the multi-agent repair spine, the
agent runtime adapter operational gate, the model provider adapter operational
gate, the review/replay/ops console spine, the export connector spine, the scale
hardening spine, and the production
persistence/queue runtime spine.
The production persistence runtime wiring gate connects the production run-control
API to port-shaped canonical metadata, event, outbox, idempotency, artifact
index, and queue lease persistence. `veracrawl-production-persistence` proves
approved run-control state survives adapter reopen, duplicate replay creates no
duplicate event/outbox side effects, and queue recovery preserves heartbeat,
dead-letter, failure, recovery, policy, and replay refs without importing
concrete database, broker, object-store, browser, model, or agent framework
clients into core.
The live HTTP acquisition runtime composes that production spine with
adapter-owned HTTP acquisition. `veracrawl-live-http` proves an authorized local
HTTP page can move through run control, production persistence, network/source
adapter ports, source observation records, artifacts, content hashes, canonical
URL refs, command/event/outbox refs, and replay refs. Scope denial,
private-network denial, malformed responses, missing artifacts, replay mismatch,
and direct-source bypass fail with typed diagnostics; core still does not import
the concrete HTTP adapter.
The structured source adapters runtime adds sitemap, RSS/feed, API-like,
document, and file-import source family support behind source adapter ports.
`veracrawl-structured-source` proves adapter-owned parsing can produce source
adapter result refs, natural output refs, artifacts, evidence seed refs, content
hash refs, family-specific refs, policy refs, command/event/outbox refs, and
replay refs without making core parse fixture files directly.
The browser snapshot runtime adds a policy-gated browser aggregate for
JavaScript-required pages. `veracrawl-browser-snapshot` proves browser snapshots
must preserve live HTTP and structured source prerequisite refs, sandbox policy
refs, browser interaction refs, DOM/screenshot/network trace/console/timing
artifacts, browser budget refs, prompt-taint boundary refs, command/event/outbox
refs, and replay refs. Egress denial, unsafe interaction, budget exhaustion,
prompt-tainted content, missing artifacts, and replay mismatch fail with typed
diagnostics while concrete browser engines remain behind replaceable adapters.
The credentialed session runtime adds an authorized session aggregate behind a
session adapter port. `veracrawl-credentialed-session` proves credentialed
paths must preserve live HTTP and browser snapshot prerequisite refs, credential
scope/origin/approval refs, credential use audit refs, redacted session artifact
refs, redaction map refs, redacted replay refs, command/event/outbox refs, and
replay refs without persisting raw secrets or adapter-native session state.
Missing authorization, out-of-scope use, raw secret leakage, unsafe credential
use, missing audit, missing redacted replay, and replay mismatch fail with typed
diagnostics.
The live normalization and site understanding runtime turns acquired live
artifacts into normalized documents, normalization manifests, source anchors,
link provenance or deterministic no-link analysis, page type classifications,
site model refs, derived-context refs, command/event/outbox refs, and replay
refs. `veracrawl-live-normalization` proves listing, detail, and browser-shaped
pages can be normalized from real local HTTP acquisitions while missing upstream
refs, empty content, missing anchor maps, missing site models, and replay
mismatch fail with typed diagnostics. Derived site understanding remains
planning context and must not be treated as source evidence.
The schema extraction candidate runtime turns live normalization results into
schema-bound extraction strategies and anchored candidates with schema
validation refs, framework-neutral model/tool trace refs, candidate field anchor
refs, confidence refs, command/event/outbox refs, and replay refs.
`veracrawl-schema-extraction` proves declared schemas, approved exploratory
schemas, and browser-shaped normalized content can create intermediate
candidates without producing published outputs. Missing normalization, schema
validation failure, missing anchors, missing model/tool trace refs, direct
candidate publication, drift repair, and replay mismatch produce typed failure
or needs-review reports.
The live evidence and verification runtime turns schema extraction candidates
into source-backed evidence packets, evidence anchors, evidence manifests,
verification decisions, review refs, freshness refs, policy/privacy refs,
command/event/outbox refs, and replay refs. `veracrawl-live-evidence` proves
that passing candidates remain unpublishable until evidence and verification
are present. Missing schema extraction, missing source anchors, stale evidence,
contradictory evidence, graph-only evidence, memory-only evidence, verification
conflict, publication bypass, and replay mismatch produce typed failure or
needs-review reports without emitting published outputs.
The result publication and export runtime turns verified evidence into
published outputs, output manifests, Result API snapshots, destination-neutral
export jobs, delivery receipts, withdrawal refs, correction refs, policy/privacy
refs, command/event/outbox refs, and replay refs. `veracrawl-result-publication`
proves that outputs cannot be exported directly from candidates or published
without evidence, accepted verification, privacy lifecycle, publication policy,
delivery receipt, withdrawal/correction, and replay lineage.
The real agent/model adapter runtime composes model providers and agent
frameworks through VeraCrawl ports for planner, extractor, and repair turns.
`veracrawl-agent-model-runtime` proves local runtime adapters can execute those
turns through port bindings while core persists only canonical requests,
responses, traces, adapter runtime refs, policy/security refs, command/event
refs, and replay refs. Missing external SDKs, provider credentials, or wrapper
callables remain `needs_review`; raw prompts/responses/credentials,
framework-native state, provider-native transcripts, unsupported adapters, and
core adapter imports fail deterministically.
The concrete persistence adapter spine adds a standard-library SQLite adapter,
Postgres contract descriptor, operational Postgres JSONB adapter, core adapter
conformance harness, migration records, adapter conformance reports, adapter
fixtures, and dynamic adapter CLI loading without importing concrete storage
into core.
The operational queue broker adapter spine adds Redis/Valkey-style broker
contracts, a core conformance harness, a Redis adapter behind optional runtime
loading, queue broker operation records, no-runtime `needs_review` reporting,
negative broker fixtures, live Redis/Docker gates, and dynamic CLI loading
without importing queue clients into core.
The operational object store adapter spine adds S3-compatible artifact storage
contracts, a core conformance harness, a MinIO/S3 adapter behind optional runtime
loading, object operation records, no-runtime `needs_review` reporting, negative
object-store fixtures, live MinIO/Docker gates, and dynamic CLI loading without
importing object-store SDKs into core.
The operational runtime infrastructure gate composes the live Postgres,
Redis/Valkey, and S3-compatible adapters into one acceptance report so
metadata/event/outbox/idempotency refs, queue broker refs, object artifact refs,
policy refs, and replay refs are validated together rather than as isolated
adapter passes.
The operational disaster recovery gate builds on that live substrate and proves
DR restore plans, ordered restore phases, metadata restore, artifact
reachability, event replay, projection rebuild, export reconciliation,
failure/recovery refs, policy refs, and replay refs in one operator-visible DR
report. It can claim `pass` only when the live integrated infrastructure report
contributes refs in the same run. It is not a claim that managed cloud backup,
cross-region replication, deployment automation, production observability,
alerting backends, or production worker fleets are ready.
The operational observability gate proves backend-neutral metrics, traces,
alerts, runbook actions, cost/quality signals, dashboard projection watermarks,
failure/recovery refs, DR refs, redaction refs, policy refs, command/event/outbox
refs, collector handoff refs, telemetry backend refs, and replay refs in one
operator-visible report. It can claim `pass` only through canonical VeraCrawl
observability contracts and backend/collector handoff refs. It is not a claim
that managed Prometheus, OpenTelemetry collectors, Grafana dashboards, cloud
monitoring, paging integrations, deployment automation, or production worker
fleets are ready.
The security/privacy lifecycle gate proves target security and lifecycle
contracts for egress/private-network denial, prompt-taint boundaries,
credential-use audit, zero credential prompt leakage, artifact redaction,
tombstone/delete/legal-hold/retention behavior, projection cleanup, redacted
replay, observability refs, policy refs, command/event/outbox refs, and
failure/recovery refs. It cannot claim `pass` from ordinary policy refs alone
and remains framework-, browser-, cloud-, telemetry-, and security-vendor-neutral
inside core.
The agent runtime adapter operational gate proves that model provider and agent
framework adapters can map OpenAI Agent SDK, LangChain, LangGraph, CrewAI,
AutoGen, Semantic Kernel, and future frameworks into canonical VeraCrawl
`AgentRunRequest`, `AgentRunResult`, trace, command, policy, observability,
security/privacy, and replay refs. It cannot claim `pass` from framework-native
state, raw prompts/responses, unsupported frameworks, or missing model/tool,
security/privacy, observability, or replay refs. Missing live SDK/runtime refs
remain `needs_review` rather than a false operational pass.
The model provider adapter operational gate proves that OpenAI, Anthropic,
Google Gemini, OpenAI-compatible endpoint, local model runtime, and future
provider adapters map into canonical `ModelRequest`, `ModelResponse`,
`ModelCallTrace`, `ContextBundleTrace`, agent run/action, command, policy,
observability, security/privacy, and replay refs. It cannot claim `pass` from
raw prompts/responses, raw credentials, provider-native transcripts, unsafe tool
suggestions, unsupported providers, or missing context/security/replay refs.
Missing live provider runtime/API credentials remain `needs_review`.
The source coverage adapter operational gate proves that HTTP, sitemap, RSS/feed,
browser snapshot, authorized session, API-like source, document source, file
import, manual seed, and prior snapshot adapters map into canonical
`SourceAdapterSpec`, `SourceAdapterResult`, natural output, fetch/browser/session,
document/API, command, policy, observability, security/privacy, event/outbox, and
replay refs. It cannot claim `pass` from adapter-native state, raw secrets,
unsafe browser side effects, unsupported adapters, or missing adapter-specific
refs. Missing live source/browser/parser/session/API runtime refs remain
`needs_review`.
The product acceptance gate proves the target buyer-value workflows and minimum
product gates in `docs/11-target-testing-and-acceptance.md`: multi-site
onboarding, objective-to-plan approval, dynamic/auth/document/API crawl,
evidence review, conflict resolution, drift repair, memory reuse,
export/withdrawal, replay/audit, and operator recovery. It cannot claim `pass`
from technical contract-only reports, mock UI screenshots, scaffold manifests,
degraded runs, or false `complete`/`verified`/`operational` labels.
The target crawl runtime turns the target contracts into an executable
objective-to-report path. `veracrawl-target-runtime` runs deterministic
multi-pattern crawl fixtures through policy-gated frontier refs, source
observations, framework-neutral AI recommendations, evidence/verification,
graph refs, export receipts, privacy refs, and replay bundle closure. The
success fixture covers at least seven website patterns in one run; drift repair,
needs-review, policy-denied, prompt-injection, missing-evidence,
replay-mismatch, partial-export, and false-complete fixtures prove unsafe or
deceptive completion claims cannot pass.
The source-backed target runtime extends that path with local multi-pattern
source corpora. Source-backed fixtures read HTML, XML, JSON, and text files from
the fixture directory, derive content-hash refs, source observation records,
accepted output refs, evidence refs, graph refs, export receipts, and replay refs
from actual file content, and fail when evidence, policy, prompt-taint, replay,
or export completeness gates are not satisfied. This remains a generic target
runtime foundation, not a single-site scraper.
The adapter-backed target runtime adds source adapter lineage to that proof.
Adapter-backed fixtures materialize deterministic local source adapter outputs
outside target runtime core, then pass canonical adapter-backed records into the
runner. A complete report must expose adapter-backed source refs, source adapter
result refs, adapter output refs, source observations, content hashes, evidence,
graph, export, policy, command/event/outbox, and replay refs. Missing adapter
results, adapter output mismatches, adapter policy denials, replay mismatches,
and direct source bypass attempts fail or block deterministically.
The processing/evidence target runtime extends adapter-backed proof through
canonical processing, evidence, and publication lineage. Processing fixtures
materialize normalized document refs, extraction candidate refs, candidate
anchors, evidence packet refs, evidence anchors, publication report refs,
policy decisions, and replay refs outside core, then pass canonical records to
the runner. A complete report cannot bypass this chain, use graph-only derived
context as source evidence, publish without a publication report, or claim
success when normalization, candidate anchors, or evidence packets are missing.
The production run-control gate turns the post-037 roadmap into an executable
control-plane slice. `veracrawl-run-control` proves that projects, site scopes,
objectives, plans, approvals, budgets, policy snapshots, run lifecycle actions,
command results, events, and replay refs exist before downstream live
acquisition can start. Missing approval, policy denial, missing budget, invalid
transitions, and missing replay fail with typed operator-visible diagnostics.
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
The multi-agent orchestration and repair runtime adds framework-neutral workflow,
handoff, coordination decision, crawl/extraction/drift repair signal, repair
replay report, controlled tool refs, owner-service command refs, row 049
agent/model adapter refs, row 047 live evidence refs, arbitration, review
escalation, and agent-reasoning-as-evidence checks. It is not a claim that any
concrete external agent framework, vendor model account, review UI, export
delivery, distributed persistence, production browser rendering, or production
scale operations are complete.
The graph and memory production runtime composes row 045 live normalization,
row 047 live evidence, row 050 multi-agent repair, advanced graph projections,
graph frontier/review decisions, temporal KG records, and memory kernel refs
into one replayable production report. It proves graph and memory influence
planning, frontier priority, and repair explanations while source evidence and
verification remain mandatory and graph/memory-as-evidence, stale memory, missing
invalidation, missing explanations, and replay gaps fail deterministically.
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
The worker orchestration and scale runtime composes production persistence,
queue broker conformance, live acquisition, live normalization, live evidence,
and scale recovery refs into one replayable worker runtime report.
`veracrawl-worker-orchestration` proves frontier, fetch, browser, processing,
verification, review, export, projection, and recovery worker pools all expose
heartbeats, capacity refs, queue items, leases, fencing tokens, visibility
timeouts, retry/dead-letter/failure/recovery refs, duplicate suppression,
backpressure, autoscaling, policy, command/event/outbox, and replay refs.
Missing persistence, missing queue broker, unrecovered stale leases, missing
heartbeats, hidden dead letters, duplicate pollution, backpressure without
policy, and replay gaps fail deterministically.
The ops replay and observability runtime composes result publication/export,
worker orchestration, ops console, and operational observability into one
operator-visible target aggregate. `veracrawl-ops-runtime` proves operators can
inspect, pause/resume, replay, recover, explain bad outputs, view graph/debug
context, track export/withdrawal status, review alerts/cost, and verify
recovery through canonical refs. Missing row 048 publication, missing row 052
worker orchestration, missing ops console, missing observability, stale
dashboards, unresolved recovery, unsafe operator action, and replay mismatch
fail with typed diagnostics.
The production benchmark and release gate composes target runtime, source
coverage, product acceptance, security/privacy, result publication/export,
worker orchestration, and ops runtime refs into one auditable production release
decision. `veracrawl-release-gate` proves the authorized deterministic benchmark
cannot pass unless source, processing, evidence, verification, publication,
export, replay, ops, scale, safety, policy, command/event/outbox, artifact,
redaction, SLO, release decision, and audit refs are present. Missing lower
runtime gates, SLO violations, release blockers, false-ready status, and replay
mismatch fail with typed diagnostics.
The real-world benchmark corpus gate supplements deterministic release gates
with authorized public website validation. `veracrawl-real-benchmark` runs a
manifest-declared corpus through origin allowlists, robots preflight,
private-network denial, live HTTP acquisition, coarse observation oracles,
artifact/content hash refs, source observation refs, command/event/outbox refs,
and replay refs. The default corpus covers static, listing/detail, pagination,
and API-like public targets without site-specific scraper code.
The concrete persistence adapter spine proves executable SQLite adapter
semantics for transactions, migrations, idempotency, event cursors, outbox,
artifact index, queue leases, and replay refs. The Postgres descriptor is
contract-only and returns `needs_review`; the operational Postgres adapter can
claim `pass` only against an explicit live DSN or Docker-backed live gate. It is
not a claim that external queue brokers, object storage, cloud deployment,
managed Postgres operations, or observability backends are production-ready.
The operational queue broker adapter spine proves Redis queue broker semantics
for enqueue, idempotent duplicate enqueue after reopen, lease, fencing token,
visibility timeout, heartbeat, ack, nack, retry requeue, dead letter, fairness,
backpressure, policy, and replay refs. It can claim `pass` only against an
explicit live Redis URL or Docker-backed live gate. It is not a claim that
managed Redis, Kafka, cloud queues, production autoscaling, production worker
fleets, or observability backends are production-ready.
The operational object store adapter spine proves S3-compatible artifact storage
semantics for put, duplicate put after reopen, get, head, list, delete, content
digest verification, lifecycle, retention, privacy, policy, and replay refs. It
can claim `pass` only against an explicit live S3-compatible endpoint or
Docker-backed MinIO gate. It is not a claim that managed S3, cloud IAM, CDN,
encryption key management, production retention workers, or observability
backends are production-ready.
The operational runtime infrastructure gate proves that live Postgres,
Redis/Valkey, and S3-compatible adapters can contribute one replayable runtime
infrastructure report. It can claim `pass` only when all three live adapter
families contribute refs in the same run. It is not a claim that managed cloud,
deployment, production worker fleets, metrics/tracing backends, production
observability, browser rendering, model SDKs, or agent frameworks are
production-ready.
The operational observability gate adds canonical observability contracts and a
`veracrawl-observability` fixture runner. `observability-runtime-unavailable`
and `observability-data-surface-only` return `needs_review`; missing metrics,
traces, alerts, runbooks, dashboard watermarks, DR refs, redaction refs, replay
refs, secret leakage, and unsafe runbook actions fail deterministically. This is
backend-neutral operational proof, not managed observability infrastructure.

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

Run live HTTP acquisition fixtures:

```sh
for fixture in \
  live-http-success \
  live-http-redirect \
  live-http-scope-denied \
  live-http-private-denied \
  live-http-malformed-response \
  live-http-missing-artifact \
  live-http-replay-mismatch \
  live-http-direct-source-bypass
do
  uv run --python python3.12 --extra dev veracrawl-live-http run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run structured source adapter fixtures:

```sh
for fixture in \
  structured-source-adapters-success \
  structured-source-adapters-policy-denied \
  structured-source-adapters-malformed-source \
  structured-source-adapters-unsupported-adapter \
  structured-source-adapters-replay-mismatch
do
  uv run --python python3.12 --extra dev veracrawl-structured-source run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run browser snapshot fixtures:

```sh
for fixture in \
  browser-snapshot-success \
  browser-snapshot-egress-denied \
  browser-snapshot-unsafe-interaction \
  browser-snapshot-budget-exceeded \
  browser-snapshot-prompt-tainted-content \
  browser-snapshot-missing-artifact \
  browser-snapshot-replay-mismatch
do
  uv run --python python3.12 --extra dev veracrawl-browser-snapshot run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run credentialed session fixtures:

```sh
for fixture in \
  credentialed-session-success \
  credentialed-session-missing-authorization \
  credentialed-session-out-of-scope \
  credentialed-session-raw-secret-leak \
  credentialed-session-unsafe-use \
  credentialed-session-missing-audit \
  credentialed-session-missing-redacted-replay \
  credentialed-session-replay-mismatch
do
  uv run --python python3.12 --extra dev veracrawl-credentialed-session run \
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

Run target output type coverage fixtures:

```sh
for fixture in \
  output-type-coverage-success \
  output-type-coverage-runtime-unavailable \
  output-type-coverage-missing-output-type \
  output-type-coverage-unsupported-output-type \
  output-type-coverage-derived-context-as-evidence \
  output-type-coverage-candidate-as-evidence \
  output-type-coverage-graph-as-evidence \
  output-type-coverage-memory-as-evidence \
  output-type-coverage-agent-reasoning-as-evidence \
  output-type-coverage-temporal-kg-as-evidence \
  output-type-coverage-missing-table-cell-evidence \
  output-type-coverage-missing-file-lifecycle \
  output-type-coverage-missing-dataset-item-evidence \
  output-type-coverage-missing-fact-verification \
  output-type-coverage-missing-replay
do
  uv run --python python3.12 --extra dev veracrawl-output-coverage run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run target website pattern coverage fixtures:

```sh
for fixture in \
  website-pattern-coverage-success \
  website-pattern-runtime-unavailable \
  website-pattern-missing-pattern \
  website-pattern-unsupported-pattern \
  website-pattern-single-site-assumption \
  website-pattern-scaffold-only \
  website-pattern-missing-source-adapter \
  website-pattern-missing-site-model \
  website-pattern-missing-output-evidence \
  website-pattern-missing-pattern-specific-refs \
  website-pattern-unsafe-interaction \
  website-pattern-missing-replay
do
  uv run --python python3.12 --extra dev veracrawl-website-patterns run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run target product acceptance fixtures:

```sh
for fixture in \
  product-acceptance-success \
  product-acceptance-runtime-unavailable \
  product-acceptance-missing-workflow \
  product-acceptance-missing-minimum-gate \
  product-acceptance-missing-evidence \
  product-acceptance-missing-replay \
  product-acceptance-missing-operator-visibility \
  product-acceptance-missing-policy \
  product-acceptance-missing-workflow-specific-refs \
  product-acceptance-scaffold-only \
  product-acceptance-contract-only \
  product-acceptance-false-complete-status \
  product-acceptance-degraded-operational \
  product-acceptance-missing-export-reconciliation
do
  uv run --python python3.12 --extra dev veracrawl-product-acceptance run \
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

Run graph-driven frontier/review runtime gate fixtures:

```sh
for fixture in \
  graph-frontier-review-success \
  graph-frontier-review-runtime-unavailable \
  graph-frontier-review-signal-as-evidence \
  graph-frontier-review-missing-source-graph \
  graph-frontier-review-missing-explanation \
  graph-frontier-review-unauthorized-frontier-mutation \
  graph-frontier-review-missing-review-route \
  graph-frontier-review-missing-replay \
  graph-frontier-review-unsupported-signal
do
  uv run --python python3.12 --extra dev veracrawl-graph-frontier-review run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run temporal KG identity projection gate fixtures:

```sh
for fixture in \
  temporal-kg-projection-success \
  temporal-kg-false-merge-adjudicated \
  temporal-kg-false-split-superseded \
  temporal-kg-runtime-unavailable \
  temporal-kg-provisional-identity \
  temporal-kg-projection-as-evidence \
  temporal-kg-missing-canonical-source \
  temporal-kg-missing-bitemporal-refs \
  temporal-kg-false-merge-without-adjudication \
  temporal-kg-false-split-without-supersession \
  temporal-kg-missing-replay
do
  uv run --python python3.12 --extra dev veracrawl-temporal-kg run \
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
  crawl-repair-success \
  extraction-repair-success \
  owner-service-bypass \
  unresolved-coordination-conflict \
  agent-reasoning-as-evidence \
  multi-agent-missing-agent-model-runtime \
  multi-agent-missing-live-evidence \
  multi-agent-missing-tool-gate \
  multi-agent-missing-owner-command \
  multi-agent-replay-mismatch
do
  uv run --python python3.12 --extra dev veracrawl-agent-workflow run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run graph/memory production runtime fixtures:

```sh
for fixture in \
  graph-memory-production-success \
  graph-memory-frontier-priority-success \
  graph-memory-repair-explanation-success \
  graph-memory-missing-live-normalization \
  graph-memory-missing-live-evidence \
  graph-memory-missing-multi-agent \
  graph-memory-graph-as-evidence \
  graph-memory-memory-as-evidence \
  graph-memory-stale-memory \
  graph-memory-missing-invalidation \
  graph-memory-missing-frontier-explanation \
  graph-memory-replay-mismatch
do
  uv run --python python3.12 --extra dev veracrawl-graph-memory-runtime run \
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

Run worker orchestration fixtures:

```sh
for fixture in \
  worker-orchestration-production-success \
  worker-orchestration-worker-crash-recovered \
  worker-orchestration-backpressure-autoscale-success \
  worker-orchestration-missing-persistence \
  worker-orchestration-missing-queue-broker \
  worker-orchestration-stale-lease-unrecovered \
  worker-orchestration-missing-heartbeat \
  worker-orchestration-dead-letter-hidden \
  worker-orchestration-duplicate-pollution \
  worker-orchestration-backpressure-without-policy \
  worker-orchestration-replay-mismatch
do
  uv run --python python3.12 --extra dev veracrawl-worker-orchestration run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run ops replay/observability runtime fixtures:

```sh
for fixture in \
  ops-runtime-review-replay-success \
  ops-runtime-incident-recovery-success \
  ops-runtime-cost-alert-success \
  ops-runtime-missing-publication \
  ops-runtime-missing-worker-orchestration \
  ops-runtime-missing-ops-console \
  ops-runtime-missing-observability \
  ops-runtime-stale-dashboard \
  ops-runtime-unresolved-recovery \
  ops-runtime-unsafe-operator-action \
  ops-runtime-replay-mismatch
do
  uv run --python python3.12 --extra dev veracrawl-ops-runtime run \
    tests/fixtures/$fixture \
    --profile target \
    --telemetry-backend-ref telemetry-backend:local \
    --collector-handoff-ref collector-handoff:local \
    --out .veracrawl-test-runs/$fixture
done
```

Run production benchmark release gate fixtures:

```sh
for fixture in tests/fixtures/production-release-*; do
  uv run --python python3.12 --extra dev veracrawl-release-gate run \
    "$fixture" \
    --profile target \
    --telemetry-backend-ref telemetry-backend:local \
    --collector-handoff-ref collector-handoff:local \
    --out ".veracrawl-test-runs/$(basename "$fixture")"
done
```

Run the real-world public benchmark corpus:

```sh
uv run --python python3.12 --extra dev veracrawl-real-benchmark run \
  tests/fixtures/real-world-public-corpus \
  --profile target \
  --out .veracrawl-real-runs/real-world-public-corpus
```

Run the real-world public AI agent benchmark:

```sh
uv run --python python3.12 --extra dev veracrawl-real-ai-benchmark run \
  tests/fixtures/real-world-ai-agent-public-corpus \
  --profile target \
  --out .veracrawl-real-runs/real-world-ai-agent-public-corpus
```

Run the same benchmark with a hosted OpenAI model through the framework-neutral
model provider port:

```sh
set -a; source ~/.env; set +a
uv run --python python3.12 --extra dev veracrawl-real-ai-benchmark run \
  tests/fixtures/real-world-ai-agent-public-corpus \
  --profile target \
  --model-provider openai \
  --openai-model gpt-5.4-mini \
  --out .veracrawl-real-runs/real-world-ai-agent-openai-public-corpus
```

The AI benchmark first runs the public corpus, then invokes VeraCrawl's
framework-neutral model and agent ports for crawl planning, site understanding,
extraction candidate generation, and verification/repair decisions. Passing
reports include model call, agent action, tool call, context bundle, source
anchor, candidate, evidence/verification gate, command/event/outbox, and replay
refs. Model or agent output is never accepted as source evidence.

Run the Taiwan/United States top ecommerce live corpus:

```sh
uv run --python python3.12 --extra dev veracrawl-real-benchmark run \
  tests/fixtures/top-ecommerce-public-corpus \
  --profile target \
  --out .veracrawl-real-runs/top-ecommerce-public-corpus
```

Run the same ecommerce corpus through the AI agent benchmark with a hosted
OpenAI model:

```sh
set -a; source ~/.env; set +a
uv run --python python3.12 --extra dev veracrawl-real-ai-benchmark run \
  tests/fixtures/top-ecommerce-ai-agent-corpus \
  --profile target \
  --model-provider openai \
  --openai-model gpt-5.4-mini \
  --out .veracrawl-real-runs/top-ecommerce-ai-agent-corpus-openai
```

This ecommerce benchmark covers public homepage entry points for Shopee Taiwan,
momo Shopping, PChome 24h, Amazon US, Walmart US, and eBay US. The Taiwan
selection is a documented local ecommerce corpus; traffic-only ranking sources
may place Coupang or Taobao as a third domain depending on methodology. Passing
results prove policy-gated live acquisition plus real AI/model/agent trace
participation for those public entry points, not full category/product deep
crawl production readiness across the complete sites.

Run the expanded real-world public quality corpus:

```sh
uv run --python python3.12 --extra dev veracrawl-real-quality-corpus run \
  tests/fixtures/real-world-quality-corpus \
  --profile quality \
  --out .veracrawl-real-runs/real-world-quality-corpus
```

The quality corpus gate composes the row 055 public crawl runner with quality
thresholds and pattern coverage. Passing reports require at least 40 passing
targets, 15 passing origins, 10 passing pattern families, policy refs,
artifact/content hash/canonical URL refs, command/event/outbox refs, and replay
refs. This gate does not claim JS/browser quality, deep crawl quality,
field-level oracle quality, precision/recall, repair success, or final
production-quality release readiness; those are handled by the later quality
gates 059-064.

Run the JavaScript browser quality benchmark:

```sh
uv run --python python3.12 --extra dev --extra browser-playwright \
  veracrawl-browser-quality-benchmark run \
  tests/fixtures/browser-quality-corpus \
  --profile quality \
  --browser-adapter playwright \
  --out .veracrawl-real-runs/browser-quality-corpus
```

The browser quality gate compares HTTP-only evidence with browser-rendered DOM
evidence for JS-required targets. Passing reports require at least 8
browser-required targets with browser-only recovered oracle fragments,
DOM/screenshot/network/console/timing artifacts, rendered content hashes,
source anchors, browser budget refs, prompt-taint boundary refs,
command/event/outbox refs, and replay refs. Playwright is optional and
adapter-owned; core benchmark code depends on VeraCrawl ports/contracts, not a
browser engine. This gate does not claim deep crawl, credentialed browsing,
CAPTCHA solving, stealth automation, field-level oracle quality,
precision/recall, repair success, or final production-quality release readiness.

Run the multi-page deep crawl frontier benchmark:

```sh
uv run --python python3.12 --extra dev veracrawl-deep-crawl-benchmark run \
  tests/fixtures/deep-crawl-quality-corpus \
  --profile quality \
  --out .veracrawl-real-runs/deep-crawl-quality-corpus
```

The deep crawl gate covers at least 5 bounded fixture/public-style sites and 50
required pages through general frontier planning, pagination, detail pages,
sitemap/feed links, canonical duplicate suppression, off-origin/private-network
skips, robots-denied skips, AI-prioritized frontier decisions, graph refs,
source anchors, artifacts/content hashes, command/event/outbox refs, and replay
refs. AI/agent traces can influence priority but never serve as source evidence.
This gate does not claim field-level oracle quality, precision/recall, repair
success, or final production-quality release readiness.

Run the field-level oracle extraction benchmark:

```sh
uv run --python python3.12 --extra dev veracrawl-field-oracle-benchmark run \
  tests/fixtures/field-oracle-quality-corpus \
  --profile quality \
  --out .veracrawl-real-runs/field-oracle-quality-corpus
```

The field oracle gate evaluates at least 8 schemas and 200 expected fields. Each
accepted field carries source anchors, artifacts, content hashes, normalized
value refs, evidence packet refs, verification decision refs,
command/event/outbox refs, and replay refs. Model/agent traces may explain
candidate generation but cannot satisfy evidence. This gate emits field-level
JSON for later precision/recall, but it does not claim precision/recall, repair
success, or final production-quality release readiness.

Run the precision/recall quality metrics benchmark:

```sh
uv run --python python3.12 --extra dev veracrawl-quality-metrics run \
  tests/fixtures/precision-recall-quality \
  --profile quality \
  --out .veracrawl-real-runs/precision-recall-quality
```

The quality metrics gate computes corpus and slice precision, recall, F1,
false-positive, false-negative, abstention, unsupported-field, and needs-review
rates from field confusion records. Passing reports enforce precision >= 0.98,
recall >= 0.90, F1 >= 0.94, and critical-field precision >= 0.99, with evidence,
publication gate, policy, command/event/outbox, and replay refs for every metric
component. This gate does not run repair or claim final production-quality
release readiness.

Run the repair success rate benchmark:

```sh
uv run --python python3.12 --extra dev veracrawl-repair-quality-benchmark run \
  tests/fixtures/repair-success-quality \
  --profile quality \
  --out .veracrawl-real-runs/repair-success-quality
```

The repair quality gate runs seeded crawl planning, fetch/browser,
normalization, extraction, verification, publication, drift, and replay repair
cases. Passing reports require at least 30 seeded cases, repair success rate >=
0.80 for repairable cases, unsafe bypass rate = 0, unresolved critical repair
rate = 0, framework-neutral model/agent/tool/context traces for AI-assisted
repairs, owner-service command refs, before/after evidence, rollback/escalation
refs, policy refs, command/event/outbox refs, and replay refs. This gate does
not claim final production-quality release readiness.

Run the final quality release gate:

```sh
uv run --python python3.12 --extra dev veracrawl-quality-release-gate run \
  tests/fixtures/quality-release-ready \
  --profile quality \
  --out .veracrawl-real-runs/quality-release-ready
```

The quality release gate aggregates the quality benchmark reports from rows
058-063, requires at least three stability runs, and blocks release on missing
quality gates, cost budget violations, latency SLO violations, retry rate
violations, stability regressions, replay gaps, false-ready status, or missing
command/event/outbox refs. Passing reports include prior gate refs, SLO metric
refs, audit refs, release decision refs, policy refs, command/event/outbox refs,
and replay refs.

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

Run queue broker no-runtime and negative fixtures:

```sh
for fixture in \
  redis-broker-runtime-unavailable \
  broker-missing-fencing-token \
  broker-missing-heartbeat \
  broker-missing-dead-letter
do
  uv run --python python3.12 --extra dev --extra queue-redis veracrawl-queue-broker run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run operational Redis queue broker fixtures with a live URL:

```sh
for fixture in \
  redis-broker-conformance-success \
  redis-broker-idempotency-success \
  redis-broker-dead-letter-success
do
  uv run --python python3.12 --extra dev --extra queue-redis veracrawl-queue-broker run \
    tests/fixtures/$fixture \
    --profile target \
    --redis-url "$VERACRAWL_REDIS_URL" \
    --out .veracrawl-test-runs/$fixture
done
```

Run the Docker-backed live Redis integration gate:

```sh
VERACRAWL_REDIS_DOCKER=1 uv run --python python3.12 --extra dev --extra queue-redis \
  pytest tests/integration/test_redis_queue_broker_live.py
```

Run object store no-runtime and negative fixtures:

```sh
for fixture in \
  s3-object-store-runtime-unavailable \
  object-store-missing-digest \
  object-store-missing-read-after-write \
  object-store-missing-delete-marker
do
  uv run --python python3.12 --extra dev --extra object-s3 veracrawl-object-store run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run operational S3-compatible object store fixtures with a live endpoint:

```sh
for fixture in \
  s3-object-store-conformance-success \
  s3-object-store-idempotency-success \
  s3-object-store-delete-success
do
  uv run --python python3.12 --extra dev --extra object-s3 veracrawl-object-store run \
    tests/fixtures/$fixture \
    --profile target \
    --endpoint-url "$VERACRAWL_S3_ENDPOINT_URL" \
    --bucket "$VERACRAWL_S3_BUCKET" \
    --access-key-id "$VERACRAWL_S3_ACCESS_KEY_ID" \
    --secret-access-key "$VERACRAWL_S3_SECRET_ACCESS_KEY" \
    --out .veracrawl-test-runs/$fixture
done
```

Run the Docker-backed live MinIO integration gate:

```sh
VERACRAWL_S3_DOCKER=1 uv run --python python3.12 --extra dev --extra object-s3 \
  pytest tests/integration/test_s3_object_store_live.py
```

Run integrated infrastructure no-runtime and negative fixtures:

```sh
for fixture in \
  operational-infrastructure-runtime-unavailable \
  infrastructure-missing-persistence-refs \
  infrastructure-missing-queue-refs \
  infrastructure-missing-object-refs \
  infrastructure-missing-replay-refs
do
  uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 \
    veracrawl-infrastructure run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run integrated infrastructure fixtures with live runtimes:

```sh
for fixture in \
  operational-infrastructure-success \
  operational-infrastructure-idempotency-success
do
  uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 \
    veracrawl-infrastructure run \
    tests/fixtures/$fixture \
    --profile target \
    --postgres-dsn "$VERACRAWL_POSTGRES_DSN" \
    --redis-url "$VERACRAWL_REDIS_URL" \
    --s3-endpoint-url "$VERACRAWL_S3_ENDPOINT_URL" \
    --s3-bucket "$VERACRAWL_S3_BUCKET" \
    --s3-access-key-id "$VERACRAWL_S3_ACCESS_KEY_ID" \
    --s3-secret-access-key "$VERACRAWL_S3_SECRET_ACCESS_KEY" \
    --out .veracrawl-test-runs/$fixture
done
```

Run the Docker-backed integrated infrastructure gate:

```sh
VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev \
  --extra postgres --extra queue-redis --extra object-s3 \
  pytest tests/integration/test_operational_infrastructure_live.py
```

Run operational DR no-runtime and negative fixtures:

```sh
for fixture in \
  dr-restore-runtime-unavailable \
  dr-restore-missing-metadata \
  dr-restore-missing-artifact-reachability \
  dr-restore-missing-event-replay \
  dr-restore-missing-projection-rebuild \
  dr-restore-missing-export-reconciliation \
  dr-restore-unresolved-refs \
  dr-restore-data-loss \
  dr-restore-unsafe-recovery-without-approval
do
  uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 \
    veracrawl-dr run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run the Docker-backed operational DR gate:

```sh
VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev \
  --extra postgres --extra queue-redis --extra object-s3 \
  pytest tests/integration/test_operational_disaster_recovery_live.py
```

Run security/privacy lifecycle fixtures:

```sh
for fixture in \
  security-privacy-success \
  security-privacy-policy-only \
  security-privacy-unsafe-network \
  security-privacy-prompt-injection \
  security-privacy-credential-leakage \
  security-privacy-missing-lifecycle \
  security-privacy-legal-hold-delete \
  security-privacy-missing-projection-cleanup \
  security-privacy-missing-redacted-replay \
  security-privacy-missing-observability
do
  uv run --python python3.12 --extra dev veracrawl-security-privacy run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run agent runtime adapter operational gate fixtures:

```sh
for fixture in \
  agent-runtime-adapter-success \
  agent-runtime-adapter-runtime-unavailable \
  agent-runtime-adapter-raw-prompt-leak \
  agent-runtime-adapter-framework-state-canonical \
  agent-runtime-adapter-missing-model-trace \
  agent-runtime-adapter-missing-tool-trace \
  agent-runtime-adapter-missing-replay \
  agent-runtime-adapter-missing-security-privacy \
  agent-runtime-adapter-unsupported-framework
do
  uv run --python python3.12 --extra dev veracrawl-agent-adapters run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run model provider adapter operational gate fixtures:

```sh
for fixture in \
  model-provider-adapter-success \
  model-provider-adapter-runtime-unavailable \
  model-provider-adapter-raw-prompt-leak \
  model-provider-adapter-raw-response-leak \
  model-provider-adapter-provider-state-canonical \
  model-provider-adapter-missing-context-trace \
  model-provider-adapter-missing-replay \
  model-provider-adapter-missing-security-privacy \
  model-provider-adapter-unsafe-tool-suggestion \
  model-provider-adapter-unsupported-provider
do
  uv run --python python3.12 --extra dev veracrawl-model-providers run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run real agent/model adapter runtime fixtures:

```sh
for fixture in \
  agent-model-adapter-local-runtime-success \
  agent-model-adapter-runtime-unavailable \
  agent-model-adapter-missing-run-control \
  agent-model-adapter-missing-live-normalization \
  agent-model-adapter-missing-schema-extraction \
  agent-model-adapter-unsupported-provider \
  agent-model-adapter-unsupported-framework \
  agent-model-adapter-raw-prompt-leak \
  agent-model-adapter-raw-response-leak \
  agent-model-adapter-raw-credential-leak \
  agent-model-adapter-framework-state-canonical \
  agent-model-adapter-provider-transcript-canonical \
  agent-model-adapter-missing-model-trace \
  agent-model-adapter-missing-tool-trace \
  agent-model-adapter-missing-replay \
  agent-model-adapter-core-import-boundary
do
  uv run --python python3.12 --extra dev veracrawl-agent-model-runtime run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run source coverage adapter operational gate fixtures:

```sh
for fixture in \
  source-coverage-adapter-success \
  source-coverage-adapter-runtime-unavailable \
  source-coverage-adapter-native-state-canonical \
  source-coverage-adapter-raw-secret-leak \
  source-coverage-adapter-missing-browser-refs \
  source-coverage-adapter-missing-credential-audit \
  source-coverage-adapter-missing-document-artifact \
  source-coverage-adapter-missing-api-payload \
  source-coverage-adapter-missing-replay \
  source-coverage-adapter-unsafe-browser-side-effect \
  source-coverage-adapter-unsupported-adapter
do
  uv run --python python3.12 --extra dev veracrawl-source-coverage run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run dynamic source adapter runtime foundation fixtures:

```sh
for fixture in \
  dynamic-source-runtime-success \
  dynamic-source-runtime-runtime-unavailable \
  dynamic-source-runtime-raw-secret-leak \
  dynamic-source-runtime-adapter-state-canonical \
  dynamic-source-runtime-missing-credential-audit \
  dynamic-source-runtime-missing-document-artifact \
  dynamic-source-runtime-missing-api-payload \
  dynamic-source-runtime-missing-replay \
  dynamic-source-runtime-unsafe-browser-side-effect \
  dynamic-source-runtime-unsupported-adapter
do
  uv run --python python3.12 --extra dev veracrawl-source-runtime run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
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
