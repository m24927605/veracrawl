# Contract: Source Coverage Adapter Gate

## CLI

```text
veracrawl-source-coverage run tests/fixtures/<fixture_id> --profile target --out .veracrawl-test-runs/<fixture_id>
```

## Required Fixtures

| Fixture | Expected |
| --- | --- |
| source-coverage-adapter-success | pass |
| source-coverage-adapter-runtime-unavailable | needs_review |
| source-coverage-adapter-native-state-canonical | fail |
| source-coverage-adapter-raw-secret-leak | fail |
| source-coverage-adapter-missing-browser-refs | fail |
| source-coverage-adapter-missing-credential-audit | fail |
| source-coverage-adapter-missing-document-artifact | fail |
| source-coverage-adapter-missing-api-payload | fail |
| source-coverage-adapter-missing-replay | fail |
| source-coverage-adapter-unsafe-browser-side-effect | fail |
| source-coverage-adapter-unsupported-adapter | fail |

## Required Adapter Families

- HTTP
- sitemap
- RSS/feed
- browser snapshot
- authorized session
- API-like source
- document source
- file import
- manual seed
- prior snapshot
