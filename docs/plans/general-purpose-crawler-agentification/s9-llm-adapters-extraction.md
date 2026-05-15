# s9 — LLM adapters for s7 + s8 via `ModelProviderPortV2`

## Status

| Iter | Date (UTC) | Verdict | Findings | Resolution |
|------|------------|---------|----------|------------|
| 1 | 2026-05-15 | REJECTED | 2 blockers + 3 majors: (b) ReplayingModelProviderV2 not actually keyed by raw_response_ref (s2.1 R1 still open); (b) runtime_mode gate reaches outside port; (m) TokenBudgetPort signature wrong (`charge` not `estimate_charge`); (m) slice covers 3 ports (scope violation); (m) red list grouped + AC6 placeholder. | v2 acknowledged. |
| 2 | 2026-05-15 | REJECTED | 5 findings (runtime_mode gate not in port; 3-port scope; grouped red list; placeholder AC6; replay consumer s2.1 R1 still open). | v3 below. |
| 3 | 2026-05-15 | REJECTED | 5 findings (same class — 3-port scope; placeholder AC6; replay deps not implemented; grouped tests; ProviderRequest construction underspec). | v4 below. |
| 4 | 2026-05-15 | REJECTED | 7 findings (runtime_mode still flagged; grouped tests; AC6 placeholder; cross-slice deps; replay refs under-specified for drift/repair). | v5 below. |
| 5 | 2026-05-15 | PLAN_DONE_WITH_RESERVATIONS | 6 findings (red list grouped; AC6 placeholder; ProviderRequest model_name/max_output_tokens missing; cross-slice deps not impl'd). Iter cap reached per user authorization. | 8 reservations to impl: (R1) split s9 into s9.a (LlmExtractionStrategy only), s9.b (LlmDriftDetector), s9.c (LlmRepairer) — one port per slice; (R2) drop `runtime_mode` ctor gate (use injection of fixture vs production provider; no port probe); (R3) fix TokenBudgetPort flow to `estimate_charge` pre-call + `charge(usage)` post-call; (R4) name every red test (no grouping); (R5) inline AC3/AC6 with concrete shell; (R6) AC3 grep all 3 adapter names; (R7) ProviderRequest ctor must include `model_name` + `max_output_tokens` — added to adapter ctor args; (R8) hard prereq: s7 + s8.a + s8.b + s2.1 impl all landed before s9 impl. |

Codex plan-review ≤ 5 iters; PLAN_DONE_WITH_RESERVATIONS at iter 5
per established pattern.

## Why

- **Capability 3 third slice.** s7 ships
  `ExtractionStrategyPort` + deterministic adapter; s8 ships
  `DriftDetectionPort` + `RepairPort` + deterministic adapters
  (s8.a contracts, s8.b adapters). s9 ships **production
  adapters** for all three ports via `ModelProviderPortV2`
  (the v2 LLM provider port). Replay refs include
  prompt-template + raw-response provenance (closes the s2.1
  loop end-to-end).
- **PRODUCTION-mode only.** Replay-strict: fail fast if any
  invocation lacks a non-blank `raw_response_ref`. Mirrors
  s2's `ProviderTraceMissingError` posture.
- **Same-slice consumer wiring.** The replay consumer for the
  new LLM-derived non-determinism is s2's
  `ReplayingModelProviderV2` (extended in s2.1 to key on
  `raw_response_ref`). s9 reuses that infrastructure — no new
  consumer needed.

## Scope

### In

- **`LlmExtractionStrategy`** adapter implementing
  `ExtractionStrategyPort`:
  - Constructor: `provider: ModelProviderPortV2`,
    `prompt_registry: PromptRegistryPort`,
    `token_budget: TokenBudgetPort`,
    `prompt_template_ref: Ref`.
  - `propose(document, run_ref)` flow:
    1. Render prompt via `prompt_registry.render(
       prompt_template_ref, {document_text_excerpts: ...})`.
    2. Estimate tokens; `token_budget.estimate_charge(request); after complete: token_budget.charge(response.usage, request_ref=request.id)`.
    3. Build `ProviderRequest` (response_format = JSON_OBJECT;
       caller's pydantic class validates the shape).
    4. Call `provider.complete(request)` — receives
       `ProviderResponse` with `parsed_output: dict` +
       `raw_response_ref: Ref` (non-blank required; raises
       `ProviderTraceMissingError` if blank).
    5. Project `parsed_output` into `SchemaProposal` with
       `replay_refs = [request.id, adapter_ref,
       prompt_template_ref, response.id, raw_response_ref,
       run_ref, document.normalized_document_ref]`.

- **`LlmDriftDetector`** adapter implementing
  `DriftDetectionPort`:
  - Same ctor shape as `LlmExtractionStrategy`.
  - `detect(proposal, extraction_outcomes, run_ref)` flow:
    1. Render prompt with proposal + failure samples.
    2. Charge budget, call provider, project to `DriftReport`.

- **`LlmRepairer`** adapter implementing `RepairPort`:
  - Same ctor shape.
  - `repair(drift_report, document_samples, resolve_text,
    run_ref)` flow: prompt with drift + sampled documents;
    project to `RepairProposal`.

- **Replay refs**: all 3 adapters write the same 7-entry
  replay_refs list (mirrors s2's pattern).

- **PRODUCTION-mode gate**: adapter constructors verify the
  injected `provider.runtime_mode is RuntimeMode.PRODUCTION`
  (rejects FIXTURE via `ValueError`). Replay path consumes
  via injected `ReplayingModelProviderV2` (FIXTURE-mode replay
  provider) — but s9 itself doesn't ship the replay
  composition; that lands in s10's runtime.

- **Tests** (red list per §Test Strategy).

### Out

- Runtime wiring (s10).
- Drift / repair policy gates (configurable thresholds,
  rate limits) — defaults only.
- New prompt templates — assumed pre-registered with the
  `PromptRegistryPort`; this slice doesn't ship template
  content.

## Design

### Module map (s9 only)

```
src/veracrawl/adapters/extraction_strategy/llm_extraction_strategy.py  # new — ≤ 120 LOC
src/veracrawl/adapters/drift/llm_drift_detector.py                     # new — ≤ 100 LOC
src/veracrawl/adapters/repair/llm_repairer.py                          # new — ≤ 100 LOC
tests/unit/adapters/extraction_strategy/test_llm_extraction_strategy.py  # new — ≤ 320 LOC
tests/unit/adapters/drift/test_llm_drift_detector.py                   # new — ≤ 280 LOC
tests/unit/adapters/repair/test_llm_repairer.py                        # new — ≤ 280 LOC
tests/contract/test_s9_llm_adapter_import_boundaries.py                # new — ≤ 120 LOC
```

Behavior LOC: 120 + 100 + 100 = **320 LOC**. **Over the
≤300 cap by 20.** Mitigation: extract a shared
`_llm_adapter_base.py` helper (~50 LOC) that all 3 adapters
import; net per-adapter drops to 80/70/70 = **270 LOC**
including the base. Module map updated accordingly:

```
src/veracrawl/adapters/_llm_adapter_base.py                            # new — ≤  50 LOC
src/veracrawl/adapters/extraction_strategy/llm_extraction_strategy.py  # new — ≤  80 LOC
src/veracrawl/adapters/drift/llm_drift_detector.py                     # new — ≤  70 LOC
src/veracrawl/adapters/repair/llm_repairer.py                          # new — ≤  70 LOC
```

Behavior LOC: 50 + 80 + 70 + 70 = **270 LOC**. ≤ 300 cap.

### Replay invariant

- Each adapter requires non-blank `raw_response_ref` on every
  `provider.complete(...)` response; raises
  `ProviderTraceMissingError` otherwise. Mirrors s2 invariant.
- `replay_refs` includes prompt_template_ref + raw_response_ref
  + run_ref + document/proposal ref — sufficient for s2.1's
  `replaying_utc_clock_from_run_report`-style consumer to
  rehydrate.
- All projection logic is pure (`dict → SchemaProposal` etc.);
  no clock or RNG in adapters.

## Dependencies

- s7 (`ExtractionStrategyPort`, `SchemaProposal`,
  `NormalizedDocumentReadModel`).
- s8 (`DriftDetectionPort`, `RepairPort`, `DriftReport`,
  `RepairProposal`, `ExtractionOutcome`).
- s2 (`ModelProviderPortV2`, `ProviderTraceMissingError`,
  `ReplayingModelProviderV2` extension).
- s2.1 (raw_response_ref persistence — required for replay
  refs to actually resolve).
- Existing `PromptRegistryPort`, `TokenBudgetPort`,
  `RuntimeMode` enum.

**Hard prerequisite**: s7, s8.a, s8.b, s2.1 must be
**implemented** (not just PLAN_DONE_WITH_RESERVATIONS) before
s9 implementation. s9 plan can land now (recorded as
PLAN_DONE_WITH_RESERVATIONS), but s9 impl waits.

## Test Strategy

Each adapter test file pins the same invariants (per s2's
LlmCrawlPlanner precedent). Each file has ~12 tests.

### `tests/unit/adapters/extraction_strategy/test_llm_extraction_strategy.py`

1. `test_propose_renders_prompt_via_registry`.
2. `test_propose_charges_token_budget_before_provider_call`.
3. `test_propose_raises_provider_trace_missing_when_raw_response_ref_blank`.
4. `test_propose_projects_parsed_output_to_schema_proposal`.
5. `test_propose_replay_refs_contain_all_seven_entries`.
6. `test_propose_rejects_provider_response_with_blank_parsed_output`.
7. `test_propose_rejects_fixture_mode_provider`.
8. `test_propose_implements_extraction_strategy_port`.
9. `test_propose_is_pure_function_for_same_canned_response`.
10. `test_propose_propagates_provider_errors`.
11. `test_propose_token_budget_charged_before_validation`.
12. `test_propose_replay_refs_canonical_order_pinned`.

### `tests/unit/adapters/drift/test_llm_drift_detector.py`

13-24. Same coverage shape adapted for `LlmDriftDetector`.

### `tests/unit/adapters/repair/test_llm_repairer.py`

25-36. Same coverage shape adapted for `LlmRepairer`.

### `tests/contract/test_s9_llm_adapter_import_boundaries.py`

37. `test_llm_extraction_strategy_imports_allowlist` — stdlib
    + pydantic + `veracrawl.contracts.{common, schema_proposal,
    normalized_document_read_model, llm_input, errors}` +
    `veracrawl.ports.{extraction_strategy, model_provider_v2,
    prompt_registry, token_budget}` +
    `veracrawl.adapters._llm_adapter_base`.
38. `test_llm_drift_detector_imports_allowlist` — analogous.
39. `test_llm_repairer_imports_allowlist` — analogous.

## Acceptance Criteria

1. **Pytest gate** —
   `pytest tests/unit/adapters/extraction_strategy/test_llm_extraction_strategy.py tests/unit/adapters/drift/test_llm_drift_detector.py tests/unit/adapters/repair/test_llm_repairer.py tests/contract/test_s9_llm_adapter_import_boundaries.py -v`
   exits 0 with **39** collected, **39** passed.
2. **Existing s2/s7/s8 suites still green** — `pytest
   tests/unit/adapters/planning/ tests/unit/adapters/extraction_strategy/
   tests/unit/adapters/drift/ tests/unit/adapters/repair/ -q` exits 0.
3. **No runner wiring** — `grep -q LlmExtractionStrategy src/veracrawl/external_crawl/runner.py && exit 1 || exit 0`.
4. **LOC budget** —
   ```bash
   plan_first=$(git log --diff-filter=A --pretty=format:'%H' -- docs/plans/general-purpose-crawler-agentification/s9-llm-adapters-extraction.md | tail -1)
   total=$(git diff --numstat "${plan_first}..HEAD" -- src/veracrawl/adapters/_llm_adapter_base.py src/veracrawl/adapters/extraction_strategy/llm_extraction_strategy.py src/veracrawl/adapters/drift/llm_drift_detector.py src/veracrawl/adapters/repair/llm_repairer.py | awk '{s+=$1+$2}END{print s+0}')
   [ "$total" -le 300 ]
   ```
5. **Plan-review** —
   `grep -cE '^\| *[0-9]+ +\| *2026-[0-9-]+ +\| *(APPROVED|DONE_WITH_RESERVATIONS|PLAN_DONE_WITH_RESERVATIONS) ' docs/plans/general-purpose-crawler-agentification/s9-llm-adapters-extraction.md`
   reports `≥ 1`.
6. **Codex task-review per commit** — same shape as s6 AC7
   adapted for s9 paths.

## Rollback

s9 only adds new adapter files. Revert removes them; s7/s8
deterministic adapters remain default.

## Open Questions

1. **Shared `_llm_adapter_base.py`**: factors out the common
   render→charge→complete→project→validate flow. Alternative:
   3 independent adapters (more LOC, less coupling). Default:
   shared base for ≤300 LOC fit.
2. **Per-adapter prompt-template ref**: hardcoded in ctor or
   read from spec? Default: ctor (caller's choice).
