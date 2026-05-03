from __future__ import annotations

from veracrawl.release.benchmark_gate import run_production_benchmark_release_gate
from veracrawl.review_replay.release_gate import (
    missing_production_release_refs,
    production_release_replay_passes,
)


def test_release_replay_passes_for_complete_release_report() -> None:
    report = run_production_benchmark_release_gate(
        fixture_id="unit-release-replay",
        scenario="production-release-benchmark-success",
    ).report
    assert missing_production_release_refs(report) == []
    assert production_release_replay_passes(report)


def test_release_replay_fails_for_missing_refs() -> None:
    report = run_production_benchmark_release_gate(
        fixture_id="unit-release-missing",
        scenario="production-release-missing-target-runtime",
    ).report
    assert "target_runtime_report_ref" in missing_production_release_refs(report)
    assert not production_release_replay_passes(report)


def test_release_replay_fails_for_replay_gap() -> None:
    report = run_production_benchmark_release_gate(
        fixture_id="unit-release-replay-gap",
        scenario="production-release-replay-mismatch",
    ).report
    assert report.replay_gap_refs
    assert not production_release_replay_passes(report)
