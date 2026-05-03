from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    AdapterType,
    CompletenessResult,
    SourceAdapterResultType,
    SourceCoverageFailureType,
)
from veracrawl.contracts.source_coverage import (
    EXPECTED_NATURAL_RESULT_TYPES,
    REQUIRED_SOURCE_COVERAGE_ADAPTERS,
    SourceCoverageAdapterExecutionRecord,
    SourceCoverageAdapterFixtureManifest,
    SourceCoverageAdapterReport,
)


def _execution_record(
    adapter_type: AdapterType = AdapterType.HTTP,
) -> SourceCoverageAdapterExecutionRecord:
    return SourceCoverageAdapterExecutionRecord(
        id=f"source-coverage-execution:{adapter_type.value}",
        adapter_type=adapter_type,
        natural_result_type=EXPECTED_NATURAL_RESULT_TYPES[adapter_type],
        source_adapter_spec_ref=f"source-adapter-spec:{adapter_type.value}",
        source_adapter_result_ref=f"source-adapter-result:{adapter_type.value}",
        natural_result_refs=[f"natural-result:{adapter_type.value}"],
        fetch_attempt_refs=(
            [f"fetch-attempt:{adapter_type.value}"]
            if adapter_type == AdapterType.HTTP
            else []
        ),
        page_snapshot_refs=(
            [f"page-snapshot:{adapter_type.value}"]
            if adapter_type in {AdapterType.HTTP, AdapterType.BROWSER_SNAPSHOT}
            else []
        ),
        browser_interaction_refs=(
            [f"browser-step:{adapter_type.value}"]
            if adapter_type == AdapterType.BROWSER_SNAPSHOT
            else []
        ),
        credential_audit_refs=(
            [f"credential-use:{adapter_type.value}"]
            if adapter_type == AdapterType.AUTHORIZED_SESSION
            else []
        ),
        document_artifact_refs=(
            [f"document-artifact:{adapter_type.value}"]
            if adapter_type in {AdapterType.DOCUMENT_SOURCE, AdapterType.FILE_IMPORT}
            else []
        ),
        api_payload_refs=(
            [f"api-payload:{adapter_type.value}"]
            if adapter_type == AdapterType.API_SOURCE
            else []
        ),
        command_result_refs=[f"command-result:{adapter_type.value}"],
        policy_decision_refs=[f"policy:{adapter_type.value}:source-coverage"],
        observability_report_refs=[f"observability-report:{adapter_type.value}"],
        security_privacy_report_refs=[f"security-privacy-report:{adapter_type.value}"],
        replay_bundle_ref=f"replay-bundle:{adapter_type.value}",
        contract_adapter_refs=[f"contract-adapter:{adapter_type.value}"],
        result=CompletenessResult.PASS,
    )


def test_source_coverage_execution_requires_natural_adapter_mapping() -> None:
    with pytest.raises(ValidationError):
        SourceCoverageAdapterExecutionRecord(
            **(
                _execution_record().model_dump()
                | {"natural_result_type": SourceAdapterResultType.DOCUMENT_ARTIFACT}
            )
        )


def test_source_coverage_execution_rejects_raw_secret_and_native_canonical_state() -> None:
    payload = _execution_record().model_dump()
    with pytest.raises(ValidationError):
        SourceCoverageAdapterExecutionRecord(**(payload | {"raw_secret_persisted": True}))
    with pytest.raises(ValidationError):
        SourceCoverageAdapterExecutionRecord(
            **(payload | {"adapter_native_state_canonical": True})
        )


