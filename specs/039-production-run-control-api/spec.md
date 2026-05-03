# Feature Specification: Production Run Control API

**Feature Branch**: `039-production-run-control-api`
**Status**: Planned - not implemented
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Make projects/sites, crawl objectives, plans, approvals, run lifecycle,
budgets, policy snapshots, and run replay executable beyond deterministic
target-runtime fixtures.

## Scope

- Production project/site/objective/plan/run API or CLI surfaces.
- Approval, pause, resume, cancel, fail, and complete commands.
- Budget and policy snapshot refs attached to runs.
- Replayable command/event lifecycle for run state transitions.

## Dependencies

- Blocks: 040, 041, 044, 049, 054.
- Requires: 038.

## Completion Gate

A real production run can be created, approved, blocked, resumed, cancelled, and
replayed through canonical commands/events without direct mutation or hidden
state.

## Non-Goals

- Does not implement live HTTP/browser acquisition.
- Does not implement production worker scaling.
