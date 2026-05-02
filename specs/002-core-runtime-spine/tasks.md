# Tasks: VeraCrawl Target Core Runtime Spine

**Input**: Design documents from `/specs/002-core-runtime-spine/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required. This feature implements runtime, owner mutations, publication gates, replay, policy, fixtures, and import boundaries. Contract, unit, integration, replay, fixture/oracle, negative, and boundary tests must be written before implementation tasks.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently after the shared runtime foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks.
- **[Story]**: User story label for story phases only.
- Each task includes exact file paths.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare runtime-spine CLI, package, fixture, and test locations without changing behavior.

- [X] T001 Add `veracrawl-runtime` console script target and keep existing lint/mypy/pytest configuration in `pyproject.toml`
- [X] T002 [P] Create runtime CLI module marker and placeholder entry point in `src/veracrawl/cli/runtime.py`
- [X] T003 [P] Create runtime repository port module in `src/veracrawl/ports/runtime_repository.py`
- [X] T004 [P] Create artifact store port module in `src/veracrawl/ports/artifact_store.py`
- [X] T005 [P] Create neutral runtime support package marker in `src/veracrawl/runtime_support/__init__.py`
- [X] T006 [P] Create runtime test fixture package helpers in `tests/helpers/runtime_fixture_assertions.py`
- [X] T007 [P] Create runtime fixture directories and README placeholders in `tests/fixtures/runtime-record-success/README.md`, `tests/fixtures/runtime-blocked-source/README.md`, `tests/fixtures/runtime-missing-evidence/README.md`, `tests/fixtures/runtime-verification-conflict/README.md`, `tests/fixtures/runtime-adapter-mismatch/README.md`, `tests/fixtures/runtime-replay-gap/README.md`, and `tests/fixtures/runtime-boundary-violation/README.md`
- [X] T008 [P] Create runtime contract test file placeholders in `tests/contract/test_runtime_contract_registry.py`, `tests/contract/test_runtime_command_event_contracts.py`, `tests/contract/test_runtime_import_boundaries.py`, and `tests/contract/test_agent_recommendation_contracts.py`
- [X] T009 [P] Create runtime unit test file placeholders in `tests/unit/test_runtime_completion_gates.py`, `tests/unit/test_evidence_publication_gates.py`, and `tests/unit/test_runtime_replay_validation.py`
- [X] T010 [P] Create runtime integration test file placeholders in `tests/integration/test_objective_to_output_runtime.py` and `tests/integration/test_runtime_negative_fixtures.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define shared runtime contracts, ports, stores, and registry surfaces that all user stories depend on.

**Critical**: No user story implementation starts until this phase is complete.

### Foundational Tests

- [X] T011 [P] Write runtime contract registry completeness tests for contracts, owners, command types, event types, policy gates, replay refs, fixture refs, and test refs in `tests/contract/test_runtime_contract_registry.py`
- [X] T012 [P] Write runtime entity validation tests for objective, plan, run, plan snapshot, artifact, normalized document, candidate, evidence, verification, publication, output manifest, replay bundle, and gate models in `tests/contract/test_runtime_command_event_contracts.py`
- [X] T013 [P] Write runtime completion gate unit tests for independent objective, plan, source, normalization, extraction, evidence, verification, publication, and replay gates in `tests/unit/test_runtime_completion_gates.py`
- [X] T014 [P] Write runtime import-boundary tests that reject direct imports of concrete agent frameworks, browser libraries, storage clients, queue clients, model SDKs, and site-specific scraper modules from core runtime packages in `tests/contract/test_runtime_import_boundaries.py`

### Foundational Implementation

