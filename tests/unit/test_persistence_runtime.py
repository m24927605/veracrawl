from __future__ import annotations

from pathlib import Path

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.persistence.runtime import run_persistence_queue_runtime


def test_persistence_success_scenarios_emit_replayable_refs(tmp_path: Path) -> None:
    for scenario in [
        "persistence-transaction-success",
        "idempotent-replay-success",
        "queue-lease-recovery-success",
    ]:
        result = run_persistence_queue_runtime(
            fixture_id=f"unit-{scenario}",
            scenario=scenario,
            root=tmp_path / scenario,
            policy_decision_refs=["policy:unit:persistence"],
        )
        assert result.report.completion_result == CompletenessResult.PASS
        assert result.report.transaction_ref
        assert result.report.idempotency_record_refs
        assert result.report.queue_operation_refs


def test_persistence_negative_scenarios_emit_failures(tmp_path: Path) -> None:
    expectations = {
        "non-atomic-commit": "non_atomic_commit",
        "idempotency-not-persisted": "idempotency_not_persisted",
        "event-log-gap": "event_log_gap",
        "outbox-dispatch-missing": "outbox_dispatch_missing",
        "artifact-index-missing": "artifact_index_missing",
        "lease-heartbeat-missing": "lease_heartbeat_missing",
    }
    for scenario, operator_status in expectations.items():
        result = run_persistence_queue_runtime(
            fixture_id=f"unit-{scenario}",
            scenario=scenario,
            root=tmp_path / scenario,
            policy_decision_refs=["policy:unit:persistence"],
        )
        assert result.report.completion_result == CompletenessResult.FAIL
        assert result.report.operator_status == operator_status
        assert result.report.missing_ref_fields
