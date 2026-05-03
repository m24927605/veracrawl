# Contract: JavaScript Browser Crawl Quality Benchmark

## Commands

| Command | Owner | Aggregate | Required policy refs | Events |
| --- | --- | --- | --- | --- |
| `record_browser_quality_observation` | browser | `BrowserQualityObservation` | `browser_interaction` | `browser_quality_observed` |
| `record_browser_quality_delta` | browser | `BrowserQualityDeltaRecord` | `browser_interaction` | `browser_quality_delta_recorded` |
| `record_browser_quality_report` | browser | `BrowserQualityReport` | `browser_interaction` | `browser_quality_reported` |
| `record_browser_quality_manifest` | tests | `BrowserQualityCorpusManifest` | none | `browser_quality_manifest_recorded` |

## Required Pass Refs

Every passing `BrowserQualityObservation` MUST include:

- live HTTP acquisition report ref
- HTTP artifact and content hash refs
- browser step ref
- DOM artifact ref
- screenshot artifact ref
- browser network trace ref
- console log ref
- timing ref
- rendered content hash ref
- recovered fragment refs
- source anchor refs
- sandbox policy ref
- browser budget ref
- prompt-taint boundary ref
- policy decision refs
- command record refs
- event cursor refs
- outbox refs
- replay bundle ref

## Failure Types

- `browser_quality_http_oracle_not_missing`
- `browser_quality_browser_oracle_not_recovered`
- `browser_quality_policy_denied`
- `browser_quality_egress_denied`
- `browser_quality_unsafe_action`
- `browser_quality_prompt_taint_bypass`
- `browser_quality_missing_artifact`
- `browser_quality_missing_anchor`
- `browser_quality_budget_exceeded`
- `browser_quality_replay_mismatch`
- `browser_quality_adapter_unavailable`
- `browser_quality_insufficient_browser_required_targets`

## CLI Contract

```sh
veracrawl-browser-quality-benchmark run \
  tests/fixtures/browser-quality-corpus \
  --profile quality \
  --browser-adapter playwright \
  --out .veracrawl-real-runs/browser-quality-corpus
```

Required output files:

- `summary.json`
- `browser_quality_report.json`
- `browser_quality_observations.json`
- `browser_quality_deltas.json`
- `state/` command/event/outbox state

## Import Boundary

- `veracrawl.benchmarks.browser_quality` MUST NOT import Playwright, Selenium,
  browser engine SDKs, or browser-native state types.
- `veracrawl.contracts.browser_quality` MUST NOT import browser engine SDKs.
- `veracrawl.adapters.browser.playwright` MAY import Playwright because it is a
  replaceable adapter.

## Non-Claims

This contract proves JS/browser rendering quality for declared targets. It does
not prove multi-page deep crawl, credentialed browsing, CAPTCHA solving, stealth
automation, field-level extraction accuracy, precision/recall, repair success,
or final production release readiness.
