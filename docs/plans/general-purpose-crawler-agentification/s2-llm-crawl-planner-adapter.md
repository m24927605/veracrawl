# s2 — Real LLM-driven `CrawlPlanner` adapter (replay-strict)

> **Framing (iter-4 demotion):** s2 ships the planner-side LLM
> adapter and the contract surface that makes a real model call
> reproducible. It is **not** a self-contained production deployment
> — live use also requires the upstream OpenAI / Anthropic v2
> provider adapters to populate `ProviderResponse.raw_response_ref`,
> which they do not today (`src/veracrawl/adapters/model_providers/
> openai_responses_v2.py` and `anthropic_messages.py` construct
> `ProviderResponse` without the durable trace ref). Adding that
> artifact-store wiring is a **directly dependent follow-up slice**
> (`s2.1` placeholder in the topic README), not part of s2. Running
> s2 against the current provider adapters fails fast with
> `ProviderTraceMissingError` — that is the desired safety property
> until s2.1 lands.

## Status

| Iter | Date (UTC) | Verdict  | Findings (one-liner) | Resolution |
|------|------------|----------|----------------------|------------|
| 1    | 2026-05-14 | REJECTED | 2 blockers (non-existent `ProviderResponse.trace_ref`, non-existent `PromptRegistryPort` version-pinned ref) + 3 majors (token-budget call shape, PRODUCTION-mode capability missing, `ProviderRequest` required fields underspecified) + 1 minor (test count math). | Plan revised to v2: model-call trace anchor uses existing `ProviderResponse.id` (always present) + `raw_response_ref` (when set); prompt anchor uses the constructor-pinned `prompt_template_ref` directly (no registry version-pin indirection); PRODUCTION-mode gate dropped as out-of-scope (caller picks which `ModelProviderPortV2` to inject); token budget call shape updated to `estimate_charge(ProviderRequest) -> TokenUsageEstimate` and `charge(TokenUsage, request_ref=...)`; `ProviderRequest` construction fully specified with `model_name`/`max_output_tokens`/`temperature` injected at adapter construction time; AC1 pinned at 24 collected (11 contract + 2 registry + 11 unit). |
| 2    | 2026-05-14 | REJECTED | iter-1 blockers all closed (per codex). 2 majors + 1 minor: (major) red list misses tests for prompt-render call shape AND the full `ProviderRequest` construction (`model_name`, `messages`, `response_format`, `max_output_tokens`, `temperature`). An implementation could pass every existing test while never sending the planned prompt/request shape. (major) topic README still says s2 is "gated behind PRODUCTION mode" and mentions `seed_ref`/model-call-trace wording that contradicts the iter-1 PRODUCTION-mode resolution. (minor) plan Status row line 7 said "23 collected, 10 unit tests" but Test Strategy / AC1 already say 24 collected, 11 unit tests. | Plan revised to v3: 2 new red unit tests added — test 14a `test_plan_renders_prompt_template_with_request_context` (asserts the prompt-registry call shape) and test 15a `test_plan_builds_provider_request_with_expected_fields` (asserts every required `ProviderRequest` field). AC1 collected count bumped 24 → 26. Topic README s2 row rewritten to drop "PRODUCTION mode" wording and align replay-refs description with the actual plan. Stale "23 collected, 10 unit" text in iter-1 row corrected to "24 collected, 11 unit". |
| 3    | 2026-05-14 | REJECTED | 1 blocker + 1 major: (blocker) `ProviderResponse.id` alone is not a durable/content replay anchor; allowing `raw_response_ref=None` means byte-identical replay is not guaranteed for the LLM output that drives `PlanDecision`. The replay consumer was also deferred to s11 — violates goal-doc rule "consumer wired in the same or a directly dependent slice". (major) `token_budget.charge()` was called only after `StructuredOutputViolation` would already have raised; failed model outputs evaded durable usage accounting. | Plan revised to v4: adapter now requires `response.raw_response_ref` to be non-blank — raises `ProviderTraceMissingError` (new typed `FatalError` subclass) on `None`. `replay_refs` always carries the durable `raw_response_ref` (no longer optional). Adapter flow reordered to call `token_budget.charge` BEFORE structured-output validation, so usage is durably persisted for every provider response (success or malformed). Tests 17/18 updated: replay-refs assertion uses the full list including `raw_response_ref`; test 18 renamed to assert that `raw_response_ref=None` raises `ProviderTraceMissingError`. New tests 20-bis `test_plan_charges_token_budget_before_structured_output_violation` covers the reorder. The same-slice replay consumer guarantee is met by the `FakeReplayingModelProvider` test adapter in s2 unit tests (which consumes recorded `raw_response_ref` to return a canned `ProviderResponse`). AC1 collected count bumped 26 → 28. |
| 4    | 2026-05-14 | REJECTED | 1 blocker + 3 majors + 1 minor: (blocker) the iter-3 fix rejects every existing PRODUCTION provider — current OpenAI/Anthropic v2 adapters do not populate `raw_response_ref`. (major) the "same-slice consumer" claim relied on a test-only fake, not in-product wiring; topic README still placed real replay consumption in s11. (major) topic README s2 row described `raw_response_ref` as "when set" rather than mandatory. (major) `ProviderTraceMissingError` fatal typing was not mechanically verified by any red test. (minor) Design data-flow diagram still showed charge-after-validation despite the iter-3 reorder. | Plan revised to v5: s2 explicitly demoted from "production adapter" framing to "real LLM adapter (replay-strict; awaits directly-dependent provider-artifact wiring slice s2.1 for live use)". Strict `raw_response_ref` requirement preserved as the fail-safe gate. Topic README s2 row updated to match. New contract test 11a `test_provider_trace_missing_error_is_fatal_error_subclass` asserts the typed inheritance. Design data-flow diagram rewritten to show the charge-before-validation order. Added Open Question + Reservation framing pointing to s2.1 (provider-artifact wiring) as the directly-dependent follow-up slice that completes live deployment. AC1 collected count bumped 28 → 29 (added test 11a). |
| 5    | 2026-05-14 | REJECTED → DONE_WITH_RESERVATIONS via post-iter-5 follow-up | iter-1/2/3 findings all closed (per codex). 1 blocker + 1 major: (blocker) replay consumer wiring still test-only via `FakeReplayingModelProvider` in unit test 25; s2.1 in topic README is provider-artifact writing, not replay consumption. (major) Open Question 1 still says "PRODUCTION v2 provider adapters already populate this" — false; current OpenAI/Anthropic v2 adapters construct `ProviderResponse(...)` without `raw_response_ref`. | Post-iter-5 follow-up landed in this same plan revision (no re-review per goal-doc workflow): (1) s2 scope expanded to add a real `ReplayingModelProviderV2` adapter at `src/veracrawl/adapters/model_providers/replaying_model_provider.py` (~30 LOC). It implements `ModelProviderPortV2` and returns canned `ProviderResponse`s from a constructor-injected `Mapping[str, ProviderResponse]` keyed by `ProviderRequest.id`. This is the in-product replay consumer; the test-only fake is retained as a test scaffold that demonstrates byte-equal replay against this real adapter. (2) Open Question 1 corrected to: "current OpenAI/Anthropic v2 adapters do NOT populate `raw_response_ref`; s2.1 is the directly-dependent slice that wires artifact persistence". Plan recorded as `PLAN_DONE_WITH_RESERVATIONS`; see "s2 plan iter-5 reservations" subsection of the topic STATUS for the items still open. |

