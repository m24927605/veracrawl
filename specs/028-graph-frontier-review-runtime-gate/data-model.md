# Data Model: VeraCrawl Graph-Driven Frontier And Review Runtime Gate

## GraphFrontierDecisionRecord

- `id`
- `run_ref`
- `graph_signal_ref`
- `signal_type`
- `decision_type`: prioritize, retry, retire, expand
- `frontier_item_ref`
- `before_priority`
- `after_priority`
- `generated_frontier_item_refs`
- `retry_frontier_item_refs`
- `retired_frontier_item_refs`
- `source_graph_refs`
- `explanation_ref`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `replay_bundle_ref`
- `result`

## GraphReviewRouteDecisionRecord

- `id`
- `run_ref`
- `graph_signal_ref`
- `signal_type`
- `route_type`
- `review_item_ref`
- `review_priority`
- `source_graph_refs`
- `explanation_ref`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `replay_bundle_ref`
- `result`

## GraphFrontierReviewRuntimeReport

- `id`
- `run_ref`
- aggregate graph signal, source graph, frontier, review, explanation, policy, command, event, outbox, and replay refs
- review/runtime failure refs
- `operator_status`
- `completion_result`

## GraphFrontierReviewFixtureManifest

- `id`
- `scenario`
- `profile_refs`
- `expected_completion_result`
- `expected_operator_status`
- `expected_failure_type`
- `negative_case`