def test_source_coverage_execution_requires_adapter_specific_refs() -> None:
    browser_payload = _execution_record(AdapterType.BROWSER_SNAPSHOT).model_dump()
    with pytest.raises(ValidationError):
        SourceCoverageAdapterExecutionRecord(
            **(browser_payload | {"browser_interaction_refs": []})
        )
    session_payload = _execution_record(AdapterType.AUTHORIZED_SESSION).model_dump()
    with pytest.raises(ValidationError):
        SourceCoverageAdapterExecutionRecord(
            **(session_payload | {"credential_audit_refs": []})
        )
    document_payload = _execution_record(AdapterType.DOCUMENT_SOURCE).model_dump()
    with pytest.raises(ValidationError):
        SourceCoverageAdapterExecutionRecord(
            **(document_payload | {"document_artifact_refs": []})
        )
    api_payload = _execution_record(AdapterType.API_SOURCE).model_dump()
    with pytest.raises(ValidationError):
        SourceCoverageAdapterExecutionRecord(**(api_payload | {"api_payload_refs": []}))


def test_source_coverage_report_pass_requires_all_required_adapters() -> None:
    with pytest.raises(ValidationError):
        SourceCoverageAdapterReport(
            id="source-coverage-report:bad",
            run_ref="run:bad",
            adapter_execution_refs=["source-coverage-execution:http"],
            required_adapter_types=list(REQUIRED_SOURCE_COVERAGE_ADAPTERS),
            verified_adapter_types=[AdapterType.HTTP],
            source_adapter_result_refs=["source-adapter-result:http"],
            natural_result_refs=["natural-result:http"],
            fetch_attempt_refs=["fetch-attempt:http"],
            page_snapshot_refs=["page-snapshot:http"],
            browser_interaction_refs=["browser-step:browser"],
            credential_audit_refs=["credential-use:session"],
            document_artifact_refs=["document-artifact:document"],
            api_payload_refs=["api-payload:api"],
            policy_decision_refs=["policy:bad:source-coverage"],
            observability_report_refs=["observability-report:bad"],
            security_privacy_report_refs=["security-privacy-report:bad"],
            command_record_refs=["command:bad"],
            event_cursor_refs=["event-cursor:bad"],
            outbox_refs=["outbox:bad"],
            replay_bundle_ref="replay-bundle:bad",
            operator_status="source_coverage_adapter_mapping_completed",
            completion_result=CompletenessResult.PASS,
        )


def test_source_coverage_report_accepts_complete_pass() -> None:
    report = SourceCoverageAdapterReport(
        id="source-coverage-report:ok",
        run_ref="run:ok",
        adapter_execution_refs=[
            f"source-coverage-execution:{adapter_type.value}"
            for adapter_type in REQUIRED_SOURCE_COVERAGE_ADAPTERS
        ],
        required_adapter_types=list(REQUIRED_SOURCE_COVERAGE_ADAPTERS),
        verified_adapter_types=list(REQUIRED_SOURCE_COVERAGE_ADAPTERS),
        source_adapter_result_refs=["source-adapter-result:ok"],
        natural_result_refs=["natural-result:ok"],
        fetch_attempt_refs=["fetch-attempt:ok"],
        page_snapshot_refs=["page-snapshot:ok"],
        browser_interaction_refs=["browser-step:ok"],
        credential_audit_refs=["credential-use:ok"],
        document_artifact_refs=["document-artifact:ok"],
        api_payload_refs=["api-payload:ok"],
        policy_decision_refs=["policy:ok:source-coverage"],
        observability_report_refs=["observability-report:ok"],
        security_privacy_report_refs=["security-privacy-report:ok"],
        command_record_refs=["command:ok"],
        event_cursor_refs=["event-cursor:ok"],
        outbox_refs=["outbox:ok"],
        replay_bundle_ref="replay-bundle:ok",
        operator_status="source_coverage_adapter_mapping_completed",
        completion_result=CompletenessResult.PASS,
    )
    assert report.verified_adapter_types == list(REQUIRED_SOURCE_COVERAGE_ADAPTERS)


def test_source_coverage_fixture_manifest_rejects_negative_pass() -> None:
    with pytest.raises(ValidationError):
        SourceCoverageAdapterFixtureManifest(
            id="source-coverage-adapter-bad",
            scenario="source-coverage-adapter-bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="bad",
            expected_failure_type=SourceCoverageFailureType.RAW_SECRET_LEAK,
            negative_case=True,
        )
