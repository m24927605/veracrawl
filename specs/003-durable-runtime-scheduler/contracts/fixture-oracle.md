# Contract: Durable Fixture Oracles

## Required Fixtures

| Fixture | Expected result |
| --- | --- |
| durable-runtime-success | `pass`, reloadable state, no missing refs |
| durable-duplicate-command | `pass`, one event and one outbox for duplicate command |
| durable-event-gap | `fail`, event gap reported |
| durable-pending-outbox | `needs_review`, pending outbox reported |
| durable-stale-lease | `needs_review`, stale lease reported and item retryable |
| durable-invalid-lease | `fail`, invalid lease mutation rejected |
| durable-missing-artifact | `fail`, missing artifact blocks recovery |

## Manifest Shape

```json
{
  "id": "durable-runtime-success",
  "scenario": "runtime-success",
  "profile_refs": ["target"],
  "expected_completion_result": "pass",
  "expected_operator_status": "durable_recovered",
  "expected_publication": false,
  "required_ref_types": ["command_records", "event_cursors", "outbox", "artifacts", "leases"]
}
```

## Runner Behavior

`veracrawl-durable run <fixture_dir> --profile target --out <output_dir>` writes `run_report.json` with:

- fixture id
- scenario
- profile
- completion result
- operator status
- command record refs
- event cursor refs
- outbox refs
- artifact refs
- frontier item refs
- lease refs
- recovery report ref
- missing ref fields
