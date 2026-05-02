from __future__ import annotations

from veracrawl.cli.evidence import EvidenceFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_evidence_success(report: EvidenceFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.candidate_ref
    assert report.coverage_result_ref
    assert report.evidence_packet_ref
    assert report.evidence_manifest_ref
    assert report.evidence_anchor_refs
    assert report.policy_decision_refs
    assert report.privacy_lifecycle_refs


def assert_publication_success(report: EvidenceFixtureRunReport) -> None:
    assert_evidence_success(report)
    assert report.operator_status == "publication_completed"
    assert report.verification_decision_ref
    assert report.review_decision_ref
    assert report.published_output_ref
    assert report.output_manifest_ref
    assert report.publication_report_ref
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.replay_bundle_ref


def assert_evidence_negative(
    report: EvidenceFixtureRunReport,
    *,
    operator_status: str,
    completion_result: CompletenessResult,
) -> None:
    assert report.operator_status == operator_status
    assert report.completion_result == completion_result
    assert not report.published_output_ref
    assert not report.output_manifest_ref