- [X] T015 [P] Implement CrawlObjective, CrawlPlan, CrawlRun, RunPlanSnapshot, RuntimeCompletionGate, lifecycle enums, and validation rules in `src/veracrawl/contracts/objective.py`
- [X] T016 [P] Implement RuntimeArtifactRef, artifact type enums, privacy classification refs, lifecycle refs, and content hash validation in `src/veracrawl/contracts/artifact.py`
- [X] T017 [P] Implement NormalizedDocument and ExtractionCandidate contracts with anchor, schema, confidence, strategy, and agent recommendation refs in `src/veracrawl/contracts/processing.py`
- [X] T018 [P] Implement EvidencePacket and evidence coverage contracts with source-evidence-only publication validation in `src/veracrawl/contracts/evidence.py`
- [X] T019 [P] Implement VerificationDecision and conflict state contracts in `src/veracrawl/contracts/verification.py`
- [X] T020 [P] Implement PublishedOutput and OutputManifest contracts with immutable manifest hash and evidence/verification refs in `src/veracrawl/contracts/publication.py`
- [X] T021 Implement runtime repository protocols for objective, plan, run, source result, artifact, normalized document, candidate, evidence, verification, publication, replay, and gate repositories in `src/veracrawl/ports/runtime_repository.py`
- [X] T022 Implement artifact store protocol for deterministic fixture-run artifact storage in `src/veracrawl/ports/artifact_store.py`
- [X] T023 Implement runtime completion gate evaluator primitives in `src/veracrawl/control/runtime.py`
- [X] T024 Extend contract exports for runtime models in `src/veracrawl/contracts/__init__.py`
- [X] T025 Extend registry registrations for runtime contracts, command types, event types, source fixture refs, completion gate coverage, and owner mappings in `src/veracrawl/contracts/registry.py`
- [X] T026 Run foundational validation commands for runtime registry, entity validation, completion gates, and import boundaries from `specs/002-core-runtime-spine/quickstart.md`

**Checkpoint**: Shared runtime contracts, ports, registry entries, and boundary tests are ready.

---

## Phase 3: User Story 1 - Run Objective To Published Output (Priority: P1)

**Goal**: Execute a deterministic record-output runtime fixture from approved objective to published output manifest and replay-complete bundle.

**Independent Test**: `veracrawl-runtime run tests/fixtures/runtime-record-success --profile target --out .veracrawl-test-runs/runtime-record-success`, `pytest tests/integration/test_objective_to_output_runtime.py`, and replay validation prove every required output field has source-backed evidence and zero missing replay refs.

### Tests for User Story 1

- [X] T027 [P] [US1] Write objective-to-output integration test for successful record fixture in `tests/integration/test_objective_to_output_runtime.py`
- [X] T028 [P] [US1] Write replay success tests for command result refs, event cursors, source adapter result refs, artifact hashes, normalized refs, candidate refs, evidence refs, verification refs, output manifest refs, policy refs, and redaction refs in `tests/unit/test_runtime_replay_validation.py`
- [X] T029 [P] [US1] Write evidence/publication success gate tests for field-level evidence coverage and accepted verification in `tests/unit/test_evidence_publication_gates.py`
- [X] T030 [P] [US1] Create success fixture manifest, expected command/event/policy/source/artifact/normalized/candidate/evidence/verification/output/replay/gate oracles, and artifact expectations under `tests/fixtures/runtime-record-success/`
- [X] T031 [P] [US1] Write CLI integration test for `veracrawl-runtime run tests/fixtures/runtime-record-success --profile target --out .veracrawl-test-runs/runtime-record-success` in `tests/integration/test_objective_to_output_runtime.py`

### Implementation for User Story 1

- [X] T032 [P] [US1] Implement deterministic in-memory runtime repositories behind ports in `src/veracrawl/runtime_support/repositories.py`
- [X] T033 [P] [US1] Implement deterministic fixture artifact store in `src/veracrawl/artifact_lifecycle/runtime.py`
- [X] T034 [US1] Implement objective creation, plan approval, run start, plan snapshot creation, and gate initialization in `src/veracrawl/control/runtime.py`
- [X] T035 [US1] Implement fetch-like source adapter execution boundary that records SourceAdapterResult and raw artifact refs in `src/veracrawl/fetch/runtime.py`
- [X] T036 [US1] Implement raw artifact to NormalizedDocument transformation with anchor map refs in `src/veracrawl/normalize/runtime.py`
- [X] T037 [US1] Implement schema-bound ExtractionCandidate creation from normalized anchors in `src/veracrawl/extract/runtime.py`
- [X] T038 [US1] Implement EvidencePacket builder and coverage result generation in `src/veracrawl/evidence/runtime.py`
- [X] T039 [US1] Implement VerificationDecision accept path with evidence and policy validation in `src/veracrawl/verify/runtime.py`
- [X] T040 [US1] Implement PublishedOutput and OutputManifest creation with immutable manifest hash in `src/veracrawl/publish/runtime.py`
- [X] T041 [US1] Implement ReplayBundleManifest builder for runtime spine refs in `src/veracrawl/review_replay/runtime.py`
- [X] T042 [US1] Extend replay completeness validation for runtime refs and publication refs in `src/veracrawl/runtime_events/replay.py`
- [X] T043 [US1] Implement `veracrawl-runtime run` CLI fixture runner and JSON report writer in `src/veracrawl/cli/runtime.py`
- [X] T044 [US1] Register runtime-record-success fixture/oracle entry in `src/veracrawl/contracts/registry.py`
- [X] T045 [US1] Run and satisfy US1 validation commands from `specs/002-core-runtime-spine/quickstart.md`

