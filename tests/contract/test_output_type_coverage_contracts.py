from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    OutputTypeCoverageFailureType,
    TargetOutputType,
)
from veracrawl.contracts.publication import (
    OutputTypeCoverageFixtureManifest,
    OutputTypeCoverageRecord,
    OutputTypePublicationGateReport,
)


def _record(output_type: TargetOutputType = TargetOutputType.RECORD) -> OutputTypeCoverageRecord:
    return OutputTypeCoverageRecord(
        id=f"output-type-coverage:{output_type.value}",
        run_ref="run:contract",
        output_type=output_type,
        candidate_ref=f"candidate:{output_type.value}",
        published_output_ref=f"published-output:{output_type.value}",
        output_manifest_ref=f"output-manifest:{output_type.value}",
        evidence_packet_ref=f"evidence-packet:{output_type.value}",
        evidence_coverage_ref=f"evidence-coverage:{output_type.value}",
        verification_decision_ref=f"verification:{output_type.value}",
        publication_policy_refs=["policy:contract"],
        source_evidence_refs=[f"source-evidence:{output_type.value}"],
        field_evidence_refs=[f"field-evidence:{output_type.value}"],
        type_specific_refs=_type_refs(output_type),
        privacy_lifecycle_refs=[f"privacy:{output_type.value}"],
        artifact_refs=[f"artifact:{output_type.value}"],
        command_record_refs=["command:contract"],
        event_cursor_refs=["event-cursor:contract"],
        outbox_refs=["outbox:contract"],
        replay_bundle_ref="replay:contract",
        result=CompletenessResult.PASS,
    )


def _type_refs(output_type: TargetOutputType) -> dict[str, str]:
    refs = {
        TargetOutputType.RECORD: ["record_schema_ref", "required_field_refs"],
        TargetOutputType.TABLE: ["table_structure_ref", "row_refs", "cell_anchor_refs"],
        TargetOutputType.DOCUMENT_METADATA: [
            "document_artifact_ref",
            "metadata_field_refs",
            "section_anchor_refs",
        ],
        TargetOutputType.DOCUMENT: [
            "document_artifact_ref",
            "normalized_document_ref",
            "section_anchor_refs",
        ],
        TargetOutputType.FILE: [
            "file_artifact_hash_ref",
            "mime_type_ref",
            "privacy_lifecycle_ref",
        ],
        TargetOutputType.DATASET: [
            "dataset_manifest_ref",
            "dataset_item_refs",
            "dataset_item_evidence_refs",
        ],
        TargetOutputType.FACT: ["fact_key_ref", "fact_verification_ref", "temporal_context_ref"],
    }
    return {name: f"type-ref:{output_type.value}:{name}" for name in refs[output_type]}


def test_output_type_record_rejects_missing_source_evidence() -> None:
    with pytest.raises(ValidationError):
        OutputTypeCoverageRecord(**(_record().model_dump() | {"source_evidence_refs": []}))


def test_output_type_record_rejects_missing_type_specific_refs() -> None:
    with pytest.raises(ValidationError):
        OutputTypeCoverageRecord(
            **(_record(TargetOutputType.TABLE).model_dump() | {"type_specific_refs": {}})
        )


def test_output_type_record_rejects_derived_context_as_evidence() -> None:
    with pytest.raises(ValidationError):
        OutputTypeCoverageRecord(
            **(
                _record().model_dump()
                | {"derived_context_as_evidence_refs": ["graph:diagnostic"]}
            )
        )


def test_output_type_report_requires_all_target_output_types() -> None:
    with pytest.raises(ValidationError):
        OutputTypePublicationGateReport(
            id="output-type-report:bad",
            run_ref="run:bad",
            coverage_record_refs=["output-type-coverage:record"],
            covered_output_types=[TargetOutputType.RECORD],
            policy_decision_refs=["policy:bad"],
            command_record_refs=["command:bad"],
            event_cursor_refs=["event-cursor:bad"],
            outbox_refs=["outbox:bad"],
            replay_bundle_ref="replay:bad",
            operator_status="output_type_coverage_completed",
            completion_result=CompletenessResult.PASS,
        )


def test_output_type_report_accepts_pass_and_typed_fail() -> None:
    report = OutputTypePublicationGateReport(
        id="output-type-report:ok",
        run_ref="run:ok",
        coverage_record_refs=[f"coverage:{output_type.value}" for output_type in TargetOutputType],
        covered_output_types=list(TargetOutputType),
        policy_decision_refs=["policy:ok"],
        command_record_refs=["command:ok"],
        event_cursor_refs=["event-cursor:ok"],
        outbox_refs=["outbox:ok"],
        replay_bundle_ref="replay:ok",
        operator_status="output_type_coverage_completed",
        completion_result=CompletenessResult.PASS,
    )
    assert report.completion_result == CompletenessResult.PASS

    failed = OutputTypePublicationGateReport(
        id="output-type-report:fail",
        run_ref="run:fail",
        failure_type=OutputTypeCoverageFailureType.DERIVED_CONTEXT_AS_EVIDENCE,
        failure_report_refs=["failure:fail"],
        derived_context_as_evidence_refs=["graph:fail"],
        missing_ref_fields=["source_evidence_refs"],
        operator_status=OutputTypeCoverageFailureType.DERIVED_CONTEXT_AS_EVIDENCE.value,
        completion_result=CompletenessResult.FAIL,
    )
    assert failed.failure_type == OutputTypeCoverageFailureType.DERIVED_CONTEXT_AS_EVIDENCE


def test_output_type_fixture_manifest_rejects_invalid_failure_expectations() -> None:
    with pytest.raises(ValidationError):
        OutputTypeCoverageFixtureManifest(
            id="output-type-bad",
            scenario="output-type-bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="bad",
            expected_failure_type=OutputTypeCoverageFailureType.MISSING_OUTPUT_TYPE,
            negative_case=True,
        )
    with pytest.raises(ValidationError):
        OutputTypeCoverageFixtureManifest(
            id="output-type-bad",
            scenario="output-type-bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.FAIL,
            expected_operator_status="bad",
            expected_failure_type=OutputTypeCoverageFailureType.MISSING_OUTPUT_TYPE,
            negative_case=False,
        )
