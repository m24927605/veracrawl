"""Deep crawl replay validation helpers."""

from __future__ import annotations

from veracrawl.contracts.deep_crawl import (
    DeepCrawlPageObservation,
    DeepCrawlQualityReport,
    DeepCrawlStopReasonRecord,
    FrontierDecisionTrace,
)
from veracrawl.contracts.enums import CompletenessResult, DeepCrawlFrontierAction


def missing_frontier_decision_replay_refs(decision: FrontierDecisionTrace) -> list[str]:
    required: dict[str, object] = {
        "policy_decision_refs": decision.policy_decision_refs,
        "command_record_refs": decision.command_record_refs,
        "event_cursor_refs": decision.event_cursor_refs,
        "outbox_refs": decision.outbox_refs,
        "replay_bundle_ref": decision.replay_bundle_ref,
    }
    if decision.action != DeepCrawlFrontierAction.STOP:
        required["link_provenance_refs"] = decision.link_provenance_refs
        required["graph_frontier_refs"] = decision.graph_frontier_refs
    if decision.ai_prioritized:
        required["model_call_refs"] = decision.model_call_refs
        required["agent_action_refs"] = decision.agent_action_refs
        required["tool_call_refs"] = decision.tool_call_refs
        required["context_bundle_refs"] = decision.context_bundle_refs
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + decision.missing_ref_fields))


def frontier_decision_replay_passes(decision: FrontierDecisionTrace) -> bool:
    return decision.completion_result == CompletenessResult.PASS and not (
        missing_frontier_decision_replay_refs(decision)
    )


def missing_deep_crawl_observation_replay_refs(
    observation: DeepCrawlPageObservation,
) -> list[str]:
    required = {
        "artifact_refs": observation.artifact_refs,
        "content_hash_refs": observation.content_hash_refs,
        "source_anchor_refs": observation.source_anchor_refs,
        "link_provenance_refs": observation.link_provenance_refs,
        "canonical_url_refs": observation.canonical_url_refs,
        "graph_page_refs": observation.graph_page_refs,
        "graph_frontier_refs": observation.graph_frontier_refs,
        "policy_decision_refs": observation.policy_decision_refs,
        "command_record_refs": observation.command_record_refs,
        "event_cursor_refs": observation.event_cursor_refs,
        "outbox_refs": observation.outbox_refs,
        "replay_bundle_ref": observation.replay_bundle_ref,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + observation.missing_ref_fields))


def deep_crawl_observation_replay_passes(observation: DeepCrawlPageObservation) -> bool:
    return observation.completion_result == CompletenessResult.PASS and not (
        missing_deep_crawl_observation_replay_refs(observation)
    )


def missing_deep_crawl_stop_replay_refs(stop_reason: DeepCrawlStopReasonRecord) -> list[str]:
    required = {
        "policy_decision_refs": stop_reason.policy_decision_refs,
        "command_record_refs": stop_reason.command_record_refs,
        "event_cursor_refs": stop_reason.event_cursor_refs,
        "outbox_refs": stop_reason.outbox_refs,
        "replay_bundle_ref": stop_reason.replay_bundle_ref,
    }
    return sorted(name for name, value in required.items() if not value)


def deep_crawl_stop_replay_passes(stop_reason: DeepCrawlStopReasonRecord) -> bool:
    return stop_reason.completion_result == CompletenessResult.PASS and not (
        missing_deep_crawl_stop_replay_refs(stop_reason)
    )


def missing_deep_crawl_report_replay_refs(report: DeepCrawlQualityReport) -> list[str]:
    required = {
        "observation_refs": report.observation_refs,
        "frontier_decision_refs": report.frontier_decision_refs,
        "stop_reason_refs": report.stop_reason_refs,
        "artifact_refs": report.artifact_refs,
        "content_hash_refs": report.content_hash_refs,
        "source_anchor_refs": report.source_anchor_refs,
        "link_provenance_refs": report.link_provenance_refs,
        "canonical_url_refs": report.canonical_url_refs,
        "duplicate_suppression_refs": report.duplicate_suppression_refs,
        "graph_refs": report.graph_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
        "replay_bundle_refs": report.replay_bundle_refs,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def deep_crawl_report_replay_passes(report: DeepCrawlQualityReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_deep_crawl_report_replay_refs(report)
    )
