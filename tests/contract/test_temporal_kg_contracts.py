from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    TemporalKGAdjudicationDecisionType,
    TemporalKGConflictType,
    TemporalKGEntityType,
    TemporalKGFailureType,
    TemporalKGStatus,
)
from veracrawl.contracts.graph import (
    TemporalKGEntityIdentity,
    TemporalKGFixtureManifest,
    TemporalKGIdentityAdjudicationRecord,
    TemporalKGProjectionRecord,
    TemporalKGRuntimeReport,
)


def _identity() -> TemporalKGEntityIdentity:
    return TemporalKGEntityIdentity(
        id="temporal-kg-identity:contract",
        run_ref="run:contract",
        entity_key="entity:contract",
        entity_type=TemporalKGEntityType.ORGANIZATION,
        canonical_label="Contract Entity",
        alias_refs=["alias:contract"],
        identity_evidence_refs=["identity-evidence:contract"],
        source_verified_fact_refs=["verified-fact:contract"],
        source_published_output_refs=["published-output:contract"],
        source_event_refs=["event:contract:published"],
        confidence=0.99,
        valid_from_ref="valid-time:contract:from",
        transaction_time_ref="transaction-time:contract:projected",
        status=TemporalKGStatus.CURRENT,
    )


def _projection() -> TemporalKGProjectionRecord:
    return TemporalKGProjectionRecord(
        id="temporal-kg-projection:contract",
        run_ref="run:contract",
        projection_version="temporal-kg-v1",
        entity_identity_ref="temporal-kg-identity:contract",
        subject_entity_key="entity:contract",
        predicate="has_verified_attribute",
        object_value_ref="verified-value:contract",
        value_type="string",
        valid_from_ref="valid-time:contract:from",
        observed_at_ref="transaction-time:contract:observed",
        projected_at_ref="transaction-time:contract:projected",
        source_verified_fact_refs=["verified-fact:contract"],
        source_published_output_refs=["published-output:contract"],
        source_event_refs=["event:contract:published"],
        evidence_packet_refs=["evidence-packet:contract"],
        status=TemporalKGStatus.CURRENT,
        projection_watermark_ref="projection-watermark:contract",
    )


def _adjudication(
    conflict_type: TemporalKGConflictType = TemporalKGConflictType.FALSE_MERGE,
) -> TemporalKGIdentityAdjudicationRecord:
    return TemporalKGIdentityAdjudicationRecord(
        id=f"temporal-kg-adjudication:{conflict_type.value}",
        run_ref="run:contract",
        conflict_type=conflict_type,
        decision_type=(
            TemporalKGAdjudicationDecisionType.INVALIDATE_IDENTITY
            if conflict_type == TemporalKGConflictType.FALSE_MERGE
            else TemporalKGAdjudicationDecisionType.MERGE_IDENTITY
        ),
        identity_refs=["temporal-kg-identity:contract:a", "temporal-kg-identity:contract:b"],
        projection_record_refs=["temporal-kg-projection:contract"],
        conflict_record_refs=[f"conflict:contract:{conflict_type.value}"],
        adjudication_authority_ref="review-authority:contract",
        evidence_input_refs=["evidence-packet:contract"],
        source_event_refs=["event:contract:review_decided"],
        policy_decision_refs=["policy:contract"],
        resulting_identity_refs=["temporal-kg-identity:contract:result"],
        invalidated_identity_refs=(
            ["temporal-kg-identity:contract:b"]
            if conflict_type == TemporalKGConflictType.FALSE_MERGE
            else []
        ),
        superseded_identity_refs=(
            ["temporal-kg-identity:contract:a", "temporal-kg-identity:contract:b"]
            if conflict_type == TemporalKGConflictType.FALSE_SPLIT
            else []
        ),
        command_record_refs=["command:contract"],
        event_cursor_refs=["event-cursor:contract"],
        outbox_refs=["outbox:contract"],
        replay_bundle_ref="replay:contract",
        result=CompletenessResult.PASS,
    )


def test_temporal_kg_identity_requires_evidence_and_canonical_sources() -> None:
    with pytest.raises(ValidationError):
        TemporalKGEntityIdentity(**(_identity().model_dump() | {"identity_evidence_refs": []}))
    with pytest.raises(ValidationError):
        TemporalKGEntityIdentity(
            **(
                _identity().model_dump()
                | {
                    "source_verified_fact_refs": [],
                    "source_published_output_refs": [],
                    "source_event_refs": [],
                }
            )
        )