Codex plan-review gate via `~/.claude/hooks/codex-review.sh plan <plan-file> --project-dir $PWD` (Reservation 2 discharged).

## Why

- **AGENTS.md hard constraint — general-purpose**: capability 1 of the
  goal doc requires "AI must be used to maximize ... crawl planning".
  s1 delivered the deterministic baseline; s2 puts real LLM-driven
  triage behind the same port. Without an LLM adapter shipped
  against `CrawlPlannerPort`, the contract surface stays unused by
  the actual AI agent layer and the audit gap stays open.
- **AGENTS.md hard constraint — low coupling**: the LLM adapter must
  not import model SDKs, browsers, storage, or queue clients
  directly. It composes existing v2 ports (`ModelProviderPortV2`,
  `PromptRegistryPort`, `TokenBudgetPort`) that isolate each
  framework / SDK behind its own adapter. s2 is the first
  `CrawlPlannerPort` consumer that validates the v2 port
  composition end-to-end.
- **AGENTS.md — framework-neutral agent runtime**: s2 introduces no
  `langchain` / `langgraph` / `crewai` / `autogen` /
  `semantic_kernel` import. The LLM call goes through
  `ModelProviderPortV2.complete`, which has OpenAI and Anthropic
  adapters today.
- **Goal doc capability 1**: s2 closes the `production adapter`
  half of `contract+port → fixture-mode adapter → production
  adapter → runtime-spine wiring → live integration test`. s3
  follows with the runner wiring.
