# Implementation Plan: Top Ecommerce Live AI Benchmark

**Branch**: `065-top-ecommerce-live-ai-benchmark` | **Date**: 2026-05-04 | **Spec**: `specs/065-top-ecommerce-live-ai-benchmark/spec.md`  
**Input**: Feature specification from `specs/065-top-ecommerce-live-ai-benchmark/spec.md`

## Summary

Add a Spec Kit benchmark corpus for three major Taiwan ecommerce homepages and
three major United States ecommerce homepages. Reuse the row 055 live public
corpus runner and row 056 real-world AI agent runner so the experiment proves
policy-gated live acquisition plus framework-neutral hosted LLM/model and agent
trace participation without introducing site-specific scraper code.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: Existing VeraCrawl contracts, CLI, live HTTP runtime,
model-provider ports, native agent runtime, OpenAI Responses adapter  
**Storage**: Local run artifacts under `.veracrawl-real-runs/` and fixture
oracles under `tests/fixtures/`  
**Testing**: pytest, ruff, mypy, registry validation, live CLI validation,
Docker-backed pytest  
**Target Platform**: Local/dev production benchmark runner  
**Project Type**: Python CLI/library  
**Performance Goals**: One target request and one robots request per site for
the public homepage corpus; 24 AI decisions for six passing sites  
**Constraints**: No robots bypass, no login, no anti-bot evasion, no
site-specific scraper modules, no core coupling to model SDKs or agent
frameworks  
**Scale/Scope**: Six large ecommerce homepage targets and one hosted OpenAI AI
benchmark run  
**VeraCrawl Owner Services**: fetch, agents, evidence/verify, review_replay,
ops, policy  
**Canonical Contracts**: `RealWorldBenchmarkCorpusManifest`,
`RealWorldBenchmarkSiteSpec`, `RealWorldBenchmarkRunReport`,
`RealWorldAIAgentBenchmarkManifest`, `RealWorldAIAgentDecisionTrace`,
`RealWorldAIAgentExtractionCandidate`, `ModelCallTrace`,
`AgentActionTrace`, `ToolCallTrace`, `ContextBundleTrace`  
**Replay/Artifact Impact**: Public corpus observations and AI decisions must
include artifact refs, content hashes, command/event/outbox refs, and replay
bundle refs  
**Security/Policy Impact**: Robots preflight, origin allowlists,
private-network denial, prompt-context policy refs, raw prompt/response
redaction, and no direct publication

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; no one-off
  scraper assumptions are introduced.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral; the OpenAI provider is isolated
  behind `ModelProviderPort`.
- [x] Low coupling/high cohesion boundaries are explicit through existing ports,
  commands, events, typed results, and owner services.
- [x] Evidence, verification, publication-gate, replay, and artifact lineage are
  defined for affected outputs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle,
  retention, and export/withdrawal gates inherit rows 055 and 056.
- [x] Fixture/oracle tests and registry tests are planned before implementation.
- [x] Target architecture is not weakened due to schedule pressure.

## Project Structure

```text
specs/065-top-ecommerce-live-ai-benchmark/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/top-ecommerce-live-ai-benchmark.md
└── tasks.md

tests/fixtures/
├── top-ecommerce-public-corpus/
└── top-ecommerce-ai-agent-corpus/

src/veracrawl/contracts/registry.py
tests/contract/
tests/integration/
README.md
AGENTS.md
docs/
```

**Structure Decision**: Reuse existing runtime and CLI modules. The only source
code changes are fixture registry and tests proving fixture materialization.

## Complexity Tracking

No constitution violations.
