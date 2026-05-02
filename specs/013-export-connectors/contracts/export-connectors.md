# Export Connector Contracts

Required contracts:

- `ExportTargetSpec`
- `ExportJob`
- `ExportAttempt`
- `ExportDeliveryReceipt`
- `ExportWithdrawalJob`
- `ExportWithdrawalAttempt`
- `ExportCorrectionRecord`
- `ExportReconciliationReport`
- `ExportFixtureManifest`

Required commands:

- `record_export_target_spec`
- `dispatch_export`
- `complete_export`
- `fail_export`
- `dispatch_withdrawal`
- `complete_withdrawal`
- `fail_withdrawal`
- `record_export_reconciliation`

Required events:

- `export_target_recorded`
- `export_dispatched`
- `export_delivered`
- `export_failed`
- `export_withdrawal_attempted`
- `export_withdrawal_completed`
- `export_withdrawal_failed`
- `export_reconciliation_reported`

Required fixtures:

- `export-file-success`
- `export-api-success`
- `export-correction-withdrawal-success`
- `export-missing-receipt`
- `duplicate-export-idempotency`
- `withdrawal-missing-mapping`
- `destination-unsupported-withdrawal`
- `correction-without-withdrawal`