- **Audit gap (goal doc, "SCAFFOLDED ONLY")**: *"`agents/
  orchestration.py` — scenario-string dict lookup; planner / drift
  / repair / adapter-choice all fixtures"*. s2 begins replacing the
  scenario-string planner half with a real LLM call.

## Scope

### In

- New production adapter
  `veracrawl.adapters.planning.llm_crawl_planner.LlmCrawlPlanner`
  implementing `veracrawl.ports.crawl_planner.CrawlPlannerPort`.
  Constructor (all parameters non-defaulted unless marked):
  - `model_provider: ModelProviderPortV2`
  - `prompt_registry: PromptRegistryPort`
  - `token_budget: TokenBudgetPort`
  - `prompt_template_ref: Ref` (the caller's responsibility to pass
    a version-pinned ref string; the registry contract today does
    not version-pin on render, so the caller's ref IS the pinned
    anchor)
  - `model_name: str` (which provider model to call —
    `ProviderRequest` requires this; pinned per-adapter instance)
  - `max_output_tokens: int` (positive; pinned per-adapter
    instance)
  - `temperature: float = 0.0` (deterministic by default; valid
    range `[0.0, 2.0]` per `ProviderRequest` validator)
  - `adapter_ref: Ref = "adapter:llm-crawl-planner:v1"`

  `plan(request: PlanRequest) -> PlanDecision` flow:
  1. Render the prompt template:
     `rendered_text = prompt_registry.render(prompt_template_ref,
     context)` where `context` is a dict carrying
     `{"objective_ref": request.objective_ref, "seed_urls":
     list(request.seed_urls), "budget_ref": request.budget_ref,
     "policy_snapshot_ref": request.policy_snapshot_ref,
     "run_ref": request.run_ref}`. The exact key set is the
     adapter's contract with the template author; the template
     decides what to interpolate.
  2. Build the `ProviderRequest` per the s1 plan + the existing
     `contracts.llm_input.ProviderRequest` schema:
     - `id = f"provider-request:{request.id}"`
     - `run_ref = request.run_ref`
     - `model_name = self._model_name`
     - `messages = [Message(role=MessageRole.USER,
       content=rendered_text)]`
     - `response_format = ResponseFormat(kind=
       ResponseFormatKind.JSON_OBJECT)` (no strict-mode schema —
       validation happens locally via `LlmPlanProposal.model_validate`)
     - `max_output_tokens = self._max_output_tokens`
     - `temperature = self._temperature`
     - `tools = []`, `anchors = []` (planner does not use either)
  3. `token_budget.estimate_charge(provider_request)` — returns
     `TokenUsageEstimate`; the port's contract is to raise
     `TokenBudgetExceeded` (or equivalent) if the estimate alone
     breaches the cap. Propagate.
  4. `model_provider.complete(provider_request)` — returns
     `ProviderResponse`. Typed retryable / fatal errors propagate.
  5. `token_budget.charge(response.usage,
     request_ref=provider_request.id)` — **durably persist usage
     BEFORE any structured-output validation**, so malformed-output
     calls still account for the tokens the provider actually
     billed. *(Iter-3 finding 2.)*
  6. Enforce the replay anchor: if
     `response.raw_response_ref is None or not response.raw_response_ref.strip()`,
     raise `ProviderTraceMissingError` (new typed `FatalError`
     subclass; see Open Questions). PRODUCTION-mode v2 provider
     adapters MUST populate this; fixture/test providers must
     opt-in by providing a canned trace ref. *(Iter-3 finding 1.)*
  7. Parse `response.parsed_output` (a `dict[str, Any] | None`).
     If `None`, raise `StructuredOutputViolation` (sanitized — never
     echo the raw output). Otherwise validate via
     `LlmPlanProposal.model_validate(response.parsed_output)`;
     pydantic validation failures become
     `StructuredOutputViolation`.
  8. Project `LlmPlanProposal` → `PlanDecision`:
     - `planned_seeds`: one per `LlmPlanProposal.planned_seeds`
       entry (input order preserved). The adapter synthesizes each
       `PlannedSeed.rationale_ref` from
       `f"rationale:{adapter_ref}:{prompt_template_ref}:seed-{i}"`
       so the rationale lineage is fully deterministic from
       constructor inputs (not LLM output).
     - `adapter_priors`: one per
       `LlmPlanProposal.adapter_priors` entry; rationale_ref
       similarly synthesized as
       `f"rationale:{adapter_ref}:{prompt_template_ref}:prior-{adapter_type}"`.
     - `frontier_priority_hints`: one per
       `LlmPlanProposal.frontier_priority_hints` entry; rationale_ref
       similarly synthesized.
     - `extraction_strategy_refs`: forwarded verbatim.
     - `replay_refs = [request.id, adapter_ref,
       request.replay_config_ref, request.objective_ref,
       prompt_template_ref, response.id,
       response.raw_response_ref]` — declared emission order.
       Because step 6 guarantees `raw_response_ref` is a non-blank
       ref string, this list has exactly 7 entries (no `None` and
       no length variance). *(Iter-3 finding 1.)*
     - `policy_decision_refs = list(request.policy_decision_refs)`
       (defensive-copied, same as s1).
  8. Return the `PlanDecision`.

- New contract module
  `veracrawl.contracts.llm_crawl_planner`. Four pydantic models
  (`VeraModel` base — no timestamp, planner contracts are pure
  data carriers per s1's iter-4 decision):
  - `LlmProposedSeed`: `canonical_url: str` (http(s) only),
    `priority_score: float` (`[0.0, 1.0]`),
    `adapter_hint: AdapterType` (strict enum — LLM is bound by the
    prompt template's enumeration).
  - `LlmProposedAdapterPrior`: `adapter_type: AdapterType`,
    `weight: float` (`[0.0, 1.0]`).
  - `LlmProposedFrontierPriorityHint`:
    `match_kind: FrontierMatchKind`, `match_value: str` (non-blank
    + consistent with `match_kind` — same rules as s1's
    `FrontierPriorityHint`), `priority_delta: float`
    (`[-1.0, 1.0]`).
  - `LlmPlanProposal`: `planned_seeds: list[LlmProposedSeed]`
    (≥ 1), `adapter_priors: list[LlmProposedAdapterPrior]`
    (≥ 1; unique adapter_type; sum ≤ 1.0 + 1e-9),
    `frontier_priority_hints: list[LlmProposedFrontierPriorityHint]`
    (default `[]`), `extraction_strategy_refs: list[Ref]`
    (default `[]`), `rationale_summary: str` (non-blank).

- Four new entries in
  `veracrawl.contracts.registry.FOUNDATION_CONTRACTS`:
  `LlmPlanProposal`, `LlmProposedSeed`, `LlmProposedAdapterPrior`,
  `LlmProposedFrontierPriorityHint`. All
  `owner_service=OwnerService.AGENTS`, `replay_required=True`.

- One new test method in
  `tests/contract/test_crawl_planner_import_boundaries.py`:
  `test_adapters_planning_llm_crawl_planner_imports_allowlist`,
  enforcing the broader allowlist for the LLM adapter (see Design
  § "Cross-module flow"). The s1 deterministic-adapter test keeps
  its tighter allowlist unchanged.

- **`ReplayingModelProviderV2`** — *(Iter-5 post-iter-5 follow-up)*.
  New adapter
  `veracrawl.adapters.model_providers.replaying_model_provider.ReplayingModelProviderV2`
  implementing `ModelProviderPortV2`. Constructor takes
  `canned: Mapping[str, ProviderResponse]` keyed by
  `ProviderRequest.id`. `complete(request)` looks up
  `canned[request.id]`; if missing, raises a typed
  `ReplayLookupMissError` (new `FatalError` subclass).
  `supports(capability)` returns `True` for any capability the
  canned `ProviderResponse` is consistent with — for s2's purposes,
  unconditional `True` is acceptable because the adapter just
  replays, but the s2 plan locks the conservative behavior:
  return `True` only if the canned response's structure permits
  the capability (e.g., `STRUCTURED_OUTPUT_JSON_SCHEMA` returns
  `True` iff `parsed_output is not None`). This adapter is the
  in-product replay consumer; the s2 unit test 25 wires
  `LlmCrawlPlanner` against it to prove byte-equal replay.

- Tests per the red list.

### Out

- Runner wiring (`ExternalCrawlRunner.plan(...)` call) — s3.
- Graph-feedback consumption (`PlannerObservationFeedback`) — s5.
- Drift / repair loops on planner output — s8/s9.
- Live network call to a real OpenAI / Anthropic endpoint. s2
  uses a canned-response fake `ModelProviderPortV2`; live
  integration arrives in s3.
- Objective-body text resolution. The s2 LLM triages by URL +
  the lineage ref strings + the pinned prompt template (the
  template decides what semantic context to inject). A typed
  body-resolver port is deferred to a later slice.
- `CalibrationPort` integration. The planner emits per-seed
  `priority_score` directly; no calibrated confidence layer.
- Multi-template / template-selection logic. Adapter takes one
  pinned `prompt_template_ref` at construction.
- PRODUCTION-mode gate. `ModelCapability` today has no
  `PRODUCTION` flag; adding one is an additive enum extension
  with its own slice. In s2 the caller picks which
  `ModelProviderPortV2` to inject — that's the gate. *(Iter-1
  finding 4.)*
- Prompt-template version-pinning at the registry layer. The
  caller passes a version-pinned ref; the registry's current
  contract returns `str`, no version metadata. Replay records the
  ref the caller passed. A registry-side version-pin contract
  change is out-of-scope for s2. *(Iter-1 finding 2.)*

## Design

### Module map (created in this slice)

```
src/veracrawl/contracts/llm_crawl_planner.py                   # new — ≤ 100 LOC
src/veracrawl/adapters/planning/llm_crawl_planner.py           # new — ≤ 150 LOC
src/veracrawl/adapters/model_providers/replaying_model_provider.py  # new — ≤  40 LOC  (iter-5 follow-up)
tests/contract/test_llm_crawl_planner_contracts.py             # new — ≤ 200 LOC
tests/contract/test_llm_crawl_planner_contract_registry.py     # new — ≤  40 LOC
tests/unit/adapters/planning/test_llm_crawl_planner.py         # new — ≤ 260 LOC
tests/unit/adapters/model_providers/test_replaying_model_provider.py  # new — ≤  90 LOC  (iter-5 follow-up; bumped 80→90 after step-3 task-review iter 2 added the valid `_canned_with_tool_calls` fixture helper for the iter-1 test 28b minor)
```

Module touched (not created):
`tests/contract/test_crawl_planner_import_boundaries.py` —
one new test method + helper allowlist tuple update; existing
budget is 60 LOC, post-update target ≤ 90 LOC.

Behavior-LOC ceiling: 100 + 150 + 40 = **290 LOC** before tests
+ the additive registry-dict edits. Under the binding ≤ 300 LOC.

### Data flow

```
PlanRequest (s1 contract; unchanged)
   │
   ▼
