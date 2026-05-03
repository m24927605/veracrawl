# Feature Specification: VeraCrawl Target Crawl Runtime

**Feature Branch**: `034-target-crawl-runtime`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "Build VeraCrawl Target Architecture End-to-End Crawl Runtime: executable crawl objective ingestion, policy-gated scheduling/frontier, HTTP/source acquisition, framework-neutral AI planning and repair adapters, evidence capture, normalization/extraction, graph projection, export materialization, replay/audit closure, and fixture/oracle acceptance across multiple website patterns without narrowing into a single-site scraper."

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This feature turns the completed target architecture contracts and gates into an executable product path for many website patterns, objective types, source patterns, schemas, and data domains. It must not contain site-specific scraper assumptions or a hardcoded extraction flow.
- **Target/V1 boundary**: This is target architecture runtime work governed by `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md`. It is not a schedule-reduced V1 demo; dependency sequencing is allowed only to preserve correctness and verification.
- **Evidence and replay impact**: Crawl objective ingestion, plan generation, frontier changes, source acquisition, AI recommendations, repairs, evidence packets, extraction outputs, graph projections, exports, command results, event cursors, outbox records, artifact refs, and replay bundle manifests are all publication-relevant and must be replayable.
- **Safety and policy impact**: Source access must carry scope, rate, budget, robots/terms, credential, browser, prompt-injection, privacy, retention, and export decisions. Unsafe or unauthorized actions must be blocked with operator-visible diagnostics and replayable policy evidence.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Execute A Complete Multi-Pattern Crawl (Priority: P1)

As an operator, I need to submit a crawl objective and receive verified outputs, evidence, graph, export manifest, and replay bundle for multiple allowed website patterns.

**Why this priority**: The product must prove it is a working general-purpose crawler runtime, not only a set of contracts, gates, or isolated adapters.

**Independent Test**: Run the target crawl runtime against a deterministic multi-pattern fixture bundle containing sitemap, listing/detail, paginated, document metadata, API-like JSON, redirect/canonical, and dynamic-change patterns. The run passes only when all expected outputs, evidence refs, graph refs, export refs, command/event/outbox refs, and replay refs are present.

**Acceptance Scenarios**:

1. **Given** an allowed objective with policy, scope, fixture sites, output expectations, and replay requirements, **When** the crawl runtime executes, **Then** it creates an approved crawl plan, schedules frontier items, acquires sources, extracts records/documents/tables/factual fields, verifies evidence, projects a site graph, materializes export outputs, and writes a replay bundle.
2. **Given** multiple website patterns and output schemas in one objective, **When** the crawl completes, **Then** each pattern has accepted outputs linked to source evidence and no pattern is treated as a hardcoded single-site special case.
3. **Given** the same objective and fixture bundle are replayed, **When** replay validation runs, **Then** replay output, event sequence, graph summary, artifact hashes, and completeness decisions match the oracle.

---

### User Story 2 - Use Framework-Neutral AI Planning And Repair (Priority: P2)

As a crawler engineer, I need the runtime to use AI recommendations for planning, extraction assistance, verification, and repair while keeping VeraCrawl core independent of any agent framework.

**Why this priority**: VeraCrawl's wedge is powerful AI-assisted crawling, but framework coupling would violate the constitution and make replay or replacement fragile.

**Independent Test**: Execute a fixture where the first pass has missing evidence, changed page structure, and conflicting facts. The runtime must request framework-neutral AI planning/repair recommendations, accept or reject them through VeraCrawl-owned contracts, and finish with corrected outputs or typed review diagnostics without importing any concrete agent framework in core.

**Acceptance Scenarios**:

1. **Given** a page structure drift causes an extraction miss, **When** repair is triggered, **Then** the runtime records an AI recommendation, applies only policy-approved tool calls, emits repair events, and re-runs the affected frontier items.
2. **Given** an AI recommendation proposes an unsafe action or unsupported source access, **When** policy evaluates it, **Then** the runtime blocks the action and records a replayable policy denial.
3. **Given** a concrete agent adapter is absent, **When** the runtime uses the built-in deterministic adapter, **Then** the same framework-neutral contracts and replay traces are emitted.

---

### User Story 3 - Provide Operator-Visible Audit And Export Closure (Priority: P3)

As an operator or reviewer, I need a concise run report showing what succeeded, what was blocked, what needs review, what was exported, and how every output can be audited or replayed.

**Why this priority**: A crawler that produces data without operator-visible evidence, failure, export, and replay closure cannot be trusted in production workflows.

**Independent Test**: Run success, needs-review, and policy-denied fixtures. Each run must produce an operator-visible report with objective, plan, scope, metrics, diagnostics, output manifest, export receipts, replay refs, privacy refs, and recovery hints.

**Acceptance Scenarios**:

