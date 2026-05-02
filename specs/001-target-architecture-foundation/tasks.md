# Tasks: VeraCrawl Target Architecture Foundation

**Input**: Design documents from `/specs/001-target-architecture-foundation/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required. This feature changes architecture, contracts, policy, replay, adapters, and fixture/oracle behavior, so contract, unit, integration, negative, replay, fixture/oracle, and import-boundary tests must be written before implementation tasks.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently after the shared foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks.
- **[Story]**: User story label for story phases only.
- Each task includes exact file paths.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the Python project skeleton and developer tooling.

- [X] T001 Create Python package configuration with project metadata, Python 3.11+ requirement, dependencies, console scripts, ruff config, mypy config, and pytest config in `pyproject.toml`
- [X] T002 Create root package marker and public version export in `src/veracrawl/__init__.py`
- [X] T003 [P] Create CLI package marker in `src/veracrawl/cli/__init__.py`
- [X] T004 [P] Create contracts package marker in `src/veracrawl/contracts/__init__.py`
- [X] T005 [P] Create ports package marker in `src/veracrawl/ports/__init__.py`
- [X] T006 [P] Create runtime events package marker in `src/veracrawl/runtime_events/__init__.py`
- [X] T007 [P] Create policy package marker in `src/veracrawl/policy/__init__.py`
- [X] T008 [P] Create agents package marker in `src/veracrawl/agents/__init__.py`
- [X] T009 [P] Create adapters package markers in `src/veracrawl/adapters/__init__.py`, `src/veracrawl/adapters/agent_frameworks/__init__.py`, and `src/veracrawl/adapters/sources/__init__.py`
- [X] T010 Create domain package markers for target owner services in `src/veracrawl/control/__init__.py`, `src/veracrawl/scheduler/__init__.py`, `src/veracrawl/fetch/__init__.py`, `src/veracrawl/browser/__init__.py`, `src/veracrawl/normalize/__init__.py`, `src/veracrawl/extract/__init__.py`, `src/veracrawl/evidence/__init__.py`, `src/veracrawl/verify/__init__.py`, `src/veracrawl/publish/__init__.py`, `src/veracrawl/artifact_lifecycle/__init__.py`, `src/veracrawl/projection/__init__.py`, `src/veracrawl/graph/__init__.py`, `src/veracrawl/memory/__init__.py`, `src/veracrawl/review_replay/__init__.py`, `src/veracrawl/export/__init__.py`, and `src/veracrawl/ops/__init__.py`
- [X] T011 Create test package skeleton markers in `tests/__init__.py`, `tests/contract/__init__.py`, `tests/unit/__init__.py`, and `tests/integration/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish primitives, error types, and test helpers that every user story depends on.

**Critical**: No user story work starts until this phase is complete.

- [X] T012 Implement shared contract base types, stable ref aliases, UTC timestamp validation, canonical JSON serialization, and hash helpers in `src/veracrawl/contracts/common.py`
- [X] T013 [P] Implement shared enum definitions for owner services, command status, result status, policy decisions, adapter types, result types, agent roles, replay modes, and fixture comparison modes in `src/veracrawl/contracts/enums.py`
- [X] T014 [P] Implement project exception hierarchy for validation, registry, policy, replay, fixture, adapter, and boundary failures in `src/veracrawl/contracts/errors.py`
- [X] T015 Implement deterministic clock and randomness ports plus test implementations in `src/veracrawl/ports/clock.py`
- [X] T016 [P] Implement base storage, artifact, event store, and repository port protocols without concrete infrastructure imports in `src/veracrawl/ports/stores.py`
- [X] T017 [P] Create reusable pytest factories for contract refs, timestamps, command IDs, event IDs, policy decisions, and replay refs in `tests/factories.py`
- [X] T018 Create import-boundary scanning helper for core-versus-adapter dependency tests in `tests/helpers/import_boundary.py`
- [X] T019 Create canonical fixture assertion helpers for JSON serialization, required refs, and missing oracle detection in `tests/helpers/fixture_assertions.py`

**Checkpoint**: Shared primitives are ready and story work can start.

---

## Phase 3: User Story 1 - Establish Foundation Contracts (Priority: P1)