LlmCrawlPlanner.plan(request):
   │
   ├─► PromptRegistryPort.render(prompt_template_ref, context)  ──► rendered_text: str
   │
   ├─► build ProviderRequest(id=…, run_ref=…, model_name=…, messages=[Message(USER, rendered_text)],
   │                          response_format=JSON_OBJECT, max_output_tokens=…, temperature=…)
   │
   ├─► TokenBudgetPort.estimate_charge(provider_request)         raises if over cap
   │
   ├─► ModelProviderPortV2.complete(provider_request)            ──► ProviderResponse{id, usage, parsed_output, raw_response_ref, …}
   │
   ├─► TokenBudgetPort.charge(response.usage, request_ref=provider_request.id)   [BEFORE validation — iter-3 finding 2]
   │
   ├─► require response.raw_response_ref non-blank                raises ProviderTraceMissingError on None/blank [iter-3 finding 1]
   │
   ├─► LlmPlanProposal.model_validate(response.parsed_output)    raises StructuredOutputViolation on None / invalid
   │
   └─► project_to_plan_decision(proposal, request, prompt_template_ref, response.id, response.raw_response_ref)
        │
        ▼
       PlanDecision (s1 contract)
```

### Contract validator behavior (s2-owned models)

- `LlmProposedSeed`:
  - `canonical_url` is absolute http(s) (private duplicate of
    the helper).
  - `0.0 ≤ priority_score ≤ 1.0`.
- `LlmProposedAdapterPrior`:
  - `0.0 ≤ weight ≤ 1.0`.
- `LlmProposedFrontierPriorityHint`:
  - `-1.0 ≤ priority_delta ≤ 1.0`.
  - `match_value` non-blank.
  - `match_value` consistent with `match_kind` (same rules as
    s1's `FrontierPriorityHint`).
- `LlmPlanProposal`:
  - `planned_seeds` non-empty.
  - `adapter_priors` non-empty.
  - `adapter_priors` `adapter_type` values are unique.
  - `sum(weights) ≤ 1.0 + 1e-9`.
  - `rationale_summary` non-blank.

### Cross-module flow

- `contracts/llm_crawl_planner.py` imports
  `veracrawl.contracts.common`, `veracrawl.contracts.enums`, and
  a private `_is_http_url` helper.
- `adapters/planning/llm_crawl_planner.py` imports:
  - `veracrawl.contracts.crawl_planner` (s1 contracts)
  - `veracrawl.contracts.llm_crawl_planner` (s2 contracts)
  - `veracrawl.contracts.agent` (`Message`, `MessageRole`,
    `ResponseFormat`, `ResponseFormatKind`, `TokenUsage`)
  - `veracrawl.contracts.llm_input` (`ProviderRequest`,
    `ProviderResponse`)
  - `veracrawl.contracts.errors` (`StructuredOutputViolation`)
  - `veracrawl.contracts.enums` (`AdapterType`,
    `FrontierMatchKind`, `MessageRole`, `ResponseFormatKind`)
  - `veracrawl.ports.crawl_planner` (port implemented)
  - `veracrawl.ports.model_provider_v2`
  - `veracrawl.ports.prompt_registry`
  - `veracrawl.ports.token_budget`
  - stdlib only otherwise.

  Forbidden imports (enforced by the import-boundary test
  extension): any `veracrawl.adapters.*` other than self, any
  other `veracrawl.ports.*`, any internal runtime module
  (`external_crawl.*`, `agents.*` except its public contracts),
  any model SDK or browser engine.

### Replay invariant

The LLM call is non-deterministic; s2 records three refs in
`PlanDecision.replay_refs` to enable byte-identical replay:

- `prompt_template_ref` — the version-pinned ref the caller
  passed at construction (caller bears version-pinning per the
  current registry contract).
- `response.id` — the provider-assigned correlation id.
  `ProviderResponse.id` is always non-blank.
- `response.raw_response_ref` — the **required** durable audit
  ref pointing to a stored copy of the provider's raw response
  bytes. The s2 adapter rejects `raw_response_ref=None` with
  `ProviderTraceMissingError`. `response.id` is too thin to
  guarantee byte-equal replay; the durable raw-response ref is
  the content anchor. *(Iter-3 finding 1.)*

**Consumer wiring in-slice.** *(Iter-5 post-iter-5 follow-up.)*
s2 ships a real
`veracrawl.adapters.model_providers.replaying_model_provider.ReplayingModelProviderV2`
adapter that implements `ModelProviderPortV2` and returns canned
`ProviderResponse`s from a constructor-injected
`Mapping[str, ProviderResponse]` keyed by `ProviderRequest.id`.
This is the in-product replay consumer required by the goal-doc
rule. The byte-equal replay guarantee is mechanically proven by
unit test 25
`test_replay_refs_enable_byte_identical_plan_decision`, which
wires `LlmCrawlPlanner` against `ReplayingModelProviderV2`
populated with a canned response captured from a first run with
a regular fake provider. A later slice (s11) will hydrate the
replay map from durable storage; s2 ships the adapter and the
byte-equal guarantee.

### Naming

`LlmCrawlPlanner` (vs `OpenAICrawlPlanner` /
`AnthropicCrawlPlanner`) because the adapter is provider-neutral
— it composes whichever `ModelProviderPortV2` adapter is
injected.

## Dependencies

### On prior slices

- s1 (`CrawlPlannerPort` + s1 contracts). All required.

### On existing repo state

- `veracrawl.ports.model_provider_v2.ModelProviderPortV2`.
- `veracrawl.ports.prompt_registry.PromptRegistryPort` —
  `render(ref: str, context: Mapping[str, Any]) -> str`.
- `veracrawl.ports.token_budget.TokenBudgetPort` —
  `estimate_charge(ProviderRequest) -> TokenUsageEstimate`,
  `charge(TokenUsage, *, request_ref: Ref) -> None`.
- `veracrawl.contracts.llm_input.{ProviderRequest,
  ProviderResponse, TokenUsageEstimate}`.
- `veracrawl.contracts.agent.{Message, ResponseFormat,
  ResponseFormatKind, TokenUsage}`.
- `veracrawl.contracts.errors.StructuredOutputViolation`
  (and `TokenBudgetExceeded` — propagated, not raised by s2).
- New typed error: `veracrawl.contracts.errors.ProviderTraceMissingError`
  (a `FatalError` subclass, mirrored on existing
  `PromptTemplateNotFoundError` shape). Lands in s2 alongside
  the adapter — single-purpose error type for the
  `raw_response_ref=None` rejection. *(Iter-3 finding 1.)*
- `veracrawl.contracts.registry.{FOUNDATION_CONTRACTS,
  _contract}`.
- `veracrawl.contracts.enums.{AdapterType, FrontierMatchKind,
  MessageRole, ResponseFormatKind, OwnerService}`.

### Prerequisites

None new. The s1 prereq (`codex-review.sh` shim) is installed
and Reservation 2 discharged.

## Test Strategy

Red-first list. Each test is written before its implementation
and verified to fail.

### `tests/contract/test_llm_crawl_planner_contracts.py`

1. `test_llm_proposed_seed_rejects_non_http_url` →
   `ValidationError(match="canonical_url")`.
2. `test_llm_proposed_seed_rejects_priority_out_of_range` →
   `ValidationError(match="priority_score")`.
3. `test_llm_proposed_adapter_prior_rejects_weight_out_of_range` →
   `ValidationError(match="weight")`.
4. `test_llm_proposed_frontier_priority_hint_rejects_delta_out_of_range`
   → `ValidationError(match="priority_delta")`.
5. `test_llm_proposed_frontier_priority_hint_rejects_blank_match_value`
   → `ValidationError(match="match_value")`.
6. `test_llm_proposed_frontier_priority_hint_rejects_match_value_inconsistent_with_kind`
   → `ValidationError(match="match_value")`.
7. `test_llm_plan_proposal_rejects_empty_planned_seeds` →
   `ValidationError(match="planned_seeds")`.
8. `test_llm_plan_proposal_rejects_empty_adapter_priors` →
   `ValidationError(match="adapter_priors")`.
9. `test_llm_plan_proposal_rejects_duplicate_adapter_types` →
   `ValidationError(match="adapter_priors")`.
10. `test_llm_plan_proposal_rejects_adapter_priors_sum_above_one`
    → `ValidationError(match="sum")`.
11. `test_llm_plan_proposal_rejects_blank_rationale_summary` →
    `ValidationError(match="rationale_summary")`.
11a. `test_provider_trace_missing_error_is_fatal_error_subclass`
    — *(Iter-4 finding 4)*. `issubclass(ProviderTraceMissingError,
    FatalError)` AND `issubclass(ProviderTraceMissingError,
    VeraCrawlError)`. Pins the typed-recovery boundary so a future
    refactor cannot quietly redefine the error as a plain
    `Exception` and weaken the recovery surface.
11a-ctor. `test_provider_trace_missing_error_constructs_with_domain_kwarg`
    — *(s2 step-1 task-review iter 1 finding)*. The error mirrors
    `PromptTemplateNotFoundError`: a single `provider_request_id`
    kwarg. Construct
    `ProviderTraceMissingError(provider_request_id="provider-request:test:1")`
    and assert: `err.provider_request_id == "provider-request:test:1"`;
    `"provider-request:test:1"` appears in `str(err)`;
    `"raw_response_ref"` appears in `str(err)`. The original 11a
    only verified subclassing — without this, a future regression
    could reintroduce the unfriendly `ModelProviderError.__init__(
    status_code, error_code, request_id)` shape without test
    coverage.
11b. `test_replay_lookup_miss_error_is_fatal_error_subclass_and_constructs`
    — *(s2 step-1 task-review iter 1 finding)*. `ReplayLookupMissError`
    has the same typed shape as `ProviderTraceMissingError`:
    `issubclass(..., FatalError)`, `issubclass(..., VeraCrawlError)`,
    constructs via `ReplayLookupMissError(provider_request_id=...)`,
    stores the kwarg, includes it in `str(err)`. Asserted in one
    test because the error is twin-shaped with
    `ProviderTraceMissingError`.

### `tests/contract/test_llm_crawl_planner_contract_registry.py`

12. `test_registry_contains_all_four_llm_planner_contracts` —
    `("LlmPlanProposal", "LlmProposedSeed",
    "LlmProposedAdapterPrior",
    "LlmProposedFrontierPriorityHint")` all in
    `FOUNDATION_CONTRACTS` with `replay_required=True` and
    `owner_service=OwnerService.AGENTS`.
13. `test_registry_validate_returns_ok` (regression check).

### `tests/unit/adapters/planning/test_llm_crawl_planner.py`

Tests use:
- `FakeModelProviderV2`: returns a canned `ProviderResponse`
  for the first `.complete` call; records the `ProviderRequest`
  it was given.
- `FakePromptRegistry`: returns a deterministic rendered string
  composed from the ref and context dict; records calls.
- `FakeTokenBudget`: records the sequence of
  `estimate_charge` and `charge` calls; raises
  `TokenBudgetExceeded` only when configured to.

None of these fakes mock the adapter under test.

14. `test_plan_returns_plan_decision_carrying_request_ref` —
    `decision.request_ref == request.id`.
14a. `test_plan_renders_prompt_template_with_request_context` —
    *(Iter-2 finding 1)*. After one `.plan(request)` call,
    `FakePromptRegistry.recorded_calls == [(prompt_template_ref,
    {"objective_ref": request.objective_ref, "seed_urls":
    list(request.seed_urls), "budget_ref": request.budget_ref,
    "policy_snapshot_ref": request.policy_snapshot_ref,
    "run_ref": request.run_ref})]` (single call; exact ref +
    context dict equality).
15. `test_plan_planned_seeds_preserve_proposal_order` — canned
    proposal with 3 seeds; `decision.planned_seeds[i].canonical_url`
    matches input order.
15a. `test_plan_builds_provider_request_with_expected_fields` —
    *(Iter-2 finding 1)*. After one `.plan(request)` call,
    `FakeModelProviderV2.recorded_request` (the
    `ProviderRequest` instance) has: `id == f"provider-request:
    {request.id}"`; `run_ref == request.run_ref`;
    `model_name == constructor_model_name`;
    `messages == [Message(role=MessageRole.USER,
    content=rendered_text)]` where `rendered_text` is the
    `FakePromptRegistry` return value; `response_format ==
    ResponseFormat(kind=ResponseFormatKind.JSON_OBJECT)`;
    `max_output_tokens == constructor_max_output_tokens`;
    `temperature == constructor_temperature`; `tools == []`;
    `anchors == []`.