1. **Given** a successful crawl, **When** the run report is inspected, **Then** it lists accepted outputs, evidence coverage, graph projection status, export receipt, replay bundle, policy decisions, and privacy lifecycle refs.
2. **Given** a crawl is incomplete because evidence is missing or contradictory, **When** the runtime finishes, **Then** the run status is `needs_review`, not `complete`, and the report lists review items and recovery actions.
3. **Given** an export is withdrawn or corrected, **When** the report is generated, **Then** export withdrawal or correction refs are visible and tied to affected output manifests.

---

### User Story 4 - Block Unsafe Or Deceptive Completion Claims (Priority: P4)

As a Staff reviewer, I need the runtime to reject unauthorized access, unsafe automation, missing replay, mock-only success, degraded capability labeled operational, and any false `complete` claim.

**Why this priority**: The constitution forbids unsafe crawl behavior and deceptive completion claims; runtime success must be earned by evidence and replay.

**Independent Test**: Negative fixtures for blocked scope, credential misuse, prompt-injection attempt, browser-required-without-approval, robots/terms denial, missing replay, mock-only artifacts, and false-complete status must fail deterministically with typed diagnostics.

**Acceptance Scenarios**:

1. **Given** a target URL, credential, browser action, or export target is outside approved policy, **When** the runtime evaluates the crawl, **Then** it blocks the action before acquisition or publication and emits a policy denial.
2. **Given** source content attempts to inject agent instructions, **When** AI planning or extraction assistance runs, **Then** untrusted content is isolated from trusted instructions and the tainted input boundary is recorded.
3. **Given** a run lacks required evidence, replay, command/event/outbox, or artifact refs, **When** completion is evaluated, **Then** it cannot be marked `complete`, `verified`, or `operational`.

### Edge Cases

- Source scope allows one domain but linked pages leave the allowed boundary.
- A sitemap references duplicate, redirected, canonical, or stale pages.
- Pagination loops, repeats cursors, or produces inconsistent page counts.
- A document metadata page links to missing, redacted, or unsupported files.
- API-like JSON responses include partial records, schema drift, or contradictory timestamps.
- Source evidence exists but has insufficient coverage for one output field.
- The AI planner proposes a browser step, credential use, or external fetch that lacks approval.
- Prompt-injection content attempts to override crawl policy or export behavior.
- A frontier item fails transiently and later succeeds; replay must preserve both attempts.
- Export succeeds for one output type and fails for another.
- Retention, deletion, tombstone, or legal hold affects evidence needed by replay.
- The run reaches budget, rate, or safety limits before completeness.
- Fixture/oracle expectations disagree with observed artifacts.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a crawl objective containing scope, policies, output expectations, website pattern hints, source fixtures or sources, and replay requirements.
- **FR-002**: System MUST produce a crawl plan with approved source scope, frontier seed items, acquisition strategy, evidence expectations, output targets, graph requirements, export intent, and replay criteria.
- **FR-003**: System MUST schedule and process frontier items through policy-gated acquisition, normalization, extraction, verification, graph projection, export materialization, and replay recording.
- **FR-004**: System MUST support multiple website patterns in one run, including sitemap, listing/detail, pagination, document metadata, API-like JSON, redirect/canonical, and dynamic-change patterns.
- **FR-005**: System MUST preserve raw source observations and link every accepted output field to evidence refs, verification decisions, artifact refs, and replay lineage.
- **FR-006**: System MUST emit command results, domain events, event cursors, outbox records, policy decisions, tool traces, artifact refs, output manifests, export receipts, operator reports, and replay bundle manifests for each run.
- **FR-007**: System MUST use framework-neutral AI recommendation contracts for planning, extraction assistance, verification support, drift repair, and recovery decisions.
- **FR-008**: System MUST keep VeraCrawl core independent of concrete agent frameworks, model SDKs, storage clients, queue clients, browser runtimes, HTTP clients, export targets, UI frameworks, and site-specific scraper modules.
- **FR-009**: System MUST provide a deterministic built-in AI adapter for offline acceptance fixtures and allow concrete agent adapters to be substituted without changing core contracts.
- **FR-010**: System MUST evaluate policy before acquisition, browser actions, credential presentation, AI tool calls, publication, export, retention, deletion, and replay exposure.
- **FR-011**: System MUST block unauthorized, out-of-scope, unsafe, prompt-injection-tainted, browser-unapproved, credential-unapproved, robots/terms-denied, or export-denied actions with typed diagnostics.
- **FR-012**: System MUST return `complete` only when required outputs, evidence, verification, policy, graph, export, command/event/outbox, artifact, privacy, and replay refs satisfy the objective oracle.
- **FR-013**: System MUST return `needs_review` when the crawl has recoverable evidence gaps, contradictions, partial exports, or operator decisions required before publication.
- **FR-014**: System MUST return `blocked` or `failed` when policy, safety, missing infrastructure, missing source, non-recoverable oracle mismatch, or runtime errors prevent trustworthy completion.
- **FR-015**: System MUST reject planned, scaffolded, degraded, mock-only, fixture-only, or contract-only claims that attempt to mark a run, capability, or output as `complete`, `verified`, or `operational`.
- **FR-016**: System MUST provide success, needs-review, policy-denied, replay-mismatch, prompt-injection, drift-repair, missing-evidence, partial-export, and false-complete fixtures.
- **FR-017**: System MUST provide a runtime CLI or equivalent executable entry point that runs fixtures, validates expected status and oracle refs, and writes a machine-readable run report.
- **FR-018**: System MUST register target crawl runtime contracts, commands, events, fixtures, and target area coverage in the contract registry.
- **FR-019**: System MUST document the runtime execution path and explicitly state that the feature is an executable target architecture path, not a single-site scraper or mock-only readiness claim.
- **FR-020**: System MUST complete the local deterministic fixture loop within 60 seconds on a developer machine.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior when outputs are affected.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, and export/withdrawal behavior when those boundaries are affected.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **TargetCrawlObjective**: Operator request defining source scope, policies, output expectations, website pattern hints, budget, and replay criteria.
- **TargetCrawlPlan**: Approved plan containing acquisition strategy, frontier seeds, evidence expectations, AI planning constraints, graph requirements, export intent, and completion criteria.
- **TargetCrawlRun**: Aggregate run record tracking status, objective, plan, processed frontier, outputs, evidence, policies, events, exports, reports, diagnostics, and replay refs.
- **TargetFrontierItem**: Unit of scheduled work with URL/source identity, website pattern, acquisition mode, policy refs, lease/retry state, evidence expectations, and replay refs.
- **TargetSourceObservation**: Raw source observation, document, network, browser, or API-like response linked to artifacts, policy decisions, taint boundaries, and acquisition attempts.
- **TargetExtractionResult**: Candidate and accepted records, tables, document metadata, and factual fields with evidence coverage and verification decisions.
- **TargetAIRecommendation**: Framework-neutral planning, extraction, verification, repair, or recovery recommendation with tool-call proposals, policy decisions, and trace refs.
- **TargetRuntimeReport**: Operator-visible outcome report with status, metrics, outputs, diagnostics, graph/export/replay/privacy refs, review items, and recovery actions.
- **TargetReplayBundle**: Replay manifest linking objective, plan, commands, events, artifacts, source observations, agent traces, policy decisions, output manifests, export receipts, and oracle results.

