"""Verification and review decisions for evidence publication fixtures."""

from __future__ import annotations

from veracrawl.contracts.enums import (
    CompletenessResult,
    PolicyDecisionValue,
    VerificationDecisionValue,
)
from veracrawl.contracts.evidence import EvidenceCoverageResult, EvidencePacket
from veracrawl.contracts.policy import PolicyDecision
from veracrawl.contracts.processing import ExtractionCandidate
from veracrawl.contracts.verification import ReviewDecision, VerificationDecision


def verify_evidence_packet(
    *,
    fixture_id: str,
    candidate: ExtractionCandidate,
    coverage: EvidenceCoverageResult,
    evidence_packet: EvidencePacket,
    verification_policy: PolicyDecision,
    conflict: bool = False,
) -> VerificationDecision:
    if conflict:
        decision = VerificationDecisionValue.CONFLICT
    elif coverage.completeness_result != CompletenessResult.PASS:
        decision = VerificationDecisionValue.REVIEW
    elif verification_policy.decision == PolicyDecisionValue.ALLOW:
        decision = VerificationDecisionValue.ACCEPT
    else:
        decision = VerificationDecisionValue.REJECT
    return VerificationDecision(
        id=f"verification:{fixture_id}",
        candidate_ref=candidate.id,
        evidence_packet_ref=evidence_packet.id,
        decision=decision,
        authority_ref="authority:evidence-publication-fixture",
        policy_decision_refs=[verification_policy.id],
        conflict_record_refs=(
            [f"conflict:{fixture_id}:evidence"]
            if decision == VerificationDecisionValue.CONFLICT
            else []
        ),
        freshness_ref=f"freshness:{fixture_id}:fixture",
    )


def review_verification_decision(
    *,
    fixture_id: str,
    run_ref: str,
    verification: VerificationDecision,
    evidence_packet: EvidencePacket,
    review_policy: PolicyDecision,
) -> ReviewDecision:
    decision = (
        VerificationDecisionValue.ACCEPT
        if verification.decision == VerificationDecisionValue.ACCEPT
        and review_policy.decision == PolicyDecisionValue.ALLOW
        else verification.decision
    )
    if review_policy.decision != PolicyDecisionValue.ALLOW:
        decision = VerificationDecisionValue.REJECT
    return ReviewDecision(
        id=f"review:{fixture_id}",
        run_ref=run_ref,
        verification_decision_ref=verification.id,
        evidence_packet_ref=evidence_packet.id,
        decision=decision,
        reviewer_ref="reviewer:evidence-publication-fixture",
        policy_decision_refs=[review_policy.id],
        rationale_refs=[f"review-rationale:{fixture_id}:{decision.value}"],
    )
