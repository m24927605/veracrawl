from __future__ import annotations

import ast
from pathlib import Path

import pytest

from veracrawl.contracts.enums import (
    CompletenessResult,
    ResultPublicationExportFailureType,
)
from veracrawl.evidence.live_verification import run_live_evidence_verification_runtime
from veracrawl.extract.schema_runtime import run_schema_extraction_runtime
from veracrawl.normalize.pipeline import NormalizationResult, normalize_html_document
from veracrawl.publish.result_runtime import (
    ResultPublicationExportRuntimeResult,
    run_result_publication_export_runtime,
)


def _normalization(fixture_id: str) -> NormalizationResult:
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


def _run_with_live_evidence(scenario: str) -> ResultPublicationExportRuntimeResult:
    normalization = _normalization(scenario)
    schema_result = run_schema_extraction_runtime(
        fixture_id=f"{scenario}-schema-extraction",
        scenario="schema-extraction-record-success",
        live_normalization_runtime_report_ref=f"live-normalization-runtime-report:{scenario}",
        normalization=normalization,
        schema_ref="schema:record-summary",
    )
    assert schema_result.candidate is not None
    live_evidence = run_live_evidence_verification_runtime(
        fixture_id=f"{scenario}-live-evidence",
        scenario="live-evidence-verification-success",
        schema_extraction_runtime_report_ref=schema_result.report.id,
        candidate=schema_result.candidate,
        normalized_document_ref=normalization.normalized_document.id,
        source_artifact_ref=normalization.normalized_document.raw_artifact_ref,
        source_anchor_refs=schema_result.report.source_anchor_refs,
    )
    assert live_evidence.evidence is not None
    assert live_evidence.verification is not None
    assert live_evidence.review is not None
    return run_result_publication_export_runtime(
        fixture_id=scenario,
        scenario=scenario,
        live_evidence_runtime_report_ref=live_evidence.report.id,
        candidate=schema_result.candidate,
        evidence=live_evidence.evidence,
        verification=live_evidence.verification,
        review=live_evidence.review,
    )


def test_result_publication_export_success_records_publication_api_export_refs() -> None:
    result = _run_with_live_evidence("result-publication-export-success")
    report = result.report

    assert report.completion_result == CompletenessResult.PASS
    assert result.publication is not None
    assert result.result_api_snapshot is not None
    assert report.live_evidence_runtime_report_ref
    assert report.published_output_refs
    assert report.output_manifest_refs
    assert report.result_api_snapshot_refs == [result.result_api_snapshot.id]
    assert report.export_target_spec_refs
    assert report.export_job_refs
    assert report.export_attempt_refs
    assert report.delivery_receipt_refs
    assert report.withdrawal_job_refs
    assert report.withdrawal_attempt_refs
    assert report.correction_record_refs
    assert report.destination_object_mapping_refs
    assert report.replay_bundle_ref


def test_result_publication_missing_live_evidence_is_typed() -> None:
    result = run_result_publication_export_runtime(
        fixture_id="result-publication-missing-live-evidence",
        scenario="result-publication-missing-live-evidence",
        live_evidence_runtime_report_ref=None,
        candidate=None,
        evidence=None,
        verification=None,
        review=None,
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == ResultPublicationExportFailureType.MISSING_LIVE_EVIDENCE
    assert result.report.failure_report_refs


@pytest.mark.parametrize(
    ("scenario", "failure", "completion"),
    [
        (
            "result-publication-policy-denied",
            ResultPublicationExportFailureType.PUBLICATION_POLICY_DENIED,
            CompletenessResult.FAIL,
        ),
        (
            "result-publication-verification-not-accepted",
            ResultPublicationExportFailureType.VERIFICATION_NOT_ACCEPTED,
            CompletenessResult.NEEDS_REVIEW,
        ),
        (
            "result-publication-missing-output-manifest",
            ResultPublicationExportFailureType.MISSING_OUTPUT_MANIFEST,
            CompletenessResult.FAIL,
        ),
        (
            "result-publication-export-missing-receipt",
            ResultPublicationExportFailureType.EXPORT_MISSING_RECEIPT,
            CompletenessResult.FAIL,
        ),
        (
            "result-publication-withdrawal-missing-propagation",
            ResultPublicationExportFailureType.WITHDRAWAL_MISSING_PROPAGATION,
            CompletenessResult.NEEDS_REVIEW,
        ),
        (
            "result-publication-correction-without-withdrawal",
            ResultPublicationExportFailureType.CORRECTION_WITHOUT_WITHDRAWAL,
            CompletenessResult.FAIL,
        ),
        (
            "result-publication-privacy-missing",
            ResultPublicationExportFailureType.PRIVACY_MISSING,
            CompletenessResult.FAIL,
        ),
        (
            "result-publication-direct-export-bypass",
            ResultPublicationExportFailureType.DIRECT_EXPORT_BYPASS,
            CompletenessResult.FAIL,
        ),
        (
            "result-publication-replay-mismatch",
            ResultPublicationExportFailureType.REPLAY_MISMATCH,
            CompletenessResult.FAIL,
        ),
    ],
)
def test_result_publication_negative_scenarios_are_typed(
    scenario: str,
    failure: ResultPublicationExportFailureType,
    completion: CompletenessResult,
) -> None:
    result = _run_with_live_evidence(scenario)
    report = result.report

    assert report.completion_result == completion
    assert report.failure_type == failure
    assert report.failure_report_refs
    if failure == ResultPublicationExportFailureType.EXPORT_MISSING_RECEIPT:
        assert report.export_job_refs
        assert not report.delivery_receipt_refs
    if failure == ResultPublicationExportFailureType.DIRECT_EXPORT_BYPASS:
        assert report.direct_export_bypass_refs
        assert not report.published_output_refs
    if failure == ResultPublicationExportFailureType.REPLAY_MISMATCH:
        assert report.replay_bundle_ref is None
        assert not report.command_record_refs


def test_result_publication_core_has_no_concrete_adapter_imports() -> None:
    tree = ast.parse(Path("src/veracrawl/publish/result_runtime.py").read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)

    forbidden_prefixes = ("veracrawl.adapters", "openai", "langchain", "langgraph")
    assert all(not name.startswith(forbidden_prefixes) for name in imports)
