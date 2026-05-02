"""Core model provider adapter operational gate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import CompletenessResult, ModelProviderAdapterFailureType
from veracrawl.contracts.model_provider_adapter import (
    REQUIRED_MODEL_PROVIDERS,
    ModelProviderAdapterExecutionRecord,
    ModelProviderAdapterReport,
)


@dataclass(frozen=True)
class ModelProviderAdapterGateResult:
    execution_records: list[ModelProviderAdapterExecutionRecord]
    report: ModelProviderAdapterReport


_FAILURES: dict[str, tuple[ModelProviderAdapterFailureType, str]] = {
    "model-provider-adapter-raw-prompt-leak": (
        ModelProviderAdapterFailureType.RAW_PROMPT_LEAK,
        "raw_prompt_leak_refs",
    ),
    "model-provider-adapter-raw-response-leak": (
        ModelProviderAdapterFailureType.RAW_RESPONSE_LEAK,
        "raw_response_leak_refs",
    ),
    "model-provider-adapter-provider-state-canonical": (
        ModelProviderAdapterFailureType.PROVIDER_TRANSCRIPT_CANONICAL,
        "provider_transcript_canonical_refs",
    ),
    "model-provider-adapter-missing-context-trace": (
        ModelProviderAdapterFailureType.MISSING_CONTEXT_TRACE,
        "context_bundle_trace_refs",
    ),
    "model-provider-adapter-missing-replay": (
        ModelProviderAdapterFailureType.MISSING_REPLAY_REFS,
        "replay_bundle_ref",
    ),
    "model-provider-adapter-missing-security-privacy": (
        ModelProviderAdapterFailureType.MISSING_SECURITY_PRIVACY_REFS,
        "security_privacy_report_refs",
    ),
    "model-provider-adapter-unsafe-tool-suggestion": (
        ModelProviderAdapterFailureType.UNSAFE_TOOL_SUGGESTION,
        "unsafe_tool_suggestion_refs",
    ),
    "model-provider-adapter-unsupported-provider": (
        ModelProviderAdapterFailureType.UNSUPPORTED_PROVIDER,
        "unsupported_provider_refs",
    ),
}


def run_model_provider_adapter_gate(
    *,
    fixture_id: str,
    scenario: str,
    execution_records: list[ModelProviderAdapterExecutionRecord] | None = None,
    policy_decision_refs: list[Ref] | None = None,
) -> ModelProviderAdapterGateResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:model-provider"]
    if scenario == "model-provider-adapter-runtime-unavailable":
        return _needs_review_result(fixture_id=fixture_id, policy_refs=policy_refs)
    if scenario in _FAILURES:
        failure, missing_field = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing_field,
            policy_refs=policy_refs,
        )
    if not execution_records:
        return _needs_review_result(fixture_id=fixture_id, policy_refs=policy_refs)
    return _success_result(
        fixture_id=fixture_id,
        execution_records=execution_records,
        policy_refs=policy_refs,
    )


def _success_result(
    *,
    fixture_id: str,
    execution_records: list[ModelProviderAdapterExecutionRecord],
    policy_refs: list[Ref],
) -> ModelProviderAdapterGateResult:
    verified = [record.provider_name for record in execution_records]
    report = ModelProviderAdapterReport(
        id=f"model-provider-adapter-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        provider_execution_refs=[record.id for record in execution_records],
        required_provider_names=list(REQUIRED_MODEL_PROVIDERS),
        verified_provider_names=verified,
        model_request_refs=[record.model_request_ref for record in execution_records],
        model_response_refs=[record.model_response_ref for record in execution_records],
        model_call_trace_refs=[record.model_call_trace_ref for record in execution_records],
        context_bundle_trace_refs=[
            record.context_bundle_trace_ref for record in execution_records
        ],
        agent_run_refs=[
            ref
            for record in execution_records
            for ref in (record.agent_run_request_ref, record.agent_run_result_ref)
        ],
        policy_decision_refs=policy_refs,
        observability_report_refs=[f"observability-report:{fixture_id}:model-provider"],
        security_privacy_report_refs=[
            f"security-privacy-report:{fixture_id}:model-provider"
        ],
        command_record_refs=[f"command:{fixture_id}:model-provider"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:model-provider"],
        outbox_refs=[f"outbox:{fixture_id}:model-provider"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:model-provider",
        operator_status="model_provider_adapter_mapping_completed",
        completion_result=CompletenessResult.PASS,
    )
    return ModelProviderAdapterGateResult(execution_records=execution_records, report=report)


def _needs_review_result(
    *,
    fixture_id: str,
    policy_refs: list[Ref],
) -> ModelProviderAdapterGateResult:
    report = ModelProviderAdapterReport(
        id=f"model-provider-adapter-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        required_provider_names=list(REQUIRED_MODEL_PROVIDERS),
        policy_decision_refs=policy_refs,
        contract_only_refs=[f"contract-only:{fixture_id}:model-provider"],
        missing_runtime_refs=[
            f"missing-runtime:{fixture_id}:{provider.lower().replace(' ', '-')}"
            for provider in REQUIRED_MODEL_PROVIDERS
        ],
        missing_ref_fields=["live_runtime_refs"],
        operator_status="model_provider_adapter_runtime_unavailable",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    return ModelProviderAdapterGateResult(execution_records=[], report=report)


def _failure_result(
    *,
    fixture_id: str,
    failure: ModelProviderAdapterFailureType,
    missing_field: str,
    policy_refs: list[Ref],
) -> ModelProviderAdapterGateResult:
    report = ModelProviderAdapterReport(
        id=f"model-provider-adapter-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        required_provider_names=list(REQUIRED_MODEL_PROVIDERS),
        verified_provider_names=[],
        policy_decision_refs=policy_refs,
        raw_prompt_leak_refs=(
            [f"raw-prompt-leak:{fixture_id}:model-provider"]
            if missing_field == "raw_prompt_leak_refs"
            else []
        ),
        raw_response_leak_refs=(
            [f"raw-response-leak:{fixture_id}:model-provider"]
            if missing_field == "raw_response_leak_refs"
            else []
        ),
        provider_transcript_canonical_refs=(
            [f"provider-transcript:{fixture_id}:canonical"]
            if missing_field == "provider_transcript_canonical_refs"
            else []
        ),
        unsafe_tool_suggestion_refs=(
            [f"unsafe-tool-suggestion:{fixture_id}:model-provider"]
            if missing_field == "unsafe_tool_suggestion_refs"
            else []
        ),
        unsupported_provider_refs=(
            [f"unsupported-provider:{fixture_id}:unknown"]
            if missing_field == "unsupported_provider_refs"
            else []
        ),
        missing_ref_fields=[missing_field],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )
    return ModelProviderAdapterGateResult(execution_records=[], report=report)
