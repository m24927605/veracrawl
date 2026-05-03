from __future__ import annotations

from veracrawl.cli.temporal_kg import TemporalKGFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult, TemporalKGStatus


def assert_temporal_kg_projection_success(report: TemporalKGFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "temporal_kg_projection_completed"
    assert report.identity_refs
    assert report.projection_record_refs
    assert report.source_verified_fact_refs
    assert report.source_published_output_refs
    assert report.source_event_refs
    assert report.evidence_packet_refs
    assert report.projection_watermark_refs
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.replay_bundle_ref
    assert set(report.identity_statuses) == {TemporalKGStatus.CURRENT}
    assert set(report.projection_statuses) == {TemporalKGStatus.CURRENT}
    assert not report.temporal_kg_as_evidence_refs
    assert not report.missing_ref_fields


def assert_temporal_kg_false_merge_success(report: TemporalKGFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "temporal_kg_identity_adjudicated"
    assert report.adjudication_record_refs
    assert report.conflict_record_refs
    assert report.invalidation_refs
    assert TemporalKGStatus.INVALIDATED in report.identity_statuses


def assert_temporal_kg_false_split_success(report: TemporalKGFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "temporal_kg_identity_superseded"
    assert report.adjudication_record_refs
    assert report.conflict_record_refs
    assert report.supersession_refs
    assert TemporalKGStatus.SUPERSEDED in report.identity_statuses


def assert_temporal_kg_needs_review(report: TemporalKGFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.operator_status == "temporal_kg_runtime_unavailable"
    assert report.contract_only_refs
    assert report.missing_runtime_refs
    assert "live_runtime_refs" in report.missing_ref_fields


def assert_temporal_kg_negative(
    report: TemporalKGFixtureRunReport,
    *,
    operator_status: str,
    missing_field: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_type is not None
    assert missing_field in report.missing_ref_fields
