# Contract: Live Evidence And Verification Runtime

## CLI Contract

```text
veracrawl-live-evidence run tests/fixtures/<fixture_id> \
  --profile target \
  --out .veracrawl-test-runs/<fixture_id>
```

## Required Fixtures

| Fixture | Expected result |
| --- | --- |
| `live-evidence-verification-success` | pass |
| `live-evidence-verification-missing-schema-extraction` | fail |
| `live-evidence-verification-missing-source-anchor` | needs_review |
| `live-evidence-verification-stale-evidence` | fail |
| `live-evidence-verification-contradiction` | fail |
| `live-evidence-verification-graph-only` | fail |
| `live-evidence-verification-memory-only` | fail |
| `live-evidence-verification-conflict` | needs_review |
| `live-evidence-verification-publication-bypass` | fail |
| `live-evidence-verification-replay-mismatch` | fail |

## Pass Rules

A passing report requires schema extraction refs, candidate refs, source anchor
refs, evidence coverage refs, evidence packet refs, evidence anchor refs,
evidence manifest refs, verification decision refs, review decision refs,
freshness refs, policy/privacy refs, command/event/outbox refs, and replay refs.

Passing reports must not include publication, output manifest, export, delivery,
or publication report refs. Graph, memory, and agent reasoning refs may be
diagnostic but cannot satisfy evidence coverage.
