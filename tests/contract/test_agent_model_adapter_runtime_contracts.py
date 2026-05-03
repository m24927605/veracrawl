from __future__ import annotations

import pytest

from veracrawl.contracts.agent_model_runtime import (
    AgentModelAdapterFixtureManifest,
    AgentModelAdapterRuntimeReport,
)
from veracrawl.contracts.enums import AgentModelAdapterRuntimeFailureType, CompletenessResult


def _pass_report() -> AgentModelAdapterRuntimeReport:
    return AgentModelAdapterRuntimeReport(
        id="agent-model-adapter-runtime-report:fixture",
        fixture_id="fixture",
        run_ref="run:fixture",
        run_control_report_ref="production-run-control-report:fixture",
        live_normalization_runtime_report_ref="live-normalization-runtime-report:fixture",
        schema_extraction_runtime_report_ref="schema-extraction-runtime-report:fixture",
        planning_agent_run_refs=["agent-run-result:fixture:planner"],
        extraction_agent_run_refs=["agent-run-result:fixture:extractor"],
        repair_agent_run_refs=["agent-run-result:fixture:drift"],
        provider_execution_refs=["model-provider-execution:fixture:planner:local"],
        framework_execution_refs=["agent-adapter-execution:fixture:planner:native"],
        requested_provider_names=["Local model runtime"],
        verified_provider_names=["Local model runtime"],
        requested_framework_names=["VeraCrawl Native Runtime"],
        verified_framework_names=["VeraCrawl Native Runtime"],
        model_request_refs=["model-request:fixture:planner"],
        model_response_refs=["model-response:fixture:planner"],
        model_call_trace_refs=["model-call-trace:fixture:planner"],
        agent_run_request_refs=["agent-run-request:fixture:planner"],
        agent_run_result_refs=["agent-run-result:fixture:planner"],
        agent_action_trace_refs=["agent-action-trace:fixture:planner"],
        tool_call_trace_refs=["tool-call-trace:fixture:planner:controlled-tool"],
        context_bundle_trace_refs=["context-bundle-trace:fixture:planner"],
        adapter_runtime_refs=["model-runtime:fixture:local", "agent-runtime:fixture:native"],
        policy_decision_refs=["policy:fixture:agent-model-adapter"],
        observability_report_refs=["observability-report:fixture:agent-model"],
        security_privacy_report_refs=["security-privacy-report:fixture:agent-model"],
        command_record_refs=["command:fixture:agent-model-adapter"],
        event_cursor_refs=["event-cursor:fixture:agent-model-adapter"],
        outbox_refs=["outbox:fixture:agent-model-adapter"],
        replay_bundle_ref="replay-bundle:fixture:agent-model",
        operator_status="agent_model_adapter_runtime_completed",
        completion_result=CompletenessResult.PASS,
    )


def test_agent_model_adapter_runtime_report_pass_requires_core_refs() -> None:
    report = _pass_report()
    assert report.completion_result == CompletenessResult.PASS
    assert report.verified_provider_names == ["Local model runtime"]


def test_agent_model_adapter_runtime_report_rejects_passing_adapter_gap() -> None:
    payload = _pass_report().model_dump()
    payload["verified_provider_names"] = []
    with pytest.raises(ValueError, match="unresolved refs"):
        AgentModelAdapterRuntimeReport(**payload)


def test_agent_model_adapter_runtime_report_rejects_raw_prompt_on_pass() -> None:
    payload = _pass_report().model_dump()
    payload["raw_prompt_leak_refs"] = ["raw-prompt-leak:fixture"]
    with pytest.raises(ValueError, match="unresolved refs"):
        AgentModelAdapterRuntimeReport(**payload)


def test_agent_model_adapter_runtime_report_needs_review_requires_availability_refs() -> None:
    with pytest.raises(ValueError, match="availability refs"):
        AgentModelAdapterRuntimeReport(
            id="agent-model-adapter-runtime-report:fixture",
            fixture_id="fixture",
            run_ref="run:fixture",
            operator_status=AgentModelAdapterRuntimeFailureType.ADAPTER_RUNTIME_UNAVAILABLE.value,
            completion_result=CompletenessResult.NEEDS_REVIEW,
        )


def test_agent_model_adapter_runtime_failed_report_requires_failure_type() -> None:
    with pytest.raises(ValueError, match="failure_type"):
        AgentModelAdapterRuntimeReport(
            id="agent-model-adapter-runtime-report:fixture",
            fixture_id="fixture",
            run_ref="run:fixture",
            failure_report_refs=["failure:fixture"],
            operator_status="failed",
            completion_result=CompletenessResult.FAIL,
        )


def test_agent_model_adapter_fixture_manifest_validation() -> None:
    manifest = AgentModelAdapterFixtureManifest(
        id="agent-model-adapter-runtime-unavailable",
        scenario="agent-model-adapter-runtime-unavailable",
        profile_refs=["target"],
        expected_completion_result=CompletenessResult.NEEDS_REVIEW,
        expected_operator_status=(
            AgentModelAdapterRuntimeFailureType.ADAPTER_RUNTIME_UNAVAILABLE.value
        ),
        expected_failure_type=AgentModelAdapterRuntimeFailureType.ADAPTER_RUNTIME_UNAVAILABLE,
        negative_case=True,
    )
    assert manifest.negative_case

    with pytest.raises(ValueError, match="cannot expect pass"):
        AgentModelAdapterFixtureManifest(
            id="bad",
            scenario="bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="bad",
            negative_case=True,
        )
