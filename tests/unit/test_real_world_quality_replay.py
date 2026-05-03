from __future__ import annotations

from tests.contract.test_real_world_quality_contracts import _report
from veracrawl.review_replay.real_world_quality import (
    missing_real_world_quality_replay_refs,
    real_world_quality_replay_passes,
)


def test_real_world_quality_replay_passes_for_complete_report() -> None:
    report = _report()
    assert real_world_quality_replay_passes(report)
    assert missing_real_world_quality_replay_refs(report) == []


def test_real_world_quality_replay_detects_missing_refs() -> None:
    report = _report()
    report = report.model_construct(**(report.model_dump() | {"replay_bundle_refs": []}))
    missing = missing_real_world_quality_replay_refs(report)
    assert "replay_bundle_refs" in missing
