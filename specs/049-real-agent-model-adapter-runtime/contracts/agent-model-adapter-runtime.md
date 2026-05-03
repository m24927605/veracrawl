# Contract: Real Agent And Model Adapter Runtime

## CLI

```text
veracrawl-agent-model-runtime run tests/fixtures/<fixture_id> --profile target --out <output_dir>
```

The CLI must:

- load the fixture manifest;
- dynamically import concrete adapter modules only at the CLI/adapter layer;
- compose `ModelProviderPort` and `AgentRuntimePort` bindings;
- call the core runtime aggregate;
- write `run_report.json`;
- fail the process when observed completion/status does not match the fixture
  manifest.

## Required Runtime Behavior

- A passing run must execute planner, extractor, and repair/drift turns through
  model and agent runtime ports.
- A passing run must write canonical model request/response/trace refs, agent
  run/result/action trace refs, context/tool trace refs, policy refs,
  command/event/outbox refs, adapter runtime refs, security/privacy refs,
  observability refs, and replay refs.
- Missing external SDKs, provider credentials, or wrapper callables must return
  `needs_review`.
- Core packages must not statically import `veracrawl.adapters`, OpenAI SDKs,
  LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, Anthropic, Gemini, or
  local model runtime packages.
- Framework/provider-native state can only appear as diagnostic refs. It cannot
  become VeraCrawl canonical state.
- Raw prompts, raw responses, and raw credentials cannot be persisted.

## Required Fixture Scenarios

| Fixture | Expected |
| --- | --- |
| agent-model-adapter-local-runtime-success | pass |
| agent-model-adapter-runtime-unavailable | needs_review |
| agent-model-adapter-missing-run-control | fail |
| agent-model-adapter-missing-live-normalization | fail |
| agent-model-adapter-missing-schema-extraction | fail |
| agent-model-adapter-unsupported-provider | fail |
| agent-model-adapter-unsupported-framework | fail |
| agent-model-adapter-raw-prompt-leak | fail |
| agent-model-adapter-raw-response-leak | fail |
| agent-model-adapter-raw-credential-leak | fail |
| agent-model-adapter-framework-state-canonical | fail |
| agent-model-adapter-provider-transcript-canonical | fail |
| agent-model-adapter-missing-model-trace | fail |
| agent-model-adapter-missing-tool-trace | fail |
| agent-model-adapter-missing-replay | fail |
| agent-model-adapter-core-import-boundary | fail |

## Registry Additions

Commands:

- `record_agent_model_adapter_runtime_report`
- `record_agent_model_adapter_fixture_manifest`

Events:

- `agent_model_adapter_runtime_reported`
- `agent_model_adapter_fixture_manifest_recorded`

Target area:

- `real_agent_model_adapter_runtime`