**Goal**: Provide a coherent foundation of canonical contracts, owner boundaries, command/event/replay model, and acceptance gates.

**Independent Test**: `veracrawl-contracts validate --format json`, `pytest tests/contract/test_contract_registry.py`, and `pytest tests/contract/test_command_event_replay_contracts.py` prove every affected foundation contract has an owner service, payload schema, event path, replay requirement, state transition, and negative test.

### Tests for User Story 1

- [X] T020 [P] [US1] Write contract registry completeness tests for foundation contracts, target contract area coverage rows, owner services, schema refs, replay flags, and test refs in `tests/contract/test_contract_registry.py`
- [X] T021 [P] [US1] Write command envelope, command result, command type, and payload schema validation tests in `tests/contract/test_command_event_replay_contracts.py`
- [X] T022 [P] [US1] Write CrawlRunEvent append ordering, event schema mapping, replay-critical refs, and state transition tests in `tests/contract/test_command_event_replay_contracts.py`
- [X] T023 [P] [US1] Write cross-owner mutation rejection tests for command ownership rules in `tests/contract/test_contract_registry.py`
- [X] T024 [P] [US1] Write core import-boundary tests that reject direct adapter, framework, browser, storage, and queue imports from core packages in `tests/contract/test_import_boundaries.py`
- [X] T025 [P] [US1] Write CLI validation test for `veracrawl-contracts validate --format json` in `tests/integration/test_contracts_cli.py`

### Implementation for User Story 1

- [X] T026 [P] [US1] Implement CommandEnvelope, CommandResult, CommandTypeSpec, and BaseCommandPayload models with state transition validation in `src/veracrawl/contracts/command.py`
- [X] T027 [P] [US1] Implement CrawlRunEvent, EventTypeSpec, event cursor refs, event payload refs, and replay-critical ref validation in `src/veracrawl/contracts/event.py`
- [X] T028 [P] [US1] Implement PolicyDecision model and policy decision enums used by command and adapter contracts in `src/veracrawl/contracts/policy.py`
- [X] T029 [P] [US1] Implement ReplayBundleManifest model with missing-ref behavior and completeness result fields in `src/veracrawl/contracts/replay.py`
- [X] T030 [P] [US1] Implement foundation registry registration models for contracts, commands, events, source adapter types, agent adapter fixtures, and fixture oracles in `src/veracrawl/contracts/registry.py`
- [X] T031 [US1] Populate FOUNDATION_CONTRACTS and TARGET_CONTRACT_AREAS for CommandEnvelope, CommandResult, CommandTypeSpec, BaseCommandPayload, CrawlRunEvent, EventTypeSpec, PolicyDecision, SourceAdapterSpec, SourceAdapterResult, AgentRuntimeSpec, AgentToolSpec, ContextRef, ContextBundle, AgentRunRequest, AgentRunResult, ModelRequest, ModelResponse, AgentActionTrace, ModelCallTrace, ToolCallTrace, ContextBundleTrace, ReplayBundleManifest, BenchmarkFixtureManifest, ExpectedOutputOracle, ExpectedEvidenceCoverageOracle, ExpectedEventSequenceOracle, ExpectedGraphOracle, FailureInjectionPlan, DRRestoreOracle, ReplayBundleOracle, TargetContractAreaCoverage, and broader FR-003 target areas in `src/veracrawl/contracts/registry.py`
- [X] T032 [US1] Populate COMMAND_TYPES and EVENT_TYPES for the minimum foundation command/event taxonomy in `src/veracrawl/contracts/registry.py`
- [X] T033 [US1] Implement registry consistency validation, canonical JSON export, missing schema detection, missing owner detection, missing target area coverage detection, missing follow-up gate detection, and missing test ref detection in `src/veracrawl/contracts/registry.py`
- [X] T034 [US1] Implement in-memory append-only event store with per-run sequence validation in `src/veracrawl/runtime_events/event_store.py`
- [X] T035 [US1] Implement foundation replay completeness checks for command refs, event cursor refs, source adapter result refs, trace refs, artifact hashes, redaction refs, and missing-ref behavior in `src/veracrawl/runtime_events/replay.py`
- [X] T036 [US1] Implement policy gate primitives for allow, deny, require-review, and blocked-command decisions in `src/veracrawl/policy/gates.py`
- [X] T037 [US1] Implement `veracrawl-contracts validate --format json` CLI entry point in `src/veracrawl/cli/contracts.py`
- [X] T038 [US1] Export contract models and registry APIs from `src/veracrawl/contracts/__init__.py`
- [X] T039 [US1] Run and satisfy US1 validation commands from `specs/001-target-architecture-foundation/quickstart.md`

