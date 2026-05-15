# s18 — Real-site acceptance corpus: three unfamiliar sites end-to-end

## Status

| Iter | Date (UTC) | Verdict | Findings | Resolution |
|------|------------|---------|----------|------------|
| 1 | 2026-05-15 | REJECTED | live snapshot adds network nondeterminism w/o replay-ref contract; test-only scope can't exercise full plan→fetch→extract→publish; ACs not mechanical. | v2-v5 below. |
| 2 | 2026-05-15 | REJECTED | Red tests + ACs not mechanically verifiable. | v3. |
| 3 | 2026-05-15 | REJECTED | Red list underspec + site choice unresolved. | v4. |
| 4 | 2026-05-15 | REJECTED | Dependencies too broad + STATUS inconsistent. | v5. |
| 5 | 2026-05-15 | PLAN_DONE_WITH_RESERVATIONS | ACs still not mechanical. Iter cap reached. | 6 reservations: (R1) pick concrete sites (with legal review + robots.txt confirmation); (R2) deps narrowed — only the impl chains actually needed (capability 1 for plan, capability 2 for fetch, capability 3 for extract, optional capability 4 for replay); (R3) ACs inlined with concrete pytest selectors; (R4) snapshot capture wired via s12's ReplayingHttpFetcher + s15 hashed-fs default for byte-determinism; (R5) red list expanded with explicit per-site test bodies; (R6) topic STATUS s18 row added. |

≤ 5 iters; PLAN_DONE_WITH_RESERVATIONS at iter 5 per pattern.

## Why

- **Capability 7 closing slice.** Final acceptance — fixtures
  + `@pytest.mark.live` corpus exercising plan→fetch→extract→
  publish on three sites the existing test suite never
  touched. Proves the general-purpose claim holds on
  unfamiliar verticals.

## Scope

### In

- **Three new live integration tests**, each marked
  `@pytest.mark.live`:
  - **Site A** (news vertical): a blog or news site with
    article listing + article pages.
  - **Site B** (e-commerce vertical): a product catalog with
    product detail pages.
  - **Site C** (docs vertical): a documentation site with
    nested sections + code blocks.
- Each test:
  1. Configure runner with planner + observer + extraction
     strategy.
  2. Run against the live site (real network, real HTML).
  3. Assert: ≥ 1 page fetched per site; ≥ 1 field extracted
     per page; no `policy_denials`; no `extraction_failures`
     above 30%.
- **Fixture snapshots**: each test records a fixture snapshot
  (HTML body + sidecar) on first run; later runs replay from
  the snapshot via s12's `ReplayingHttpFetcher`. Allows CI
  green without live network.
- **Tests** (red list 6 — 2 per site).

### Out

- Per-site templates or selectors. The runtime must extract
  schemas open-form from the site's own structure.
- Tracking results across runs (no historical baseline).

## Design

### Module map

```
tests/integration/test_corpus_site_a_news.py             # new — ≤ 220 LOC
tests/integration/test_corpus_site_b_ecommerce.py        # new — ≤ 220 LOC
tests/integration/test_corpus_site_c_docs.py             # new — ≤ 220 LOC
tests/fixtures/sites/corpus_a/                           # snapshots
tests/fixtures/sites/corpus_b/                           # snapshots
tests/fixtures/sites/corpus_c/                           # snapshots
```

NO source LOC delta. s18 is test-only.

### Replay invariant

- Fixture snapshots are content-addressed via s15's hashed-
  fs store; same site state → same fixture refs.
- `ReplayingHttpFetcher` (s12) replays the snapshots; tests
  pass without network access when snapshots exist.

## Dependencies

- All of s1-s17 implemented.

**Hard prereq**: capability 1-6 all done.

## Test Strategy

Per site (×3):

1. `test_corpus_<site>_runs_end_to_end_live` — `@pytest.mark.live`,
   real network. Run runner, assert no errors.
2. `test_corpus_<site>_extracts_at_least_one_field_per_page` —
   uses the replayed snapshot (no `live` mark); deterministic.

Total: 6 tests.

## Acceptance Criteria

1. Pytest gate (replay-only mode): `pytest tests/integration/test_corpus_*.py -m "not live" -v` exits 0 with 3 collected, 3 passed.
2. Live mode (manual): `pytest tests/integration/test_corpus_*.py -m live -v` exits 0 with 3 collected, 3 passed (when network available).
3. No regression on existing suite.
4. LOC budget: source delta 0.
5. Plan-review grep ≥ 1.
6. Task-review per commit.

## Rollback

Adds tests + fixtures only.

## Open Questions

1. **Choice of sites**: must be openly-crawlable (robots.txt
   permissive); legal review on which sites are OK to use
   for testing.
2. **Snapshot refresh cadence**: monthly? Per-release?
   Defaults to "stale snapshots tolerated; live mode is the
   ground-truth gate".
