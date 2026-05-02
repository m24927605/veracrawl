# Feature Specification: VeraCrawl Target Architecture Foundation

**Feature Branch**: `001-target-architecture-foundation`  
**Created**: 2026-05-02  
**Status**: Draft  
**Input**: User description: "$speckit-specify 建立 VeraCrawl Target Architecture Foundation：Python 專案骨架、domain contracts、ports/adapters、command/event/replay 基礎、policy gates、fixture/oracle 測試基礎，以及 framework-neutral agent abstraction layer，必須能透過 adapters 對接 OpenAI Agent SDK、LangChain、LangGraph、CrewAI、AutoGen、Semantic Kernel 或其他 agent framework，但 VeraCrawl core 不得直接耦合任何 agent framework。必須遵守 docs/07、09、10、11 與 constitution，不得實作成單站 scraper。"

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This foundation establishes the shared platform surface for VeraCrawl as a general-purpose AI agent web crawler. It must support many websites, source patterns, schemas, data domains, and agent runtimes instead of baking in a single-site scraper path.
- **Target/V1 boundary**: This is target architecture foundation work. It defines the substrate that later V1 and target capabilities depend on, while preserving future compatibility with the full target profiles in `docs/09-target-capability-model.md`.
- **Evidence and replay impact**: The feature covers domain contracts, command envelopes/results, crawl run events, source adapter results, replay manifests, trace refs, fixture/oracle expectations, and policy-gated state transitions.
- **Safety and policy impact**: The feature covers source scope, policy decisions, credential/session audit boundaries, prompt-injection boundaries, privacy lifecycle hooks, and negative tests for blocked behavior.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, and `.specify/memory/constitution.md`.

## Clarifications

### Session 2026-05-02

- Q: What should the first foundation phase deliver? → A: An executable Python skeleton with domain contracts, ports/adapters interfaces, command/event/replay foundations, policy gates, fixture/oracle test foundations, and contract tests; it must not implement the full crawler runtime.
- Q: Which agent framework adapter conformance targets define the first acceptance baseline? → A: A generic framework adapter contract plus conformance fixtures for OpenAI Agent SDK and LangGraph; LangChain, CrewAI, AutoGen, Semantic Kernel, and future frameworks must use the same adapter contract later.
- Q: How broad should source adapter foundation coverage be? → A: Contract/interface coverage for all target adapter families, with executable fixture/stub coverage for at least one fetch-like adapter result and one non-fetch adapter result.
- Q: Which docs/07 contracts must be materialized first? → A: The foundation subset is CommandEnvelope, CommandResult, CrawlRunEvent, SourceAdapterResult, PolicyDecision, AgentRuntime/Tool/Context/Model trace contracts, ReplayBundleManifest, and fixture/oracle contracts; broader target contracts remain referenced and must not be contradicted.
- Q: What is the minimum foundation acceptance gate before implementation can claim success? → A: Contract registry consistency, no direct agent-framework core dependency, no direct cross-owner mutation, replay-missing-ref failure, and policy-blocked fixture behavior must all pass.
- Q: How should broad `docs/07` target contract areas be covered without falsely implementing the full runtime? → A: The foundation must materialize the clarified foundation subset and also maintain a target contract area coverage matrix for broader `docs/07` areas, including owner service, coverage status, canonical store/artifact impact where known, follow-up spec gate, replay/privacy impact, and tests required before any later target-complete claim.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Establish Foundation Contracts (Priority: P1)

A VeraCrawl platform implementer can start a new target architecture implementation from a coherent foundation that defines the product skeleton, canonical contracts, ownership boundaries, command/event/replay model, and acceptance gates.

**Why this priority**: Without the foundation contracts, later crawler, agent, source adapter, evidence, memory, graph, export, and recovery work would invent incompatible state and event models.

**Independent Test**: Run the foundation contract checks to confirm every affected foundation contract has an owner service, command payload schema, event payload schema, state transition spec, replay requirement, and negative test before implementation begins.

**Acceptance Scenarios**:

1. **Given** the foundation is specified, **When** a later feature references a domain contract, **Then** the contract has a canonical owner, command/event path, payload schema, replay behavior, and acceptance test requirement.
2. **Given** a proposed implementation introduces shared mutable state or direct cross-owner mutation, **When** the foundation gates are applied, **Then** the proposal is rejected until it uses ports, commands, events, and typed results.

