# Feature Specification: Optimization Regression Release Gate

**Feature Branch**: `088-optimization-owner-integration`
**Created**: 2026-05-06
**Status**: Implemented
**Input**: Spec 088 approved integration roadmap row 096.

## Purpose

Aggregate lower integration evidence from specs 089-095 into a
release-blocking optimization regression gate.

## Constitution Alignment

- Regression release gates supplement, but do not replace, production-grade
  closure specs 069-075.
- Passing requires parsed lower integration evidence, not arbitrary string refs.
- Missing policy, evidence, replay, metrics, or lower reports fail the gate.

## Requirements

- **FR-096-001**: System MUST expose an optimization regression release gate
  with lower integration refs, metric refs, replay refs, false-ready guards,
  diagnostics, and pass/fail status.
- **FR-096-002**: System MUST require present lower reports for scheduler, DOM,
  extraction, dedupe, ranking, cost/cache, and drift/recovery integration.
- **FR-096-003**: System MUST fail on quality regression, duplicate regression,
  ranking regression, cost regression, latency regression, unsafe recovery,
  stale cache reuse, source-limited fabrication, and replay gaps.
- **FR-096-004**: System MUST record validation commands and results in
  `tasks.md` before implementation closure.

## Completion Gate

Release-gate tests prove complete lower integration evidence passes and all
required negative fixtures fail with typed diagnostics.

## Non-Goals

- This spec does not claim every target website is crawlable.
- This spec does not change the aggregate 075 production-grade release gate.
