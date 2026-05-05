"""Crawler optimization replay helpers."""

from __future__ import annotations

from veracrawl.contracts.crawler_optimization import CrawlerOptimizationReport
from veracrawl.contracts.enums import CompletenessResult


def missing_crawler_optimization_report_replay_refs(
    report: CrawlerOptimizationReport,
) -> list[str]:
    required = {
        "frontier_score_refs": report.frontier_score_refs,
        "dom_context_refs": report.dom_context_refs,
        "extractor_plan_refs": report.extractor_plan_refs,
        "extractor_attempt_refs": report.extractor_attempt_refs,
        "field_confidence_refs": report.field_confidence_refs,
        "canonicalization_refs": report.canonicalization_refs,
        "fingerprint_refs": report.fingerprint_refs,
        "identity_decision_refs": report.identity_decision_refs,
        "duplicate_suppression_refs": report.duplicate_suppression_refs,
        "ranking_score_refs": report.ranking_score_refs,
        "ranked_output_set_refs": report.ranked_output_set_refs,
        "ranking_evaluation_refs": report.ranking_evaluation_refs,
        "metric_slice_refs": report.metric_slice_refs,
        "policy_decision_refs": report.policy_decision_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
        "replay_bundle_refs": report.replay_bundle_refs,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def crawler_optimization_report_replay_passes(report: CrawlerOptimizationReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_crawler_optimization_report_replay_refs(report)
    )