16. `test_plan_adapter_priors_round_trip_from_proposal` — typed
    `AdapterPrior` instances carrying the proposal's weights and
    adapter_types; rationale_refs synthesized from
    `adapter_ref` + `prompt_template_ref` + adapter_type per the
    Scope formula.
17. `test_plan_replay_refs_emission_order` —
    `decision.replay_refs == [request.id, adapter_ref,
    request.replay_config_ref, request.objective_ref,
    prompt_template_ref, response.id,
    response.raw_response_ref]` — exact 7-entry list.
18. `test_plan_raises_provider_trace_missing_when_raw_response_ref_none`
    — *(Iter-3 finding 1)*. Canned response with
    `raw_response_ref=None` → adapter raises
    `ProviderTraceMissingError`. Same test with
    `raw_response_ref=""` (whitespace-stripped to empty) → same
    error.
19. `test_plan_policy_decision_refs_forwarded_verbatim` —
    `decision.policy_decision_refs == request.policy_decision_refs`;
    mutating the request afterward does not change the decision.
20. `test_plan_calls_token_budget_estimate_then_charge_in_order` —
    `FakeTokenBudget` records the sequence; expected:
    `[("estimate_charge", provider_request),
    ("charge", response.usage, provider_request.id)]`.
20a. `test_plan_charges_token_budget_before_structured_output_validation`
    — *(Iter-3 finding 2)*. Canned `parsed_output = None` (would
    raise `StructuredOutputViolation`). The adapter MUST have
    called `token_budget.charge(response.usage, ...)` BEFORE
    raising. Assertion: `FakeTokenBudget.recorded_calls`
    contains a `("charge", ...)` entry even though the
    `StructuredOutputViolation` propagates up. Same shape for
    `parsed_output = {"foo": "bar"}` (validation failure path).
