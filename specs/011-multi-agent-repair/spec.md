# Feature Specification: VeraCrawl Multi-Agent Repair

**Feature Branch**: `011-multi-agent-repair`  
**Created**: 2026-05-02  
**Status**: Draft  
**Input**: User description: "建立 VeraCrawl Full Multi-Agent Orchestration and Repair Loops Spine：在 memory kernel 之後，實作 framework-neutral multi-agent workflow、agent handoff、coordination decision、repair loop、drift/verification repair signal、tool/policy/replay gating、loop budget、arbitration/escalation/cancellation、memory/graph/evidence context refs，以及 fixture/oracle 測試基礎。必須遵守 docs/07、08、09、10、11 與 constitution；multi-agent orchestration 不得繞過 owner service、policy gate、command/event/replay；memory/graph/agent reasoning 不得取代 source evidence；不得實作成單站 scraper；core 不得耦合 OpenAI Agent SDK、LangChain、LangGraph、CrewAI、AutoGen、Semantic Kernel、model SDK、browser、storage、queue、memory store、graph store、export target 或具體 HTTP client。"

## Requirements

- **FR-001**: System MUST define `MultiAgentWorkflow`, `AgentHandoff`, `CoordinationDecision`, `DriftRepairSignal`, `MultiAgentRepairReport`, and `MultiAgentFixtureManifest`.
- **FR-002**: System MUST require loop budget, termination, escalation, arbitration, context, policy, graph, memory, and evidence refs for workflows.
- **FR-003**: System MUST record explicit handoffs between agent roles with context bundle trace refs, required output schema refs, policy refs, status, and output refs.
- **FR-004**: System MUST resolve conflicting recommendations through `CoordinationDecision`, not last-writer-wins behavior.
- **FR-005**: System MUST preserve before/after evidence and rollback refs for repair loops.
- **FR-006**: System MUST keep owner services responsible for durable mutations; agents may only propose or command through owner-service commands.
- **FR-007**: System MUST reject owner-service bypass, unresolved coordination conflict, and agent-reasoning-as-evidence attempts.
- **FR-008**: System MUST include success fixtures for repair, arbitration, and evidence-backed repair loops.
- **FR-009**: System MUST include negative fixtures for owner-service bypass, unresolved coordination conflict, and agent reasoning as evidence.
- **FR-010**: System MUST register contracts, commands, events, fixtures, and target area coverage.
- **FR-011**: System MUST keep core independent of concrete agent frameworks, model SDKs, browser, storage, queue, graph store, memory store, export target, and HTTP clients.

## Non-Goals

- This feature does not integrate any concrete agent framework, model SDK, UI, queue, store, browser, export target, or production repair automation.
- This feature does not let memory, graph, or agent reasoning satisfy publication evidence.
