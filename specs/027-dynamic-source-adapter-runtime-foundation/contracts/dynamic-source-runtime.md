# Contract: Dynamic Source Runtime Gate

## CLI

```text
veracrawl-source-runtime run tests/fixtures/<fixture_id> --profile target --out .veracrawl-test-runs/<fixture_id>
```

## Required Fixtures

- `dynamic-source-runtime-success`
- `dynamic-source-runtime-runtime-unavailable`
- `dynamic-source-runtime-raw-secret-leak`
- `dynamic-source-runtime-adapter-state-canonical`
- `dynamic-source-runtime-missing-credential-audit`
- `dynamic-source-runtime-missing-document-artifact`
- `dynamic-source-runtime-missing-api-payload`
- `dynamic-source-runtime-missing-replay`
- `dynamic-source-runtime-unsafe-browser-side-effect`
- `dynamic-source-runtime-unsupported-adapter`

## Boundary

- Core gate imports only VeraCrawl contracts.
- CLI imports deterministic/local adapter builder dynamically.
- Non-fetch adapters are accepted only through native refs.
