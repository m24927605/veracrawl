# Contract: Multi-Agent Repair

## Commands

- `start_multi_agent_workflow`
- `record_agent_handoff`
- `record_coordination_decision`
- `record_multi_agent_repair_report`

## Events

- `multi_agent_workflow_started`
- `multi_agent_workflow_completed`
- `agent_handoff_completed`
- `coordination_decision_recorded`

## Invariants

- pass requires workflow, handoff, coordination, repair, agent trace, policy, command, event cursor, and outbox refs.
- applied coordination requires owner command ref.
- repair requires before/after evidence and rollback refs.
