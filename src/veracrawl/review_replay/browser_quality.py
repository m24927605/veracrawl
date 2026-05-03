"""Browser quality replay validation helpers."""

from __future__ import annotations

from veracrawl.contracts.browser_quality import (
    BrowserQualityObservation,
    BrowserQualityReport,
)
from veracrawl.contracts.enums import CompletenessResult


def missing_browser_quality_observation_replay_refs(
    observation: BrowserQualityObservation,
) -> list[str]:
    required = {
        "browser_step_ref": observation.browser_step_ref,
        "dom_artifact_refs": observation.dom_artifact_refs,
        "screenshot_artifact_refs": observation.screenshot_artifact_refs,
        "network_trace_refs": observation.network_trace_refs,
        "console_log_refs": observation.console_log_refs,
        "timing_refs": observation.timing_refs,
        "rendered_content_hash_refs": observation.rendered_content_hash_refs,
        "source_anchor_refs": observation.source_anchor_refs,
        "policy_decision_refs": observation.policy_decision_refs,
        "command_record_refs": observation.command_record_refs,
        "event_cursor_refs": observation.event_cursor_refs,
        "outbox_refs": observation.outbox_refs,
        "replay_bundle_ref": observation.replay_bundle_ref,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + observation.missing_ref_fields))


def browser_quality_observation_replay_passes(
    observation: BrowserQualityObservation,
) -> bool:
    return observation.completion_result == CompletenessResult.PASS and not (
        missing_browser_quality_observation_replay_refs(observation)
    )


def missing_browser_quality_report_replay_refs(report: BrowserQualityReport) -> list[str]:
    required = {
        "observation_refs": report.observation_refs,
        "delta_record_refs": report.delta_record_refs,
        "dom_artifact_refs": report.dom_artifact_refs,
        "screenshot_artifact_refs": report.screenshot_artifact_refs,
        "network_trace_refs": report.network_trace_refs,
        "content_hash_refs": report.content_hash_refs,
        "source_anchor_refs": report.source_anchor_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
        "replay_bundle_refs": report.replay_bundle_refs,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def browser_quality_report_replay_passes(report: BrowserQualityReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_browser_quality_report_replay_refs(report)
    )
