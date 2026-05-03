from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.cli.schema_extraction import run_fixture
from veracrawl.contracts.enums import CompletenessResult

SCHEMA_EXTRACTION_FIXTURES = [
    "schema-extraction-record-success",
    "schema-extraction-exploratory-success",
    "schema-extraction-browser-success",
    "schema-extraction-drift-repair-required",
    "schema-extraction-missing-normalization",
    "schema-extraction-schema-validation-failed",
    "schema-extraction-missing-field-anchor",
    "schema-extraction-missing-model-tool-trace",
    "schema-extraction-candidate-direct-publication",
    "schema-extraction-replay-mismatch",
]


@pytest.mark.parametrize("fixture_id", SCHEMA_EXTRACTION_FIXTURES)
def test_schema_extraction_cli_fixture_contracts(tmp_path: Path, fixture_id: str) -> None:
    fixture_dir = Path("tests/fixtures") / fixture_id
    report = run_fixture(
        fixture_dir,
        profile="target",
        out=tmp_path / fixture_id,
    )

    assert report.fixture_id == fixture_id
    assert (tmp_path / fixture_id / "run_report.json").exists()
    if report.completion_result == CompletenessResult.PASS:
        assert report.live_normalization_runtime_report_ref
        assert report.normalized_document_refs
        assert report.source_anchor_refs
        assert report.anchor_map_refs
        assert report.extraction_strategy_refs
        assert report.extraction_candidate_refs
        assert report.candidate_field_anchor_refs
        assert report.schema_refs
        assert report.schema_validation_refs
        assert report.model_trace_refs
        assert report.tool_trace_refs
        assert report.confidence_refs
        assert report.policy_decision_refs
        assert report.command_record_refs
        assert report.event_cursor_refs
        assert report.outbox_refs
        assert report.replay_bundle_ref
        assert report.publication_refs == []
    elif report.completion_result == CompletenessResult.NEEDS_REVIEW:
        assert report.failure_type is not None
        assert report.candidate_rejection_refs
        assert report.drift_signal_refs
        assert report.repair_recommendation_refs
        assert report.publication_refs == []
    else:
        assert report.failure_type is not None
        assert report.failure_report_refs
        assert report.missing_ref_fields
        if fixture_id == "schema-extraction-candidate-direct-publication":
            assert report.publication_refs
