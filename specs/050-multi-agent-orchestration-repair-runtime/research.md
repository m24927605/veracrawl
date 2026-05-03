# Research: Multi-Agent Orchestration And Repair Runtime

## Decision 1: Build On The Existing Multi-Agent Spine

The repository already has framework-neutral `MultiAgentWorkflow`,
`AgentHandoff`, `CoordinationDecision`, `DriftRepairSignal`,
`MultiAgentRepairReport`, a CLI runner, fixtures, and replay tests. Row 050 will
extend these contracts with row 049 adapter runtime refs, row 047 evidence refs,
controlled tool refs, owner command refs, and replay bundle refs.

Rationale:

- Avoids duplicate orchestration models.
- Preserves established contract names and tests.
- Turns a deterministic spine into the production runtime gate required by the
  post-037 roadmap.

Rejected alternative:

- Create a second `MultiAgentOrchestrationReport`. That would split ownership
  and make later specs decide which report is authoritative.

## Decision 2: Passing Repair Requires Row 049 And Row 047 Refs

A passing multi-agent repair report must include the real agent/model adapter
runtime report ref and live evidence verification report ref. Agents may use
graph, memory, and reasoning as context, but source-backed evidence remains
mandatory for repair acceptance.

Rationale:

- Row 050 depends on 049 and 047.
- It prevents a multi-agent repair loop from acting on reasoning alone.
- It keeps rows 051/054 from inheriting a false capability claim.

Rejected alternative:

- Let orchestration pass without evidence refs and rely on later publication to
  catch it. That would make repair state itself misleading.

## Decision 3: Owner-Service Commands Gate Mutations

Coordination decisions may select repair proposals, but mutation is valid only
when represented by owner-service command refs. Direct agent store mutation is a
typed failure.

Rationale:

- This is the core safety boundary for AI agents.
- It preserves auditability, policy checks, and replay.

Rejected alternative:

- Let the orchestration runtime mutate durable state directly for convenience.
  That violates the constitution and cannot be replayed safely.

## Decision 4: Success Must Cover Crawl, Extraction, And Drift Repair

Row 050 adds dedicated success fixtures for crawl repair, extraction repair, and
drift/evidence repair. This prevents a single generic workflow from being used
as evidence that all repair categories work.

Rationale:

- The roadmap calls out crawl and extraction repair.
- Drift repair has different evidence and rollback expectations from frontier
  or extraction repair.