21. `test_plan_refuses_when_token_budget_estimate_raises` —
    `FakeTokenBudget.estimate_charge` raises
    `TokenBudgetExceeded`; the adapter propagates without
    calling `model_provider.complete`.
22. `test_plan_raises_structured_output_violation_on_none_parsed_output`
    — canned `ProviderResponse.parsed_output = None`; adapter
    raises `StructuredOutputViolation`. (Budget charge already
    happened — verified separately by test 20a.)
23. `test_plan_raises_structured_output_violation_on_invalid_json`
    — canned `parsed_output = {"foo": "bar"}` (missing
    `planned_seeds` etc.); adapter raises
    `StructuredOutputViolation`.
24. `test_planner_implements_crawl_planner_port` —
    `isinstance(LlmCrawlPlanner(...), CrawlPlannerPort)`.
25. `test_replay_refs_enable_byte_identical_plan_decision` —
    *(Iter-3 finding 1; iter-5 follow-up wires the real
    consumer.)* Run 1: adapter calls a `FakeModelProviderV2`
    configured with a canned `ProviderResponse{id="provider-response:test:R1",
    raw_response_ref="raw-response:test:R1", parsed_output={…},
    usage=…}`. Capture `decision_1.canonical_json()`. Run 2:
    construct the real
    `ReplayingModelProviderV2({"provider-request:test:1":
    canned_response_1})` (keyed by the deterministic
    `ProviderRequest.id`). Invoke the same
    `LlmCrawlPlanner.plan(request)`. Assert
    `decision_2.canonical_json() == decision_1.canonical_json()`.
    The in-product `ReplayingModelProviderV2` is the consumer
    wiring the goal-doc rule requires.

