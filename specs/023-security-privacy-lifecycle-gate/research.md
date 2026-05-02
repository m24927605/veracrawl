# Research: Security Privacy Lifecycle Gate

## Decision: Canonical Security/Privacy Contracts Own Pass Semantics

Use VeraCrawl-owned contracts for policy checks, credential audits, prompt taint boundaries, lifecycle actions, projection cleanup, and gate reports.

**Rationale**: Security readiness must be replayable and framework-neutral. Vendor-native DLP, browser, vault, or cloud security state cannot become canonical state.

## Decision: Policy-Only Is Needs-Review

Policy refs alone show intent but do not prove credential isolation, prompt taint blocking, lifecycle propagation, or redacted replay completeness.

**Rationale**: The user explicitly prohibits fake completion. Security/privacy acceptance needs executable evidence and negative fixtures.

## Decision: Raw Secret Leakage Is A Deterministic Failure

Secret-like values in prompt/log/replay/artifact/trace/browser/model/agent-visible refs fail the gate.

**Rationale**: Target acceptance requires credential prompt leakage to remain zero across fixtures.

## Decision: Lifecycle And Projection Cleanup Are Same-Gate Requirements

Redaction, tombstone, delete, legal hold, retention, and projection cleanup refs are validated together.

**Rationale**: Privacy lifecycle is incomplete if derived projections retain stale or prohibited data.