**Checkpoint**: User Story 1 is independently functional and no later implementation can claim success without registry, command/event, replay, owner, and import-boundary validation.

---

## Phase 4: User Story 2 - Add Source And Agent Runtime Adapters (Priority: P2)

**Goal**: Allow source adapters and agent framework adapters to integrate through VeraCrawl-owned contracts without coupling core to websites, model providers, browser workflows, or agent frameworks.

**Independent Test**: `pytest tests/contract/test_agent_framework_conformance.py` and `pytest tests/contract/test_source_adapter_conformance.py` prove OpenAI Agent SDK and LangGraph fixtures plus fetch-like and non-fetch source stubs emit canonical VeraCrawl contracts and traces while core contracts remain unchanged.

### Tests for User Story 2

- [X] T040 [P] [US2] Write source adapter type mapping and natural result validation tests in `tests/contract/test_source_adapter_conformance.py`
- [X] T041 [P] [US2] Write fetch-like source adapter conformance tests for output refs, policy refs, replay refs, and idempotency in `tests/contract/test_source_adapter_conformance.py`
- [X] T042 [P] [US2] Write non-fetch source adapter conformance tests that reject fake FetchResult and PageSnapshot semantics in `tests/contract/test_source_adapter_conformance.py`
- [X] T043 [P] [US2] Write agent runtime port and tool gateway conformance tests in `tests/contract/test_agent_framework_conformance.py`
- [X] T044 [P] [US2] Write OpenAI Agent SDK adapter fixture tests for canonical AgentRunRequest, AgentRunResult, AgentActionTrace, ModelCallTrace, ToolCallTrace, and CommandResult refs in `tests/contract/test_agent_framework_conformance.py`
- [X] T045 [P] [US2] Write LangGraph adapter fixture tests for workflow-style state mapping, diagnostic-only framework state, and canonical trace refs in `tests/contract/test_agent_framework_conformance.py`
- [X] T046 [P] [US2] Extend import-boundary tests for named framework packages and adapter-only imports in `tests/contract/test_import_boundaries.py`

### Implementation for User Story 2

- [X] T047 [P] [US2] Implement SourceAdapterSpec, SourceAdapterResult, SourceAdapterCommand, adapter type/result mapping, and blocked-source validation in `src/veracrawl/contracts/source_adapter.py`
- [X] T048 [P] [US2] Implement AgentToolSpec, AgentRuntimeSpec, ContextRef, ContextBundle, AgentRunRequest, AgentRunResult, ModelRequest, ModelResponse, AgentActionTrace, ModelCallTrace, ToolCallTrace, and ContextBundleTrace models in `src/veracrawl/contracts/agent.py`
- [X] T049 [P] [US2] Implement SourceAdapterPort protocol and source adapter command protocol types in `src/veracrawl/ports/source_adapter.py`
- [X] T050 [P] [US2] Implement AgentRuntimePort, ModelProviderPort, ToolGatewayPort, and ContextStorePort protocols in `src/veracrawl/ports/agent_runtime.py`
- [X] T051 [US2] Register all target source adapter type mappings and required owner services in `src/veracrawl/contracts/registry.py`
- [X] T052 [US2] Register OpenAI Agent SDK and LangGraph conformance fixtures plus compatibility targets for LangChain, CrewAI, AutoGen, Semantic Kernel, and future frameworks in `src/veracrawl/contracts/registry.py`
- [X] T053 [US2] Implement framework-neutral agent runtime orchestration helpers that consume only VeraCrawl contracts and ports in `src/veracrawl/agents/runtime.py`
- [X] T054 [US2] Implement tool gateway validation that converts tool proposals to CommandEnvelope and CommandResult refs through owner service boundaries in `src/veracrawl/agents/tool_gateway.py`
- [X] T055 [US2] Implement reusable agent adapter conformance assertions in `src/veracrawl/agents/conformance.py`
- [X] T056 [P] [US2] Implement OpenAI Agent SDK conformance stub adapter without importing the real SDK from core packages in `src/veracrawl/adapters/agent_frameworks/openai_agent_sdk.py`
- [X] T057 [P] [US2] Implement LangGraph conformance stub adapter without importing LangGraph from core packages in `src/veracrawl/adapters/agent_frameworks/langgraph.py`
- [X] T058 [P] [US2] Implement fetch-like source adapter stub for `http` or `api_source` conformance in `src/veracrawl/adapters/sources/fetch_like_stub.py`
- [X] T059 [P] [US2] Implement non-fetch source adapter stub for `manual_seed`, `prior_snapshot`, `document_source`, or `file_import` conformance in `src/veracrawl/adapters/sources/non_fetch_stub.py`
- [X] T060 [US2] Run and satisfy US2 validation commands from `specs/001-target-architecture-foundation/quickstart.md`

