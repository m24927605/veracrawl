# Data Model: Production Benchmark And Release Gate

## ProductionBenchmarkReleaseReport

Top-level row 054 aggregate proving target production readiness can be approved
or blocked from canonical refs.

Required for pass:

- dependency refs: target runtime, source coverage, product acceptance,
  security/privacy, result publication/export, worker orchestration, and ops
  replay/observability reports
- benchmark refs: authorized manifest, authorized corpus, scenario, benchmark
  run, SLO metric, release decision, and audit refs
- gate refs: source, processing, evidence, verification, publication, export,
  replay, ops, scale, safety, policy, command, event cursor, outbox, artifact,
  and redaction refs

Pass is rejected when typed failures, missing gate refs, SLO violation refs,
release blocker refs, false-ready refs, replay gaps, or missing ref fields are
present.

Non-pass requires:

- `failure_type`
- at least one of `failure_report_refs`, `missing_gate_refs`,
  `slo_violation_refs`, `release_blocker_refs`, `false_ready_refs`,
  `replay_gap_refs`, or `missing_ref_fields`

## ProductionBenchmarkReleaseFixtureManifest

Fixture manifest for target-profile deterministic release fixtures.

Required:

- `target` profile
- expected completion result and release status
- expected failure type for negative cases
- required gate refs list

## Failure Types

- `production_release_missing_target_runtime`
- `production_release_missing_source_coverage`
- `production_release_missing_product_acceptance`
- `production_release_missing_security_privacy`
- `production_release_missing_publication`
- `production_release_missing_worker_orchestration`
- `production_release_missing_ops_runtime`
- `production_release_slo_violation`
- `production_release_blocker_present`
- `production_release_false_ready`
- `production_release_replay_mismatch`
