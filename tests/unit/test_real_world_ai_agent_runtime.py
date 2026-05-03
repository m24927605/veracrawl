from __future__ import annotations

from veracrawl.adapters.agent_frameworks.native_runtime import build_agent_runtime
from veracrawl.adapters.model_providers.local_runtime import build_model_provider
from veracrawl.benchmarks.real_world import RealWorldBenchmarkResult
from veracrawl.benchmarks.real_world_ai_agent import (
    RealWorldAIAgentBinding,
    RealWorldAIModelBinding,
    run_real_world_ai_agent_benchmark,
)
from veracrawl.contracts.enums import (
    CompletenessResult,
    RealWorldAIAgentBenchmarkFailureType,
    RealWorldAIAgentDecisionType,
)
from veracrawl.contracts.real_world_ai_agent import RealWorldAIAgentBenchmarkManifest
from veracrawl.contracts.real_world_benchmark import (
    RealWorldBenchmarkRunReport,
    RealWorldBenchmarkSiteObservation,
)


def _manifest(
    *,
    scenario: str = "real-world-ai-agent-public-corpus",
    expected: CompletenessResult = CompletenessResult.PASS,
    failure: RealWorldAIAgentBenchmarkFailureType | None = None,
) -> RealWorldAIAgentBenchmarkManifest:
    return RealWorldAIAgentBenchmarkManifest(
        id=scenario,
        scenario=scenario,
        profile_refs=["target"],
        real_world_corpus_fixture_path="tests/fixtures/real-world-public-corpus",
        provider_names=["Local model runtime"],
        framework_names=["VeraCrawl Native Runtime"],
        required_decision_types=list(RealWorldAIAgentDecisionType),
        required_public_site_count=4,
        expected_completion_result=expected,
        expected_operator_status=(
            failure.value if failure else "real_world_ai_agent_benchmark_completed"
        ),
        expected_failure_type=failure,
        negative_case=failure is not None,
        required_ref_types=["trace", "candidate", "replay"],
    )


def _real_world_result(site_count: int = 4) -> RealWorldBenchmarkResult:
    observations = [_observation(index) for index in range(site_count)]
    report = RealWorldBenchmarkRunReport(
        id="real-world-benchmark-run-report:fixture",
        fixture_id="real-world-public-corpus",
        run_ref="run:real-world-public-corpus",
        benchmark_corpus_ref="real-world-benchmark-corpus:fixture",
        benchmark_run_refs=[f"benchmark-run:site-{index}" for index in range(site_count)],
        site_observation_refs=[item.id for item in observations],
        live_http_report_refs=[item.live_http_report_ref or "" for item in observations],
        network_response_refs=[item.network_response_ref or "" for item in observations],
        source_observation_refs=[
            ref for item in observations for ref in item.source_observation_refs
        ],
        artifact_refs=[ref for item in observations for ref in item.artifact_refs],
        content_hash_refs=[ref for item in observations for ref in item.content_hash_refs],
        canonical_url_refs=[ref for item in observations for ref in item.canonical_url_refs],
        policy_decision_refs=[ref for item in observations for ref in item.policy_decision_refs],
        command_record_refs=[ref for item in observations for ref in item.command_record_refs],
        event_cursor_refs=[ref for item in observations for ref in item.event_cursor_refs],
        outbox_refs=[ref for item in observations for ref in item.outbox_refs],
        replay_bundle_refs=[item.replay_bundle_ref or "" for item in observations],
        observation_summary_refs=[
            f"observation-summary:site-{index}" for index in range(site_count)
        ],
        operator_status="real_world_benchmark_completed",
        completion_result=CompletenessResult.PASS,
    )
    return RealWorldBenchmarkResult(
        report=report,
        observations=observations,
        live_http_results=[],
    )


