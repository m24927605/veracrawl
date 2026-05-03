from __future__ import annotations

from veracrawl.adapters.sources.dynamic_runtime import build_dynamic_source_runtime_records
from veracrawl.contracts.enums import CompletenessResult, DynamicSourceRuntimeFailureType
from veracrawl.contracts.source_runtime import REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS
from veracrawl.fetch.dynamic_source_runtime import run_dynamic_source_runtime_gate


def test_dynamic_source_runtime_gate_success_requires_all_target_source_adapters() -> None:
    fixture_id = "unit"
    result = run_dynamic_source_runtime_gate(
        fixture_id=fixture_id,
        scenario="dynamic-source-runtime-success",
        adapter_records=build_dynamic_source_runtime_records(fixture_id),
    )
    report = result.report
    assert report.completion_result == CompletenessResult.PASS
    assert set(report.verified_adapter_types) == set(REQUIRED_DYNAMIC_SOURCE_RUNTIME_ADAPTERS)
    assert report.adapter_record_refs
    assert report.source_adapter_result_refs
    assert report.natural_result_refs
    assert report.fetch_attempt_refs
    assert report.page_snapshot_refs
    assert report.browser_interaction_refs
    assert report.credential_audit_refs
    assert report.document_artifact_refs
    assert report.api_payload_refs
    assert report.file_artifact_refs
    assert report.seed_plan_refs
    assert report.prior_snapshot_refs
    assert report.policy_decision_refs
    assert report.observability_report_refs
    assert report.security_privacy_report_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.runtime_adapter_refs
    assert report.replay_bundle_ref
    assert result.adapter_records


def test_dynamic_source_runtime_runtime_unavailable_needs_review() -> None:
    result = run_dynamic_source_runtime_gate(
        fixture_id="unit-no-runtime",
        scenario="dynamic-source-runtime-runtime-unavailable",
    )
    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.contract_only_refs
    assert result.report.missing_runtime_refs
    assert "live_runtime_refs" in result.report.missing_ref_fields


def test_dynamic_source_runtime_negative_scenarios_fail() -> None:
    expectations = {
        "dynamic-source-runtime-raw-secret-leak": (
            DynamicSourceRuntimeFailureType.RAW_SECRET_LEAK
        ),
        "dynamic-source-runtime-adapter-state-canonical": (
            DynamicSourceRuntimeFailureType.ADAPTER_NATIVE_STATE_CANONICAL
        ),
        "dynamic-source-runtime-missing-credential-audit": (
            DynamicSourceRuntimeFailureType.MISSING_CREDENTIAL_AUDIT
        ),
        "dynamic-source-runtime-missing-document-artifact": (
            DynamicSourceRuntimeFailureType.MISSING_DOCUMENT_ARTIFACT
        ),
        "dynamic-source-runtime-missing-api-payload": (
            DynamicSourceRuntimeFailureType.MISSING_API_PAYLOAD
        ),
        "dynamic-source-runtime-missing-replay": (
            DynamicSourceRuntimeFailureType.MISSING_REPLAY_REFS
        ),
        "dynamic-source-runtime-unsafe-browser-side-effect": (
            DynamicSourceRuntimeFailureType.UNSAFE_BROWSER_SIDE_EFFECT
        ),
        "dynamic-source-runtime-unsupported-adapter": (
            DynamicSourceRuntimeFailureType.UNSUPPORTED_ADAPTER
        ),
    }
    for scenario, failure in expectations.items():
        result = run_dynamic_source_runtime_gate(fixture_id=scenario, scenario=scenario)
        assert result.report.completion_result == CompletenessResult.FAIL
        assert result.report.operator_status == failure.value
        assert result.report.missing_ref_fields
