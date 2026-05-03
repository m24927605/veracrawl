# Data Model: Top Ecommerce Live AI Benchmark

## TopEcommercePublicCorpusFixture

Reuses `RealWorldBenchmarkCorpusManifest`.

Fields:

- `id`: `top-ecommerce-public-corpus`.
- `allowed_origin_refs`: the six declared ecommerce origins.
- `rate_budget_ref`: one homepage request per origin.
- `site_specs`: six `RealWorldBenchmarkSiteSpec` rows with target URL, robots
  URL, expected status/content type/body size, coarse title/body fragments, and
  target pattern refs.
- `required_ref_types`: live HTTP, artifact, content hash, canonical URL,
  command/event/outbox, and replay refs.

Validation:

- All targets must be public http(s) URLs.
- All robots URLs must share the target origin.
- Private network targets fail validation.
- Passing observations require matched coarse oracles and replay refs.

## TopEcommerceAIAgentCorpusFixture

Reuses `RealWorldAIAgentBenchmarkManifest`.

Fields:

- `id`: `top-ecommerce-ai-agent-corpus`.
- `real_world_corpus_fixture_path`:
  `tests/fixtures/top-ecommerce-public-corpus`.
- `required_public_site_count`: `6`.
- `required_decision_types`: crawl planning, site understanding, extraction
  candidate generation, verification/repair.
- `required_ref_types`: model, agent, tool, context, source anchor, extraction
  candidate, evidence/verification gate, command/event/outbox, and replay refs.

Validation:

- Passing AI reports require a passing public corpus run first.
- Each public site requires four AI decisions.
- Extraction candidates require source anchors, artifacts, and content hashes.
- Model/agent output cannot satisfy source evidence requirements.

## ValidationRunOutput

Files:

- `run_report.json`
- `summary.json`
- `site_observations.json`
- `decision_traces.json`
- `model_call_traces.json`
- `agent_action_traces.json`
- `tool_call_traces.json`
- `context_bundle_traces.json`
- `extraction_candidates.json`

Validation:

- Hosted OpenAI run must show non-empty model/agent/tool/context trace files.
- The task log records exact counts and pass/fail status.