### Non-Goals *(mandatory)*

- This feature does not implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.
- This feature does not make one live website, one scraper module, one browser automation demo, one static fixture, or one output schema a proxy for general-purpose product capability.
- This feature does not require a specific external agent framework or model provider for core runtime execution.
- This feature does not treat deterministic offline fixtures as production Internet coverage; they are executable acceptance gates for the target runtime path.
- This feature does not bypass existing target gates for infrastructure, storage, queues, object store, security/privacy, source coverage, model provider, or agent adapters.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Success fixture run completes with status `complete` and includes accepted outputs for at least seven website patterns: sitemap, listing/detail, pagination, document metadata, API-like JSON, redirect/canonical, and dynamic-change.
- **SC-002**: Every accepted output field in the success fixture has evidence refs, verification refs, artifact refs, policy refs, event refs, outbox refs, and replay refs.
- **SC-003**: Drift-repair fixture records at least one framework-neutral AI recommendation, one policy-approved repair action, one reprocessed frontier item, and accepted corrected outputs.
- **SC-004**: Needs-review fixture returns `needs_review` and includes review items, evidence gaps or contradictions, recovery hints, and no false `complete` claim.
- **SC-005**: Negative fixtures for policy-denied access, prompt injection, missing evidence, replay mismatch, partial export, and false completion fail deterministically with typed diagnostics.
- **SC-006**: Import-boundary tests prove core runtime modules do not import concrete agent frameworks, model SDKs, storage clients, queue clients, browser runtimes, HTTP clients, export targets, UI frameworks, or site-specific scraper modules.
- **SC-007**: Registry validation includes every target crawl runtime contract, command, event, fixture, and target area coverage.
- **SC-008**: Full local fixture loop completes within 60 seconds.

## Assumptions

- Deterministic acceptance fixtures use local source observations and oracles so they can run without live Internet instability while still exercising the full runtime path.
- Existing contracts and gates from specs 001-033 are available and must be reused rather than bypassed.
- Concrete production adapters may be present or absent; the runtime must remain usable with in-memory/deterministic adapters for acceptance and replaceable concrete adapters for production.
- Browser execution and credential presentation require explicit policy approval even in fixtures.
- Output publication requires evidence and verification; raw extraction candidates are not published outputs.
