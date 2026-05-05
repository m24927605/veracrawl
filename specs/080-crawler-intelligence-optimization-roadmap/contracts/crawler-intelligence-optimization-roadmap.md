# Contract: Crawler Intelligence Optimization Roadmap

## Command Types

| Command | Owner | Purpose | Required Refs |
| --- | --- | --- | --- |
| `record_crawler_optimization_roadmap` | control | Record spec 080 and approved specs 081-086 | roadmap ref, policy refs, command/event/outbox refs, replay ref |
| `record_optimization_metric_set` | ops | Record canonical optimization metric definitions and thresholds | metric refs, slice refs, policy refs, replay ref |
| `record_optimization_capability_report` | ops | Record aggregate optimization readiness over lower reports | lower report refs, blocker refs, false-ready guard refs, replay ref |

## Event Types

| Event | Payload | Required Before/After State |
| --- | --- | --- |
| `crawler_optimization_roadmap_recorded` | roadmap id, spec refs, dependency refs, status | after required |
| `optimization_metric_set_recorded` | metric keys, thresholds, slice refs | after required |
| `optimization_capability_reported` | lower reports, blockers, completion result | after required |

## Required Negative Cases

- Missing lower optimization report cannot pass.
- Optimization signal used as source evidence cannot pass.
- LLM output used as source evidence cannot pass.
- Unsafe browser/source recovery cannot pass.
- Source-limited fabrication cannot pass.
- Missing command/event/outbox or replay refs cannot pass.
- Quality, cost, latency, or duplicate regression beyond threshold cannot pass.

## Owner Boundaries

- `scheduler` owns durable frontier mutations.
- `normalize` and `browser` own DOM intelligence artifacts.
- `extract`, `evidence`, and `verify` own extraction fallback, evidence, and
  verification outcomes.
- `graph` owns graph and duplicate projections.
- `publish` owns ranked output materialization.
- `ops` owns aggregate metrics, recovery reports, and optimization release
  gates.
- `agents` may propose recommendations only through framework-neutral ports and
  controlled tools.
