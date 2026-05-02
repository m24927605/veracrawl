"""Runtime evidence owner service."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult, EvidencePacketStatus, OwnerService
from veracrawl.contracts.evidence import EvidenceCoverageResult, EvidencePacket
from veracrawl.contracts.objective import CrawlRun
from veracrawl.contracts.processing import ExtractionCandidate
from veracrawl.control.runtime import require_owner


def build_evidence_packet(
    *,
    run: CrawlRun,
    candidate: ExtractionCandidate,
    missing_fields: list[str] | None = None,
    owner: OwnerService = OwnerService.EVIDENCE,
) -> tuple[EvidenceCoverageResult, EvidencePacket]:
    require_owner(
        actual_owner=owner,
        expected_owner=OwnerService.EVIDENCE,
        target_ref=f"evidence:{run.id}",
    )
    required_fields = list(candidate.field_values)
    missing = missing_fields or []
    covered = [field for field in required_fields if field not in missing]
    coverage = EvidenceCoverageResult(
        id=f"evidence-coverage:{run.id}",
        candidate_ref=candidate.id,
        required_field_refs=required_fields,
        covered_field_refs=covered,
        missing_field_refs=missing,
        completeness_result=CompletenessResult.NEEDS_REVIEW if missing else CompletenessResult.PASS,
    )
    packet = EvidencePacket(
        id=f"evidence:{run.id}",
        candidate_ref=candidate.id,
        source_evidence_refs=[candidate.field_anchor_refs[field] for field in covered],
        anchor_refs=list(candidate.field_anchor_refs.values()),
        coverage_result_ref=coverage.id,
        status=(
            EvidencePacketStatus.BUILT
            if missing
            else EvidencePacketStatus.ACCEPTED_FOR_VERIFICATION
        ),
    )
    return coverage, packet
