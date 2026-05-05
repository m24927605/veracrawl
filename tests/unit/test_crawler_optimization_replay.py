from __future__ import annotations

from pathlib import Path

from veracrawl.benchmarks.crawler_optimization import run_crawler_optimization_benchmark
from veracrawl.contracts.crawler_optimization import CrawlerOptimizationManifest
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.review_replay.crawler_optimization import (
    crawler_optimization_report_replay_passes,
    missing_crawler_optimization_report_replay_refs,
)
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


def _manifest() -> CrawlerOptimizationManifest:
    return CrawlerOptimizationManifest(
        id="crawler-optimization-success",
        scenario="crawler-optimization-success",
        profile_refs=["optimization"],
        objective_ref="objective:crawler-optimization:test",
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="crawler_optimization_completed",
        required_ref_types=["frontier_score", "dom_context", "replay"],
        algorithm_refs=["algorithm:focused-priority-queue"],
        architecture_refs=["architecture:crawler-intelligence-optimization:v1"],
    )


def test_crawler_optimization_replay_passes_for_successful_runtime(tmp_path: Path) -> None:
    result = run_crawler_optimization_benchmark(
        manifest=_manifest(),
        profile="optimization",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )

    assert crawler_optimization_report_replay_passes(result.report)


def test_crawler_optimization_replay_detects_missing_report_refs(tmp_path: Path) -> None:
    result = run_crawler_optimization_benchmark(
        manifest=_manifest(),
        profile="optimization",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )
    broken = result.report.model_copy(update={"replay_bundle_refs": []})

    assert "replay_bundle_refs" in missing_crawler_optimization_report_replay_refs(broken)
    assert not crawler_optimization_report_replay_passes(broken)
