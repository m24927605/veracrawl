"""``AuthorizedSessionAdapter`` — Phase 2 step 2.4b.

Per request, two-phase audit:

1. Pre-flight clock validation (tz-aware required).
2. Apply :class:`~veracrawl.ports.session_scope_policy.SessionScopePolicy`
   against the credential's scope. **Out-of-scope refusal**:
   emit a ``credential_scope_denied`` structured-log event AND
   raise :class:`CredentialScopeViolation` (Phase 0.4 +
   Phase 2 step 2.2b structured ``CredentialScopeReason``).
3. Fetch a :class:`CredentialValue` from the
   :class:`~veracrawl.ports.credential_vault.CredentialVaultPort`.
   Failures propagate as :class:`CredentialNotFoundError`. The
   vault layer's own :class:`CredentialAccessAuditPort` has
   already recorded the access attempt.
4. **Pre-send audit** (codex iter-1 critical): write a PENDING
   :class:`CredentialUseRecord` (``response_status=None``,
   ``attempt_evidence_ref="attempt:pending:<uuid>"``) to the
   :class:`CredentialUseAuditPort` BEFORE the transport sees the
   request. On audit-write failure, refuse the request before
   transmission (true "no use without audit" — the credential
   never goes over the wire).
5. Reveal credential and inject ``Authorization: Bearer <reveal>``
   header on the request (design.md §3.3 narrowest possible
   reveal scope).
6. Send via the injected :class:`httpx.BaseTransport`. On
   transport exception (no response materializes), emit a
   ``credential_use_transport_failed`` structured-log event and
   re-raise the original transport exception. The pending record
   stays in the audit log for correlation.
7. **Post-receive audit** (codex iter-1 critical): on a
   successful HTTP completion (response received, any status),
   write a SECOND :class:`CredentialUseRecord` with the actual
   ``response_status``. On audit-write failure, refuse to return
   the response (close + raise).

What this adapter does NOT do (reservation — Phase 6 step 6.1):

* Phase 1 transport composition (robots check, AIMD limiter,
  retry, redirect SSRF re-check, NetworkAttemptEvidence capture,
  cross-origin Authorization strip on redirect). The injected
  ``transport`` is a raw :class:`httpx.BaseTransport`; production
  wiring composes the adapter through Phase 1's
  :class:`StdlibHttpSourceAdapter` by routing the authorized
  request through the Phase 1 stack with the Authorization
  header configured in ``HttpClientConfig.extra_headers``.
  This Phase 2 step 2.4b adapter is the credential-plumbing
  layer; Phase 6 step 6.1 wires the production composition
  through the cooperative HTTP transport.
* Real :class:`NetworkAttemptEvidence` correlation. The pending
  record's ``attempt_evidence_ref="attempt:pending:..."`` is a
  placeholder; Phase 6 step 6.1 replaces it with the real
  evidence ref produced by the wrapped Phase 1 transport.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

import httpx

from veracrawl.contracts.common import Ref
from veracrawl.contracts.errors import CredentialScopeViolation, _redact_url
from veracrawl.contracts.security_privacy import (
    CredentialScope,
    CredentialUseRecord,
)
from veracrawl.ports.credential_use_audit import CredentialUseAuditPort
from veracrawl.ports.credential_vault import (
    CredentialNotFoundError,
    CredentialVaultPort,
)
from veracrawl.ports.session_scope_policy import SessionScopePolicy
from veracrawl.runtime_support.logging import get_logger

_logger = get_logger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class AuthorizedSessionAdapter:
    """Production credential-injection HTTP adapter.

    Construction:

    * ``transport`` — :class:`httpx.BaseTransport` (real HTTP in
      production; ``httpx.MockTransport`` in tests).
    * ``vault`` — :class:`CredentialVaultPort` (production:
      :class:`OutboxVaultClient`; tests: any Protocol satisfier).
    * ``scope_policy`` — :class:`SessionScopePolicy` (production:
      :class:`StrictAllowlistScope`).
    * ``credential_scope`` — :class:`CredentialScope` Phase 0
      record carrying ``allowed_origins`` / ``allowed_route_patterns``
      / ``allowed_methods`` / ``expires_at``. The scope-policy
      check uses this on every request.
    * ``vault_scope_ref`` — env-var-safe scope identifier the
      vault uses (Phase 2 step 2.1's ``^[A-Z0-9_]+$`` shape). The
      orchestrator translates ``credential_scope.id`` to this
      vault-safe form at wiring time.
    * ``vault_key`` — env-var-safe credential key.
    * ``use_audit`` — :class:`CredentialUseAuditPort`.
    * ``run_ref`` — opaque run identifier for audit correlation.
    * ``clock`` — injectable tz-aware clock for replay determinism.

    The adapter is stateless beyond its injected dependencies and
    is safe to share across requests in a single run. Construction
    does NOT fetch the credential — fetch is per-request so a
    long-running adapter picks up token refreshes from the vault.
    """

    def __init__(
        self,
        *,
        transport: httpx.BaseTransport,
        vault: CredentialVaultPort,
        scope_policy: SessionScopePolicy,
        credential_scope: CredentialScope,
        vault_scope_ref: str,
        vault_key: str,
        use_audit: CredentialUseAuditPort,
        run_ref: Ref,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._transport = transport
        self._vault = vault
        self._scope_policy = scope_policy
        self._credential_scope = credential_scope
        self._vault_scope_ref = vault_scope_ref
        self._vault_key = vault_key
        self._use_audit = use_audit
        self._run_ref = run_ref
        self._clock = clock

    def _now(self) -> datetime:
        ts = self._clock()
        if ts.tzinfo is None or ts.utcoffset() is None:
            raise RuntimeError(
                "AuthorizedSessionAdapter.clock returned a tz-naive "
                "datetime; replay determinism requires tz-aware timestamps"
            )
        return ts

    def request(self, *, method: str, url: str) -> httpx.Response:
        """Send an authorized HTTP request with two-phase audit.

        See module docstring for the full ordering. URL field on
        any structured-log event is redacted via
        ``contracts.errors._redact_url`` (drops query / fragment /
        userinfo) so OAuth / session-id query parameters cannot
        leak via the audit fallback path.
        """

        timestamp = self._now()
        sanitized_url = _redact_url(url)

        # 2. Scope policy check — out-of-scope refusal emits a
        #    structured-log audit event so denied attempts are
        #    visible (codex iter-1 important).
        try:
            self._scope_policy.check(
                self._credential_scope,
                request_url=url,
                method=method,
                now=timestamp,
            )
        except CredentialScopeViolation as exc:
            _logger.info(
                "credential_scope_denied",
                run_ref=self._run_ref,
                credential_scope_ref=self._credential_scope.id,
                request_url=sanitized_url,
                request_method=method,
                reason=exc.reason.value,
                timestamp_iso=timestamp.isoformat(),
            )
            raise

        # 3. Vault fetch (vault layer's own audit fires inside).
        cred = self._vault.get(scope_ref=self._vault_scope_ref, key=self._vault_key)

        # 4. Pre-send audit (codex iter-1 critical): write a
        #    PENDING CredentialUseRecord BEFORE transport. If the
        #    audit write fails, the credential never goes over the
        #    wire — true "no use without audit".
        use_record_id = f"credential-use:{uuid.uuid4().hex}"
        pending_evidence_ref = f"attempt:pending:{uuid.uuid4().hex}"
        pending_record = CredentialUseRecord(
            id=use_record_id,
            run_ref=self._run_ref,
            credential_scope_ref=self._credential_scope.id,
            request_url=url,
            request_method=method,
            response_status=None,
            timestamp_used=timestamp,
            attempt_evidence_ref=pending_evidence_ref,
        )
        pending_audit_failed = False
        try:
            self._use_audit.record(pending_record)
        except Exception:
            pending_audit_failed = True
        if pending_audit_failed:
            _logger.error(  # noqa: TRY400
                "credential_use_audit_failed",
                phase="pending",
                use_record_id=use_record_id,
                run_ref=self._run_ref,
                credential_scope_ref=self._credential_scope.id,
                request_method=method,
                request_url=sanitized_url,
                timestamp_iso=timestamp.isoformat(),
            )
            raise CredentialNotFoundError(
                "credential use pre-send audit write failed; refusing "
                "to send the credential-bearing request (no use "
                "without audit). See structured-log fallback event "
                "``credential_use_audit_failed`` (phase=pending)."
            ) from None

        # 5 + 6. Reveal + send. Reveal at the single call site
        #    (design.md §3.3) and immediately hand to the transport.
        #    Transport exception still has the pending record in
        #    the audit log for correlation.
        request = httpx.Request(
            method=method,
            url=url,
            headers={"Authorization": f"Bearer {cred.reveal()}"},
        )
        try:
            response = self._transport.handle_request(request)
        except Exception:
            _logger.error(  # noqa: TRY400
                "credential_use_transport_failed",
                use_record_id=use_record_id,
                pending_attempt_ref=pending_evidence_ref,
                run_ref=self._run_ref,
                credential_scope_ref=self._credential_scope.id,
                request_method=method,
                request_url=sanitized_url,
                timestamp_iso=timestamp.isoformat(),
            )
            raise

        # 7. Post-receive audit (codex iter-1 critical): write a
        #    SECOND record with the actual response_status. This is
        #    the audit-of-record; the pending record + this record
        #    correlate by run_ref + credential_scope_ref + adjacent
        #    timestamps in the audit pipeline.
        completion_record = CredentialUseRecord(
            id=f"credential-use:{uuid.uuid4().hex}",
            run_ref=self._run_ref,
            credential_scope_ref=self._credential_scope.id,
            request_url=url,
            request_method=method,
            response_status=response.status_code,
            timestamp_used=self._now(),
            attempt_evidence_ref=None,
        )
        completion_audit_failed = False
        try:
            self._use_audit.record(completion_record)
        except Exception:
            completion_audit_failed = True
        if completion_audit_failed:
            _logger.error(  # noqa: TRY400
                "credential_use_audit_failed",
                phase="completion",
                use_record_id=completion_record.id,
                pending_record_id=use_record_id,
                run_ref=self._run_ref,
                credential_scope_ref=self._credential_scope.id,
                request_method=method,
                request_url=sanitized_url,
                response_status=response.status_code,
                timestamp_iso=completion_record.timestamp_used.isoformat(),
            )
            response.close()
            raise CredentialNotFoundError(
                "credential use completion audit write failed; "
                "refusing to return the credential-bearing response "
                "(no use without audit). The pending record is still "
                "in the audit log; the missing completion event is "
                "in the structured-log fallback "
                "``credential_use_audit_failed`` (phase=completion)."
            ) from None

        return response


__all__ = ["AuthorizedSessionAdapter"]
