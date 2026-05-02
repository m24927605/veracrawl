# Contract: Security Privacy Lifecycle Gate

## CLI

```text
veracrawl-security-privacy run tests/fixtures/<fixture_id> --profile target --out .veracrawl-test-runs/<fixture_id>
```

## Pass Contract

Passing reports require:

- security policy check refs
- credential use audit refs
- prompt taint boundary refs
- artifact lifecycle action refs
- projection cleanup refs
- redacted replay refs
- observability refs
- policy, command, event cursor, and outbox refs
- failure and recovery action refs
- leakage count equal to 0

## Needs-Review Contract

`security-privacy-policy-only` returns `needs_review` and cannot claim pass.

## Negative Contract

Negative fixtures fail for unsafe network, prompt-injection tool misuse, credential leakage, missing lifecycle propagation, legal-hold delete, missing projection cleanup, missing redacted replay, and missing observability refs.

## Boundary Contract

Core validation must not import browser libraries, model SDKs, agent frameworks, cloud SDKs, security vendor SDKs, or site-specific scraper modules.
