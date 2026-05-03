from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.cli.live_evidence import run_fixture
from veracrawl.contracts.enums import (
    CompletenessResult,
    LiveEvidenceVerificationFailureType,
)

LIVE_EVIDENCE_FIXTURES = [
    "live-evidence-verification-success",
    "live-evidence-verification-missing-schema-extraction",
    "live-evidence-verification-missing-source-anchor",
    "live-evidence-verification-stale-evidence",
    "live-evidence-verification-contradiction",
    "live-evidence-verification-graph-only",
    "live-evidence-verification-memory-only",
    "live-evidence-verification-conflict",
    "live-evidence-verification-publication-bypass",
    "live-evidence-verification-replay-mismatch",
]


@pytest.mark.parametrize("fixture_id", LIVE_EVIDENCE_FIXTURES)
def test_live_evidence_cli_fixture_contracts(tmp_path: Path, fixture_id: str) -> None:
    fixture_dir = Path("tests/fixtures") / fixture_id
    report = run_fixture(
        fixture_dir,
        profile="target",
        out=tmp_path / fixture_id,
    )

    assert report.fixture_id == fixture_id
    assert (tmp_path / fixture_id / "run_report.json").exists()
    if report.completion_result == CompletenessResult.PASS:
        assert report.schema_extraction_runtime_report_ref
        assert report.extraction_candidate_refs
        assert report.normalized_document_refs
        assert report.source_anchor_refs
        assert report.evidence_coverage_refs
        assert report.evidence_packet_refs
        assert report.evidence_anchor_refs
        assert report.evidence_manifest_refs
        assert report.verification_decision_refs
        assert report.review_decision_refs
        assert report.freshness_refs
        assert report.policy_decision_refs
        assert report.privacy_lifecycle_refs
        assert report.command_record_refs
        assert report.event_cursor_refs
        assert report.outbox_refs
        assert report.replay_bundle_ref
        assert report.publication_refs == []
    elif report.completion_result == CompletenessResult.NEEDS_REVIEW:
        assert report.failure_type is not None
        assert report.failure_report_refs
        if report.failure_type == LiveEvidenceVerificationFailureType.MISSING_SOURCE_ANCHOR:
            assert report.evidence_packet_refs
            assert report.evidence_anchor_refs
        if report.failure_type == LiveEvidenceVerificationFailureType.VERIFICATION_CONFLICT:
            assert report.conflict_record_refs
    else:
        assert report.failure_type is not None
        assert report.failure_report_refs
        assert report.missing_ref_fields
        if report.failure_type == LiveEvidenceVerificationFailureType.CONTRADICTORY_EVIDENCE:
            assert report.contradiction_record_refs
        if report.failure_type == LiveEvidenceVerificationFailureType.GRAPH_ONLY_EVIDENCE:
            assert report.graph_signal_refs
            assert not report.evidence_anchor_refs
        if report.failure_type == LiveEvidenceVerificationFailureType.MEMORY_ONLY_EVIDENCE:
            assert report.memory_refs
            assert not report.evidence_anchor_refs
        if report.failure_type == LiveEvidenceVerificationFailureType.PUBLICATION_GATE_BYPASS:
            assert report.publication_refs
        if report.failure_type == LiveEvidenceVerificationFailureType.REPLAY_MISMATCH:
            assert report.replay_bundle_ref is None