Acceptance Criterion 1 pytest count = **14** contract + 2
registry + **15** planner-unit + **6** replaying-unit =
**37 collected**. The replaying-unit count rose 3 → 6 after
step-3 task-review iter 1 required `supports()` to be derived
from the canned bundle (tests 28a, 28b, 28c added).

### `tests/unit/adapters/model_providers/test_replaying_model_provider.py` *(iter-5 follow-up)*

26. `test_replaying_model_provider_returns_canned_response_keyed_by_request_id` —
    `ReplayingModelProviderV2({"provider-request:test:1":
    canned})`.complete(request_with_id_provider_request_test_1)
    == canned`.
27. `test_replaying_model_provider_raises_on_missing_key` —
    request id not in the canned mapping → `ReplayLookupMissError`
    (new typed `FatalError` subclass).
28. `test_replaying_model_provider_implements_model_provider_port` —
    `isinstance(ReplayingModelProviderV2(...), ModelProviderPortV2)`.
28a. `test_supports_structured_output_iff_any_canned_has_parsed_output`
    — *(step-3 task-review iter 1 finding)*. `supports()` must be
    derived from the canned bundle. Empty bundle → `False`. Canned
    response with `parsed_output=None` → `False`. Canned with a
    non-`None` `parsed_output` → `True`.
28b. `test_supports_tool_calls_iff_any_canned_has_tool_calls` —
    *(step-3 task-review iter 1 finding)*. Canned with empty
    `tool_calls` → `False`; canned with at least one `ToolCall`
    → `True`.
28c. `test_supports_vision_and_extended_thinking_default_false` —
    *(step-3 task-review iter 1 finding)*. Capabilities with no
    signal in the canned bundle default to `False` so an unrelated
    consumer cannot accidentally route work through a replay
    provider.

### Import boundary

`tests/contract/test_crawl_planner_import_boundaries.py` gains
one test:

25. `test_adapters_planning_llm_crawl_planner_imports_allowlist` —
    walks the LLM adapter AST and accepts only stdlib +
    `veracrawl.contracts.*` + `veracrawl.ports.crawl_planner` +
    `veracrawl.ports.model_provider_v2` +
    `veracrawl.ports.prompt_registry` +
    `veracrawl.ports.token_budget`. Relative imports rejected.

The existing s1 deterministic-adapter allowlist test stays
tighter (no model-provider / prompt-registry / token-budget
imports allowed there).

### Green path

Each red test gets a minimal implementation. One purpose per
commit. After all 38 tests pass (counted as 14 + 2 + 15 + 6 + 1),
refactor to dedupe URL / match-value validators.

## Acceptance Criteria

Mechanically verifiable from a fresh checkout.

1. **Pytest gate (s2-owned files)** —
   `pytest tests/contract/test_llm_crawl_planner_contracts.py tests/contract/test_llm_crawl_planner_contract_registry.py tests/unit/adapters/planning/test_llm_crawl_planner.py tests/unit/adapters/model_providers/test_replaying_model_provider.py -v`
   exits 0 with **37** collected, **37** passed, **0** failed,
   **0** errored.

2. **Pytest gate (import-boundary file)** —
   `pytest tests/contract/test_crawl_planner_import_boundaries.py -v`
   exits 0 with **4** collected (s1's 3 plus the new test 25).

3. **Contract registry** — Python one-liner verifying all four
   new entries (`LlmPlanProposal`, `LlmProposedSeed`,
   `LlmProposedAdapterPrior`, `LlmProposedFrontierPriorityHint`)
   present with `replay_required=True`,
   `owner_service=OwnerService.AGENTS`, and
   `validate_registry().ok`.

4. **No runner wiring** —
   `python -c "import pathlib; assert 'llm_crawl_planner' not in pathlib.Path('src/veracrawl/external_crawl/runner.py').read_text()"`
   exits 0. (Runner wires the adapter in s3.)

5. **No agent-framework / browser / storage SDK in the adapter**
   —
   `! grep -rE '\b(langchain|langgraph|crewai|autogen|semantic_kernel|playwright|selenium|boto3|sqlalchemy|redis|kombu|celery)\b' src/veracrawl/adapters/planning/llm_crawl_planner.py`
   (grep exits 1). The model SDK imports (`openai` /
   `anthropic`) MUST NOT appear in this file — they live behind
   `veracrawl.ports.model_provider_v2` and its adapter
   implementations under `src/veracrawl/adapters/model_providers/`.

6. **Behavior LOC budget** —
   `total=$(wc -l src/veracrawl/contracts/llm_crawl_planner.py src/veracrawl/adapters/planning/llm_crawl_planner.py | tail -1 | awk '{print $1}'); test "$total" -le 300`
   exits 0.

7. **Codex plan-review gate** —
   `CODEX_REVIEW_ITERATION=N ~/.claude/hooks/codex-review.sh plan
   docs/plans/general-purpose-crawler-agentification/s2-llm-crawl-planner-adapter.md
   --project-dir $PWD` returns `VERDICT: APPROVED` in ≤ 5
   iterations, OR DONE_WITH_RESERVATIONS per goal doc.

8. **Codex task-review per commit** — each implementation
   commit passes
   `~/.claude/hooks/codex-review.sh task <BASELINE> --project-dir
   $PWD` in ≤ 5 iterations, or carries a recorded reservation.

## Rollback

s2 only adds new files plus four `FOUNDATION_CONTRACTS` entries
and one new test method in the import-boundary file. Rollback is
`git revert <s2-commit-range>` — no migrations, no schema
changes, no consumer breakage. s1 keeps working with the
deterministic adapter as the only `CrawlPlannerPort` impl.

## Open Questions

1. **`raw_response_ref` requirement** — *(Resolved iter 3;
   correction landed iter 5)*. s2 rejects
   `response.raw_response_ref=None` with
   `ProviderTraceMissingError`. The current OpenAI / Anthropic v2
   provider adapters do **NOT** populate `raw_response_ref`
   (verified by reading
   `src/veracrawl/adapters/model_providers/openai_responses_v2.py`
   and `anthropic_messages.py`); the directly-dependent slice
   s2.1 lands the artifact-store wiring that populates the field
   on every `complete(...)` call. s2's unit test 25 wires
   `LlmCrawlPlanner` against the real
   `ReplayingModelProviderV2` (introduced in this slice) to
   prove the byte-equal replay guarantee.
2. **Prompt-template version-pinning at the registry layer**:
   the current `PromptRegistryPort.render` returns `str` only,
   so the caller's `prompt_template_ref` IS the pin anchor. A
   future slice can extend the registry port to return version
   metadata; s2 just records what the caller passed. Decision:
   accept current contract; deferred to a registry-port slice.
3. **`LlmProposedSeed.adapter_hint` enum vs string**: strict
   enum (validation failure caught by
   `StructuredOutputViolation`) keeps the proposal contract
   sharp; the prompt template enumerates allowed values for the
   LLM. Default: **strict enum**.
4. **Multiple-call retry on malformed proposal**: s2 fails
   immediately with `StructuredOutputViolation`. Retry / repair
   logic is s8 / s9 territory.
5. **Caching**: identical `PlanRequest`s are NOT cached in s2.
   Caching is a runtime-spine concern (s14).
6. **`temperature=0.0` default**: zero gives provider-side
   determinism where supported. Provider adapters that ignore
   `temperature=0.0` semantics still yield byte-different
   responses across calls; replay is the canonical mechanism
   for byte-equal replay. Decision: **default to 0.0**.
