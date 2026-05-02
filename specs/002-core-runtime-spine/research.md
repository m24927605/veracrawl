# Research: VeraCrawl Target Core Runtime Spine

## Decision: First Success Fixture Is Record Output From Fetch-Like Local Source

**Rationale**: A record-output fixture is the smallest end-to-end path that still exercises objective, plan, run, source adapter result, raw artifact ref, normalized anchor, extraction candidate, field-level evidence, verification, publication, output manifest, and replay. It proves the product path without requiring browser, graph, memory, export, or distributed worker profiles to be falsely marked target-complete.

**Alternatives considered**:

- Table/document/dataset/fact first: broader surface, but it increases oracle complexity before the owner-service spine is proven.
- Browser-authenticated first: valuable target profile, but it would couple this feature to browser/security details better handled by a dedicated profile.
- Agent-generated output first: risks making the deterministic success path depend on a framework or model provider.

## Decision: In-Memory Canonical Repositories Behind Ports

**Rationale**: The feature must implement runtime behavior without introducing concrete Postgres, queue, object store, browser, or model provider clients into core. In-memory repositories allow command/event/owner/replay semantics to be tested deterministically while preserving production architecture through ports.

**Alternatives considered**:

- Concrete database now: would force migrations and infrastructure adapters into a spine feature and increase coupling risk.
- Fixture files as canonical state: too weak for owner-service mutation, idempotency, and state transition tests.
- Ad hoc module globals: not replayable, not injectable, and not compatible with later adapter replacement.

## Decision: Fixture-Run Artifact Store With Content Hashes

**Rationale**: The spine needs raw artifact refs, normalized artifact refs, output manifests, replay refs, privacy classification, lifecycle state, and deterministic artifact hashes. A fixture-run artifact store behind `ArtifactStorePort` proves these semantics without choosing production object storage.

**Alternatives considered**:

- Store artifact bodies directly in contracts: violates artifact/reference separation and makes replay/privacy handling brittle.
- Omit artifact bodies: cannot validate evidence anchors, hashes, or replay completeness.
- Production object store adapter: out of scope for this feature and forbidden as a core dependency.

## Decision: Independent Runtime Completion Gates

**Rationale**: A single `completed` run status can hide missing evidence, incomplete replay, or unpublished outputs. Independent gates for objective, plan, source, normalization, extraction, evidence, verification, publication, and replay make partial completion explicit and prevent false success claims.

**Alternatives considered**:

- One terminal run status only: insufficient for non-deceptive completion rules.
- Gate status derived only at report time: makes state transitions and operator-visible failures less testable.
- Publication implies replay completion: incorrect because replay may be structurally incomplete under redaction or missing refs.

## Decision: Owner Services Own Mutations, Agents Provide Recommendations

**Rationale**: Agents must help planning, extraction, verification, and repair, but durable mutations must remain command/event backed and owner-service validated. This preserves framework neutrality and prevents hidden framework state from becoming canonical runtime state.

**Alternatives considered**:

- Agent framework directly mutates runtime state: violates constitution and replay requirements.
- Disable agents in this feature: weakens target architecture and misses the framework-neutral recommendation path.
- Couple to one initial agent framework: undermines adapter portability and future compatibility.

## Decision: Mandatory Negative Fixtures

**Rationale**: The runtime spine is only trustworthy if unsafe or incomplete paths fail visibly. The mandatory negative fixtures cover blocked source, missing evidence, verification conflict, adapter mismatch, replay gap, direct cross-owner mutation, and forbidden framework/core imports.

**Alternatives considered**:

- Only happy-path fixture: insufficient for policy, replay, and non-deceptive completion.
- Push boundary violations to unit tests only: fixture/oracle coverage is needed to prove end-to-end operator-visible outcomes.
- Treat conflicts as failures only: conflicts should create review/conflict state and prevent publication rather than collapse into generic failure.

## Decision: Runtime CLI/Harness Is Developer-Facing, Not Product UI

**Rationale**: This feature needs deterministic verification commands and fixture outputs, not a user-facing console. Product UI and operator consoles are separate acceptance profiles.

**Alternatives considered**:

- Build a web UI now: distracts from runtime correctness and increases frontend scope.
- No CLI/harness: makes acceptance difficult to reproduce and weakens Spec Kit tasks.
