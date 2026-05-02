# Contract: Framework-Neutral Agent Adapter

VeraCrawl core owns the agent runtime contracts. Agent frameworks are replaceable adapters. This contract allows OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, and future frameworks to integrate without making framework-native state canonical.

## Core Port

`veracrawl.ports.agent_runtime.AgentRuntimePort`:

```python
class AgentRuntimePort(Protocol):
    def run(self, request: AgentRunRequest) -> AgentRunResult: ...
```

Rules:

- The port accepts and returns only VeraCrawl contracts.
- The port must not expose framework-native request, state, graph, message, memory, or tool objects.
- Runtime-specific diagnostics may be stored as artifact refs or trace refs, but replay uses VeraCrawl contracts.

## Required Adapter Inputs

Every framework adapter must accept:

- `AgentRunRequest`
- `AgentRuntimeSpec`
- `ContextBundle`
- `AgentToolSpec` list
- policy decisions relevant to prompt context, tool calls, memory retrieval, graph signal use, and recovery
- deterministic clock/randomness ports when running fixture tests

Validation:

- `runtime_spec.runtime_type` must be `agent_framework_adapter`.
- `framework_state_persistence` must be `forbidden` or `diagnostic_only`.
- Context refs must already be sanitized and taint-labeled.

## Required Adapter Outputs

Every framework adapter must produce:

- `AgentRunResult`
- `AgentActionTrace`
- zero or more `ModelCallTrace`
- zero or more `ToolCallTrace`
- one `ContextBundleTrace`
- `CommandEnvelope` and `CommandResult` refs for executed mutating tools
- `PolicyDecision` refs for gated tool calls and prompt context decisions

Validation:

- `AgentRunResult.agent_action_trace_id` must resolve.
- Tool calls must not bypass `ToolGatewayPort`.
- Mutating tool output must resolve to a `CommandResult`.
- Framework-native messages, graph nodes, task objects, or memories must not be persisted as canonical VeraCrawl state.

## Tool Execution Contract

Framework adapters may propose tool calls. VeraCrawl executes tools through `ToolGatewayPort`:

```python
class ToolGatewayPort(Protocol):
    def execute(self, command: CommandEnvelope) -> CommandResult: ...
```

Rules:

- Adapters must convert proposed tool calls into `CommandEnvelope`.
- Policy gates run before execution.
- Owner services commit or reject state changes.
- `ToolCallTrace` records proposed, rejected, approved, executed, or failed status.

## Conformance Fixtures

### OpenAI Agent SDK Fixture

Fixture ID: `agent-openai-sdk-planner-conformance`

Purpose:

- prove a model/tool SDK adapter can map a planner-style run into VeraCrawl canonical contracts
- verify sanitized context handling, tool proposal conversion, policy decisions, and trace completeness

Expected outputs:

- `AgentRunResult.status=completed`
- `AgentActionTrace.agent_role=planner`
- at least one `ModelCallTrace`
- zero or more `ToolCallTrace`, each mapped to `CommandEnvelope` and `CommandResult` when executed
- no core import of OpenAI Agent SDK packages

### LangGraph Fixture

Fixture ID: `agent-langgraph-workflow-conformance`

Purpose:

- prove a graph/workflow-style agent framework can map orchestration state into VeraCrawl canonical workflow and trace contracts
- verify framework-native graph state remains diagnostic only

Expected outputs:

- `AgentRunResult.status=completed` or `escalated` with review refs
- `AgentActionTrace` and `ContextBundleTrace`
- tool and command traces when a graph node requests mutation
- no core import of LangGraph packages

## Compatibility Requirements For Other Frameworks

LangChain, CrewAI, AutoGen, Semantic Kernel, and future frameworks must satisfy the same conformance rules:

- implement `AgentRuntimePort`
- emit VeraCrawl contracts
- isolate framework-native state in adapter-only modules
- preserve policy decisions, command results, trace refs, and replay refs
- pass the same import-boundary tests

No framework gets a special canonical path.

## Negative Tests

Tests must fail when:

- a core package imports an agent framework package or `veracrawl.adapters.agent_frameworks`
- an adapter returns framework-native state as `AgentRunResult.output_ref`
- a mutating tool bypasses `ToolGatewayPort`
- a tool call has no `CommandEnvelope` or `CommandResult`
- a denied prompt-context policy still reaches the model provider
- a replay manifest omits required model/tool/context trace refs
