# Contract: Process Fixture Oracle

Required success fixtures:

- `process-static-basic`
- `process-link-provenance`
- `process-anchored-candidate`

Required negative fixtures:

- `process-missing-raw`
- `process-empty-content`
- `process-anchor-gap`

Runner:

```text
veracrawl-process run tests/fixtures/<process_fixture_id> --profile target --out .veracrawl-test-runs/<process_fixture_id>
```
