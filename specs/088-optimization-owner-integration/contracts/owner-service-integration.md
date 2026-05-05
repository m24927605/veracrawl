# Contract: Optimization Owner-Service Integration

## Command Types

| Command | Owner | Purpose | Required Refs |
| --- | --- | --- | --- |
| `record_optimization_owner_integration_roadmap` | control | Record specs 088-096 as approved integration set | spec refs, dependency refs, policy refs, command/event/outbox refs, replay ref |
| `record_scheduler_optimization_integration` | scheduler | Record optimized frontier adoption | frontier decision refs, enqueue/block/retire/stop refs, policy refs, replay ref |
| `record_normalize_optimization_integration` | normalize | Record DOM intelligence adoption | normalized document ref, DOM context ref, artifact refs, replay ref |
| `record_extract_verify_optimization_integration` | extract_verify | Record extractor fallback and field verification adoption | extractor refs, confidence refs, abstention/review refs, replay ref |
| `record_dedupe_identity_optimization_integration` | graph | Record canonical dedupe and identity adoption | canonical refs, fingerprint refs, identity refs, retained/suppressed refs, replay ref |
| `record_ranking_publication_optimization_integration` | publish | Record ranked publication projection adoption | ranked output ref, ranking score refs, publication gate refs, replay ref |
| `record_cost_cache_budget_optimization_integration` | ops | Record cost/cache/budget integration | cost values, cache refs, metric refs, replay ref |
| `record_drift_recovery_feedback_integration` | ops | Record drift and repair feedback | drift refs, repair refs, diagnostics, replay ref |
| `record_optimization_regression_release_gate` | ops | Record aggregate integration release gate | lower integration refs, metric refs, false-ready guards, replay ref |

## Event Types

| Event | Payload | Required Before/After State |
| --- | --- | --- |
| `optimization_owner_integration_roadmap_recorded` | specs 088-096, dependencies, status | after required |
| `scheduler_optimization_integrated` | enqueue/block/retire/stop refs | after required |
| `normalize_optimization_integrated` | DOM context and artifact refs | after required |
| `extract_verify_optimization_integrated` | accepted/rejected/abstained field refs | after required |
| `dedupe_identity_optimization_integrated` | retained/suppressed/variant refs | after required |
| `ranking_publication_optimization_integrated` | ranked output and score refs | after required |
| `cost_cache_budget_optimization_integrated` | metric and cache refs | after required |
| `drift_recovery_feedback_integrated` | drift/recovery diagnostics | after required |
| `optimization_regression_release_gated` | lower refs, metrics, pass/fail diagnostics | after required |

## Required Negative Cases

- Policy-blocked URL cannot enqueue.
- Missing DOM source anchor cannot pass normalize integration.
- LLM-only, graph-only, memory-only, or ranking-only value cannot be accepted.
- Duplicate suppression cannot collapse declared variants.
- Ranking cannot modify verification status or fabricate optional fields.
- Stale cache reuse or budget overrun cannot pass cost/cache integration.
- Unsafe repair, owner bypass, or policy weakening cannot pass drift feedback.
- Missing lower integration refs, metric refs, command/event/outbox refs, or
  replay refs cannot pass the regression release gate.

## Owner Boundaries

- `scheduler` owns frontier enqueue/block/retire/stop adoption.
- `normalize` and `browser` own DOM context and prompt-taint adoption.
- `extract` and `verify` own field acceptance, rejection, abstention, and
  review routing.
- `graph` owns identity and duplicate projections.
- `publish` and `projection` own ranked output materialization.
- `ops` owns cost/cache/recovery metrics and aggregate release decisions.
- `agents` may recommend repairs or priorities only through controlled,
  framework-neutral ports and typed owner-service commands.