**Checkpoint**: User Story 1 is independently functional and proves the target core runtime spine happy path without claiming full target crawler completion.

---

## Phase 4: User Story 2 - Execute Source And Processing Through Owner Boundaries (Priority: P2)

**Goal**: Prove source adapter and processing mutations flow through owner service command/event boundaries and reject wrong-owner mutation.

**Independent Test**: `pytest tests/contract/test_runtime_command_event_contracts.py`, `pytest tests/contract/test_runtime_import_boundaries.py`, and runtime-boundary fixture tests prove owner validation, command/event emission, natural adapter semantics, and dependency boundaries.

### Tests for User Story 2

- [X] T046 [P] [US2] Write owner command/event contract tests for objective, plan, run, source adapter result, normalized document, candidate, evidence, verification, publication, and replay mutations in `tests/contract/test_runtime_command_event_contracts.py`
- [X] T047 [P] [US2] Write wrong-owner mutation rejection tests in `tests/contract/test_runtime_command_event_contracts.py`
- [X] T048 [P] [US2] Write fetch-like and non-fetch source adapter natural semantics tests for runtime execution in `tests/contract/test_runtime_command_event_contracts.py`
- [X] T049 [P] [US2] Write runtime boundary violation fixture/oracle data under `tests/fixtures/runtime-boundary-violation/`
- [X] T050 [P] [US2] Extend runtime import-boundary tests with source-processing owner modules in `tests/contract/test_runtime_import_boundaries.py`

### Implementation for User Story 2

- [X] T051 [US2] Implement owner command dispatcher and expected-owner validation helpers in `src/veracrawl/control/runtime.py`
- [X] T052 [US2] Implement command result creation and rejection reason mapping for runtime owner mutations in `src/veracrawl/control/runtime.py`
- [X] T053 [US2] Implement runtime event emission helpers for command, plan, processing, source adapter, evidence, verification, publication, replay, and error events in `src/veracrawl/runtime_events/event_store.py`
- [X] T054 [US2] Extend source adapter execution boundary to preserve natural fetch-like and non-fetch result semantics in `src/veracrawl/fetch/runtime.py`
- [X] T055 [US2] Implement processing owner boundary checks for normalize, extract, evidence, verify, and publish services in `src/veracrawl/normalize/runtime.py`, `src/veracrawl/extract/runtime.py`, `src/veracrawl/evidence/runtime.py`, `src/veracrawl/verify/runtime.py`, and `src/veracrawl/publish/runtime.py`
- [X] T056 [US2] Register owner command/event runtime taxonomy and wrong-owner negative fixture in `src/veracrawl/contracts/registry.py`
- [X] T057 [US2] Run and satisfy US2 validation commands from `specs/002-core-runtime-spine/quickstart.md`

**Checkpoint**: User Story 2 is independently functional and owner boundaries cannot be bypassed by adapters, agents, fixtures, or runtime helpers.

---

## Phase 5: User Story 3 - Block Unsafe Or Incomplete Publication (Priority: P3)

**Goal**: Prevent publication when policy, evidence, verification, replay, privacy lifecycle, or adapter validity gates fail.

**Independent Test**: Negative runtime fixtures for blocked source, missing evidence, verification conflict, adapter mismatch, replay gap, and boundary violation produce typed non-success outcomes and no successful publication.

### Tests for User Story 3

