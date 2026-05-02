# Implementation Plan: VeraCrawl Target Core Runtime Spine

**Branch**: `002-core-runtime-spine` | **Date**: 2026-05-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-core-runtime-spine/spec.md`

## Summary

Implement the first executable target core runtime spine on top of the completed foundation. The runtime must take a governed `CrawlObjective` through approved `CrawlPlan`, `CrawlRun`, source adapter execution, artifact refs, normalization, extraction candidate, evidence packet, verification decision, published output manifest, and replay bundle. The first successful profile is a deterministic record-output fixture from a fetch-like local source with normalized anchors and field-level evidence.

This plan deliberately keeps concrete databases, queues, browser engines, model SDKs, storage clients, and agent frameworks outside core. The feature uses deterministic in-memory canonical repositories and fixture-run artifact storage behind VeraCrawl ports while preserving target contracts and owner boundaries for later browser, graph, memory, export, scale, and operations profiles.

## Technical Context

**Language/Version**: Python 3.11+; local validation may use Python 3.12.  
**Primary Dependencies**: Existing foundation dependencies: Pydantic v2 for contracts, standard-library `typing.Protocol` for ports, pytest, ruff, and mypy. No concrete agent framework, browser library, storage client, queue client, model SDK, or website-specific scraper module is a core dependency.  
**Storage**: Deterministic in-memory canonical repositories and fixture-run artifact storage behind VeraCrawl-owned ports. Production database, queue, object store, browser, model provider, and export adapters remain out of scope for this feature.  
**Testing**: pytest contract, unit, integration, replay, policy, fixture/oracle, import-boundary, and deterministic objective-to-output runtime tests.  
**Target Platform**: Python package and CLI/runtime tests runnable on local developer machines and CI. Production deployment topology remains adapter-defined in later specs.  
**Project Type**: Python library plus developer CLI/test harness for deterministic runtime-spine fixtures and replay validation.  
**Performance Goals**: Local runtime-spine gate should remain within the foundation envelope of 30 seconds, or emit a timing report explaining fixture complexity and why the timing is not a regression. Successful fixture replay must report zero missing required refs.  
**Constraints**: Runtime core must not import concrete adapters, agent frameworks, browser libraries, storage clients, queue clients, model SDKs, or site-specific scraper modules. Every mutating or publication-relevant path must flow through `CommandEnvelope`, owner service validation, `CommandResult`, policy gates, typed events, and replay refs. Non-fetch adapters must not fake fetch/page snapshot semantics.  
**Scale/Scope**: One deterministic successful record-output objective-to-output fixture plus mandatory negative fixtures for blocked source, missing evidence, verification conflict, adapter mismatch, replay gap, direct cross-owner mutation, and forbidden framework/core import. Table, document, file, dataset, fact, full browser, graph, memory, export, distributed queue, autoscaling, and DR profiles remain not target-complete.  
**VeraCrawl Owner Services**: `control`, `fetch`, `normalize`, `extract`, `evidence`, `verify`, `publish`, `runtime_events`, `policy`, `ports`, `agents`, `review_replay`, `artifact_lifecycle`, and `ops` are directly affected. `browser`, `scheduler`, `projection`, `graph`, `memory`, and `export` retain compatibility refs and boundaries only.  
**Canonical Contracts**: CrawlObjective, CrawlPlan, CrawlRun, RunPlanSnapshot, RuntimeCompletionGate, RuntimeArtifactRef, NormalizedDocument, ExtractionCandidate, EvidencePacket, VerificationDecision, PublishedOutput, OutputManifest, ReplayBundleManifest, SourceAdapterCommand, SourceAdapterResult, PolicyDecision, CommandEnvelope, CommandResult, CrawlRunEvent, AgentActionTrace, ToolCallTrace, ModelCallTrace, ContextBundleTrace.  
**Replay/Artifact Impact**: Runtime replay requires command result refs, event cursor refs, source adapter result refs, artifact hashes, normalized document refs, candidate refs, evidence packet refs, verification decision refs, output manifest refs, policy decision refs, optional agent/model/tool/context trace refs, deterministic clock/randomness refs, and redaction map refs.  
**Security/Policy Impact**: Source scope, robots/terms/customer authorization, adapter execution, credential/session use, prompt context, publication, artifact lifecycle, retention, recovery, and forbidden dependency/import boundaries must emit typed allow, deny, require-review, blocked, conflict, failed, or replay-incomplete outcomes.

## Constitution Check

*GATE: Passed before Phase 0 research. Re-checked after Phase 1 design.*

- [x] General-purpose AI agent crawler capability is preserved; no one-off scraper assumptions are introduced.
- [x] Python remains the implementation language unless a constitution amendment changes it.
- [x] Agent runtime remains framework-neutral; model SDKs and agent frameworks are isolated behind replaceable adapters.
- [x] Low coupling/high cohesion boundaries are explicit through ports, commands, events, typed results, and owner services.
- [x] Evidence, verification, publication, replay, and artifact lineage are defined for affected outputs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and export/withdrawal gates are defined where applicable.
- [x] Command payload schemas, event payload schemas, state transitions, fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

### Documentation (this feature)

```text
specs/002-core-runtime-spine/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── runtime-spine.md
│   ├── owner-command-event.md
│   ├── replay-publication.md
│   ├── fixture-oracle.md
│   └── agent-recommendation.md
└── tasks.md              # Created by $speckit-tasks, not by $speckit-plan
```

### Source Code (repository root)

```text
src/
└── veracrawl/
    ├── contracts/
    │   ├── objective.py          # CrawlObjective, CrawlPlan, CrawlRun, RunPlanSnapshot
    │   ├── artifact.py           # RuntimeArtifactRef and lifecycle/privacy refs
    │   ├── processing.py         # NormalizedDocument, ExtractionCandidate
    │   ├── evidence.py           # EvidencePacket and coverage results
    │   ├── verification.py       # VerificationDecision and conflict state
    │   ├── publication.py        # PublishedOutput and OutputManifest
    │   └── registry.py           # Runtime contract/command/event registrations
    ├── control/
    │   └── runtime.py            # Objective, plan, run, gate orchestration
    ├── fetch/
    │   └── runtime.py            # Source adapter execution service boundary
    ├── normalize/
    │   └── runtime.py            # Artifact-to-normalized document boundary
    ├── extract/
    │   └── runtime.py            # Candidate creation boundary
    ├── evidence/
    │   └── runtime.py            # Evidence packet builder boundary
    ├── verify/
    │   └── runtime.py            # Verification decision boundary
    ├── publish/
    │   └── runtime.py            # Publication/output manifest boundary
    ├── review_replay/
    │   └── runtime.py            # Runtime replay bundle builder
    ├── runtime_events/
    │   └── replay.py             # Extended runtime replay completeness
    ├── ports/
    │   ├── runtime_repository.py # Canonical repository protocols
    │   └── artifact_store.py     # Fixture artifact store protocol
    ├── runtime_support/
    │   ├── __init__.py
    │   └── repositories.py       # In-memory repository profile behind ports
    ├── agents/
    │   └── recommendations.py    # Framework-neutral recommendation intake
    └── cli/
        └── runtime.py            # Deterministic fixture runner entry point if needed

