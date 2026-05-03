from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.cli.result_publication import run_fixture
from veracrawl.contracts.enums import (
    CompletenessResult,
    ResultPublicationExportFailureType,
)

RESULT_PUBLICATION_FIXTURES = [
    "result-publication-export-success",
    "result-publication-api-success",
    "result-publication-correction-withdrawal-success",
    "result-publication-missing-live-evidence",
    "result-publication-policy-denied",
    "result-publication-verification-not-accepted",
    "result-publication-missing-output-manifest",
    "result-publication-export-missing-receipt",
    "result-publication-withdrawal-missing-propagation",
    "result-publication-correction-without-withdrawal",
    "result-publication-privacy-missing",
    "result-publication-direct-export-bypass",
    "result-publication-replay-mismatch",
]


@pytest.mark.parametrize("fixture_id", RESULT_PUBLICATION_FIXTURES)
def test_result_publication_cli_fixture_contracts(tmp_path: Path, fixture_id: str) -> None:
    fixture_dir = Path("tests/fixtures") / fixture_id
    report = run_fixture(
        fixture_dir,
        profile="target",
        out=tmp_path / fixture_id,
    )

    assert report.fixture_id == fixture_id
    assert (tmp_path / fixture_id / "run_report.json").exists()
    if report.completion_result == CompletenessResult.PASS:
        assert report.live_evidence_runtime_report_ref
        assert report.extraction_candidate_refs
        assert report.evidence_packet_refs
        assert report.verification_decision_refs
        assert report.review_decision_refs
        assert report.publication_report_refs
        assert report.published_output_refs
        assert report.output_manifest_refs
        assert report.result_api_snapshot_refs
        assert report.export_target_spec_refs
        assert report.export_job_refs
        assert report.export_attempt_refs
        assert report.delivery_receipt_refs
        assert report.withdrawal_job_refs
        assert report.withdrawal_attempt_refs
        assert report.correction_record_refs
        assert report.destination_object_mapping_refs
        assert report.policy_decision_refs
        assert report.privacy_lifecycle_refs
        assert report.command_record_refs
        assert report.event_cursor_refs
        assert report.outbox_refs
        assert report.replay_bundle_ref
    elif report.completion_result == CompletenessResult.NEEDS_REVIEW:
        assert report.failure_type is not None
        assert report.failure_report_refs
        if report.failure_type == ResultPublicationExportFailureType.VERIFICATION_NOT_ACCEPTED:
            assert not report.published_output_refs
        if (
            report.failure_type
            == ResultPublicationExportFailureType.WITHDRAWAL_MISSING_PROPAGATION
        ):
            assert report.published_output_refs
            assert not report.withdrawal_job_refs
    else:
        assert report.failure_type is not None
        assert report.failure_report_refs
        assert report.missing_ref_fields
        if report.failure_type == ResultPublicationExportFailureType.DIRECT_EXPORT_BYPASS:
            assert report.direct_export_bypass_refs
            assert not report.published_output_refs
        if report.failure_type == ResultPublicationExportFailureType.EXPORT_MISSING_RECEIPT:
            assert report.export_job_refs
            assert not report.delivery_receipt_refs
        if report.failure_type == ResultPublicationExportFailureType.PRIVACY_MISSING:
            assert not report.privacy_lifecycle_refs
        if report.failure_type == ResultPublicationExportFailureType.REPLAY_MISMATCH:
            assert report.replay_bundle_ref is None
