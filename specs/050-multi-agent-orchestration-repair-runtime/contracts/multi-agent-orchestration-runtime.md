# Contract: Multi-Agent Orchestration And Repair Runtime

## CLI

```text
veracrawl-agent-workflow run tests/fixtures/<multi_agent_fixture_id> --profile target --out <output_dir>
```

The CLI must write `run_report.json` and fail when completion or operator status
does not match the fixture manifest.

## Required Runtime Behavior

- Passing workflows must include row 049 real agent/model adapter runtime refs.
- Passing workflows must include row 047 live evidence verification refs.
- Planner, frontier, fetch-analysis, extractor, verifier, drift, memory, and ops
  roles must be represented in workflow or trace refs where applicable.
- Handoffs, coordination decisions, repair signals, controlled tool refs, owner
  command refs, policy refs, command/event/outbox refs, and replay refs must be
  complete.
- Agents cannot directly mutate canonical stores.
- Agent reasoning, graph refs, memory refs, or temporal KG refs cannot satisfy
  source evidence requirements.

## Required Fixtures

| Fixture | Expected |
| --- | --- |
| multi-agent-repair-success | pass |
| coordination-arbitration-success | pass |
| repair-loop-evidence-success | pass |
| crawl-repair-success | pass |
| extraction-repair-success | pass |
| owner-service-bypass | fail |
| unresolved-coordination-conflict | fail |
| agent-reasoning-as-evidence | fail |
| multi-agent-missing-agent-model-runtime | fail |
| multi-agent-missing-live-evidence | fail |
| multi-agent-missing-tool-gate | fail |
| multi-agent-missing-owner-command | fail |
| multi-agent-replay-mismatch | fail |

## Registry Additions

This spec extends existing multi-agent contracts, commands, events, fixtures, and
the `agent_runtime` target area. No new owner service is introduced.