---

### User Story 2 - Add Source And Agent Runtime Adapters (Priority: P2)

A VeraCrawl integrator can add source adapters and agent framework adapters without coupling VeraCrawl core to any specific website, browser workflow, model provider, or agent framework.

**Why this priority**: VeraCrawl must use AI deeply while remaining framework-neutral. Adapter boundaries are required so OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, or other frameworks can be integrated without becoming canonical state.

**Independent Test**: Define adapter conformance fixtures that prove each adapter emits VeraCrawl-owned contracts and traces, while core contracts remain unchanged when swapping framework adapters.

**Acceptance Scenarios**:

1. **Given** an OpenAI Agent SDK adapter and a LangGraph adapter, **When** either is used for the same agent role, **Then** VeraCrawl persists the same canonical request/result, tool trace, model trace, command result, and replay refs.
2. **Given** a source adapter handles a non-HTTP source, **When** it completes, **Then** it records `SourceAdapterResult` and adapter-native output refs without faking `FetchResult` or `PageSnapshot` semantics.

---

### User Story 3 - Verify Safety, Replay, And Fixtures (Priority: P3)

A reviewer or operator can verify that foundation behavior is testable through fixtures, oracles, replay bundles, blocked-action reports, and security/privacy checks before any production crawler path claims completion.

**Why this priority**: Target capability cannot be trusted if unsafe behavior, missing evidence, replay gaps, or fixture/oracle drift are discovered only after implementation.

**Independent Test**: Run foundation-level contract and fixture checks that intentionally include missing evidence, blocked credentials, policy-denied sources, replay gaps, and adapter mismatch cases.

**Acceptance Scenarios**:

1. **Given** a fixture contains a policy-denied source or unsafe credential path, **When** the fixture runs, **Then** VeraCrawl records the block and audit trail instead of bypassing the policy.
2. **Given** a replay bundle lacks a required command result, source adapter result, event cursor, artifact hash, or trace ref, **When** replay validation runs, **Then** the foundation reports failure or needs-review instead of claiming completion.

### Edge Cases

- A source is blocked by robots, terms, customer authorization, scope, rate, budget, credential, browser safety, or privacy policy.
- A website returns partial, malformed, dynamic, authenticated, document, API-like, prior snapshot, or manual seed inputs.
- A framework adapter returns framework-native state that cannot be mapped to VeraCrawl contracts.
- Evidence is missing, stale, contradictory, redacted, deleted, legally held, or unsupported by accepted verification.
- Replay-critical command, event, artifact, source adapter result, model/tool trace, projection watermark, or redaction ref is unavailable.
- A later implementation attempts direct storage/client/framework dependency from core packages.
- A test fixture defines tolerance or expected output behavior without an explicit oracle schema.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define the target architecture foundation as a general-purpose AI agent crawler substrate, not a single-site crawler, scraper script, or vertical extraction pipeline.
- **FR-002**: System MUST define an executable Python skeleton for core services, workers, contracts, policy checks, event handling, and agent runtime abstractions.
- **FR-003**: System MUST define domain contract coverage for the target architecture areas referenced by `docs/07-data-contracts.md`, including source adapters, commands, events, replay, evidence, verification, publication, projection, memory, export, ops, and artifact lifecycle. For this foundation, coverage means materialized models for the clarified subset plus a target contract area coverage matrix for broader target areas that are intentionally deferred to later implementation specs.
- **FR-004**: System MUST define ports and adapters so storage clients, queue clients, browser libraries, model providers, and agent frameworks are replaceable behind VeraCrawl-owned interfaces.
- **FR-005**: System MUST define a framework-neutral agent abstraction layer that supports adapters for OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, and other agent frameworks without direct core coupling.
- **FR-006**: System MUST define command envelopes, command results, command payload schemas, event payload schemas, state transition specs, and replay refs for foundation-level behavior.
- **FR-007**: System MUST define policy gates for source scope, robots/terms/customer authorization, credential/session use, browser interactions, prompt context, publication, export, memory, graph signal use, recovery, retention, and artifact lifecycle where applicable.
- **FR-008**: System MUST define fixture/oracle foundations for outputs, evidence anchors, event ordering, replay bundles, graph expectations, failure injections, and DR restore expectations.
- **FR-009**: System MUST define negative acceptance requirements for unsafe actions, missing evidence, direct framework coupling, direct cross-owner mutation, incomplete replay, and untyped adapter outputs.
- **FR-010**: System MUST require every later implementation task to trace to a Spec Kit task ID, affected contract, owner service, and verification check.
- **FR-011**: System MUST include foundation contract tests and registry consistency checks before any crawler runtime path can claim implementation success.
- **FR-012**: System MUST define a generic agent framework adapter contract and initial conformance fixtures for OpenAI Agent SDK and LangGraph.
- **FR-013**: System MUST define adapter compatibility requirements for LangChain, CrewAI, AutoGen, Semantic Kernel, and future frameworks through the same framework-neutral adapter contract.
- **FR-014**: System MUST include source adapter interface coverage for all target adapter families, with executable fixture/stub coverage for at least one fetch-like adapter result and one non-fetch adapter result.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior when outputs are affected.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, and export/withdrawal behavior when those boundaries are affected.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities *(include if feature involves data)*

