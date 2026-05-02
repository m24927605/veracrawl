from __future__ import annotations

from veracrawl.cli.agent_adapters import AgentRuntimeAdapterFixtureRunReport
from veracrawl.contracts.agent_adapter import REQUIRED_AGENT_FRAMEWORKS
from veracrawl.contracts.enums import CompletenessResult


def assert_agent_adapter_success(report: AgentRuntimeAdapterFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "agent_runtime_adapter_mapping_completed"
    assert set(report.verified_framework_names) == set(REQUIRED_AGENT_FRAMEWORKS)
    assert report.framework_execution_refs
    assert report.model_provider_refs
    assert report.policy_decision_refs
    assert report.observability_report_refs
    assert report.security_privacy_report_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.replay_bundle_ref
    assert not report.contract_only_refs
    assert not report.missing_ref_fields


def assert_agent_adapter_needs_review(report: AgentRuntimeAdapterFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.operator_status == "agent_runtime_adapter_runtime_unavailable"
    assert report.contract_only_refs
    assert report.missing_runtime_refs
    assert "live_runtime_refs" in report.missing_ref_fields


def assert_agent_adapter_negative(
    report: AgentRuntimeAdapterFixtureRunReport,
    *,
    operator_status: str,
    missing_field: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert missing_field in report.missing_ref_fields
