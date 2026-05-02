# Feature Specification: VeraCrawl Agent Runtime Adapter Operational Gate

**Feature Branch**: `024-agent-runtime-adapter-operational-gate`  
**Created**: 2026-05-03  
**Status**: Draft  
**Input**: User description: "建立 VeraCrawl Agent Runtime Adapter Operational Gate：在 framework-neutral agent runtime foundation 與 multi-agent repair spine 之上，實作 adapter-owned operational gate，證明 model provider adapter 與 agent framework adapters 能映射到 VeraCrawl canonical AgentRunRequest、AgentRunResult、AgentActionTrace、ModelCallTrace、ToolCallTrace、ContextBundleTrace、CommandResult、policy、observability、security/privacy、replay refs；必須支援 OpenAI Agent SDK、LangChain、LangGraph、CrewAI、AutoGen、Semantic Kernel 與 future framework 的同一 adapter contract；core 不得直接耦合任何 model SDK 或 agent framework；不得把 framework-native state 或 raw prompts/responses 當 canonical state；缺少 live SDK/runtime 時必須 needs_review，不得假裝 operational pass；必須遵守 docs/07、09、10、11 與 constitution，不得實作成單站 scraper。"

## Constitution Alignment

- **General-purpose crawler impact**: This feature strengthens VeraCrawl as a general-purpose AI agent crawler by letting multiple agent framework families map into the same canonical agent/runtime contracts without making any website, schema, source pattern, model provider, or framework special.
- **Target/V1 boundary**: This is target architecture work after `001`, `011`, `022`, and `023`. It does not alter V1 scope and does not claim production crawling completion by itself.
- **Evidence and replay impact**: Adds adapter-gate reports tying `AgentRunRequest`, `AgentRunResult`, `AgentActionTrace`, `ModelCallTrace`, `ToolCallTrace`, `ContextBundleTrace`, command result, policy, observability, security/privacy, and replay refs into a single conformance result.
- **Safety and policy impact**: Raw prompts/responses, credentials, and framework-native state cannot become canonical. Missing live SDK/runtime must return `needs_review`; unsafe leaks or missing replay/security refs fail.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`.

## User Scenarios & Testing

### User Story 1 - Prove Canonical Agent Adapter Mapping (Priority: P1)

An integrator can run a deterministic adapter gate and prove OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, and future framework adapters all map to the same VeraCrawl canonical runtime contracts.

**Why this priority**: The user requires VeraCrawl to be able to connect to all major agent frameworks while core remains decoupled.

**Independent Test**: Run `agent-runtime-adapter-success`; it passes only when every framework family has execution record refs plus agent action, model, tool, context, command, policy, observability, security/privacy, and replay refs.

**Acceptance Scenarios**:

1. **Given** adapter-owned framework contract adapters, **When** the gate runs, **Then** the report is `pass` with required refs for every framework family.
2. **Given** the same role request, **When** framework adapters run, **Then** canonical output uses VeraCrawl refs rather than framework-native state.

### User Story 2 - Reject Missing Live Runtime Claims (Priority: P2)

An operator can run a concrete SDK/runtime scenario without required live runtime refs and receive `needs_review` instead of a fake operational pass.

**Why this priority**: Non-deceptive completion is mandatory; missing SDK/runtime cannot be labeled operational.

**Independent Test**: Run `agent-runtime-adapter-runtime-unavailable`; it returns `needs_review` with contract-only and missing-runtime refs.

**Acceptance Scenarios**:

1. **Given** no live SDK/runtime refs, **When** the gate runs, **Then** it returns `needs_review`.
2. **Given** only adapter contract descriptors, **When** the gate runs, **Then** it does not claim live framework operational pass.

### User Story 3 - Block Unsafe Adapter Mappings (Priority: P3)

The gate fails when adapters leak raw prompt/response data, persist framework-native state as canonical state, omit model/tool/context/replay/security refs, or register unsupported frameworks.

**Why this priority**: Framework adapter power is only acceptable if safety, replay, and canonical ownership are preserved.

**Independent Test**: Run negative fixtures for raw prompt leak, framework-state canonicalization, missing model trace, missing tool trace, missing replay, missing security/privacy refs, and unsupported framework.

**Acceptance Scenarios**:

1. **Given** an adapter reports raw prompt persistence, **When** the gate validates it, **Then** the report fails.
2. **Given** an adapter emits framework-native state as canonical output, **When** the gate validates it, **Then** the report fails.
3. **Given** an adapter omits replay or security/privacy refs, **When** the gate validates it, **Then** the report fails.

### Edge Cases

- A framework has only contract adapter refs and no live runtime refs: return `needs_review`.
- A model provider call has raw prompt or raw response persisted: fail.
- A framework adapter returns diagnostic framework state but does not mark it canonical: allowed only as diagnostic refs.
- A tool-capable framework omits `ToolCallTrace` or command result refs: fail.
- An adapter reports policy refs but omits observability, security/privacy, or replay refs: fail.
- A future framework appears through the same contract: pass only if it satisfies the same record requirements.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define executable `AgentAdapterExecutionRecord`, `AgentRuntimeAdapterReport`, and `AgentRuntimeAdapterFixtureManifest` contracts.
- **FR-002**: System MUST expose a repeatable `veracrawl-agent-adapters` fixture runner.
- **FR-003**: System MUST support OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, and future framework families through one adapter contract.
- **FR-004**: System MUST keep core independent of model SDKs and agent framework SDKs.
- **FR-005**: Passing reports MUST include agent request/result/action trace, model trace, tool trace, context trace, command result, policy, observability, security/privacy, and replay refs.
- **FR-006**: Framework-native state MUST be diagnostic only and MUST NOT become canonical output, replay, or policy state.
- **FR-007**: Raw prompts, raw responses, raw credentials, and raw tool payload secrets MUST NOT be serialized as canonical refs.
- **FR-008**: Missing live SDK/runtime refs MUST return `needs_review`, not `pass`.
- **FR-009**: Negative adapter scenarios MUST fail deterministically for raw prompt leak, framework state canonicalization, missing model trace, missing tool trace, missing replay refs, missing security/privacy refs, and unsupported framework.
- **FR-010**: CLI adapter loading MUST be dynamic and adapter-owned; static imports of concrete framework modules in core or CLI are forbidden.

### VeraCrawl Contract Requirements

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid framework-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST define affected owner services, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior when outputs are affected; this feature does not publish outputs.
- **VC-004**: System MUST define security, credential, prompt-injection, privacy lifecycle, and export/withdrawal behavior when those boundaries are affected.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and acceptance tests before implementation.

### Key Entities

- **AgentAdapterExecutionRecord**: Per-framework adapter execution record tying framework family, runtime spec, request/result, traces, command, policy, observability, security/privacy, live/runtime, diagnostic state, and replay refs.
- **AgentRuntimeAdapterReport**: Gate-level result aggregating all framework families and determining pass/fail/needs-review.
- **AgentRuntimeAdapterFixtureManifest**: Fixture manifest declaring expected completion result, operator status, and negative failure type.

### Non-Goals

- This feature does not call external model APIs or require live customer credentials.
- This feature does not implement production model quality evaluation, prompt optimization, or agent reasoning quality beyond canonical trace completeness.
- This feature does not make framework-native state canonical.
- This feature does not implement UI, production worker fleets, browser rendering, export delivery, managed observability, cloud deployment, or vendor operations.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `agent-runtime-adapter-success` produces `pass` with all required framework refs.
- **SC-002**: `agent-runtime-adapter-runtime-unavailable` produces `needs_review`.
- **SC-003**: All negative fixtures produce `fail` with the expected failure type and missing field.
- **SC-004**: Import-boundary tests prove core and CLI do not statically import OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, or model SDK packages.
- **SC-005**: Registry validation reports no contract, command, event, fixture, or target-area errors.
- **SC-006**: Full test suite passes after implementation.

## Assumptions

- Deterministic adapter-owned contract adapters are sufficient to prove canonical mapping without network/API credentials.
- Live SDK/runtime integration remains `needs_review` unless explicit live runtime refs are supplied by future adapter specs.
- Existing `AgentRunRequest`, `AgentRunResult`, `AgentActionTrace`, `ModelCallTrace`, `ToolCallTrace`, and `ContextBundleTrace` contracts remain canonical.
