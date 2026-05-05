from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.cli import crawler_optimization
from veracrawl.contracts.enums import CompletenessResult, CrawlerOptimizationFailureType


@pytest.mark.parametrize(
    ("fixture_id", "expected_result", "expected_failure"),
    [
        ("crawler-optimization-success", CompletenessResult.PASS, None),
        (
            "crawler-optimization-missing-frontier-score",
            CompletenessResult.FAIL,
            CrawlerOptimizationFailureType.MISSING_FRONTIER_SCORE,
        ),
        (
            "crawler-optimization-llm-as-evidence",
            CompletenessResult.FAIL,
            CrawlerOptimizationFailureType.LLM_OUTPUT_AS_EVIDENCE,
        ),
        (
            "crawler-optimization-unsafe-recovery",
            CompletenessResult.FAIL,
            CrawlerOptimizationFailureType.UNSAFE_RECOVERY_ACTION,
        ),
        (
            "crawler-optimization-quality-regression",
            CompletenessResult.FAIL,
            CrawlerOptimizationFailureType.RANKING_QUALITY_REGRESSION,
        ),
        (
            "crawler-optimization-missing-replay",
            CompletenessResult.FAIL,
            CrawlerOptimizationFailureType.MISSING_REPLAY_REFS,
        ),
    ],
)
def test_crawler_optimization_fixture_contracts(
    tmp_path: Path,
    fixture_id: str,
    expected_result: CompletenessResult,
    expected_failure: CrawlerOptimizationFailureType | None,
) -> None:
    result = crawler_optimization.run_fixture(
        Path("tests/fixtures") / fixture_id,
        profile="optimization",
        out=tmp_path / fixture_id,
    )

    assert result.report.completion_result == expected_result
    assert result.report.failure_type == expected_failure
    assert (tmp_path / fixture_id / "crawler_optimization_report.json").exists()
    assert (tmp_path / fixture_id / "summary.json").exists()
    if expected_result == CompletenessResult.PASS:
        assert result.report.cost_per_success <= 0.12
        assert result.report.ranking_ndcg >= 0.90
