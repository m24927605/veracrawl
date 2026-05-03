from __future__ import annotations

from pathlib import Path

from veracrawl.benchmarks.deep_crawl import run_deep_crawl_quality_corpus
from veracrawl.contracts.deep_crawl import DeepCrawlQualityManifest, DeepCrawlSiteSpec
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.review_replay.deep_crawl import (
    deep_crawl_observation_replay_passes,
    deep_crawl_report_replay_passes,
    deep_crawl_stop_replay_passes,
    frontier_decision_replay_passes,
    missing_deep_crawl_report_replay_refs,
    missing_frontier_decision_replay_refs,
)
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


def _manifest() -> DeepCrawlQualityManifest:
    sites = [
        DeepCrawlSiteSpec(
            id=f"deep-site-{index:02d}",
            allowed_origin=f"https://deepcrawl-fixture-{index:02d}.example",
            generated_page_count=10,
            rate_budget_ref=f"budget:deep-site-{index:02d}:rate",
            robots_policy_ref=f"policy:deep-site-{index:02d}:robots",
            private_network_policy_ref=f"policy:deep-site-{index:02d}:private",
        )
        for index in range(1, 6)
    ]
    return DeepCrawlQualityManifest(
        id="deep-crawl-quality-corpus",
        scenario="deep-crawl-quality-corpus",
        profile_refs=["quality"],
        site_specs=sites,
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="deep_crawl_completed",
        required_ref_types=["frontier_decision", "replay"],
    )


def test_deep_crawl_replay_passes_for_successful_runtime(tmp_path: Path) -> None:
    result = run_deep_crawl_quality_corpus(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )

    assert all(frontier_decision_replay_passes(item) for item in result.frontier_decisions)
    assert all(deep_crawl_observation_replay_passes(item) for item in result.page_observations)
    assert all(deep_crawl_stop_replay_passes(item) for item in result.stop_reasons)
    assert deep_crawl_report_replay_passes(result.report)


def test_deep_crawl_replay_detects_missing_decision_replay_ref(tmp_path: Path) -> None:
    result = run_deep_crawl_quality_corpus(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )
    broken = result.frontier_decisions[0].model_copy(
        update={"replay_bundle_ref": None},
    )

    assert "replay_bundle_ref" in missing_frontier_decision_replay_refs(broken)
    assert not frontier_decision_replay_passes(broken)


def test_deep_crawl_replay_detects_missing_report_refs(tmp_path: Path) -> None:
    result = run_deep_crawl_quality_corpus(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )
    broken = result.report.model_copy(update={"replay_bundle_refs": []})

    assert "replay_bundle_refs" in missing_deep_crawl_report_replay_refs(broken)
    assert not deep_crawl_report_replay_passes(broken)
