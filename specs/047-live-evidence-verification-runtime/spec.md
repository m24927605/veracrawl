# Feature Specification: Live Evidence And Verification Runtime

**Feature Branch**: `047-live-evidence-verification-runtime`
**Created**: 2026-05-03
**Status**: Active
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Build live evidence packets, evidence anchors, manifests, verification
decisions, review refs, conflict/contradiction diagnostics, and replay refs for
schema extraction candidates without allowing graph, memory, or AI reasoning to
replace source evidence.

## User Stories

### US1 - Build Source-Backed Evidence For Candidates (P1)

As a verifier, I need every candidate field to be backed by source evidence
anchors, evidence packet refs, evidence manifest refs, policy/privacy refs,
command/event/outbox refs, and replay refs.

**Independent Test**: Run `live-evidence-verification-success` through the CLI
and assert a passing report with source-backed evidence, verification, review,
and replay refs.

### US2 - Block Non-Source Evidence (P1)

As a reviewer, I need missing, stale, contradictory, graph-only, memory-only, or
agent-reasoning-only evidence to fail or enter needs-review deterministically.

**Independent Test**: Run all negative live-evidence fixtures and assert typed
failure diagnostics with no publication refs.

## Functional Requirements

- **FR-001**: Core live evidence runtime MUST receive schema extraction refs and
  candidate objects through explicit inputs; it MUST NOT import concrete source,
  browser, model, agent framework, storage, queue, export, or site-specific
  scraper adapters.
- **FR-002**: Passing reports MUST include schema extraction report refs,
  extraction candidate refs, normalized document refs, source anchor refs,
  evidence coverage refs, evidence packet refs, evidence anchor refs, evidence
  manifest refs, verification decision refs, review decision refs, freshness
  refs, policy refs, privacy lifecycle refs, command/event/outbox refs, and
  replay refs.
- **FR-003**: Passing evidence MUST include source evidence anchors. Graph,
  memory, and AI reasoning refs are allowed only as diagnostic context and MUST
  NOT satisfy source evidence coverage.
- **FR-004**: Missing source anchors, stale evidence, contradictory evidence,
  graph-only evidence, memory-only evidence, verification conflict, publication
  gate bypass, and replay mismatch MUST fail or enter needs-review with typed
  diagnostics.
- **FR-005**: This runtime MUST NOT emit published output, output manifest,
  export, delivery, or publication refs.

## Dependencies

- Blocks: 048, 050, 051, 052, 054.
- Requires: 046.

## Completion Gate

Outputs cannot publish without source-backed evidence, verification, policy, and
replay refs. Missing, stale, contradictory, graph-only, memory-only, or
agent-reasoning-only evidence fails deterministically.

## Non-Goals

- Does not implement export destinations.
- Does not publish outputs.
- Does not treat graph, memory, or AI reasoning as source evidence.
