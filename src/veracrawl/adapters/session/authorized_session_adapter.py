"""``AuthorizedSessionAdapter`` — Phase 2 step 2.4b.

Per request:

1. Apply :class:`~veracrawl.ports.session_scope_policy.SessionScopePolicy`
   against the credential's scope. Out-of-scope refusal raises
   :class:`CredentialScopeViolation` (Phase 0.4 + Phase 2 step 2.2b
   structured ``CredentialScopeReason``).
2. Fetch a :class:`CredentialValue` from the
   :class:`~veracrawl.ports.credential_vault.CredentialVaultPort`
   (e.g., :class:`OutboxVaultClient` Phase 2 step 2.4a). Failures
   propagate as :class:`CredentialNotFoundError`.
3. Inject ``Authorization: Bearer <reveal()>`` header on the
   request. The credential value is revealed at this single
   call site — design.md §3.3 narrowest possible reveal scope —
   then immediately handed to the transport which sends bytes.
4. Send via the injected :class:`httpx.BaseTransport`.
5. On a successful HTTP completion (response received, any
   status), write a :class:`CredentialUseRecord` to the
   :class:`CredentialUseAuditPort`.
6. On audit-write failure: refuse to return the response (no use
   without audit) and emit a fallback structured-log event.

What this adapter does NOT do:

* Transport-level retries — the injected transport is the
  post-retry transport (Phase 1 step 1.5 wraps).
* Network attempt evidence (`NetworkAttemptEvidence`) capture —
  Phase 1 step 1.5 owns that. This adapter only wires the
  credential plumbing on top.
* Response-body capture / HAR — Phase 1 step 1.4 owns that.

Reservation (carried forward to Phase 6 step 6.1): on transport-
level failure (exception before a response materializes), the
adapter currently propagates without writing a use record because
:class:`CredentialUseRecord` requires ``attempt_evidence_ref`` for
``response_status=None`` rows, and this adapter does not produce
attempt evidence. Phase 6 wires the
:class:`NetworkAttemptEvidence` correlation so the use record
can fire on transport failure too.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

import httpx

from veracrawl.contracts.common import Ref
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
        """Send an authorized HTTP request and audit the use.

        Order:

        1. Pre-flight clock validation (consistent with step 2.4a
           ``OutboxVaultClient`` — fail before any side-effect).
        2. Scope-policy check. Out of scope → raise
           :class:`CredentialScopeViolation` with no vault call,
           no transport call.
        3. Vault fetch. Failure → raise
           :class:`CredentialNotFoundError`. The vault layer's own
           audit has already recorded the failed access.
        4. Send request with ``Authorization: Bearer <reveal>``.
        5. On successful HTTP completion: write
           :class:`CredentialUseRecord` to the use audit. If the
           audit write fails, refuse to return the response (no
           use without audit) and emit a fallback structured-log
           event.
        """

        timestamp = self._now()

        # 2. Scope policy check — refuses with CredentialScopeViolation
        #    (typed PolicyViolation). Side-effect-free.
        self._scope_policy.check(
            self._credential_scope,
            request_url=url,
            method=method,
            now=timestamp,
        )

        # 3. Vault fetch.
        cred = self._vault.get(scope_ref=self._vault_scope_ref, key=self._vault_key)

        # 4. Build + send request. Reveal credential ONLY at this
        #    single call site (design.md §3.3 narrowest scope) and
        #    immediately hand to the transport.
        request = httpx.Request(
            method=method,
            url=url,
            headers={"Authorization": f"Bearer {cred.reveal()}"},
        )
        response = self._transport.handle_request(request)

        # 5. Build + write the CredentialUseRecord. Wrap in
        #    flag + raise-outside-except to keep `__context__` clean.
        use_record = CredentialUseRecord(
            id=f"credential-use:{uuid.uuid4().hex}",
            run_ref=self._run_ref,
            credential_scope_ref=self._credential_scope.id,
            request_url=url,
            request_method=method,
            response_status=response.status_code,
            timestamp_used=timestamp,
            attempt_evidence_ref=None,
        )
        audit_failed = False
        try:
            self._use_audit.record(use_record)
        except Exception:
            audit_failed = True
        if audit_failed:
            _logger.error(  # noqa: TRY400 — caller doesn't need our traceback
                "credential_use_audit_failed",
                use_record_id=use_record.id,
                run_ref=self._run_ref,
                credential_scope_ref=self._credential_scope.id,
                request_method=method,
                request_url=url,
                response_status=response.status_code,
                timestamp_iso=timestamp.isoformat(),
            )
            # Close the response so the connection / file handle
            # is not leaked. Then refuse the response to the caller.
            response.close()
            raise CredentialNotFoundError(
                "credential use audit write failed; refusing to return "
                "the credential-bearing response (no use without audit). "
                "See structured-log fallback event "
                "``credential_use_audit_failed``."
            ) from None

        return response


__all__ = ["AuthorizedSessionAdapter"]
