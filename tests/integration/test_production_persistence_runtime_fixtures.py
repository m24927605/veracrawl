from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.cli.production_persistence import run_fixture
from veracrawl.contracts.enums import CompletenessResult

PRODUCTION_PERSISTENCE_FIXTURES = [
    "production-persistence-wiring-success",
    "production-persistence-idempotent-replay",
    "production-persistence-queue-recovery",
    "production-persistence-non-atomic-commit",
    "production-persistence-canonical-state-missing",
    "production-persistence-idempotency-missing",
    "production-persistence-event-gap",
    "production-persistence-outbox-missing",
    "production-persistence-artifact-index-missing",
    "production-persistence-lease-heartbeat-missing",
    "production-persistence-replay-missing",
]


@pytest.mark.parametrize("fixture_id", PRODUCTION_PERSISTENCE_FIXTURES)
def test_production_persistence_cli_fixture_contracts(
    tmp_path: Path,
    fixture_id: str,
) -> None:
    fixture_dir = Path("tests/fixtures") / fixture_id
    report = run_fixture(
        fixture_dir,
        profile="target",
        out=tmp_path / fixture_id,
    )

    assert report.fixture_id == fixture_id
    assert (tmp_path / fixture_id / "run_report.json").exists()
    if report.completion_result == CompletenessResult.PASS:
        assert report.reloaded
        assert report.canonical_state_refs
        assert report.event_cursor_ref
        assert report.replay_bundle_ref
    else:
        assert report.failure_type is not None
        assert report.missing_ref_fields


def test_idempotent_replay_fixture_records_zero_duplicate_side_effects(
    tmp_path: Path,
) -> None:
    report = run_fixture(
        Path("tests/fixtures/production-persistence-idempotent-replay"),
        profile="target",
        out=tmp_path / "idempotent",
    )

    assert report.duplicate_deduped is True
    assert report.event_count == report.pre_duplicate_event_count
    assert report.outbox_count == report.pre_duplicate_outbox_count
