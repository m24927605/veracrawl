# Implementation Plan: Multi-Agent Orchestration And Repair Runtime

**Branch**: `050-multi-agent-orchestration-repair-runtime` | **Date**: 2026-05-03 | **Spec**: `specs/050-multi-agent-orchestration-repair-runtime/spec.md`
**Input**: Feature specification from `/specs/050-multi-agent-orchestration-repair-runtime/spec.md`

## Summary

Implement the row 050 runtime gate by upgrading the existing framework-neutral
multi-agent repair spine into a production runtime slice tied to row 049 real
agent/model adapter execution and row 047 live evidence. The runtime coordinates
planner, frontier, fetch-analysis, extractor, verifier, drift, memory, and ops
roles through explicit handoffs, controlled tool refs, owner-service command
refs, coordination decisions, repair signals, review escalation, policy refs,
and replay refs.

## Technical Context

**Language/Version**: Python 3.12 validation, package supports Python >=3.11  
**Primary Dependencies**: pydantic, existing VeraCrawl contracts/runtime helpers  
**Storage**: No concrete storage in core; deterministic refs and fixture artifacts  
**Testing**: pytest, ruff, mypy, Spec Kit prerequisite checks, Docker-backed pytest gate  
**Target Platform**: Python CLI/runtime package  
**Project Type**: single Python package  
**Performance Goals**: fixture CLI loop completes under deterministic test thresholds  
**Constraints**: general-purpose AI agent crawler, low coupling/high cohesion, framework-neutral core, agents cannot mutate canonical stores directly  
**Scale/Scope**: target-architecture multi-agent repair slice for crawl, extraction, and drift repair  
**VeraCrawl Owner Services**: agents, evidence, verify, review_replay, control, ops, tests  
**Canonical Contracts**: MultiAgentWorkflow, AgentHandoff, CoordinationDecision, DriftRepairSignal, MultiAgentRepairReport, MultiAgentFixtureManifest, AgentModelAdapterRuntimeReport, LiveEvidenceVerificationRuntimeReport  
**Replay/Artifact Impact**: agent action traces, handoff refs, tool call refs, owner command refs, repair evidence refs, command/event/outbox refs, replay bundle refs  
**Security/Policy Impact**: tool policy, owner-service boundary, agent reasoning as non-evidence, prompt context policy, review escalation, loop budget

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; no one-off scraper assumptions are introduced.
- [x] Python remains the implementation language unless a constitution amendment changes it.
- [x] Agent runtime remains framework-neutral; model SDKs and agent frameworks are isolated behind replaceable adapters.
- [x] Low coupling/high cohesion boundaries are explicit through ports, commands, events, typed results, and owner services.
- [x] Evidence, verification, publication, replay, and artifact lineage are defined for affected outputs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and export/withdrawal gates are defined where applicable.
- [x] Command payload schemas, event payload schemas, state transitions, fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

```text
specs/050-multi-agent-orchestration-repair-runtime/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/multi-agent-orchestration-runtime.md
├── quickstart.md
└── tasks.md

src/veracrawl/contracts/{agent.py,enums.py,registry.py}
src/veracrawl/agents/orchestration.py
src/veracrawl/review_replay/agents.py
src/veracrawl/cli/agents.py
tests/contract/test_multi_agent_contracts.py
tests/contract/test_multi_agent_contract_registry.py
tests/unit/test_multi_agent_orchestration.py
tests/unit/test_multi_agent_repair_boundary.py
tests/unit/test_multi_agent_replay.py
tests/integration/test_multi_agent_fixtures.py
tests/fixtures/{multi-agent,crawl-repair,extraction-repair,...}/
```

**Structure Decision**: extend the existing multi-agent owner package because
the earlier 011 spine already owns workflow, handoff, coordination, repair
signal, and replay primitives. Row 050 adds production dependency refs and
runtime acceptance gates rather than creating a parallel abstraction.

## Complexity Tracking

No constitution violations.
