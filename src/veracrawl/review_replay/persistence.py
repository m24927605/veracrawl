"""Persistence runtime replay validation."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.persistence import PersistenceRuntimeReport


def missing_persistence_replay_refs(report: PersistenceRuntimeReport) -> list[str]:
    required = {
        "adapter_ref": report.adapter_ref,
        "transaction_ref": report.transaction_ref,
        "command_record_refs": report.command_record_refs,
        "idempotency_record_refs": report.idempotency_record_refs,
        "event_cursor_ref": report.event_cursor_ref,
        "outbox_refs": report.outbox_refs,
        "artifact_refs": report.artifact_refs,
        "queue_operation_refs": report.queue_operation_refs,
        "lease_refs": report.lease_refs,
        "policy_decision_refs": report.policy_decision_refs,
        "replay_bundle_ref": report.replay_bundle_ref,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def persistence_replay_passes(report: PersistenceRuntimeReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_persistence_replay_refs(report)
    )
