from __future__ import annotations

import ast
from pathlib import Path

import pytest

from veracrawl.contracts.enums import (
    CompletenessResult,
    LiveEvidenceVerificationFailureType,
)
from veracrawl.evidence.live_verification import (
    LiveEvidenceVerificationRuntimeResult,
    run_live_evidence_verification_runtime,
)
from veracrawl.extract.schema_runtime import run_schema_extraction_runtime
from veracrawl.normalize.pipeline import NormalizationResult, normalize_html_document


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


def _run_scenario(scenario: str) -> LiveEvidenceVerificationRuntimeResult:
    normalization = _normalization(scenario)
    schema_result = run_schema_extraction_runtime(
        fixture_id=f"{scenario}-schema-extraction",
        scenario="schema-extraction-record-success",
        live_normalization_runtime_report_ref=f"live-normalization-runtime-report:{scenario}",
        normalization=normalization,
        schema_ref="schema:record-summary",
    )
    assert schema_result.candidate is not None
    return run_live_evidence_verification_runtime(
        fixture_id=scenario,
        scenario=scenario,
        schema_extraction_runtime_report_ref=schema_result.report.id,
        candidate=schema_result.candidate,
        normalized_document_ref=normalization.normalized_document.id,
        source_artifact_ref=normalization.normalized_document.raw_artifact_ref,
        source_anchor_refs=schema_result.report.source_anchor_refs,
    )


def test_live_evidence_success_records_source_backed_verification_and_replay() -> None:
    result = _run_scenario("live-evidence-verification-success")
    report = result.report

    assert report.completion_result == CompletenessResult.PASS
    assert result.evidence is not None
    assert result.verification is not None
    assert result.review is not None
    assert report.schema_extraction_runtime_report_ref
    assert report.extraction_candidate_refs
    assert report.evidence_packet_refs == [result.evidence.packet.id]
    assert report.evidence_anchor_refs
    assert report.verification_decision_refs == [result.verification.id]
    assert report.review_decision_refs == [result.review.id]
    assert report.freshness_refs
    assert report.publication_refs == []
    assert report.replay_bundle_ref


def test_live_evidence_missing_schema_extraction_is_typed() -> None:
    result = run_live_evidence_verification_runtime(
        fixture_id="live-evidence-verification-missing-schema-extraction",
        scenario="live-evidence-verification-missing-schema-extraction",
        schema_extraction_runtime_report_ref=None,
        candidate=None,
        normalized_document_ref="normalized:missing",
        source_artifact_ref="artifact:missing:raw",
        source_anchor_refs=[],
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert (
        result.report.failure_type
        == LiveEvidenceVerificationFailureType.MISSING_SCHEMA_EXTRACTION
    )
    assert result.report.failure_report_refs
    assert result.report.missing_ref_fields


@pytest.mark.parametrize(
    ("scenario", "failure", "completion"),
    [
        (
            "live-evidence-verification-missing-source-anchor",
            LiveEvidenceVerificationFailureType.MISSING_SOURCE_ANCHOR,
            CompletenessResult.NEEDS_REVIEW,
        ),
        (
            "live-evidence-verification-conflict",
            LiveEvidenceVerificationFailureType.VERIFICATION_CONFLICT,
            CompletenessResult.NEEDS_REVIEW,
        ),
        (
            "live-evidence-verification-stale-evidence",
            LiveEvidenceVerificationFailureType.STALE_EVIDENCE,
            CompletenessResult.FAIL,
        ),
        (
            "live-evidence-verification-contradiction",
            LiveEvidenceVerificationFailureType.CONTRADICTORY_EVIDENCE,
            CompletenessResult.FAIL,
        ),
        (
            "live-evidence-verification-graph-only",
            LiveEvidenceVerificationFailureType.GRAPH_ONLY_EVIDENCE,
            CompletenessResult.FAIL,
        ),
        (
            "live-evidence-verification-memory-only",
            LiveEvidenceVerificationFailureType.MEMORY_ONLY_EVIDENCE,
            CompletenessResult.FAIL,
        ),
        (
            "live-evidence-verification-publication-bypass",
            LiveEvidenceVerificationFailureType.PUBLICATION_GATE_BYPASS,
            CompletenessResult.FAIL,
        ),
        (
            "live-evidence-verification-replay-mismatch",
            LiveEvidenceVerificationFailureType.REPLAY_MISMATCH,
            CompletenessResult.FAIL,
        ),
    ],
)
def test_live_evidence_negative_scenarios_are_typed(
    scenario: str,
    failure: LiveEvidenceVerificationFailureType,
    completion: CompletenessResult,
) -> None:
    result = _run_scenario(scenario)
    report = result.report

    assert report.completion_result == completion
    assert report.failure_type == failure
    assert report.failure_report_refs
    if failure == LiveEvidenceVerificationFailureType.VERIFICATION_CONFLICT:
        assert report.conflict_record_refs
    if failure == LiveEvidenceVerificationFailureType.CONTRADICTORY_EVIDENCE:
        assert report.contradiction_record_refs
    if failure == LiveEvidenceVerificationFailureType.GRAPH_ONLY_EVIDENCE:
        assert report.graph_signal_refs
        assert not report.evidence_anchor_refs
    if failure == LiveEvidenceVerificationFailureType.MEMORY_ONLY_EVIDENCE:
        assert report.memory_refs
        assert not report.evidence_anchor_refs
    if failure == LiveEvidenceVerificationFailureType.PUBLICATION_GATE_BYPASS:
        assert report.publication_refs
    if failure == LiveEvidenceVerificationFailureType.REPLAY_MISMATCH:
        assert report.replay_bundle_ref is None


def test_live_evidence_core_has_no_concrete_adapter_imports() -> None:
    tree = ast.parse(
        Path("src/veracrawl/evidence/live_verification.py").read_text(encoding="utf-8")
    )
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)

    forbidden_prefixes = ("veracrawl.adapters", "openai", "langchain", "langgraph")
    assert all(not name.startswith(forbidden_prefixes) for name in imports)