- **Domain Contract**: A VeraCrawl-owned schema or aggregate that defines canonical state, references, lifecycle, ownership, and validation rules.
- **Owner Service**: The single service authorized to mutate an aggregate or append an audit record, such as control, scheduler, fetch, browser, agents, projection, export, ops, or artifact lifecycle.
- **Port**: A VeraCrawl-owned interface that core packages depend on for replaceable storage, queue, model, browser, source adapter, agent runtime, policy, replay, projection, and export behavior.
- **Adapter**: A replaceable implementation behind a port, including source adapters and agent framework adapters.
- **Agent Framework Adapter**: A plugin that maps a framework such as OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, or Semantic Kernel to VeraCrawl-owned runtime, context, tool, model, command, and trace contracts.
- **Command/Event Record**: A replayable mutation request, result, and emitted event with causation, correlation, idempotency, policy, and payload refs.
- **Fixture Oracle**: A deterministic expected-output, evidence, event, graph, failure, replay, or DR restore definition used to validate implementation behavior.

### Non-Goals *(mandatory)*

- This feature does not implement the full crawler runtime, production worker fleet, browser execution engine, export connector suite, memory kernel, graph store, or complete target architecture behavior.
- This feature does not implement a real production HTTP crawl path or real production agent framework integrations; it defines executable skeletons, interfaces, conformance fixtures, and contract tests.
- This feature does not couple VeraCrawl core to OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, or any other agent framework.
- This feature does not optimize for schedule, staffing, or short-term delivery by narrowing the target architecture.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of foundation contracts affected by this feature have an owner service, mutation path, replay behavior, and acceptance test category.
- **SC-002**: 100% of foundation command/event types introduced by this feature have payload schema coverage and at least one negative validation case.
- **SC-003**: OpenAI Agent SDK and LangGraph adapter conformance scenarios prove that core contracts remain unchanged across different frameworks.
- **SC-004**: Source adapter conformance covers HTTP-like and non-HTTP-like adapter outcomes without requiring non-fetch sources to fake fetch/page snapshot semantics.
- **SC-005**: Replay validation fails or returns needs-review when any required command result, source adapter result, event cursor, artifact hash, trace ref, or redaction map is missing.
- **SC-006**: Security and policy fixtures prove unsafe or unauthorized source, credential, browser, prompt, export, memory, and artifact lifecycle actions are blocked and visible.
- **SC-007**: No generated plan or task can pass constitution checks if it introduces direct core coupling to an agent framework or direct cross-owner mutation.

## Assumptions

- The foundation is allowed to define architecture and contract requirements because the user explicitly requested target architecture foundation work.
- Existing target docs are authoritative and are already approved for Spec Kit implementation planning.
- Python remains mandatory under the current constitution.
- Framework adapter support means adapter compatibility and conformance contracts, not direct dependency from core packages.
- Initial framework conformance fixtures use OpenAI Agent SDK and LangGraph as representative adapters; other named frameworks are compatibility targets for later adapter implementations.
- Initial source adapter fixtures use one fetch-like adapter result and one non-fetch adapter result to prove typed adapter output semantics before production adapter implementations.
- Broader target contract areas that are outside the materialized foundation subset must be represented by explicit registry coverage entries rather than implied or silently omitted.
- Implementation details such as exact package names, dependency versions, storage products, and module layout will be finalized in `$speckit-plan`.
