# Feature Specification: Real-World AI Agent Crawl Planning And Extraction Benchmark

**Feature Branch**: `056-real-world-ai-agent-benchmark`  
**Created**: 2026-05-03  
**Status**: Draft  
**Input**: User request: "請使用 Spec Kit 建立並實作 056 Real-World AI Agent Crawl Planning And Extraction Benchmark."

## Constitution Alignment

- **General-purpose crawler impact**: Adds a manifest-driven public corpus benchmark proving real crawl planning, site understanding, extraction candidate generation, and verification/repair decisions are mediated by VeraCrawl's framework-neutral model/agent ports. It must not add a single-site scraper, domain-specific parser, or hard-coded website extraction rule.
- **Target/V1 boundary**: Target architecture validation work after row 055. This spec proves the live public corpus gate can be combined with row 049 model/agent adapter contracts and row 047 evidence/verification/publication discipline.
- **Evidence and replay impact**: Requires live HTTP report refs, source observation refs, artifact refs, content hash refs, source anchor refs, model call traces, agent action traces, tool call traces, context bundle traces, command/event/outbox refs, and replay refs before the benchmark can pass.
- **Safety and policy impact**: Keeps public crawling read-only and allowlisted, preserves robots/private-network gates from row 055, redacts raw model prompts/responses, blocks LLM output as source evidence, blocks direct publication bypass, and forbids framework-native state as canonical core state.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `AGENTS.md`, `README.md`, and `specs/038-production-runtime-closure/spec.md`.

## User Scenarios & Testing

### User Story 1 - Run Real Public Crawl With AI Agent Decisions (Priority: P1)

An operator can run one benchmark command against an authorized public corpus and inspect a report proving every crawled public target had AI-assisted crawl planning, site understanding, extraction candidate generation, and verification/repair decisions.

**Why this priority**: The product claim is an AI agent crawler. A live HTTP corpus without AI decision traces is not sufficient proof.

**Independent Test**: Run `veracrawl-real-ai-benchmark run tests/fixtures/real-world-ai-agent-public-corpus --profile target --out .veracrawl-real-runs/real-world-ai-agent-public-corpus` and verify the aggregate report passes with non-empty model call, agent action, tool call, context bundle, source anchor, candidate, verification, command/event/outbox, and replay refs.

**Acceptance Scenarios**:

1. **Given** a corpus manifest referencing public authorized targets, **When** the benchmark runs, **Then** every target is fetched through row 055 live HTTP acquisition and every site has AI decision traces for all required decision kinds.
2. **Given** a successful AI decision, **When** saved outputs are inspected, **Then** model request/response refs, model call traces, agent run request/result refs, agent action traces, tool call traces, and context bundle traces exist and are tied to source artifact/content hash refs.

### User Story 2 - Keep AI Output Separate From Source Evidence (Priority: P2)

An operator can trust that LLM/agent output influences planning and candidate proposals but never becomes source evidence or directly published output.

**Why this priority**: VeraCrawl's correctness depends on source-backed evidence. AI text can guide extraction, but it cannot replace observed website artifacts.

**Independent Test**: Run negative fixtures for LLM-output-as-evidence, missing candidate anchors, and publication bypass; each must fail with a typed diagnostic.

**Acceptance Scenarios**:

1. **Given** an extraction candidate produced after an AI decision, **When** the report passes, **Then** the candidate is bound to source anchor refs, artifact refs, and content hash refs from the live crawl.
2. **Given** a candidate whose evidence only points to a model response, **When** validation runs, **Then** the benchmark fails with `real_world_ai_llm_output_as_evidence`.
3. **Given** a published output ref without evidence/verification gate refs, **When** validation runs, **Then** the benchmark fails with `real_world_ai_publication_bypass`.

### User Story 3 - Prove Framework-Neutral Agent/Model Boundaries (Priority: P3)

A maintainer can verify the benchmark uses VeraCrawl-owned ports and contracts rather than directly coupling core to OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, or any other agent framework.

**Why this priority**: VeraCrawl must support all agent frameworks through adapters while keeping core contracts portable and replayable.

**Independent Test**: Run import-boundary tests and registry validation; core benchmark modules must not import concrete model SDKs or agent frameworks, while CLI composition may dynamically load adapters.

**Acceptance Scenarios**:

1. **Given** the benchmark runtime module, **When** import-boundary tests parse imports, **Then** no forbidden framework/model SDK imports appear in core.
2. **Given** a report containing framework-native state refs as canonical state, **When** validation runs, **Then** it fails with `real_world_ai_framework_state_persisted`.
3. **Given** missing model, agent, tool, context, command, event, outbox, or replay refs, **When** validation runs, **Then** it fails with a typed benchmark failure.

## Edge Cases

