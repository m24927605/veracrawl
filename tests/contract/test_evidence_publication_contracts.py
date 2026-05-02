from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.common import stable_hash
from veracrawl.contracts.enums import CompletenessResult, VerificationDecisionValue
from veracrawl.contracts.evidence import EvidenceAnchor, EvidencePacketManifest
from veracrawl.contracts.publication import PublicationReport
from veracrawl.contracts.verification import ReviewDecision


def test_evidence_anchor_requires_hash_and_policy_refs() -> None:
    anchor = EvidenceAnchor(
        id="evidence-anchor:unit:title",
        evidence_packet_ref="evidence:unit",
        candidate_ref="candidate:unit",
        field_name="title",
        source_artifact_ref="artifact:unit:raw",
        normalized_document_ref="normalized:unit",
        anchor_ref="text-anchor:unit:title",
        expected_text_hash=stable_hash({"title": "value"}),
        policy_decision_refs=["policy:unit:evidence"],
    )
    assert anchor.field_name == "title"
    with pytest.raises(ValidationError):
        EvidenceAnchor(
            id="evidence-anchor:unit:bad",
            evidence_packet_ref="evidence:unit",
            candidate_ref="candidate:unit",
            field_name="title",
            source_artifact_ref="artifact:unit:raw",
            normalized_document_ref="normalized:unit",
            anchor_ref="text-anchor:unit:title",
            expected_text_hash="",
        )


def test_evidence_manifest_requires_privacy_policy_and_hash() -> None:
    manifest = EvidencePacketManifest(
        id="evidence-manifest:unit",
        evidence_packet_ref="evidence:unit",
        candidate_ref="candidate:unit",
        coverage_result_ref="evidence-coverage:unit",
        evidence_anchor_refs=["evidence-anchor:unit:title"],
        source_artifact_refs=["artifact:unit:raw"],
        normalized_document_refs=["normalized:unit"],
        privacy_lifecycle_refs=["privacy:unit"],
        policy_decision_refs=["policy:unit:evidence"],
        replay_bundle_ref="replay:unit",
        manifest_hash="hash",
    )
    assert manifest.replay_bundle_ref == "replay:unit"
    with pytest.raises(ValidationError):
        EvidencePacketManifest(
            id="evidence-manifest:bad",
            evidence_packet_ref="evidence:unit",
            candidate_ref="candidate:unit",
            coverage_result_ref="evidence-coverage:unit",
            evidence_anchor_refs=[],
            source_artifact_refs=["artifact:unit:raw"],
            normalized_document_refs=["normalized:unit"],
            privacy_lifecycle_refs=["privacy:unit"],
            policy_decision_refs=["policy:unit:evidence"],
            replay_bundle_ref="replay:unit",
            manifest_hash="hash",
        )


def test_review_decision_and_publication_report_gates() -> None:
    review = ReviewDecision(
        id="review:unit",
        run_ref="run:unit",
        verification_decision_ref="verification:unit",
        evidence_packet_ref="evidence:unit",
        decision=VerificationDecisionValue.ACCEPT,
        reviewer_ref="reviewer:unit",
        policy_decision_refs=["policy:unit:review"],
        rationale_refs=["rationale:unit"],
    )
    assert review.decision == VerificationDecisionValue.ACCEPT
    with pytest.raises(ValidationError):
        PublicationReport(
            id="publication-report:bad",
            run_ref="run:unit",
            candidate_ref="candidate:unit",
            operator_status="publication_completed",
            completion_result=CompletenessResult.PASS,
        )
