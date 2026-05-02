# Feature Specification: VeraCrawl Target Core Runtime Spine

**Feature Branch**: `002-core-runtime-spine`  
**Created**: 2026-05-02  
**Status**: Draft  
**Input**: User description: "建立 VeraCrawl Target Core Runtime Spine：實作從 CrawlObjective / CrawlPlan / CrawlRun 到 source adapter execution、artifact refs、normalization、extraction candidate、evidence packet、verification decision、published output manifest、replay bundle 的端到端 runtime spine。必須基於既有 foundation contracts/ports/adapters/policy/replay/fixture oracle，不得繞過 command/event/replay，不得做成單站 scraper，不得讓 core 耦合任何 agent framework、browser library、storage client 或 queue client。必須維持 framework-neutral agent abstraction，可透過 adapters 接 OpenAI Agent SDK、LangGraph、LangChain、CrewAI、AutoGen、Semantic Kernel 或其他 framework。必須遵守 constitution、docs/07、docs/09、docs/10、docs/11，並補齊設計、測試、驗收文件。"

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This feature turns the completed foundation into the first executable objective-to-output runtime spine for many websites, source patterns, schemas, and output domains. It must not encode a single website, fixed selector set, one-off scraper path, or framework-native agent workflow.
- **Target/V1 boundary**: This is target architecture work for the core runtime spine described in `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md`. It is not a schedule-reduced V1 shortcut. It implements the durable spine required before broader browser, graph, memory, export, scale, and operations capability profiles can be claimed target-complete.
- **Evidence and replay impact**: The feature affects `CrawlObjective`, `CrawlPlan`, `CrawlRun`, `RunPlanSnapshot`, `SourceAdapterResult`, artifact refs, normalized documents, extraction candidates, evidence packets, verification decisions, published outputs, output manifests, command results, crawl run events, and replay bundle manifests.
- **Safety and policy impact**: All source access, adapter execution, prompt context, credential/session use, browser-capable routing, publication, retention, artifact lifecycle, and recovery decisions must pass policy gates and produce visible allow, deny, or require-review results.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, `specs/001-target-architecture-foundation/spec.md`, and `specs/001-target-architecture-foundation/contracts/`.

## Clarifications

### Session 2026-05-02

- Q: What is the first successful end-to-end fixture profile? -> A: A deterministic record-output fixture from a fetch-like local source with normalized anchors and field-level evidence is the required first success path; contracts must remain generic for table, document, file, dataset, and fact outputs, but those output profiles are not target-complete in this feature.
- Q: What persistence profile should this runtime spine implement first? -> A: Use deterministic in-memory canonical repositories and fixture-run artifact storage behind VeraCrawl ports; no concrete database, queue, browser, storage, or model provider client may enter core packages in this feature.
- Q: How should completion gates be represented? -> A: Runtime completion must be gate-specific: objective, plan, source, normalization, extraction, evidence, verification, publication, and replay gates are tracked independently; publication-complete requires every prerequisite gate to pass.
- Q: Is an external agent framework required for the successful runtime fixture? -> A: No. The successful runtime fixture must be deterministic without an external agent framework; separate conformance fixtures must prove framework-neutral recommendations can enter through adapters and owner-service commands.
- Q: Which negative fixtures are mandatory for this feature? -> A: Blocked source, missing evidence, verification conflict, adapter mismatch, replay gap, direct cross-owner mutation, and forbidden framework/core import fixtures are mandatory and must fail visibly without successful publication.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Objective To Published Output (Priority: P1)

An operator defines a governed crawl objective with source scope, schema needs, evidence requirements, and publication policy. VeraCrawl turns it into an approved plan, starts a run, executes source adapter work, records artifact refs, normalizes source content, creates extraction candidates, builds evidence, verifies the candidate, publishes an output manifest, and emits a replay bundle for the full path.

**Why this priority**: This is the core product path. Without this end-to-end spine, VeraCrawl remains contracts and stubs rather than a working AI agent crawler substrate.

**Independent Test**: A deterministic record-output fixture run can start from an approved objective and finish with a published output manifest whose required fields all point to evidence refs and whose replay bundle reconstructs every mutating and publication-relevant action.

**Acceptance Scenarios**:

1. **Given** a crawl objective with approved scope, schema, policy, and evidence requirements, **When** the run is started, **Then** VeraCrawl creates a plan snapshot, command results, run events, adapter commands, artifact refs, normalized artifacts, extraction candidates, evidence packets, verification decisions, published output, output manifest, and replay bundle refs.
2. **Given** a published output produced by the run, **When** a reviewer inspects the output manifest, **Then** each required output field or item has source-backed evidence refs and accepted verification lineage.
3. **Given** the run has completed, **When** replay is requested, **Then** replay reconstructs the objective, plan, policy decisions, source adapter results, artifacts, normalized refs, candidate refs, evidence packets, verification decisions, publication decisions, and output manifest without relying on hidden framework state.

