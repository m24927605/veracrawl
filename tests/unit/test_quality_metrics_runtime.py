from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.benchmarks.quality_metrics import run_quality_metric_benchmark
from veracrawl.contracts.enums import CompletenessResult, QualityMetricFailureType
from veracrawl.contracts.quality_metrics import QualityMetricManifest
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


def _manifest(
    *,
    scenario: str = "precision-recall-quality",
    expected_result: CompletenessResult = CompletenessResult.PASS,
    expected_failure: QualityMetricFailureType | None = None,
) -> QualityMetricManifest:
    return QualityMetricManifest(
        id=scenario,
        scenario=scenario,
        profile_refs=["quality"],
        expected_completion_result=expected_result,
        expected_operator_status=(
            expected_failure.value if expected_failure else "quality_metrics_completed"
        ),
        expected_failure_type=expected_failure,
        negative_case=expected_failure is not None,
        required_ref_types=["field_confusion", "replay"],
    )


def test_quality_metric_runtime_computes_corpus_and_slice_metrics(tmp_path: Path) -> None:
    result = run_quality_metric_benchmark(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )

    assert result.report.completion_result == CompletenessResult.PASS
    assert result.report.precision >= 0.98
    assert result.report.recall >= 0.90
    assert result.report.f1 >= 0.94
    assert result.report.critical_field_precision >= 0.99
    assert result.report.false_positive_rate > 0
    assert result.report.abstention_rate > 0
    assert result.report.unsupported_rate > 0
    assert result.report.needs_review_rate > 0
    assert len(result.slice_metrics) >= 6
    assert all(item.replay_bundle_ref for item in result.confusion_records)


@pytest.mark.parametrize(
    ("scenario", "failure"),
    [
        ("precision-recall-low-precision", QualityMetricFailureType.PRECISION_BELOW_THRESHOLD),
        ("precision-recall-low-recall", QualityMetricFailureType.RECALL_BELOW_THRESHOLD),
        ("precision-recall-low-f1", QualityMetricFailureType.F1_BELOW_THRESHOLD),
        ("precision-recall-hidden-false-positive", QualityMetricFailureType.HIDDEN_FALSE_POSITIVE),
        ("precision-recall-llm-true-positive", QualityMetricFailureType.LLM_AS_TRUE_POSITIVE),
        ("precision-recall-replay-missing", QualityMetricFailureType.MISSING_REPLAY_REFS),
    ],
)
def test_quality_metric_runtime_maps_negative_fixtures(
    tmp_path: Path,
    scenario: str,
    failure: QualityMetricFailureType,
) -> None:
    result = run_quality_metric_benchmark(
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
