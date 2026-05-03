"""Deterministic temporal KG identity and projection runtime gate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
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
    TemporalKGIdentityAdjudicationRecord,
    TemporalKGProjectionRecord,
    TemporalKGRuntimeReport,
)


@dataclass(frozen=True)
class TemporalKGRuntimeResult:
    identities: list[TemporalKGEntityIdentity]
    projection_records: list[TemporalKGProjectionRecord]
    adjudications: list[TemporalKGIdentityAdjudicationRecord]
    report: TemporalKGRuntimeReport


_FAILURES: dict[str, tuple[TemporalKGFailureType, str | None, str]] = {
    "temporal-kg-provisional-identity": (
        TemporalKGFailureType.PROVISIONAL_IDENTITY,
        "provisional_identity_refs",
        "provisional_graph_identity_refs",
    ),
    "temporal-kg-projection-as-evidence": (
        TemporalKGFailureType.PROJECTION_AS_EVIDENCE,
        "temporal_kg_as_evidence_refs",
        "temporal_kg_projection_ref",
    ),
    "temporal-kg-missing-canonical-source": (
        TemporalKGFailureType.MISSING_CANONICAL_SOURCES,
        "missing_canonical_source_refs",
        "source_verified_fact_refs",
    ),
    "temporal-kg-missing-bitemporal-refs": (
        TemporalKGFailureType.MISSING_BITEMPORAL_REFS,
        "missing_bitemporal_refs",
        "valid_time_and_transaction_time_refs",
    ),
    "temporal-kg-false-merge-without-adjudication": (
        TemporalKGFailureType.FALSE_MERGE_WITHOUT_ADJUDICATION,
        "false_merge_without_adjudication_refs",
        "adjudication_record_refs",
    ),
    "temporal-kg-false-split-without-supersession": (
        TemporalKGFailureType.FALSE_SPLIT_WITHOUT_SUPERSESSION,
        "false_split_without_supersession_refs",
        "supersession_refs",
    ),
    "temporal-kg-missing-replay": (
        TemporalKGFailureType.MISSING_REPLAY_REFS,
        None,
        "replay_bundle_ref",
    ),
}


def run_temporal_kg_runtime_gate(
    *,
    fixture_id: str,
    scenario: str,
    policy_decision_refs: list[Ref] | None = None,
) -> TemporalKGRuntimeResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:temporal-kg"]
    if scenario == "temporal-kg-runtime-unavailable":
        return _needs_review_result(fixture_id=fixture_id, policy_refs=policy_refs)
    if scenario == "temporal-kg-false-merge-adjudicated":
        return _false_merge_success(fixture_id=fixture_id, policy_refs=policy_refs)
    if scenario == "temporal-kg-false-split-superseded":
        return _false_split_success(fixture_id=fixture_id, policy_refs=policy_refs)
    if scenario in _FAILURES:
        failure, report_field, missing_field = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            report_field=report_field,
            missing_field=missing_field,
            policy_refs=policy_refs,
        )
    return _projection_success(fixture_id=fixture_id, policy_refs=policy_refs)


def _projection_success(
    *,
    fixture_id: str,
    policy_refs: list[Ref],
) -> TemporalKGRuntimeResult:
    source_refs = _source_refs(fixture_id)
    identity = _identity(
        fixture_id=fixture_id,
        suffix="entity-1",
        entity_key=f"entity:{fixture_id}:1",
        label="Verified Entity 1",
        source_refs=source_refs,
    )
    projection = _projection(
        fixture_id=fixture_id,
        suffix="fact-1",
        identity_ref=identity.id,
        subject_key=identity.entity_key,
        source_refs=source_refs,
    )
    report = _pass_report(
        fixture_id=fixture_id,
        identities=[identity],
        projections=[projection],
        adjudications=[],
        source_refs=source_refs,
        policy_refs=policy_refs,
        operator_status="temporal_kg_projection_completed",
    )
    return TemporalKGRuntimeResult([identity], [projection], [], report)


def _false_merge_success(
    *,
    fixture_id: str,
    policy_refs: list[Ref],
) -> TemporalKGRuntimeResult:
    source_refs = _source_refs(fixture_id)
    adjudication_ref = f"temporal-kg-adjudication:{fixture_id}:false-merge"
    kept_identity = _identity(
        fixture_id=fixture_id,
        suffix="kept",
        entity_key=f"entity:{fixture_id}:kept",
        label="Adjudicated Entity",
        source_refs=source_refs,
    )
    invalidated_identity = _identity(
        fixture_id=fixture_id,
        suffix="invalidated",
        entity_key=f"entity:{fixture_id}:invalidated",
        label="Invalidated Merge Candidate",
        source_refs=source_refs,
        status=TemporalKGStatus.INVALIDATED,
        adjudication_record_refs=[adjudication_ref],
        conflict_record_refs=[f"conflict:{fixture_id}:false-merge"],
        invalidation_ref=f"invalidation:{fixture_id}:false-merge",
    )
    projection = _projection(
        fixture_id=fixture_id,
        suffix="false-merge-repaired-fact",
        identity_ref=kept_identity.id,
        subject_key=kept_identity.entity_key,
        source_refs=source_refs,
    )
    adjudication = _adjudication(
        fixture_id=fixture_id,
        suffix="false-merge",
        conflict_type=TemporalKGConflictType.FALSE_MERGE,
        decision_type=TemporalKGAdjudicationDecisionType.INVALIDATE_IDENTITY,
        identity_refs=[kept_identity.id, invalidated_identity.id],
        projection_refs=[projection.id],
        resulting_identity_refs=[kept_identity.id],
        invalidated_identity_refs=[invalidated_identity.id],
        source_refs=source_refs,
        policy_refs=policy_refs,
    )
    report = _pass_report(
        fixture_id=fixture_id,
        identities=[kept_identity, invalidated_identity],
        projections=[projection],
        adjudications=[adjudication],
        source_refs=source_refs,
        policy_refs=policy_refs,
        operator_status="temporal_kg_identity_adjudicated",
        conflict_refs=[f"conflict:{fixture_id}:false-merge"],
        invalidation_refs=[f"invalidation:{fixture_id}:false-merge"],
    )
    return TemporalKGRuntimeResult(
        [kept_identity, invalidated_identity],
        [projection],
        [adjudication],
        report,
    )


def _false_split_success(
    *,
    fixture_id: str,
    policy_refs: list[Ref],
) -> TemporalKGRuntimeResult:
    source_refs = _source_refs(fixture_id)
    adjudication_ref = f"temporal-kg-adjudication:{fixture_id}:false-split"
    resulting_identity_ref = f"temporal-kg-identity:{fixture_id}:merged"
    split_left = _identity(
        fixture_id=fixture_id,
        suffix="split-left",
        entity_key=f"entity:{fixture_id}:split-left",
        label="Split Candidate Left",
        source_refs=source_refs,
        status=TemporalKGStatus.SUPERSEDED,
        adjudication_record_refs=[adjudication_ref],
        conflict_record_refs=[f"conflict:{fixture_id}:false-split"],
        superseded_by_identity_ref=resulting_identity_ref,
    )
    split_right = _identity(
        fixture_id=fixture_id,
        suffix="split-right",
        entity_key=f"entity:{fixture_id}:split-right",
        label="Split Candidate Right",
        source_refs=source_refs,
        status=TemporalKGStatus.SUPERSEDED,
        adjudication_record_refs=[adjudication_ref],
        conflict_record_refs=[f"conflict:{fixture_id}:false-split"],
        superseded_by_identity_ref=resulting_identity_ref,
    )
    merged = _identity(
        fixture_id=fixture_id,
        suffix="merged",
        entity_key=f"entity:{fixture_id}:merged",
        label="Merged Entity",
        source_refs=source_refs,
        adjudication_record_refs=[adjudication_ref],
        conflict_record_refs=[f"conflict:{fixture_id}:false-split"],
        supersedes_identity_ref=split_left.id,
    )
    projection = _projection(
        fixture_id=fixture_id,
        suffix="merged-fact",
        identity_ref=merged.id,
        subject_key=merged.entity_key,
        source_refs=source_refs,
        supersedes_projection_record_ref=f"temporal-kg-projection:{fixture_id}:split-fact",
    )
    adjudication = _adjudication(
        fixture_id=fixture_id,
        suffix="false-split",
        conflict_type=TemporalKGConflictType.FALSE_SPLIT,
        decision_type=TemporalKGAdjudicationDecisionType.MERGE_IDENTITY,
        identity_refs=[split_left.id, split_right.id, merged.id],
        projection_refs=[projection.id],
        resulting_identity_refs=[merged.id],
        resulting_projection_refs=[projection.id],
        superseded_identity_refs=[split_left.id, split_right.id],
        superseded_projection_refs=[f"temporal-kg-projection:{fixture_id}:split-fact"],
        source_refs=source_refs,
        policy_refs=policy_refs,
    )
    report = _pass_report(
        fixture_id=fixture_id,
        identities=[split_left, split_right, merged],
        projections=[projection],
        adjudications=[adjudication],
        source_refs=source_refs,
        policy_refs=policy_refs,
        operator_status="temporal_kg_identity_superseded",
        conflict_refs=[f"conflict:{fixture_id}:false-split"],
        supersession_refs=[
            split_left.id,
            split_right.id,
            f"temporal-kg-projection:{fixture_id}:split-fact",
        ],
    )
    return TemporalKGRuntimeResult(
        [split_left, split_right, merged],
        [projection],
        [adjudication],
        report,
    )


def _needs_review_result(
    *,
    fixture_id: str,
    policy_refs: list[Ref],
) -> TemporalKGRuntimeResult:
    report = TemporalKGRuntimeReport(
        id=f"temporal-kg-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        policy_decision_refs=policy_refs,
        contract_only_refs=[f"contract-only:{fixture_id}:temporal-kg"],
        missing_runtime_refs=[
            f"missing-runtime:{fixture_id}:graph-store",
            f"missing-runtime:{fixture_id}:projection-worker",
        ],
        missing_ref_fields=["live_runtime_refs"],
        operator_status="temporal_kg_runtime_unavailable",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    return TemporalKGRuntimeResult([], [], [], report)


def _failure_result(
    *,
    fixture_id: str,
    failure: TemporalKGFailureType,
    report_field: str | None,
    missing_field: str,
    policy_refs: list[Ref],
) -> TemporalKGRuntimeResult:
    report_kwargs: dict[str, object] = {}
    if report_field is not None:
        report_kwargs[report_field] = [f"{report_field}:{fixture_id}"]
    report = TemporalKGRuntimeReport(
        id=f"temporal-kg-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        policy_decision_refs=policy_refs,
        failure_type=failure,
        failure_report_refs=[f"failure:{fixture_id}:{failure.value}"],
        missing_ref_fields=[missing_field],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
        **report_kwargs,
    )
    return TemporalKGRuntimeResult([], [], [], report)


def _identity(
    *,
    fixture_id: str,
    suffix: str,
    entity_key: str,
    label: str,
    source_refs: dict[str, list[Ref]],
    status: TemporalKGStatus = TemporalKGStatus.CURRENT,
    adjudication_record_refs: list[Ref] | None = None,
    conflict_record_refs: list[Ref] | None = None,
    supersedes_identity_ref: Ref | None = None,
    superseded_by_identity_ref: Ref | None = None,
    invalidation_ref: Ref | None = None,
) -> TemporalKGEntityIdentity:
    return TemporalKGEntityIdentity(
        id=f"temporal-kg-identity:{fixture_id}:{suffix}",
        run_ref=f"run:{fixture_id}",
        entity_key=entity_key,
        entity_type=TemporalKGEntityType.ORGANIZATION,
        canonical_label=label,
        alias_refs=[f"alias:{fixture_id}:{suffix}"],
        identity_evidence_refs=[f"identity-evidence:{fixture_id}:{suffix}"],
        source_verified_fact_refs=source_refs["verified_facts"],
        source_published_output_refs=source_refs["published_outputs"],
        source_event_refs=source_refs["events"],
        confidence=0.98,
        valid_from_ref=f"valid-time:{fixture_id}:from",
        valid_to_ref=None,
        transaction_time_ref=f"transaction-time:{fixture_id}:projected",
        status=status,
        conflict_record_refs=conflict_record_refs or [],
        adjudication_record_refs=adjudication_record_refs or [],
        supersedes_identity_ref=supersedes_identity_ref,
        superseded_by_identity_ref=superseded_by_identity_ref,
        invalidation_ref=invalidation_ref,
    )


def _projection(
    *,
    fixture_id: str,
    suffix: str,
    identity_ref: Ref,
    subject_key: str,
    source_refs: dict[str, list[Ref]],
    supersedes_projection_record_ref: Ref | None = None,
) -> TemporalKGProjectionRecord:
    return TemporalKGProjectionRecord(
        id=f"temporal-kg-projection:{fixture_id}:{suffix}",
        run_ref=f"run:{fixture_id}",
        projection_version="temporal-kg-v1",
        entity_identity_ref=identity_ref,
        subject_entity_key=subject_key,
        predicate="has_verified_attribute",
        object_value_ref=f"verified-value:{fixture_id}:{suffix}",
        object_entity_key=None,
        value_type="string",
        valid_from_ref=f"valid-time:{fixture_id}:from",
        observed_at_ref=f"transaction-time:{fixture_id}:observed",
        projected_at_ref=f"transaction-time:{fixture_id}:projected",
        source_verified_fact_refs=source_refs["verified_facts"],
        source_published_output_refs=source_refs["published_outputs"],
        source_event_refs=source_refs["events"],
        evidence_packet_refs=source_refs["evidence_packets"],
        supersedes_projection_record_ref=supersedes_projection_record_ref,
        status=TemporalKGStatus.CURRENT,
        projection_watermark_ref=source_refs["watermarks"][0],
    )


def _adjudication(
    *,
    fixture_id: str,
    suffix: str,
    conflict_type: TemporalKGConflictType,
    decision_type: TemporalKGAdjudicationDecisionType,
    identity_refs: list[Ref],
    projection_refs: list[Ref],
    resulting_identity_refs: list[Ref],
    source_refs: dict[str, list[Ref]],
    policy_refs: list[Ref],
    resulting_projection_refs: list[Ref] | None = None,
    invalidated_identity_refs: list[Ref] | None = None,
    superseded_identity_refs: list[Ref] | None = None,
    superseded_projection_refs: list[Ref] | None = None,
) -> TemporalKGIdentityAdjudicationRecord:
    return TemporalKGIdentityAdjudicationRecord(
        id=f"temporal-kg-adjudication:{fixture_id}:{suffix}",
        run_ref=f"run:{fixture_id}",
        conflict_type=conflict_type,
        decision_type=decision_type,
        identity_refs=identity_refs,
        projection_record_refs=projection_refs,
        conflict_record_refs=[f"conflict:{fixture_id}:{suffix}"],
        adjudication_authority_ref=f"review-authority:{fixture_id}:temporal-kg",
        evidence_input_refs=source_refs["evidence_packets"],
        source_event_refs=source_refs["events"],
        policy_decision_refs=policy_refs,
        resulting_identity_refs=resulting_identity_refs,
        resulting_projection_record_refs=resulting_projection_refs or [],
        invalidated_identity_refs=invalidated_identity_refs or [],
        superseded_identity_refs=superseded_identity_refs or [],
        superseded_projection_record_refs=superseded_projection_refs or [],
        command_record_refs=_command_refs(fixture_id),
        event_cursor_refs=_event_cursor_refs(fixture_id),
        outbox_refs=_outbox_refs(fixture_id),
        replay_bundle_ref=_replay_ref(fixture_id),
        result=CompletenessResult.PASS,
    )


def _pass_report(
    *,
    fixture_id: str,
    identities: list[TemporalKGEntityIdentity],
    projections: list[TemporalKGProjectionRecord],
    adjudications: list[TemporalKGIdentityAdjudicationRecord],
    source_refs: dict[str, list[Ref]],
    policy_refs: list[Ref],
    operator_status: str,
    conflict_refs: list[Ref] | None = None,
    supersession_refs: list[Ref] | None = None,
    invalidation_refs: list[Ref] | None = None,
) -> TemporalKGRuntimeReport:
    return TemporalKGRuntimeReport(
        id=f"temporal-kg-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        identity_refs=[identity.id for identity in identities],
        projection_record_refs=[record.id for record in projections],
        adjudication_record_refs=[record.id for record in adjudications],
        conflict_record_refs=conflict_refs or [],
        supersession_refs=supersession_refs or [],
        invalidation_refs=invalidation_refs or [],
        source_verified_fact_refs=source_refs["verified_facts"],
        source_published_output_refs=source_refs["published_outputs"],
        source_event_refs=source_refs["events"],
        evidence_packet_refs=source_refs["evidence_packets"],
        projection_watermark_refs=source_refs["watermarks"],
        policy_decision_refs=policy_refs,
        command_record_refs=_command_refs(fixture_id),
        event_cursor_refs=_event_cursor_refs(fixture_id),
        outbox_refs=_outbox_refs(fixture_id),
        replay_bundle_ref=_replay_ref(fixture_id),
        operator_status=operator_status,
        completion_result=CompletenessResult.PASS,
    )


def _source_refs(fixture_id: str) -> dict[str, list[Ref]]:
    return {
        "verified_facts": [f"verified-fact:{fixture_id}:accepted"],
        "published_outputs": [f"published-output:{fixture_id}:accepted"],
        "events": [
            f"event:{fixture_id}:verification_decided",
            f"event:{fixture_id}:output_published",
        ],
        "evidence_packets": [f"evidence-packet:{fixture_id}:accepted"],
        "watermarks": [f"projection-watermark:{fixture_id}:temporal-kg"],
    }


def _command_refs(fixture_id: str) -> list[Ref]:
    return [f"command:{fixture_id}:temporal-kg"]


def _event_cursor_refs(fixture_id: str) -> list[Ref]:
    return [f"event-cursor:{fixture_id}:temporal-kg"]


def _outbox_refs(fixture_id: str) -> list[Ref]:
    return [f"outbox:{fixture_id}:temporal-kg"]


def _replay_ref(fixture_id: str) -> Ref:
    return f"replay:{fixture_id}:temporal-kg"
