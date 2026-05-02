# Contract: Agent Recommendation Intake

## Purpose

Define how framework-neutral agent recommendations can contribute to the runtime spine without owning durable state.

## Recommendation Subjects

Agents may propose:

- crawl plan assumptions, alternatives, and adapter rationale
- extraction strategy or field mapping
- evidence anchor candidates
- verification recommendation
- repair or recovery recommendation

## Required Contract Fields

An agent recommendation must include:

- `recommendation_id`
- `run_ref`
- `subject_type`
- `subject_ref`
- `agent_role`
- `context_bundle_trace_ref`
- `agent_action_trace_ref`
- optional `model_call_trace_ref`
- optional `tool_call_trace_refs`
- `recommendation_payload_ref`
- `policy_decision_refs`
- `created_at`

## Intake Rules

- Recommendation intake does not mutate target aggregates directly.
- Accepted recommendations must be converted into owner-service commands.
- Rejected recommendations must retain trace refs and reasons.
- Swapping OpenAI Agent SDK, LangGraph, LangChain, CrewAI, AutoGen, Semantic Kernel, or future framework adapters must not change canonical runtime state.
- Framework-native state is diagnostic-only and cannot be required for replay.

## Negative Rules

Reject recommendation intake when:

- context refs include raw secrets
- untrusted page text is not taint-labeled
- policy denies the tool or prompt context
- recommendation attempts cross-owner mutation
- adapter emits framework-native state as canonical aggregate state
