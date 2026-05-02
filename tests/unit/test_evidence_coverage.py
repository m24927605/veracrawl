from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.processing import ExtractionCandidate
from veracrawl.evidence.coverage import build_field_evidence


def _candidate() -> ExtractionCandidate:
    return ExtractionCandidate(
        id="candidate:unit",
        run_ref="run:unit",
        schema_ref="schema:unit",
        normalized_document_refs=["normalized:unit"],
        field_values={"title": "Title", "summary": "Summary"},
        field_anchor_refs={
            "title": "text-anchor:unit:title",
            "summary": "text-anchor:unit:summary",
        },
        confidence_refs=["confidence:unit"],
        strategy_ref="strategy:unit",
    )


def test_build_field_evidence_covers_required_fields() -> None:
    result = build_field_evidence(
        fixture_id="unit",
        candidate=_candidate(),
        normalized_document_ref="normalized:unit",
        source_artifact_ref="artifact:unit:raw",
        policy_decision_refs=["policy:unit:evidence"],
        privacy_lifecycle_refs=["privacy:unit"],
        replay_bundle_ref="replay:unit",
        graph_signal_refs=["graph:diagnostic"],
        memory_refs=["memory:diagnostic"],
        agent_reasoning_refs=["agent:diagnostic"],
    )
    assert result.coverage.completeness_result == CompletenessResult.PASS
    assert {anchor.field_name for anchor in result.anchors} == {"title", "summary"}
    assert result.packet.source_evidence_refs
    assert result.packet.graph_signal_refs
    assert result.packet.memory_refs
    assert result.packet.agent_reasoning_refs


def test_missing_field_anchor_returns_needs_review() -> None:
    result = build_field_evidence(
        fixture_id="unit-missing",
        candidate=_candidate(),
        normalized_document_ref="normalized:unit",
        source_artifact_ref="artifact:unit:raw",
        policy_decision_refs=["policy:unit:evidence"],
        privacy_lifecycle_refs=["privacy:unit"],
        replay_bundle_ref="replay:unit",
        missing_fields=["summary"],
    )
    assert result.coverage.completeness_result == CompletenessResult.NEEDS_REVIEW
    assert result.coverage.missing_field_refs == ["summary"]
