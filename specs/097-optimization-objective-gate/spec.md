# Feature Specification: Optimization Objective Gate

**Feature Branch**: `097-optimization-objective-gate-attempt`
**Created**: 2026-05-06
**Status**: Implemented
**Input**: User description: "End-to-end VeraCrawl optimization must prove shortest crawl/search time, highest extraction and intent accuracy, and lowest LLM/API/browser cost while preserving a general-purpose AI agent crawler. Fill the remaining Spec Kit gap after specs 080-096 by materializing an OptimizationScore formula, agent observe/think/act/verify evidence, deterministic/LLM boundaries, replay refs, negative fixtures, tests, and a release gate. Do not push remote."

## Constitution Alignment *(mandatory)*

- **General-purpose crawler impact**: This feature does not add a site-specific scraper, fixed selector pipeline, browser automation demo, or vertical workflow. It adds a reusable objective-score contract and agent decision-loop gate that can evaluate any crawler optimization profile across URL frontier, DOM understanding, extraction, dedupe, ranking, cost, recovery, and evaluation signals from specs 080-096.
- **Target/V1 boundary**: This is post-079 crawler intelligence optimization target-architecture work layered after specs 080-096. It does not modify the production-grade closure meaning of specs 069-075 and does not expand V1 acceptance beyond documented V1 profiles. It references `docs/README.md`, `docs/01-product-definition.md`, `docs/02-production-architecture.md`, `docs/06-agent-system-design.md`, `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md`.
- **Evidence and replay impact**: Adds replayable contracts for objective-score reports, agent observe/think/act/verify loop evidence, and an aggregate optimization objective release gate. Passing reports require policy decision refs, command refs, event cursor refs, outbox refs, replay bundle refs, lower optimization regression gate refs, metric refs, and algorithm recommendation refs.
- **Safety and policy impact**: The gate must fail if the optimization claim depends on CAPTCHA solving, login-wall bypass, WAF evasion, unsafe browser escalation, raw secrets, prompt-injection-tainted LLM output as evidence, missing policy refs, or missing replay refs. LLM fallback is allowed only as a bounded proposal or structured fallback with deterministic validation and source evidence.
- **Required reference docs**: `docs/README.md`, `docs/01-product-definition.md`, `docs/02-production-architecture.md`, `docs/06-agent-system-design.md`, `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `specs/080-crawler-intelligence-optimization-roadmap/spec.md`, `specs/081-focused-frontier-scoring/spec.md`, `specs/082-dom-page-understanding/spec.md`, `specs/083-extractor-fallback-confidence/spec.md`, `specs/084-canonical-dedupe-identity/spec.md`, `specs/085-recommendation-ranking-runtime/spec.md`, `specs/086-cost-recovery-evaluation-gates/spec.md`, `specs/087-crawler-optimization-runtime-wiring/spec.md`, and `specs/088-096` owner integration specs.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Objective Score Is Computable And Replayable (Priority: P1)

An operator needs a single, replayable report that proves whether an optimization run is faster, more accurate, and cheaper according to the approved weighted formula, without accepting a proxy such as "tests passed" or "metrics exist".

**Why this priority**: Without a concrete objective score, specs 080-096 provide useful lower-level evidence but do not prove the user's end-to-end optimization target.

**Independent Test**: Build an `OptimizationObjectiveScore` from deterministic metric slices, cost, latency, dedupe, intent, freshness, policy refs, command/event/outbox refs, replay refs, and algorithm refs. The report passes only when the computed score matches the formula and threshold and all replay-critical refs exist.

**Acceptance Scenarios**:

1. **Given** complete metric and replay refs, **When** the objective-score report is validated, **Then** it records the exact score formula, component values, weighted score, threshold, algorithm refs, and a `pass` completion result.
2. **Given** a low objective score, missing replay refs, missing policy refs, missing algorithm refs, or formula mismatch, **When** validation runs, **Then** the report is `fail` or validation rejects it with typed diagnostics.

---

### User Story 2 - Agent Decision Loop Is Bounded And Evidence-Backed (Priority: P1)

An architect needs to know that AI agent browsing decisions used observe/think/act/verify with confidence threshold and stop conditions, while deterministic algorithms remained responsible for scoring, dedupe, canonicalization, budget, retry, validation, and release gates.

**Why this priority**: The user explicitly requested stronger agent decision ability without allowing wasteful LLM browsing or using LLM output as evidence.

**Independent Test**: Build `AgentDecisionLoopEvidence` records for pass and negative cases. Passing evidence requires observe, think, act, verify, stop condition, confidence threshold, deterministic decision refs, bounded LLM fallback refs if used, policy refs, command/event/outbox refs, model/tool trace refs, and replay bundle refs.

**Acceptance Scenarios**:

1. **Given** a complete decision trace with confidence above threshold, stop condition, deterministic decision refs, and replay refs, **When** validation runs, **Then** the decision-loop evidence passes.
2. **Given** missing observe/think/act/verify refs, confidence below threshold, missing stop condition, LLM output used as evidence, or missing deterministic decision refs, **When** validation runs, **Then** the evidence fails with diagnostics.

---

### User Story 3 - Release Gate Aggregates Objective, Agent, And Lower Optimization Evidence (Priority: P2)

An owner service needs a single release gate that blocks "better/faster/cheaper" claims unless lower integration reports from 089-096, objective-score reports, agent decision-loop evidence, and replay refs all pass.

**Why this priority**: A final optimization claim must aggregate lower evidence and prevent false readiness from deterministic fixtures or incomplete lower gates.

**Independent Test**: Build an `OptimizationObjectiveReleaseGate` from passing lower regression gates, objective-score reports, agent loop evidence, metric refs, policy refs, command/event/outbox refs, replay refs, and negative fixtures. The gate passes only with complete lower and objective evidence.

**Acceptance Scenarios**:

1. **Given** passing 096 regression gate refs, passing objective reports, passing agent loop evidence, and complete replay refs, **When** the release gate is evaluated, **Then** it passes and records the optimization claim scope.
2. **Given** missing 096 lower gate refs, failed objective score, failed agent loop evidence, missing replay refs, missing policy refs, or LLM-only evidence, **When** the release gate is evaluated, **Then** it fails and identifies the blocked evidence refs.

---

### User Story 4 - Documentation And Roadmap Stay Consistent (Priority: P3)

Future Codex runs and release audits need the optimization roadmap to name 097 as the final end-to-end objective gate after specs 080-096.

**Why this priority**: The repository already constrains production-grade and optimization spec sequencing. The roadmap must not imply 096 is sufficient for the user's complete objective.

**Independent Test**: Inspect `AGENTS.md`, `docs/08-build-roadmap.md`, `specs/038-production-runtime-closure/spec.md`, `specs/068-production-grade-crawler-closure-roadmap/spec.md`, and `specs/080-crawler-intelligence-optimization-roadmap/spec.md` for explicit 097 references.

**Acceptance Scenarios**:

1. **Given** the optimization roadmap docs, **When** a reader searches for specs 080-097, **Then** 097 is described as the end-to-end objective/agent decision release gate after 096.

### Edge Cases

- Missing command, event cursor, outbox, replay bundle, artifact hash, model trace, tool trace, or policy decision refs must block a pass claim.
- Objective-score reports with component values outside 0.0 to 1.0 or formula mismatch must be rejected.
- Objective-score reports with excellent latency/cost but poor extraction or intent accuracy must not pass if below threshold.
- Agent evidence with high confidence but no stop condition must fail.
- Agent evidence that treats LLM output as source evidence must fail.
- LLM fallback may be recorded only when deterministic extractors or heuristics are insufficient and the fallback is bounded by schema validation, field validation, policy refs, source evidence refs, and replay refs.
- A gate supplied with deterministic fixture reports can pass for the recorded validation corpus only; it must not claim arbitrary live ecommerce coverage unless live/authorized/browser/deep-crawl lower reports exist.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define an `OptimizationObjectiveScore` contract that records component metrics, weights, exact formula ref, computed score, pass threshold, completion result, diagnostics, algorithm recommendation refs, metric refs, policy refs, command refs, event cursor refs, outbox refs, artifact refs, and replay bundle ref.
- **FR-002**: System MUST compute the objective score using:

  ```text
  OptimizationScore =
    0.35 * extraction_accuracy +
    0.25 * intent_match_precision +
    0.15 * crawl_success_rate +
    0.10 * dedupe_quality +
    0.10 * freshness -
    0.03 * normalized_latency -
    0.02 * normalized_cost
  ```

- **FR-003**: System MUST reject or fail score reports when component values are outside 0.0 to 1.0, score formula refs are missing, computed score differs from component values and weights, score is below threshold, required metric refs are missing, required replay refs are missing, or policy refs are missing.
- **FR-004**: System MUST define `AgentDecisionLoopEvidence` for observe/think/act/verify decisions, including confidence threshold, stop condition, deterministic decision refs, bounded LLM fallback refs, model/tool trace refs, policy refs, command refs, event cursor refs, outbox refs, and replay bundle ref.
- **FR-005**: System MUST fail agent loop evidence when observe, think, act, verify, confidence threshold, stop condition, deterministic decision refs, replay refs, or policy refs are missing.
- **FR-006**: System MUST fail agent loop evidence if LLM output is used as source evidence or as an unvalidated publication/release claim.
- **FR-007**: System MUST define `OptimizationObjectiveReleaseGate` that aggregates 096 lower regression gate refs, objective-score report refs, agent decision-loop evidence refs, algorithm recommendation refs, metric refs, policy refs, command refs, event cursor refs, outbox refs, artifact refs, and replay bundle refs.
- **FR-008**: System MUST pass the objective release gate only when all required lower regression gates, objective scores, agent loop evidence, policy refs, replay refs, and metric refs are present and passing.
- **FR-009**: System MUST expose adapter-free Python runtime helpers for computing objective scores, recording agent loop evidence, and evaluating the objective release gate.
- **FR-010**: System MUST add command and event registry entries for recording objective-score reports, agent decision-loop evidence, and objective release gates.
- **FR-011**: System MUST add negative fixture/oracle refs for low score, formula mismatch, missing replay refs, missing policy refs, missing lower gate refs, missing observe/think/act/verify refs, low confidence, missing stop condition, and LLM-only evidence.
- **FR-012**: System MUST update roadmap docs and AGENTS guidance so 097 is visible as the end-to-end optimization objective gate after specs 080-096.
- **FR-013**: System MUST provide a deterministic CLI evidence command that materializes 096 lower regression gate evidence, 097 objective score, 097 agent loop evidence, 097 objective release gate, and an audit summary in one run without live network, browser, model SDK, storage, queue, or adapter dependencies.

### VeraCrawl Contract Requirements *(mandatory for crawler/platform changes)*

- **VC-001**: System MUST preserve general-purpose crawling capability and avoid feature-specific assumptions that block other websites, source patterns, schemas, or domains.
- **VC-002**: Owner services affected are ops/replay/release-gate services consuming optimizer, scheduler, normalize, extract/verify, dedupe, ranking, cost/cache, and drift/recovery evidence through typed refs.
- **VC-003**: New contracts MUST be command/event backed and replayable without importing concrete storage, queue, browser, model SDK, or agent framework internals.
- **VC-004**: Objective and agent evidence MUST not publish extracted records. They evaluate optimization readiness and must reference source-backed lower reports for publication-relevant claims.
- **VC-005**: Security and policy gates MUST block unsafe browser escalation, credential misuse, prompt-injection-tainted evidence, CAPTCHA solving, login-wall bypass, paywall bypass, WAF evasion, raw secret persistence, and missing policy refs.
- **VC-006**: Contract, unit, replay, registry, import-boundary, and negative tests MUST be added before implementation is marked complete.

### Key Entities *(include if feature involves data)*

- **OptimizationObjectiveScore**: Weighted objective-score report for one validation corpus, profile, or run slice. Includes component scores, weights, computed score, threshold, algorithm refs, metrics, policy decisions, command/event/outbox refs, artifact refs, replay refs, diagnostics, completion result, and failure type.
- **AgentDecisionLoopEvidence**: Replayable observe/think/act/verify decision loop evidence. Includes objective/run refs, phase refs, confidence and threshold, stop condition, deterministic decision refs, LLM fallback boundary refs, model/tool traces, policy refs, command/event/outbox refs, artifact refs, replay refs, diagnostics, completion result, and failure type.
- **OptimizationObjectiveReleaseGate**: Aggregate release gate that proves the end-to-end optimization claim for a recorded corpus by requiring passing lower 096 regression gates, objective-score reports, agent loop evidence, metric refs, policy refs, command/event/outbox refs, artifact refs, and replay refs.

### Non-Goals *(mandatory)*

- This feature does not add new website-specific crawl rules, manual product URL lists, fixed selectors for specific domains, or single-site crawler behavior.
- This feature does not add a concrete LLM SDK, browser engine, queue, storage client, or agent framework dependency to core packages.
- This feature does not replace specs 081-096 lower algorithms; it aggregates and verifies their evidence.
- This feature does not claim arbitrary live ecommerce completion from deterministic fixtures alone.
- This feature does not implement learning-to-rank training. It preserves readiness through feature refs and score evidence.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential theft, login-wall circumvention, WAF evasion, stealth automation, ban-avoidance proxy tactics, or bypassing robots, terms, or customer authorization policy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Contract tests validate `OptimizationObjectiveScore`, `AgentDecisionLoopEvidence`, and `OptimizationObjectiveReleaseGate` pass and fail behavior for complete and negative fixtures.
- **SC-002**: Runtime unit tests prove the exact objective score formula, threshold behavior, failure diagnostics, and release gate aggregation.
- **SC-003**: Replay tests prove objective-score, agent-loop, and release-gate reports require command refs, event cursor refs, outbox refs, artifact refs, policy refs, and replay bundle refs.
- **SC-004**: Registry tests prove new contracts, commands, events, and fixture oracle refs are discoverable by VeraCrawl contract tooling.
- **SC-005**: Import-boundary tests prove new runtime code does not import concrete model SDKs, browser libraries, storage clients, queue clients, benchmark modules, or agent framework packages.
- **SC-006**: Roadmap docs name specs 080-097 and describe 097 as the end-to-end optimization objective/agent release gate after 096.
- **SC-007**: Targeted tests, contract validation, lint/type checks where available, and the feasible full test suite pass before local commit.
- **SC-008**: `veracrawl-crawler-optimization run-objective-gate` or its module equivalent writes `optimization_regression_release_gate.json`, `optimization_objective_score.json`, `agent_decision_loop_evidence.json`, `optimization_objective_release_gate.json`, and `summary.json` for deterministic evidence runs.

## Assumptions

- Existing specs 081-096 already provide lower-level algorithm contracts, runtime services, owner-service integration refs, metrics, and regression gates.
- The objective threshold defaults to 0.82 for deterministic local fixtures unless a future policy profile supplies a stricter threshold.
- Component values are normalized to 0.0 through 1.0 before score computation; latency and cost are penalties, not rewards.
- LLM fallback is a bounded decision aid. Source-backed evidence and deterministic validation remain authoritative for pass claims.
- Release-gate pass scope is limited to the recorded validation corpus and supplied lower gate reports.

## Implementation Closure

- Implemented `OptimizationObjectiveScore`, `AgentDecisionLoopEvidence`, and
  `OptimizationObjectiveReleaseGate` contracts with typed diagnostics, policy
  refs, command/event/outbox refs, artifact refs, and replay refs.
- Implemented adapter-free objective score, agent-loop evidence, and release
  gate helpers in `src/veracrawl/optimization/objective_gate.py`.
- Implemented replay completeness helpers in
  `src/veracrawl/review_replay/crawler_optimization_objective_gate.py`.
- Registered objective contracts, commands, events, target area coverage, and
  positive/negative fixture oracle refs in `src/veracrawl/contracts/registry.py`.
- Updated `AGENTS.md`, `docs/08-build-roadmap.md`,
  `specs/038-production-runtime-closure/spec.md`,
  `specs/068-production-grade-crawler-closure-roadmap/spec.md`, and
  `specs/080-crawler-intelligence-optimization-roadmap/spec.md` to name 097 as
  the final end-to-end optimization objective gate after 096.
- Validation passed on 2026-05-06: targeted objective gate suite
  `21 passed`, `ruff check`, `mypy` on objective modules/contracts/registry,
  full `pytest` `1425 passed, 5 skipped`, and `git diff --check`.
- Extended implementation with deterministic objective evidence runner support:
  `veracrawl-crawler-optimization run-objective-gate` materializes 096 and 097
  JSON evidence artifacts and a summary from local fixtures.
- Evidence runner validation passed on 2026-05-06: targeted objective/evidence
  suite `25 passed`, CLI command wrote 096/097 evidence artifacts to
  `/private/tmp/veracrawl-optimization-objective-gate-success`, `ruff check`,
  `mypy` on six affected files, full `pytest` `1429 passed, 5 skipped`, and
  `git diff --check`.
