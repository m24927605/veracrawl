from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.benchmarks.deep_crawl import run_deep_crawl_quality_corpus
from veracrawl.contracts.deep_crawl import DeepCrawlQualityManifest, DeepCrawlSiteSpec
from veracrawl.contracts.enums import (
    CompletenessResult,
    DeepCrawlFailureType,
    DeepCrawlFrontierAction,
)
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


def _site(index: int) -> DeepCrawlSiteSpec:
    return DeepCrawlSiteSpec(
        id=f"deep-site-{index:02d}",
        allowed_origin=f"https://deepcrawl-fixture-{index:02d}.example",
        generated_page_count=10,
        max_depth=4,
        max_pages=12,
        rate_budget_ref=f"budget:deep-site-{index:02d}:rate",
        robots_policy_ref=f"policy:deep-site-{index:02d}:robots",
        private_network_policy_ref=f"policy:deep-site-{index:02d}:private",
    )


def _manifest(
    *,
    scenario: str = "deep-crawl-quality-corpus",
    expected_result: CompletenessResult = CompletenessResult.PASS,
    expected_failure: DeepCrawlFailureType | None = None,
) -> DeepCrawlQualityManifest:
    return DeepCrawlQualityManifest(
        id=scenario,
        scenario=scenario,
        profile_refs=["quality"],
        site_specs=[_site(index) for index in range(1, 6)],
        expected_completion_result=expected_result,
        expected_operator_status=(
            expected_failure.value if expected_failure else "deep_crawl_completed"
        ),
        expected_failure_type=expected_failure,
        negative_case=expected_failure is not None,
        required_ref_types=["frontier_decision", "page_observation", "replay"],
    )


def test_deep_crawl_runtime_covers_five_sites_and_fifty_pages(tmp_path: Path) -> None:
    result = run_deep_crawl_quality_corpus(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )

    assert result.report.completion_result == CompletenessResult.PASS
    assert result.report.site_count == 5
    assert result.report.required_page_count == 50
    assert result.report.covered_page_count == 50
    assert result.report.stop_reason_count == 5
    assert result.report.duplicate_suppressed_count == 5
    assert result.report.off_origin_skip_count == 5
    assert result.report.robots_denied_skip_count == 5
    assert result.report.private_network_skip_count == 5
    assert result.report.ai_decision_refs
    assert all(item.replay_bundle_ref for item in result.frontier_decisions)
    assert all(item.command_record_refs for item in result.page_observations)


def test_deep_crawl_runtime_records_ai_prioritized_frontier_decisions(
    tmp_path: Path,
) -> None:
    result = run_deep_crawl_quality_corpus(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )
    prioritized = [
        item
        for item in result.frontier_decisions
        if item.action == DeepCrawlFrontierAction.PRIORITIZE
    ]

    assert len(prioritized) == 5
    assert all(item.model_call_refs for item in prioritized)
    assert all(item.agent_action_refs for item in prioritized)
    assert all(item.tool_call_refs for item in prioritized)
    assert all(item.context_bundle_refs for item in prioritized)


@pytest.mark.parametrize(
    ("scenario", "failure"),
    [
        ("deep-crawl-duplicate-loop", DeepCrawlFailureType.DUPLICATE_NOT_SUPPRESSED),
        ("deep-crawl-off-origin-pollution", DeepCrawlFailureType.FRONTIER_POLLUTION),
        ("deep-crawl-robots-denied", DeepCrawlFailureType.ROBOTS_DENIAL_BYPASSED),
        ("deep-crawl-budget-exhausted", DeepCrawlFailureType.BUDGET_EXHAUSTED),
        ("deep-crawl-infinite-pagination", DeepCrawlFailureType.INFINITE_PAGINATION),
        ("deep-crawl-replay-mismatch", DeepCrawlFailureType.REPLAY_MISMATCH),
    ],
)
def test_deep_crawl_runtime_maps_direct_negative_fixtures(
    tmp_path: Path,
    scenario: str,
    failure: DeepCrawlFailureType,
) -> None:
    result = run_deep_crawl_quality_corpus(
        manifest=_manifest(
            scenario=scenario,
            expected_result=CompletenessResult.FAIL,
            expected_failure=failure,
        ),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )

    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == failure
    assert result.report.operator_status == failure.value
