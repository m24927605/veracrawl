from __future__ import annotations

from veracrawl.contracts.enums import OwnerService
from veracrawl.contracts.registry import (
    COMMAND_TYPES,
    EVENT_TYPES,
    FIXTURE_ORACLES,
    FOUNDATION_CONTRACTS,
    TARGET_CONTRACT_AREAS,
    validate_registry,
)


def test_export_contracts_are_registered() -> None:
    expected = {
        "ExportTargetSpec",
        "ExportJob",
        "ExportAttempt",
        "ExportDeliveryReceipt",
        "ExportWithdrawalJob",
        "ExportWithdrawalAttempt",
        "ExportCorrectionRecord",
        "ExportReconciliationReport",
        "ExportFixtureManifest",
    }
    assert expected.issubset(FOUNDATION_CONTRACTS)
    assert validate_registry().ok


def test_export_commands_and_events_are_registered() -> None:
    expected = {
        "record_export_target_spec": "export_target_recorded",
        "dispatch_export": "export_dispatched",
        "complete_export": "export_delivered",
        "fail_export": "export_failed",
        "dispatch_withdrawal": "export_withdrawal_attempted",
        "complete_withdrawal": "export_withdrawal_completed",
        "fail_withdrawal": "export_withdrawal_failed",
        "record_export_reconciliation": "export_reconciliation_reported",
    }
    for command_type, event_type in expected.items():
        assert command_type in COMMAND_TYPES
        assert event_type in COMMAND_TYPES[command_type].emitted_event_types
        assert event_type in EVENT_TYPES


def test_export_target_area_is_materialized() -> None:
    area = TARGET_CONTRACT_AREAS["export"]
    assert area.owner_service == OwnerService.EXPORT
    assert area.coverage_status == "materialized"
    assert "ExportDeliveryReceipt" in area.materialized_contract_refs
    assert "ExportWithdrawalAttempt" in area.materialized_contract_refs
    assert area.followup_spec_gate is None


def test_export_fixtures_are_registered() -> None:
    expected = {
        "export-file-success",
        "export-api-success",
        "export-correction-withdrawal-success",
        "export-missing-receipt",
        "duplicate-export-idempotency",
        "withdrawal-missing-mapping",
        "destination-unsupported-withdrawal",
        "correction-without-withdrawal",
    }
    assert expected.issubset(FIXTURE_ORACLES)
    assert not FIXTURE_ORACLES["export-file-success"].negative_case
    assert FIXTURE_ORACLES["correction-without-withdrawal"].negative_case
