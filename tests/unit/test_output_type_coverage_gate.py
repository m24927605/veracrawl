from __future__ import annotations

from veracrawl.contracts.enums import (
    CompletenessResult,
    OutputTypeCoverageFailureType,
    TargetOutputType,
)
from veracrawl.publish.output_coverage import run_output_type_coverage_gate


def test_output_type_coverage_success_covers_all_target_types() -> None:
    result = run_output_type_coverage_gate(
        fixture_id="unit",
        scenario="output-type-coverage-success",
    )
    report = result.report
    assert report.completion_result == CompletenessResult.PASS
    assert set(report.covered_output_types) == set(TargetOutputType)
    assert len(result.coverage_records) == len(TargetOutputType)
    for record in result.coverage_records:
        assert record.source_evidence_refs
        assert record.evidence_packet_ref
        assert record.evidence_coverage_ref
        assert record.verification_decision_ref
        assert record.published_output_ref
        assert record.output_manifest_ref
        assert record.type_specific_refs
        assert record.privacy_lifecycle_refs
        assert record.command_record_refs
        assert record.event_cursor_refs
        assert record.outbox_refs
        assert record.replay_bundle_ref


def test_output_type_coverage_runtime_unavailable_needs_review() -> None:
    result = run_output_type_coverage_gate(
        fixture_id="unit-no-runtime",
        scenario="output-type-coverage-runtime-unavailable",
    )
    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.contract_only_refs
    assert result.report.missing_runtime_refs
    assert "live_runtime_refs" in result.report.missing_ref_fields


def test_output_type_coverage_negative_scenarios_fail() -> None:
    expectations = {
        "output-type-coverage-missing-output-type": (
            OutputTypeCoverageFailureType.MISSING_OUTPUT_TYPE
        ),
        "output-type-coverage-unsupported-output-type": (
            OutputTypeCoverageFailureType.UNSUPPORTED_OUTPUT_TYPE
        ),
        "output-type-coverage-derived-context-as-evidence": (
            OutputTypeCoverageFailureType.DERIVED_CONTEXT_AS_EVIDENCE
        ),
        "output-type-coverage-candidate-as-evidence": (
            OutputTypeCoverageFailureType.CANDIDATE_AS_EVIDENCE
        ),
        "output-type-coverage-graph-as-evidence": (
            OutputTypeCoverageFailureType.GRAPH_AS_EVIDENCE
        ),
        "output-type-coverage-memory-as-evidence": (
            OutputTypeCoverageFailureType.MEMORY_AS_EVIDENCE
        ),
        "output-type-coverage-agent-reasoning-as-evidence": (
            OutputTypeCoverageFailureType.AGENT_REASONING_AS_EVIDENCE
        ),
        "output-type-coverage-temporal-kg-as-evidence": (
            OutputTypeCoverageFailureType.TEMPORAL_KG_AS_EVIDENCE
        ),
        "output-type-coverage-missing-table-cell-evidence": (
            OutputTypeCoverageFailureType.MISSING_TABLE_CELL_EVIDENCE
        ),
        "output-type-coverage-missing-file-lifecycle": (
            OutputTypeCoverageFailureType.MISSING_FILE_LIFECYCLE
        ),
        "output-type-coverage-missing-dataset-item-evidence": (
            OutputTypeCoverageFailureType.MISSING_DATASET_ITEM_EVIDENCE
        ),
        "output-type-coverage-missing-fact-verification": (
            OutputTypeCoverageFailureType.MISSING_FACT_VERIFICATION
        ),
        "output-type-coverage-missing-replay": (
            OutputTypeCoverageFailureType.MISSING_REPLAY_REFS
        ),
    }
    for scenario, failure in expectations.items():
        result = run_output_type_coverage_gate(fixture_id=scenario, scenario=scenario)
        assert result.report.completion_result == CompletenessResult.FAIL
        assert result.report.failure_type == failure
        assert result.report.operator_status == failure.value
        assert result.report.missing_ref_fields
