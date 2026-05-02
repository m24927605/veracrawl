"""Evidence/publication fixture runner CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    PublicationFailureType,
)
from veracrawl.contracts.evidence import EvidencePublicationFixtureManifest
from veracrawl.contracts.processing import ExtractionCandidate
from veracrawl.contracts.publication import PublicationReport
from veracrawl.evidence.coverage import EvidenceBuildResult, build_field_evidence
from veracrawl.policy.gates import decision_for
from veracrawl.publish.gates import (
    PublicationOutcome,
    publish_evidence_backed_output,
    reject_direct_candidate_publication,
)
from veracrawl.verify.review import review_verification_decision, verify_evidence_packet


class EvidenceFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    candidate_ref: Ref | None = None
    coverage_result_ref: Ref | None = None
    evidence_packet_ref: Ref | None = None
    evidence_manifest_ref: Ref | None = None
    evidence_anchor_refs: list[Ref] = Field(default_factory=list)
    verification_decision_ref: Ref | None = None
    review_decision_ref: Ref | None = None
    published_output_ref: Ref | None = None
    output_manifest_ref: Ref | None = None
    publication_report_ref: Ref | None = None
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    privacy_lifecycle_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _candidate(fixture_id: str) -> ExtractionCandidate:
    return ExtractionCandidate(
        id=f"candidate:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        schema_ref="schema:evidence-publication-record",
        normalized_document_refs=[f"normalized:{fixture_id}"],
        field_values={
            "title": f"{fixture_id} title",
            "summary": f"{fixture_id} summary",
            "link_count": 1,
        },
        field_anchor_refs={
            "title": f"text-anchor:{fixture_id}:title",
            "summary": f"text-anchor:{fixture_id}:summary",
            "link_count": f"text-anchor:{fixture_id}:summary",
        },
        confidence_refs=[f"confidence:{fixture_id}:candidate"],
        strategy_ref=f"extraction-strategy:{fixture_id}",
    )


def _policy(
    *,
    fixture_id: str,
    decision_type: str,
    subject_ref: str,
    allow: bool = True,
) -> Any:
    return decision_for(
        decision_id=f"policy:{fixture_id}:{decision_type}",
        run_id=f"run:{fixture_id}",
        objective_id=f"objective:{fixture_id}",
        decision_type=decision_type,
        subject_ref=subject_ref,
        allow=allow,
        reasons=[f"{decision_type} denied for fixture"],
    )


def _build_evidence(
    manifest: EvidencePublicationFixtureManifest,
    candidate: ExtractionCandidate,
) -> tuple[EvidenceBuildResult, list[Ref], list[Ref]]:
    evidence_policy = _policy(
        fixture_id=manifest.id,
        decision_type="runtime_evidence",
        subject_ref=candidate.id,
    )
    privacy_refs = [f"privacy-lifecycle:{manifest.id}:public"]
    missing_fields = (
        ["summary"] if manifest.scenario == "missing-anchor" else None
    )
    built = build_field_evidence(
        fixture_id=manifest.id,
        candidate=candidate,
        normalized_document_ref=f"normalized:{manifest.id}",
        source_artifact_ref=f"artifact:{manifest.id}:raw",
        policy_decision_refs=[evidence_policy.id],
        privacy_lifecycle_refs=privacy_refs,
        replay_bundle_ref=f"replay-bundle:{manifest.id}",
        missing_fields=missing_fields,
        graph_signal_refs=[f"graph-signal:{manifest.id}:diagnostic"],
        memory_refs=[f"memory:{manifest.id}:diagnostic"],
        agent_reasoning_refs=[f"agent-reasoning:{manifest.id}:diagnostic"],
    )
    return built, [evidence_policy.id], privacy_refs


def _run_publication(
    manifest: EvidencePublicationFixtureManifest,
    candidate: ExtractionCandidate,
    built: EvidenceBuildResult,
    privacy_refs: list[Ref],
) -> tuple[PublicationOutcome, list[Ref]]:
    verification_policy = _policy(
        fixture_id=manifest.id,
        decision_type="runtime_verification",
        subject_ref=built.packet.id,
    )
    review_policy = _policy(
        fixture_id=manifest.id,
        decision_type="runtime_verification",
        subject_ref=f"review:{manifest.id}",
    )
    publication_policy = _policy(
        fixture_id=manifest.id,
        decision_type="runtime_publication",
        subject_ref=candidate.id,
        allow=manifest.scenario != "policy-denied",
    )
    verification = verify_evidence_packet(
        fixture_id=manifest.id,
        candidate=candidate,
        coverage=built.coverage,
        evidence_packet=built.packet,
        verification_policy=verification_policy,
        conflict=manifest.scenario == "verification-conflict",
    )
    review = review_verification_decision(
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        verification=verification,
        evidence_packet=built.packet,
        review_policy=review_policy,
    )
    command_refs = (
        []
        if manifest.scenario == "replay-gap"
        else [f"command-record:{manifest.id}:publish"]
    )
    event_refs = (
        []
        if manifest.scenario == "replay-gap"
        else [f"event-cursor:{manifest.id}:publish"]
    )
    outbox_refs = [] if manifest.scenario == "replay-gap" else [f"outbox:{manifest.id}:publish"]
    replay_ref = None if manifest.scenario == "replay-gap" else f"replay-bundle:{manifest.id}"
    outcome = publish_evidence_backed_output(
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        candidate=candidate,
        coverage=built.coverage,
        evidence_packet=built.packet,
        evidence_manifest=built.manifest,
        verification=verification,
        review=review,
        publication_policy=publication_policy,
        privacy_lifecycle_refs=privacy_refs,
        replay_bundle_ref=replay_ref,
        command_record_refs=command_refs,
        event_cursor_refs=event_refs,
        outbox_refs=outbox_refs,
    )
    return outcome, [verification_policy.id, review_policy.id, publication_policy.id]


def _run_review_only(
    manifest: EvidencePublicationFixtureManifest,
    candidate: ExtractionCandidate,
    built: EvidenceBuildResult,
) -> tuple[str, str, list[Ref]]:
    verification_policy = _policy(
        fixture_id=manifest.id,
        decision_type="runtime_verification",
        subject_ref=built.packet.id,
    )
    review_policy = _policy(
        fixture_id=manifest.id,
        decision_type="runtime_verification",
        subject_ref=f"review:{manifest.id}",
    )
    verification = verify_evidence_packet(
        fixture_id=manifest.id,
        candidate=candidate,
        coverage=built.coverage,
        evidence_packet=built.packet,
        verification_policy=verification_policy,
    )
    review = review_verification_decision(
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        verification=verification,
        evidence_packet=built.packet,
        review_policy=review_policy,
    )
    return verification.id, review.id, [verification_policy.id, review_policy.id]


def _run_report(
    *,
    manifest: EvidencePublicationFixtureManifest,
    profile: str,
    candidate: ExtractionCandidate,
    built: EvidenceBuildResult | None = None,
    policy_refs: list[Ref] | None = None,
    privacy_refs: list[Ref] | None = None,
    publication_report: PublicationReport | None = None,
    verification_decision_ref: Ref | None = None,
    review_decision_ref: Ref | None = None,
    completion_result: CompletenessResult,
    operator_status: str,
) -> EvidenceFixtureRunReport:
    return EvidenceFixtureRunReport(
        id=f"evidence-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        run_ref=f"run:{manifest.id}",
        completion_result=completion_result,
        operator_status=operator_status,
        candidate_ref=candidate.id,
        coverage_result_ref=built.coverage.id if built else None,
        evidence_packet_ref=built.packet.id if built else None,
        evidence_manifest_ref=built.manifest.id if built else None,
        evidence_anchor_refs=[anchor.id for anchor in built.anchors] if built else [],
        verification_decision_ref=(
            publication_report.verification_decision_ref
            if publication_report
            else verification_decision_ref
        ),
        review_decision_ref=(
            publication_report.review_decision_ref if publication_report else review_decision_ref
        ),
        published_output_ref=(
            publication_report.published_output_ref if publication_report else None
        ),
        output_manifest_ref=publication_report.output_manifest_ref if publication_report else None,
        publication_report_ref=publication_report.id if publication_report else None,
        policy_decision_refs=policy_refs or [],
        privacy_lifecycle_refs=privacy_refs or [],
        command_record_refs=publication_report.command_record_refs if publication_report else [],
        event_cursor_refs=publication_report.event_cursor_refs if publication_report else [],
        outbox_refs=publication_report.outbox_refs if publication_report else [],
        replay_bundle_ref=publication_report.replay_bundle_ref if publication_report else None,
        failure_report_refs=publication_report.failure_report_refs if publication_report else [],
        missing_ref_fields=publication_report.missing_ref_fields if publication_report else [],
    )


def run_evidence_fixture(
    manifest: EvidencePublicationFixtureManifest,
    *,
    profile: str,
) -> EvidenceFixtureRunReport:
    candidate = _candidate(manifest.id)
    if manifest.scenario == "candidate-direct-publication":
        outcome = reject_direct_candidate_publication(
            fixture_id=manifest.id,
            run_ref=f"run:{manifest.id}",
            candidate=candidate,
        )
        return _run_report(
            manifest=manifest,
            profile=profile,
            candidate=candidate,
            publication_report=outcome.report,
            completion_result=outcome.report.completion_result,
            operator_status=outcome.report.operator_status,
        )

    built, evidence_policy_refs, privacy_refs = _build_evidence(manifest, candidate)
    if manifest.scenario == "field-coverage":
        return _run_report(
            manifest=manifest,
            profile=profile,
            candidate=candidate,
            built=built,
            policy_refs=evidence_policy_refs,
            privacy_refs=privacy_refs,
            completion_result=CompletenessResult.PASS,
            operator_status="evidence_coverage_completed",
        )
    if manifest.scenario == "missing-anchor":
        return _run_report(
            manifest=manifest,
            profile=profile,
            candidate=candidate,
            built=built,
            policy_refs=evidence_policy_refs,
            privacy_refs=privacy_refs,
            completion_result=CompletenessResult.NEEDS_REVIEW,
            operator_status=PublicationFailureType.MISSING_EVIDENCE_ANCHOR.value,
        )

    if manifest.scenario == "verification-review":
        verification_ref, review_ref, review_policy_refs = _run_review_only(
            manifest,
            candidate,
            built,
        )
        return _run_report(
            manifest=manifest,
            profile=profile,
            candidate=candidate,
            built=built,
            policy_refs=evidence_policy_refs + review_policy_refs,
            privacy_refs=privacy_refs,
            verification_decision_ref=verification_ref,
            review_decision_ref=review_ref,
            completion_result=CompletenessResult.PASS,
            operator_status="verification_review_completed",
        )
    outcome, downstream_policy_refs = _run_publication(
        manifest,
        candidate,
        built,
        privacy_refs,
    )
    report = outcome.report
    return _run_report(
        manifest=manifest,
        profile=profile,
        candidate=candidate,
        built=built,
        policy_refs=evidence_policy_refs + downstream_policy_refs,
        privacy_refs=privacy_refs,
        publication_report=report,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
    )


def run_fixture(fixture_dir: Path, *, profile: str, out: Path) -> EvidenceFixtureRunReport:
    manifest = EvidencePublicationFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_evidence_fixture(manifest, profile=profile)
    if report.completion_result.value != manifest.expected_completion_result:
        raise ValueError(
            f"fixture {manifest.id} completion mismatch: "
            f"{report.completion_result.value}"
        )
    if report.operator_status != manifest.expected_operator_status:
        raise ValueError(f"fixture {manifest.id} status mismatch: {report.operator_status}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-evidence")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        try:
            report = run_fixture(Path(args.fixture_dir), profile=args.profile, out=Path(args.out))
        except (OSError, ValueError) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
            return 1
        print(
            json.dumps(
                {
                    "ok": True,
                    "fixture_id": report.fixture_id,
                    "completion_result": report.completion_result.value,
                    "operator_status": report.operator_status,
                },
                sort_keys=True,
            )
        )
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
