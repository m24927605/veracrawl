from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult, RealWorldAIAgentDecisionType
from veracrawl.contracts.real_world_ai_agent import (
    RealWorldAIAgentBenchmarkRunReport,
    RealWorldAIAgentDecisionTrace,
    RealWorldAIAgentExtractionCandidate,
)
from veracrawl.review_replay.real_world_ai_agent import (
    real_world_ai_agent_candidate_replay_passes,
    real_world_ai_agent_decision_replay_passes,
    real_world_ai_agent_report_replay_passes,
)


def _decision() -> RealWorldAIAgentDecisionTrace:
    return RealWorldAIAgentDecisionTrace(
        id="decision:1",
        benchmark_fixture_id="fixture",
        site_observation_ref="site:1",
        target_url="https://example.com/",
        decision_type=RealWorldAIAgentDecisionType.CRAWL_PLANNING,
        model_request_ref="model-request:1",
        model_response_ref="model-response:1",
        model_call_trace_ref="model-call-trace:1",
        agent_run_request_ref="agent-run-request:1",
        agent_run_result_ref="agent-run-result:1",
        agent_action_trace_ref="agent-action-trace:1",
        tool_call_trace_refs=["tool-call-trace:1"],
        context_bundle_trace_ref="context-bundle-trace:1",
        source_observation_refs=["source-observation:1"],
        artifact_refs=["artifact:1"],
        content_hash_refs=["content-hash:1"],
        source_anchor_refs=["source-anchor:1"],
        policy_decision_refs=["policy:1"],
        command_record_refs=["command:1"],
        event_cursor_refs=["event-cursor:1"],
        outbox_refs=["outbox:1"],
        replay_bundle_ref="replay-bundle:1",
        decision_output_ref="agent-output:1",
        completion_result=CompletenessResult.PASS,
    )


def _candidate() -> RealWorldAIAgentExtractionCandidate:
    return RealWorldAIAgentExtractionCandidate(
        id="candidate:1",
        benchmark_fixture_id="fixture",
        site_observation_ref="site:1",
        target_url="https://example.com/",
        candidate_payload_ref="candidate-payload:1",
        field_anchor_refs={"title": "source-anchor:1"},
        source_anchor_refs=["source-anchor:1"],
        artifact_refs=["artifact:1"],
        content_hash_refs=["content-hash:1"],
        model_call_trace_ref="model-call-trace:1",
        agent_action_trace_ref="agent-action-trace:1",
        tool_call_trace_refs=["tool-call-trace:1"],
        context_bundle_trace_ref="context-bundle-trace:1",
        evidence_coverage_ref="evidence-coverage:1",
        evidence_packet_ref="evidence-packet:1",
        evidence_anchor_refs=["evidence-anchor:1"],
        verification_decision_refs=["verification:1"],
        review_decision_refs=["review:1"],
        publication_gate_ref="publication-gate:1",
        policy_decision_refs=["policy:1"],
        command_record_refs=["command:1"],
        event_cursor_refs=["event-cursor:1"],
        outbox_refs=["outbox:1"],
        replay_bundle_ref="replay-bundle:1",
        completion_result=CompletenessResult.PASS,
    )


def _report() -> RealWorldAIAgentBenchmarkRunReport:
    return RealWorldAIAgentBenchmarkRunReport(
        id="report:1",
        fixture_id="fixture",
        run_ref="run:fixture",
        real_world_benchmark_run_report_ref="real-world-report:1",
        site_observation_refs=["site:1"],
        live_http_report_refs=["live-http:1"],
        source_observation_refs=["source-observation:1"],
        artifact_refs=["artifact:1"],
        content_hash_refs=["content-hash:1"],
        source_anchor_refs=["source-anchor:1"],
        crawl_planning_decision_refs=["decision:planning"],
        site_understanding_decision_refs=["decision:site"],
        extraction_candidate_decision_refs=["decision:extract"],
        verification_repair_decision_refs=["decision:verify"],
        decision_trace_refs=["decision:1"],
        extraction_candidate_refs=["candidate:1"],
        evidence_coverage_refs=["evidence-coverage:1"],
        evidence_packet_refs=["evidence-packet:1"],
        evidence_anchor_refs=["evidence-anchor:1"],
        verification_decision_refs=["verification:1"],
        review_decision_refs=["review:1"],
        publication_gate_refs=["publication-gate:1"],
        requested_provider_names=["Local model runtime"],
        verified_provider_names=["Local model runtime"],
        requested_framework_names=["VeraCrawl Native Runtime"],
        verified_framework_names=["VeraCrawl Native Runtime"],
        model_request_refs=["model-request:1"],
        model_response_refs=["model-response:1"],
        model_call_trace_refs=["model-call-trace:1"],
        agent_run_request_refs=["agent-run-request:1"],
        agent_run_result_refs=["agent-run-result:1"],
        agent_action_trace_refs=["agent-action-trace:1"],
        tool_call_trace_refs=["tool-call-trace:1"],
        context_bundle_trace_refs=["context-bundle-trace:1"],
        policy_decision_refs=["policy:1"],
        command_record_refs=["command:1"],
        event_cursor_refs=["event-cursor:1"],
        outbox_refs=["outbox:1"],
        replay_bundle_refs=["replay-bundle:1"],
        operator_status="real_world_ai_agent_benchmark_completed",
        completion_result=CompletenessResult.PASS,
    )


def test_replay_helpers_require_ai_replay_refs() -> None:
    assert real_world_ai_agent_decision_replay_passes(_decision())
    assert real_world_ai_agent_candidate_replay_passes(_candidate())
    assert real_world_ai_agent_report_replay_passes(_report())
    assert not real_world_ai_agent_decision_replay_passes(
        _decision().model_copy(update={"replay_bundle_ref": None})
    )
    assert not real_world_ai_agent_candidate_replay_passes(
        _candidate().model_copy(update={"replay_bundle_ref": None})
    )