- Public corpus crawl fails due to DNS, TLS, timeout, robots denial, or observation drift: the AI benchmark must fail or need review through the row 055 report instead of fabricating AI success.
- A site contains prompt-injection text: the text remains tainted page content in a context bundle; controlled tools and policy refs are still required before any action.
- The model adapter returns a parsed output ref but no source anchors: candidate generation fails because source anchors/artifacts/content hashes are mandatory.
- Model response or agent recommendation is accidentally attached as source evidence: the report fails before publication.
- External agent framework adapter exposes native state: that state may only be diagnostic and must not be saved as canonical core state.
- Replay bundle refs are missing for any AI decision, candidate, or aggregate report: the report fails with replay diagnostics.
- External provider credentials are unavailable: deterministic validation uses the local model provider adapter and native agent adapter through the same neutral ports; an external provider adapter can be plugged in without changing core.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define contracts for `RealWorldAIAgentDecisionTrace`, `RealWorldAIAgentExtractionCandidate`, `RealWorldAIAgentBenchmarkRunReport`, and `RealWorldAIAgentBenchmarkManifest`.
- **FR-002**: System MUST run row 055 real-world public corpus acquisition before any AI benchmark pass can be reported.
- **FR-003**: System MUST invoke a `ModelProviderPort` and an `AgentRuntimePort` for crawl planning, site understanding, extraction candidate generation, and verification/repair decision on every passing public site observation.
- **FR-004**: System MUST record model call traces, agent action traces, tool call traces, and context bundle traces for every AI decision.
- **FR-005**: System MUST record policy refs, command refs, event cursor refs, outbox refs, and replay refs for every AI decision and for the aggregate report.
- **FR-006**: System MUST bind every extraction candidate to source anchor refs, source artifact refs, and content hash refs from the live public crawl.
- **FR-007**: System MUST treat model/agent outputs as recommendations or candidate payload refs only; they MUST NOT be recorded as source evidence.
- **FR-008**: System MUST require evidence coverage, evidence packet, evidence anchor, verification decision, review decision, and publication gate refs before a candidate can be considered eligible for publication.
- **FR-009**: System MUST fail direct publication refs that bypass evidence/verification gates.
- **FR-010**: System MUST keep VeraCrawl core independent of OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, model SDKs, concrete adapters, and framework-native state.
- **FR-011**: CLI output MUST write deterministic JSON reports for aggregate report, decision traces, extraction candidates, model/agent/tool/context traces, and a machine-readable summary.
- **FR-012**: Test suite MUST include contract, registry, runtime, CLI/fixture, negative, replay, and import-boundary tests, plus one recorded live public corpus AI benchmark validation.

### VeraCrawl Contract Requirements

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: System MUST register owner services, commands, events, typed failures, fixture oracles, and target area coverage for the real-world AI agent benchmark.
- **VC-003**: System MUST define evidence, verification, publication, and output manifest behavior for AI-generated extraction candidates while blocking publication bypass.
- **VC-004**: System MUST define source scope, robots, private-network, prompt-injection, credential, privacy lifecycle, retention, and replay boundaries.
- **VC-005**: System MUST define fixture/oracle, negative, replay, import-boundary, focused, full, Docker-backed, and live public validation before the spec can be marked complete.

### Key Entities

- **RealWorldAIAgentDecisionTrace**: One AI-mediated decision for one site and decision kind, tied to model call, agent action, tool call, context bundle, policy, command/event/outbox, source, and replay refs.
- **RealWorldAIAgentExtractionCandidate**: One AI-proposed candidate that remains separate from publication and is bound to source anchors, artifacts, content hashes, evidence, verification, and publication gate refs.
- **RealWorldAIAgentBenchmarkRunReport**: Aggregate proof that row 055 real public crawling and framework-neutral AI decision traces both exist and pass all safety/evidence/replay gates.
- **RealWorldAIAgentBenchmarkManifest**: Fixture manifest declaring the row 055 corpus fixture, required decision kinds, provider/framework adapter names, expected result, and negative-case expectations.

### Non-Goals

- This spec does not implement a single-site scraper, domain-specific extraction parser, website-specific schema, CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.
- This spec does not require external API credentials in CI; external LLM/provider/framework adapters remain pluggable behind the same neutral ports.
- This spec does not directly publish real website extracted outputs; it proves candidate generation and publication gate readiness with source-backed evidence refs.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A declared public corpus of at least four URLs runs through one AI benchmark CLI command and produces a passing aggregate report when the public sites match their oracles.
- **SC-002**: 100% of passing site observations have four AI decision kinds: crawl planning, site understanding, extraction candidate generation, and verification/repair.
- **SC-003**: 100% of AI decisions include model call trace, agent action trace, tool call trace, context bundle trace, policy, command, event cursor, outbox, and replay refs.
- **SC-004**: 100% of extraction candidates include source anchor refs, artifact refs, content hash refs, evidence gate refs, verification gate refs, and no LLM-output-as-evidence refs.
- **SC-005**: Missing AI traces, missing candidate anchors, LLM-as-evidence, publication bypass, framework-native canonical state, core import coupling, and replay gaps fail with typed diagnostics.
- **SC-006**: Ruff, mypy, registry validation, focused tests, full pytest, Docker-backed pytest, and one live public AI benchmark CLI run are executed and recorded in `tasks.md`.

## Assumptions

- The default live corpus reuses `tests/fixtures/real-world-public-corpus` from row 055.
- The default adapter composition uses the existing local model provider adapter and VeraCrawl native agent adapter through `ModelProviderPort` and `AgentRuntimePort`; external model/provider/framework adapters can replace them without changing core contracts.
- The benchmark records trace refs and structured canonical trace objects, but raw prompts/responses remain redacted unless a future policy explicitly permits retention.
- Evidence anchors for the benchmark are coarse source anchors derived from the live site observation, artifact, and content hash refs; AI output never becomes source evidence.
