# Data Model: Security Privacy Lifecycle Gate

## SecurityPolicyCheck

Records a blocked or allowed check for network, prompt, credential, browser, memory, graph, export, recovery, or artifact lifecycle action.

Pass requires policy, subject, scope, decision, observability, command, event, and replay refs.

## CredentialUseAudit

Records customer-authorized credential presentation through scoped header, scoped cookie, request signing, or vault-brokered form fill.

Pass requires origin allowlist, scoped delivery mode, authorization, redaction, policy, audit, and replay refs. Raw secret refs are forbidden.

## PromptTaintBoundary

Records taint labels, sanitized context refs, blocked tool refs, and prompt-use restrictions for untrusted content.

Pass requires taint, sanitized context, blocked unsafe tool, policy, and replay refs.

## ArtifactLifecycleAction

Records classify, redact, tombstone, delete, legal hold, retention, or release legal hold action.

Pass requires artifact, lifecycle, retention/privacy policy, approval for side effects, projection cleanup, command/event/outbox, and replay refs.

## ProjectionCleanupRecord

Records cleanup propagation to search, graph, memory, dashboard, export, and replay projections.

Pass requires affected projection refs, watermark refs, lifecycle action refs, policy refs, and replay refs.

## SecurityPrivacyReport

Pass requires security policy checks, credential audit, prompt taint, artifact lifecycle, projection cleanup, redacted replay, observability, policy, command, event cursor, outbox, failure/recovery, and zero leakage refs.

Needs-review requires contract-only refs. Fail requires typed failure refs or leakage diagnostics.
