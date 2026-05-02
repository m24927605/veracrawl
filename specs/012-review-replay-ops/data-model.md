# Data Model: VeraCrawl Review Replay Ops Console

## ReviewItem

Replay-visible review queue item for evidence, publication, graph/memory/agent signal, export, recovery, drift, conflict, or safety policy review. Open items require input refs, reason, priority, status, and policy refs. Accepted/rejected/resolved items require decision refs.

## ReplayAuditView

Replay console projection for a run. Passing views require replay bundle ref, validation report ref, command refs, event cursor refs, artifact hash refs, projection watermarks, policy refs, and completeness result.

## FailureRecord

Operational failure record with failure type, failed ref, owner, severity, retryability, policy refs, evidence/replay refs, recovery refs, and redacted diagnostic refs.

## RecoveryAction

Review/policy-gated recovery action. Destructive or side-effecting actions require policy and approval refs. Completed actions require result refs.

## DRRestoreReport

Disaster recovery validation report. Passing reports require metadata restore, artifact reachability, event replay, projection rebuild, validation refs, and no unresolved refs.

## QualityReport

Run quality dashboard record with fetch/output counts, verification counts, conflicts, drift events, freshness lag, quality rates, cost summary, open reviews, and replay/policy refs.

## OpsDashboardSnapshot

Replayable dashboard snapshot for run, frontier, review, replay, quality, or cost surfaces. Passing snapshots require event cursors, projection watermarks, quality report refs, and no stale projection refs.

## OpsConsoleReport

End-to-end report for the deterministic ops console slice. Passing reports require review items, replay audit views, quality reports, dashboard snapshot, DR restore report, policy refs, command refs, event cursors, and outbox refs.

## OpsFixtureManifest

Fixture manifest declaring scenario, target profile support, expected completion result, expected operator status, and whether the fixture is negative.
