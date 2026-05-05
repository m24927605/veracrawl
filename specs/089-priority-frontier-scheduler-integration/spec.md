# Feature Specification: Priority Frontier Scheduler Integration

**Feature Branch**: `088-optimization-owner-integration`
**Created**: 2026-05-06
**Status**: Implemented
**Input**: Spec 088 approved integration roadmap row 089.

## Purpose

Connect runtime frontier optimization decisions from specs 081 and 087 to
scheduler-owned enqueue, block, retire, and stop-condition integration records.

## Constitution Alignment

- Preserve general-purpose crawling by scoring arbitrary URL candidates rather
  than site-specific selectors or product-only paths.
- Scheduler remains the owner of durable frontier decisions.
- Policy, budget, duplicate, and replay refs gate every integration outcome.
- No adapter, benchmark, browser, model SDK, or agent-framework imports are
  allowed in scheduler integration code.

## Requirements

- **FR-089-001**: System MUST map allowed frontier optimization decisions to
  scheduler enqueue integration records with score refs and priority values.
- **FR-089-002**: System MUST map denied, duplicate-risk, low-score, or
  exhausted-budget candidates to block, retire, or stop integration records.
- **FR-089-003**: System MUST preserve policy refs, command/event/outbox refs,
  score refs, and replay refs for every scheduler integration outcome.
- **FR-089-004**: System MUST reject integration records missing source anchors
  or replay refs before scheduler adoption.

## Completion Gate

Contract, unit, replay, and import-boundary tests prove scheduler integration
emits optimized enqueue/block/retire/stop records without benchmark or adapter
coupling.

## Non-Goals

- This spec does not replace durable scheduler lease semantics.
- This spec does not allow agents to mutate the scheduler directly.
