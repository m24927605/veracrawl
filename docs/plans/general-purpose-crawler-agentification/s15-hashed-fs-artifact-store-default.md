# s15 — Hashed-filesystem `ArtifactStorePort` default

## Status

| Iter | Date (UTC) | Verdict | Findings | Resolution |
|------|------------|---------|----------|------------|
| 1    | TBD        | TBD     | TBD      | TBD        |
| 2    | TBD        | TBD     | TBD      | TBD        |
| 3    | TBD        | TBD     | TBD      | TBD        |
| 4    | TBD        | TBD     | TBD      | TBD        |
| 5    | TBD        | TBD     | TBD      | TBD        |

≤ 5 iters; PLAN_DONE_WITH_RESERVATIONS at iter 5 per pattern.

## Why

- **Capability 5 second slice.** Replace
  `ReferencePersistenceStore` (or whatever in-memory default
  the runtime currently wires) with a hashed-filesystem
  `ArtifactStorePort` impl. Stable on content hash → safe
  for replay (same bytes → same ref). Regression tests for
  outbox and replay refs.

## Scope

### In

- **Confirm hashed-fs `ArtifactStorePort` impl exists.** Survey:
  `src/veracrawl/adapters/object_stores/hashed_fs_artifact_store.py`
  or similar. If absent, draft in s15 (≤ 200 LOC).

- **`control/runtime.py` default change**: replace existing
  default with hashed-fs adapter for `ArtifactStorePort`.

- **Outbox regression**: existing outbox/replay-ref tests
  still pass with the new default.

- **Sidecar metadata determinism**: any wall-clock fields
  (e.g., `created_at`) in sidecar must be injected via
  `utc_clock` closure (s6/s12 pattern) or excluded from the
  content-hashed identity.

- **Tests** (red list ≥ 10):
  - Hashed-fs adapter: content-addressed write returns same
    Ref for same bytes; read round-trip.
  - Runtime default test (factory yields hashed-fs).
  - Outbox regression.
  - Sidecar determinism.

### Out

- New schema migrations.
- S3/GCS backed adapters (future slice).

## Design

### Module map (assumes adapter exists or new)

```
src/veracrawl/adapters/object_stores/hashed_fs_artifact_store.py  # new or modify — ≤ 200 LOC
src/veracrawl/control/runtime.py                          # modify — ≤ 30 LOC
tests/unit/adapters/object_stores/test_hashed_fs_artifact_store.py  # new — ≤ 280 LOC
tests/unit/control/test_runtime_default_artifact_store.py  # new — ≤ 100 LOC
```

Behavior LOC: 200 + 30 = **230 LOC** (or 30 wiring-only).
Under ≤ 300 cap.

### Replay invariant

- Hashed-fs adapter: `write(bytes) → Ref` where Ref =
  `f"artifact:sha256:{hexdigest}"`. Same bytes → same ref.
- `read(ref) → bytes` round-trips byte-equal.
- Sidecar (metadata) is non-content but MUST NOT affect Ref
  (only bytes do).

## Dependencies

- Existing `ArtifactStorePort` (`veracrawl.ports.stores`).
- Existing `control/runtime.py` composition root.

**Prereq**: s2.1 plan reservations note that
`ArtifactStorePort.read` was extended; s15 ensures default
adapter implements it.

## Test Strategy

### `tests/unit/adapters/object_stores/test_hashed_fs_artifact_store.py`

1. `test_write_returns_sha256_ref`.
2. `test_write_same_bytes_returns_same_ref`.
3. `test_write_different_bytes_returns_different_ref`.
4. `test_read_round_trip_byte_equal`.
5. `test_exists_true_after_write`.
6. `test_read_raises_key_error_for_unknown_ref`.
7. `test_sidecar_metadata_isolated_from_content_hash`.

### `tests/unit/control/test_runtime_default_artifact_store.py`

8. `test_default_runtime_uses_hashed_fs_artifact_store`.
9. `test_caller_can_override_default`.
10. `test_existing_outbox_tests_pass_with_new_default`.

## Acceptance Criteria

1. Pytest gate: 10 collected, 10 passed.
2. Existing suite green: `pytest tests/ -q` exits 0.
3. LOC budget ≤ 300.
4. Plan-review grep ≥ 1.
5. Task-review per commit (s6 AC7 shape).

## Rollback

s15 changes runtime default + adds files. Revert restores
existing default; outbox/replay tests would still need passing.

## Open Questions

1. **Storage root path**: configurable via env
   (`VERACRAWL_ARTIFACT_STORE_PATH`); default
   `~/.veracrawl/artifacts/`.
2. **Hash algorithm**: SHA-256 default. SHA-3 alternative
   deferred.
