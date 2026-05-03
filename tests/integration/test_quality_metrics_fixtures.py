from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.cli import quality_metrics
from veracrawl.contracts.enums import CompletenessResult, QualityMetricFailureType


@pytest.mark.parametrize(
    ("fixture_id", "expected_result", "expected_failure"),
    [
        ("precision-recall-quality", CompletenessResult.PASS, None),
        (
            "precision-recall-low-precision",
            CompletenessResult.FAIL,
            QualityMetricFailureType.PRECISION_BELOW_THRESHOLD,
        ),
        (
            "precision-recall-low-recall",
            CompletenessResult.FAIL,
            QualityMetricFailureType.RECALL_BELOW_THRESHOLD,
        ),
        (
            "precision-recall-low-f1",
            CompletenessResult.FAIL,
            QualityMetricFailureType.F1_BELOW_THRESHOLD,
        ),
        (
            "precision-recall-hidden-false-positive",
            CompletenessResult.FAIL,
            QualityMetricFailureType.HIDDEN_FALSE_POSITIVE,
        ),
        (
            "precision-recall-llm-true-positive",
            CompletenessResult.FAIL,
            QualityMetricFailureType.LLM_AS_TRUE_POSITIVE,
        ),
        (
            "precision-recall-replay-missing",
            CompletenessResult.FAIL,
            QualityMetricFailureType.MISSING_REPLAY_REFS,
        ),
    ],
)
def test_quality_metric_fixture_contracts(
    tmp_path: Path,
    fixture_id: str,
    expected_result: CompletenessResult,
    expected_failure: QualityMetricFailureType | None,
) -> None:
    result = quality_metrics.run_fixture(
        Path("tests/fixtures") / fixture_id,
        profile="quality",
        out=tmp_path / fixture_id,
    )

    assert result.report.completion_result == expected_result
    assert result.report.failure_type == expected_failure
    assert (tmp_path / fixture_id / "precision_recall_report.json").exists()
    assert (tmp_path / fixture_id / "summary.json").exists()
    if expected_result == CompletenessResult.PASS:
        assert result.report.precision >= 0.98
        assert result.report.recall >= 0.90
