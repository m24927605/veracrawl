from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.cli import quality_release
from veracrawl.contracts.enums import (
    CompletenessResult,
    QualityReleaseDecision,
    QualityReleaseFailureType,
)


@pytest.mark.parametrize(
    ("fixture_id", "expected_result", "expected_failure"),
    [
        ("quality-release-ready", CompletenessResult.PASS, None),
        (
            "quality-release-missing-prior-gate",
            CompletenessResult.FAIL,
            QualityReleaseFailureType.MISSING_QUALITY_GATE_REPORT,
        ),
        (
            "quality-release-cost-exceeded",
            CompletenessResult.FAIL,
            QualityReleaseFailureType.COST_BUDGET_EXCEEDED,
        ),
        (
            "quality-release-latency-violation",
            CompletenessResult.FAIL,
            QualityReleaseFailureType.LATENCY_SLO_VIOLATION,
        ),
        (
            "quality-release-retry-violation",
            CompletenessResult.FAIL,
            QualityReleaseFailureType.RETRY_RATE_EXCEEDED,
        ),
        (
            "quality-release-stability-regression",
            CompletenessResult.FAIL,
            QualityReleaseFailureType.STABILITY_REGRESSION,
        ),
        (
            "quality-release-insufficient-runs",
            CompletenessResult.FAIL,
            QualityReleaseFailureType.INSUFFICIENT_STABILITY_RUNS,
        ),
        (
            "quality-release-replay-gap",
            CompletenessResult.FAIL,
            QualityReleaseFailureType.REPLAY_GAP,
        ),
        (
            "quality-release-false-ready",
            CompletenessResult.FAIL,
            QualityReleaseFailureType.FALSE_READY_STATUS,
        ),
        (
            "quality-release-missing-command-event",
            CompletenessResult.FAIL,
            QualityReleaseFailureType.MISSING_COMMAND_EVENT_REFS,
        ),
    ],
)
def test_quality_release_fixture_contracts(
    tmp_path: Path,
    fixture_id: str,
    expected_result: CompletenessResult,
    expected_failure: QualityReleaseFailureType | None,
) -> None:
    result = quality_release.run_fixture(
        Path("tests/fixtures") / fixture_id,
        profile="quality",
        out=tmp_path / fixture_id,
    )

    assert result.report.completion_result == expected_result
    assert result.report.failure_type == expected_failure
    assert (tmp_path / fixture_id / "quality_release_report.json").exists()
    assert (tmp_path / fixture_id / "summary.json").exists()
    if expected_result == CompletenessResult.PASS:
        assert result.report.release_decision == QualityReleaseDecision.RELEASE_READY
        assert result.report.observed_quality_gate_count == 6
        assert result.report.stability_run_count == 3
