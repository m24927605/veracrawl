from __future__ import annotations

from veracrawl.adapters.model_providers.contract import build_contract_execution_records
from veracrawl.agents.model_provider_gate import run_model_provider_adapter_gate
from veracrawl.contracts.enums import CompletenessResult, ModelProviderAdapterFailureType
from veracrawl.contracts.model_provider_adapter import REQUIRED_MODEL_PROVIDERS


def test_model_provider_adapter_gate_success_requires_all_providers() -> None:
    fixture_id = "unit"
    result = run_model_provider_adapter_gate(
        fixture_id=fixture_id,
        scenario="model-provider-adapter-success",
        execution_records=build_contract_execution_records(fixture_id),
    )
    report = result.report
    assert report.completion_result == CompletenessResult.PASS
    assert set(report.verified_provider_names) == set(REQUIRED_MODEL_PROVIDERS)
    assert report.provider_execution_refs
    assert report.model_request_refs
    assert report.model_response_refs
    assert report.model_call_trace_refs
    assert report.context_bundle_trace_refs
    assert report.security_privacy_report_refs
    assert report.replay_bundle_ref
    assert result.execution_records


def test_model_provider_adapter_runtime_unavailable_needs_review() -> None:
    result = run_model_provider_adapter_gate(
        fixture_id="unit-no-runtime",
        scenario="model-provider-adapter-runtime-unavailable",
    )
    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.contract_only_refs
    assert result.report.missing_runtime_refs
    assert "live_runtime_refs" in result.report.missing_ref_fields


def test_model_provider_adapter_negative_scenarios_fail() -> None:
    expectations = {
        "model-provider-adapter-raw-prompt-leak": (
            ModelProviderAdapterFailureType.RAW_PROMPT_LEAK
        ),
        "model-provider-adapter-raw-response-leak": (
            ModelProviderAdapterFailureType.RAW_RESPONSE_LEAK
        ),
        "model-provider-adapter-provider-state-canonical": (
            ModelProviderAdapterFailureType.PROVIDER_TRANSCRIPT_CANONICAL
        ),
        "model-provider-adapter-missing-context-trace": (
            ModelProviderAdapterFailureType.MISSING_CONTEXT_TRACE
        ),
        "model-provider-adapter-missing-replay": (
            ModelProviderAdapterFailureType.MISSING_REPLAY_REFS
        ),
        "model-provider-adapter-missing-security-privacy": (
            ModelProviderAdapterFailureType.MISSING_SECURITY_PRIVACY_REFS
        ),
        "model-provider-adapter-unsafe-tool-suggestion": (
            ModelProviderAdapterFailureType.UNSAFE_TOOL_SUGGESTION
        ),
        "model-provider-adapter-unsupported-provider": (
            ModelProviderAdapterFailureType.UNSUPPORTED_PROVIDER
        ),
    }
    for scenario, failure in expectations.items():
        result = run_model_provider_adapter_gate(fixture_id=scenario, scenario=scenario)
        assert result.report.completion_result == CompletenessResult.FAIL
        assert result.report.operator_status == failure.value
        assert result.report.missing_ref_fields
