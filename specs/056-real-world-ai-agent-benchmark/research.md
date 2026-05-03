# Research: Real-World AI Agent Crawl Planning And Extraction Benchmark

## Decision 1: Compose Row 055 Live Public Corpus Before AI Decisions

**Decision**: The benchmark must first produce a passing `RealWorldBenchmarkRunReport` through row 055. AI decisions are only valid for passing site observations from that report.

**Rationale**: This prevents an AI-only trace from masking failed source acquisition. The source evidence and artifact lineage remain anchored in the already implemented public corpus gate.

**Alternatives Rejected**:

- Running AI planning against fixture text only: rejected because the user explicitly requires true public website crawl.
- Letting AI choose arbitrary public URLs: rejected because scope/robots/allowlist policy must remain deterministic and auditable.

## Decision 2: Use Existing Framework-Neutral Ports For All AI Behavior

**Decision**: Every model turn uses `ModelProviderPort.complete(ModelRequest)` and every agent turn uses `AgentRuntimePort.run(AgentRunRequest)`. CLI composition dynamically loads the default local model provider and VeraCrawl native agent adapter.

**Rationale**: This proves the core does not couple to OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, or any model SDK. External providers can replace the adapters without changing benchmark core.

**Alternatives Rejected**:

- Directly importing an external model SDK in core: rejected by constitution and AGENTS constraints.
- Adding a mandatory hosted LLM dependency for tests: rejected because CI and Docker-backed validation cannot depend on user credentials.

## Decision 3: Persist Structured Trace Contracts, Not Raw Prompts Or Framework State

**Decision**: Persist `ModelRequest`, `ModelResponse`, `ModelCallTrace`, `AgentRunRequest`, `AgentRunResult`, `AgentActionTrace`, `ToolCallTrace`, and `ContextBundleTrace` as structured JSON outputs. Raw prompt and raw response retention remains false.

**Rationale**: The benchmark must prove the AI path executed while preserving privacy, prompt-injection, and replay constraints.

**Alternatives Rejected**:

- Saving raw prompt/response as evidence: rejected because LLM output must not be source evidence and raw transcripts can leak data.
- Saving framework-native state: rejected because core state must remain framework-neutral.

## Decision 4: Source-Anchored Candidates, No Direct Publication

**Decision**: AI extraction candidates are represented by `RealWorldAIAgentExtractionCandidate` and must bind to source anchor refs, artifact refs, and content hash refs from the live site observation. Publication readiness is represented by evidence/verification/publication gate refs; direct published output refs fail this benchmark.

**Rationale**: The benchmark proves AI-assisted candidate generation without weakening evidence or publication guarantees.

**Alternatives Rejected**:

- Treating model output as extracted fact evidence: rejected because source evidence must come from crawled artifacts.
- Publishing benchmark candidates as outputs: rejected because row 056 is a proof gate, not an export/publication workflow.

## Decision 5: Negative Fixtures Are Contract-Level, Live Run Is Success Path

**Decision**: Deterministic tests cover negative scenarios by fixture/contract/runtime injection. The required live public corpus run uses the positive fixture and records results in `tasks.md`.

**Rationale**: Negative live public website tests would be flaky and potentially unsafe. Typed failure behavior can be proven without intentionally violating public site policies.

**Alternatives Rejected**:

- Forcing public websites into failure cases: rejected as unsafe and brittle.
- Skipping the live run: rejected by the user requirement.
