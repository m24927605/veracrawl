from __future__ import annotations

from veracrawl.adapters.source_coverage.contract import build_contract_execution_records
from veracrawl.contracts.enums import CompletenessResult, SourceCoverageFailureType
from veracrawl.contracts.source_coverage import REQUIRED_SOURCE_COVERAGE_ADAPTERS
from veracrawl.fetch.source_coverage_gate import run_source_coverage_adapter_gate


def test_source_coverage_gate_success_requires_all_target_source_adapters() -> None:
    fixture_id = "unit"
    result = run_source_coverage_adapter_gate(
        fixture_id=fixture_id,
        scenario="source-coverage-adapter-success",
        execution_records=build_contract_execution_records(fixture_id),
    )
    report = result.report
    assert report.completion_result == CompletenessResult.PASS
    assert set(report.verified_adapter_types) == set(REQUIRED_SOURCE_COVERAGE_ADAPTERS)
    assert report.adapter_execution_refs
    assert report.source_adapter_result_refs
    assert report.natural_result_refs
    assert report.fetch_attempt_refs
    assert report.page_snapshot_refs
    assert report.browser_interaction_refs
    assert report.credential_audit_refs
    assert report.document_artifact_refs
    assert report.api_payload_refs
    assert report.policy_decision_refs
    assert report.observability_report_refs
    assert report.security_privacy_report_refs
    assert report.command_record_refs
    assert report.replay_bundle_ref
    assert result.execution_records


def test_source_coverage_runtime_unavailable_needs_review() -> None:
    result = run_source_coverage_adapter_gate(
        fixture_id="unit-no-runtime",
        scenario="source-coverage-adapter-runtime-unavailable",
    )
    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.contract_only_refs
    assert result.report.missing_runtime_refs
    assert "live_runtime_refs" in result.report.missing_ref_fields


def test_source_coverage_negative_scenarios_fail() -> None:
    expectations = {
        "source-coverage-adapter-native-state-canonical": (
            SourceCoverageFailureType.ADAPTER_NATIVE_STATE_CANONICAL
        ),
        "source-coverage-adapter-raw-secret-leak": (
            SourceCoverageFailureType.RAW_SECRET_LEAK
        ),
        "source-coverage-adapter-missing-browser-refs": (
            SourceCoverageFailureType.MISSING_BROWSER_REFS
        ),
        "source-coverage-adapter-missing-credential-audit": (
            SourceCoverageFailureType.MISSING_CREDENTIAL_AUDIT
        ),
        "source-coverage-adapter-missing-document-artifact": (
            SourceCoverageFailureType.MISSING_DOCUMENT_ARTIFACT
        ),
        "source-coverage-adapter-missing-api-payload": (
            SourceCoverageFailureType.MISSING_API_PAYLOAD
        ),
        "source-coverage-adapter-missing-replay": (
            SourceCoverageFailureType.MISSING_REPLAY_REFS
        ),
        "source-coverage-adapter-unsafe-browser-side-effect": (
            SourceCoverageFailureType.UNSAFE_BROWSER_SIDE_EFFECT
        ),
        "source-coverage-adapter-unsupported-adapter": (
            SourceCoverageFailureType.UNSUPPORTED_ADAPTER
        ),
    }
    for scenario, failure in expectations.items():
        result = run_source_coverage_adapter_gate(fixture_id=scenario, scenario=scenario)
        assert result.report.completion_result == CompletenessResult.FAIL
        assert result.report.operator_status == failure.value
        assert result.report.missing_ref_fields
