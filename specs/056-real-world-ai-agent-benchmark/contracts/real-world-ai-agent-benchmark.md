# Contract: Real-World AI Agent Crawl Planning And Extraction Benchmark

## Commands

### `record_real_world_ai_agent_decision`

- Owner: `agents`
- Target aggregate: `RealWorldAIAgentDecisionTrace`
- Required policy refs: source scope, prompt/context, controlled tool, evidence/verification.
- Emits: `real_world_ai_agent_decision_recorded`

### `record_real_world_ai_agent_extraction_candidate`

- Owner: `extract`
- Target aggregate: `RealWorldAIAgentExtractionCandidate`
- Required policy refs: source scope, prompt/context, evidence/verification, publication gate.
- Emits: `real_world_ai_agent_extraction_candidate_recorded`

### `record_real_world_ai_agent_benchmark_report`

- Owner: `ops`
- Target aggregate: `RealWorldAIAgentBenchmarkRunReport`
- Required policy refs: source scope, prompt/context, evidence/verification, runtime verification.
- Emits: `real_world_ai_agent_benchmark_reported`

### `record_real_world_ai_agent_benchmark_manifest`

- Owner: `tests`
- Target aggregate: `RealWorldAIAgentBenchmarkManifest`
- Emits: `real_world_ai_agent_benchmark_manifest_recorded`

## Runtime Contract

1. Load `RealWorldAIAgentBenchmarkManifest`.
2. Execute the referenced row 055 corpus fixture and require a passing `RealWorldBenchmarkRunReport`.
3. For each passing site observation, build sanitized context bundle refs from source observation, artifact, content hash, and policy refs.
4. Invoke `ModelProviderPort.complete(ModelRequest)` and `AgentRuntimePort.run(AgentRunRequest)` for each required decision type.
5. Materialize `ModelCallTrace`, `AgentActionTrace`, `ToolCallTrace`, and `ContextBundleTrace`.
6. Generate extraction candidates only from source-backed anchors and artifact/content hash refs.
7. Record evidence/verification/publication gate refs, while keeping published output refs empty for this benchmark.
8. Build `RealWorldAIAgentBenchmarkRunReport` and fail with typed diagnostics if any mandatory refs are missing.

## Pass Requirements

- Row 055 public corpus report passes.
- At least four public site observations are covered.
- Every site has crawl planning, site understanding, extraction candidate generation, and verification/repair decision refs.
- Every AI decision has model call, agent action, tool call, context bundle, policy, command/event/outbox, and replay refs.
- Every extraction candidate has source anchors, artifacts, content hashes, evidence coverage, evidence packet, evidence anchors, verification, review, and publication gate refs.
- No `llm_output_evidence_refs`, `direct_publication_refs`, `framework_native_state_refs`, or `core_import_violation_refs` are present.

## Failure Types

- `real_world_ai_missing_real_world_corpus`
- `real_world_ai_missing_model_call_trace`
- `real_world_ai_missing_agent_action_trace`
- `real_world_ai_missing_tool_call_trace`
- `real_world_ai_missing_context_bundle_trace`
- `real_world_ai_missing_candidate_source_anchor`
- `real_world_ai_llm_output_as_evidence`
- `real_world_ai_publication_bypass`
- `real_world_ai_framework_state_persisted`
- `real_world_ai_core_import_boundary`
- `real_world_ai_missing_replay_refs`
- `real_world_ai_adapter_unavailable`

## Fixture/Oracle Contract

- Success fixture: `tests/fixtures/real-world-ai-agent-public-corpus`.
- Negative fixtures cover missing model trace, missing candidate anchor, LLM output as evidence, publication bypass, framework-native state, and replay gaps.
- Oracles are JSON/YAML-compatible files under each fixture's `oracles/` directory and are registered in `FixtureOracleRegistration`.
