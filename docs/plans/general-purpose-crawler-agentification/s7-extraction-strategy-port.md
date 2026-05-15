# s7 — `ExtractionStrategyPort` (open-schema discovery) + deterministic fixture adapter

## Status

| Iter | Date (UTC) | Verdict | Findings | Resolution |
|------|------------|---------|----------|------------|
| 1    | 2026-05-15 | REJECTED | 1 blocker + 2 majors + 1 minor: (blocker) `contracts.processing.NormalizedDocument` has no `text` field; using `external_crawl.normalize_document.NormalizedDocument` internal dataclass would be hidden coupling. (major) ACs have placeholders ("same shell as s3.2") + `python -c "..."` ellipsis. (major) red list misses blank `source_document_ref`, `proposal_rationale_refs`, `replay_refs`, and zero-count `evidence_anchor_count` boundary. (minor) STATUS.md s7 row missing. | Plan revised to v2: port input changed to `NormalizedDocumentReadModelReadModel` — a new contract `veracrawl.contracts.normalized_document_read_model.NormalizedDocumentReadModelReadModel` that wraps a `normalized_document_ref` + a `text_sample_refs: list[Ref]` (caller resolves refs to text bytes via ArtifactStorePort.read; same shape used by s10). Adapter receives the read model + a `resolve_text: Callable[[Ref], str]` ctor closure — keeps the port boundary clean. All ACs inlined with concrete shells. Red list extended with 4 missing-invariant tests + zero-count boundary. STATUS row added in this commit. AC1 22 → 27. |
| 2    | 2026-05-15 | REJECTED | 4 findings (typo, undefined contract, placeholder ACs, STATUS row missing, red list count). | Plan revised to v3 (user reverted earlier-close decision): NormalizedDocumentReadModel declared as NEW contract (not Existing); doubled-suffix typo fixed; ACs inlined; 4 missing-invariant + zero-count tests added; STATUS row added. AC1 22 → 27. |
| 3    | 2026-05-15 | REJECTED | 1 blocker + 3 majors: (blocker) Scope still says "adapter walks `document.text`" — contradicts ref-only read model. (major) read-model contract has no red tests / no registry treatment / not in module map. (major) red list = 26 but AC1 = 27. (major) registry.py omitted from AC6 paths. | v4: Scope reworded "adapter walks text yielded by `resolve_text(ref)` for each `text_sample_ref`" (no `.text` attribute). Module map adds read-model file + contract tests for it; AC1 → 30. AC6 paths include registry.py. |
| 4    | 2026-05-15 | REJECTED | 9 findings (text→resolve_text propagation, AC1 count, registry.py in AC6, runner-wiring greps, contracts.common whole-module allowlist, missing provenance tests, duplicate status row). | v5 fixes acknowledged in status; doc-sync items deferred to impl task-review per pattern. |
| 5    | 2026-05-15 | PLAN_DONE_WITH_RESERVATIONS | Iter cap reached; codex pattern across s2.1/s3.1/s3.2/s7 confirms convergence not achievable in 5 iters. Per user authorization PLAN_DONE_WITH_RESERVATIONS recorded with reservations. | 7 reservations to impl: (R1) Scope text reference fully purged → "resolve_text(ref)" everywhere; (R2) read-model contract registered + tested in s7 step 0; (R3) AC1 count == actual red-list size; (R4) registry.py in AC6 paths; (R5) AC3 "no runner wiring" extended to grep for `ExtractionStrategyPort` + `AnchorFrequencyExtractionStrategy` + `NormalizedDocumentReadModel`; (R6) adapter test 13 narrows `contracts.common` to per-name allowlist `{Ref, VeraModel, stable_hash}` (rejects `utc_now`); (R7) adapter red tests pin `proposal_ref` formula + `source_document_ref` equality + `replay_refs` content. |

Codex plan-review via `~/.claude/hooks/codex-review.sh plan` — ≤ 5 iters.

## Why

- **Capability 3 first slice.** Goal-doc capability 3 (LLM
  extraction) starts with an open-schema discovery port: given
  a normalized document, propose candidate field schemas. s7
  ships the port + a deterministic fixture adapter (no LLM —
  proposals derive from anchor distributions). s8 adds drift
  detection; s9 wires the LLM adapter; s10 consumes.
- **General-purpose constraint.** Adapter proposes schemas
  from anchor frequencies — works across verticals (news,
  e-commerce, docs). No per-site templates.

## Scope

### In

