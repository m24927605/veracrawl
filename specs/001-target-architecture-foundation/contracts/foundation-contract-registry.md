# Contract: Foundation Contract Registry

The foundation registry is the executable source of truth that ties Python models, command schemas, event schemas, owner services, replay requirements, and tests together. It implements the target contract profile subset clarified for this feature.

## Registry Shape

The implementation must expose a machine-readable registry from `veracrawl.contracts.registry`:

```python
FOUNDATION_CONTRACTS: dict[str, ContractRegistration]
COMMAND_TYPES: dict[str, CommandTypeRegistration]
EVENT_TYPES: dict[str, EventTypeRegistration]
SOURCE_ADAPTER_TYPES: dict[str, SourceAdapterTypeRegistration]
AGENT_ADAPTER_FIXTURES: dict[str, AgentAdapterFixtureRegistration]
FIXTURE_ORACLES: dict[str, FixtureOracleRegistration]
TARGET_CONTRACT_AREAS: dict[str, TargetContractAreaCoverageRegistration]
```

Each registration must be serializable to canonical JSON for test snapshots.

## ContractRegistration

Required fields:

- `contract_name`
- `owner_service`
- `python_model`
- `schema_ref`
- `source_doc_ref`
- `mutation_allowed`
- `replay_required`
- `privacy_lifecycle_required`
- `test_refs`

Validation:

- `contract_name` must be unique.
- `owner_service` must match the ownership rules in `docs/07-data-contracts.md`.
- `python_model` must import from `veracrawl.contracts.*`, not from adapters.
- `test_refs` must include at least one contract or negative test for every foundation contract.

## Foundation Contract Coverage

The first registry must include these contracts:

| Contract | Owner service/package | Required test category |
| --- | --- | --- |
| CommandEnvelope | target aggregate owner | command validation and state transition |
| CommandResult | target aggregate owner | command/result/event linkage |
| CommandTypeSpec | contracts/runtime_events | registry consistency |
| BaseCommandPayload | contracts | payload schema completeness |
| CrawlRunEvent | runtime_events | append ordering and replay refs |
| EventTypeSpec | runtime_events | payload schema mapping |
| PolicyDecision | policy/control | allow/deny/review behavior |
| SourceAdapterSpec | ports/adapters | adapter declaration validation |
| SourceAdapterResult | adapter owner by type | natural result mapping |
| AgentToolSpec | agents | tool schema and policy gate |
| AgentRuntimeSpec | agents | framework-neutral runtime |
| ContextRef | agents | taint and redaction refs |
| ContextBundle | agents | sanitized context and exclusions |
| AgentRunRequest | agents | role/tool/runtime compatibility |
| AgentRunResult | agents | trace linkage |
| ModelRequest | agents | sanitized prompt context |
| ModelResponse | agents | parsed output and safety status |
| AgentActionTrace | agents | replayable agent trace |
| ModelCallTrace | agents | provider diagnostic boundary |
| ToolCallTrace | agents | command/result/tool linkage |
| ContextBundleTrace | agents | replayable context refs |
| ReplayBundleManifest | review_replay/runtime_events | missing-ref behavior |
| BenchmarkFixtureManifest | tests | fixture required refs |
| ExpectedOutputOracle | tests | output oracle required refs and tolerance rules |
| ExpectedEvidenceCoverageOracle | tests | evidence anchor and verification coverage |
| ExpectedEventSequenceOracle | tests | event ordering and payload refs |
| ExpectedGraphOracle | tests | graph expectation and forbidden graph semantics |
| FailureInjectionPlan | tests | failure injection and recovery visibility |
| DRRestoreOracle | tests | restore oracle shape and missing-ref behavior |
| ReplayBundleOracle | tests | replay completeness |
| TargetContractAreaCoverage | contracts | target area coverage matrix and no-false-completion gate |

## TargetContractAreaCoverageRegistration

Required fields:

- `contract_area`
- `owner_service`
- `coverage_status`
- `materialized_contract_refs`
- `placeholder_contract_refs`
- `canonical_store_impact`
- `artifact_store_impact`
- `event_refs`
- `projection_refs`
- `replay_impact`
- `privacy_lifecycle_impact`
- `required_test_refs`
- `followup_spec_gate`

Minimum target area coverage rows:

| Contract area | Foundation status | Required gate |
| --- | --- | --- |
| source_adapters | materialized | source adapter conformance tests pass |
| commands | materialized | command payload and owner registry tests pass |
| events | materialized | event payload and sequence tests pass |
| replay | materialized | missing-ref replay tests pass |
| agent_runtime | materialized | framework adapter conformance tests pass |
| fixture_oracles | materialized | output/evidence/event/graph/failure/DR/replay oracle tests pass |
| evidence | foundation_placeholder | follow-up evidence spec must materialize EvidencePacket and evidence coverage contracts before publication claims |
| verification | foundation_placeholder | follow-up verification spec must materialize VerificationDecision and conflict contracts before publication claims |
| publication | foundation_placeholder | follow-up publication spec must materialize PublishedOutput and OutputManifest contracts before publication claims |
| projection | foundation_placeholder | follow-up projection spec must materialize projection watermarks and rebuild contracts before projection claims |
| graph | foundation_placeholder | follow-up graph spec must materialize graph projection contracts before graph intelligence claims |
| memory | foundation_placeholder | follow-up memory spec must materialize memory contracts before memory intelligence claims |
| export | foundation_placeholder | follow-up export spec must materialize export and withdrawal contracts before export claims |
| ops | foundation_placeholder | follow-up ops spec must materialize failure/recovery/DR contracts before operations claims |
| artifact_lifecycle | foundation_placeholder | follow-up artifact lifecycle spec must materialize retention, redaction, tombstone, deletion, and legal hold contracts before lifecycle claims |