- [X] T058 [P] [US3] Write blocked-source negative runtime fixture and oracle data under `tests/fixtures/runtime-blocked-source/`
- [X] T059 [P] [US3] Write missing-evidence negative runtime fixture and oracle data under `tests/fixtures/runtime-missing-evidence/`
- [X] T060 [P] [US3] Write verification-conflict negative runtime fixture and oracle data under `tests/fixtures/runtime-verification-conflict/`
- [X] T061 [P] [US3] Write adapter-mismatch negative runtime fixture and oracle data under `tests/fixtures/runtime-adapter-mismatch/`
- [X] T062 [P] [US3] Write replay-gap negative runtime fixture and oracle data under `tests/fixtures/runtime-replay-gap/`
- [X] T063 [P] [US3] Write negative fixture runner integration tests for blocked, missing evidence, conflict, adapter mismatch, replay gap, and boundary violation in `tests/integration/test_runtime_negative_fixtures.py`
- [X] T064 [P] [US3] Write publication gate unit tests for missing evidence, rejected verification, conflict, policy deny, missing replay refs, and blocked lifecycle refs in `tests/unit/test_evidence_publication_gates.py`
- [X] T065 [P] [US3] Write replay failure and needs-review tests for missing runtime refs in `tests/unit/test_runtime_replay_validation.py`

### Implementation for User Story 3

- [X] T066 [US3] Extend policy gates for runtime source, evidence, verification, publication, artifact lifecycle, retention, recovery, and prompt context subjects in `src/veracrawl/policy/gates.py`
- [X] T067 [US3] Implement blocked-source runtime handling with SourceAdapterResult blocked status and operator-visible diagnostics in `src/veracrawl/fetch/runtime.py`
- [X] T068 [US3] Implement evidence gate failure and needs-review outcomes in `src/veracrawl/evidence/runtime.py`
- [X] T069 [US3] Implement verification conflict and reject outcomes that prevent publication in `src/veracrawl/verify/runtime.py`
- [X] T070 [US3] Implement publication precondition checks for evidence, verification, policy, lifecycle, and replay completeness in `src/veracrawl/publish/runtime.py`
- [X] T071 [US3] Implement replay gap reporting for runtime bundle missing refs in `src/veracrawl/review_replay/runtime.py`
- [X] T072 [US3] Extend `veracrawl-runtime run` to emit typed negative outcomes and run reports for all negative fixtures in `src/veracrawl/cli/runtime.py`
- [X] T073 [US3] Register negative runtime fixture/oracle entries in `src/veracrawl/contracts/registry.py`
- [X] T074 [US3] Run and satisfy US3 validation commands from `specs/002-core-runtime-spine/quickstart.md`

**Checkpoint**: User Story 3 is independently functional and unsafe or incomplete runtime paths cannot falsely publish.

---

## Phase 6: User Story 4 - Use Framework-Neutral Agents Without Core Coupling (Priority: P4)

**Goal**: Allow agent recommendations to enter the runtime through VeraCrawl contracts and owner-service commands while external frameworks remain replaceable adapters.

**Independent Test**: Agent recommendation conformance tests prove recommendations can contribute plan, extraction, verification, or repair proposals without direct mutation or framework-native canonical state.

### Tests for User Story 4

- [X] T075 [P] [US4] Write agent recommendation contract tests for recommendation subjects, trace refs, context bundle refs, policy refs, and owner-command conversion in `tests/contract/test_agent_recommendation_contracts.py`
- [X] T076 [P] [US4] Write framework adapter swap conformance test proving canonical runtime state remains unchanged across OpenAI Agent SDK and LangGraph-style recommendation fixtures in `tests/contract/test_agent_recommendation_contracts.py`
- [X] T077 [P] [US4] Write negative tests for raw secret context, untainted page text, policy-denied prompt context, cross-owner mutation, and framework-native canonical state in `tests/contract/test_agent_recommendation_contracts.py`

### Implementation for User Story 4

