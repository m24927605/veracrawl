from __future__ import annotations

import ast
from pathlib import Path

import pytest

from veracrawl.contracts.enums import CompletenessResult, SchemaExtractionFailureType
from veracrawl.extract.schema_runtime import (
    SchemaExtractionRuntimeResult,
    run_schema_extraction_runtime,
)
from veracrawl.normalize.pipeline import NormalizationResult, normalize_html_document


def _normalization(
    fixture_id: str = "schema-extraction-record-success",
) -> NormalizationResult:
    return normalize_html_document(
        fixture_id=f"{fixture_id}-live-normalization",
        run_ref=f"run:{fixture_id}-live-normalization",
        source_adapter_result_ref=f"source-result:{fixture_id}",
        source_url="http://example.test/static/basic",
        raw_artifact_ref=f"artifact:{fixture_id}:raw",
        raw_html=(
            "<!doctype html><html><title>Vera</title><body><main><h1>Static fixture</h1>"
            "<a href='/static/detail'>Detail</a></main></body></html>"
        ),
        policy_decision_refs=[f"policy:{fixture_id}:live-normalization"],
    )


def _run_success(
    fixture_id: str = "schema-extraction-record-success",
    *,
    schema_ref: str = "schema:record-summary",
    approved_exploratory_schema: bool = False,
) -> SchemaExtractionRuntimeResult:
    return run_schema_extraction_runtime(
        fixture_id=fixture_id,
        scenario=fixture_id,
        live_normalization_runtime_report_ref=(
            f"live-normalization-runtime-report:{fixture_id}"
        ),
        normalization=_normalization(fixture_id),
        schema_ref=schema_ref,
        approved_exploratory_schema=approved_exploratory_schema,
    )


def test_schema_extraction_success_records_candidate_trace_and_replay_refs() -> None:
    result = _run_success()
    report = result.report

    assert report.completion_result == CompletenessResult.PASS
    assert result.strategy is not None
    assert result.candidate is not None
    assert report.live_normalization_runtime_report_ref
    assert report.normalized_document_refs
    assert report.source_anchor_refs
    assert report.extraction_strategy_refs == [result.strategy.id]
    assert report.extraction_candidate_refs == [result.candidate.id]
    assert report.candidate_field_anchor_refs
    assert report.schema_validation_refs == result.candidate.schema_validation_refs
    assert report.model_trace_refs == result.candidate.model_trace_refs
    assert report.tool_trace_refs == result.candidate.tool_trace_refs
    assert report.replay_bundle_ref
    assert report.publication_refs == []


def test_schema_extraction_approved_exploratory_schema_passes() -> None:
    result = _run_success(
        "schema-extraction-exploratory-success",
        schema_ref="schema:exploratory-summary",
        approved_exploratory_schema=True,
    )

    assert result.report.completion_result == CompletenessResult.PASS
    assert result.report.approved_exploratory_schema_refs


@pytest.mark.parametrize(
    ("scenario", "failure"),
    [
        (
            "schema-extraction-schema-validation-failed",
            SchemaExtractionFailureType.SCHEMA_VALIDATION_FAILED,
        ),
        (
            "schema-extraction-missing-field-anchor",
            SchemaExtractionFailureType.MISSING_FIELD_ANCHOR,
        ),
        (
            "schema-extraction-missing-model-tool-trace",
            SchemaExtractionFailureType.MISSING_MODEL_TOOL_TRACE,
        ),
        (
            "schema-extraction-candidate-direct-publication",
            SchemaExtractionFailureType.CANDIDATE_DIRECT_PUBLICATION,
        ),
        ("schema-extraction-replay-mismatch", SchemaExtractionFailureType.REPLAY_MISMATCH),
    ],
)
def test_schema_extraction_negative_scenarios_are_typed(
    scenario: str,
    failure: SchemaExtractionFailureType,
) -> None:
    result = run_schema_extraction_runtime(
        fixture_id=scenario,
        scenario=scenario,
        live_normalization_runtime_report_ref=f"live-normalization-runtime-report:{scenario}",
        normalization=_normalization(scenario),
        schema_ref="schema:record-summary",
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == failure
    assert result.report.failure_report_refs
    assert result.report.missing_ref_fields


def test_schema_extraction_missing_normalization_is_typed() -> None:
    result = run_schema_extraction_runtime(
        fixture_id="schema-extraction-missing-normalization",
        scenario="schema-extraction-missing-normalization",
        live_normalization_runtime_report_ref=None,
        normalization=None,
        schema_ref="schema:record-summary",
    )

    assert result.report.failure_type == SchemaExtractionFailureType.MISSING_LIVE_NORMALIZATION


def test_schema_extraction_drift_requires_review_not_pass() -> None:
    result = run_schema_extraction_runtime(
        fixture_id="schema-extraction-drift-repair-required",
        scenario="schema-extraction-drift-repair-required",
        live_normalization_runtime_report_ref=(
            "live-normalization-runtime-report:schema-extraction-drift-repair-required"
        ),
        normalization=_normalization("schema-extraction-drift-repair-required"),
        schema_ref="schema:record-summary",
    )

    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.failure_type == SchemaExtractionFailureType.DRIFT_REPAIR_REQUIRED
    assert result.report.candidate_rejection_refs
    assert result.report.drift_signal_refs
    assert result.report.repair_recommendation_refs


def test_schema_extraction_core_has_no_concrete_adapter_imports() -> None:
    tree = ast.parse(Path("src/veracrawl/extract/schema_runtime.py").read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)

    forbidden_prefixes = ("veracrawl.adapters", "openai", "langchain", "langgraph")
    assert all(not name.startswith(forbidden_prefixes) for name in imports)
