from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult, ExportTargetType
from veracrawl.export.runtime import run_export_connector


def test_export_success_scenarios_emit_receipts_and_mappings() -> None:
    expectations = {
        "export-file-success": ExportTargetType.FILE,
        "export-api-success": ExportTargetType.API,
        "export-correction-withdrawal-success": ExportTargetType.FILE,
    }
    for scenario, target_type in expectations.items():
        result = run_export_connector(
            fixture_id=f"unit-{scenario}",
            scenario=scenario,
            policy_decision_refs=["policy:unit:export"],
        )
        assert result.report.completion_result == CompletenessResult.PASS
        assert result.target_specs[0].target_type == target_type
        assert result.delivery_receipts
        assert result.withdrawal_attempts
        assert result.correction_records


def test_export_negative_scenarios_emit_failure_reports() -> None:
    expectations = {
        "export-missing-receipt": "missing_delivery_receipt",
        "duplicate-export-idempotency": "duplicate_idempotency",
        "withdrawal-missing-mapping": "withdrawal_mapping_missing",
        "correction-without-withdrawal": "correction_without_withdrawal",
    }
    for scenario, operator_status in expectations.items():
        result = run_export_connector(
            fixture_id=f"unit-{scenario}",
            scenario=scenario,
            policy_decision_refs=["policy:unit:export"],
        )
        assert result.report.completion_result == CompletenessResult.FAIL
        assert result.report.operator_status == operator_status
        assert result.report.failure_report_refs