tests/
├── contract/
│   ├── test_runtime_contract_registry.py
│   ├── test_runtime_command_event_contracts.py
│   ├── test_runtime_import_boundaries.py
│   └── test_agent_recommendation_contracts.py
├── unit/
│   ├── test_runtime_completion_gates.py
│   ├── test_evidence_publication_gates.py
│   └── test_runtime_replay_validation.py
├── integration/
│   ├── test_objective_to_output_runtime.py
│   └── test_runtime_negative_fixtures.py
└── fixtures/
    ├── runtime-record-success/
    ├── runtime-blocked-source/
    ├── runtime-missing-evidence/
    ├── runtime-verification-conflict/
    ├── runtime-adapter-mismatch/
    ├── runtime-replay-gap/
    └── runtime-boundary-violation/
```

**Structure Decision**: Extend the existing single Python `src/` package. Each owner service gets a cohesive runtime boundary module, but shared durable behavior remains represented by contracts, commands, events, policy decisions, and ports. The deterministic in-memory repository profile lives in `veracrawl.runtime_support` behind repository ports so it does not collapse owner responsibilities into `control`. Concrete infrastructure and framework integrations stay under adapters or test fixtures and must never be imported by runtime core packages.

## Phase 0: Research

Phase 0 decisions are captured in [research.md](research.md). The core choices are:

- Use an in-memory canonical repository profile behind ports for the first runtime spine.
- Use fixture-run artifact storage with content hashes and lifecycle/privacy metadata.
- Use a deterministic record-output success fixture as the first objective-to-output proof.
- Track completion as independent gates rather than a single run status.
- Keep agent framework participation optional for the success path and prove framework neutrality with separate conformance fixtures.

## Phase 1: Design And Contracts

Phase 1 design artifacts are:

- [data-model.md](data-model.md): runtime entities, relationships, validation rules, owner services, completion gates, and state transitions.
- [contracts/runtime-spine.md](contracts/runtime-spine.md): objective-to-output runtime contract and fixture runner behavior.
- [contracts/owner-command-event.md](contracts/owner-command-event.md): command/event/owner mutation rules and rejection behavior.
- [contracts/replay-publication.md](contracts/replay-publication.md): evidence, verification, publication, output manifest, and replay completeness contract.
- [contracts/fixture-oracle.md](contracts/fixture-oracle.md): success and negative runtime fixture/oracle requirements.
- [contracts/agent-recommendation.md](contracts/agent-recommendation.md): framework-neutral agent recommendation intake contract.
- [quickstart.md](quickstart.md): expected developer flow and verification commands for the implementation tasks.

## Post-Design Constitution Check

- [x] Design artifacts preserve the target core runtime spine and do not reduce scope for schedule or staffing reasons.
- [x] The first success fixture is deterministic but not single-site or framework-coupled.
- [x] Core runtime depends on VeraCrawl contracts, ports, commands, events, policy, and replay only.
- [x] Evidence, verification, publication, output manifest, and replay gates are blocking before successful publication.
- [x] Negative fixture/oracle coverage is defined before implementation.
- [x] No constitution violation or justified complexity exception is present.

## Complexity Tracking

No constitution violations are introduced. No complexity exception is required.
