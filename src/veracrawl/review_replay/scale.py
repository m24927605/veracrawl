"""Scale hardening replay validation."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.scale import ScaleRecoveryReport


def missing_scale_replay_refs(report: ScaleRecoveryReport) -> list[str]:
    required = {
        "queue_topology_ref": report.queue_topology_ref,
        "queue_item_refs": report.queue_item_refs,
        "shard_lease_refs": report.shard_lease_refs,
        "backpressure_signal_refs": report.backpressure_signal_refs,
        "autoscaling_decision_refs": report.autoscaling_decision_refs,
        "dead_letter_record_refs": report.dead_letter_record_refs,
        "failure_record_refs": report.failure_record_refs,
        "recovery_action_refs": report.recovery_action_refs,
        "dr_restore_report_refs": report.dr_restore_report_refs,
        "policy_decision_refs": report.policy_decision_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
        "replay_bundle_ref": report.replay_bundle_ref,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def scale_replay_passes(report: ScaleRecoveryReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_scale_replay_refs(report)
    )
