from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.agent_adapter import (
    REQUIRED_AGENT_FRAMEWORKS,
    AgentAdapterExecutionRecord,
    AgentRuntimeAdapterFixtureManifest,
    AgentRuntimeAdapterReport,
)
from veracrawl.contracts.enums import AgentAdapterFailureType, CompletenessResult


def _execution_record() -> AgentAdapterExecutionRecord:
    return AgentAdapterExecutionRecord(
        id="agent-adapter-execution:ok",
        framework_name="OpenAI Agent SDK",
        runtime_spec_ref="runtime:openai",
        agent_run_request_ref="agent-run-request:ok",
        agent_run_result_ref="agent-run-result:ok",
        agent_action_trace_ref="agent-action-trace:ok",
        model_call_trace_refs=["model-call-trace:ok"],
        tool_call_trace_refs=["tool-call-trace:ok"],
        context_bundle_trace_ref="context-bundle-trace:ok",
        command_result_refs=["command-result:ok"],
        policy_decision_refs=["policy:ok:agent-adapter"],
        observability_report_refs=["observability-report:ok"],
        security_privacy_report_refs=["security-privacy-report:ok"],
        replay_bundle_ref="replay-bundle:ok",
        contract_adapter_refs=["contract-adapter:ok"],
        result=CompletenessResult.PASS,
    )


def test_adapter_execution_pass_requires_model_tool_security_and_replay_refs() -> None:
    with pytest.raises(ValidationError):
        AgentAdapterExecutionRecord(
            id="agent-adapter-execution:bad",
            framework_name="OpenAI Agent SDK",
            runtime_spec_ref="runtime:openai",
            agent_run_request_ref="agent-run-request:bad",
            agent_run_result_ref="agent-run-result:bad",
            agent_action_trace_ref="agent-action-trace:bad",
            context_bundle_trace_ref="context-bundle-trace:bad",
            command_result_refs=["command-result:bad"],
            policy_decision_refs=["policy:bad:agent-adapter"],
            observability_report_refs=["observability-report:bad"],
            security_privacy_report_refs=["security-privacy-report:bad"],
            replay_bundle_ref="replay-bundle:bad",
            contract_adapter_refs=["contract-adapter:bad"],
            result=CompletenessResult.PASS,
        )


def test_adapter_execution_rejects_raw_prompt_and_framework_canonical_state() -> None:
    payload = _execution_record().model_dump()
    with pytest.raises(ValidationError):
        AgentAdapterExecutionRecord(**(payload | {"raw_prompt_persisted": True}))
    with pytest.raises(ValidationError):
        AgentAdapterExecutionRecord(**(payload | {"framework_state_canonical": True}))


def test_adapter_report_pass_requires_all_required_frameworks() -> None:
    with pytest.raises(ValidationError):
        AgentRuntimeAdapterReport(
            id="agent-runtime-adapter-report:bad",
            run_ref="run:bad",
            framework_execution_refs=["agent-adapter-execution:openai"],
            required_framework_names=list(REQUIRED_AGENT_FRAMEWORKS),
            verified_framework_names=["OpenAI Agent SDK"],
            model_provider_refs=["model-provider:bad"],
            policy_decision_refs=["policy:bad:agent-adapter"],
            observability_report_refs=["observability-report:bad"],
            security_privacy_report_refs=["security-privacy-report:bad"],
            command_record_refs=["command:bad"],
            event_cursor_refs=["event-cursor:bad"],
            outbox_refs=["outbox:bad"],
            replay_bundle_ref="replay-bundle:bad",
            operator_status="agent_runtime_adapter_mapping_completed",
            completion_result=CompletenessResult.PASS,
        )


def test_adapter_report_accepts_complete_pass() -> None:
    report = AgentRuntimeAdapterReport(
        id="agent-runtime-adapter-report:ok",
        run_ref="run:ok",
        framework_execution_refs=[
            f"agent-adapter-execution:{framework}" for framework in REQUIRED_AGENT_FRAMEWORKS
        ],
        required_framework_names=list(REQUIRED_AGENT_FRAMEWORKS),
        verified_framework_names=list(REQUIRED_AGENT_FRAMEWORKS),
        model_provider_refs=["model-provider:ok"],
        policy_decision_refs=["policy:ok:agent-adapter"],
        observability_report_refs=["observability-report:ok"],
        security_privacy_report_refs=["security-privacy-report:ok"],
        command_record_refs=["command:ok"],
        event_cursor_refs=["event-cursor:ok"],
        outbox_refs=["outbox:ok"],
        replay_bundle_ref="replay-bundle:ok",
        operator_status="agent_runtime_adapter_mapping_completed",
        completion_result=CompletenessResult.PASS,
    )
    assert report.verified_framework_names == list(REQUIRED_AGENT_FRAMEWORKS)


def test_adapter_fixture_manifest_rejects_negative_pass() -> None:
    with pytest.raises(ValidationError):
        AgentRuntimeAdapterFixtureManifest(
            id="agent-runtime-adapter-bad",
            scenario="agent-runtime-adapter-bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="bad",
            expected_failure_type=AgentAdapterFailureType.RAW_PROMPT_LEAK,
            negative_case=True,
        )
