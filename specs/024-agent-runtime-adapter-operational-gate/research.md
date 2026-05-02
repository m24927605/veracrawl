# Research: Agent Runtime Adapter Operational Gate

## Decision: Add a gate-specific report instead of overloading AgentRunResult

**Rationale**: `AgentRunResult` is a per-run terminal result. The gate needs to aggregate multiple framework families, runtime availability, security/privacy refs, observability refs, and negative reasons.

**Rejected**: Marking individual `AgentRunResult` objects as operational. This would hide missing framework coverage.

## Decision: Dynamic adapter loading in CLI

**Rationale**: Existing persistence, queue, and object-store gates use dynamic imports so core and CLI do not statically couple to adapter SDKs. The same approach fits agent framework adapters.

**Rejected**: Static imports of `veracrawl.adapters.agent_frameworks.*` or real SDK packages in core/CLI. This violates the framework-neutral boundary.

## Decision: Deterministic contract adapters pass only canonical mapping

**Rationale**: CI cannot require API keys or installed framework SDKs. Deterministic adapter-owned modules can prove canonical mapping. A live SDK/runtime path without runtime refs returns `needs_review`.

**Rejected**: Claiming real OpenAI/LangChain/LangGraph live integration without credentials, packages, or runtime refs.

## Decision: Framework-native state is diagnostic only

**Rationale**: The constitution requires VeraCrawl contracts, commands, events, policy decisions, tool calls, artifact refs, and replay records to be canonical. Framework-native state is not replay source of truth.

**Rejected**: Persisting framework graph/checkpoint/thread state as `AgentRunResult.output_ref`.
