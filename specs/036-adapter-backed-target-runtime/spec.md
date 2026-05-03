# Feature Specification: VeraCrawl Adapter-Backed Target Runtime

**Feature Branch**: `036-adapter-backed-target-runtime`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "Build VeraCrawl Adapter-Backed Target Runtime: extend target crawl runtime so source-backed target fixtures can require source adapter result records, adapter output refs, adapter policy/replay refs, and adapter-backed observations produced behind SourceAdapterPort. Core must remain framework-neutral and adapter-neutral; CLI/adapters may materialize deterministic local source adapter outputs. Negative fixtures must fail on missing adapter result, adapter output mismatch, policy-denied adapter output, replay mismatch, and direct source bypass. Do not implement a single-site scraper."

## Hard Constraints

- **General-purpose crawler**: Implementation must model adapter-backed acquisition for target runtime, not a single-site scraper.
- **Low coupling, high cohesion**: Target runtime core may depend on VeraCrawl contracts only. Concrete adapter materialization belongs outside core behind ports/adapters.
- **Framework neutrality**: No concrete agent framework, model SDK, browser runtime, HTTP client, storage client, queue client, or export destination dependency may enter target runtime core.
- **Non-deceptive completion**: Adapter-backed completion requires source adapter result refs, adapter output refs, policy refs, replay refs, source observations, content hashes, evidence, graph, export, and operator-visible report refs.

## User Stories & Testing

### User Story 1 - Complete Adapter-Backed Source Runtime (Priority: P1)

As a crawler platform engineer, I need target runtime success to prove that source observations were backed by source adapter outputs rather than direct file reads only.

**Independent Test**: Run `veracrawl-target-runtime run tests/fixtures/adapter-backed-target-success --profile target --out .veracrawl-test-runs/adapter-backed-target-success`; the report passes only when at least seven source observations include adapter-backed records and source adapter result refs.

**Acceptance Scenarios**:

1. Given a multi-pattern source corpus and adapter backing manifest, when the target runtime runs, then every accepted output has source observation, content hash, adapter result, adapter output, evidence, graph, export, policy, event/outbox, and replay refs.
2. Given drift alias evidence in an adapter-backed source, when the runtime repairs extraction, then the report includes a framework-neutral AI repair recommendation without framework-native state.

### User Story 2 - Block Adapter-Backed False Completion (Priority: P2)

As a Staff reviewer, I need adapter-backed target fixtures to fail when adapter output proof is missing, mismatched, policy-blocked, replay-mismatched, or bypassed by direct source access.

**Independent Test**: Negative adapter-backed fixtures fail or block with typed target runtime failures and cannot produce `complete`.

**Acceptance Scenarios**:

1. Missing source adapter result refs fail with `target_runtime_adapter_result_missing`.
2. Adapter output mismatch fails with `target_runtime_adapter_output_mismatch`.
3. Policy-denied adapter output blocks with `target_runtime_policy_denied`.
4. Replay mismatch fails with `target_runtime_replay_mismatch`.
5. Direct source bypass fails with `target_runtime_direct_source_bypass`.

### User Story 3 - Preserve Adapter/Core Boundary (Priority: P3)

As a maintainer, I need adapter materialization to stay outside target runtime core while still being executable through the CLI.

**Independent Test**: Import-boundary tests prove `veracrawl.target_runtime` imports no concrete adapters or SDKs; integration tests prove the CLI can load deterministic local adapter materialization and pass only canonical records into core.

## Edge Cases

- Adapter backing manifest references a corpus entry that does not exist.
- Adapter result exists but produces no output refs.
- Adapter output refs exist but do not correspond to the source observation content hash.
- Adapter record attempts to mark direct source fallback as acceptable.
- Adapter policy denial is present alongside otherwise valid source content.
- Adapter-backed replay oracle disagrees with source content hash.

## Requirements

- **FR-001**: System MUST define adapter-backed target runtime contracts for adapter backing entries, manifests, and observation records.
- **FR-002**: System MUST allow `TargetRuntimeFixtureManifest` to reference an adapter backing manifest.
- **FR-003**: System MUST materialize adapter-backed source observation records outside target runtime core and pass only canonical VeraCrawl records into core.
- **FR-004**: System MUST expose aggregate source adapter result refs, adapter output refs, and adapter-backed source refs on `TargetRuntimeReport`.
- **FR-005**: System MUST fail or block missing adapter result, adapter output mismatch, policy-denied adapter output, replay mismatch, and direct source bypass fixtures.
- **FR-006**: System MUST preserve existing 034 deterministic target runtime and 035 source-backed runtime behavior.
- **FR-007**: System MUST register contracts, commands/events where applicable, fixtures, and target area coverage in the contract registry.
- **FR-008**: System MUST update target capability, implementation, and acceptance docs so adapter-backed runtime cannot be confused with live Internet crawling or a single-site scraper.

## Key Entities

- **TargetAdapterBackedSourceEntry**: Declares adapter type, corpus entry mapping, adapter policy, expected output/hash, and direct fallback policy.
- **TargetAdapterBackedSourceManifest**: Declares adapter-backed acquisition requirements for a target runtime fixture.
- **TargetAdapterBackedSourceRecord**: Canonical adapter-backed proof record tying source adapter result refs and adapter output refs to source observations and content hashes.
- **TargetRuntimeReport**: Aggregate target report extended with adapter-backed source, source adapter result, and adapter output refs.

## Success Criteria

- **SC-001**: Adapter-backed success fixture completes with seven website patterns and seven adapter-backed records.
- **SC-002**: Every adapter-backed accepted output includes source observation, content hash, source adapter result, adapter output, evidence, graph, policy, command/event/outbox, export, and replay refs.
- **SC-003**: Negative adapter-backed fixtures fail or block deterministically with typed target runtime failures.
- **SC-004**: Import-boundary tests prove target runtime core remains adapter-neutral.
- **SC-005**: Full non-Docker and Docker-backed test gates pass.

## Assumptions

- Adapter-backed local fixtures use deterministic local source adapter materialization, not external network access.
- Live Internet crawling remains a separate future production adapter capability and is not claimed by this spec.
- Existing source-backed corpus descriptors remain the content/evidence source; adapter-backed records prove acquisition lineage around those descriptors.
