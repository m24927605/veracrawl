# Contract: Browser Snapshot Runtime

## CLI Contract

```text
veracrawl-browser-snapshot run tests/fixtures/<fixture_id> \
  --profile target \
  --out .veracrawl-test-runs/<fixture_id>
```

## Required Fixtures

| Fixture | Expected result |
| --- | --- |
| `browser-snapshot-success` | pass |
| `browser-snapshot-egress-denied` | fail |
| `browser-snapshot-unsafe-interaction` | fail |
| `browser-snapshot-budget-exceeded` | fail |
| `browser-snapshot-prompt-tainted-content` | fail |
| `browser-snapshot-missing-artifact` | fail |
| `browser-snapshot-replay-mismatch` | fail |

## Pass Rules

A passing report requires:

- upstream `LiveHttpAcquisitionReport` and
  `StructuredSourceAdaptersRuntimeReport` refs
- sandbox policy and browser interaction step refs
- DOM, screenshot, network trace, console log, timing, and browser budget refs
- policy, command, event cursor, outbox, and replay refs
- no browser-native adapter state persisted as canonical state

## Failure Rules

Negative fixtures must fail with typed `BrowserSnapshotFailureType` values and
must include failure report refs plus missing ref fields. Prompt-tainted content
must be blocked before downstream normalization or model context construction.
