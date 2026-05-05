# Data Model: Crawler Intelligence Optimization Roadmap

## CrawlerOptimizationRoadmap

- **Purpose**: Records the approved optimization spec set and dependency order.
- **Fields**:
  - `id`
  - `spec_refs`
  - `dependency_refs`
  - `closure_gate_refs`
  - `activation_policy_ref`
  - `roadmap_status`
  - `policy_decision_refs`
  - `replay_bundle_ref`
- **Validation Rules**:
  - Must include specs 081-087.
  - Must state that specs 081-087 do not replace or weaken specs 069-075.
  - Must carry refs to docs/08 and specs/038/068 when those roadmap docs are
    updated.

## OptimizationMetricSet

- **Purpose**: Canonical metric set for optimization validation.
- **Fields**:
  - `crawl_precision`
  - `crawl_recall`
  - `extraction_accuracy`
  - `duplicate_rate`
  - `crawl_success_rate`
  - `cost_per_successful_result`
  - `latency_p50_p95_p99`
  - `token_usage_per_successful_result`
  - `browser_seconds_per_successful_result`
  - `cache_hit_rate`
  - `repair_success_rate`
  - `ranking_ndcg_mrr_precision_at_k`
  - `replay_completeness`
  - `slice_refs`
- **Validation Rules**:
  - Metrics must be sliced by site, source type, page pattern, schema, field,
    acquisition mode, and ranking profile where applicable.
  - Metrics that affect release readiness must have thresholds or explicit
    needs-review status.

## OptimizationCapabilityReport

- **Purpose**: Aggregate report for optimization readiness across lower specs.
- **Fields**:
  - `id`
  - `roadmap_ref`
  - `lower_report_refs`
  - `missing_lower_report_refs`
  - `metric_set_ref`
  - `blocker_refs`
  - `false_ready_guard_refs`
  - `policy_decision_refs`
  - `command_record_refs`
  - `event_cursor_refs`
  - `outbox_refs`
  - `replay_bundle_ref`
  - `completion_result`
- **Validation Rules**:
  - Passing reports require all required lower reports and no blockers.
  - Missing replay, unsafe recovery, LLM-as-evidence, graph/memory-as-evidence,
    source-limited fabrication, stale cache reuse, or quality regression must
    block pass.

## State Transitions

```text
planned -> activated -> implemented -> validated -> optimization_release_ready
planned -> activated -> blocked
validated -> superseded
```

- `activated` requires an implementation spec plan/tasks set.
- `validated` requires passing contract, fixture, negative, replay, and
  benchmark tests for that spec.
- `optimization_release_ready` requires spec 086 aggregate pass plus spec 087
  runtime wiring evidence before owner services consume optimization decisions.
