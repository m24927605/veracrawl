# Data Model: Cost Latency Stability Release Gate

## QualityReleaseThresholds

Declares required prior gate count, minimum stability run count, max total cost,
max p95 latency, minimum throughput, max retry rate, token/model-call budgets,
and max stability variance.

## QualityReleaseGateRef

References one passing prior quality gate report and its replay, policy,
command, event, and outbox refs.

## QualityReleaseStabilityRun

Records one run's cost, p95 latency, throughput, retry rate, token count, model
call count, SLO metric refs, policy refs, command/event/outbox refs, and replay
ref.

## QualityReleaseReport

Aggregates prior gate refs and stability runs into the final release decision,
with typed failure diagnostics and replayable release decision/audit refs.

## QualityReleaseManifest

Declares fixture scenario, expected completion, expected release decision,
expected failure type, required gate refs, and thresholds.
