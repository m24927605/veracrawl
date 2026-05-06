# Contract: Optimization Objective Gate

## Command Types

| Command | Owner | Purpose | Required Refs |
| --- | --- | --- | --- |
| `record_optimization_objective_score` | ops | Record deterministic weighted optimization objective score | formula ref, metric refs, algorithm refs, policy refs, command/event/outbox refs, artifact refs, replay ref |
| `record_agent_decision_loop_evidence` | agents/ops | Record observe/think/act/verify evidence for optimization-affecting agent decisions | phase refs, confidence threshold, stop condition, deterministic refs, policy refs, trace refs, command/event/outbox refs, artifact refs, replay ref |
| `record_optimization_objective_release_gate` | ops | Record final objective release gate over lower regression gates, objective scores, and agent evidence | 096 lower gate refs, objective score refs, agent loop refs, metric refs, algorithm refs, policy refs, command/event/outbox refs, artifact refs, replay ref |

## CLI Evidence Command

```text
veracrawl-crawler-optimization run-objective-gate <fixture_dir> --out <dir>
```

The command must write:

- `optimization_regression_release_gate.json`
- `optimization_objective_score.json`
- `agent_decision_loop_evidence.json`
- `optimization_objective_release_gate.json`
- `metric_slice.json`
- `summary.json`

The command is deterministic and local-fixture only. It does not call live
network, browser engines, LLM/model SDKs, concrete storage, queues, or adapters.

## Event Types

| Event | Payload | Required Before/After State |
| --- | --- | --- |
| `optimization_objective_score_recorded` | component scores, computed score, threshold, diagnostics | after required |
| `agent_decision_loop_evidence_recorded` | observe/think/act/verify refs, confidence, fallback boundary, diagnostics | after required |
| `optimization_objective_release_gated` | lower gates, score refs, agent refs, pass/fail diagnostics | after required |

## Score Formula

```text
OptimizationScore =
  0.35 * extraction_accuracy
+ 0.25 * intent_match_precision
+ 0.15 * crawl_success_rate
+ 0.10 * dedupe_quality
+ 0.10 * freshness
- 0.03 * normalized_latency
- 0.02 * normalized_cost
```

The implementation must store the formula ref
`optimization-score-v1-weighted-accuracy-time-cost`, component values, computed
score, and threshold. Component values are normalized from 0.0 through 1.0.

## Fallback And Decision Chain

```text
observe:
  collect lower metric refs, policy refs, crawl/replay refs, and page evidence refs

think:
  use deterministic rules to compute score, detect missing refs, check thresholds,
  classify failures, and choose whether LLM fallback is allowed

act:
  record objective-score report, agent-loop evidence, or release gate through
  typed commands and events

verify:
  validate formula, thresholds, replay refs, policy refs, lower gate pass status,
  LLM fallback boundaries, and negative guards
```

LLM fallback may propose semantic labels, repair hypotheses, or structured
extraction attempts only when deterministic methods cannot decide. It cannot be
the final evidence for a source fact, publication claim, or release gate pass.

## Required Negative Cases

- `optimization-objective-low-score`: score below threshold fails.
- `optimization-objective-formula-mismatch`: supplied score does not match
  component formula.
- `optimization-objective-missing-policy`: missing policy refs fail.
- `optimization-objective-missing-replay`: missing command/event/outbox/artifact
  or replay refs fail.
- `optimization-objective-missing-algorithms`: missing algorithm refs fail.
- `agent-decision-missing-phase`: missing observe, think, act, or verify refs
  fail.
- `agent-decision-low-confidence`: confidence below threshold fails.
- `agent-decision-missing-stop`: missing stop condition fails.
- `agent-decision-llm-output-as-evidence`: LLM output evidence refs fail pass.
- `objective-release-missing-lower-gate`: missing 096 gate refs fail.
- `objective-release-failed-lower-gate`: failed lower refs fail.

## Owner Boundaries

- `ops` owns objective score computation and aggregate release-gate decision.
- `review_replay` owns replay gap detection for objective reports and agent
  loop evidence.
- `agents` may emit decision traces and fallback proposals through
  framework-neutral typed refs only.
- Lower owner services from specs 089-096 own their domain-specific decisions.
  097 consumes their refs and never mutates lower owner state directly.

## Pseudo Code

```python
def compute_score(metrics):
    return (
        0.35 * metrics.extraction_accuracy
        + 0.25 * metrics.intent_match_precision
        + 0.15 * metrics.crawl_success_rate
        + 0.10 * metrics.dedupe_quality
        + 0.10 * metrics.freshness
        - 0.03 * metrics.normalized_latency
        - 0.02 * metrics.normalized_cost
    )

def objective_report(metrics, refs, threshold):
    score = compute_score(metrics)
    missing = required_refs(refs)
    if missing:
        return fail("missing_replay_refs", missing)
    if score < threshold:
        return fail("quality_regression", ["score_below_threshold"])
    return pass_report(score)

def decision_loop_evidence(loop):
    if not loop.observe or not loop.think or not loop.act or not loop.verify:
        return fail("missing_replay_refs", ["missing_phase"])
    if loop.confidence < loop.threshold:
        return fail("quality_regression", ["low_confidence"])
    if loop.llm_output_evidence_refs:
        return fail("policy_blocked", ["llm_output_as_evidence"])
    return pass_report(loop)

def objective_release_gate(lower_gates, scores, loops, refs):
    if any(g.failed for g in lower_gates) or missing_required_lower(lower_gates):
        return fail("quality_regression", ["lower_gate_failed"])
    if any(s.failed for s in scores) or any(l.failed for l in loops):
        return fail("quality_regression", ["objective_or_agent_failed"])
    if required_refs(refs):
        return fail("missing_replay_refs", required_refs(refs))
    return pass_gate()
```
