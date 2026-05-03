from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import CompletenessResult, SchemaExtractionFailureType
from veracrawl.contracts.processing import (
    SchemaExtractionFixtureManifest,
    SchemaExtractionRuntimeReport,
)
from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def _passing_report() -> SchemaExtractionRuntimeReport:
    return SchemaExtractionRuntimeReport(
        id="schema-extraction-runtime-report:test",
        fixture_id="schema-extraction-record-success",
        run_ref="run:test",
        live_normalization_runtime_report_ref="live-normalization-runtime-report:test",
        normalized_document_refs=["normalized:test"],
        source_anchor_refs=["text-anchor:test:1"],
        anchor_map_refs=["anchor-map:test"],
        extraction_strategy_refs=["extraction-strategy:test"],
        extraction_candidate_refs=["candidate:test"],
        candidate_field_anchor_refs=["text-anchor:test:1"],
        schema_refs=["schema:record-summary"],
        schema_validation_refs=["schema-validation:test:pass"],
        model_trace_refs=["model-trace:test:schema-extraction"],
        tool_trace_refs=["tool-trace:test:extract-fields"],
        confidence_refs=["confidence:test:candidate"],
        artifact_refs=["artifact:test:normalized", "anchor-map:test"],
        policy_decision_refs=["policy:test:schema-extraction"],
        command_record_refs=["durable-command:test:schema-extraction"],
        event_cursor_refs=["event-cursor:test:schema-extraction"],
        outbox_refs=["outbox:test:schema-extraction"],
        replay_bundle_ref="replay-bundle:test:schema-extraction",
        operator_status="schema_extraction_completed",
        completion_result=CompletenessResult.PASS,
    )


def test_schema_extraction_report_requires_trace_anchor_and_no_publication() -> None:
    report = _passing_report()
    assert report.completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        SchemaExtractionRuntimeReport.model_validate(
            report.model_dump(mode="json") | {"candidate_field_anchor_refs": []}
        )
    with pytest.raises(ValidationError):
        SchemaExtractionRuntimeReport.model_validate(
            report.model_dump(mode="json") | {"model_trace_refs": []}
        )
    with pytest.raises(ValidationError):
        SchemaExtractionRuntimeReport.model_validate(
            report.model_dump(mode="json")
            | {"publication_refs": ["published-output:test:forbidden"]}
        )


def test_schema_extraction_drift_needs_repair_refs() -> None:
    report = SchemaExtractionRuntimeReport(
        id="schema-extraction-runtime-report:drift",
        fixture_id="schema-extraction-drift-repair-required",
        run_ref="run:drift",
        schema_refs=["schema:record-summary"],
        policy_decision_refs=["policy:drift:schema-extraction"],
        candidate_rejection_refs=["candidate-rejection:drift:schema-drift"],
        drift_signal_refs=["drift-signal:drift:schema-fields"],
        repair_recommendation_refs=["repair-recommendation:drift:schema-refresh"],
        failure_report_refs=["failure:drift:schema-drift"],
        failure_type=SchemaExtractionFailureType.DRIFT_REPAIR_REQUIRED,
        operator_status=SchemaExtractionFailureType.DRIFT_REPAIR_REQUIRED.value,
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    with pytest.raises(ValidationError):
        SchemaExtractionRuntimeReport.model_validate(
            report.model_dump(mode="json") | {"repair_recommendation_refs": []}
        )


def test_schema_extraction_manifest_requires_exploratory_approval_and_failure_type() -> None:
    manifest = SchemaExtractionFixtureManifest(
        id="schema-extraction-record-success",
        scenario="schema-extraction-record-success",
        path="/static/basic",
        profile_refs=["target"],
        schema_ref="schema:record-summary",
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="schema_extraction_completed",
        required_ref_types=["candidate", "schema_validation", "model_trace"],
    )
    assert manifest.expected_completion_result == CompletenessResult.PASS
    with pytest.raises(ValidationError):
        SchemaExtractionFixtureManifest(
            id="schema-extraction-exploratory-success",
            scenario="schema-extraction-exploratory-success",
            path="/static/detail",
            profile_refs=["target"],
            schema_ref="schema:exploratory-summary",
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="schema_extraction_completed",
            required_ref_types=["candidate"],
        )
    with pytest.raises(ValidationError):
        SchemaExtractionFixtureManifest(
            id="schema-extraction-missing-normalization",
            scenario="schema-extraction-missing-normalization",
            path="/static/basic",
            profile_refs=["target"],
            schema_ref="schema:record-summary",
            expected_completion_result=CompletenessResult.FAIL,
            expected_operator_status=(
                SchemaExtractionFailureType.MISSING_LIVE_NORMALIZATION.value
            ),
            negative_case=True,
            required_ref_types=["typed_failure"],
        )


def test_schema_extraction_registry_is_materialized() -> None:
    assert "SchemaExtractionRuntimeReport" in FOUNDATION_CONTRACTS
    assert "SchemaExtractionFixtureManifest" in FOUNDATION_CONTRACTS
    assert "record_schema_extraction_runtime_report" in COMMAND_TYPES
    assert "record_schema_extraction_fixture_manifest" in COMMAND_TYPES
    assert "schema_extraction_runtime_reported" in EVENT_TYPES
    assert "schema-extraction-record-success" in FIXTURE_ORACLES
    area = TARGET_CONTRACT_AREAS["schema_extraction_candidate_runtime"]
    assert area.coverage_status == "materialized"
    assert "SchemaExtractionRuntimeReport" in area.materialized_contract_refs
    assert validate_registry().ok