def test_temporal_kg_identity_rejects_current_provisional_identity() -> None:
    with pytest.raises(ValidationError):
        TemporalKGEntityIdentity(
            **(_identity().model_dump() | {"provisional_graph_identity_refs": ["graph:cluster"]})
        )


def test_temporal_kg_projection_requires_sources_and_rejects_evidence_use() -> None:
    with pytest.raises(ValidationError):
        TemporalKGProjectionRecord(**(_projection().model_dump() | {"source_event_refs": []}))
    with pytest.raises(ValidationError):
        TemporalKGProjectionRecord(**(_projection().model_dump() | {"evidence_ref_allowed": True}))


def test_temporal_kg_adjudication_requires_conflict_specific_refs() -> None:
    with pytest.raises(ValidationError):
        TemporalKGIdentityAdjudicationRecord(
            **(_adjudication().model_dump() | {"invalidated_identity_refs": []})
        )
    with pytest.raises(ValidationError):
        TemporalKGIdentityAdjudicationRecord(
            **(
                _adjudication(TemporalKGConflictType.FALSE_SPLIT).model_dump()
                | {"superseded_identity_refs": []}
            )
        )


def test_temporal_kg_report_requires_complete_pass_refs() -> None:
    with pytest.raises(ValidationError):
        TemporalKGRuntimeReport(
            id="temporal-kg-report:bad",
            run_ref="run:bad",
            identity_refs=["temporal-kg-identity:bad"],
            projection_record_refs=[],
            source_verified_fact_refs=["verified-fact:bad"],
            source_published_output_refs=["published-output:bad"],
            source_event_refs=["event:bad"],
            evidence_packet_refs=["evidence-packet:bad"],
            projection_watermark_refs=["projection-watermark:bad"],
            policy_decision_refs=["policy:bad"],
            command_record_refs=["command:bad"],
            event_cursor_refs=["event-cursor:bad"],
            outbox_refs=["outbox:bad"],
            replay_bundle_ref="replay:bad",
            operator_status="temporal_kg_projection_completed",
            completion_result=CompletenessResult.PASS,
        )


def test_temporal_kg_report_accepts_complete_pass_and_typed_fail() -> None:
    report = TemporalKGRuntimeReport(
        id="temporal-kg-report:ok",
        run_ref="run:ok",
        identity_refs=["temporal-kg-identity:ok"],
        projection_record_refs=["temporal-kg-projection:ok"],
        source_verified_fact_refs=["verified-fact:ok"],
        source_published_output_refs=["published-output:ok"],
        source_event_refs=["event:ok"],
        evidence_packet_refs=["evidence-packet:ok"],
        projection_watermark_refs=["projection-watermark:ok"],
        policy_decision_refs=["policy:ok"],
        command_record_refs=["command:ok"],
        event_cursor_refs=["event-cursor:ok"],
        outbox_refs=["outbox:ok"],
        replay_bundle_ref="replay:ok",
        operator_status="temporal_kg_projection_completed",
        completion_result=CompletenessResult.PASS,
    )
    assert report.completion_result == CompletenessResult.PASS

    failed = TemporalKGRuntimeReport(
        id="temporal-kg-report:fail",
        run_ref="run:fail",
        failure_type=TemporalKGFailureType.PROJECTION_AS_EVIDENCE,
        failure_report_refs=["failure:fail"],
        temporal_kg_as_evidence_refs=["temporal-kg-projection:fail"],
        missing_ref_fields=["temporal_kg_projection_ref"],
        operator_status=TemporalKGFailureType.PROJECTION_AS_EVIDENCE.value,
        completion_result=CompletenessResult.FAIL,
    )
    assert failed.failure_type == TemporalKGFailureType.PROJECTION_AS_EVIDENCE


def test_temporal_kg_fixture_manifest_rejects_invalid_negative_expectations() -> None:
    with pytest.raises(ValidationError):
        TemporalKGFixtureManifest(
            id="temporal-kg-bad",
            scenario="temporal-kg-bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="bad",
            expected_failure_type=TemporalKGFailureType.PROVISIONAL_IDENTITY,
            negative_case=True,
        )
    with pytest.raises(ValidationError):
        TemporalKGFixtureManifest(
            id="temporal-kg-bad",
            scenario="temporal-kg-bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.FAIL,
            expected_operator_status="bad",
            expected_failure_type=TemporalKGFailureType.PROVISIONAL_IDENTITY,
            negative_case=False,
        )
