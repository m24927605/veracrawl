# Contract: Structured Source Adapters Runtime

## CLI Contract

```text
veracrawl-structured-source run tests/fixtures/<fixture_id> \
  --profile target \
  --out .veracrawl-test-runs/<fixture_id>
```

## Required Fixtures

| Fixture | Expected result |
| --- | --- |
| `structured-source-adapters-success` | pass |
| `structured-source-adapters-policy-denied` | fail |
| `structured-source-adapters-malformed-source` | fail |
| `structured-source-adapters-unsupported-adapter` | fail |
| `structured-source-adapters-replay-mismatch` | fail |

## Pass Rules

Passing reports require all five structured source adapter families:
`sitemap`, `rss`, `api_source`, `document_source`, and `file_import`. Each
passing adapter record requires source adapter result refs, natural output refs,
artifact refs, evidence seed refs, content hash refs, policy refs, command refs,
event cursor refs, outbox refs, and replay refs. Sitemap/RSS must include
discovered URL refs; API-like sources must include API payload refs; document
sources must include document artifact refs; file imports must include file
artifact refs.
