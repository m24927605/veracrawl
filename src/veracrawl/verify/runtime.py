"""Runtime verification owner service."""

from __future__ import annotations

from veracrawl.contracts.enums import OwnerService, PolicyDecisionValue, VerificationDecisionValue
from veracrawl.contracts.evidence import EvidencePacket
from veracrawl.contracts.objective import CrawlRun
from veracrawl.contracts.policy import PolicyDecision
from veracrawl.contracts.processing import ExtractionCandidate
from veracrawl.contracts.verification import VerificationDecision
from veracrawl.control.runtime import require_owner


def verify_candidate(
    *,
    run: CrawlRun,
    candidate: ExtractionCandidate,
    evidence: EvidencePacket,
    policy_decision: PolicyDecision,
    conflict: bool = False,
    owner: OwnerService = OwnerService.VERIFY,
) -> VerificationDecision:
    require_owner(
        actual_owner=owner,
        expected_owner=OwnerService.VERIFY,
        target_ref=f"verification:{run.id}",
    )
    if conflict:
        return VerificationDecision(
            id=f"verification:{run.id}",
            candidate_ref=candidate.id,
            evidence_packet_ref=evidence.id,
            decision=VerificationDecisionValue.CONFLICT,
            authority_ref="authority:runtime-fixture",
            policy_decision_refs=[policy_decision.id],
            conflict_record_refs=[f"conflict:{run.id}:field-price"],
            freshness_ref="freshness:fixture",
        )
    decision = (
        VerificationDecisionValue.ACCEPT
        if policy_decision.decision == PolicyDecisionValue.ALLOW
        else VerificationDecisionValue.REJECT
    )
    return VerificationDecision(
        id=f"verification:{run.id}",
        candidate_ref=candidate.id,
        evidence_packet_ref=evidence.id,
        decision=decision,
        authority_ref="authority:runtime-fixture",
        policy_decision_refs=[policy_decision.id],
        freshness_ref="freshness:fixture",
    )
