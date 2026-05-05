# Runtime Wiring Contracts

## Commands

- `record_runtime_frontier_optimization_decision`
- `record_runtime_dom_extraction_context`
- `record_runtime_dedupe_ranking_decision`
- `record_runtime_optimization_aggregate`

## Events

- `runtime_frontier_optimization_decision_recorded`
- `runtime_dom_extraction_context_recorded`
- `runtime_dedupe_ranking_decision_recorded`
- `runtime_optimization_aggregate_recorded`

## Fixture Oracles

- `runtime-optimization-wiring-success`
- `runtime-optimization-policy-blocked-url`
- `runtime-optimization-missing-dom-anchor`
- `runtime-optimization-llm-as-evidence`
- `runtime-optimization-variant-collapse`
- `runtime-optimization-ranking-regression`
- `runtime-optimization-missing-replay`

## Module Boundary Contract

- `src/veracrawl/optimization/runtime.py` may import contracts, common helpers,
  and deterministic standard-library utilities.
- `src/veracrawl/optimization/runtime.py` must not import benchmark modules,
  model SDKs, browser engines, queue clients, storage clients, or agent
  frameworks.
- Benchmark modules may call the runtime service later, but runtime services
  must remain independently testable.
