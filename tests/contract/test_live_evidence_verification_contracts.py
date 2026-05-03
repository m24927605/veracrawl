from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    LiveEvidenceVerificationFailureType,
)
from veracrawl.contracts.evidence import (
    LiveEvidenceVerificationFixtureManifest,
    LiveEvidenceVerificationRuntimeReport,
)
from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def _passing_report() -> LiveEvidenceVerificationRuntimeReport:
    return LiveEvidenceVerificationRuntimeReport(
        id="live-evidence-verification-runtime-report:test",
        fixture_id="live-evidence-verification-success",
        run_ref="run:test",
        schema_extraction_runtime_report_ref="schema-extraction-runtime-report:test",
        extraction_candidate_refs=["candidate:test"],
        normalized_document_refs=["normalized:test"],
        source_anchor_refs=["text-anchor:test:title"],
        evidence_coverage_refs=["evidence-coverage:test"],
        evidence_packet_refs=["evidence:test"],
        evidence_anchor_refs=["evidence-anchor:test:title"],
        evidence_manifest_refs=["evidence-manifest:test"],
        verification_decision_refs=["verification:test"],
        review_decision_refs=["review:test"],
        freshness_refs=["freshness:test:fixture"],
        policy_decision_refs=["policy:test:runtime_evidence", "policy:test:runtime_verification"],
        privacy_lifecycle_refs=["privacy-lifecycle:test:public"],
        command_record_refs=["durable-command:test:live-evidence"],
        event_cursor_refs=["event-cursor:test:live-evidence"],
        outbox_refs=["outbox:test:live-evidence"],
        replay_bundle_ref="replay-bundle:test:live-evidence",
        operator_status="live_evidence_verification_completed",
        completion_result=CompletenessResult.PASS,
    )


def test_live_evidence_report_requires_evidence_verification_and_no_publication() -> None:
    report = _passing_report()
    assert report.completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        LiveEvidenceVerificationRuntimeReport.model_validate(
            report.model_dump(mode="json") | {"evidence_packet_refs": []}
        )
    with pytest.raises(ValidationError):
        LiveEvidenceVerificationRuntimeReport.model_validate(
            report.model_dump(mode="json") | {"verification_decision_refs": []}
        )
    with pytest.raises(ValidationError):
        LiveEvidenceVerificationRuntimeReport.model_validate(
            report.model_dump(mode="json")
            | {"publication_refs": ["published-output:test:forbidden"]}
        )


def test_live_evidence_nonpass_requires_typed_diagnostics() -> None:
    report = LiveEvidenceVerificationRuntimeReport(
        id="live-evidence-verification-runtime-report:conflict",
        fixture_id="live-evidence-verification-conflict",
        run_ref="run:conflict",
        schema_extraction_runtime_report_ref="schema-extraction-runtime-report:conflict",
        extraction_candidate_refs=["candidate:conflict"],
        normalized_document_refs=["normalized:conflict"],
        evidence_coverage_refs=["evidence-coverage:conflict"],
        evidence_packet_refs=["evidence:conflict"],
        evidence_anchor_refs=["evidence-anchor:conflict:title"],
        evidence_manifest_refs=["evidence-manifest:conflict"],
        verification_decision_refs=["verification:conflict"],
        review_decision_refs=["review:conflict"],
        conflict_record_refs=["conflict:conflict:evidence"],
        policy_decision_refs=["policy:conflict:runtime_evidence"],
        privacy_lifecycle_refs=["privacy-lifecycle:conflict:public"],
        failure_report_refs=["failure:conflict:verification-conflict"],
        failure_type=LiveEvidenceVerificationFailureType.VERIFICATION_CONFLICT,
        operator_status=LiveEvidenceVerificationFailureType.VERIFICATION_CONFLICT.value,
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    assert report.conflict_record_refs
    with pytest.raises(ValidationError):
        LiveEvidenceVerificationRuntimeReport(
            id="live-evidence-verification-runtime-report:invalid",
            fixture_id="live-evidence-verification-invalid",
            run_ref="run:invalid",
            operator_status="invalid",
            completion_result=CompletenessResult.FAIL,
        )


def test_live_evidence_manifest_requires_failure_type_for_negative_case() -> None:
    manifest = LiveEvidenceVerificationFixtureManifest(
        id="live-evidence-verification-success",
        scenario="live-evidence-verification-success",
        path="/static/basic",
        profile_refs=["target"],
        schema_ref="schema:record-summary",
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="live_evidence_verification_completed",
        required_ref_types=["evidence_packet", "verification", "review", "replay"],
    )
    assert manifest.expected_completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        LiveEvidenceVerificationFixtureManifest(
            id="live-evidence-verification-missing-source-anchor",
            scenario="live-evidence-verification-missing-source-anchor",
            path="/static/basic",
            profile_refs=["target"],
            schema_ref="schema:record-summary",
            expected_completion_result=CompletenessResult.NEEDS_REVIEW,
            expected_operator_status=(
                LiveEvidenceVerificationFailureType.MISSING_SOURCE_ANCHOR.value
            ),
            negative_case=True,
            required_ref_types=["typed_failure"],
        )


def test_live_evidence_registry_is_materialized() -> None:
    assert "LiveEvidenceVerificationRuntimeReport" in FOUNDATION_CONTRACTS
    assert "LiveEvidenceVerificationFixtureManifest" in FOUNDATION_CONTRACTS
    assert "record_live_evidence_verification_runtime_report" in COMMAND_TYPES
    assert "record_live_evidence_verification_fixture_manifest" in COMMAND_TYPES
    assert "live_evidence_verification_runtime_reported" in EVENT_TYPES
    assert "live-evidence-verification-success" in FIXTURE_ORACLES
    area = TARGET_CONTRACT_AREAS["live_evidence_verification_runtime"]
    assert area.coverage_status == "materialized"
    assert "LiveEvidenceVerificationRuntimeReport" in area.materialized_contract_refs
    assert validate_registry().ok
