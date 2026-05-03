# Contract: Live HTTP Acquisition Runtime

## CLI Contract

```text
veracrawl-live-http run tests/fixtures/<fixture_id> \
  --profile target \
  --out .veracrawl-test-runs/<fixture_id>
```

## Required Fixtures

| Fixture | Expected result |
| --- | --- |
| `live-http-success` | pass |
| `live-http-redirect` | pass with redirect hop refs |
| `live-http-scope-denied` | fail |
| `live-http-private-denied` | fail |
| `live-http-malformed-response` | fail |
| `live-http-missing-artifact` | fail |
| `live-http-replay-mismatch` | fail |
| `live-http-direct-source-bypass` | fail |

## Pass Rules

Passing reports require row 039/040 refs, network request/response refs, source
acquisition report refs, source adapter result refs, fetch attempt/result refs,
page snapshot refs, source observation refs, artifact refs, content hash refs,
canonical URL refs, policy refs, command refs, event cursor refs, outbox refs,
and replay bundle refs.
