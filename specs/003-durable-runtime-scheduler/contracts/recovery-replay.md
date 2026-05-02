# Contract: Recovery And Replay

## Durable Replay Recovery

Recovery validates:

- durable command records
- command result refs
- event cursor refs
- outbox refs
- artifact refs
- frontier item refs
- queue lease refs
- scheduler recovery refs
- deterministic clock and redaction refs

## Completion Rules

The durable recovery result is:

- `pass` when every required ref is present and no gaps are reported
- `needs_review` when a pending outbox or recoverable stale lease exists
- `fail` when event gaps, missing artifacts, invalid lease mutations, dead letters, or missing command refs exist

Publication or completion must not pass when recovery result is `fail` or when required refs are missing.

## Operator Diagnostics

Every non-pass report must list the blocking field names and operator-visible status, for example:

- `event_gap`
- `pending_outbox`
- `stale_lease`
- `invalid_lease`
- `missing_artifact`
- `dead_letter`
