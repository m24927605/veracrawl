# Research: VeraCrawl Memory Kernel

## Decisions

### Decision 1: Memory Is Planning Context Only

Memory can guide planning, repair, and review, but it cannot satisfy publication evidence or replace source artifacts and anchors.

### Decision 2: Deterministic Fixture Runtime Before Production Stores

This slice proves contracts and policy/replay semantics with stable refs instead of a memory, vector, or search store.

### Decision 3: Retrieval Trace Is Mandatory

Every retrieval records retrieved refs, excluded refs, exclusion reasons, policy refs, freshness refs, index refs, tunnel refs, taint labels, and sanitized context refs.

### Decision 4: Cross-Scope Memory Requires Sanitized Tunnel

Cross-scope memory reuse requires authorization, policy refs, sanitized-only transfer, evidence anchoring, and taint exclusion rules.