**Checkpoint**: User Story 2 is independently functional and adapter compatibility exists through stable ports, not through core framework coupling.

---

## Phase 5: User Story 3 - Verify Safety, Replay, And Fixtures (Priority: P3)

**Goal**: Make foundation behavior verifiable through deterministic fixtures, explicit oracles, replay bundles, policy-blocked reports, and security/privacy checks before any production crawler path claims completion.

**Independent Test**: `pytest tests/unit/test_policy_gates.py`, `pytest tests/unit/test_replay_validation.py`, `pytest tests/integration/test_foundation_fixture_runner.py`, and `veracrawl-fixture run tests/fixtures/<fixture_id> --profile target --out .veracrawl-test-runs/<fixture_id>` prove blocked behavior and replay gaps are visible and cannot falsely pass.

### Tests for User Story 3

- [X] T061 [P] [US3] Write policy gate unit tests for source scope, robots/terms/customer authorization, credential/session use, browser side effects, prompt context, export, memory, graph, recovery, retention, and artifact lifecycle decisions in `tests/unit/test_policy_gates.py`
- [X] T062 [P] [US3] Write replay validation unit tests for fail_replay, allow_with_gap_report, redaction refs, command refs, source adapter refs, event cursor refs, artifact hashes, and trace refs in `tests/unit/test_replay_validation.py`
- [X] T063 [P] [US3] Write fixture runner integration tests for missing manifest, missing output/evidence/event/graph/failure/DR/replay oracle, undeclared tolerance, event ordering, forbidden events, missing evidence, adapter mismatch, blocked-source behavior, and raw credential leakage in `tests/integration/test_foundation_fixture_runner.py`
- [X] T064 [P] [US3] Create fetch-like fixture manifest, output/evidence/event/graph/DR/replay oracles, threshold file, artifact hash expectations, and README in `tests/fixtures/foundation-fetch-like/manifest.yaml`, `tests/fixtures/foundation-fetch-like/oracles/expected_outputs.yaml`, `tests/fixtures/foundation-fetch-like/oracles/expected_evidence.yaml`, `tests/fixtures/foundation-fetch-like/oracles/expected_events.yaml`, `tests/fixtures/foundation-fetch-like/oracles/expected_graph.yaml`, `tests/fixtures/foundation-fetch-like/oracles/expected_dr_restore.yaml`, `tests/fixtures/foundation-fetch-like/oracles/expected_replay.yaml`, `tests/fixtures/foundation-fetch-like/oracles/thresholds.yaml`, `tests/fixtures/foundation-fetch-like/artifacts/expected_hashes.yaml`, and `tests/fixtures/foundation-fetch-like/README.md`
- [X] T065 [P] [US3] Create non-fetch fixture manifest, output/evidence/event/graph/DR/replay oracles, threshold file, artifact hash expectations, and README in `tests/fixtures/foundation-non-fetch/manifest.yaml`, `tests/fixtures/foundation-non-fetch/oracles/expected_outputs.yaml`, `tests/fixtures/foundation-non-fetch/oracles/expected_evidence.yaml`, `tests/fixtures/foundation-non-fetch/oracles/expected_events.yaml`, `tests/fixtures/foundation-non-fetch/oracles/expected_graph.yaml`, `tests/fixtures/foundation-non-fetch/oracles/expected_dr_restore.yaml`, `tests/fixtures/foundation-non-fetch/oracles/expected_replay.yaml`, `tests/fixtures/foundation-non-fetch/oracles/thresholds.yaml`, `tests/fixtures/foundation-non-fetch/artifacts/expected_hashes.yaml`, and `tests/fixtures/foundation-non-fetch/README.md`
- [X] T066 [P] [US3] Create policy-blocked fixture manifest, output/evidence/event/graph/DR/replay oracles, failure injection plan, threshold file, and README in `tests/fixtures/foundation-policy-blocked-source/manifest.yaml`, `tests/fixtures/foundation-policy-blocked-source/oracles/expected_outputs.yaml`, `tests/fixtures/foundation-policy-blocked-source/oracles/expected_evidence.yaml`, `tests/fixtures/foundation-policy-blocked-source/oracles/expected_events.yaml`, `tests/fixtures/foundation-policy-blocked-source/oracles/expected_graph.yaml`, `tests/fixtures/foundation-policy-blocked-source/oracles/expected_dr_restore.yaml`, `tests/fixtures/foundation-policy-blocked-source/oracles/failure_injection.yaml`, `tests/fixtures/foundation-policy-blocked-source/oracles/expected_replay.yaml`, `tests/fixtures/foundation-policy-blocked-source/oracles/thresholds.yaml`, and `tests/fixtures/foundation-policy-blocked-source/README.md`
- [X] T067 [P] [US3] Create replay-missing-ref fixture manifest, output/evidence/event/graph/DR/replay oracles, failure injection plan, threshold file, and README in `tests/fixtures/foundation-replay-missing-ref/manifest.yaml`, `tests/fixtures/foundation-replay-missing-ref/oracles/expected_outputs.yaml`, `tests/fixtures/foundation-replay-missing-ref/oracles/expected_evidence.yaml`, `tests/fixtures/foundation-replay-missing-ref/oracles/expected_events.yaml`, `tests/fixtures/foundation-replay-missing-ref/oracles/expected_graph.yaml`, `tests/fixtures/foundation-replay-missing-ref/oracles/expected_dr_restore.yaml`, `tests/fixtures/foundation-replay-missing-ref/oracles/expected_replay.yaml`, `tests/fixtures/foundation-replay-missing-ref/oracles/failure_injection.yaml`, `tests/fixtures/foundation-replay-missing-ref/oracles/thresholds.yaml`, and `tests/fixtures/foundation-replay-missing-ref/README.md`
- [X] T068 [P] [US3] Create missing-evidence fixture manifest, output/evidence/event/DR/replay oracles, failure injection plan, threshold file, and README in `tests/fixtures/foundation-missing-evidence/manifest.yaml`, `tests/fixtures/foundation-missing-evidence/oracles/expected_outputs.yaml`, `tests/fixtures/foundation-missing-evidence/oracles/expected_evidence.yaml`, `tests/fixtures/foundation-missing-evidence/oracles/expected_events.yaml`, `tests/fixtures/foundation-missing-evidence/oracles/expected_dr_restore.yaml`, `tests/fixtures/foundation-missing-evidence/oracles/expected_replay.yaml`, `tests/fixtures/foundation-missing-evidence/oracles/failure_injection.yaml`, `tests/fixtures/foundation-missing-evidence/oracles/thresholds.yaml`, and `tests/fixtures/foundation-missing-evidence/README.md`
- [X] T069 [P] [US3] Create adapter-mismatch fixture manifest, event/replay/failure oracles, threshold file, and README in `tests/fixtures/foundation-adapter-mismatch/manifest.yaml`, `tests/fixtures/foundation-adapter-mismatch/oracles/expected_events.yaml`, `tests/fixtures/foundation-adapter-mismatch/oracles/expected_replay.yaml`, `tests/fixtures/foundation-adapter-mismatch/oracles/failure_injection.yaml`, `tests/fixtures/foundation-adapter-mismatch/oracles/thresholds.yaml`, and `tests/fixtures/foundation-adapter-mismatch/README.md`

