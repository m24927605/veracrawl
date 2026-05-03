# Research: Repair Success Rate Benchmark

## Decisions

- Use deterministic seeded repair fixtures instead of uncontrolled live drift.
  This keeps the benchmark repeatable while still covering the target failure
  families that production crawls experience.
- Treat AI-assisted repair as a traceable decision path, not source evidence.
  Every repair attempt records model call, agent action, tool call, context
  bundle, owner-service command, policy, before/after evidence, rollback or
  escalation, command/event/outbox, and replay refs.
- Count repaired and rollback-applied outcomes as repair successes for
  repairable cases. Failed-safe and escalated cases are safe outcomes but do not
  count as success.
- Enforce three release-blocking thresholds: repair success rate >= 0.80,
  unsafe bypass rate = 0, and unresolved critical repair rate = 0.

## Alternatives Considered

- Live website drift injection: rejected for this row because public sites drift
  unpredictably and can make failure injection unethical or non-repeatable.
- Framework-native agent state in the benchmark: rejected because VeraCrawl core
  must remain framework-neutral and replay canonical VeraCrawl contracts.
- Counting model-proposed fixes without evidence as successes: rejected because
  LLM output cannot serve as source evidence or publication proof.
