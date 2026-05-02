<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- PRINCIPLE_1_NAME -> I. General-Purpose AI Agent Crawler
- PRINCIPLE_2_NAME -> II. Python, Ports, And Framework-Neutral Agents
- PRINCIPLE_3_NAME -> III. Evidence, Verification, And Replay Before Publication
- PRINCIPLE_4_NAME -> IV. Security, Policy, Credential, And Privacy Boundaries
- PRINCIPLE_5_NAME -> V. Executable Contracts And Test-First Acceptance
Added sections:
- Target Architecture Constraints
- Spec Kit Development Workflow
Removed sections:
- Placeholder SECTION_2_NAME and SECTION_3_NAME
Templates requiring updates:
- ✅ .specify/templates/spec-template.md
- ✅ .specify/templates/plan-template.md
- ✅ .specify/templates/tasks-template.md
Runtime guidance requiring updates:
- ✅ AGENTS.md
Extension hooks:
- ✅ before_constitution speckit.git.initialize executed; existing git repository detected and skipped
Deferred follow-ups:
- None
-->

# VeraCrawl Constitution

## Core Principles

### I. General-Purpose AI Agent Crawler

VeraCrawl MUST remain a powerful general-purpose AI agent web crawler.
Specifications, plans, tasks, and code MUST NOT narrow the product into a
single-site scraper, browser automation demo, vertical intelligence product, or
one-off extraction pipeline. Any V1/V2/V3 boundary is dependency sequencing and
validation strategy only; it MUST NOT weaken target architecture capability or
introduce assumptions that block general-purpose crawling across websites,
source patterns, schemas, and data domains.

AI capability MUST be used to maximize website understanding, crawl planning,
frontier prioritization, extraction, verification, repair, debugging, and
learning within authorized and replayable boundaries. Target architecture
planning MUST NOT be reduced because of staffing, schedule, sprint pressure, or
delivery speed.

Rationale: VeraCrawl's product value is the broad, durable crawling platform,
not a smaller scraper implementation that happens to use AI.

### II. Python, Ports, And Framework-Neutral Agents

VeraCrawl is a Python product unless an explicit constitution amendment changes
that decision. Core services, workers, contracts, policy checks, event handling,
and agent runtime abstractions MUST be planned and implemented in Python.

The AI agent runtime MUST remain framework-neutral and owned by VeraCrawl.
Core packages MUST depend on VeraCrawl-owned contracts, commands, events, ports,
and typed results, not on LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel,
model SDKs, storage clients, queue clients, browser libraries, or agent
framework-native state. Any such dependency MUST live behind a replaceable
adapter.

Code MUST preserve low coupling and high cohesion. Cross-module behavior MUST
flow through explicit ports, commands, events, policy decisions, typed results,
artifact refs, and replay records rather than shared mutable state or hidden
side effects.

Rationale: framework independence and clear ownership are required for replay,
testing, replacement, and long-term crawler evolution.

### III. Evidence, Verification, And Replay Before Publication

Raw observations MUST be preserved. Extracted candidates are not published
outputs. Published records, tables, documents, files, datasets, and facts MUST
point back to evidence, accepted verification decisions, immutable manifests,
and replayable lineage.

Graph intelligence, temporal KG projections, memory, agent reasoning, and prior
outputs MAY guide planning, prioritization, contradiction detection, and review.
They MUST NOT substitute for source evidence unless the referenced prior output
is accepted by policy and its transitive source evidence remains available.

Every mutating or publication-relevant action MUST be command/event backed.
Replay bundles MUST include command results, source adapter results, event
cursors, artifact hashes, agent/model/tool traces, projection watermarks,
redaction maps, and completeness results sufficient to reproduce or audit the
behavior.

Rationale: a crawler that cannot prove where outputs came from cannot be trusted
for production or regulated workflows.

### IV. Security, Policy, Credential, And Privacy Boundaries

VeraCrawl MUST support authorized and controlled acquisition only. It MUST NOT
implement CAPTCHA solving, paywall bypass, credential theft, login-wall
circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or
bypassing robots, terms, or customer authorization policy.

