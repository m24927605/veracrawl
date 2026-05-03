"""Replay checks for expanded real-world quality corpus reports."""

from __future__ import annotations

from veracrawl.contracts.real_world_quality import RealWorldQualityCorpusReport


def missing_real_world_quality_replay_refs(
    report: RealWorldQualityCorpusReport,
) -> list[str]:
    required = {
        "real_world_benchmark_run_report_ref": report.real_world_benchmark_run_report_ref,
        "quality_observation_refs": report.quality_observation_refs,
        "pattern_coverage_refs": report.pattern_coverage_refs,
        "site_observation_refs": report.site_observation_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
        "replay_bundle_refs": report.replay_bundle_refs,
    }
    return [name for name, value in required.items() if not value]


def real_world_quality_replay_passes(report: RealWorldQualityCorpusReport) -> bool:
    return not missing_real_world_quality_replay_refs(report)
