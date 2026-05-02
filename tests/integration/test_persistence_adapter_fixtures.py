from __future__ import annotations

from pathlib import Path

from tests.helpers.persistence_adapter_fixture_assertions import (
    assert_persistence_adapter_negative,
    assert_postgres_contract_only,
    assert_sqlite_adapter_success,
)
from veracrawl.cli.persistence_adapter import run_fixture


def test_persistence_adapter_success_fixtures(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id in [
        "sqlite-adapter-conformance-success",
        "sqlite-reopen-idempotency-success",
        "sqlite-queue-recovery-success",
    ]:
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_sqlite_adapter_success(report)
        if fixture_id == "sqlite-reopen-idempotency-success":
            assert report.reloaded is True
            assert report.duplicate_deduped is True
            assert report.event_count == 1
            assert report.outbox_count == 1


def test_postgres_adapter_contract_fixture_is_not_operational_pass(tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "postgres-adapter-contract-harness",
        profile="target",
        out=tmp_path / "postgres-adapter-contract-harness",
    )
    assert_postgres_contract_only(report)


def test_persistence_adapter_negative_fixtures(tmp_path: Path) -> None:
    expectations = {
        "adapter-missing-capability": "adapter_missing_capability",
        "sqlite-idempotency-gap": "sqlite_idempotency_gap",
        "sqlite-event-cursor-gap": "sqlite_event_cursor_gap",
        "sqlite-outbox-gap": "sqlite_outbox_gap",
        "sqlite-migration-missing": "sqlite_migration_missing",
    }
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id, operator_status in expectations.items():
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
        )
        assert_persistence_adapter_negative(report, operator_status=operator_status)