All source access MUST carry explicit scope, rate, budget, policy, and audit
refs. Untrusted web content MUST be treated as prompt-injection-prone input.
Raw secrets MUST NOT enter agents, model prompts, logs, replay bundles, captured
artifacts, untrusted page text, or framework-native state. Customer-authorized
credential presentation to an approved origin is allowed only through scoped
headers, scoped cookies, request signing, or vault-brokered form fill with
origin allowlist, policy approval, and `CredentialUseAudit`.

Artifact privacy classification, PII handling, retention, redaction, tombstone,
deletion, legal hold, export withdrawal, and projection cleanup MUST be evented,
auditable, and tested.

Rationale: maximizing crawl capability requires explicit safety boundaries, not
implicit trust in agents or websites.

### V. Executable Contracts And Test-First Acceptance

Specifications and plans MUST be implementable, not aspirational. Any feature
that changes crawling, source adapters, browser behavior, agents, contracts,
state machines, events, evidence, verification, publication, memory, graph,
export, migration, projection, recovery, or DR MUST define executable contracts
and acceptance tests before implementation.

Required artifacts MUST include command payload schemas, event payload schemas,
state transition specs, ownership boundaries, fixture/oracle definitions,
negative tests, replay checks, and security/privacy checks relevant to the
feature. Tasks MUST be traceable to these artifacts and MUST NOT be marked done
unless implementation and verification are actually complete.

Rationale: target architecture cannot be honestly delivered unless the docs can
drive generated tasks and tests with pass/fail criteria.

## Target Architecture Constraints

Every non-trivial Spec Kit artifact MUST reference the applicable target docs:

- `docs/09-target-capability-model.md`
- `docs/10-target-implementation-design.md`
- `docs/11-target-testing-and-acceptance.md`
- `docs/07-data-contracts.md`

For V1 production spine work, artifacts MUST also reference:

- `docs/01-product-definition.md`
- `docs/02-production-architecture.md`
- `docs/06-agent-system-design.md`
- `docs/08-build-roadmap.md`

Target architecture work MUST include the full intended capability unless a
specific spec is explicitly limited to dependency sequencing. Such sequencing
MUST preserve future compatibility with graph intelligence, memory intelligence,
browser execution, multi-agent orchestration, export/correction, scale,
operations, migration, projection rebuild, and DR restore.

All architecture plans MUST assign concrete owner services, canonical stores,
artifact stores, emitted events, projection outputs, replay behavior, privacy
lifecycle behavior, tests, and acceptance gates for affected contracts.

## Spec Kit Development Workflow

Non-trivial work MUST follow the Spec Kit workflow:

1. `$speckit-constitution` for changes to principles, safety boundaries,
   architecture rules, or governance.
2. `$speckit-specify` for user value, scenarios, requirements, entities,
   success criteria, scope, safety, evidence, and non-goals.
3. `$speckit-clarify` when requirements, acceptance criteria, safety boundaries,
   user roles, data contracts, source semantics, or output semantics are
   ambiguous.
4. `$speckit-plan` for Python architecture, package boundaries, ports/adapters,
   data contracts, state/event/replay design, migrations, tests, and rollout.
5. `$speckit-tasks` for executable tasks grouped by independently testable
   stories and foundational architecture work.
6. `$speckit-analyze` before implementation when available.
7. `$speckit-implement` or manual task execution with task IDs preserved.

Small mechanical fixes, typo corrections, formatting-only edits, or narrowly
scoped documentation wording changes MAY be done directly, but the final note
MUST state why the full workflow was not used.

## Governance

This constitution supersedes conflicting local practices, templates, generated
plans, and implementation shortcuts. If a Spec Kit artifact conflicts with this
constitution, the artifact MUST be corrected before implementation continues.

Amendments require:

- a documented reason for the change
- updates to affected templates and runtime guidance
- a version bump following semantic versioning
- a review of existing active specs and tasks for conflicts

Versioning policy:

- MAJOR: removes or redefines a core principle or weakens a hard boundary
- MINOR: adds a principle, section, required artifact, or material gate
- PATCH: clarifies wording without changing required behavior

Compliance review is mandatory at each Spec Kit phase. Constitution violations
are blocking issues and MUST NOT be waived silently. Any intentional exception
requires an explicit constitution amendment first.

**Version**: 1.0.0 | **Ratified**: 2026-05-02 | **Last Amended**: 2026-05-02
