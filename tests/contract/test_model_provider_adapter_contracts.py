from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import CompletenessResult, ModelProviderAdapterFailureType
from veracrawl.contracts.model_provider_adapter import (
    REQUIRED_MODEL_PROVIDERS,
    ModelProviderAdapterExecutionRecord,
    ModelProviderAdapterFixtureManifest,
    ModelProviderAdapterReport,
)


def _execution_record() -> ModelProviderAdapterExecutionRecord:
    return ModelProviderAdapterExecutionRecord(
        id="model-provider-execution:ok",
        provider_name="OpenAI",
        runtime_spec_ref="runtime:openai",
        model_request_ref="model-request:ok",
        model_response_ref="model-response:ok",
        model_call_trace_ref="model-call-trace:ok",
        context_bundle_trace_ref="context-bundle-trace:ok",
        agent_run_request_ref="agent-run-request:ok",
        agent_run_result_ref="agent-run-result:ok",
        agent_action_trace_ref="agent-action-trace:ok",
        command_result_refs=["command-result:ok"],
        policy_decision_refs=["policy:ok:model-provider"],
        observability_report_refs=["observability-report:ok"],
        security_privacy_report_refs=["security-privacy-report:ok"],
        replay_bundle_ref="replay-bundle:ok",
        contract_adapter_refs=["contract-adapter:ok"],
        result=CompletenessResult.PASS,
    )


def test_provider_execution_pass_requires_context_security_and_replay_refs() -> None:
    with pytest.raises(ValidationError):
        ModelProviderAdapterExecutionRecord(
            id="model-provider-execution:bad",
            provider_name="OpenAI",
            runtime_spec_ref="runtime:openai",
            model_request_ref="model-request:bad",
            model_response_ref="model-response:bad",
            model_call_trace_ref="model-call-trace:bad",
            agent_run_request_ref="agent-run-request:bad",
            agent_run_result_ref="agent-run-result:bad",
            agent_action_trace_ref="agent-action-trace:bad",
            command_result_refs=["command-result:bad"],
            policy_decision_refs=["policy:bad:model-provider"],
            observability_report_refs=["observability-report:bad"],
            security_privacy_report_refs=["security-privacy-report:bad"],
            replay_bundle_ref="replay-bundle:bad",
            contract_adapter_refs=["contract-adapter:bad"],
            result=CompletenessResult.PASS,
        )


def test_provider_execution_rejects_raw_and_provider_canonical_state() -> None:
    payload = _execution_record().model_dump()
    with pytest.raises(ValidationError):
        ModelProviderAdapterExecutionRecord(**(payload | {"raw_prompt_persisted": True}))
    with pytest.raises(ValidationError):
        ModelProviderAdapterExecutionRecord(**(payload | {"raw_response_persisted": True}))
    with pytest.raises(ValidationError):
        ModelProviderAdapterExecutionRecord(
            **(payload | {"provider_transcript_canonical": True})
        )


def test_provider_report_pass_requires_all_required_providers() -> None:
    with pytest.raises(ValidationError):
        ModelProviderAdapterReport(
            id="model-provider-adapter-report:bad",
            run_ref="run:bad",
            provider_execution_refs=["model-provider-execution:openai"],
            required_provider_names=list(REQUIRED_MODEL_PROVIDERS),
            verified_provider_names=["OpenAI"],
            model_request_refs=["model-request:bad"],
            model_response_refs=["model-response:bad"],
            model_call_trace_refs=["model-call-trace:bad"],
            context_bundle_trace_refs=["context-bundle-trace:bad"],
            agent_run_refs=["agent-run-request:bad", "agent-run-result:bad"],
            policy_decision_refs=["policy:bad:model-provider"],
            observability_report_refs=["observability-report:bad"],
            security_privacy_report_refs=["security-privacy-report:bad"],
            command_record_refs=["command:bad"],
            event_cursor_refs=["event-cursor:bad"],
            outbox_refs=["outbox:bad"],
            replay_bundle_ref="replay-bundle:bad",
            operator_status="model_provider_adapter_mapping_completed",
            completion_result=CompletenessResult.PASS,
        )


def test_provider_report_accepts_complete_pass() -> None:
    report = ModelProviderAdapterReport(
        id="model-provider-adapter-report:ok",
        run_ref="run:ok",
        provider_execution_refs=[
            f"model-provider-execution:{provider}" for provider in REQUIRED_MODEL_PROVIDERS
        ],
        required_provider_names=list(REQUIRED_MODEL_PROVIDERS),
        verified_provider_names=list(REQUIRED_MODEL_PROVIDERS),
        model_request_refs=["model-request:ok"],
        model_response_refs=["model-response:ok"],
        model_call_trace_refs=["model-call-trace:ok"],
        context_bundle_trace_refs=["context-bundle-trace:ok"],
        agent_run_refs=["agent-run-request:ok", "agent-run-result:ok"],
        policy_decision_refs=["policy:ok:model-provider"],
        observability_report_refs=["observability-report:ok"],
        security_privacy_report_refs=["security-privacy-report:ok"],
        command_record_refs=["command:ok"],
        event_cursor_refs=["event-cursor:ok"],
        outbox_refs=["outbox:ok"],
        replay_bundle_ref="replay-bundle:ok",
        operator_status="model_provider_adapter_mapping_completed",
        completion_result=CompletenessResult.PASS,
    )
    assert report.verified_provider_names == list(REQUIRED_MODEL_PROVIDERS)


def test_provider_fixture_manifest_rejects_negative_pass() -> None:
    with pytest.raises(ValidationError):
        ModelProviderAdapterFixtureManifest(
            id="model-provider-adapter-bad",
            scenario="model-provider-adapter-bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="bad",
            expected_failure_type=ModelProviderAdapterFailureType.RAW_PROMPT_LEAK,
            negative_case=True,
        )
