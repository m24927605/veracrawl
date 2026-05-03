# Contract: Production Persistence Runtime Wiring

## CLI Contract

```text
veracrawl-production-persistence run tests/fixtures/<fixture_id> \
  --profile target \
  --out .veracrawl-test-runs/<fixture_id>
```

The runner writes:

```text
.veracrawl-test-runs/<fixture_id>/run_report.json
.veracrawl-test-runs/<fixture_id>/state/
```

## Required Fixtures

| Fixture | Expected result |
| --- | --- |
| `production-persistence-wiring-success` | pass |
| `production-persistence-idempotent-replay` | pass with duplicate dedupe and no duplicate event/outbox side effects |
| `production-persistence-queue-recovery` | pass with heartbeat, nack, dead-letter, failure, and recovery refs |
| `production-persistence-non-atomic-commit` | fail |
| `production-persistence-canonical-state-missing` | fail |
| `production-persistence-idempotency-missing` | fail |
| `production-persistence-event-gap` | fail |
| `production-persistence-outbox-missing` | fail |
| `production-persistence-artifact-index-missing` | fail |
| `production-persistence-lease-heartbeat-missing` | fail |
| `production-persistence-replay-missing` | fail |

## Report Rules

- `completion_result=pass` requires adapter, transaction, canonical state,
  run-control command, persistence command, idempotency, event cursor, outbox,
  artifact, queue operation, lease, policy, and replay refs.
- Duplicate replay pass requires `duplicate_deduped=true`, `event_count` equal
  to the pre-duplicate count, and `outbox_count` equal to the pre-duplicate
  count.
- Queue recovery pass requires nack, dead-letter, failure, recovery, lease, and
  heartbeat refs.
- Negative fixtures must set `completion_result=fail`, a typed `failure_type`,
  and `missing_ref_fields`.

## Boundary Rules

- Core runtime imports contracts and ports only.
- CLI and adapter-owned packages may choose reference or concrete adapters.
- No core package may import psycopg, redis, boto3, botocore, browser libraries,
  model SDKs, or agent frameworks.
