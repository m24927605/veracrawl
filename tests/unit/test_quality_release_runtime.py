from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.benchmarks.quality_release import run_quality_release_gate
from veracrawl.contracts.enums import (
    CompletenessResult,
    QualityReleaseDecision,
    QualityReleaseFailureType,
)
from veracrawl.contracts.quality_release import QualityReleaseManifest
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


def _manifest(
    *,
    scenario: str = "quality-release-ready",
    expected_result: CompletenessResult = CompletenessResult.PASS,
    expected_failure: QualityReleaseFailureType | None = None,
) -> QualityReleaseManifest:
    return QualityReleaseManifest(
        id=scenario,
        scenario=scenario,
        profile_refs=["quality"],
        expected_completion_result=expected_result,
        expected_release_decision=(
            QualityReleaseDecision.BLOCKED
            if expected_failure
            else QualityReleaseDecision.RELEASE_READY
        ),
        expected_failure_type=expected_failure,
        negative_case=expected_failure is not None,
        required_gate_refs=["058", "059", "060", "061", "062", "063"],
    )


def test_quality_release_runtime_aggregates_quality_gates_and_stability(
    tmp_path: Path,
) -> None:
    result = run_quality_release_gate(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )

    assert result.report.completion_result == CompletenessResult.PASS
    assert result.report.release_decision == QualityReleaseDecision.RELEASE_READY
    assert result.report.observed_quality_gate_count == 6
    assert result.report.stability_run_count == 3
    assert result.report.total_cost_usd <= 2.50
    assert result.report.p95_latency_ms <= 5000
    assert result.report.retry_rate <= 0.10
    assert result.report.stability_variance <= 0.05
    assert len(result.report.gate_report_refs) == 6
    assert all(item.replay_bundle_ref for item in result.quality_gates)
    assert all(item.slo_metric_refs for item in result.stability_runs)


@pytest.mark.parametrize(
    ("scenario", "failure"),
    [
        (
            "quality-release-missing-prior-gate",
            QualityReleaseFailureType.MISSING_QUALITY_GATE_REPORT,
        ),
        ("quality-release-cost-exceeded", QualityReleaseFailureType.COST_BUDGET_EXCEEDED),
        (
            "quality-release-latency-violation",
            QualityReleaseFailureType.LATENCY_SLO_VIOLATION,
        ),
        ("quality-release-retry-violation", QualityReleaseFailureType.RETRY_RATE_EXCEEDED),
        (
            "quality-release-stability-regression",
            QualityReleaseFailureType.STABILITY_REGRESSION,
        ),
        (
            "quality-release-insufficient-runs",
            QualityReleaseFailureType.INSUFFICIENT_STABILITY_RUNS,
        ),
        ("quality-release-replay-gap", QualityReleaseFailureType.REPLAY_GAP),
        ("quality-release-false-ready", QualityReleaseFailureType.FALSE_READY_STATUS),
        (
            "quality-release-missing-command-event",
            QualityReleaseFailureType.MISSING_COMMAND_EVENT_REFS,
        ),
    ],
)
def test_quality_release_runtime_maps_negative_fixtures(
    tmp_path: Path,
    scenario: str,
    failure: QualityReleaseFailureType,
) -> None:
    result = run_quality_release_gate(
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
    assert result.report.release_decision == QualityReleaseDecision.BLOCKED