def _observation(index: int) -> RealWorldBenchmarkSiteObservation:
    return RealWorldBenchmarkSiteObservation(
        id=f"real-world-site-observation:site-{index}",
        site_spec_ref=f"site-{index}",
        target_url=f"https://example.com/{index}",
        robots_policy_ref=f"policy:site-{index}:robots",
        live_http_report_ref=f"live-http-report:site-{index}",
        network_response_ref=f"network-response:site-{index}",
        source_observation_refs=[f"source-observation:site-{index}"],
        artifact_refs=[f"artifact:site-{index}"],
        content_hash_refs=[f"content-hash:site-{index}"],
        canonical_url_refs=[f"canonical-url:site-{index}"],
        policy_decision_refs=[f"policy:site-{index}"],
        command_record_refs=[f"command:site-{index}"],
        event_cursor_refs=[f"event-cursor:site-{index}"],
        outbox_refs=[f"outbox:site-{index}"],
        replay_bundle_ref=f"replay-bundle:site-{index}",
        status_code=200,
        content_type="text/html",
        body_size_bytes=128,
        content_digest=f"digest-{index}",
        matched_observation_refs=[f"observation:site-{index}:title"],
        completion_result=CompletenessResult.PASS,
    )


def _model_binding() -> RealWorldAIModelBinding:
    provider = build_model_provider()
    return RealWorldAIModelBinding(
        provider_name=provider.provider_name,
        model_id=provider.model_id,
        model_version=provider.model_version,
        runtime_ref="model-runtime:local",
        port=provider,
    )


def _agent_binding() -> RealWorldAIAgentBinding:
    runtime = build_agent_runtime()
    return RealWorldAIAgentBinding(
        framework_name=runtime.framework_name,
        runtime_spec_id="agent-runtime-spec:native",
        runtime_ref="agent-runtime:native",
        port=runtime,
    )


def test_real_world_ai_agent_runtime_generates_traces_and_candidates() -> None:
    result = run_real_world_ai_agent_benchmark(
        manifest=_manifest(),
        profile="target",
        real_world_result=_real_world_result(),
        model_binding=_model_binding(),
        agent_binding=_agent_binding(),
    )

    assert result.report.completion_result == CompletenessResult.PASS
    assert len(result.decision_traces) == 16
    assert len(result.model_call_traces) == 16
    assert len(result.agent_action_traces) == 16
    assert len(result.tool_call_traces) == 16
    assert len(result.context_bundle_traces) == 16
    assert len(result.extraction_candidates) == 4
    assert not result.report.llm_output_evidence_refs
    assert not result.report.direct_publication_refs


def test_real_world_ai_agent_runtime_fails_without_public_corpus() -> None:
    result = run_real_world_ai_agent_benchmark(
        manifest=_manifest(),
        profile="target",
        real_world_result=None,
        model_binding=_model_binding(),
        agent_binding=_agent_binding(),
    )

    assert result.report.failure_type == (
        RealWorldAIAgentBenchmarkFailureType.MISSING_REAL_WORLD_CORPUS
    )


def test_real_world_ai_agent_negative_scenarios_are_typed() -> None:
    cases = {
        "real-world-ai-agent-missing-model-trace": (
            RealWorldAIAgentBenchmarkFailureType.MISSING_MODEL_CALL_TRACE
        ),
        "real-world-ai-agent-candidate-missing-source-anchor": (
            RealWorldAIAgentBenchmarkFailureType.MISSING_CANDIDATE_SOURCE_ANCHOR
        ),
        "real-world-ai-agent-llm-output-as-evidence": (
            RealWorldAIAgentBenchmarkFailureType.LLM_OUTPUT_AS_EVIDENCE
        ),
        "real-world-ai-agent-publication-bypass": (
            RealWorldAIAgentBenchmarkFailureType.PUBLICATION_BYPASS
        ),
        "real-world-ai-agent-framework-state-canonical": (
            RealWorldAIAgentBenchmarkFailureType.FRAMEWORK_STATE_PERSISTED
        ),
        "real-world-ai-agent-missing-replay": (
            RealWorldAIAgentBenchmarkFailureType.MISSING_REPLAY_REFS
        ),
    }
    for scenario, failure in cases.items():
        result = run_real_world_ai_agent_benchmark(
            manifest=_manifest(
                scenario=scenario,
                expected=CompletenessResult.FAIL,
                failure=failure,
            ),
            profile="target",
            real_world_result=_real_world_result(),
            model_binding=_model_binding(),
            agent_binding=_agent_binding(),
        )

        assert result.report.completion_result == CompletenessResult.FAIL
        assert result.report.failure_type == failure
