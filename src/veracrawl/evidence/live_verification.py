"""Live evidence and verification runtime aggregate."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    LiveEvidenceVerificationFailureType,
)
from veracrawl.contracts.evidence import (
    LiveEvidenceVerificationRuntimeReport,
)
from veracrawl.contracts.policy import PolicyDecision
from veracrawl.contracts.processing import ExtractionCandidate
from veracrawl.contracts.verification import ReviewDecision, VerificationDecision
from veracrawl.evidence.coverage import EvidenceBuildResult, build_field_evidence
from veracrawl.policy.gates import decision_for
from veracrawl.verify.review import review_verification_decision, verify_evidence_packet


@dataclass(frozen=True)
class LiveEvidenceVerificationRuntimeResult:
    report: LiveEvidenceVerificationRuntimeReport
    evidence: EvidenceBuildResult | None = None
    verification: VerificationDecision | None = None
    review: ReviewDecision | None = None


_DIRECT_FAILURES: dict[str, tuple[LiveEvidenceVerificationFailureType, str]] = {
    "live-evidence-verification-stale-evidence": (
        LiveEvidenceVerificationFailureType.STALE_EVIDENCE,
        "freshness_refs",
    ),
    "live-evidence-verification-contradiction": (
        LiveEvidenceVerificationFailureType.CONTRADICTORY_EVIDENCE,
        "contradiction_record_refs",
    ),
    "live-evidence-verification-graph-only": (
        LiveEvidenceVerificationFailureType.GRAPH_ONLY_EVIDENCE,
        "source_anchor_refs",
    ),
    "live-evidence-verification-memory-only": (
        LiveEvidenceVerificationFailureType.MEMORY_ONLY_EVIDENCE,
        "source_anchor_refs",
    ),
    "live-evidence-verification-publication-bypass": (
        LiveEvidenceVerificationFailureType.PUBLICATION_GATE_BYPASS,
        "evidence_packet_refs",
    ),
    "live-evidence-verification-replay-mismatch": (
        LiveEvidenceVerificationFailureType.REPLAY_MISMATCH,
        "replay_bundle_ref",
    ),
}


def run_live_evidence_verification_runtime(
    *,
    fixture_id: str,
    scenario: str,
    schema_extraction_runtime_report_ref: Ref | None,
    candidate: ExtractionCandidate | None,
    normalized_document_ref: Ref,
    source_artifact_ref: Ref,
    source_anchor_refs: list[Ref],
) -> LiveEvidenceVerificationRuntimeResult:
    policy_refs = _policy_refs(fixture_id=fixture_id, candidate=candidate)
    privacy_refs = [f"privacy-lifecycle:{fixture_id}:public"]

    if schema_extraction_runtime_report_ref is None or candidate is None:
        return _failure_result(
            fixture_id=fixture_id,
            failure=LiveEvidenceVerificationFailureType.MISSING_SCHEMA_EXTRACTION,
            missing_field="schema_extraction_runtime_report_ref",
            schema_extraction_runtime_report_ref=schema_extraction_runtime_report_ref,
            candidate=candidate,
            normalized_document_refs=[],
            source_anchor_refs=[],
            policy_refs=policy_refs,
            privacy_refs=privacy_refs,
        )

    if scenario in _DIRECT_FAILURES:
        failure, missing_field = _DIRECT_FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing_field,
            schema_extraction_runtime_report_ref=schema_extraction_runtime_report_ref,
            candidate=candidate,
            normalized_document_refs=_normalized_refs(candidate, normalized_document_ref),
            source_anchor_refs=(
                []
                if failure
                in {
                    LiveEvidenceVerificationFailureType.GRAPH_ONLY_EVIDENCE,
                    LiveEvidenceVerificationFailureType.MEMORY_ONLY_EVIDENCE,
                }
                else source_anchor_refs
            ),
            policy_refs=policy_refs,
            privacy_refs=privacy_refs,
        )

    try:
        evidence = _build_evidence(
            fixture_id=fixture_id,
            candidate=candidate,
            normalized_document_ref=normalized_document_ref,
            source_artifact_ref=source_artifact_ref,
            privacy_refs=privacy_refs,
            missing_fields=(
                ["summary"]
                if scenario == "live-evidence-verification-missing-source-anchor"
                else None
            ),
        )
    except (ValueError, ValidationError) as exc:
        return _failure_result(
            fixture_id=fixture_id,
            failure=LiveEvidenceVerificationFailureType.EVIDENCE_BUILD_FAILED,
            missing_field="evidence_packet_refs",
            schema_extraction_runtime_report_ref=schema_extraction_runtime_report_ref,
            candidate=candidate,
            normalized_document_refs=_normalized_refs(candidate, normalized_document_ref),
            source_anchor_refs=source_anchor_refs,
            policy_refs=policy_refs,
            privacy_refs=privacy_refs,
            diagnostics=[str(exc)],
        )

    verification_policy = _policy(
        fixture_id=fixture_id,
        decision_type="runtime_verification",
        subject_ref=evidence.packet.id,
    )
    verification = verify_evidence_packet(
        fixture_id=fixture_id,
        candidate=candidate,
        coverage=evidence.coverage,
        evidence_packet=evidence.packet,
        verification_policy=verification_policy,
        conflict=scenario == "live-evidence-verification-conflict",
    )
    review_policy = _policy(
        fixture_id=fixture_id,
        decision_type="runtime_verification",
        subject_ref=f"review:{fixture_id}",
    )
    review = review_verification_decision(
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        verification=verification,
        evidence_packet=evidence.packet,
        review_policy=review_policy,
    )

    if scenario == "live-evidence-verification-missing-source-anchor":
        report = _report(
            fixture_id=fixture_id,
            completion_result=CompletenessResult.NEEDS_REVIEW,
            operator_status=LiveEvidenceVerificationFailureType.MISSING_SOURCE_ANCHOR.value,
            schema_extraction_runtime_report_ref=schema_extraction_runtime_report_ref,
            candidate=candidate,
            normalized_document_refs=_normalized_refs(candidate, normalized_document_ref),
            source_anchor_refs=source_anchor_refs,
            evidence=evidence,
            verification=verification,
            review=review,
            policy_refs=policy_refs + [verification_policy.id, review_policy.id],
            privacy_refs=privacy_refs,
            failure=LiveEvidenceVerificationFailureType.MISSING_SOURCE_ANCHOR,
            failure_refs=[f"failure:{fixture_id}:missing-source-anchor"],
            missing_fields=["source_anchor_refs"],
            diagnostics=["candidate field summary lacks source-backed evidence anchor"],
        )
        return LiveEvidenceVerificationRuntimeResult(
            report=report,
            evidence=evidence,
            verification=verification,
            review=review,
        )

    if scenario == "live-evidence-verification-conflict":
        report = _report(
            fixture_id=fixture_id,
            completion_result=CompletenessResult.NEEDS_REVIEW,
            operator_status=LiveEvidenceVerificationFailureType.VERIFICATION_CONFLICT.value,
            schema_extraction_runtime_report_ref=schema_extraction_runtime_report_ref,
            candidate=candidate,
            normalized_document_refs=_normalized_refs(candidate, normalized_document_ref),
            source_anchor_refs=source_anchor_refs,
            evidence=evidence,
            verification=verification,
            review=review,
            policy_refs=policy_refs + [verification_policy.id, review_policy.id],
            privacy_refs=privacy_refs,
            failure=LiveEvidenceVerificationFailureType.VERIFICATION_CONFLICT,
            failure_refs=[f"failure:{fixture_id}:verification-conflict"],
            diagnostics=["conflicting source evidence requires review before publication"],
        )
        return LiveEvidenceVerificationRuntimeResult(
            report=report,
            evidence=evidence,
            verification=verification,
            review=review,
        )

    report = _report(
        fixture_id=fixture_id,
        completion_result=CompletenessResult.PASS,
        operator_status="live_evidence_verification_completed",
        schema_extraction_runtime_report_ref=schema_extraction_runtime_report_ref,
        candidate=candidate,
        normalized_document_refs=_normalized_refs(candidate, normalized_document_ref),
        source_anchor_refs=source_anchor_refs,
        evidence=evidence,
        verification=verification,
        review=review,
        policy_refs=policy_refs + [verification_policy.id, review_policy.id],
        privacy_refs=privacy_refs,
    )
    return LiveEvidenceVerificationRuntimeResult(
        report=report,
        evidence=evidence,
        verification=verification,
        review=review,
    )


def _policy_refs(
    *,
    fixture_id: str,
    candidate: ExtractionCandidate | None,
) -> list[Ref]:
    subject_ref = candidate.id if candidate else f"candidate:{fixture_id}:missing"
    return [
        _policy(
            fixture_id=fixture_id,
            decision_type="runtime_evidence",
            subject_ref=subject_ref,
        ).id
    ]


def _policy(
    *,
    fixture_id: str,
    decision_type: str,
    subject_ref: str,
) -> PolicyDecision:
    return decision_for(
        decision_id=f"policy:{fixture_id}:{decision_type}:{subject_ref}",
        run_id=f"run:{fixture_id}",
        objective_id=f"objective:{fixture_id}",
        decision_type=decision_type,
        subject_ref=subject_ref,
        allow=True,
    )


def _build_evidence(
    *,
    fixture_id: str,
    candidate: ExtractionCandidate,
    normalized_document_ref: Ref,
    source_artifact_ref: Ref,
    privacy_refs: list[Ref],
    missing_fields: list[str] | None,
) -> EvidenceBuildResult:
    evidence_policy = _policy(
        fixture_id=fixture_id,
        decision_type="runtime_evidence",
        subject_ref=candidate.id,
    )
    return build_field_evidence(
        fixture_id=fixture_id,
        candidate=candidate,
        normalized_document_ref=normalized_document_ref,
        source_artifact_ref=source_artifact_ref,
        policy_decision_refs=[evidence_policy.id],
        privacy_lifecycle_refs=privacy_refs,
        replay_bundle_ref=f"replay-bundle:{fixture_id}:live-evidence",
        missing_fields=missing_fields,
        graph_signal_refs=[f"graph-signal:{fixture_id}:diagnostic"],
        memory_refs=[f"memory:{fixture_id}:diagnostic"],
        agent_reasoning_refs=[f"agent-reasoning:{fixture_id}:diagnostic"],
    )


def _failure_result(
    *,
    fixture_id: str,
    failure: LiveEvidenceVerificationFailureType,
    missing_field: str,
    schema_extraction_runtime_report_ref: Ref | None,
    candidate: ExtractionCandidate | None,
    normalized_document_refs: list[Ref],
    source_anchor_refs: list[Ref],
    policy_refs: list[Ref],
    privacy_refs: list[Ref],
    diagnostics: list[str] | None = None,
) -> LiveEvidenceVerificationRuntimeResult:
    report = _report(
        fixture_id=fixture_id,
        completion_result=CompletenessResult.FAIL,
        operator_status=failure.value,
        schema_extraction_runtime_report_ref=schema_extraction_runtime_report_ref,
        candidate=candidate,
        normalized_document_refs=normalized_document_refs,
        source_anchor_refs=source_anchor_refs,
        policy_refs=policy_refs,
        privacy_refs=privacy_refs,
        failure=failure,
        failure_refs=[f"failure:{fixture_id}:{failure.value}"],
        missing_fields=[missing_field],
        diagnostics=diagnostics or [f"live evidence verification failed: {failure.value}"],
    )
    return LiveEvidenceVerificationRuntimeResult(report=report)


def _report(
    *,
    fixture_id: str,
    completion_result: CompletenessResult,
    operator_status: str,
    schema_extraction_runtime_report_ref: Ref | None,
    candidate: ExtractionCandidate | None,
    normalized_document_refs: list[Ref],
    source_anchor_refs: list[Ref],
    policy_refs: list[Ref],
    privacy_refs: list[Ref],
    evidence: EvidenceBuildResult | None = None,
    verification: VerificationDecision | None = None,
    review: ReviewDecision | None = None,
    failure: LiveEvidenceVerificationFailureType | None = None,
    failure_refs: list[Ref] | None = None,
    missing_fields: list[str] | None = None,
    diagnostics: list[str] | None = None,
) -> LiveEvidenceVerificationRuntimeReport:
    replay_bundle_ref: Ref | None = f"replay-bundle:{fixture_id}:live-evidence"
    if failure == LiveEvidenceVerificationFailureType.REPLAY_MISMATCH:
        replay_bundle_ref = None
    conflict_refs = verification.conflict_record_refs if verification else []
    contradiction_refs = (
        [f"contradiction:{fixture_id}:source-evidence"]
        if failure == LiveEvidenceVerificationFailureType.CONTRADICTORY_EVIDENCE
        else []
    )
    graph_refs = (
        [f"graph-signal:{fixture_id}:diagnostic"]
        if failure == LiveEvidenceVerificationFailureType.GRAPH_ONLY_EVIDENCE
        else (evidence.packet.graph_signal_refs if evidence else [])
    )
    memory_refs = (
        [f"memory:{fixture_id}:diagnostic"]
        if failure == LiveEvidenceVerificationFailureType.MEMORY_ONLY_EVIDENCE
        else (evidence.packet.memory_refs if evidence else [])
    )
    agent_reasoning_refs = evidence.packet.agent_reasoning_refs if evidence else []
    publication_refs = (
        [f"published-output:{fixture_id}:forbidden"]
        if failure == LiveEvidenceVerificationFailureType.PUBLICATION_GATE_BYPASS
        else []
    )
    return LiveEvidenceVerificationRuntimeReport(
        id=f"live-evidence-verification-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        schema_extraction_runtime_report_ref=schema_extraction_runtime_report_ref,
        extraction_candidate_refs=_present([candidate.id]) if candidate else [],
        normalized_document_refs=normalized_document_refs,
        source_anchor_refs=source_anchor_refs,
        evidence_coverage_refs=_present([evidence.coverage.id]) if evidence else [],
        evidence_packet_refs=_present([evidence.packet.id]) if evidence else [],
        evidence_anchor_refs=[anchor.id for anchor in evidence.anchors] if evidence else [],
        evidence_manifest_refs=_present([evidence.manifest.id]) if evidence else [],
        verification_decision_refs=_present([verification.id]) if verification else [],
        review_decision_refs=_present([review.id]) if review else [],
        conflict_record_refs=conflict_refs,
        contradiction_record_refs=contradiction_refs,
        freshness_refs=(
            []
            if failure == LiveEvidenceVerificationFailureType.STALE_EVIDENCE
            else _present([verification.freshness_ref]) if verification else []
        ),
        graph_signal_refs=graph_refs,
        memory_refs=memory_refs,
        agent_reasoning_refs=agent_reasoning_refs,
        policy_decision_refs=_dedupe(policy_refs),
        privacy_lifecycle_refs=privacy_refs,
        command_record_refs=[f"durable-command:{fixture_id}:live-evidence"]
        if failure != LiveEvidenceVerificationFailureType.REPLAY_MISMATCH
        else [],
        event_cursor_refs=[f"event-cursor:{fixture_id}:live-evidence"]
        if failure != LiveEvidenceVerificationFailureType.REPLAY_MISMATCH
        else [],
        outbox_refs=[f"outbox:{fixture_id}:live-evidence"]
        if failure != LiveEvidenceVerificationFailureType.REPLAY_MISMATCH
        else [],
        replay_bundle_ref=replay_bundle_ref,
        publication_refs=publication_refs,
        failure_report_refs=failure_refs or [],
        missing_ref_fields=missing_fields or [],
        failure_type=failure,
        operator_status=operator_status,
        completion_result=completion_result,
        diagnostics=diagnostics or [],
    )


def _normalized_refs(
    candidate: ExtractionCandidate,
    normalized_document_ref: Ref,
) -> list[Ref]:
    return _dedupe([*candidate.normalized_document_refs, normalized_document_ref])


def _present(refs: list[Ref | None]) -> list[Ref]:
    return [ref for ref in refs if ref is not None]


def _dedupe(refs: list[Ref]) -> list[Ref]:
    return list(dict.fromkeys(refs))
