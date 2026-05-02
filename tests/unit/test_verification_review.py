from __future__ import annotations

from veracrawl.cli.evidence import _candidate
from veracrawl.contracts.enums import VerificationDecisionValue
from veracrawl.evidence.coverage import build_field_evidence
from veracrawl.policy.gates import decision_for
from veracrawl.verify.review import review_verification_decision, verify_evidence_packet


def test_verification_and_review_accept_complete_evidence() -> None:
    candidate = _candidate("unit-review")
    built = build_field_evidence(
        fixture_id="unit-review",
        candidate=candidate,
        normalized_document_ref="normalized:unit-review",
        source_artifact_ref="artifact:unit-review:raw",
        policy_decision_refs=["policy:unit-review:evidence"],
        privacy_lifecycle_refs=["privacy:unit-review"],
        replay_bundle_ref="replay:unit-review",
    )
    policy = decision_for(
        decision_id="policy:unit-review:verification",
        run_id="run:unit-review",
        objective_id="objective:unit-review",
        decision_type="runtime_verification",
        subject_ref=built.packet.id,
        allow=True,
    )
    verification = verify_evidence_packet(
        fixture_id="unit-review",
        candidate=candidate,
        coverage=built.coverage,
        evidence_packet=built.packet,
        verification_policy=policy,
    )
    review = review_verification_decision(
        fixture_id="unit-review",
        run_ref="run:unit-review",
        verification=verification,
        evidence_packet=built.packet,
        review_policy=policy,
    )
    assert verification.decision == VerificationDecisionValue.ACCEPT
    assert review.decision == VerificationDecisionValue.ACCEPT


def test_verification_records_conflict() -> None:
    candidate = _candidate("unit-conflict")
    built = build_field_evidence(
        fixture_id="unit-conflict",
        candidate=candidate,
        normalized_document_ref="normalized:unit-conflict",
        source_artifact_ref="artifact:unit-conflict:raw",
        policy_decision_refs=["policy:unit-conflict:evidence"],
        privacy_lifecycle_refs=["privacy:unit-conflict"],
        replay_bundle_ref="replay:unit-conflict",
    )
    policy = decision_for(
        decision_id="policy:unit-conflict:verification",
        run_id="run:unit-conflict",
        objective_id="objective:unit-conflict",
        decision_type="runtime_verification",
        subject_ref=built.packet.id,
        allow=True,
    )
    verification = verify_evidence_packet(
        fixture_id="unit-conflict",
        candidate=candidate,
        coverage=built.coverage,
        evidence_packet=built.packet,
        verification_policy=policy,
        conflict=True,
    )
    assert verification.decision == VerificationDecisionValue.CONFLICT
    assert verification.conflict_record_refs