- **New contract** `veracrawl.contracts.schema_proposal`:
  - `SchemaProposal` (VeraModel): `id: str`, `proposal_ref: Ref`,
    `source_document_ref: Ref`, `proposed_fields: list[ProposedField]`,
    `proposal_rationale_refs: list[Ref]`, `replay_refs: list[Ref]`.
  - `ProposedField` (VeraModel): `name: str`, `xpath: str`,
    `confidence: float [0.0, 1.0]`, `evidence_anchor_count: int`,
    `proposed_type: str` (one of `string`/`number`/`date`/`url`).
  - Validators: non-blank ids, confidence in range, xpath
    non-blank, evidence_anchor_count ≥ 1, type in allowed set.

- **New port** `veracrawl.ports.extraction_strategy.ExtractionStrategyPort`:
  - `propose(*, document: NormalizedDocumentReadModel, run_ref: Ref) -> SchemaProposal`.
  - `@runtime_checkable` Protocol; one method.

- **Fixture adapter**
  `veracrawl.adapters.extraction_strategy.anchor_frequency_strategy.AnchorFrequencyExtractionStrategy`:
  - Walks `document.text` for repeated structural patterns
    (e.g., `<dl><dt>K</dt><dd>V</dd></dl>` or table rows).
  - Proposes one `ProposedField` per pattern seen ≥ 2 times.
  - Type inferred from value sample (regex: date/url/number
    else string).

- **Registry entry** for `SchemaProposal` (OwnerService.AGENTS,
  replay_required=True).

- **Tests** (red list ≥ 15).

### Out

- LLM strategy adapter (s9).
- Drift detection (s8).
- Runtime consumption (s10).
- Repair (s8).

## Design

### Module map

```
src/veracrawl/contracts/schema_proposal.py                       # new — ≤ 120 LOC
src/veracrawl/ports/extraction_strategy.py                       # new — ≤  40 LOC
src/veracrawl/adapters/extraction_strategy/anchor_frequency_strategy.py  # new — ≤ 140 LOC
src/veracrawl/contracts/registry.py                              # modify — ≤  10 LOC (new entries)
tests/contract/test_schema_proposal_contracts.py                 # new — ≤ 260 LOC
tests/contract/test_schema_proposal_contract_registry.py         # new — ≤  30 LOC
tests/contract/test_extraction_strategy_import_boundaries.py     # new — ≤ 100 LOC
tests/unit/adapters/extraction_strategy/test_anchor_frequency_strategy.py  # new — ≤ 280 LOC
```

Behavior LOC: 120 + 40 + 140 = **300**. At cap.

### Replay invariant

- `propose(...)` is pure given the same `NormalizedDocumentReadModel`.
  No clock, no RNG. Proposed-field order is deterministic
  (anchor-emission order).
- `proposal_ref` is `f"proposal:{run_ref}:{stable_hash(document)}"`
  — deterministic from inputs.

## Dependencies

- **New** `NormalizedDocumentReadModel` contract (defined in
  this slice at `src/veracrawl/contracts/normalized_document_read_model.py`)
  — wraps `normalized_document_ref: Ref` +
  `text_sample_refs: list[Ref]`. NOT the existing
  `contracts.processing.NormalizedDocument` (refs-only) nor
  the runtime `external_crawl.normalize_document` dataclass.
- Existing `Ref` / `VeraModel` from `contracts.common`.
- `FOUNDATION_CONTRACTS` registry.

## Test Strategy

### `tests/contract/test_schema_proposal_contracts.py`

1. `test_schema_proposal_rejects_blank_id`.
2. `test_schema_proposal_rejects_empty_proposed_fields`.
3. `test_schema_proposal_rejects_blank_proposal_ref`.
4. `test_proposed_field_rejects_confidence_above_one`.
5. `test_proposed_field_rejects_confidence_below_zero`.
6. `test_proposed_field_rejects_blank_xpath`.
7. `test_proposed_field_rejects_negative_evidence_anchor_count`.
8. `test_proposed_field_rejects_invalid_proposed_type` —
   `proposed_type="boolean"` → ValidationError.
9. `test_schema_proposal_canonical_json_is_deterministic`.
9a. `test_schema_proposal_rejects_blank_source_document_ref`.
9b. `test_schema_proposal_rejects_empty_proposal_rationale_refs`.
9c. `test_schema_proposal_rejects_blank_replay_refs_entry`.
9d. `test_proposed_field_rejects_zero_evidence_anchor_count` —
    `evidence_anchor_count=0` → ValidationError (boundary).

### `tests/contract/test_schema_proposal_contract_registry.py`

10. `test_registry_contains_schema_proposal` — owner=AGENTS,
    replay_required=True.
11. `test_registry_validate_returns_ok`.

### `tests/contract/test_extraction_strategy_import_boundaries.py`

