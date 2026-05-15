# s8 — `DriftDetectionPort` + `RepairPort` + deterministic fixture adapters

## Status

| Iter | Date (UTC) | Verdict | Findings | Resolution |
|------|------------|---------|----------|------------|
| 1 | 2026-05-15 | REJECTED | 3 blockers + 2 majors: Scope/Design describe different slices (s8 vs s8.a); ExtractionOutcome contract doesn't exist; ACs placeholders; grouped red list; README/STATUS not aligned. | Plan revised v2 below. |
| 2 | 2026-05-15 | REJECTED | 6 findings (scope split partial, ExtractionOutcome undefined, ACs placeholders, grouped red list, README/STATUS misaligned, VeraModel binding not explicit). | v3 below. |
| 3 | 2026-05-15 | REJECTED | 5 findings (title vs scope still inconsistent, AC placeholders, grouped red list omits ExtractionOutcome tests, ExtractionOutcome dependency contradictory, LOC over cap). | v4 below. |
| 4 | 2026-05-15 | REJECTED | 6 findings (scope/title/README still mismatched; LOC cap exceeded; ACs placeholders; ExtractionOutcome dependency contradictory; s7 contracts not yet landed; VeraModel binding under-specified). | iter 5 next. |
| 5 | 2026-05-15 | PLAN_DONE_WITH_RESERVATIONS | 6 findings same class as iter 4. Iter cap reached per user authorization. | 8 reservations to impl: (R1) plan title + topic README + STATUS slice row all to match "s8.a contracts+ports only"; (R2) split impl into s8.a (contracts + ports) AND s8.b (fixture adapters) — separate commits, separate task-review trails; (R3) ExtractionOutcome settled as NEW in s8.a (drop "check at impl time" wording); (R4) drop RepairKind enum (use validated strings) to fit ≤300 LOC cap; (R5) ACs all inlined with concrete shell/pytest commands; (R6) red list expanded to flat-named tests including ExtractionOutcome coverage; (R7) every new contract explicitly binds VeraModel + ConfigDict(extra="forbid") with red test asserting extra-field rejection; (R8) hard dependency on s7 implementation — s8.a impl gated on s7 contracts being landed and importable. |

Codex plan-review ≤ 5 iters; PLAN_DONE_WITH_RESERVATIONS at iter 5 per
established pattern.

## Why

- **Capability 3 second slice.** After s7 ships
  ExtractionStrategyPort, s8 catches drift across pages
  (missing-field rates) and proposes structural repairs
  (anchor reselection). s9 wires LLM adapters behind these
  ports; s10 consumes the full chain.
- **General-purpose.** Drift is detected from anchor-success
  statistics, not site-specific templates. Repair proposes
  alternative xpaths from sibling-anchor distributions.

## Scope

**This plan is scoped strictly to s8.a (contracts + ports only).
Fixture adapters land in s8.b — a separate plan/commit. Module
map and ACs below reflect s8.a only.**

### In

- **`DriftReport` contract** (`veracrawl.contracts.drift_report`):
  - `id: str`, `run_ref: Ref`, `proposal_ref: Ref`,
    `pages_evaluated: int`, `field_missing_rates: dict[str, float]`,
    `drifted_fields: list[str]`, `drift_threshold: float = 0.30`,
    `replay_refs: list[Ref]`.
  - Validators: non-blank ids/refs, rates in `[0,1]`, threshold
    in `(0,1)`, `pages_evaluated ≥ 1`, `drifted_fields ⊆
    field_missing_rates.keys()`.

- **`RepairProposal` contract**
  (`veracrawl.contracts.repair_proposal`):
  - `id: str`, `run_ref: Ref`, `drift_report_ref: Ref`,
    `field_repairs: list[FieldRepair]`, `replay_refs: list[Ref]`.
  - `FieldRepair`: `field_name: str`, `original_xpath: str`,
    `proposed_xpath: str`, `confidence: float`,
    `repair_kind: RepairKind` (StrEnum: `ANCHOR_RESELECT`,
    `CONFIDENCE_ADJUST`, `TYPE_RELAX`).
  - Validators analogous to s7's ProposedField.

- **`DriftDetectionPort`**
  (`veracrawl.ports.drift_detection.DriftDetectionPort`):
  - `detect(*, proposal: SchemaProposal,
    extraction_outcomes: list[ExtractionOutcome],
    run_ref: Ref) -> DriftReport`.