Validation:

- Every `docs/07` target area listed in FR-003 must appear exactly once.
- `foundation_placeholder` and `deferred_with_gate` rows must define a follow-up spec gate and required tests.
- Placeholder coverage cannot be used to claim target-complete runtime behavior.

## CommandTypeRegistration

Required fields:

- `command_type`
- `owner_service`
- `target_aggregate_type`
- `payload_schema_ref`
- `required_policy_decision_types`
- `approval_required`
- `expected_version_required`
- `lease_required`
- `emitted_event_types`
- `failure_contract_ref`

Minimum foundation command types:

| Command type | Owner | Payload schema | Emits |
| --- | --- | --- | --- |
| `execute_source_adapter` | adapter owner by type | SourceAdapterCommandPayload | source_adapter_result_recorded, command_committed or command_rejected |
| `run_agent_runtime` | agents | AgentWorkflowPayload | agent_action_recorded, model_called, tool_called as applicable |
| `execute_agent_tool` | target aggregate owner | BaseCommandPayload or specific payload | tool_called, command_committed or command_rejected |
| `record_policy_decision` | policy/control | BaseCommandPayload | policy_evaluated |
| `append_replay_manifest` | review_replay | BaseCommandPayload | command_committed |
| `validate_fixture_oracle` | review_replay/ops | BaseCommandPayload | command_committed or error_recorded |

Validation:

- Every `payload_schema_ref` must resolve to a Pydantic model and exported JSON Schema.
- Every emitted event must resolve to `EVENT_TYPES`.
- A command owned by one service must not mutate another service's aggregate directly.

## EventTypeRegistration

Required fields:

- `event_type`
- `event_version`
- `payload_schema_ref`
- `owner_service`
- `state_before_required`
- `state_after_required`
- `replay_critical_refs`
- `redaction_policy`

Minimum foundation event types:

- `command_received`
- `command_committed`
- `command_rejected`
- `policy_evaluated`
- `agent_action_recorded`
- `model_called`
- `tool_called`
- `source_adapter_result_recorded`
- `review_created`
- `error_recorded`

Validation:

- Replay-critical refs must not be removed by redaction.
- State transition events must include `state_before` and `state_after`.
- Event schema versions must be present in `ReplayBundleManifest.contract_schema_versions` or `event_schema_versions`.

## SourceAdapterTypeRegistration

Required fields:

- `adapter_type`
- `owner_service`
- `natural_result_types`
- `required_policy_decision_types`
- `companion_contracts`
- `fixture_refs`

Minimum mapping:

| Adapter type | Owner | Natural result types |
| --- | --- | --- |
| `http` | fetch | fetch_result, blocked_source |
| `sitemap` | fetch | discovered_links, blocked_source |
| `rss` | fetch | discovered_links, blocked_source |
| `browser_snapshot` | browser | browser_snapshot, blocked_source |
| `authorized_session` | control | session_state, blocked_source |
| `api_source` | fetch | api_payload, blocked_source |
| `document_source` | normalize | document_artifact, blocked_source |
| `file_import` | artifact_lifecycle | file_artifact |
| `manual_seed` | control | seed_plan |
| `prior_snapshot` | control | prior_snapshot_ref |

Validation:

- At least one fetch-like fixture must emit a valid fetch-like result.
- At least one non-fetch fixture must emit a valid non-fetch result.
- Policy-denied adapter execution must emit a blocked source result and policy decision refs.

## AgentAdapterFixtureRegistration

Required fields:

- `fixture_id`
- `framework_name`
- `runtime_spec_ref`
- `input_request_ref`
- `expected_result_ref`
- `expected_trace_refs`
- `forbidden_core_imports`

Initial required fixtures:

- `agent-openai-sdk-planner-conformance`
- `agent-langgraph-workflow-conformance`

Validation:

- Both fixtures must produce the same canonical `AgentRunRequest`, `AgentRunResult`, trace, command, policy, and replay shapes for equivalent roles.
- Core packages must not import either adapter module.
- Framework-native state may be persisted only as diagnostic refs that point back to canonical VeraCrawl events.

## FixtureOracleRegistration

Required fields:

- `fixture_id`
- `manifest_ref`
- `expected_outputs_ref`
- `expected_evidence_ref`
- `expected_events_ref`
- `expected_graph_ref`
- `expected_dr_restore_ref`
- `expected_replay_ref`
- `expected_artifact_hashes_ref`
- `failure_injection_ref`
- `thresholds_ref`
- `negative_case`

Required foundation fixtures:

- `foundation-fetch-like`
- `foundation-non-fetch`
- `foundation-policy-blocked-source`
- `foundation-replay-missing-ref`
- `foundation-missing-evidence`
- `foundation-adapter-mismatch`

Validation:

- Missing output, evidence, event, graph, failure, DR restore, or replay oracle files fail the fixture runner when referenced by the manifest.
- Undeclared tolerances fail the fixture runner.
- Replay missing required refs fails or returns needs-review, never pass.

## Required Tests

The implementation must include tests that fail when:

- a foundation contract is missing owner, schema, or test refs
- a command references an unknown payload schema
- an event references an unknown event payload schema
- core imports `veracrawl.adapters` or named agent framework packages
- a non-fetch adapter emits fetch-only result refs
- a denied policy gate still permits command execution
- replay completeness passes with a missing required ref
- a fixture declares tolerance without an explicit threshold field
- a target contract area listed in FR-003 has no registry coverage row
- missing evidence still permits publication or pass status
- an adapter mismatch returns framework-native or adapter-native state as canonical VeraCrawl state