### Implementation for User Story 3

- [X] T070 [P] [US3] Implement BenchmarkFixtureManifest, ExpectedOutputOracle, ExpectedEvidenceCoverageOracle, ExpectedEventSequenceOracle, ExpectedGraphOracle, FailureInjectionPlan, DRRestoreOracle, ReplayBundleOracle, threshold, and artifact hash models in `src/veracrawl/contracts/fixture.py`
- [X] T071 [US3] Extend policy gates with blocked-action reports and deny/require-review enforcement for adapter, tool, prompt context, credential, browser, memory, graph, export, retention, and artifact lifecycle subjects in `src/veracrawl/policy/gates.py`
- [X] T072 [US3] Extend replay validator with gap reports, fail versus needs-review outcomes, stable redaction refs, and no-pass-on-missing-required-ref behavior in `src/veracrawl/runtime_events/replay.py`
- [X] T073 [US3] Implement fixture manifest loading, output oracle validation, evidence oracle validation, event oracle validation, graph oracle validation, DR restore oracle validation, replay oracle validation, artifact hash validation, tolerance validation, adapter mismatch diagnostics, and raw secret scanning in `src/veracrawl/cli/fixtures.py`
- [X] T074 [US3] Register required foundation fixture/oracle entries for fetch-like, non-fetch, policy-blocked, replay-missing-ref, missing-evidence, and adapter-mismatch fixtures in `src/veracrawl/contracts/registry.py`
- [X] T075 [US3] Implement `veracrawl-fixture run tests/fixtures/<fixture_id> --profile target --out .veracrawl-test-runs/<fixture_id>` CLI behavior in `src/veracrawl/cli/fixtures.py`
- [X] T076 [US3] Run and satisfy US3 validation commands from `specs/001-target-architecture-foundation/quickstart.md`

