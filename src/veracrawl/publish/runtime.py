"""Runtime publication owner service and safety gates."""

from __future__ import annotations

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import (
    CompletenessResult,
    OwnerService,
    PolicyDecisionValue,
    RuntimeCompletionGateType,
    RuntimeGateStatus,
    VerificationDecisionValue,
)
from veracrawl.contracts.evidence import EvidenceCoverageResult
from veracrawl.contracts.objective import CrawlRun, RuntimeCompletionGate
from veracrawl.contracts.policy import PolicyDecision
from veracrawl.contracts.processing import ExtractionCandidate
from veracrawl.contracts.publication import OutputManifest, PublishedOutput
from veracrawl.contracts.replay import ReplayValidationReport
from veracrawl.contracts.verification import VerificationDecision
from veracrawl.control.runtime import evaluate_completion_gate, require_owner


def publication_blockers(
    *,
    coverage: EvidenceCoverageResult,
    verification: VerificationDecision,
    publication_policy_decision: PolicyDecision,
    replay_report: ReplayValidationReport,
) -> list[str]:
    blockers: list[str] = []
    if coverage.completeness_result != CompletenessResult.PASS:
        blockers.append(coverage.id)
    if verification.decision != VerificationDecisionValue.ACCEPT:
        blockers.append(verification.id)
    if publication_policy_decision.decision != PolicyDecisionValue.ALLOW:
        blockers.append(publication_policy_decision.id)
    if replay_report.completeness_result != CompletenessResult.PASS:
        blockers.extend(replay_report.missing_ref_fields or [replay_report.id])
    return blockers


def publish_verified_output(
    *,
    run: CrawlRun,
    candidate: ExtractionCandidate,
    coverage: EvidenceCoverageResult,
    verification: VerificationDecision,
    publication_policy_decision: PolicyDecision,
    replay_report: ReplayValidationReport,
    replay_manifest_ref: Ref,
    output_manifest_id: str,
    owner: OwnerService = OwnerService.PUBLISH,
) -> tuple[PublishedOutput, OutputManifest, RuntimeCompletionGate]:
    require_owner(
        actual_owner=owner,
        expected_owner=OwnerService.PUBLISH,
        target_ref=f"published-output:{run.id}",
    )
    blockers = publication_blockers(
        coverage=coverage,
        verification=verification,
        publication_policy_decision=publication_policy_decision,
        replay_report=replay_report,
    )
    gate = evaluate_completion_gate(
        gate_id=f"gate:{run.id}:publication",
        run_ref=run.id,
        gate_type=RuntimeCompletionGateType.PUBLICATION,
        required_refs={
            "coverage_ref": coverage.id,
            "verification_decision_ref": verification.id,
            "publication_policy_decision_ref": publication_policy_decision.id,
            "replay_report_ref": replay_report.id,
        },
        forced_status=RuntimeGateStatus.FAIL if blockers else None,
        blocking_reason_refs=blockers,
    )
    if blockers:
        raise ValueError(f"publication blockers: {blockers}")

    published_id = f"published-output:{run.id}"
    manifest_payload = {
        "id": output_manifest_id,
        "published_output_ref": published_id,
        "output_version": "1",
        "schema_refs": [candidate.schema_ref],
        "field_evidence_refs": {
            field: candidate.field_anchor_refs[field] for field in candidate.field_values
        },
        "evidence_coverage_ref": coverage.id,
        "verification_decision_refs": [verification.id],
        "publication_policy_decision_refs": [publication_policy_decision.id],
        "artifact_refs": [],
        "privacy_lifecycle_refs": ["privacy-lifecycle:runtime-fixture"],
        "export_lifecycle_refs": [],
        "replay_bundle_ref": replay_manifest_ref,
    }
    manifest = OutputManifest(
        **manifest_payload,
        manifest_hash=stable_hash(manifest_payload),
    )
    published = PublishedOutput(
        id=published_id,
        run_ref=run.id,
        candidate_ref=candidate.id,
        verification_decision_ref=verification.id,
        output_manifest_ref=manifest.id,
    )
    return published, manifest, gate
