from __future__ import annotations

from pathlib import Path

from veracrawl.benchmarks.quality_metrics import run_quality_metric_benchmark
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.quality_metrics import QualityMetricManifest
from veracrawl.review_replay.quality_metrics import (
    confusion_record_replay_passes,
    missing_confusion_record_replay_refs,
    missing_quality_metric_report_replay_refs,
    quality_metric_report_replay_passes,
)
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


def _manifest() -> QualityMetricManifest:
    return QualityMetricManifest(
        id="precision-recall-quality",
        scenario="precision-recall-quality",
        profile_refs=["quality"],
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="quality_metrics_completed",
        required_ref_types=["field_confusion", "replay"],
    )


def test_quality_metric_replay_passes_for_successful_runtime(tmp_path: Path) -> None:
    result = run_quality_metric_benchmark(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )

    assert all(confusion_record_replay_passes(item) for item in result.confusion_records)
    assert quality_metric_report_replay_passes(result.report)


def test_quality_metric_replay_detects_missing_confusion_replay_ref(tmp_path: Path) -> None:
    result = run_quality_metric_benchmark(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )
    broken = result.confusion_records[0].model_copy(update={"replay_bundle_ref": None})

    assert "replay_bundle_ref" in missing_confusion_record_replay_refs(broken)
    assert not confusion_record_replay_passes(broken)


def test_quality_metric_replay_detects_missing_report_refs(tmp_path: Path) -> None:
    result = run_quality_metric_benchmark(
        manifest=_manifest(),
        profile="quality",
        store=ReferencePersistenceStore(tmp_path / "state"),
    )
    broken = result.report.model_copy(update={"replay_bundle_refs": []})

    assert "replay_bundle_refs" in missing_quality_metric_report_replay_refs(broken)
    assert not quality_metric_report_replay_passes(broken)
