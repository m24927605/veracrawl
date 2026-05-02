# Data Model: VeraCrawl Export Connectors

## ExportTargetSpec

Destination-neutral target contract for file, API, database, warehouse, object store, and queue export targets. Stores destination, schema, auth scope, delivery mode, and idempotency template refs.

## ExportJob

Owner-service job for dispatching immutable output refs to a target. Requires output refs, policy refs, idempotency refs, and status.

## ExportAttempt

Single export dispatch attempt with idempotency key, output refs, destination object IDs, receipt ref, retry classification, status, and redacted error data.

## ExportDeliveryReceipt

Destination receipt proving delivered or withdrawn output refs map to external object IDs.

## ExportWithdrawalJob

Policy-gated job for supersession, dispute, retention delete, schema migration, or operator withdrawal.

## ExportWithdrawalAttempt

Single withdrawal propagation attempt with idempotency key, external mappings, propagation status, receipt ref, unsupported reason, and error data.

## ExportCorrectionRecord

Correction propagation record tying superseded output, replacement output, withdrawal job, replacement export job, destination mappings, receipt refs, and policy refs together.

## ExportReconciliationReport

Replayable report proving export dispatch, receipts, withdrawal, correction, policy, command, event cursor, outbox, and replay refs.

## ExportFixtureManifest

Fixture manifest declaring scenario, target profile support, expected completion result, expected operator status, and negative-case status.
