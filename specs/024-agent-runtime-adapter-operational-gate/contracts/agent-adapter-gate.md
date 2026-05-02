# Agent Adapter Gate Contract

Run:

```text
veracrawl-agent-adapters run tests/fixtures/<fixture_id> --profile target --out .veracrawl-test-runs/<fixture_id>
```

Required pass refs:

- framework execution refs for OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, and FutureFramework
- `AgentRunRequest`, `AgentRunResult`, `AgentActionTrace`, `ModelCallTrace`, `ToolCallTrace`, and `ContextBundleTrace` refs
- command result, policy, observability, security/privacy, event cursor, outbox, and replay refs
- diagnostic framework-state refs only when they are not canonical

Fixtures:

- `agent-runtime-adapter-success`
- `agent-runtime-adapter-runtime-unavailable`
- `agent-runtime-adapter-raw-prompt-leak`
- `agent-runtime-adapter-framework-state-canonical`
- `agent-runtime-adapter-missing-model-trace`
- `agent-runtime-adapter-missing-tool-trace`
- `agent-runtime-adapter-missing-replay`
- `agent-runtime-adapter-missing-security-privacy`
- `agent-runtime-adapter-unsupported-framework`

Passing this gate proves canonical adapter mapping and non-deceptive live-runtime handling. It does not prove external API calls or vendor production operations.