- [X] T078 [P] [US4] Implement AgentRecommendation contract models and enums in `src/veracrawl/contracts/agent.py`
- [X] T079 [US4] Implement framework-neutral agent recommendation intake, validation, rejection, and owner-command conversion in `src/veracrawl/agents/recommendations.py`
- [X] T080 [US4] Extend tool gateway validation so accepted recommendations become CommandEnvelope instances without direct durable mutation in `src/veracrawl/agents/tool_gateway.py`
- [X] T081 [US4] Extend OpenAI Agent SDK and LangGraph conformance stub adapters to emit runtime recommendation fixtures in `src/veracrawl/adapters/agent_frameworks/openai_agent_sdk.py` and `src/veracrawl/adapters/agent_frameworks/langgraph.py`
- [X] T082 [US4] Register agent recommendation runtime contracts and conformance fixtures in `src/veracrawl/contracts/registry.py`
- [X] T083 [US4] Run and satisfy US4 validation commands from `specs/002-core-runtime-spine/quickstart.md`

**Checkpoint**: User Story 4 is independently functional and agent frameworks cannot own canonical runtime state.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Verify consistency across the full runtime spine and prepare for implementation workflow.

- [X] T084 [P] Update package usage notes for runtime-spine validation and fixture execution in `README.md`
- [X] T085 [P] Update target implementation notes for runtime spine package map and non-completion boundaries in `docs/10-target-implementation-design.md`
- [X] T086 [P] Update target testing notes for runtime-spine fixtures and gates in `docs/11-target-testing-and-acceptance.md`
- [X] T087 Run ruff, mypy, and pytest full runtime-spine gate with a 30-second local timing check from `specs/002-core-runtime-spine/quickstart.md`
- [X] T088 Run Spec Kit consistency checks with `$speckit-analyze` and record any required follow-up in `specs/002-core-runtime-spine/tasks.md`
- [X] T089 Verify every task ID maps to a contract, owner service, command/event, fixture/oracle, or verification check in `specs/002-core-runtime-spine/tasks.md`
- [X] T090 Confirm no code, docs, tests, CLI output, or task text claims full target crawler completion, full browser capability, full graph/memory capability, full export capability, or production scale readiness in `specs/002-core-runtime-spine/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1 and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Phase 2 and proves the deterministic objective-to-output spine.
- **User Story 2 (Phase 4)**: Depends on Phase 2 and can proceed after US1 contracts exist; final integration depends on runtime command/event helpers from US1.
- **User Story 3 (Phase 5)**: Depends on Phase 2 and can proceed after US1 publication/replay contracts exist; final negative fixture behavior depends on US1/US2 runtime paths.
- **User Story 4 (Phase 6)**: Depends on Phase 2 and can proceed after runtime command/event boundaries are available.
- **Polish (Phase 7)**: Depends on selected user stories being complete.

### User Story Dependencies

- **US1 - Run Objective To Published Output**: First executable spine and required before claiming runtime-spine implementation.
- **US2 - Execute Source And Processing Through Owner Boundaries**: Strengthens owner mutation enforcement and must pass before adding richer source profiles.
- **US3 - Block Unsafe Or Incomplete Publication**: Must pass before any runtime publication success can be trusted.
- **US4 - Use Framework-Neutral Agents Without Core Coupling**: Must pass before agent-driven runtime work can claim framework-neutral integration.

### Within Each User Story

- Tests must be written first and fail before implementation.
- Contract models must exist before registry population.
- Owner service boundaries must exist before runtime orchestration.
- Fixture manifests and oracles must exist before fixture runner acceptance can pass.
- Replay and publication gates must pass before publication-complete can be claimed.

## Parallel Opportunities

- Setup tasks T002-T010 can run in parallel after T001.
- Foundational tests T011-T014 can run in parallel.
- Foundational models T015-T020 can run in parallel before exports and registry work.
- US1 tests T027-T031 can run in parallel.
- US1 owner runtime service modules T032-T041 can be developed in parallel after contracts and ports exist, then integrated through T043-T045.
- US2 tests T046-T050 can run in parallel.
- US3 fixture tasks T058-T062 can run in parallel with US3 unit tests T064-T065.
- US4 tests T075-T077 can run in parallel before recommendation implementation.
- Polish docs T084-T086 can run in parallel after user stories are stable.

## Parallel Example: User Story 1

```text
Task: "T027 [P] [US1] Write objective-to-output integration test in tests/integration/test_objective_to_output_runtime.py"
Task: "T028 [P] [US1] Write replay success tests in tests/unit/test_runtime_replay_validation.py"
Task: "T029 [P] [US1] Write evidence/publication success gate tests in tests/unit/test_evidence_publication_gates.py"
Task: "T030 [P] [US1] Create success fixture under tests/fixtures/runtime-record-success/"
Task: "T035 [US1] Implement source adapter execution boundary in src/veracrawl/fetch/runtime.py"
Task: "T036 [US1] Implement normalization boundary in src/veracrawl/normalize/runtime.py"
Task: "T037 [US1] Implement extraction boundary in src/veracrawl/extract/runtime.py"
```

## Parallel Example: User Story 2

```text
Task: "T046 [P] [US2] Write owner command/event contract tests in tests/contract/test_runtime_command_event_contracts.py"
Task: "T049 [P] [US2] Write boundary violation fixture under tests/fixtures/runtime-boundary-violation/"
Task: "T050 [P] [US2] Extend runtime import-boundary tests in tests/contract/test_runtime_import_boundaries.py"
Task: "T054 [US2] Extend source adapter natural semantics in src/veracrawl/fetch/runtime.py"
Task: "T055 [US2] Implement processing owner boundary checks across normalize/extract/evidence/verify/publish runtime modules"
```

## Implementation Verification Record

- 2026-05-02: Re-ran Spec Kit prerequisite check with `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`; feature dir and required docs resolved.
- 2026-05-02: Re-ran cross-artifact consistency checks equivalent to `$speckit-analyze`: 20 functional requirements, 9 success criteria, T001-T090 contiguous, no placeholders, and runtime contract, owner command/event, fixture, agent abstraction, replay/publication, and import-boundary coverage present.
- 2026-05-02: Verified `veracrawl-contracts validate --format json` reports no registry errors.
- 2026-05-02: Verified `veracrawl-runtime run tests/fixtures/runtime-record-success --profile target --out .veracrawl-test-runs/runtime-record-success` publishes with replay pass.
- 2026-05-02: Verified negative runtime fixtures for blocked source, missing evidence, verification conflict, adapter mismatch, replay gap, and boundary violation all produce typed non-published outcomes.
- 2026-05-02: Verified full runtime-spine gate: `ruff check src tests`, `mypy src`, and `pytest tests/contract tests/unit tests/integration` pass within the 30-second target.
- 2026-05-02: Confirmed no task text claims full target crawler completion, full browser capability, full graph/memory capability, full export capability, or production scale readiness.

## Parallel Example: User Story 3

```text
Task: "T058 [P] [US3] Write blocked-source fixture under tests/fixtures/runtime-blocked-source/"
Task: "T059 [P] [US3] Write missing-evidence fixture under tests/fixtures/runtime-missing-evidence/"
Task: "T060 [P] [US3] Write verification-conflict fixture under tests/fixtures/runtime-verification-conflict/"
Task: "T064 [P] [US3] Write publication gate unit tests in tests/unit/test_evidence_publication_gates.py"
Task: "T065 [P] [US3] Write replay failure tests in tests/unit/test_runtime_replay_validation.py"
```

## Parallel Example: User Story 4

```text
Task: "T075 [P] [US4] Write recommendation contract tests in tests/contract/test_agent_recommendation_contracts.py"
Task: "T076 [P] [US4] Write framework adapter swap conformance test in tests/contract/test_agent_recommendation_contracts.py"
Task: "T078 [P] [US4] Implement AgentRecommendation contracts in src/veracrawl/contracts/agent.py"
Task: "T079 [US4] Implement recommendation intake in src/veracrawl/agents/recommendations.py"
```

## Implementation Strategy

### First Runtime Spine

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational runtime contracts, ports, gates, and registry entries.
3. Complete Phase 3 User Story 1.
4. Validate with the runtime-record-success fixture and replay-complete bundle.

### Incremental Delivery

1. Add US1 to prove the deterministic objective-to-output happy path.
2. Add US2 to enforce owner boundaries and natural adapter semantics.
3. Add US3 to prove unsafe or incomplete paths cannot publish.
4. Add US4 to prove framework-neutral agent recommendation intake.
5. Run the full runtime-spine gate from [quickstart.md](quickstart.md).

### Non-Deceptive Completion Rule

This task list completes the target core runtime spine only. It must not be used to claim full target crawler completion, full browser execution, graph intelligence, memory intelligence, export connector, distributed queue scale, autoscaling, disaster recovery, or production operations readiness.
