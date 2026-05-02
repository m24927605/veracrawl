# Feature Specification: VeraCrawl Memory Kernel

**Feature Branch**: `010-memory-kernel`  
**Created**: 2026-05-02  
**Status**: Draft  
**Input**: User description: "建立 VeraCrawl Memory Kernel and Scoped Retrieval/Invalidation Spine：在 advanced graph projection spine 之後，實作 memory event contract、memory retrieval trace、cross-scope memory tunnel、operational temporal memory record、memory write/retrieve/invalidation/supersession runtime、taint/trust/prompt-use policy gates、memory-derived strategy evidence re-anchor boundary，以及 fixture/oracle 測試基礎。必須遵守 docs/07、08、09、10、11 與 constitution；memory 不得取代 source evidence，不得讓 memory/graph 成為 publication source of truth；不得實作成單站 scraper；core 不得耦合 memory store、vector/search store、agent framework、model SDK、browser、storage、queue、export target 或具體 HTTP client。"

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This feature defines scoped memory primitives for site behavior, page type, extraction strategy, failure repair, task context, and agent diary memory without encoding a single website or vertical.
- **Target/V1 boundary**: This is target architecture dependency sequencing after `009-advanced-graph-projection`, aligned with `docs/08-build-roadmap.md` Phase 5 and `docs/10-target-implementation-design.md` memory architecture.
- **Evidence and replay impact**: Memory can guide planning and repair, but memory refs cannot satisfy publication evidence. Memory-derived strategies must re-anchor to current or selected source evidence before publication.
- **Safety and policy impact**: Memory writes and retrievals preserve trust, taint, freshness, prompt-use restrictions, poisoning checks, policy decisions, replay refs, and cross-scope authorization.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Write And Retrieve Scoped Memory (Priority: P1)

As a crawler planner, I need previous site behavior and repair lessons to be stored and retrieved with scope, freshness, taint, trust, sanitized context, evidence refs, and replay refs.

**Independent Test**: Run `veracrawl-memory run tests/fixtures/memory-write-retrieve-success --profile target --out .veracrawl-test-runs/memory-write-retrieve-success`.

**Acceptance Scenarios**:

1. **Given** evidence-backed operational lessons, **When** memory write runs, **Then** memory events include scope, provenance, evidence refs, trust, taint, poisoning check, freshness, prompt-use, policy, and replay refs.
2. **Given** scoped retrieval, **When** memory retrieval runs, **Then** retrieval traces list retrieved refs, excluded refs, policy refs, freshness refs, index refs, and sanitized context refs.

---

### User Story 2 - Exclude Invalidated Or Tainted Memory (Priority: P2)

As an operator, I need stale, invalidated, tainted, or prompt-forbidden memory excluded from planning and replay-visible when excluded.

**Independent Test**: `memory-invalidation-exclusion` passes only when invalidated memory is excluded; `poisoned-memory-blocked` fails when tainted memory would enter prompt/tool context.

**Acceptance Scenarios**:

1. **Given** invalidated memory, **When** retrieval runs, **Then** the memory is excluded and replay explains the exclusion.
2. **Given** poisoned or prompt-forbidden memory, **When** prompt/tool context would use it, **Then** memory use fails with `tainted_memory_for_prompt`.

---

### User Story 3 - Enforce Cross-Scope And Evidence Boundaries (Priority: P3)

As a platform owner, I need cross-scope memory to require authorization and sanitized-only transfer, and I need memory-derived strategies to re-anchor to evidence before publication.

**Independent Test**: `cross-scope-sanitized-memory` passes with authorization and sanitized-only tunnel; `unauthorized-cross-scope-memory` and `memory-as-evidence` fail with typed reports.

**Acceptance Scenarios**:

1. **Given** cross-scope memory retrieval, **When** authorization and policy allow it, **Then** retrieval uses a `CrossScopeMemoryTunnel` with sanitized-only and taint-exclusion rules.
2. **Given** memory refs are offered as publication evidence, **When** evidence boundary validation runs, **Then** the attempt fails with `memory_as_evidence` and `missing_reanchor_evidence`.

### Edge Cases

- Missing memory scope, provenance, policy, poisoning, freshness, sanitized context, or evidence refs.
- Invalidated memory returned as retrieved.
- Cross-scope tunnel lacks authorization, sanitized-only restriction, or taint exclusion.
- Memory ref used as source evidence or publication proof.
- Tainted memory enters prompt/tool context.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define `MemoryEvent`, `MemoryRetrievalTrace`, `CrossScopeMemoryTunnel`, `OperationalTemporalMemoryRecord`, `MemoryKernelReport`, and `MemoryFixtureManifest` contracts.
- **FR-002**: System MUST write memory events with scope, type, content ref, provenance refs, evidence refs, trust level, taint labels, promotion policy, poisoning check, sanitized context, allowed prompt use, freshness, status, and policy refs.
- **FR-003**: System MUST retrieve memory through traces that record retrieved refs, excluded refs, exclusion reasons, policy refs, freshness cutoff, retrieval index refs, tunnel refs, taint labels, and sanitized context refs.
- **FR-004**: System MUST exclude invalidated memory from retrieved refs and record replay-visible exclusion reasons.
- **FR-005**: System MUST block tainted or prompt-forbidden memory from prompt/tool context.
- **FR-006**: System MUST require cross-scope memory tunnels to have different scopes, allowed memory types, authorization, policy refs, sanitized-only transfer, evidence anchoring, and taint exclusion rules before use.
- **FR-007**: System MUST record operational temporal memory separately from publication temporal graph records.
- **FR-008**: System MUST reject memory-as-evidence and require current or selected historical evidence re-anchoring before publication.
- **FR-009**: System MUST include success fixtures for memory write/retrieve, invalidation exclusion, and cross-scope sanitized memory.
- **FR-010**: System MUST include negative fixtures for poisoned memory, unauthorized cross-scope memory, and memory-as-evidence.
- **FR-011**: System MUST register contracts, commands, events, fixtures, and target area coverage in the executable registry.
- **FR-012**: System MUST keep core independent of concrete memory stores, vector/search stores, graph stores, browser, HTTP client, storage, queue, model SDK, agent framework, export target, and site-specific scraper dependencies.
- **FR-013**: System MUST document implemented memory kernel capability and explicitly avoid claiming production memory store, vector search, export, distributed persistence, production browser rendering, or production scale readiness.

### Non-Goals *(mandatory)*

- This feature does not implement a production memory store, vector store, search store, memory retrieval service API, memory UI, export delivery, distributed persistence, or production scale operations.
- This feature does not let memory satisfy evidence or publication requirements.
- This feature does not use LLM/model calls or external agent frameworks.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria *(mandatory)*

- **SC-001**: Memory write/retrieve fixture emits memory event, retrieval trace, operational temporal record, report refs, and pass result.
- **SC-002**: Invalidation fixture excludes invalidated memory and records exclusion reason while still passing replay.
- **SC-003**: Cross-scope fixture emits authorized sanitized-only tunnel refs and pass result.
- **SC-004**: Poisoned memory, unauthorized cross-scope memory, and memory-as-evidence fixtures produce typed non-success reports.
- **SC-005**: Registry validation includes every memory contract, command, event, fixture, and test ref.
- **SC-006**: Import-boundary tests prove core memory packages do not import concrete memory/vector/search stores, graph stores, browser, HTTP client, storage, queue, model SDK, agent framework, export target, or site-specific scraper dependencies.
- **SC-007**: Full local memory gate completes within 30 seconds in the deterministic fixture profile.
