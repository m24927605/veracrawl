# Research: VeraCrawl Target Crawl Runtime

## Decision: Use A Deterministic Local Runtime Fixture Harness

**Rationale**: Target architecture must be executable and repeatedly testable. Live Internet crawls are valuable later, but they introduce timing, availability, policy, and content drift that make acceptance non-deterministic. Local fixture observations and oracles let the runtime prove objective-to-output behavior, evidence, graph, export, replay, and policy closure without pretending that one website proves general-purpose capability.

**Alternatives considered**:

- Live multi-site crawl acceptance: rejected for deterministic CI and safety reasons.
- Mock-only report generation: rejected because it would not execute runtime state transitions or typed contract validation.
- Single website fixture: rejected because it violates the general-purpose crawler constraint.

## Decision: Add A Target Runtime Layer Instead Of Expanding Low-Level Runtime Spine

**Rationale**: Existing `control.runtime` already proves low-level command/event/source/evidence/publication/replay behavior. The target runtime should compose the product path across website patterns, AI recommendations, graph/export/operator reports, and negative fixtures. A new package keeps cohesion high and avoids turning the control runtime into a broad product acceptance module.

**Alternatives considered**:

- Put all behavior into `control.runtime`: rejected due to low cohesion and increasing blast radius.
- Put behavior inside CLI only: rejected because core runtime must be testable without CLI.
- Duplicate existing source/evidence/output contracts: rejected because existing contracts are canonical and registry-validated.

## Decision: Represent AI Behavior Through Framework-Neutral Recommendation Records

**Rationale**: The constitution requires AI to maximize crawl planning and repair, but VeraCrawl core cannot depend on OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, or any concrete framework. Deterministic recommendation records provide executable acceptance coverage for planning/repair while preserving adapter substitutability.

**Alternatives considered**:

- Add a concrete external agent SDK dependency: rejected by the framework-neutral agent boundary.
- Omit AI from target runtime: rejected because AI-assisted crawl planning and repair are core product capability.
- Persist framework-native state: rejected because replay requires VeraCrawl-owned canonical contracts.

## Decision: Use Per-Pattern Runtime Records And One Aggregate Report

**Rationale**: One aggregate run proves the system can coordinate multiple website patterns in a single objective. Per-pattern records let tests assert evidence, output, graph, policy, and replay refs for each pattern without relying on a hardcoded site.

**Alternatives considered**:

- One pass/fail report only: rejected because it would hide pattern-level gaps.
- Separate fixture run per pattern only: rejected because it would not prove a multi-pattern crawl objective.

## Decision: Failure Types Are Explicit Runtime Contract Values

**Rationale**: Negative fixtures must prove unsafe access, prompt injection, missing evidence, replay mismatch, partial export, and false completion cannot silently pass. Typed failure values make CLI, reports, tests, and registry validation precise.

**Alternatives considered**:

- Free-form diagnostic strings only: rejected because tests and operators need stable categories.
- Reuse product acceptance failure values only: rejected because target runtime failures include source, replay, AI repair, and export specifics.

## Decision: Register Target Runtime As A Materialized Target Area

**Rationale**: Specs 001-033 closed contract readiness and registry coverage. 034 adds a product runtime path that must also be visible in the contract registry, with commands/events/fixtures/test refs and no placeholder/follow-up refs.

**Alternatives considered**:

- Leave target runtime outside registry: rejected because it would bypass the acceptance mechanism.
- Register as planned/scaffolded: rejected because implementation must be executable and tested.