**Checkpoint**: User Story 3 is independently functional and unsafe behavior, missing refs, blocked sources, and fixture/oracle drift cannot falsely pass.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify consistency across the full foundation and prepare for analysis/implementation workflow.

- [X] T077 [P] Update package usage notes for contract validation and fixture execution in `README.md`
- [X] T078 [P] Update implementation notes for the target foundation package map in `docs/10-target-implementation-design.md`
- [X] T079 Run ruff, mypy, and pytest full foundation gate with a 30-second local timing check from `specs/001-target-architecture-foundation/quickstart.md`
- [X] T080 Run Spec Kit consistency checks with `$speckit-analyze` and record any required follow-up in `specs/001-target-architecture-foundation/tasks.md`
- [X] T081 Verify every task ID maps to a contract, owner service, or verification check in `specs/001-target-architecture-foundation/tasks.md`
- [X] T082 Confirm no code, docs, tests, or CLI output claim full crawler runtime completion in `specs/001-target-architecture-foundation/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1 and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Phase 2 and is the MVP foundation.
- **User Story 2 (Phase 4)**: Depends on Phase 2 and can proceed after US1 tests define registry expectations; final registry integration depends on T031-T033.
- **User Story 3 (Phase 5)**: Depends on Phase 2 and can proceed after US1 replay and policy contract surfaces exist; final fixture registration depends on T033.
- **Polish (Phase 6)**: Depends on selected user stories being complete.

### User Story Dependencies

- **US1 - Establish Foundation Contracts**: Must complete before claiming the foundation contract checkpoint.
- **US2 - Add Source And Agent Runtime Adapters**: Can be developed after Phase 2, but registry updates integrate with US1 registry APIs.
- **US3 - Verify Safety, Replay, And Fixtures**: Can be developed after Phase 2, but replay and policy implementation integrates with US1/US2 contract surfaces.

### Within Each User Story

- Tests must be written first and fail before implementation.
- Contract models must exist before registry population.
- Registry validation must exist before CLI validation can pass.
- Ports must exist before adapters.
- Fixture manifests and oracles must exist before fixture runner acceptance can pass.

## Parallel Opportunities

- Setup tasks T003-T009 can run in parallel after T001-T002.
- Foundational tasks T013-T014 and T016-T017 can run in parallel after T012.
- US1 tests T020-T025 can run in parallel.
- US1 models T026-T030 can run in parallel before registry population T031-T033.
- US2 tests T040-T046 can run in parallel.
- US2 ports/models T047-T050 can run in parallel before adapter implementations T053-T059.
- US2 adapter stubs T056-T059 can run in parallel after ports and contracts exist.
- US3 tests T061-T063 and fixture data tasks T064-T069 can run in parallel.
- US3 model task T070 can run in parallel with fixture data tasks T064-T069.

## Parallel Example: User Story 1

```text
Task: "T020 [P] [US1] Write contract registry completeness tests in tests/contract/test_contract_registry.py"
Task: "T021 [P] [US1] Write command validation tests in tests/contract/test_command_event_replay_contracts.py"
Task: "T024 [P] [US1] Write import-boundary tests in tests/contract/test_import_boundaries.py"
Task: "T026 [P] [US1] Implement command models in src/veracrawl/contracts/command.py"
Task: "T027 [P] [US1] Implement event models in src/veracrawl/contracts/event.py"
Task: "T029 [P] [US1] Implement replay models in src/veracrawl/contracts/replay.py"
```

## Parallel Example: User Story 2

```text
Task: "T040 [P] [US2] Write source adapter type mapping tests in tests/contract/test_source_adapter_conformance.py"
Task: "T043 [P] [US2] Write agent runtime port conformance tests in tests/contract/test_agent_framework_conformance.py"
Task: "T049 [P] [US2] Implement SourceAdapterPort in src/veracrawl/ports/source_adapter.py"
Task: "T050 [P] [US2] Implement AgentRuntimePort in src/veracrawl/ports/agent_runtime.py"
Task: "T056 [P] [US2] Implement OpenAI Agent SDK conformance stub in src/veracrawl/adapters/agent_frameworks/openai_agent_sdk.py"
Task: "T057 [P] [US2] Implement LangGraph conformance stub in src/veracrawl/adapters/agent_frameworks/langgraph.py"
```

## Parallel Example: User Story 3

```text
Task: "T061 [P] [US3] Write policy gate unit tests in tests/unit/test_policy_gates.py"
Task: "T062 [P] [US3] Write replay validation unit tests in tests/unit/test_replay_validation.py"
Task: "T064 [P] [US3] Create fetch-like fixture files in tests/fixtures/foundation-fetch-like/"
Task: "T065 [P] [US3] Create non-fetch fixture files in tests/fixtures/foundation-non-fetch/"
Task: "T068 [P] [US3] Create missing-evidence fixture files in tests/fixtures/foundation-missing-evidence/"
Task: "T069 [P] [US3] Create adapter-mismatch fixture files in tests/fixtures/foundation-adapter-mismatch/"
Task: "T070 [P] [US3] Implement fixture oracle models in src/veracrawl/contracts/fixture.py"
```

## Implementation Strategy

### Foundation First

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational primitives.
3. Complete Phase 3 User Story 1.
4. Validate with `veracrawl-contracts validate --format json`, `pytest tests/contract/test_contract_registry.py`, `pytest tests/contract/test_command_event_replay_contracts.py`, and `pytest tests/contract/test_import_boundaries.py`.

### Incremental Delivery

1. Add US1 to lock contract registry, command/event/replay, owner, and import-boundary rules.
2. Add US2 to prove source and agent adapter abstractions through conformance fixtures.
3. Add US3 to prove policy-blocked behavior, replay gaps, and fixture/oracle validation.
4. Run the full foundation gate from [quickstart.md](quickstart.md).

### Non-Deceptive Completion Rule

This task list completes the target architecture foundation only. It must not be used to claim full production crawler runtime, browser execution, memory intelligence, graph intelligence, export connector, or scale/reliability completion.

### Implementation Verification Record

- `$speckit-analyze` consistency pass on 2026-05-02 found no blocking constitution, requirement coverage, or task ordering issue after implementation document updates.
- T080/T081 verification maps all FR-001 through FR-014 and SC-001 through SC-007 to at least one task group, contract registry entry, owner package boundary, or validation command.
- T082 verification found only negative/non-deceptive statements about full crawler runtime completion; no source, test, CLI, README, docs, spec, plan, or task text claims the production crawler runtime is complete.
