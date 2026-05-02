# Feature Specification: VeraCrawl Model Provider Adapter Operational Gate

**Feature Branch**: `025-model-provider-adapter-operational-gate`  
**Created**: 2026-05-03  
**Status**: Draft  
**Input**: User description: "建立 VeraCrawl Model Provider Adapter Operational Gate：在 framework-neutral agent runtime 與 agent runtime adapter gate 之上，實作 model-provider-owned operational gate，證明 OpenAI、Anthropic、Google Gemini、OpenAI-compatible endpoint、local model runtime 與 future provider adapters 能映射到 VeraCrawl canonical ModelRequest、ModelResponse、ModelCallTrace、ContextBundleTrace、AgentRunRequest、AgentRunResult、AgentActionTrace、CommandResult、policy、observability、security/privacy、replay refs；core 不得直接耦合任何 model SDK 或 provider SDK；不得把 provider-native transcript、raw prompts/responses、raw credentials 或 unsafe tool suggestions 當 canonical state；缺少 live provider runtime/API credentials 時必須 needs_review，不得假裝 operational pass；必須遵守 docs/07、09、10、11 與 constitution，不得實作成單站 scraper。"

## Constitution Alignment

- **General-purpose crawler impact**: This strengthens VeraCrawl as a general-purpose AI agent crawler by making model providers interchangeable behind canonical request/response/trace contracts. No website, schema, model vendor, or provider runtime becomes special.
- **Target/V1 boundary**: This is target architecture work after `001`, `011`, `023`, and `024`. It completes the model-provider half of the framework-neutral agent runtime stage from `docs/10-target-implementation-design.md`; it does not claim full production crawling completion.
- **Evidence and replay impact**: Adds provider gate reports tying `ModelRequest`, `ModelResponse`, `ModelCallTrace`, `ContextBundleTrace`, `AgentRunRequest`, `AgentRunResult`, `AgentActionTrace`, command result, policy, observability, security/privacy, and replay refs into one conformance result.
- **Safety and policy impact**: Raw prompts, raw responses, provider-native transcripts, credentials, and unsafe tool suggestions cannot become canonical. Missing live provider runtime/API credentials must return `needs_review`; unsafe leaks or missing replay/security refs fail.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`.

## User Scenarios & Testing

### User Story 1 - Canonical Model Provider Mapping (Priority: P1)

An integrator can run a deterministic model provider gate and prove OpenAI, Anthropic, Google Gemini, OpenAI-compatible endpoint, local model runtime, and future provider adapters all map to VeraCrawl canonical model/runtime contracts.

**Why this priority**: VeraCrawl must maximize AI crawling ability without locking core behavior to one provider SDK.

**Independent Test**: Run `model-provider-adapter-success`; it passes only when every provider family has execution refs plus model request, response, trace, context, agent action, command, policy, observability, security/privacy, and replay refs.

**Acceptance Scenarios**:

1. **Given** adapter-owned provider contract adapters, **When** the gate runs, **Then** the report is `pass` with required refs for every provider family.
2. **Given** a provider produces native response metadata, **When** the gate records it, **Then** canonical output uses VeraCrawl refs rather than provider-native transcript state.

---

### User Story 2 - Missing Live Provider Needs Review (Priority: P2)

An operator can distinguish provider contract readiness from live provider availability.

**Why this priority**: The system must not claim operational provider integration when credentials, runtime, SDK, or endpoint execution did not happen.

**Independent Test**: Run `model-provider-adapter-runtime-unavailable`; it returns `needs_review` with contract-only and missing-runtime refs.

**Acceptance Scenarios**:

1. **Given** no live provider credentials or runtime, **When** the provider gate runs, **Then** it returns `needs_review`.
2. **Given** only adapter contract descriptors, **When** the gate runs, **Then** it does not claim live model provider operational pass.

---

### User Story 3 - Unsafe Or Incomplete Provider Mapping Fails (Priority: P3)

The gate fails when model provider adapters leak raw prompts/responses, persist provider-native transcripts as canonical state, omit context/security/replay refs, or emit unsafe tool suggestions.

**Why this priority**: Model provider flexibility is useful only if safety, replay, and canonical ownership are preserved.

**Independent Test**: Run negative fixtures for raw prompt leak, raw response leak, provider-native canonicalization, missing context trace, missing security/privacy refs, missing replay refs, unsafe tool suggestion, and unsupported provider.

**Acceptance Scenarios**:

1. **Given** an adapter reports raw prompt or raw response persistence, **When** the gate validates it, **Then** the report fails.
2. **Given** an adapter emits provider-native transcript as canonical output, **When** the gate validates it, **Then** the report fails.
3. **Given** an adapter omits context, replay, or security/privacy refs, **When** the gate validates it, **Then** the report fails.

### Edge Cases

- A provider has only contract adapter refs and no live runtime refs: return `needs_review`.
- A provider adapter returns provider-native transcript metadata but does not mark it canonical: allowed only as diagnostic refs.
- A provider response suggests an unsafe tool call or side effect: fail unless policy and command refs prove it was blocked.
- A provider adapter omits `ContextBundleTrace` or `ModelCallTrace`: fail.
- An OpenAI-compatible endpoint appears through the same contract: pass only if it satisfies the same record requirements.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define model provider adapter execution and gate report contracts.
- **FR-002**: System MUST expose a repeatable `veracrawl-model-providers` fixture runner.
- **FR-003**: System MUST support OpenAI, Anthropic, Google Gemini, OpenAI-compatible endpoint, local model runtime, and future provider families through one adapter contract.
- **FR-004**: System MUST keep core independent of model provider SDKs and provider-native clients.
- **FR-005**: Passing reports MUST include model request, response, model trace, context trace, agent request/result/action trace, command result, policy, observability, security/privacy, and replay refs.
- **FR-006**: Missing live provider runtime/API credentials MUST return `needs_review`; they MUST NOT be coerced to pass.
- **FR-007**: Raw prompts, raw responses, raw credentials, and provider-native transcripts MUST NOT be canonical state.
- **FR-008**: Provider-native transcript metadata MAY be diagnostic only when canonical VeraCrawl refs are complete.
- **FR-009**: Negative provider scenarios MUST fail deterministically for raw prompt leak, raw response leak, provider-native canonical state, missing context trace, missing replay refs, missing security/privacy refs, unsafe tool suggestion, and unsupported provider.
- **FR-010**: CLI provider loading MUST be dynamic and adapter-owned; static imports of concrete provider SDKs in core or CLI are forbidden.

### VeraCrawl Contract Requirements

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid provider-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST register affected contracts, commands, events, typed results, policy decisions, and replay refs.
- **VC-003**: System MUST preserve evidence/publication boundaries; model output is not source evidence or published output by itself.
- **VC-004**: System MUST preserve prompt-injection, credential, privacy lifecycle, observability, and replay boundaries.
- **VC-005**: System MUST define fixture/oracle, negative, replay, import-boundary, and acceptance tests before implementation.

### Key Entities

- **ModelProviderAdapterExecutionRecord**: Per-provider execution record tying provider family, model request/response/trace, context trace, agent run refs, command, policy, observability, security/privacy, live/runtime, diagnostic provider state, and replay refs.
- **ModelProviderAdapterReport**: Gate-level result aggregating all provider families and determining pass/fail/needs-review.
- **ModelProviderAdapterFixtureManifest**: Fixture manifest describing expected completion result and failure type for provider adapter gate tests.

### Non-Goals

- This feature does not call external model APIs.
- This feature does not implement production model account management, token billing, vendor observability, rate-limit retry orchestration, or model selection optimization.
- This feature does not make provider-native transcript state canonical.
- This feature does not implement UI, production worker fleets, browser rendering, export delivery, managed observability, cloud deployment, or vendor operations.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `model-provider-adapter-success` produces `pass` with all required provider refs.
- **SC-002**: `model-provider-adapter-runtime-unavailable` produces `needs_review`.
- **SC-003**: Negative provider fixtures produce `fail` with the expected failure type.
- **SC-004**: Import-boundary tests prove core packages do not statically import provider SDKs or concrete provider adapters.
- **SC-005**: Contract registry validation includes model provider adapter contracts, command types, event types, fixture registrations, and target area coverage.
- **SC-006**: Full test suite and Docker-backed live operational gates remain passing after implementation.

## Assumptions

- Deterministic adapter-owned contract adapters are sufficient to prove canonical mapping without network/API credentials.
- Live provider integration remains `needs_review` unless explicit live runtime refs are supplied by future adapter specs.
- Provider family names are target architecture compatibility families, not a guarantee that their SDKs are installed in the runtime environment.
