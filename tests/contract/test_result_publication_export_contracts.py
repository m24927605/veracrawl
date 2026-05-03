from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    ResultPublicationExportFailureType,
)
from veracrawl.contracts.publication import (
    ResultApiSnapshot,
    ResultPublicationExportFixtureManifest,
    ResultPublicationExportRuntimeReport,
)
from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def _passing_report() -> ResultPublicationExportRuntimeReport:
    return ResultPublicationExportRuntimeReport(
        id="result-publication-export-runtime-report:test",
        fixture_id="result-publication-export-success",
        run_ref="run:test",
        live_evidence_runtime_report_ref="live-evidence-verification-runtime-report:test",
        extraction_candidate_refs=["candidate:test"],
        evidence_coverage_refs=["evidence-coverage:test"],
        evidence_packet_refs=["evidence:test"],
        evidence_manifest_refs=["evidence-manifest:test"],
        verification_decision_refs=["verification:test"],
        review_decision_refs=["review:test"],
        publication_report_refs=["publication-report:test"],
        published_output_refs=["published-output:test"],
        output_manifest_refs=["output-manifest:test"],
        result_api_snapshot_refs=["result-api-snapshot:test"],
        export_target_spec_refs=["export-target:test"],
        export_job_refs=["export-job:test"],
        export_attempt_refs=["export-attempt:test:1"],
        delivery_receipt_refs=["export-receipt:test"],
        withdrawal_job_refs=["export-withdrawal-job:test"],
        withdrawal_attempt_refs=["export-withdrawal-attempt:test:1"],
        correction_record_refs=["export-correction:test"],
        destination_object_mapping_refs=["destination-object-mapping:test"],
        policy_decision_refs=["policy:test:publication", "policy:test:export"],
        privacy_lifecycle_refs=["privacy-lifecycle:test:published-output"],
        command_record_refs=["durable-command:test:publication", "durable-command:test:export"],
        event_cursor_refs=["event-cursor:test:publication", "event-cursor:test:export"],
        outbox_refs=["outbox:test:publication", "outbox:test:export"],
        replay_bundle_ref="replay-bundle:test:result-publication",
        operator_status="result_publication_export_completed",
        completion_result=CompletenessResult.PASS,
    )


def test_result_publication_report_requires_publication_export_and_replay() -> None:
    report = _passing_report()
    assert report.completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        ResultPublicationExportRuntimeReport.model_validate(
            report.model_dump(mode="json") | {"published_output_refs": []}
        )
    with pytest.raises(ValidationError):
        ResultPublicationExportRuntimeReport.model_validate(
            report.model_dump(mode="json") | {"delivery_receipt_refs": []}
        )
    with pytest.raises(ValidationError):
        ResultPublicationExportRuntimeReport.model_validate(
            report.model_dump(mode="json") | {"replay_bundle_ref": None}
        )


def test_result_api_snapshot_requires_privacy_and_hash_refs() -> None:
    snapshot = ResultApiSnapshot(
        id="result-api-snapshot:test",
        run_ref="run:test",
        published_output_refs=["published-output:test"],
        output_manifest_refs=["output-manifest:test"],
        response_artifact_ref="artifact:test:result-api-response",
        response_schema_ref="schema:result-api:v1",
        privacy_lifecycle_refs=["privacy-lifecycle:test:published-output"],
        replay_bundle_ref="replay-bundle:test:result-publication",
        response_hash="hash:test",
    )
    assert snapshot.response_hash
    with pytest.raises(ValidationError):
        ResultApiSnapshot.model_validate(
            snapshot.model_dump(mode="json") | {"privacy_lifecycle_refs": []}
        )


def test_result_publication_fixture_requires_failure_type_for_negative_case() -> None:
    manifest = ResultPublicationExportFixtureManifest(
        id="result-publication-export-success",
        scenario="result-publication-export-success",
        path="/static/basic",
        profile_refs=["target"],
        schema_ref="schema:record-summary",
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="result_publication_export_completed",
        required_ref_types=["published_output", "export_receipt", "replay"],
    )
    assert manifest.expected_completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        ResultPublicationExportFixtureManifest(
            id="result-publication-policy-denied",
            scenario="result-publication-policy-denied",
            path="/static/basic",
            profile_refs=["target"],
            schema_ref="schema:record-summary",
            expected_completion_result=CompletenessResult.FAIL,
            expected_operator_status=(
                ResultPublicationExportFailureType.PUBLICATION_POLICY_DENIED.value
            ),
            negative_case=True,
            required_ref_types=["typed_failure"],
        )


def test_result_publication_registry_is_materialized() -> None:
    assert "ResultApiSnapshot" in FOUNDATION_CONTRACTS
    assert "ResultPublicationExportRuntimeReport" in FOUNDATION_CONTRACTS
    assert "ResultPublicationExportFixtureManifest" in FOUNDATION_CONTRACTS
    assert "record_result_publication_export_runtime_report" in COMMAND_TYPES
    assert "record_result_publication_export_fixture_manifest" in COMMAND_TYPES
    assert "result_publication_export_runtime_reported" in EVENT_TYPES
    assert "result-publication-export-success" in FIXTURE_ORACLES
    area = TARGET_CONTRACT_AREAS["result_publication_export_runtime"]
    assert area.coverage_status == "materialized"
    assert "ResultPublicationExportRuntimeReport" in area.materialized_contract_refs
    assert validate_registry().ok
