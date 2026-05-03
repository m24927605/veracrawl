from __future__ import annotations

from veracrawl.contracts.enums import (
    CompletenessResult,
    TemporalKGConflictType,
    TemporalKGFailureType,
    TemporalKGStatus,
)
from veracrawl.graph.temporal_kg import run_temporal_kg_runtime_gate


def test_temporal_kg_projection_success_requires_canonical_bitemporal_refs() -> None:
    result = run_temporal_kg_runtime_gate(
        fixture_id="unit",
        scenario="temporal-kg-projection-success",
    )
    report = result.report
    assert report.completion_result == CompletenessResult.PASS
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
    assert {identity.status for identity in result.identities} == {TemporalKGStatus.CURRENT}
    assert {record.status for record in result.projection_records} == {TemporalKGStatus.CURRENT}


def test_temporal_kg_false_merge_records_adjudication_and_invalidation() -> None:
    result = run_temporal_kg_runtime_gate(
        fixture_id="unit-false-merge",
        scenario="temporal-kg-false-merge-adjudicated",
    )
    assert result.report.completion_result == CompletenessResult.PASS
    assert result.report.adjudication_record_refs
    assert result.report.conflict_record_refs
    assert result.report.invalidation_refs
    assert {adjudication.conflict_type for adjudication in result.adjudications} == {
        TemporalKGConflictType.FALSE_MERGE
    }
    assert TemporalKGStatus.INVALIDATED in {identity.status for identity in result.identities}


def test_temporal_kg_false_split_records_supersession() -> None:
    result = run_temporal_kg_runtime_gate(
        fixture_id="unit-false-split",
        scenario="temporal-kg-false-split-superseded",
    )
    assert result.report.completion_result == CompletenessResult.PASS
    assert result.report.adjudication_record_refs
    assert result.report.conflict_record_refs
    assert result.report.supersession_refs
    assert {adjudication.conflict_type for adjudication in result.adjudications} == {
        TemporalKGConflictType.FALSE_SPLIT
    }
    assert TemporalKGStatus.SUPERSEDED in {identity.status for identity in result.identities}


def test_temporal_kg_runtime_unavailable_needs_review() -> None:
    result = run_temporal_kg_runtime_gate(
        fixture_id="unit-no-runtime",
        scenario="temporal-kg-runtime-unavailable",
    )
    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.contract_only_refs
    assert result.report.missing_runtime_refs
    assert "live_runtime_refs" in result.report.missing_ref_fields


def test_temporal_kg_negative_scenarios_fail() -> None:
    expectations = {
        "temporal-kg-provisional-identity": TemporalKGFailureType.PROVISIONAL_IDENTITY,
        "temporal-kg-projection-as-evidence": TemporalKGFailureType.PROJECTION_AS_EVIDENCE,
        "temporal-kg-missing-canonical-source": (
            TemporalKGFailureType.MISSING_CANONICAL_SOURCES
        ),
        "temporal-kg-missing-bitemporal-refs": (
            TemporalKGFailureType.MISSING_BITEMPORAL_REFS
        ),
        "temporal-kg-false-merge-without-adjudication": (
            TemporalKGFailureType.FALSE_MERGE_WITHOUT_ADJUDICATION
        ),
        "temporal-kg-false-split-without-supersession": (
            TemporalKGFailureType.FALSE_SPLIT_WITHOUT_SUPERSESSION
        ),
        "temporal-kg-missing-replay": TemporalKGFailureType.MISSING_REPLAY_REFS,
    }
    for scenario, failure in expectations.items():
        result = run_temporal_kg_runtime_gate(fixture_id=scenario, scenario=scenario)
        assert result.report.completion_result == CompletenessResult.FAIL
        assert result.report.failure_type == failure
        assert result.report.operator_status == failure.value
        assert result.report.missing_ref_fields
