from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.deep_crawl import (
    DeepCrawlPageObservation,
    DeepCrawlPageSpec,
    DeepCrawlQualityManifest,
    DeepCrawlQualityReport,
    DeepCrawlSiteSpec,
    DeepCrawlStopReasonRecord,
    FrontierDecisionTrace,
)
from veracrawl.contracts.enums import (
    CompletenessResult,
    DeepCrawlFrontierAction,
    DeepCrawlPageType,
    DeepCrawlStopReason,
)


def _page(ai_prioritized: bool = False) -> DeepCrawlPageSpec:
    return DeepCrawlPageSpec(
        id="page:1",
        url="https://example.com/page-1",
        allowed_origin="https://example.com",
        canonical_url="https://example.com/page-1",
        page_type=DeepCrawlPageType.LISTING,
        depth=1,
        artifact_ref="artifact:page:1",
        content_hash_ref="hash:page:1",
        source_anchor_refs=["anchor:page:1"],
        ai_prioritized=ai_prioritized,
        model_call_refs=["model:frontier"] if ai_prioritized else [],
        agent_action_refs=["agent:frontier"] if ai_prioritized else [],
        tool_call_refs=["tool:frontier"] if ai_prioritized else [],
        context_bundle_refs=["context:frontier"] if ai_prioritized else [],
    )


def test_deep_crawl_manifest_supports_generated_quality_sites() -> None:
    manifest = DeepCrawlQualityManifest(
        id="deep-crawl-quality-corpus",
        scenario="deep-crawl-quality-corpus",
        profile_refs=["quality"],
        site_specs=[
            DeepCrawlSiteSpec(
                id="site:1",
                allowed_origin="https://example.com",
                generated_page_count=10,
                rate_budget_ref="budget:site:1",
                robots_policy_ref="policy:robots:site:1",
                private_network_policy_ref="policy:private:site:1",
            )
        ],
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="deep_crawl_completed",
        required_ref_types=["frontier_decision", "replay"],
    )

    assert manifest.site_specs[0].generated_page_count == 10


def test_ai_prioritized_page_requires_framework_neutral_trace_refs() -> None:
    with pytest.raises(ValidationError):
        DeepCrawlPageSpec(
            id="page:ai",
            url="https://example.com/ai",
            allowed_origin="https://example.com",
            canonical_url="https://example.com/ai",
            page_type=DeepCrawlPageType.LISTING,
            depth=1,
            artifact_ref="artifact:ai",
            content_hash_ref="hash:ai",
            source_anchor_refs=["anchor:ai"],
            ai_prioritized=True,
        )


def test_frontier_decision_requires_replay_and_ai_trace_refs_when_passing() -> None:
    page = _page(ai_prioritized=True)
    decision = FrontierDecisionTrace(
        id="frontier:1",
        site_ref="site:1",
        target_url=page.url,
        canonical_url=page.canonical_url,
        depth=1,
        action=DeepCrawlFrontierAction.PRIORITIZE,
        reason="frontier_policy_allowed",
        ai_prioritized=True,
        source_anchor_refs=page.source_anchor_refs,
        link_provenance_refs=["link:page:1"],
        graph_frontier_refs=["graph:frontier:1"],
        model_call_refs=page.model_call_refs,
        agent_action_refs=page.agent_action_refs,
        tool_call_refs=page.tool_call_refs,
        context_bundle_refs=page.context_bundle_refs,
        policy_decision_refs=["policy:allow"],
        command_record_refs=["command:frontier:1"],
        event_cursor_refs=["event-cursor:frontier:1"],
        outbox_refs=["outbox:frontier:1"],
        replay_bundle_ref="replay:frontier:1",
    )

    assert decision.ai_prioritized is True


def test_page_observation_requires_source_and_graph_refs() -> None:
    observation = DeepCrawlPageObservation(
        id="observation:1",
        site_ref="site:1",
        page_spec_ref="page:1",
        url="https://example.com/page-1",
        canonical_url="https://example.com/page-1",
        page_type=DeepCrawlPageType.DETAIL,
        depth=2,
        artifact_refs=["artifact:page:1"],
        content_hash_refs=["hash:page:1"],
        source_anchor_refs=["anchor:page:1"],
        link_provenance_refs=["link:page:1"],
        canonical_url_refs=["canonical:page:1"],
        graph_page_refs=["graph-page:page:1"],
        graph_frontier_refs=["graph-frontier:page:1"],
        policy_decision_refs=["policy:allow"],
        command_record_refs=["command:observation:1"],
        event_cursor_refs=["event-cursor:observation:1"],
        outbox_refs=["outbox:observation:1"],
        replay_bundle_ref="replay:observation:1",
    )

    assert observation.completion_result == CompletenessResult.PASS


def test_report_enforces_site_page_stop_and_replay_minimums() -> None:
    report = DeepCrawlQualityReport(
        id="report:deep",
        fixture_id="deep-crawl-quality-corpus",
        run_ref="run:deep",
        site_count=5,
        required_page_count=50,
        covered_page_count=50,
        observed_page_count=50,
        frontier_decision_count=70,
        stop_reason_count=5,
        observation_refs=["observation:1"],
        frontier_decision_refs=["frontier:1"],
        stop_reason_refs=["stop:1"],
        artifact_refs=["artifact:1"],
        content_hash_refs=["hash:1"],
        source_anchor_refs=["anchor:1"],
        link_provenance_refs=["link:1"],
        canonical_url_refs=["canonical:1"],
        duplicate_suppression_refs=["duplicate:1"],
        graph_refs=["graph:1"],
        policy_decision_refs=["policy:1"],
        command_record_refs=["command:1"],
        event_cursor_refs=["event-cursor:1"],
        outbox_refs=["outbox:1"],
        replay_bundle_refs=["replay:1"],
        operator_status="deep_crawl_completed",
        completion_result=CompletenessResult.PASS,
    )

    assert report.covered_page_count == 50


def test_stop_reason_requires_command_event_outbox_and_replay() -> None:
    stop = DeepCrawlStopReasonRecord(
        id="stop:1",
        site_ref="site:1",
        reason=DeepCrawlStopReason.FRONTIER_EXHAUSTED,
        frontier_remaining_count=0,
        page_count=10,
        max_depth=4,
        max_pages=12,
        policy_decision_refs=["policy:stop"],
        command_record_refs=["command:stop"],
        event_cursor_refs=["event-cursor:stop"],
        outbox_refs=["outbox:stop"],
        replay_bundle_ref="replay:stop",
    )

    assert stop.reason == DeepCrawlStopReason.FRONTIER_EXHAUSTED
