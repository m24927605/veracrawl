"""Real-world benchmark replay validation."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.real_world_benchmark import RealWorldBenchmarkRunReport


def missing_real_world_benchmark_replay_refs(
    report: RealWorldBenchmarkRunReport,
) -> list[str]:
    required = {
        "site_observation_refs": report.site_observation_refs,
        "live_http_report_refs": report.live_http_report_refs,
        "network_response_refs": report.network_response_refs,
        "artifact_refs": report.artifact_refs,
        "content_hash_refs": report.content_hash_refs,
        "canonical_url_refs": report.canonical_url_refs,
        "policy_decision_refs": report.policy_decision_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
        "replay_bundle_refs": report.replay_bundle_refs,
        "observation_summary_refs": report.observation_summary_refs,
    }
    missing = [name for name, value in required.items() if not value]
    if report.completion_result == CompletenessResult.PASS:
        missing.extend(report.missing_ref_fields)
    return sorted(set(missing))


def real_world_benchmark_replay_passes(report: RealWorldBenchmarkRunReport) -> bool:
    return (
        report.completion_result == CompletenessResult.PASS
        and not missing_real_world_benchmark_replay_refs(report)
        and not report.failure_report_refs
        and report.failure_type is None
    )