---

### User Story 2 - Execute Source And Processing Through Owner Boundaries (Priority: P2)

A runtime worker executes source adapter and processing work through VeraCrawl-owned commands and owner services. Fetch-like and non-fetch source adapter outcomes use their natural output refs, and every state transition is idempotent, policy-checked, and evented.

**Why this priority**: The runtime spine must prove low coupling, high cohesion, and owner-service mutation boundaries before adding richer browser, memory, graph, export, and distributed worker capabilities.

**Independent Test**: Contract and integration tests can run source adapter execution, normalization, extraction, evidence, verification, and publication tasks while proving no core package imports concrete adapter frameworks, browser libraries, storage clients, queue clients, or agent frameworks.

**Acceptance Scenarios**:

1. **Given** a fetch-like source adapter command, **When** source policy allows execution, **Then** the natural owner records `SourceAdapterResult`, source artifact refs, and replay-critical events without bypassing the command/result path.
2. **Given** a non-fetch source adapter command, **When** it succeeds, **Then** the result references adapter-native output refs and does not fake `FetchResult` or `PageSnapshot` semantics.
3. **Given** a processing task for normalization, extraction, evidence, verification, or publication, **When** the wrong owner attempts mutation, **Then** the command is rejected and the rejection is evented.

---

### User Story 3 - Block Unsafe Or Incomplete Publication (Priority: P3)

Policy, evidence, verification, and replay gates prevent VeraCrawl from publishing outputs when source access is unauthorized, evidence is missing, verification is rejected, conflicts are unresolved, artifacts are unavailable, replay refs are incomplete, or privacy lifecycle rules block use.

**Why this priority**: A powerful AI crawler is only production-worthy if unsafe or incomplete results fail visibly instead of silently producing unverified outputs.

**Independent Test**: Negative fixtures intentionally trigger blocked source access, missing evidence, contradictory evidence, missing replay refs, redacted artifacts, and adapter mismatch. Each case must produce a denied, needs-review, failed, or conflict result, never a successful publication.

**Acceptance Scenarios**:

1. **Given** source access is denied by scope, robots/terms, customer authorization, credential policy, or budget, **When** the runtime attempts execution, **Then** it records a blocked source result, policy decision, command result, and operator-visible report without bypass.
2. **Given** extraction produced a candidate without required source anchors, **When** evidence is built or verification runs, **Then** the runtime fails or routes to review and prevents publication.
3. **Given** a replay bundle is missing a command result, source adapter result, event cursor, artifact hash, trace ref, or redaction map, **When** completion is evaluated, **Then** the run cannot be marked replay-complete or publication-complete.

---

### User Story 4 - Use Framework-Neutral Agents Without Core Coupling (Priority: P4)

Planner, extraction, verification, and repair recommendations may come from VeraCrawl's framework-neutral agent runtime. External frameworks remain replaceable adapters and cannot become canonical state or direct mutation paths.

**Why this priority**: VeraCrawl must maximize AI power without becoming dependent on any single agent framework or allowing agents to mutate durable stores directly.

**Independent Test**: Agent conformance fixtures can provide plan, extraction, verification, or repair recommendations through OpenAI Agent SDK and LangGraph-style adapters while the core runtime records only VeraCrawl contracts, traces, command results, policy decisions, and events.

**Acceptance Scenarios**:

1. **Given** an agent proposes a crawl plan, extraction candidate, verification recommendation, or repair action, **When** the runtime accepts the proposal, **Then** the durable mutation still flows through owner service commands and policy gates.
2. **Given** the agent framework adapter is swapped, **When** the same fixture is replayed, **Then** canonical runtime state, trace refs, and replay outputs remain framework-neutral.

### Edge Cases

