"""Replay checks for quality release gate records."""

from __future__ import annotations

from veracrawl.contracts.quality_release import (
    QualityReleaseGateRef,
    QualityReleaseReport,
    QualityReleaseStabilityRun,
)


def missing_quality_release_gate_replay_refs(gate_ref: QualityReleaseGateRef) -> list[str]:
    missing: list[str] = []
    for field_name in [
        "report_ref",
        "policy_decision_refs",
        "command_record_refs",
        "event_cursor_refs",
        "outbox_refs",
    ]:
        if not getattr(gate_ref, field_name):
            missing.append(field_name)
    if not gate_ref.replay_bundle_ref:
        missing.append("replay_bundle_ref")
    return missing


def quality_release_gate_replay_passes(gate_ref: QualityReleaseGateRef) -> bool:
    return not missing_quality_release_gate_replay_refs(gate_ref)


def missing_quality_release_stability_replay_refs(
    stability_run: QualityReleaseStabilityRun,
) -> list[str]:
    missing: list[str] = []
    for field_name in [
        "run_ref",
        "policy_decision_refs",
        "command_record_refs",
        "event_cursor_refs",
        "outbox_refs",
        "slo_metric_refs",
    ]:
        if not getattr(stability_run, field_name):
            missing.append(field_name)
    if not stability_run.replay_bundle_ref:
        missing.append("replay_bundle_ref")
    return missing


def quality_release_stability_replay_passes(
    stability_run: QualityReleaseStabilityRun,
) -> bool:
    return not missing_quality_release_stability_replay_refs(stability_run)


def missing_quality_release_report_replay_refs(report: QualityReleaseReport) -> list[str]:
    missing: list[str] = []
    for field_name in [
        "quality_gate_refs",
        "stability_run_refs",
        "gate_report_refs",
        "policy_decision_refs",
        "command_record_refs",
        "event_cursor_refs",
        "outbox_refs",
        "slo_metric_refs",
        "audit_report_refs",
        "release_decision_refs",
        "replay_bundle_refs",
    ]:
        if not getattr(report, field_name):
            missing.append(field_name)
    return missing


def quality_release_report_replay_passes(report: QualityReleaseReport) -> bool:
    return not missing_quality_release_report_replay_refs(report)
