# s10 — `SchemaExtractionRuntime` consumes s7–s9 on real pages

## Status

| Iter | Date (UTC) | Verdict | Findings | Resolution |
|------|------------|---------|----------|------------|
| 1 | 2026-05-15 | REJECTED | 2 blockers + 2 majors: (b) s7/s8/s9 prereqs not impl'd; (b) `SchemaExtractionRuntimeReport` shape doesn't support planned output; (m) AC6 placeholder; (m) name clash with existing `SchemaExtractionRuntime` in `processing/` + `extract/schema_runtime.py`. | v2 below. |
| 2 | 2026-05-15 | REJECTED | README contradicts slice scope on runner wiring. | v3. |
| 3 | 2026-05-15 | REJECTED | XPath extraction has no valid input contract. | v4. |
| 4 | 2026-05-15 | REJECTED | SchemaExtractionRuntime name clash unresolved. | v5. |
| 5 | 2026-05-15 | PLAN_DONE_WITH_RESERVATIONS | SchemaExtractionRuntime ownership/name clash unresolved + cumulative findings. Iter cap reached. | 7 reservations to impl: (R1) rename to `SchemaExtractionLoop` or place in new `src/veracrawl/extraction/` dir to avoid clash with existing `processing/schema_extraction_runtime.py` + `extract/schema_runtime.py`; (R2) `SchemaExtractionRuntimeReport` contract needs extension (new fields: proposal_ref, drift_ref, repair_ref, per_page_outcomes) — separate contract design slice or extension in s10; (R3) AC6 inlined; (R4) topic README s10 row corrected — runtime wiring is OUT of s10 (future slice); (R5) XPath extraction path requires `NormalizedDocumentReadModelReadModel.resolve_text` resolver — make explicit; (R6) hard prereq: s7+s8+s9 ALL impl'd before s10 impl; (R7) integration fixture corpus must avoid using real external sites. |

Codex plan-review ≤ 5 iters; PLAN_DONE_WITH_RESERVATIONS at iter 5 per
established pattern.

## Why

- **Capability 3 fourth slice — closes the extraction loop.**
  s7 ships ExtractionStrategyPort (propose); s8 ships
  DriftDetectionPort + RepairPort (detect+repair); s9 ships
  the LLM adapters. s10 ships the **runtime** that pipes per-
  page normalized docs through:
  `strategy.propose → extract → drift.detect → repair.repair`,
  and reports per-corpus quality.
- **Live integration.** Tests use a real fixture site (3-page
  HTML corpus) — first end-to-end real-page extraction in the
  topic. Closes capability 3.
- **General-purpose constraint.** The runtime is vertical-
  agnostic; the fixture site is chosen to be unfamiliar
  (`docs/08-build-roadmap.md` recommends one new site per
  slice).

## Scope

### In

- **`SchemaExtractionRuntime`** class at
  `src/veracrawl/agents/schema_extraction_runtime.py`:
  - Constructor: `strategy: ExtractionStrategyPort`,
    `drift_detector: DriftDetectionPort`,
    `repairer: RepairPort`,
    `resolve_text: Callable[[Ref], str]`,
    `quality_threshold: float = 0.7` (per-field success rate
    below which repair is invoked).
  - `extract_corpus(documents: list[NormalizedDocumentReadModel],
    run_ref: Ref) -> SchemaExtractionRuntimeReport`:
    1. `proposal = strategy.propose(documents[0], run_ref)`.
    2. For each `doc` in `documents`: apply `proposal` to
       extract field values (deterministic xpath eval).
       Record per-field success/miss into `ExtractionOutcome`.
    3. `drift = drift_detector.detect(proposal,
       extraction_outcomes, run_ref)`.
    4. If `drift.drifted_fields`: `repair = repairer.repair(
       drift, documents, resolve_text, run_ref)`.
       Apply repair to proposal; re-extract drifted fields.
    5. Return `SchemaExtractionRuntimeReport` with per-page
       extracted values + final proposal + drift + repair refs.

- **Existing `SchemaExtractionRuntimeReport` contract** is
  in `contracts/processing.py:335` — verify shape matches
  s10's emission; extend if necessary (≤30 LOC delta).

- **Fixture site**: 3-page HTML corpus under
  `tests/fixtures/sites/sample_news_corpus/` with deliberate
  drift on the third page (one field xpath changes).

- **Integration test** uses `httpx.MockTransport` or local
  stub serving the fixture; runs through the full
  propose→extract→detect→repair loop and asserts:
  - Final proposal includes repaired xpath for drifted field.
  - All 3 pages have full field coverage after repair.
  - `replay_refs` chain links every step back to inputs.

- **Tests** (red list 18).

### Out

- Runner integration. The runtime is called by a future slice
  that wires it into `ExternalCrawlRunner.run()` (post-extract
  hook). Out of s10.
- Multi-strategy fallback. If primary strategy fails, run
  alternative? Out of s10 (single strategy only).
- Drift threshold dynamic adjustment. Out of s10.

## Design

### Module map

