"""Graph replay validation."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.graph import AdvancedGraphProjectionReport, GraphBuildReport


def missing_graph_replay_refs(report: GraphBuildReport) -> list[str]:
    required = {
        "manifest_ref": report.manifest_ref,
        "node_refs": report.node_refs,
        "edge_refs": report.edge_refs,
        "provenance_refs": report.provenance_refs,
        "watermark_ref": report.watermark_ref,
        "policy_decision_refs": report.policy_decision_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def graph_replay_passes(report: GraphBuildReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_graph_replay_refs(report)
    )


def missing_advanced_graph_replay_refs(report: AdvancedGraphProjectionReport) -> list[str]:
    required = {
        "projection_spec_ref": report.projection_spec_ref,
        "rebuild_job_ref": report.rebuild_job_ref,
        "delta_report_ref": report.delta_report_ref,
        "quality_report_ref": report.quality_report_ref,
        "signal_refs": report.signal_refs,
        "temporal_record_refs": report.temporal_record_refs,
        "watermark_ref": report.watermark_ref,
        "policy_decision_refs": report.policy_decision_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def advanced_graph_replay_passes(report: AdvancedGraphProjectionReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_advanced_graph_replay_refs(report)
    )
