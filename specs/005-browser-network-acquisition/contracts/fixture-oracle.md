# Contract: Network And Browser Fixture Oracle

## Required Fixtures

Success:

- `network-http-success`
- `network-http-redirect`
- `network-browser-readonly`

Negative:

- `network-robots-blocked`
- `network-private-denied`
- `network-egress-denied`
- `network-rate-budget`
- `network-size-budget`
- `network-redirect-denied`
- `network-timeout`
- `network-browser-unsafe-side-effect`

## Fixture Layout

```text
tests/fixtures/<fixture_id>/
  manifest.yaml
  oracles/
    expected_outputs.yaml
    expected_events.yaml
    expected_replay.yaml
    thresholds.yaml
  README.md
```

## Runner Contract

```text
veracrawl-network run tests/fixtures/<fixture_id> --profile target --out .veracrawl-test-runs/<fixture_id>
```

## Acceptance

- Success fixtures produce `completion_result: pass`.
- Negative fixtures produce the expected typed operator status and never accept forbidden artifact refs.
- Every report is canonical JSON and includes replay-critical refs.
