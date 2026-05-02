# Contract: Source Fixture Oracles

## Required Fixtures

| Fixture | Expected result |
| --- | --- |
| source-http-success | pass |
| source-sitemap-success | pass |
| source-rss-success | pass |
| source-api-success | pass |
| source-document-success | pass |
| source-blocked | fail, source_blocked |
| source-rate-limited | needs_review, source_rate_limited |
| source-adapter-mismatch | fail, adapter_mismatch |
| source-malformed-response | fail, malformed_response |
| source-retry-exhausted | fail, retry_exhausted |
| source-missing-artifact | fail, missing_raw_artifact |

## Runner

`veracrawl-source run <fixture_dir> --profile target --out <output_dir>` writes `run_report.json` with source result refs, fetch refs, artifact refs, durable refs, scheduler refs, recovery refs, completion result, operator status, and missing ref fields.