- Source access is blocked by scope, robots/terms, customer authorization, credential scope, budget, retention, or safety gates.
- A run is cancelled, paused, resumed, retried, or failed while adapter work or processing tasks are in flight.
- A source adapter returns partial output, malformed output, adapter mismatch, stale prior snapshot, unsupported document format, or missing artifact ref.
- Evidence is missing, stale, contradictory, redacted, deleted, legally held, or tied to an expired prior output.
- Verification returns reject, needs-review, conflict, or accept with insufficient authority.
- Publication is requested without accepted verification, coverage aggregate, policy allow decision, immutable output manifest, or replay-complete lineage.
- Replay-critical command, event, artifact, source adapter result, model trace, tool trace, or redaction refs are unavailable.
- Agent-proposed actions conflict with policy, owner boundaries, source evidence, or another agent recommendation.
- Runtime restarts after a command is accepted but before downstream events are materialized.
- A fixture or oracle drifts from the runtime output and must fail loudly instead of being tolerated silently.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement an executable objective-to-output runtime spine from `CrawlObjective` and `CrawlPlan` through `CrawlRun`, source adapter execution, artifacts, normalization, extraction candidate, evidence packet, verification decision, published output, output manifest, and replay bundle.
- **FR-002**: System MUST require every mutating or publication-relevant runtime action to flow through `CommandEnvelope`, owner service validation, `CommandResult`, typed event emission, and replay refs.
- **FR-003**: System MUST create and persist a run plan snapshot through VeraCrawl-owned repository ports that freezes approved objective, plan, source scope, schema refs, evidence requirements, policy refs, adapter choices, prompt/tool/model refs when used, and replay-critical configuration.
- **FR-004**: System MUST execute source adapter commands through the existing source adapter ports and record canonical `SourceAdapterResult` records for fetch-like, browser-capable, API-like, document, file, manual seed, authorized session, and prior snapshot outcomes as applicable to the fixture.
- **FR-005**: System MUST preserve natural adapter semantics: fetch-like adapters may produce fetch/page artifacts, while non-fetch adapters must emit adapter-native refs and must not fake fetch/page snapshot records.
- **FR-006**: System MUST record raw artifact refs before normalization and preserve enough hash, lifecycle, privacy, and source metadata for replay and evidence validation.
- **FR-007**: System MUST normalize source artifacts into replayable normalized document refs with source anchors or equivalent evidence anchor mappings.
- **FR-008**: System MUST create extraction candidates only from declared schema requirements, approved exploratory fields, or policy-approved agent proposals, and each candidate must carry source, artifact, schema, and confidence refs.
- **FR-009**: System MUST build evidence packets with required source evidence refs and coverage results before verification or publication can accept the candidate.
- **FR-010**: System MUST create verification decisions that explicitly accept, reject, route to review, or mark conflict based on evidence, policy, schema constraints, freshness, and contradiction checks.
- **FR-011**: System MUST publish outputs only when verification, evidence coverage, publication policy, privacy lifecycle, and replay completeness gates pass.
- **FR-012**: System MUST create immutable output manifests that include output version, schema refs, evidence coverage refs, verification refs, publication decision refs, artifact refs, replay refs, and privacy/export lifecycle refs.
- **FR-013**: System MUST produce replay bundle manifests that can reconstruct the runtime spine without relying on framework-native state, in-memory-only state, unrecorded tool calls, or hidden side effects.
- **FR-014**: System MUST expose denied, failed, partial, needs-review, conflict, and blocked outcomes as typed command results, policy decisions, events, and operator-visible reports.
- **FR-015**: System MUST prevent direct cross-owner mutation for objective, plan, run, adapter result, normalized artifact, extraction candidate, evidence packet, verification decision, published output, output manifest, and replay bundle state.
- **FR-016**: System MUST preserve framework-neutral agent integration: agents can propose or recommend, but durable mutations must route through VeraCrawl command, policy, owner service, and event paths.
- **FR-017**: System MUST reject any runtime core dependency on concrete agent frameworks, browser libraries, storage clients, queue clients, model SDKs, or website-specific scraper modules.
- **FR-018**: System MUST extend deterministic fixture/oracle coverage to include at least one successful record-output objective-to-output run and negative runs for blocked source, missing evidence, verification conflict, adapter mismatch, replay gap, direct cross-owner mutation, and forbidden framework/core imports.
- **FR-019**: System MUST make completion status precise: a run can be objective-complete, plan-complete, source-complete, normalization-complete, extraction-complete, evidence-complete, verification-complete, publication-complete, and replay-complete independently, and no status may be claimed without its gate passing.
- **FR-020**: System MUST update design, contract, quickstart, test, and task artifacts so every runtime behavior maps to an owner service, command, event, contract, policy gate, replay requirement, fixture/oracle, and acceptance check.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior when outputs are affected.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, and export/withdrawal behavior when those boundaries are affected.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **CrawlObjective**: Governed user intent, source scope, schemas, evidence requirements, freshness requirements, and policy refs.
- **CrawlPlan**: Approved crawl strategy, adapter choices, assumptions, alternatives, budget, frontier seeds, and evidence plan.
- **CrawlRun**: Runtime execution record with lifecycle status, plan snapshot, budget, task refs, policy refs, event cursors, and completion gates.
- **RunPlanSnapshot**: Immutable snapshot of the objective, plan, policy, schema, adapter, tool, model, evidence, and replay-critical refs used by a run.
- **RuntimeCompletionGate**: Independent gate result for objective, plan, source, normalization, extraction, evidence, verification, publication, and replay readiness.
- **SourceAdapterResult**: Canonical outcome from a source adapter command, including natural adapter result type, status, output refs, policy refs, diagnostics, and replay refs.
- **RuntimeArtifactRef**: Stable ref for raw, normalized, extracted, evidence, output, replay, or redacted artifacts with hash, privacy, lifecycle, and source metadata.
- **NormalizedDocument**: Replayable normalized representation of source content with anchor maps and transformation refs.
- **ExtractionCandidate**: Schema-bound candidate output with source refs, normalized anchors, confidence, extraction strategy, and review state.
- **EvidencePacket**: Source-backed evidence bundle proving candidate fields/items against required coverage.
- **VerificationDecision**: Durable accept, reject, review, or conflict decision tied to evidence, policy, authority, and freshness.
- **PublishedOutput**: Immutable accepted result version that cannot exist without verification and evidence lineage.
- **OutputManifest**: Manifest linking published output, schema, evidence coverage, verification decisions, artifact refs, privacy/export lifecycle, and replay refs.
- **ReplayBundleManifest**: Manifest proving command, event, adapter result, artifact, trace, policy, redaction, and output lineage for reconstruction and audit.
- **PolicyDecision**: Allow, deny, or require-review decision for source, adapter, credential, prompt, tool, publication, artifact lifecycle, retention, and recovery subjects.
- **CommandResult**: Durable command outcome with emitted event refs, rejection reasons, idempotency behavior, and owner-service validation result.