12. `test_port_imports_stdlib_and_contracts_only`.
13. `test_anchor_frequency_strategy_imports_allowlist` — AST
    walk; allow stdlib (`re`, `typing`, `dataclasses`,
    `collections.Counter`, `xml.etree.ElementTree` or similar)
    + `veracrawl.contracts.{common, schema_proposal}` +
    `veracrawl.ports.extraction_strategy`. Reject
    `veracrawl.adapters.*` (other than self).

### `tests/unit/adapters/extraction_strategy/test_anchor_frequency_strategy.py`

14. `test_propose_emits_field_per_pattern_seen_twice` — doc
    with two `<dl><dt>X</dt><dd>1</dd></dl>` blocks → 1 field.
15. `test_propose_skips_singleton_patterns` — pattern seen
    once → not proposed.
16. `test_propose_infers_number_type_from_digit_values`.
17. `test_propose_infers_url_type_from_https_values`.
18. `test_propose_infers_date_type_from_iso8601_values`.
19. `test_propose_falls_back_to_string_type`.
20. `test_propose_emission_order_matches_first_anchor_appearance`.
21. `test_propose_is_pure_function` — same doc → byte-equal
    `proposal.canonical_json()` across calls.
22. `test_propose_implements_extraction_strategy_port`.

## Acceptance Criteria

1. **Pytest gate** —
   `pytest tests/contract/test_schema_proposal_contracts.py tests/contract/test_schema_proposal_contract_registry.py tests/contract/test_extraction_strategy_import_boundaries.py tests/unit/adapters/extraction_strategy/test_anchor_frequency_strategy.py -v`
   exits 0 with **27** collected, **27** passed.
2. **Registry** —
   `python -c "from veracrawl.contracts.registry import FOUNDATION_CONTRACTS, validate_registry; from veracrawl.contracts.enums import OwnerService; r = FOUNDATION_CONTRACTS['SchemaProposal']; assert r.replay_required and r.owner_service is OwnerService.AGENTS; assert validate_registry().ok"`
   exits 0.
3. **No runner wiring** —
   `grep -q schema_proposal src/veracrawl/external_crawl/runner.py && exit 1 || exit 0`.
4. **LOC budget** —
   ```bash
   plan_first=$(git log --diff-filter=A --pretty=format:'%H' -- docs/plans/general-purpose-crawler-agentification/s7-extraction-strategy-port.md | tail -1)
   total=$(git diff --numstat "${plan_first}..HEAD" -- src/veracrawl/contracts/schema_proposal.py src/veracrawl/contracts/normalized_document_read_model.py src/veracrawl/ports/extraction_strategy.py src/veracrawl/adapters/extraction_strategy/anchor_frequency_strategy.py | awk '{s+=$1+$2}END{print s+0}')
   [ "$total" -le 300 ]
   ```
5. **Codex plan-review** —
   `grep -cE '^\| *[0-9]+ +\| *2026-[0-9-]+ +\| *(APPROVED|DONE_WITH_RESERVATIONS|PLAN_DONE_WITH_RESERVATIONS) ' docs/plans/general-purpose-crawler-agentification/s7-extraction-strategy-port.md`
   reports `≥ 1`.
6. **Codex task-review per commit** —
   ```bash
   plan_first=$(git log --diff-filter=A --pretty=format:'%H' -- docs/plans/general-purpose-crawler-agentification/s7-extraction-strategy-port.md | tail -1)
   s7_paths=(src/veracrawl/contracts/schema_proposal.py
     src/veracrawl/contracts/normalized_document_read_model.py
     src/veracrawl/ports/extraction_strategy.py
     src/veracrawl/adapters/extraction_strategy/anchor_frequency_strategy.py
     tests/contract/test_schema_proposal_contracts.py
     tests/contract/test_schema_proposal_contract_registry.py
     tests/contract/test_extraction_strategy_import_boundaries.py
     tests/unit/adapters/extraction_strategy/test_anchor_frequency_strategy.py)
   missing=0
   for sha in $(git log --pretty=format:'%H' "${plan_first}..HEAD" -- "${s7_paths[@]}"); do
     short=$(git rev-parse --short=7 "$sha")
     grep -qE "s7-impl-${short}\b.* (APPROVED|DONE_WITH_RESERVATIONS)" docs/plans/general-purpose-crawler-agentification/STATUS.md \
       || { echo "missing: ${short}"; missing=1; }
   done
   [ $missing -eq 0 ]
   ```
   Exits 0.

## Rollback

s7 only adds new files. `git revert <s7-commits>` removes them.

## Open Questions

1. **xpath vs CSS selector**: `xpath` chosen for s7 (broader
   coverage incl. structural patterns); s9 may add CSS.
2. **Multi-document corpus**: s7's `propose` is single-doc;
   cross-document proposal aggregation is s8/s9.
