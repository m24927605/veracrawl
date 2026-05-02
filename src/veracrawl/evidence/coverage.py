"""Evidence coverage builder for extraction candidates."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import (
    CompletenessResult,
    EvidencePacketStatus,
    PrivacyClassification,
)
from veracrawl.contracts.evidence import (
    EvidenceAnchor,
    EvidenceCoverageResult,
    EvidencePacket,
    EvidencePacketManifest,
)
from veracrawl.contracts.processing import ExtractionCandidate


@dataclass(frozen=True)
class EvidenceBuildResult:
    coverage: EvidenceCoverageResult
    packet: EvidencePacket
    anchors: list[EvidenceAnchor]
    manifest: EvidencePacketManifest


def build_field_evidence(
    *,
    fixture_id: str,
    candidate: ExtractionCandidate,
    normalized_document_ref: Ref,
    source_artifact_ref: Ref,
    policy_decision_refs: list[Ref],
    privacy_lifecycle_refs: list[Ref],
    replay_bundle_ref: Ref,
    missing_fields: list[str] | None = None,
    graph_signal_refs: list[Ref] | None = None,
    memory_refs: list[Ref] | None = None,
    agent_reasoning_refs: list[Ref] | None = None,
) -> EvidenceBuildResult:
    missing = set(missing_fields or [])
    required_fields = list(candidate.field_values)
    covered_fields = [
        field
        for field in required_fields
        if field not in missing and field in candidate.field_anchor_refs
    ]
    missing_field_refs = [
        field
        for field in required_fields
        if field not in covered_fields
    ]
    coverage = EvidenceCoverageResult(
        id=f"evidence-coverage:{fixture_id}",
        candidate_ref=candidate.id,
        required_field_refs=required_fields,
        covered_field_refs=covered_fields,
        missing_field_refs=missing_field_refs,
        completeness_result=(
            CompletenessResult.NEEDS_REVIEW
            if missing_field_refs
            else CompletenessResult.PASS
        ),
    )
    packet_ref = f"evidence:{fixture_id}"
    anchors = [
        EvidenceAnchor(
            id=f"evidence-anchor:{fixture_id}:{field}",
            evidence_packet_ref=packet_ref,
            candidate_ref=candidate.id,
            field_name=field,
            source_artifact_ref=source_artifact_ref,
            normalized_document_ref=normalized_document_ref,
            anchor_ref=candidate.field_anchor_refs[field],
            expected_text_hash=stable_hash(
                {"field": field, "value": candidate.field_values[field]}
            ),
            privacy_classification=PrivacyClassification.PUBLIC,
            policy_decision_refs=policy_decision_refs,
        )
        for field in covered_fields
    ]
    packet = EvidencePacket(
        id=packet_ref,
        candidate_ref=candidate.id,
        source_evidence_refs=[anchor.id for anchor in anchors],
        anchor_refs=[anchor.anchor_ref for anchor in anchors],
        coverage_result_ref=coverage.id,
        graph_signal_refs=graph_signal_refs or [],
        memory_refs=memory_refs or [],
        agent_reasoning_refs=agent_reasoning_refs or [],
        status=(
            EvidencePacketStatus.ACCEPTED_FOR_VERIFICATION
            if coverage.completeness_result == CompletenessResult.PASS
            else EvidencePacketStatus.BUILT
        ),
    )
    manifest_payload = {
        "id": f"evidence-manifest:{fixture_id}",
        "evidence_packet_ref": packet.id,
        "candidate_ref": candidate.id,
        "coverage_result_ref": coverage.id,
        "evidence_anchor_refs": [anchor.id for anchor in anchors],
        "source_artifact_refs": [source_artifact_ref],
        "normalized_document_refs": [normalized_document_ref],
        "privacy_lifecycle_refs": privacy_lifecycle_refs,
        "policy_decision_refs": policy_decision_refs,
        "replay_bundle_ref": replay_bundle_ref,
    }
    manifest = EvidencePacketManifest(
        **manifest_payload,
        manifest_hash=stable_hash(manifest_payload),
    )
    return EvidenceBuildResult(
        coverage=coverage,
        packet=packet,
        anchors=anchors,
        manifest=manifest,
    )
