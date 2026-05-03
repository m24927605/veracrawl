# Research: Real Agent And Model Adapter Runtime

## Decision 1: Runtime Composition Uses Ports, Not SDK Imports

The integrated runtime will accept `ModelProviderPort` and `AgentRuntimePort`
bindings. Core code can construct canonical `ModelRequest`, `ModelResponse`,
`AgentRunRequest`, `AgentRunResult`, and trace records from port results, but it
must not import concrete model SDKs, provider clients, or agent frameworks.

Rationale:

- It preserves the framework-neutral VeraCrawl core required by the constitution.
- It lets CLI/runtime composition load OpenAI Agent SDK, LangChain, LangGraph,
  CrewAI, AutoGen, Semantic Kernel, OpenAI-compatible endpoints, local model
  runtimes, or future adapters without changing core packages.
- It gives tests a clean import-boundary assertion.

Rejected alternative:

- Import optional SDKs in `veracrawl.agents`. This would make the core unstable,
  hard to install, and would persist framework choices in the wrong layer.

## Decision 2: Unavailable External SDKs Are `needs_review`

External adapters may be configured for SDK/framework families, but a missing
package, missing credentials, or missing wrapper callable cannot be counted as
an operational pass. The runtime returns `needs_review` with explicit
unavailable runtime refs.

Rationale:

- Earlier adapter gates already forbid pretending that contract descriptors are
  live operations.
- This gives operators an honest boundary between "runtime adapter executed" and
  "adapter has a configured contract only".

Rejected alternative:

- Treat external SDK absence as success when a deterministic fixture exists. That
  would fake target capability and break the user's hard requirement.

## Decision 3: Local Runtime Adapters Provide Testable Real Execution

The test suite uses a local deterministic model provider adapter and a native
VeraCrawl agent runtime adapter as real port implementations. They are adapter
modules, dynamically loaded by CLI, and return canonical requests/results/traces
without claiming that external provider accounts or framework SDKs are present.

Rationale:

- The runtime can be tested without network credentials.
- It proves the integrated planning/extraction/repair path executes through
  ports rather than contract-only records.
- It remains honest about external SDK availability.

Rejected alternative:

- Make the success fixture depend on paid or networked model accounts. That would
  make the deterministic gate flaky and not runnable in local CI.

## Decision 4: Planning, Extraction, And Repair Are Required Agent Turns

A passing row 049 report must include planner, extractor, and repair/drift agent
turn refs. This proves the runtime is useful to rows 050/051 and not merely an
isolated provider ping.

Rationale:

- The roadmap completion gate explicitly mentions planning, extraction, and
  repair.
- These three roles cover the main AI decisions needed before multi-agent
  orchestration.

Rejected alternative:

- Only call a model completion once. That would not demonstrate agent runtime
  usefulness for VeraCrawl workflows.
