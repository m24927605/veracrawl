# Research: VeraCrawl Multi-Agent Repair

## Decisions

- Workflows are VeraCrawl contracts, not framework-native state.
- Handoffs are explicit replayable records.
- Coordination decisions resolve conflicts and apply through owner commands.
- Repair loops require before/after evidence and rollback refs.
- Agent reasoning is diagnostic context, not source evidence.
