# Research: Ops Console, Replay, And Observability Runtime

## Decision: Add A Row 053 Aggregate Instead Of Reusing Existing Gates

The repository already has a review/replay/ops console data surface and an
operational observability gate. Those prove useful lower-level contracts, but
roadmap row 053 requires one operator runtime connected to rows 048 and 052.

Rationale:

- Prevents a partial ops console or observability-only report from being labeled
  target ops runtime.
- Gives row 054 one stable operator runtime report for release gating.
- Keeps publication/export, worker orchestration, ops console, and
  observability owner boundaries intact.

Rejected alternative:

- Mark existing `OpsConsoleReport` plus `ObservabilityReport` as row 053
  complete. That would miss row 048/052 dependency proof and allow dashboard-only
  state to masquerade as operational readiness.

## Decision: Keep Runtime Deterministic And Adapter-Neutral

The runtime composes deterministic refs and existing deterministic runtime
helpers. It does not import UI frameworks, telemetry SDKs, queue clients, storage
clients, browser engines, model SDKs, agent frameworks, or site-specific
scrapers.

Rationale:

- Preserves low coupling and high cohesion.
- Keeps concrete dashboards and telemetry collectors as adapter work, not core
  state.
- Allows fixtures to prove replay semantics without external services.

## Decision: Fail Missing Dependency And Unsafe Operator Cases Explicitly

The negative set covers missing publication/export, missing worker
orchestration, missing ops console, missing observability, stale dashboard,
unresolved recovery, unsafe operator action, and replay mismatch.

Rationale:

- These are the ways row 053 could falsely claim operational completion.
- They map directly to missing canonical refs or unsafe unreviewed actions.
- The failures are typed so row 054 can consume them without string matching.
