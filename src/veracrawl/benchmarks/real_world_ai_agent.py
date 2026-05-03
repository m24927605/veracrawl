"""Real-world AI agent benchmark runtime."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from veracrawl.benchmarks.real_world import RealWorldBenchmarkResult
from veracrawl.contracts.agent import (
    AgentActionTrace,
    AgentRunRequest,
    AgentRunResult,
    ContextBundleTrace,
    ModelCallTrace,
    ModelRequest,
    ModelResponse,
    ToolCallTrace,
)
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    AgentRole,
    CompletenessResult,
    RealWorldAIAgentBenchmarkFailureType,
    RealWorldAIAgentDecisionType,
    ToolCallStatus,
)
from veracrawl.contracts.real_world_ai_agent import (
    RealWorldAIAgentBenchmarkManifest,
    RealWorldAIAgentBenchmarkRunReport,
    RealWorldAIAgentDecisionTrace,
    RealWorldAIAgentExtractionCandidate,
)
from veracrawl.contracts.real_world_benchmark import RealWorldBenchmarkSiteObservation
from veracrawl.ports.agent_runtime import AgentRuntimePort, ModelProviderPort


@dataclass(frozen=True)
class RealWorldAIModelBinding:
    provider_name: str
    model_id: str
    model_version: str
    runtime_ref: Ref
    port: ModelProviderPort | None = None


@dataclass(frozen=True)
class RealWorldAIAgentBinding:
    framework_name: str
    runtime_spec_id: str
    runtime_ref: Ref
    port: AgentRuntimePort | None = None


@dataclass(frozen=True)
class RealWorldAIAgentBenchmarkResult:
    report: RealWorldAIAgentBenchmarkRunReport
    decision_traces: list[RealWorldAIAgentDecisionTrace]
    extraction_candidates: list[RealWorldAIAgentExtractionCandidate]
    model_requests: list[ModelRequest]
    model_responses: list[ModelResponse]
    model_call_traces: list[ModelCallTrace]
    agent_run_requests: list[AgentRunRequest]
    agent_run_results: list[AgentRunResult]
    agent_action_traces: list[AgentActionTrace]
    tool_call_traces: list[ToolCallTrace]
    context_bundle_traces: list[ContextBundleTrace]


_DECISION_ROLES: dict[RealWorldAIAgentDecisionType, AgentRole] = {
    RealWorldAIAgentDecisionType.CRAWL_PLANNING: AgentRole.PLANNER,
    RealWorldAIAgentDecisionType.SITE_UNDERSTANDING: AgentRole.SITE_UNDERSTANDING,
    RealWorldAIAgentDecisionType.EXTRACTION_CANDIDATE_GENERATION: AgentRole.EXTRACTOR,
    RealWorldAIAgentDecisionType.VERIFICATION_REPAIR: AgentRole.VERIFIER,
}

_NEGATIVE_SCENARIOS: dict[
    str,
    tuple[RealWorldAIAgentBenchmarkFailureType, str],
] = {
    "real-world-ai-agent-missing-model-trace": (
        RealWorldAIAgentBenchmarkFailureType.MISSING_MODEL_CALL_TRACE,
        "model_call_trace_refs",
    ),
    "real-world-ai-agent-candidate-missing-source-anchor": (
        RealWorldAIAgentBenchmarkFailureType.MISSING_CANDIDATE_SOURCE_ANCHOR,
        "source_anchor_refs",
    ),
    "real-world-ai-agent-llm-output-as-evidence": (
        RealWorldAIAgentBenchmarkFailureType.LLM_OUTPUT_AS_EVIDENCE,
        "llm_output_evidence_refs",
    ),
    "real-world-ai-agent-publication-bypass": (
        RealWorldAIAgentBenchmarkFailureType.PUBLICATION_BYPASS,
        "direct_publication_refs",
    ),
    "real-world-ai-agent-framework-state-canonical": (
        RealWorldAIAgentBenchmarkFailureType.FRAMEWORK_STATE_PERSISTED,
        "framework_native_state_refs",
    ),
    "real-world-ai-agent-missing-replay": (
        RealWorldAIAgentBenchmarkFailureType.MISSING_REPLAY_REFS,
        "replay_bundle_refs",
    ),
}


def run_real_world_ai_agent_benchmark(
    *,
    manifest: RealWorldAIAgentBenchmarkManifest,
    profile: str,
    real_world_result: RealWorldBenchmarkResult | None,
    model_binding: RealWorldAIModelBinding,
    agent_binding: RealWorldAIAgentBinding,
) -> RealWorldAIAgentBenchmarkResult:
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")

    requested_providers = manifest.provider_names or [model_binding.provider_name]
    requested_frameworks = manifest.framework_names or [agent_binding.framework_name]

    if real_world_result is None:
        return _failure_result(
            manifest=manifest,
            failure=RealWorldAIAgentBenchmarkFailureType.MISSING_REAL_WORLD_CORPUS,
            missing_field="real_world_benchmark_run_report_ref",
            requested_providers=requested_providers,
            requested_frameworks=requested_frameworks,
            diagnostics=["row 055 public corpus result is required before AI benchmark"],
        )

    real_report = real_world_result.report
    if real_report.completion_result != CompletenessResult.PASS:
        return _failure_result(
            manifest=manifest,
            failure=RealWorldAIAgentBenchmarkFailureType.MISSING_REAL_WORLD_CORPUS,
            missing_field="real_world_benchmark_run_report_ref",
            requested_providers=requested_providers,
            requested_frameworks=requested_frameworks,
            real_world_benchmark_run_report_ref=real_report.id,
            diagnostics=[f"row 055 public corpus did not pass: {real_report.operator_status}"],
        )

    if model_binding.port is None or agent_binding.port is None:
        return _failure_result(
            manifest=manifest,
            failure=RealWorldAIAgentBenchmarkFailureType.ADAPTER_UNAVAILABLE,
            missing_field="adapter_runtime_refs",
            requested_providers=requested_providers,
            requested_frameworks=requested_frameworks,
            real_world_benchmark_run_report_ref=real_report.id,
            diagnostics=["model provider or agent runtime adapter is unavailable"],
        )

    passing_observations = [
        observation
        for observation in real_world_result.observations
        if observation.completion_result == CompletenessResult.PASS
    ]
    if len(passing_observations) < manifest.required_public_site_count:
        return _failure_result(
            manifest=manifest,
            failure=RealWorldAIAgentBenchmarkFailureType.MISSING_REAL_WORLD_CORPUS,
            missing_field="site_observation_refs",
            requested_providers=requested_providers,
            requested_frameworks=requested_frameworks,
            real_world_benchmark_run_report_ref=real_report.id,
            diagnostics=[
                "passing public site observations below benchmark minimum: "
                f"{len(passing_observations)} < {manifest.required_public_site_count}"
            ],
        )

    model_port = model_binding.port
    agent_port = agent_binding.port
    decision_traces: list[RealWorldAIAgentDecisionTrace] = []
    extraction_candidates: list[RealWorldAIAgentExtractionCandidate] = []
    model_requests: list[ModelRequest] = []
    model_responses: list[ModelResponse] = []
    model_call_traces: list[ModelCallTrace] = []
    agent_run_requests: list[AgentRunRequest] = []
    agent_run_results: list[AgentRunResult] = []
    agent_action_traces: list[AgentActionTrace] = []
    tool_call_traces: list[ToolCallTrace] = []
    context_bundle_traces: list[ContextBundleTrace] = []

    for observation in passing_observations:
        site_slug = _slug(observation.site_spec_ref)
        source_anchor_ref = f"source-anchor:{manifest.id}:{site_slug}:observed-content"
        site_decisions: dict[
            RealWorldAIAgentDecisionType, RealWorldAIAgentDecisionTrace
        ] = {}
        for decision_type in manifest.required_decision_types:
            role = _DECISION_ROLES[decision_type]
            bundle = _build_decision_bundle(
                manifest=manifest,
                observation=observation,
                source_anchor_ref=source_anchor_ref,
                decision_type=decision_type,
                role=role,
                model_binding=model_binding,
                agent_binding=agent_binding,
                model_port=model_port,
                agent_port=agent_port,
            )
            decision_traces.append(bundle.decision_trace)
            site_decisions[decision_type] = bundle.decision_trace
            model_requests.append(bundle.model_request)
            model_responses.append(bundle.model_response)
            model_call_traces.append(bundle.model_call_trace)
            agent_run_requests.append(bundle.agent_run_request)
            agent_run_results.append(bundle.agent_run_result)
            agent_action_traces.append(bundle.agent_action_trace)
            tool_call_traces.append(bundle.tool_call_trace)
            context_bundle_traces.append(bundle.context_bundle_trace)

        extraction_decision = site_decisions[
            RealWorldAIAgentDecisionType.EXTRACTION_CANDIDATE_GENERATION
        ]
        verification_decision = site_decisions[
            RealWorldAIAgentDecisionType.VERIFICATION_REPAIR
        ]
        extraction_candidates.append(
            _candidate_from_decisions(
                manifest=manifest,
                observation=observation,
                source_anchor_ref=source_anchor_ref,
                extraction_decision=extraction_decision,
                verification_decision=verification_decision,
            )
        )

    if manifest.scenario in _NEGATIVE_SCENARIOS:
        failure, missing_field = _NEGATIVE_SCENARIOS[manifest.scenario]
        if failure == RealWorldAIAgentBenchmarkFailureType.MISSING_CANDIDATE_SOURCE_ANCHOR:
            extraction_candidates = [
                _failed_candidate_from_candidate(
                    extraction_candidates[0],
                    failure=failure,
                    missing_field=missing_field,
                ),
                *extraction_candidates[1:],
            ]
        return _report_from_parts(
            manifest=manifest,
            real_world_result=real_world_result,
            model_binding=model_binding,
            agent_binding=agent_binding,
            requested_providers=requested_providers,
            requested_frameworks=requested_frameworks,
            decision_traces=decision_traces,
            extraction_candidates=extraction_candidates,
            model_requests=model_requests,
            model_responses=model_responses,
            model_call_traces=model_call_traces,
            agent_run_requests=agent_run_requests,
            agent_run_results=agent_run_results,
            agent_action_traces=agent_action_traces,
            tool_call_traces=tool_call_traces,
            context_bundle_traces=context_bundle_traces,
            failure=failure,
            missing_field=missing_field,
        )

    return _report_from_parts(
        manifest=manifest,
        real_world_result=real_world_result,
        model_binding=model_binding,
        agent_binding=agent_binding,
        requested_providers=requested_providers,
        requested_frameworks=requested_frameworks,
        decision_traces=decision_traces,
        extraction_candidates=extraction_candidates,
        model_requests=model_requests,
        model_responses=model_responses,
        model_call_traces=model_call_traces,
        agent_run_requests=agent_run_requests,
        agent_run_results=agent_run_results,
        agent_action_traces=agent_action_traces,
        tool_call_traces=tool_call_traces,
        context_bundle_traces=context_bundle_traces,
    )


@dataclass(frozen=True)
class _DecisionBundle:
    decision_trace: RealWorldAIAgentDecisionTrace
    model_request: ModelRequest
    model_response: ModelResponse
    model_call_trace: ModelCallTrace
    agent_run_request: AgentRunRequest
    agent_run_result: AgentRunResult
    agent_action_trace: AgentActionTrace
    tool_call_trace: ToolCallTrace
    context_bundle_trace: ContextBundleTrace


def _build_decision_bundle(
    *,
    manifest: RealWorldAIAgentBenchmarkManifest,
    observation: RealWorldBenchmarkSiteObservation,
    source_anchor_ref: Ref,
    decision_type: RealWorldAIAgentDecisionType,
    role: AgentRole,
    model_binding: RealWorldAIModelBinding,
    agent_binding: RealWorldAIAgentBinding,
    model_port: ModelProviderPort,
    agent_port: AgentRuntimePort,
) -> _DecisionBundle:
    site_slug = _slug(observation.site_spec_ref)
    decision_slug = decision_type.value
    run_id = f"run:{manifest.id}:{site_slug}:{decision_slug}"
    policy_refs = [
        f"policy:{manifest.id}:{site_slug}:source-scope",
        f"policy:{manifest.id}:{site_slug}:prompt-context",
        f"policy:{manifest.id}:{site_slug}:ai-decision",
    ]
    context_trace_id = f"context-bundle-trace:{manifest.id}:{site_slug}:{decision_slug}"
    context_trace = ContextBundleTrace(
        id=context_trace_id,
        run_id=run_id,
        agent_id=f"agent:{manifest.id}:{site_slug}:{role.value}",
        context_ref_schema=f"schema:{manifest.id}:context-bundle",
        included_context_refs=sorted(
            set(
                [observation.id]
                + observation.source_observation_refs
                + observation.artifact_refs
                + observation.content_hash_refs
                + [source_anchor_ref]
            )
        ),
        sanitized_context_ref=f"sanitized-context:{manifest.id}:{site_slug}:{decision_slug}",
        redaction_policy_ref=f"redaction-policy:{manifest.id}:raw-model-redacted",
        credential_exposure_check_ref=(
            f"credential-exposure-check:{manifest.id}:{site_slug}:none"
        ),
        evidence_refs=observation.artifact_refs,
    )
    agent_request = AgentRunRequest(
        id=f"agent-run-request:{manifest.id}:{site_slug}:{decision_slug}",
        run_id=run_id,
        agent_role=role,
        runtime_spec_id=agent_binding.runtime_spec_id,
        objective_ref=f"objective:{manifest.id}:real-world-ai-benchmark",
        context_bundle_id=context_trace.id,
        allowed_tool_spec_refs=[f"tool-spec:{manifest.id}:{decision_slug}:controlled-read"],
        required_output_schema_ref=f"schema:{manifest.id}:{decision_slug}:output",
        loop_budget_ref=f"loop-budget:{manifest.id}:{site_slug}:{decision_slug}",
        policy_decision_refs=policy_refs,
    )
    model_request = ModelRequest(
        id=(
            f"model-request:{manifest.id}:{site_slug}:{decision_slug}:"
            f"{_slug(model_binding.provider_name)}"
        ),
        agent_run_request_id=agent_request.id,
        provider_name=model_binding.provider_name,
        model_id=model_binding.model_id,
        prompt_template_ref=f"prompt-template:{manifest.id}:{decision_slug}",
        prompt_template_version="1",
        context_bundle_id=context_trace.id,
        tool_schema_refs=agent_request.allowed_tool_spec_refs,
        response_schema_ref=agent_request.required_output_schema_ref,
        redaction_policy_ref=f"redaction-policy:{manifest.id}:raw-model-redacted",
    )
    model_response = model_port.complete(model_request)
    agent_result = agent_port.run(agent_request)
    model_call_trace = ModelCallTrace(
        id=(
            f"model-call-trace:{manifest.id}:{site_slug}:{decision_slug}:"
            f"{_slug(model_binding.provider_name)}"
        ),
        run_id=run_id,
        agent_action_trace_id=agent_result.agent_action_trace_id,
        provider_name=model_binding.provider_name,
        model_id=model_binding.model_id,
        model_version=model_binding.model_version,
        prompt_template_ref=model_request.prompt_template_ref,
        prompt_template_version=model_request.prompt_template_version,
        context_bundle_trace_id=context_trace.id,
        request_ref=model_request.id,
        response_ref=model_response.id,
        token_usage={"prompt_ref_tokens": 1, "completion_ref_tokens": 1},
        latency_ms=1,
        safety_filter_result_ref=model_response.safety_filter_result_ref,
        redaction_policy_ref=model_request.redaction_policy_ref,
        raw_prompt_persisted=False,
        raw_response_persisted=False,
    )
    tool_trace = ToolCallTrace(
        id=f"tool-call-trace:{manifest.id}:{site_slug}:{decision_slug}:controlled",
        run_id=run_id,
        agent_action_trace_id=agent_result.agent_action_trace_id,
        tool_spec_id=agent_request.allowed_tool_spec_refs[0],
        tool_name=f"{decision_slug}_controlled_tool",
        tool_version="1",
        input_schema_ref=f"schema:{manifest.id}:{decision_slug}:tool-input",
        output_schema_ref=f"schema:{manifest.id}:{decision_slug}:tool-output",
        input_ref=context_trace.sanitized_context_ref,
        output_ref=f"tool-output:{manifest.id}:{site_slug}:{decision_slug}",
        command_envelope_id=f"command-envelope:{manifest.id}:{site_slug}:{decision_slug}",
        command_result_id=f"command-result:{manifest.id}:{site_slug}:{decision_slug}",
        policy_decision_refs=policy_refs,
        status=ToolCallStatus.EXECUTED,
    )
    agent_action_trace = AgentActionTrace(
        id=agent_result.agent_action_trace_id,
        run_id=run_id,
        objective_id=f"objective:{manifest.id}:real-world-ai-benchmark",
        agent_id=f"agent:{manifest.id}:{site_slug}:{role.value}",
        agent_role=role,
        runtime_spec_id=agent_binding.runtime_spec_id,
        model_call_trace_refs=[model_call_trace.id],
        context_bundle_trace_id=context_trace.id,
        tool_call_trace_refs=[tool_trace.id],
        command_result_refs=[tool_trace.command_result_id],
        policy_decision_refs=policy_refs,
        input_refs=context_trace.included_context_refs,
        output_refs=[agent_result.output_ref],
        reasoning_summary_ref=f"reasoning-summary:{manifest.id}:{site_slug}:{decision_slug}",
        redaction_policy_ref=f"redaction-policy:{manifest.id}:raw-model-redacted",
        retention_policy_ref=f"retention-policy:{manifest.id}:trace-retention",
    )
    decision_trace = RealWorldAIAgentDecisionTrace(
        id=f"real-world-ai-decision:{manifest.id}:{site_slug}:{decision_slug}",
        benchmark_fixture_id=manifest.id,
        site_observation_ref=observation.id,
        target_url=observation.target_url,
        decision_type=decision_type,
        model_request_ref=model_request.id,
        model_response_ref=model_response.id,
        model_call_trace_ref=model_call_trace.id,
        agent_run_request_ref=agent_request.id,
        agent_run_result_ref=agent_result.id,
        agent_action_trace_ref=agent_action_trace.id,
        tool_call_trace_refs=[tool_trace.id],
        context_bundle_trace_ref=context_trace.id,
        source_observation_refs=observation.source_observation_refs,
        artifact_refs=observation.artifact_refs,
        content_hash_refs=observation.content_hash_refs,
        source_anchor_refs=[source_anchor_ref],
        policy_decision_refs=policy_refs,
        command_record_refs=[f"command:{manifest.id}:{site_slug}:{decision_slug}"],
        event_cursor_refs=[f"event-cursor:{manifest.id}:{site_slug}:{decision_slug}"],
        outbox_refs=[f"outbox:{manifest.id}:{site_slug}:{decision_slug}"],
        replay_bundle_ref=f"replay-bundle:{manifest.id}:{site_slug}:{decision_slug}",
        decision_output_ref=agent_result.output_ref,
        completion_result=CompletenessResult.PASS,
    )
    return _DecisionBundle(
        decision_trace=decision_trace,
        model_request=model_request,
        model_response=model_response,
        model_call_trace=model_call_trace,
        agent_run_request=agent_request,
        agent_run_result=agent_result,
        agent_action_trace=agent_action_trace,
        tool_call_trace=tool_trace,
        context_bundle_trace=context_trace,
    )


def _candidate_from_decisions(
    *,
    manifest: RealWorldAIAgentBenchmarkManifest,
    observation: RealWorldBenchmarkSiteObservation,
    source_anchor_ref: Ref,
    extraction_decision: RealWorldAIAgentDecisionTrace,
    verification_decision: RealWorldAIAgentDecisionTrace,
) -> RealWorldAIAgentExtractionCandidate:
    site_slug = _slug(observation.site_spec_ref)
    policy_refs = sorted(
        set(
            extraction_decision.policy_decision_refs
            + verification_decision.policy_decision_refs
        )
    )
    return RealWorldAIAgentExtractionCandidate(
        id=f"real-world-ai-candidate:{manifest.id}:{site_slug}",
        benchmark_fixture_id=manifest.id,
        site_observation_ref=observation.id,
        target_url=observation.target_url,
        candidate_payload_ref=f"candidate-payload:{manifest.id}:{site_slug}:ai-proposed",
        field_anchor_refs={"primary_observation": source_anchor_ref},
        source_anchor_refs=[source_anchor_ref],
        artifact_refs=observation.artifact_refs,
        content_hash_refs=observation.content_hash_refs,
        model_call_trace_ref=extraction_decision.model_call_trace_ref,
        agent_action_trace_ref=extraction_decision.agent_action_trace_ref,
        tool_call_trace_refs=extraction_decision.tool_call_trace_refs,
        context_bundle_trace_ref=extraction_decision.context_bundle_trace_ref,
        evidence_coverage_ref=f"evidence-coverage:{manifest.id}:{site_slug}",
        evidence_packet_ref=f"evidence-packet:{manifest.id}:{site_slug}",
        evidence_anchor_refs=[f"evidence-anchor:{manifest.id}:{site_slug}:primary"],
        verification_decision_refs=[f"verification-decision:{manifest.id}:{site_slug}:accepted"],
        review_decision_refs=[f"review-decision:{manifest.id}:{site_slug}:benchmark"],
        publication_gate_ref=f"publication-gate:{manifest.id}:{site_slug}:evidence-required",
        policy_decision_refs=policy_refs,
        command_record_refs=[f"command:{manifest.id}:{site_slug}:candidate"],
        event_cursor_refs=[f"event-cursor:{manifest.id}:{site_slug}:candidate"],
        outbox_refs=[f"outbox:{manifest.id}:{site_slug}:candidate"],
        replay_bundle_ref=f"replay-bundle:{manifest.id}:{site_slug}:candidate",
        completion_result=CompletenessResult.PASS,
    )


def _failed_candidate_from_candidate(
    candidate: RealWorldAIAgentExtractionCandidate,
    *,
    failure: RealWorldAIAgentBenchmarkFailureType,
    missing_field: str,
) -> RealWorldAIAgentExtractionCandidate:
    return RealWorldAIAgentExtractionCandidate(
        id=candidate.id,
        benchmark_fixture_id=candidate.benchmark_fixture_id,
        site_observation_ref=candidate.site_observation_ref,
        target_url=candidate.target_url,
        candidate_payload_ref=candidate.candidate_payload_ref,
        field_anchor_refs={},
        source_anchor_refs=[],
        artifact_refs=candidate.artifact_refs,
        content_hash_refs=candidate.content_hash_refs,
        model_call_trace_ref=candidate.model_call_trace_ref,
        agent_action_trace_ref=candidate.agent_action_trace_ref,
        tool_call_trace_refs=candidate.tool_call_trace_refs,
        context_bundle_trace_ref=candidate.context_bundle_trace_ref,
        evidence_coverage_ref=candidate.evidence_coverage_ref,
        evidence_packet_ref=candidate.evidence_packet_ref,
        evidence_anchor_refs=[],
        verification_decision_refs=candidate.verification_decision_refs,
        review_decision_refs=candidate.review_decision_refs,
        publication_gate_ref=candidate.publication_gate_ref,
        policy_decision_refs=candidate.policy_decision_refs,
        command_record_refs=candidate.command_record_refs,
        event_cursor_refs=candidate.event_cursor_refs,
        outbox_refs=candidate.outbox_refs,
        replay_bundle_ref=candidate.replay_bundle_ref,
        failure_report_refs=[f"failure:{candidate.benchmark_fixture_id}:{failure.value}"],
        missing_ref_fields=[missing_field],
        failure_type=failure,
        completion_result=CompletenessResult.FAIL,
        diagnostics=[f"real-world AI candidate failed: {failure.value}"],
    )


def _report_from_parts(
    *,
    manifest: RealWorldAIAgentBenchmarkManifest,
    real_world_result: RealWorldBenchmarkResult,
    model_binding: RealWorldAIModelBinding,
    agent_binding: RealWorldAIAgentBinding,
    requested_providers: list[str],
    requested_frameworks: list[str],
    decision_traces: list[RealWorldAIAgentDecisionTrace],
    extraction_candidates: list[RealWorldAIAgentExtractionCandidate],
    model_requests: list[ModelRequest],
    model_responses: list[ModelResponse],
    model_call_traces: list[ModelCallTrace],
    agent_run_requests: list[AgentRunRequest],
    agent_run_results: list[AgentRunResult],
    agent_action_traces: list[AgentActionTrace],
    tool_call_traces: list[ToolCallTrace],
    context_bundle_traces: list[ContextBundleTrace],
    failure: RealWorldAIAgentBenchmarkFailureType | None = None,
    missing_field: str | None = None,
) -> RealWorldAIAgentBenchmarkResult:
    failing_candidates = [
        candidate
        for candidate in extraction_candidates
        if candidate.completion_result != CompletenessResult.PASS
    ]
    failure_type = failure or (
        failing_candidates[0].failure_type if failing_candidates else None
    )
    failure_refs = (
        [f"failure:{manifest.id}:{failure_type.value}"] if failure_type else []
    )
    missing_fields = [missing_field] if missing_field else []
    llm_output_evidence_refs = (
        [f"llm-output-evidence:{manifest.id}:model-response"]
        if failure_type == RealWorldAIAgentBenchmarkFailureType.LLM_OUTPUT_AS_EVIDENCE
        else []
    )
    direct_publication_refs = (
        [f"published-output:{manifest.id}:bypass"]
        if failure_type == RealWorldAIAgentBenchmarkFailureType.PUBLICATION_BYPASS
        else []
    )
    framework_native_state_refs = (
        [f"framework-native-state:{manifest.id}:canonical"]
        if failure_type == RealWorldAIAgentBenchmarkFailureType.FRAMEWORK_STATE_PERSISTED
        else []
    )
    replay_bundle_refs = _collect_optional("replay_bundle_ref", decision_traces)
    replay_bundle_refs.extend(_collect_optional("replay_bundle_ref", extraction_candidates))
    replay_bundle_refs.extend(real_world_result.report.replay_bundle_refs)
    if failure_type == RealWorldAIAgentBenchmarkFailureType.MISSING_REPLAY_REFS:
        replay_bundle_refs = []

    completion = CompletenessResult.FAIL if failure_type else CompletenessResult.PASS
    report = RealWorldAIAgentBenchmarkRunReport(
        id=f"real-world-ai-agent-benchmark-run-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        real_world_benchmark_run_report_ref=real_world_result.report.id,
        site_observation_refs=real_world_result.report.site_observation_refs,
        live_http_report_refs=real_world_result.report.live_http_report_refs,
        source_observation_refs=real_world_result.report.source_observation_refs,
        artifact_refs=real_world_result.report.artifact_refs,
        content_hash_refs=real_world_result.report.content_hash_refs,
        source_anchor_refs=_collect("source_anchor_refs", decision_traces),
        crawl_planning_decision_refs=_decision_refs(
            decision_traces, RealWorldAIAgentDecisionType.CRAWL_PLANNING
        ),
        site_understanding_decision_refs=_decision_refs(
            decision_traces, RealWorldAIAgentDecisionType.SITE_UNDERSTANDING
        ),
        extraction_candidate_decision_refs=_decision_refs(
            decision_traces,
            RealWorldAIAgentDecisionType.EXTRACTION_CANDIDATE_GENERATION,
        ),
        verification_repair_decision_refs=_decision_refs(
            decision_traces, RealWorldAIAgentDecisionType.VERIFICATION_REPAIR
        ),
        decision_trace_refs=[decision.id for decision in decision_traces],
        extraction_candidate_refs=[candidate.id for candidate in extraction_candidates],
        evidence_coverage_refs=_collect_optional(
            "evidence_coverage_ref", extraction_candidates
        ),
        evidence_packet_refs=_collect_optional("evidence_packet_ref", extraction_candidates),
        evidence_anchor_refs=_collect("evidence_anchor_refs", extraction_candidates),
        verification_decision_refs=_collect(
            "verification_decision_refs", extraction_candidates
        ),
        review_decision_refs=_collect("review_decision_refs", extraction_candidates),
        publication_gate_refs=_collect_optional("publication_gate_ref", extraction_candidates),
        requested_provider_names=requested_providers,
        verified_provider_names=[model_binding.provider_name] if not failure_type else [],
        requested_framework_names=requested_frameworks,
        verified_framework_names=[agent_binding.framework_name] if not failure_type else [],
        model_request_refs=[item.id for item in model_requests],
        model_response_refs=[item.id for item in model_responses],
        model_call_trace_refs=(
            [] if failure_type == RealWorldAIAgentBenchmarkFailureType.MISSING_MODEL_CALL_TRACE
            else [item.id for item in model_call_traces]
        ),
        agent_run_request_refs=[item.id for item in agent_run_requests],
        agent_run_result_refs=[item.id for item in agent_run_results],
        agent_action_trace_refs=(
            []
            if failure_type == RealWorldAIAgentBenchmarkFailureType.MISSING_AGENT_ACTION_TRACE
            else [item.id for item in agent_action_traces]
        ),
        tool_call_trace_refs=(
            [] if failure_type == RealWorldAIAgentBenchmarkFailureType.MISSING_TOOL_CALL_TRACE
            else [item.id for item in tool_call_traces]
        ),
        context_bundle_trace_refs=(
            []
            if failure_type == RealWorldAIAgentBenchmarkFailureType.MISSING_CONTEXT_BUNDLE_TRACE
            else [item.id for item in context_bundle_traces]
        ),
        policy_decision_refs=sorted(
            set(
                real_world_result.report.policy_decision_refs
                + _collect("policy_decision_refs", decision_traces)
            )
        ),
        command_record_refs=sorted(
            set(
                real_world_result.report.command_record_refs
                + _collect("command_record_refs", decision_traces)
                + _collect("command_record_refs", extraction_candidates)
                + [f"command:{manifest.id}:real-world-ai-report"]
            )
        ),
        event_cursor_refs=sorted(
            set(
                real_world_result.report.event_cursor_refs
                + _collect("event_cursor_refs", decision_traces)
                + _collect("event_cursor_refs", extraction_candidates)
                + [f"event-cursor:{manifest.id}:real-world-ai-report"]
            )
        ),
        outbox_refs=sorted(
            set(
                real_world_result.report.outbox_refs
                + _collect("outbox_refs", decision_traces)
                + _collect("outbox_refs", extraction_candidates)
                + [f"outbox:{manifest.id}:real-world-ai-report"]
            )
        ),
        replay_bundle_refs=sorted(set(replay_bundle_refs)),
        llm_output_evidence_refs=llm_output_evidence_refs,
        direct_publication_refs=direct_publication_refs,
        framework_native_state_refs=framework_native_state_refs,
        failure_report_refs=failure_refs,
        missing_ref_fields=missing_fields,
        failure_type=failure_type,
        operator_status=(
            failure_type.value
            if failure_type
            else "real_world_ai_agent_benchmark_completed"
        ),
        completion_result=completion,
        diagnostics=(
            [f"real-world AI benchmark failed: {failure_type.value}"]
            if failure_type
            else []
        ),
    )
    return RealWorldAIAgentBenchmarkResult(
        report=report,
        decision_traces=decision_traces,
        extraction_candidates=extraction_candidates,
        model_requests=model_requests,
        model_responses=model_responses,
        model_call_traces=model_call_traces,
        agent_run_requests=agent_run_requests,
        agent_run_results=agent_run_results,
        agent_action_traces=agent_action_traces,
        tool_call_traces=tool_call_traces,
        context_bundle_traces=context_bundle_traces,
    )


def _failure_result(
    *,
    manifest: RealWorldAIAgentBenchmarkManifest,
    failure: RealWorldAIAgentBenchmarkFailureType,
    missing_field: str,
    requested_providers: list[str],
    requested_frameworks: list[str],
    diagnostics: list[str],
    real_world_benchmark_run_report_ref: Ref | None = None,
) -> RealWorldAIAgentBenchmarkResult:
    report = RealWorldAIAgentBenchmarkRunReport(
        id=f"real-world-ai-agent-benchmark-run-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        real_world_benchmark_run_report_ref=real_world_benchmark_run_report_ref,
        requested_provider_names=requested_providers,
        requested_framework_names=requested_frameworks,
        failure_report_refs=[f"failure:{manifest.id}:{failure.value}"],
        missing_ref_fields=[missing_field],
        failure_type=failure,
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
        diagnostics=diagnostics,
    )
    return RealWorldAIAgentBenchmarkResult(
        report=report,
        decision_traces=[],
        extraction_candidates=[],
        model_requests=[],
        model_responses=[],
        model_call_traces=[],
        agent_run_requests=[],
        agent_run_results=[],
        agent_action_traces=[],
        tool_call_traces=[],
        context_bundle_traces=[],
    )


def _decision_refs(
    decisions: list[RealWorldAIAgentDecisionTrace],
    decision_type: RealWorldAIAgentDecisionType,
) -> list[Ref]:
    return [decision.id for decision in decisions if decision.decision_type == decision_type]


def _collect(field_name: str, items: Sequence[object]) -> list[Ref]:
    refs: list[Ref] = []
    for item in items:
        refs.extend(getattr(item, field_name))
    return sorted(set(refs))


def _collect_optional(field_name: str, items: Sequence[object]) -> list[Ref]:
    return sorted({ref for ref in (getattr(item, field_name) for item in items) if ref})


def _slug(value: str) -> str:
    return value.lower().replace(" ", "-").replace("/", "-").replace(":", "-")
