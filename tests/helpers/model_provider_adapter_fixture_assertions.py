from __future__ import annotations

from veracrawl.cli.model_providers import ModelProviderAdapterFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.model_provider_adapter import REQUIRED_MODEL_PROVIDERS


def assert_model_provider_adapter_success(
    report: ModelProviderAdapterFixtureRunReport,
) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "model_provider_adapter_mapping_completed"
    assert set(report.verified_provider_names) == set(REQUIRED_MODEL_PROVIDERS)
    assert report.provider_execution_refs
    assert report.model_request_refs
    assert report.model_response_refs
    assert report.model_call_trace_refs
    assert report.context_bundle_trace_refs
    assert report.agent_run_refs
    assert report.policy_decision_refs
    assert report.observability_report_refs
    assert report.security_privacy_report_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.replay_bundle_ref
    assert not report.contract_only_refs
    assert not report.missing_ref_fields


def assert_model_provider_adapter_needs_review(
    report: ModelProviderAdapterFixtureRunReport,
) -> None:
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.operator_status == "model_provider_adapter_runtime_unavailable"
    assert report.contract_only_refs
    assert report.missing_runtime_refs
    assert "live_runtime_refs" in report.missing_ref_fields


def assert_model_provider_adapter_negative(
    report: ModelProviderAdapterFixtureRunReport,
    *,
    operator_status: str,
    missing_field: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert missing_field in report.missing_ref_fields
