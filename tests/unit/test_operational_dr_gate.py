from __future__ import annotations

from veracrawl.contracts.enums import (
    CompletenessResult,
    DRRestoreFailureType,
    RuntimeInfrastructureAdapterFamily,
)
from veracrawl.contracts.infrastructure import RuntimeInfrastructureReport
from veracrawl.runtime_support.disaster_recovery import (
    dr_restore_plan,
    run_operational_dr_gate,
    run_operational_dr_runtime_unavailable_gate,
)


def test_operational_dr_gate_success_requires_integrated_runtime_refs() -> None:
    plan = dr_restore_plan(
        "unit",
        policy_decision_refs=["policy:unit:dr"],
        approval_decision_refs=["approval:unit:dr"],
    )
    result = run_operational_dr_gate(
        fixture_id="unit",
        scenario="dr-restore-success",
        plan=plan,
        runtime_infrastructure_report=_runtime_infrastructure_report("unit"),
    )
    assert result.report.result == CompletenessResult.PASS
    assert result.report.runtime_infrastructure_report_refs
    assert result.report.queue_recovery_refs
    assert result.report.recovery_action_refs


def test_operational_dr_runtime_unavailable_needs_review() -> None:
    plan = dr_restore_plan(
        "unit-no-runtime",
        policy_decision_refs=["policy:unit-no-runtime:dr"],
        approval_decision_refs=["approval:unit-no-runtime:dr"],
    )
    result = run_operational_dr_runtime_unavailable_gate(
        fixture_id="unit-no-runtime",
        plan=plan,
    )
    assert result.report.result == CompletenessResult.NEEDS_REVIEW
    assert result.report.contract_only_refs
    assert result.report.unresolved_refs


def test_operational_dr_negative_scenarios_fail_with_recovery_refs() -> None:
    expectations = {
        "dr-restore-missing-metadata": DRRestoreFailureType.MISSING_METADATA_RESTORE_REFS,
        "dr-restore-missing-artifact-reachability": (
            DRRestoreFailureType.MISSING_ARTIFACT_REACHABILITY_REFS
        ),
        "dr-restore-missing-event-replay": DRRestoreFailureType.MISSING_EVENT_REPLAY_REFS,
        "dr-restore-missing-projection-rebuild": (
            DRRestoreFailureType.MISSING_PROJECTION_REBUILD_REFS
        ),
        "dr-restore-missing-export-reconciliation": (
            DRRestoreFailureType.MISSING_EXPORT_RECONCILIATION_REFS
        ),
        "dr-restore-unresolved-refs": DRRestoreFailureType.UNRESOLVED_REFS,
        "dr-restore-data-loss": DRRestoreFailureType.DATA_LOSS_DETECTED,
        "dr-restore-unsafe-recovery-without-approval": (
            DRRestoreFailureType.UNSAFE_RECOVERY_WITHOUT_APPROVAL
        ),
    }
    for scenario, failure in expectations.items():
        plan = dr_restore_plan(
            scenario,
            policy_decision_refs=[f"policy:{scenario}:dr"],
            approval_decision_refs=[f"approval:{scenario}:dr"],
        )
        result = run_operational_dr_gate(
            fixture_id=scenario,
            scenario=scenario,
            plan=plan,
            runtime_infrastructure_report=None,
        )
        assert result.report.result == CompletenessResult.FAIL
        assert result.report.operator_status == failure.value
        assert result.failure_records
        assert result.recovery_actions


def _runtime_infrastructure_report(fixture_id: str) -> RuntimeInfrastructureReport:
    return RuntimeInfrastructureReport(
        id=f"runtime-infrastructure-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        infrastructure_spec_ref=f"runtime-infrastructure-spec:{fixture_id}",
        live_adapter_families=list(RuntimeInfrastructureAdapterFamily),
        persistence_report_refs=[f"persistence-report:{fixture_id}"],
        queue_broker_report_refs=[f"queue-broker-report:{fixture_id}"],
        object_store_report_refs=[f"object-store-report:{fixture_id}"],
        persistence_adapter_refs=[f"persistence-adapter:{fixture_id}"],
        queue_broker_adapter_refs=[f"queue-broker-adapter:{fixture_id}"],
        object_store_adapter_refs=[f"object-store-adapter:{fixture_id}"],
        transaction_refs=[f"transaction:{fixture_id}"],
        command_record_refs=[f"command:{fixture_id}"],
        idempotency_record_refs=[f"idempotency:{fixture_id}"],
        event_cursor_refs=[f"event-cursor:{fixture_id}"],
        outbox_refs=[f"outbox:{fixture_id}"],
        queue_topology_refs=[f"queue-topology:{fixture_id}"],
        queue_item_refs=[f"queue-item:{fixture_id}"],
        broker_operation_refs=[f"broker-operation:{fixture_id}"],
        queue_operation_refs=[f"queue-operation:{fixture_id}"],
        lease_refs=[f"lease:{fixture_id}"],
        heartbeat_refs=[f"heartbeat:{fixture_id}"],
        ack_refs=[f"ack:{fixture_id}"],
        nack_refs=[f"nack:{fixture_id}"],
        dead_letter_refs=[f"dead-letter:{fixture_id}"],
        artifact_refs=[f"artifact:{fixture_id}"],
        object_operation_refs=[f"object-operation:{fixture_id}"],
        content_digest_refs=[f"digest:{fixture_id}"],
        read_result_refs=[f"read:{fixture_id}"],
        head_refs=[f"head:{fixture_id}"],
        list_refs=[f"list:{fixture_id}"],
        delete_refs=[f"delete:{fixture_id}"],
        lifecycle_state_refs=[f"lifecycle:{fixture_id}"],
        retention_policy_refs=[f"retention:{fixture_id}"],
        privacy_policy_refs=[f"privacy:{fixture_id}"],
        policy_decision_refs=[f"policy:{fixture_id}:infra"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:infra",
        operator_status="operational_infrastructure_completed",
        completion_result=CompletenessResult.PASS,
    )
