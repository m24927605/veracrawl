# Research: VeraCrawl Target Architecture Foundation

## Decision: Python 3.11+ With Pydantic v2 Contract Models

**Rationale**: VeraCrawl is constitutionally a Python product. Python 3.11+ gives stable typing, dataclass, enum, exception group, and packaging support without requiring experimental runtime features. Pydantic v2 provides executable validation and JSON Schema export for the contracts in `docs/07-data-contracts.md`, which lets tests verify contract registry completeness instead of treating contracts as static prose.

**Alternatives considered**:

- Plain dataclasses only: rejected because JSON Schema export and structured validation would become custom infrastructure before the foundation exists.
- Marshmallow or ad hoc schema dictionaries: rejected because this increases duplicated validation logic and weakens type integration.
- Python 3.9 runtime baseline: rejected for target architecture planning because later typing and validation work would be constrained by an old runtime.

## Decision: Use `typing.Protocol` For Ports

**Rationale**: Ports must be owned by VeraCrawl and must not import concrete infrastructure, model SDK, browser library, storage client, queue client, or agent framework types. `typing.Protocol` provides structural interfaces that can be implemented by both in-memory foundation adapters and later production adapters without coupling core packages to concrete classes.

**Alternatives considered**:

- Abstract base classes for every port: acceptable for some ports, but rejected as the default because it forces inheritance where structural conformance is enough.
- Framework-native base classes: rejected because it would violate the framework-neutral architecture rule.
- Direct function callbacks: rejected because they do not carry enough typed interface structure for contract tests and future adapter suites.

## Decision: Keep Foundation Storage In-Memory And Fixture-File Based

**Rationale**: This feature proves contracts, owner boundaries, policy gates, replay validation, and adapter conformance. It does not implement production persistence. In-memory repositories and deterministic JSON/YAML fixtures are enough to test owner-service mutation rules, event append behavior, registry consistency, and replay missing-ref failures.

**Alternatives considered**:

- Add Postgres/object store/queue adapters now: rejected for this feature because production infrastructure adapters need their own specs and acceptance gates.
- Persist only markdown contracts: rejected because the foundation must be executable and testable.

## Decision: Agent Framework Support Goes Through A VeraCrawl Adapter Contract

**Rationale**: VeraCrawl must support OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, and future frameworks without coupling core to them. The foundation therefore defines an `AgentRuntimePort` and conformance fixtures that map framework-native execution into VeraCrawl-owned `AgentRunRequest`, `AgentRunResult`, `AgentActionTrace`, `ModelCallTrace`, `ToolCallTrace`, `ContextBundleTrace`, `CommandEnvelope`, and `CommandResult` contracts. Framework-native state is diagnostic only and cannot become canonical state.

**Alternatives considered**:

- Pick one framework as the core runtime: rejected because it would make VeraCrawl less general and violate the constitution.
- Avoid framework adapters entirely: rejected because the user explicitly requires adapter compatibility with major agent frameworks.
- Store framework-native traces as replay source of truth: rejected because replay must use VeraCrawl contracts and stable refs.

## Decision: Initial Agent Conformance Fixtures Cover OpenAI Agent SDK And LangGraph

**Rationale**: The clarify session set OpenAI Agent SDK and LangGraph as the first executable conformance baseline. They exercise two important adapter shapes: model/tool SDK integration and graph/workflow-style orchestration. Other named frameworks are compatibility targets that must use the same adapter contract in later tasks.

**Alternatives considered**:

- Implement conformance for all named frameworks immediately: rejected for this foundation feature because it would obscure whether the adapter contract itself is correct.
- Use only fake adapters: rejected because the baseline must prove at least two representative framework shapes can map to VeraCrawl-owned contracts.

## Decision: Source Adapter Results Are Typed Natural Results

**Rationale**: Target docs require source adapters for HTTP, sitemap, RSS, browser snapshot, authorized session, API source, document source, file import, manual seed, and prior snapshot. Not all of these yield HTTP fetch artifacts. `SourceAdapterResult` must carry `result_type` values such as `fetch_result`, `discovered_links`, `session_state`, `api_payload`, `document_artifact`, `file_artifact`, `seed_plan`, `prior_snapshot_ref`, and `blocked_source` so non-fetch adapters do not fake `FetchResult` or `PageSnapshot`.

**Alternatives considered**:

- Treat every source as a fetch: rejected because it would corrupt replay semantics and violate `docs/07-data-contracts.md`.
- Create independent result classes with no shared envelope: rejected because policy, replay, idempotency, and event handling need a common canonical result surface.

## Decision: Foundation Acceptance Is Contract-First And Negative-Test Driven

**Rationale**: The minimum gate must prove registry consistency, no direct agent-framework core dependency, no direct cross-owner mutation, replay missing-ref failure, and policy-blocked fixture behavior. These tests prevent false completion while allowing later specs to implement actual crawler runtime behavior behind stable interfaces.

**Alternatives considered**:

- Happy-path skeleton only: rejected because it would not meet Staff-level readiness or constitution requirements.
- Manual checklist acceptance: rejected because the constitution requires executable contracts and tests.

## Decision: Fixture Runner Starts With Foundation Fixtures, Not Full Benchmark Suite

**Rationale**: `docs/11-target-testing-and-acceptance.md` defines the full target benchmark suite. This foundation must establish the runner contract and include deterministic fixture stubs for fetch-like success, non-fetch success, policy-blocked source, and replay-missing-ref failure. The full benchmark site suite is implemented by later profile specs.

**Alternatives considered**:

- Implement all benchmark sites in foundation: rejected because this feature is the foundation contract layer, not the full target crawler runtime.
- Defer fixture/oracle work: rejected because later implementation could not prove acceptance without stable fixture semantics.
