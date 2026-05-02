from __future__ import annotations

from pathlib import Path

from veracrawl.persistence.runtime import run_persistence_queue_runtime
from veracrawl.review_replay.persistence import (
    missing_persistence_replay_refs,
    persistence_replay_passes,
)


def test_persistence_replay_passes_for_complete_report(tmp_path: Path) -> None:
    result = run_persistence_queue_runtime(
        fixture_id="unit-persistence-replay",
        scenario="persistence-transaction-success",
        root=tmp_path,
        policy_decision_refs=["policy:unit:persistence"],
    )
    assert persistence_replay_passes(result.report)
    assert not missing_persistence_replay_refs(result.report)


def test_persistence_replay_reports_missing_idempotency(tmp_path: Path) -> None:
    result = run_persistence_queue_runtime(
        fixture_id="unit-persistence-missing-idempotency",
        scenario="idempotency-not-persisted",
        root=tmp_path,
        policy_decision_refs=["policy:unit:persistence"],
    )
    assert not persistence_replay_passes(result.report)
    assert "idempotency_record_refs" in missing_persistence_replay_refs(result.report)
