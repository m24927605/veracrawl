# Contract: Model Provider Adapter Gate

## CLI

```text
veracrawl-model-providers run tests/fixtures/<fixture_id> --profile target --out .veracrawl-test-runs/<fixture_id>
```

## Required Fixtures

| Fixture | Expected |
| --- | --- |
| model-provider-adapter-success | pass |
| model-provider-adapter-runtime-unavailable | needs_review |
| model-provider-adapter-raw-prompt-leak | fail |
| model-provider-adapter-raw-response-leak | fail |
| model-provider-adapter-provider-state-canonical | fail |
| model-provider-adapter-missing-context-trace | fail |
| model-provider-adapter-missing-replay | fail |
| model-provider-adapter-missing-security-privacy | fail |
| model-provider-adapter-unsafe-tool-suggestion | fail |
| model-provider-adapter-unsupported-provider | fail |

## Required Provider Families

- OpenAI
- Anthropic
- Google Gemini
- OpenAI-compatible endpoint
- Local model runtime
- FutureProvider

## Pass Requirements

- provider execution refs for every required provider family
- model request refs
- model response refs
- model call trace refs
- context bundle trace refs
- agent run/action refs
- command records
- policy refs
- observability refs
- security/privacy refs
- event cursor refs
- outbox refs
- replay bundle ref

## Failure Requirements

The report fails for raw prompt leakage, raw response leakage, raw credential leakage, provider-native transcript as canonical state, unsafe tool suggestions without policy/command blocking refs, missing context trace, missing replay refs, missing security/privacy refs, or unsupported provider names.
