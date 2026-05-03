# Contract: Credentialed Session Runtime

## CLI Contract

```text
veracrawl-credentialed-session run tests/fixtures/<fixture_id> \
  --profile target \
  --out .veracrawl-test-runs/<fixture_id>
```

## Required Fixtures

| Fixture | Expected result |
| --- | --- |
| `credentialed-session-success` | pass |
| `credentialed-session-missing-authorization` | fail |
| `credentialed-session-out-of-scope` | fail |
| `credentialed-session-raw-secret-leak` | fail |
| `credentialed-session-unsafe-use` | fail |
| `credentialed-session-missing-audit` | fail |
| `credentialed-session-missing-redacted-replay` | fail |
| `credentialed-session-replay-mismatch` | fail |

## Pass Rules

A passing report requires live HTTP and browser snapshot prerequisite refs,
credential audit refs, scope/origin/approval refs, session adapter result refs,
redacted session artifacts, redaction map refs, redacted replay refs,
command/event/outbox refs, policy refs, and replay refs. Raw secrets and
adapter-native session state must not be canonical.