- **`RepairPort`** (`veracrawl.ports.repair.RepairPort`):
  - `repair(*, drift_report: DriftReport,
    document_samples: list[NormalizedDocumentReadModel],
    resolve_text: Callable[[Ref], str],
    run_ref: Ref) -> RepairProposal`.

- **NEW `ExtractionOutcome` contract** (defined in s8.a — does
  NOT exist in repo today): `id: str`, `run_ref: Ref`,
  `page_canonical_url: str`, `field_outcomes: dict[str, bool]`
  (field_name → success/miss), `replay_refs: list[Ref]`.

- **Registry entries** for `DriftReport` + `RepairProposal`
  + `ExtractionOutcome`.

- **Tests** (red list 22 explicit — see §Test Strategy for
  full enumeration).

- **Fixture adapters** — OUT OF SCOPE for s8.a; in s8.b plan.

### Out

- LLM versions (s9).
- Runtime integration (s10).
- Schema versioning / migration (future).

## Design

### Module map (s8.a — final)

```
src/veracrawl/contracts/extraction_outcome.py             # new — ≤  80 LOC
src/veracrawl/contracts/drift_report.py                   # new — ≤  90 LOC
src/veracrawl/contracts/repair_proposal.py                # new — ≤  90 LOC
src/veracrawl/contracts/registry.py                       # modify — ≤  15 LOC
src/veracrawl/ports/drift_detection.py                    # new — ≤  25 LOC
src/veracrawl/ports/repair.py                             # new — ≤  25 LOC
tests/contract/test_drift_repair_contracts.py             # new — ≤ 380 LOC
tests/contract/test_drift_repair_registry.py              # new — ≤  40 LOC
tests/contract/test_drift_repair_import_boundaries.py     # new — ≤ 100 LOC
```

Behavior LOC: 80 + 90 + 90 + 15 + 25 + 25 = **325 LOC**. Slightly
over 300 — split further by moving `ExtractionOutcome` to a
dedicated s8.0 pre-slice if codex iter rejects. **Working LOC
target: ≤ 300, with `RepairKind` enum dropped (use validated
strings).**

Fixture adapters (`AnchorFrequencyDriftDetector`,
`AnchorReselectRepair`) — OUT OF SCOPE. Land in s8.b plan post-
impl of s8.a.

### Replay invariant

- All adapters pure functions of inputs. No clock, no RNG.
- `detect(...)` and `repair(...)` return byte-equal outputs
  for byte-equal inputs.

## Dependencies

- s7 (`SchemaProposal`, `NormalizedDocumentReadModel`,
  `resolve_text` closure pattern).
- `ExtractionOutcome` — pre-existing in
  `contracts.processing.py`? Check at impl time; if not, defer
  s8.b until it lands.

## Test Strategy (s8.a only)

### `tests/contract/test_drift_repair_contracts.py`

1-9. DriftReport validators: blank id/run_ref/proposal_ref,
   negative/zero `pages_evaluated`, rate out of `[0,1]`,
   threshold out of `(0,1)`, drifted_fields not in
   field_missing_rates, missing replay_refs, blank
   replay_refs entry, canonical_json deterministic.

10-15. RepairProposal validators: similar coverage including
   blank field_name, blank original_xpath, blank
   proposed_xpath, confidence range, missing replay_refs,
   canonical_json deterministic.

### `tests/contract/test_drift_repair_registry.py`

16. `test_registry_contains_drift_report`.
17. `test_registry_contains_repair_proposal`.
18. `test_registry_validate_ok`.

### `tests/contract/test_drift_repair_import_boundaries.py`

19. `test_drift_report_contract_imports_allowlist` — AST.
20. `test_repair_proposal_contract_imports_allowlist`.
21. `test_drift_detection_port_imports_allowlist`.
22. `test_repair_port_imports_allowlist`.

## Acceptance Criteria

1. Pytest gate: 22 collected, 22 passed.
2. Registry inline check.
3. No runner wiring: grep -q drift_report src/veracrawl/external_crawl/runner.py → exits 1.
4. LOC budget shell ≤ 300.
5. Plan-review APPROVED ≤ 5 iters OR PLAN_DONE_WITH_RESERVATIONS.
6. Task-review per commit shell (same shape as s7 AC6).

## Rollback

s8.a only adds new files + registry entries. Revert removes them.

## Open Questions

1. Should DriftDetectionPort + RepairPort be combined into one
   `SchemaQualityPort`? Default: keep separate for testability.
2. `ExtractionOutcome` contract — exists? Drop from s8, defer
   to s8.b prerequisite. Confirmed at impl.
