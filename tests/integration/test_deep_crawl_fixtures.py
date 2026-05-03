from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.cli import deep_crawl
from veracrawl.contracts.enums import CompletenessResult, DeepCrawlFailureType


@pytest.mark.parametrize(
    ("fixture_id", "expected_result", "expected_failure"),
    [
        ("deep-crawl-quality-corpus", CompletenessResult.PASS, None),
        (
            "deep-crawl-duplicate-loop",
            CompletenessResult.FAIL,
            DeepCrawlFailureType.DUPLICATE_NOT_SUPPRESSED,
        ),
        (
            "deep-crawl-off-origin-pollution",
            CompletenessResult.FAIL,
            DeepCrawlFailureType.FRONTIER_POLLUTION,
        ),
        (
            "deep-crawl-robots-denied",
            CompletenessResult.FAIL,
            DeepCrawlFailureType.ROBOTS_DENIAL_BYPASSED,
        ),
        (
            "deep-crawl-budget-exhausted",
            CompletenessResult.FAIL,
            DeepCrawlFailureType.BUDGET_EXHAUSTED,
        ),
        (
            "deep-crawl-infinite-pagination",
            CompletenessResult.FAIL,
            DeepCrawlFailureType.INFINITE_PAGINATION,
        ),
        (
            "deep-crawl-replay-mismatch",
            CompletenessResult.FAIL,
            DeepCrawlFailureType.REPLAY_MISMATCH,
        ),
    ],
)
def test_deep_crawl_fixture_contracts(
    tmp_path: Path,
    fixture_id: str,
    expected_result: CompletenessResult,
    expected_failure: DeepCrawlFailureType | None,
) -> None:
    result = deep_crawl.run_fixture(
        Path("tests/fixtures") / fixture_id,
        profile="quality",
        out=tmp_path / fixture_id,
    )

    assert result.report.completion_result == expected_result
    assert result.report.failure_type == expected_failure
    assert (tmp_path / fixture_id / "deep_crawl_report.json").exists()
    assert (tmp_path / fixture_id / "summary.json").exists()
    if expected_result == CompletenessResult.PASS:
        assert result.report.covered_page_count == 50
        assert result.report.duplicate_suppressed_count == 5
