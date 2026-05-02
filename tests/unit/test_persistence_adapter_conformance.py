from __future__ import annotations

from pathlib import Path

from veracrawl.adapters.persistence.postgres_contract import postgres_adapter_spec
from veracrawl.adapters.persistence.sqlite import SQLitePersistenceAdapter, sqlite_adapter_spec
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.persistence.adapter_conformance import (
    run_postgres_contract_conformance,
    run_sqlite_adapter_conformance,
)


def test_sqlite_adapter_conformance_success(tmp_path: Path) -> None:
    fixture_id = "sqlite-adapter-conformance-success"
    policy_refs = [f"policy:{fixture_id}:persistence-adapter"]
    result = run_sqlite_adapter_conformance(
        fixture_id=fixture_id,
        scenario=fixture_id,
        store=SQLitePersistenceAdapter(tmp_path / "adapter.db"),
        adapter_spec=sqlite_adapter_spec(fixture_id, policy_refs),
        policy_decision_refs=policy_refs,
    )
    assert result.report.completion_result == CompletenessResult.PASS
    assert result.migrations
    assert result.transaction is not None
    assert result.event_count == 1
    assert result.outbox_count == 1


def test_sqlite_reopen_idempotency_dedupes_side_effects(tmp_path: Path) -> None:
    fixture_id = "sqlite-reopen-idempotency-success"
    policy_refs = [f"policy:{fixture_id}:persistence-adapter"]
    result = run_sqlite_adapter_conformance(
        fixture_id=fixture_id,
        scenario=fixture_id,
        store=SQLitePersistenceAdapter(tmp_path / "adapter.db"),
        adapter_spec=sqlite_adapter_spec(fixture_id, policy_refs),
        policy_decision_refs=policy_refs,
    )
    assert result.report.completion_result == CompletenessResult.PASS
    assert result.reloaded is True
    assert result.duplicate_deduped is True
    assert result.event_count == 1
    assert result.outbox_count == 1


def test_sqlite_negative_conformance_reports_missing_ref(tmp_path: Path) -> None:
    fixture_id = "sqlite-outbox-gap"
    policy_refs = [f"policy:{fixture_id}:persistence-adapter"]
    result = run_sqlite_adapter_conformance(
        fixture_id=fixture_id,
        scenario=fixture_id,
        store=SQLitePersistenceAdapter(tmp_path / "adapter.db"),
        adapter_spec=sqlite_adapter_spec(fixture_id, policy_refs),
        policy_decision_refs=policy_refs,
    )
    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.operator_status == "sqlite_outbox_gap"
    assert result.report.missing_ref_fields == ["outbox_refs"]


def test_postgres_contract_descriptor_reports_needs_review() -> None:
    fixture_id = "postgres-adapter-contract-harness"
    policy_refs = [f"policy:{fixture_id}:persistence-adapter"]
    result = run_postgres_contract_conformance(
        fixture_id=fixture_id,
        adapter_spec=postgres_adapter_spec(fixture_id, policy_refs),
        policy_decision_refs=policy_refs,
    )
    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.operator_status == "postgres_contract_declared"
    assert result.report.contract_only_refs
    assert not result.report.transaction_refs
