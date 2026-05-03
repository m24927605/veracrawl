# Data Model: Real-World AI Agent Crawl Planning And Extraction Benchmark

## RealWorldAIAgentBenchmarkManifest

- `id`: Fixture id.
- `scenario`: Success or negative scenario key.
- `profile_refs`: Must include `target`.
- `real_world_corpus_fixture_path`: Path to the row 055 public corpus fixture.
- `provider_names`: Requested model provider adapter names.
- `framework_names`: Requested agent runtime adapter names.
- `required_decision_types`: Required AI decision types; success requires crawl planning, site understanding, extraction candidate generation, and verification/repair.
- `required_public_site_count`: Minimum passing public site observations.
- `expected_completion_result`, `expected_operator_status`, `expected_failure_type`, `negative_case`: Fixture oracle expectations.
- `required_ref_types`: Ref categories required by the benchmark.

## RealWorldAIAgentDecisionTrace

- `id`: Stable decision trace id.
- `benchmark_fixture_id`, `site_observation_ref`, `target_url`: Source and benchmark scope.
- `decision_type`: One of `crawl_planning`, `site_understanding`, `extraction_candidate_generation`, `verification_repair`.
- `model_request_ref`, `model_response_ref`, `model_call_trace_ref`: Model provider invocation refs.
- `agent_run_request_ref`, `agent_run_result_ref`, `agent_action_trace_ref`: Agent runtime invocation refs.
- `tool_call_trace_refs`, `context_bundle_trace_ref`: Controlled tool and sanitized context refs.
- `source_observation_refs`, `artifact_refs`, `content_hash_refs`, `source_anchor_refs`: Source-backed inputs.
- `policy_decision_refs`, `command_record_refs`, `event_cursor_refs`, `outbox_refs`, `replay_bundle_ref`: Control, audit, and replay refs.
- `decision_output_ref`: Framework-neutral output/recommendation ref.
- `framework_native_state_refs`, `llm_output_evidence_refs`: Must be empty for pass.
- `completion_result`, `failure_type`, `missing_ref_fields`, `diagnostics`: Typed result.

## RealWorldAIAgentExtractionCandidate

- `id`: Stable candidate id.
- `site_observation_ref`, `target_url`: Source site scope.
- `candidate_payload_ref`: AI-proposed candidate payload ref, not evidence.
- `field_anchor_refs`: Field to source anchor mapping.
- `source_anchor_refs`, `artifact_refs`, `content_hash_refs`: Mandatory source evidence bindings.
- `model_call_trace_ref`, `agent_action_trace_ref`, `tool_call_trace_refs`, `context_bundle_trace_ref`: AI trace refs for candidate generation.
- `evidence_coverage_ref`, `evidence_packet_ref`, `evidence_anchor_refs`, `verification_decision_refs`, `review_decision_refs`, `publication_gate_ref`: Evidence and publication readiness gates.
- `policy_decision_refs`, `command_record_refs`, `event_cursor_refs`, `outbox_refs`, `replay_bundle_ref`: Control and replay refs.
- `llm_output_evidence_refs`, `direct_publication_refs`: Must be empty for pass.
- `completion_result`, `failure_type`, `missing_ref_fields`, `diagnostics`: Typed result.

## RealWorldAIAgentBenchmarkRunReport

- `id`, `fixture_id`, `run_ref`: Aggregate identity.
- `real_world_benchmark_run_report_ref`: Row 055 aggregate report dependency.
- `site_observation_refs`, `live_http_report_refs`, `source_observation_refs`, `artifact_refs`, `content_hash_refs`, `source_anchor_refs`: Public crawl evidence refs.
- `crawl_planning_decision_refs`, `site_understanding_decision_refs`, `extraction_candidate_decision_refs`, `verification_repair_decision_refs`, `decision_trace_refs`: AI decision coverage.
- `extraction_candidate_refs`, `evidence_coverage_refs`, `evidence_packet_refs`, `evidence_anchor_refs`, `verification_decision_refs`, `review_decision_refs`, `publication_gate_refs`: Candidate and gate refs.
- `model_request_refs`, `model_response_refs`, `model_call_trace_refs`, `agent_run_request_refs`, `agent_run_result_refs`, `agent_action_trace_refs`, `tool_call_trace_refs`, `context_bundle_trace_refs`: Framework-neutral AI execution refs.
- `requested_provider_names`, `verified_provider_names`, `requested_framework_names`, `verified_framework_names`: Adapter coverage.
- `policy_decision_refs`, `command_record_refs`, `event_cursor_refs`, `outbox_refs`, `replay_bundle_refs`: Audit and replay closure.
- `llm_output_evidence_refs`, `direct_publication_refs`, `framework_native_state_refs`, `core_import_violation_refs`: Failure-only diagnostics.
- `completion_result`, `failure_type`, `operator_status`, `missing_ref_fields`, `failure_report_refs`, `diagnostics`: Aggregate result.

## State Transitions

1. `manifest_loaded`
2. `real_world_corpus_completed`
3. `crawl_planning_decision_recorded`
4. `site_understanding_decision_recorded`
5. `extraction_candidate_generated`
6. `verification_repair_decision_recorded`
7. `evidence_publication_gate_evaluated`
8. `real_world_ai_agent_benchmark_reported`
