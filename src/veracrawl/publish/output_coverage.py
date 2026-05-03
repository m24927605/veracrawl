"""Deterministic target output type coverage gate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    OutputTypeCoverageFailureType,
    TargetOutputType,
)
from veracrawl.contracts.publication import (
    OutputTypeCoverageRecord,
    OutputTypePublicationGateReport,
)


@dataclass(frozen=True)
class OutputTypeCoverageRuntimeResult:
    coverage_records: list[OutputTypeCoverageRecord]
    report: OutputTypePublicationGateReport


_FAILURES: dict[
    str,
    tuple[OutputTypeCoverageFailureType, str | None, str, TargetOutputType | None],
] = {
    "output-type-coverage-missing-output-type": (
        OutputTypeCoverageFailureType.MISSING_OUTPUT_TYPE,
        None,
        "covered_output_types",
        TargetOutputType.FACT,
    ),
    "output-type-coverage-unsupported-output-type": (
        OutputTypeCoverageFailureType.UNSUPPORTED_OUTPUT_TYPE,
        "unsupported_output_type_refs",
        "unsupported_output_type",
        None,
    ),
    "output-type-coverage-derived-context-as-evidence": (
        OutputTypeCoverageFailureType.DERIVED_CONTEXT_AS_EVIDENCE,
        "derived_context_as_evidence_refs",
        "source_evidence_refs",
        None,
    ),
    "output-type-coverage-candidate-as-evidence": (
        OutputTypeCoverageFailureType.CANDIDATE_AS_EVIDENCE,
        "derived_context_as_evidence_refs",
        "source_evidence_refs",
        None,
    ),
    "output-type-coverage-graph-as-evidence": (
        OutputTypeCoverageFailureType.GRAPH_AS_EVIDENCE,
        "derived_context_as_evidence_refs",
        "source_evidence_refs",
        None,
    ),
    "output-type-coverage-memory-as-evidence": (
        OutputTypeCoverageFailureType.MEMORY_AS_EVIDENCE,
        "derived_context_as_evidence_refs",
        "source_evidence_refs",
        None,
    ),
    "output-type-coverage-agent-reasoning-as-evidence": (
        OutputTypeCoverageFailureType.AGENT_REASONING_AS_EVIDENCE,
        "derived_context_as_evidence_refs",
        "source_evidence_refs",
        None,
    ),
    "output-type-coverage-temporal-kg-as-evidence": (
        OutputTypeCoverageFailureType.TEMPORAL_KG_AS_EVIDENCE,
        "derived_context_as_evidence_refs",
        "source_evidence_refs",
        None,
    ),
    "output-type-coverage-missing-table-cell-evidence": (
        OutputTypeCoverageFailureType.MISSING_TABLE_CELL_EVIDENCE,
        "missing_type_specific_refs",
        "cell_anchor_refs",
        None,
    ),
    "output-type-coverage-missing-file-lifecycle": (
        OutputTypeCoverageFailureType.MISSING_FILE_LIFECYCLE,
        "missing_type_specific_refs",
        "file_artifact_hash_ref",
        None,
    ),
    "output-type-coverage-missing-dataset-item-evidence": (
        OutputTypeCoverageFailureType.MISSING_DATASET_ITEM_EVIDENCE,
        "missing_type_specific_refs",
        "dataset_item_evidence_refs",
        None,
    ),
    "output-type-coverage-missing-fact-verification": (
        OutputTypeCoverageFailureType.MISSING_FACT_VERIFICATION,
        "missing_type_specific_refs",
        "fact_verification_ref",
        None,
    ),
    "output-type-coverage-missing-replay": (
        OutputTypeCoverageFailureType.MISSING_REPLAY_REFS,
        "missing_replay_refs",
        "replay_bundle_ref",
        None,
    ),
}


def run_output_type_coverage_gate(
    *,
    fixture_id: str,
    scenario: str,
    policy_decision_refs: list[Ref] | None = None,
) -> OutputTypeCoverageRuntimeResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:output-coverage"]
    if scenario == "output-type-coverage-runtime-unavailable":
        return _needs_review_result(fixture_id=fixture_id, policy_refs=policy_refs)
    if scenario in _FAILURES:
        failure, report_field, missing_field, missing_output_type = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            report_field=report_field,
            missing_field=missing_field,
            policy_refs=policy_refs,
            missing_output_type=missing_output_type,
        )
    return _success_result(fixture_id=fixture_id, policy_refs=policy_refs)


def _success_result(
    *,
    fixture_id: str,
    policy_refs: list[Ref],
) -> OutputTypeCoverageRuntimeResult:
    records = [
        _coverage_record(fixture_id=fixture_id, output_type=output_type, policy_refs=policy_refs)
        for output_type in TargetOutputType
    ]
    report = OutputTypePublicationGateReport(
        id=f"output-type-coverage-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        coverage_record_refs=[record.id for record in records],
        covered_output_types=[record.output_type for record in records],
        policy_decision_refs=policy_refs,
        command_record_refs=_command_refs(fixture_id),
        event_cursor_refs=_event_cursor_refs(fixture_id),
        outbox_refs=_outbox_refs(fixture_id),
        replay_bundle_ref=_replay_ref(fixture_id),
        operator_status="output_type_coverage_completed",
        completion_result=CompletenessResult.PASS,
    )
    return OutputTypeCoverageRuntimeResult(records, report)


def _needs_review_result(
    *,
    fixture_id: str,
    policy_refs: list[Ref],
) -> OutputTypeCoverageRuntimeResult:
    report = OutputTypePublicationGateReport(
        id=f"output-type-coverage-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        policy_decision_refs=policy_refs,
        contract_only_refs=[f"contract-only:{fixture_id}:output-coverage"],
        missing_runtime_refs=[
            f"missing-runtime:{fixture_id}:publication-worker",
            f"missing-runtime:{fixture_id}:evidence-store",
        ],
        missing_ref_fields=["live_runtime_refs"],
        operator_status="output_type_coverage_runtime_unavailable",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    return OutputTypeCoverageRuntimeResult([], report)


def _failure_result(
    *,
    fixture_id: str,
    failure: OutputTypeCoverageFailureType,
    report_field: str | None,
    missing_field: str,
    policy_refs: list[Ref],
    missing_output_type: TargetOutputType | None,
) -> OutputTypeCoverageRuntimeResult:
    report_kwargs: dict[str, object] = {}
    if report_field is not None:
        report_kwargs[report_field] = [f"{report_field}:{fixture_id}"]
    missing_output_types = [missing_output_type] if missing_output_type is not None else []
    report = OutputTypePublicationGateReport(
        id=f"output-type-coverage-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        policy_decision_refs=policy_refs,
        missing_output_types=missing_output_types,
        failure_type=failure,
        failure_report_refs=[f"failure:{fixture_id}:{failure.value}"],
        missing_ref_fields=[missing_field],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
        **report_kwargs,
    )
    return OutputTypeCoverageRuntimeResult([], report)


def _coverage_record(
    *,
    fixture_id: str,
    output_type: TargetOutputType,
    policy_refs: list[Ref],
) -> OutputTypeCoverageRecord:
    suffix = output_type.value
    return OutputTypeCoverageRecord(
        id=f"output-type-coverage:{fixture_id}:{suffix}",
        run_ref=f"run:{fixture_id}",
        output_type=output_type,
        candidate_ref=f"candidate:{fixture_id}:{suffix}",
        published_output_ref=f"published-output:{fixture_id}:{suffix}",
        output_manifest_ref=f"output-manifest:{fixture_id}:{suffix}",
        evidence_packet_ref=f"evidence-packet:{fixture_id}:{suffix}",
        evidence_coverage_ref=f"evidence-coverage:{fixture_id}:{suffix}",
        verification_decision_ref=f"verification:{fixture_id}:{suffix}",
        publication_policy_refs=policy_refs,
        source_evidence_refs=[f"source-evidence:{fixture_id}:{suffix}"],
        field_evidence_refs=[f"field-evidence:{fixture_id}:{suffix}:required"],
        type_specific_refs=_type_specific_refs(fixture_id, output_type),
        privacy_lifecycle_refs=[f"privacy-lifecycle:{fixture_id}:{suffix}"],
        artifact_refs=[f"artifact:{fixture_id}:{suffix}"],
        diagnostic_graph_refs=[f"graph-diagnostic:{fixture_id}:{suffix}"],
        diagnostic_memory_refs=[f"memory-diagnostic:{fixture_id}:{suffix}"],
        diagnostic_agent_reasoning_refs=[f"agent-reasoning:{fixture_id}:{suffix}"],
        diagnostic_temporal_kg_refs=[f"temporal-kg-diagnostic:{fixture_id}:{suffix}"],
        command_record_refs=_command_refs(fixture_id),
        event_cursor_refs=_event_cursor_refs(fixture_id),
        outbox_refs=_outbox_refs(fixture_id),
        replay_bundle_ref=_replay_ref(fixture_id),
        result=CompletenessResult.PASS,
    )


def _type_specific_refs(fixture_id: str, output_type: TargetOutputType) -> dict[str, Ref]:
    prefix = f"type-specific:{fixture_id}:{output_type.value}"
    match output_type:
        case TargetOutputType.RECORD:
            names = ["record_schema_ref", "required_field_refs"]
        case TargetOutputType.TABLE:
            names = ["table_structure_ref", "row_refs", "cell_anchor_refs"]
        case TargetOutputType.DOCUMENT_METADATA:
            names = ["document_artifact_ref", "metadata_field_refs", "section_anchor_refs"]
        case TargetOutputType.DOCUMENT:
            names = ["document_artifact_ref", "normalized_document_ref", "section_anchor_refs"]
        case TargetOutputType.FILE:
            names = ["file_artifact_hash_ref", "mime_type_ref", "privacy_lifecycle_ref"]
        case TargetOutputType.DATASET:
            names = ["dataset_manifest_ref", "dataset_item_refs", "dataset_item_evidence_refs"]
        case TargetOutputType.FACT:
            names = ["fact_key_ref", "fact_verification_ref", "temporal_context_ref"]
    return {name: f"{prefix}:{name}" for name in names}


def _command_refs(fixture_id: str) -> list[Ref]:
    return [f"command:{fixture_id}:output-coverage"]


def _event_cursor_refs(fixture_id: str) -> list[Ref]:
    return [f"event-cursor:{fixture_id}:output-coverage"]


def _outbox_refs(fixture_id: str) -> list[Ref]:
    return [f"outbox:{fixture_id}:output-coverage"]


def _replay_ref(fixture_id: str) -> Ref:
    return f"replay:{fixture_id}:output-coverage"
