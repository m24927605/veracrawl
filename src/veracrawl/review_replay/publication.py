"""Publication replay validation."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.publication import PublicationReport


def missing_publication_replay_refs(report: PublicationReport) -> list[str]:
    required = {
        "evidence_packet_ref": report.evidence_packet_ref,
        "evidence_manifest_ref": report.evidence_manifest_ref,
        "coverage_result_ref": report.coverage_result_ref,
        "verification_decision_ref": report.verification_decision_ref,
        "review_decision_ref": report.review_decision_ref,
        "publication_policy_decision_refs": report.publication_policy_decision_refs,
        "privacy_lifecycle_refs": report.privacy_lifecycle_refs,
        "published_output_ref": report.published_output_ref,
        "output_manifest_ref": report.output_manifest_ref,
        "artifact_refs": report.artifact_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
        "replay_bundle_ref": report.replay_bundle_ref,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def publication_replay_passes(report: PublicationReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_publication_replay_refs(report)
    )
