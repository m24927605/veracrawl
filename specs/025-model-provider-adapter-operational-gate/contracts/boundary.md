# Contract: Model Provider Boundary

- Core packages must not import `openai`, `anthropic`, `google.generativeai`, `google.genai`, provider SDKs, local runtime clients, or `veracrawl.adapters.model_providers`.
- Provider SDK imports are allowed only inside provider adapter modules.
- `veracrawl-model-providers` must dynamically import adapter modules.
- Provider-native transcript state is diagnostic only and cannot satisfy canonical replay or completion.
- Raw prompts, raw responses, raw credentials, and unsafe tool suggestions cannot be persisted as canonical state.
- Missing live provider runtime/API credentials return `needs_review`.
- This feature does not claim production model provider account readiness, vendor uptime, token billing, model selection optimization, or production AI operations.
