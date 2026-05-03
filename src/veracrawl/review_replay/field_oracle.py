"""Field oracle replay validation helpers."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.field_oracle import FieldEvaluationRecord, FieldOracleBenchmarkReport


def missing_field_evaluation_replay_refs(evaluation: FieldEvaluationRecord) -> list[str]:
    required = {
        "source_anchor_refs": evaluation.source_anchor_refs,
        "artifact_refs": evaluation.artifact_refs,
        "content_hash_refs": evaluation.content_hash_refs,
        "normalized_value_ref": evaluation.normalized_value_ref,
        "evidence_packet_refs": evaluation.evidence_packet_refs,
        "verification_decision_refs": evaluation.verification_decision_refs,
        "policy_decision_refs": evaluation.policy_decision_refs,
        "command_record_refs": evaluation.command_record_refs,
        "event_cursor_refs": evaluation.event_cursor_refs,
        "outbox_refs": evaluation.outbox_refs,
        "replay_bundle_ref": evaluation.replay_bundle_ref,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + evaluation.missing_ref_fields))


def field_evaluation_replay_passes(evaluation: FieldEvaluationRecord) -> bool:
    return (
        evaluation.completion_result == CompletenessResult.PASS
        and evaluation.accepted
        and not missing_field_evaluation_replay_refs(evaluation)
    )


def missing_field_oracle_report_replay_refs(report: FieldOracleBenchmarkReport) -> list[str]:
    required = {
        "schema_refs": report.schema_refs,
        "expected_field_refs": report.expected_field_refs,
        "field_evaluation_refs": report.field_evaluation_refs,
        "source_anchor_refs": report.source_anchor_refs,
        "artifact_refs": report.artifact_refs,
        "content_hash_refs": report.content_hash_refs,
        "normalized_value_refs": report.normalized_value_refs,
        "evidence_packet_refs": report.evidence_packet_refs,
        "verification_decision_refs": report.verification_decision_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
        "replay_bundle_refs": report.replay_bundle_refs,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def field_oracle_report_replay_passes(report: FieldOracleBenchmarkReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_field_oracle_report_replay_refs(report)
    )
