from __future__ import annotations

from veracrawl.cli.scale import ScaleFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_scale_success(report: ScaleFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "scale_hardening_completed"
    assert report.queue_topology_ref
    assert report.queue_item_refs
    assert report.shard_lease_refs
    assert report.backpressure_signal_refs
    assert report.autoscaling_decision_refs
    assert report.dead_letter_record_refs
    assert report.failure_record_refs
    assert report.recovery_action_refs
    assert report.dr_restore_report_refs
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs
    assert report.replay_bundle_ref


def assert_scale_negative(
    report: ScaleFixtureRunReport,
    *,
    operator_status: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_record_refs
    assert report.missing_ref_fields
