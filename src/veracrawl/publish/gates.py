"""Publication gates for evidence-backed outputs."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import (
    CompletenessResult,
    PolicyDecisionValue,
    PublicationFailureType,
    VerificationDecisionValue,
)
from veracrawl.contracts.evidence import (
    EvidenceCoverageResult,
    EvidencePacket,
    EvidencePacketManifest,
)
from veracrawl.contracts.policy import PolicyDecision
from veracrawl.contracts.processing import ExtractionCandidate
from veracrawl.contracts.publication import OutputManifest, PublicationReport, PublishedOutput
from veracrawl.contracts.verification import ReviewDecision, VerificationDecision


@dataclass(frozen=True)
class PublicationOutcome:
    report: PublicationReport
    published_output: PublishedOutput | None = None
    output_manifest: OutputManifest | None = None


def reject_direct_candidate_publication(
    *,
    fixture_id: str,
    run_ref: Ref,
    candidate: ExtractionCandidate,
) -> PublicationOutcome:
    failure = PublicationFailureType.CANDIDATE_DIRECT_PUBLICATION
    return PublicationOutcome(
        report=PublicationReport(
            id=f"publication-report:{fixture_id}",
            run_ref=run_ref,
            candidate_ref=candidate.id,
            failure_report_refs=[f"publication-failure:{fixture_id}:{failure.value}"],
            missing_ref_fields=[failure.value],
            operator_status=failure.value,
            completion_result=CompletenessResult.FAIL,
        )
    )


def publish_evidence_backed_output(
    *,
    fixture_id: str,
    run_ref: Ref,
    candidate: ExtractionCandidate,
    coverage: EvidenceCoverageResult,
    evidence_packet: EvidencePacket,
    evidence_manifest: EvidencePacketManifest,
    verification: VerificationDecision,
    review: ReviewDecision,
    publication_policy: PolicyDecision,
    privacy_lifecycle_refs: list[Ref],
    replay_bundle_ref: Ref | None,
    command_record_refs: list[Ref],
    event_cursor_refs: list[Ref],
    outbox_refs: list[Ref],
) -> PublicationOutcome:
    failures = _publication_failures(
        coverage=coverage,
        verification=verification,
        review=review,
        publication_policy=publication_policy,
        replay_bundle_ref=replay_bundle_ref,
        command_record_refs=command_record_refs,
        event_cursor_refs=event_cursor_refs,
        outbox_refs=outbox_refs,
    )
    if failures:
        primary = failures[0]
        completion = (
            CompletenessResult.NEEDS_REVIEW
            if primary == PublicationFailureType.MISSING_EVIDENCE_ANCHOR
            else CompletenessResult.FAIL
        )
        return PublicationOutcome(
            report=PublicationReport(
                id=f"publication-report:{fixture_id}",
                run_ref=run_ref,
                candidate_ref=candidate.id,
                evidence_packet_ref=evidence_packet.id,
                evidence_manifest_ref=evidence_manifest.id,
                coverage_result_ref=coverage.id,
                verification_decision_ref=verification.id,
                review_decision_ref=review.id,
                publication_policy_decision_refs=[publication_policy.id],
                privacy_lifecycle_refs=privacy_lifecycle_refs,
                replay_bundle_ref=replay_bundle_ref,
                failure_report_refs=[
                    f"publication-failure:{fixture_id}:{failure.value}"
                    for failure in failures
                ],
                missing_ref_fields=[failure.value for failure in failures],
                operator_status=primary.value,
                completion_result=completion,
            )
        )

    published_ref = f"published-output:{fixture_id}"
    output_manifest_ref = f"output-manifest:{fixture_id}"
    manifest_payload = {
        "id": output_manifest_ref,
        "published_output_ref": published_ref,
        "output_version": "1",
        "schema_refs": [candidate.schema_ref],
        "field_evidence_refs": {
            field: f"evidence-anchor:{fixture_id}:{field}"
            for field in candidate.field_values
        },
        "evidence_coverage_ref": coverage.id,
        "verification_decision_refs": [verification.id, review.id],
        "publication_policy_decision_refs": [publication_policy.id],
        "artifact_refs": [evidence_manifest.id],
        "privacy_lifecycle_refs": privacy_lifecycle_refs,
        "export_lifecycle_refs": [],
        "replay_bundle_ref": replay_bundle_ref,
    }
    output_manifest = OutputManifest(
        **manifest_payload,
        manifest_hash=stable_hash(manifest_payload),
    )
    published = PublishedOutput(
        id=published_ref,
        run_ref=run_ref,
        candidate_ref=candidate.id,
        verification_decision_ref=verification.id,
        output_manifest_ref=output_manifest.id,
    )
    report = PublicationReport(
        id=f"publication-report:{fixture_id}",
        run_ref=run_ref,
        candidate_ref=candidate.id,
        evidence_packet_ref=evidence_packet.id,
        evidence_manifest_ref=evidence_manifest.id,
        coverage_result_ref=coverage.id,
        verification_decision_ref=verification.id,
        review_decision_ref=review.id,
        publication_policy_decision_refs=[publication_policy.id],
        privacy_lifecycle_refs=privacy_lifecycle_refs,
        published_output_ref=published.id,
        output_manifest_ref=output_manifest.id,
        artifact_refs=[evidence_manifest.id],
        command_record_refs=command_record_refs,
        event_cursor_refs=event_cursor_refs,
        outbox_refs=outbox_refs,
        replay_bundle_ref=replay_bundle_ref,
        operator_status="publication_completed",
        completion_result=CompletenessResult.PASS,
    )
    return PublicationOutcome(
        report=report,
        published_output=published,
        output_manifest=output_manifest,
    )


def _publication_failures(
    *,
    coverage: EvidenceCoverageResult,
    verification: VerificationDecision,
    review: ReviewDecision,
    publication_policy: PolicyDecision,
    replay_bundle_ref: Ref | None,
    command_record_refs: list[Ref],
    event_cursor_refs: list[Ref],
    outbox_refs: list[Ref],
) -> list[PublicationFailureType]:
    failures: list[PublicationFailureType] = []
    if coverage.completeness_result != CompletenessResult.PASS:
        failures.append(PublicationFailureType.MISSING_EVIDENCE_ANCHOR)
    if verification.decision == VerificationDecisionValue.CONFLICT:
        failures.append(PublicationFailureType.VERIFICATION_CONFLICT)
    elif verification.decision != VerificationDecisionValue.ACCEPT:
        failures.append(PublicationFailureType.REVIEW_NOT_ACCEPTED)
    if review.decision != VerificationDecisionValue.ACCEPT:
        failures.append(PublicationFailureType.REVIEW_NOT_ACCEPTED)
    if publication_policy.decision != PolicyDecisionValue.ALLOW:
        failures.append(PublicationFailureType.PUBLICATION_POLICY_DENIED)
    if not (replay_bundle_ref and command_record_refs and event_cursor_refs and outbox_refs):
        failures.append(PublicationFailureType.REPLAY_GAP)
    return list(dict.fromkeys(failures))
