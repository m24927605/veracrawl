# Feature Specification: Live Evidence And Verification Runtime

**Feature Branch**: `047-live-evidence-verification-runtime`
**Status**: Planned - not implemented
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Build live evidence packets, evidence anchors, verification decisions, conflict
records, contradiction records, and review refs for extraction candidates.

## Scope

- Evidence packet builder over raw-to-normalized anchors.
- Verification decision runtime.
- Conflict and contradiction handling.
- Review refs and negative publication gate checks.
- Replay completeness for evidence-impacting actions.

## Dependencies

- Blocks: 048, 050, 051, 052, 054.
- Requires: 046.

## Completion Gate

Outputs cannot publish without source-backed evidence, verification, policy, and
replay refs. Missing, stale, contradictory, graph-only, or memory-only evidence
fails deterministically.

## Non-Goals

- Does not implement export destinations.
- Does not treat graph, memory, or AI reasoning as source evidence.
