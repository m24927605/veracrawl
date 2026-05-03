from __future__ import annotations

from tests.contract.test_real_world_benchmark_contracts import _run_report
from veracrawl.review_replay.real_world_benchmark import (
    missing_real_world_benchmark_replay_refs,
    real_world_benchmark_replay_passes,
)


def test_real_world_benchmark_replay_passes_for_complete_report() -> None:
    report = _run_report()
    assert real_world_benchmark_replay_passes(report)
    assert missing_real_world_benchmark_replay_refs(report) == []


def test_real_world_benchmark_replay_detects_missing_refs() -> None:
    report = _run_report()
    report = report.model_construct(**(report.model_dump() | {"replay_bundle_refs": []}))
    missing = missing_real_world_benchmark_replay_refs(report)
    assert "replay_bundle_refs" in missing