```
src/veracrawl/agents/schema_extraction_runtime.py             # new — ≤ 200 LOC
src/veracrawl/contracts/processing.py                         # modify — ≤  30 LOC (extend report if needed)
tests/fixtures/sites/sample_news_corpus/page_a.html           # new — fixture
tests/fixtures/sites/sample_news_corpus/page_b.html           # new — fixture
tests/fixtures/sites/sample_news_corpus/page_c.html           # new — fixture (with drift)
tests/unit/agents/test_schema_extraction_runtime.py           # new — ≤ 320 LOC
tests/integration/test_schema_extraction_runtime_corpus.py    # new — ≤ 260 LOC
tests/contract/test_schema_extraction_runtime_import_boundaries.py  # new — ≤ 100 LOC
```

Behavior LOC: 200 + 30 = **230 LOC**. Under ≤ 300 cap.

### Replay invariant

- Runtime is pure given (documents, run_ref, ports). All
  non-determinism flows through the injected ports — same
  fixture-mode ports → byte-equal report.
- Replay refs propagate: `report.proposal_ref →
  proposal.replay_refs`; `report.drift_ref →
  drift_report.replay_refs`; etc.

## Dependencies

- s7, s8 (s8.a + s8.b), s9 (s9.a + s9.b + s9.c) — all impl'd.
- `SchemaExtractionRuntimeReport` contract
  (`contracts/processing.py`).

**Hard prerequisite**: s7 + s8 + s9 implementations must all
be landed before s10 impl.

## Test Strategy

### `tests/unit/agents/test_schema_extraction_runtime.py`

1. `test_extract_corpus_calls_strategy_propose_with_first_document`.
2. `test_extract_corpus_records_extraction_outcomes_per_page`.
3. `test_extract_corpus_calls_drift_detector_with_outcomes`.
4. `test_extract_corpus_skips_repair_when_no_drift`.
5. `test_extract_corpus_calls_repair_when_drift_present`.
6. `test_extract_corpus_re_extracts_after_repair`.
7. `test_extract_corpus_quality_threshold_gates_repair`.
8. `test_extract_corpus_report_includes_proposal_ref`.
9. `test_extract_corpus_report_includes_drift_ref`.
10. `test_extract_corpus_report_includes_repair_ref_when_repaired`.
11. `test_extract_corpus_replay_refs_chain_complete`.
12. `test_extract_corpus_pure_function_given_canned_ports`.
13. `test_extract_corpus_handles_empty_document_list`.

### `tests/integration/test_schema_extraction_runtime_corpus.py`

14. `test_corpus_three_pages_full_field_coverage_after_repair` —
    fixture site, full propose→extract→drift→repair loop;
    final report has all fields extracted for all 3 pages.
15. `test_corpus_drift_detected_on_page_c` — verifies drift
    detector flagged the deliberately-drifted field.
16. `test_corpus_repair_proposes_alternative_xpath` — verifies
    repair output contains a new xpath for the drifted field.

### `tests/contract/test_schema_extraction_runtime_import_boundaries.py`

17. `test_runtime_imports_allowlist` — stdlib + `veracrawl.ports.{
    extraction_strategy, drift_detection, repair}` +
    `veracrawl.contracts.{schema_proposal, drift_report,
    repair_proposal, extraction_outcome, processing,
    normalized_document_read_model, common}`. Reject any
    `veracrawl.adapters.*`.
18. `test_external_crawl_runner_does_not_import_schema_extraction_runtime` —
    s10 doesn't wire into runner; that's a future slice.

## Acceptance Criteria

1. **Pytest gate** —
   `pytest tests/unit/agents/test_schema_extraction_runtime.py tests/integration/test_schema_extraction_runtime_corpus.py tests/contract/test_schema_extraction_runtime_import_boundaries.py -v`
   exits 0 with **18** collected, **18** passed.
2. **Existing s7/s8/s9 suites still green** — `pytest
   tests/unit/adapters/extraction_strategy/ tests/unit/adapters/drift/
   tests/unit/adapters/repair/ -q` exits 0.
3. **No runner wiring** —
   `grep -q SchemaExtractionRuntime src/veracrawl/external_crawl/runner.py && exit 1 || exit 0`.
4. **LOC budget** —
   ```bash
   plan_first=$(git log --diff-filter=A --pretty=format:'%H' -- docs/plans/general-purpose-crawler-agentification/s10-schema-extraction-runtime.md | tail -1)
   total=$(git diff --numstat "${plan_first}..HEAD" -- src/veracrawl/agents/schema_extraction_runtime.py src/veracrawl/contracts/processing.py | awk '{s+=$1+$2}END{print s+0}')
   [ "$total" -le 300 ]
   ```
5. **Plan-review** —
   `grep -cE '^\| *[0-9]+ +\| *2026-[0-9-]+ +\| *(APPROVED|DONE_WITH_RESERVATIONS|PLAN_DONE_WITH_RESERVATIONS) ' docs/plans/general-purpose-crawler-agentification/s10-schema-extraction-runtime.md`
   reports `≥ 1`.
6. **Codex task-review per commit** — same shape as s6 AC7
   adapted for s10 paths.

## Rollback

s10 only adds new files. Revert removes them; s7-s9 adapters
remain unwired.

## Open Questions

1. **Quality threshold default (0.7)**: arbitrary first cut.
   Tuning slice may follow.
2. **Multi-strategy fallback**: deferred. s10 uses single
   strategy.
3. **Per-corpus vs per-domain proposal scope**: s10 proposes
   once for the corpus; future slice may scope per-domain.