### Non-Goals *(mandatory)*

- This feature does not claim full target architecture completion, full browser execution profile, full graph intelligence, full memory intelligence, full export connector suite, distributed queue scale, autoscaling, disaster recovery, or all target adapter profiles as target-complete.
- This feature does not implement website-specific scraper modules, fixed selectors, one-off extraction pipelines, or framework-native canonical state.
- This feature does not allow agents, adapters, browser workers, or external frameworks to directly mutate durable stores.
- This feature does not publish extraction candidates without evidence packets, verification decisions, publication policy allow decisions, output manifests, and replay-complete lineage.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A deterministic successful record-output fixture produces one objective-to-output run with 100% of required output fields or items linked to source-backed evidence refs.
- **SC-002**: 100% of mutating and publication-relevant actions in the successful fixture have command result refs, event refs, owner service refs, policy decision refs when applicable, and replay refs.
- **SC-003**: Replay validation for the successful fixture reconstructs objective, plan, run, adapter result, artifacts, normalized refs, candidate, evidence, verification, publication, and output manifest with zero missing required refs.
- **SC-004**: Blocked-source, missing-evidence, verification-conflict, adapter-mismatch, replay-gap, direct cross-owner mutation, and forbidden framework/core import fixtures never produce a successful publication and always emit typed failure, review, conflict, blocked, boundary-violation, or replay-incomplete outcomes.
- **SC-005**: Import-boundary checks prove runtime core packages have zero direct imports of concrete agent frameworks, browser libraries, storage clients, queue clients, model SDKs, or website-specific scraper modules.
- **SC-006**: At least one framework-neutral agent conformance fixture can contribute a plan, extraction, verification, or repair recommendation while durable runtime state remains unchanged when the framework adapter is swapped.
- **SC-007**: Contract registry validation covers every new runtime contract, command type, event type, owner service, policy gate, replay requirement, and fixture/oracle introduced by this feature.
- **SC-008**: Local contract, unit, integration, fixture/oracle, replay, policy, and import-boundary gates complete within the foundation performance envelope or record a justified timing report.
- **SC-009**: Documentation and CLI output describe this as the target core runtime spine only and do not claim full target crawler completion, full browser capability, full graph/memory capability, full export capability, or production scale readiness.

## Assumptions

- The existing target architecture foundation from `specs/001-target-architecture-foundation/` is the required base and remains valid.
- The first executable successful runtime fixture uses local deterministic source content, a fetch-like source adapter, a record output schema, normalized anchors, and field-level evidence.
- Runtime contracts and owner boundaries must support target adapter and output families without single-site assumptions, even though table, document, file, dataset, fact, full browser, graph, memory, export, and scale profiles are not marked target-complete by this feature.
- The spine uses in-memory canonical repositories and fixture-run artifact storage through ports during this feature. Concrete storage, queue, browser, model provider, and export infrastructure remain behind replaceable ports and are not core dependencies.
- AI agent participation is allowed for recommendations and reasoning traces, but the runtime must still pass without requiring a specific external agent framework.
- Export delivery is out of scope for this feature, but publication manifests must preserve export and withdrawal lifecycle refs so later export work can attach without redesign.
- Graph and memory intelligence may provide optional planning context in later features, but neither can satisfy evidence coverage or publication proof in this spine.
