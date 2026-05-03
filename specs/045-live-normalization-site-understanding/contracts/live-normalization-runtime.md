# Contract: Live Normalization Runtime

## CLI Contract

```text
veracrawl-live-normalization run tests/fixtures/<fixture_id> \
  --profile target \
  --out .veracrawl-test-runs/<fixture_id>
```

## Required Fixtures

| Fixture | Expected result |
| --- | --- |
| `live-normalization-listing-success` | pass |
| `live-normalization-detail-success` | pass |
| `live-normalization-browser-success` | pass |
| `live-normalization-missing-upstream` | fail |
| `live-normalization-empty-content` | fail |
| `live-normalization-missing-anchor-map` | fail |
| `live-normalization-missing-site-model` | fail |
| `live-normalization-replay-mismatch` | fail |

## Pass Rules

A passing report requires upstream acquisition refs, normalized document refs,
normalization manifests, anchor maps/source anchors, link analysis, page type,
site model, artifacts, policy, command/event/outbox, and replay refs. Linked
pages include link provenance refs. Linkless pages include a deterministic
no-link analysis ref and must not fabricate link provenance.
