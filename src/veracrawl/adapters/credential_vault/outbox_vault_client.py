"""``OutboxVaultClient`` — production :class:`CredentialVaultPort` impl.

Phase 2 step 2.4a: the production credential-retrieval path.
Delegates the actual fetch to a :class:`VaultBackendPort` adapter
(HashiCorp Vault / AWS Secrets Manager / customer-supplied), writes
a :class:`CredentialAccessAuditPort` row per access, and returns
the value wrapped in :class:`CredentialValue` (Phase 2 step 2.1)
so the secret is auto-redacted in ``__repr__`` / ``__str__`` /
``__format__`` / ``dir()``.

Unlike Phase 2 step 2.1's :class:`EnvVarVault` (test-only,
production-gated), this client IS the production path — no
``ProductionRuntimeNotImplemented`` gate. The injectable
``VaultBackendPort`` lets tests substitute an
:class:`InMemoryVaultBackend` (which has its own production gate)
without changing the client's wiring.

Key design decisions:

* Failure translation: the client converts the structured
  :class:`VaultBackendError` (operational failure) into
  :class:`CredentialNotFoundError` (the typed
  :class:`CredentialVaultPort` failure) for the
  ``BACKEND_UNREACHABLE`` / ``AUTH_FAILED`` / ``INTERNAL`` kinds.
  ``NOT_FOUND`` from the backend (or a ``None`` return) maps to
  ``CredentialNotFoundError`` directly. The original kind is
  carried through the audit row's ``success=False`` event but
  never on the exception's public attributes.
* Audit emission: every ``get`` writes one audit row, regardless
  of success / failure. This is design.md §3.3's "audit trail"
  requirement.
* Clock injection: ``clock`` is injected for replay determinism.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Final

from veracrawl.contracts.common import Ref
from veracrawl.ports.credential_access_audit import (
    CredentialAccessAuditPort,
    CredentialAccessOutcome,
)
from veracrawl.ports.credential_vault import (
    CredentialNotFoundError,
    CredentialValue,
)
from veracrawl.ports.vault_backend import (
    VaultBackendError,
    VaultBackendErrorKind,
    VaultBackendPort,
)
from veracrawl.runtime_support.logging import get_logger

_SAFE_IDENT_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Z0-9_]+$")
_REDACTED_IDENT: Final[str] = "[REDACTED]"

# Maps the structured backend-failure kind onto the corresponding
# audit outcome. Kept as a closed dict so a new VaultBackendErrorKind
# value forces a deliberate decision at the next test run.
_BACKEND_KIND_TO_OUTCOME: Final[dict[VaultBackendErrorKind, CredentialAccessOutcome]] = {
    VaultBackendErrorKind.NOT_FOUND: CredentialAccessOutcome.NOT_FOUND,
    VaultBackendErrorKind.BACKEND_UNREACHABLE: CredentialAccessOutcome.BACKEND_UNREACHABLE,
    VaultBackendErrorKind.AUTH_FAILED: CredentialAccessOutcome.AUTH_FAILED,
    VaultBackendErrorKind.INTERNAL: CredentialAccessOutcome.INTERNAL,
}

_logger = get_logger(__name__)


def _is_valid_identifier(name: str) -> bool:
    """Symmetric with EnvVarVault: scope_ref and key must be
    env-var-safe."""

    return bool(name) and _SAFE_IDENT_RE.fullmatch(name) is not None


def _hashed_ref(name: str) -> str:
    """Stable opaque identifier for audit rows.

    Codex iter-2 important: even shape-validated identifiers (uppercase
    + digit + underscore matching ``^[A-Z0-9_]+$``) may carry secret-
    shaped tokens. The audit pipeline should never persist the
    caller-supplied string directly. Replace with a stable
    deterministic hash so operators can correlate log entries
    across services without seeing the original identifier.

    Format: ``"sha256:<first 16 hex chars>"``. 64-bit collision
    space is enough for audit correlation; not used for security
    decisions.
    """

    return f"sha256:{hashlib.sha256(name.encode('utf-8')).hexdigest()[:16]}"


def _utc_now() -> datetime:
    return datetime.now(UTC)


class OutboxVaultClient:
    """Production :class:`CredentialVaultPort` implementation.

    Construction:

    * ``backend`` — :class:`VaultBackendPort` adapter for the actual
      vault store.
    * ``audit`` — :class:`CredentialAccessAuditPort` writer.
    * ``run_ref`` — opaque run identifier appended to every audit row.
    * ``clock`` — injectable callable returning a tz-aware
      :class:`datetime`. Default: :func:`datetime.now` with UTC.

    The client itself is stateless beyond its three injected
    dependencies; safe to share across requests in a single run.
    """

    def __init__(
        self,
        *,
        backend: VaultBackendPort,
        audit: CredentialAccessAuditPort,
        run_ref: Ref,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._backend = backend
        self._audit = audit
        self._run_ref = run_ref
        self._clock = clock

    def _now(self) -> datetime:
        """Defense in depth: enforce tz-aware on every clock read.
        ``LoggingCredentialAccessAuditWriter`` validates timestamps,
        but a custom audit adapter may not. Producer-side guard
        keeps replay determinism even when wired to a permissive
        audit sink (codex iter-2 minor)."""

        ts = self._clock()
        if ts.tzinfo is None or ts.utcoffset() is None:
            raise RuntimeError(
                "OutboxVaultClient.clock returned a tz-naive datetime; "
                "replay determinism requires tz-aware timestamps"
            )
        return ts

    def _audit_record(
        self,
        *,
        scope_ref_for_audit: str,
        key_for_audit: str,
        outcome: CredentialAccessOutcome,
        timestamp: datetime,
    ) -> None:
        """Write one audit row. Codex iter-3 important: any failure
        in the audit writer (network down, queue full, etc.) MUST
        be detected by the caller — the caller refuses the
        credential return when audit fails so the contract "no
        access without audit" holds end-to-end. This method does
        NOT swallow exceptions; it propagates them.
        """

        self._audit.record(
            scope_ref=scope_ref_for_audit,
            key=key_for_audit,
            outcome=outcome,
            run_ref=self._run_ref,
            timestamp=timestamp,
        )

    def get(self, *, scope_ref: str, key: str) -> CredentialValue:
        # Codex iter-3 important: validate the clock BEFORE any
        # backend call. A tz-naive clock means we cannot write a
        # replay-deterministic audit row, so refuse the access
        # before fetching any credential. ``_now()`` raises
        # RuntimeError on naive timestamps (defense in depth).
        # We compute timestamps lazily for each audit row from the
        # same clock; failing here means later audit rows would
        # also fail, so abort up front.
        pre_flight_ts = self._now()

        # Identifier shape validation. Audit the rejection BEFORE
        # raising the ValueError so operators can count
        # invalid-identifier attempts. Redacted placeholders
        # because the rejected values may carry secret-shaped
        # strings.
        if not _is_valid_identifier(scope_ref) or not _is_valid_identifier(key):
            self._audit_record(
                scope_ref_for_audit=_REDACTED_IDENT,
                key_for_audit=_REDACTED_IDENT,
                outcome=CredentialAccessOutcome.INVALID_IDENTIFIER,
                timestamp=pre_flight_ts,
            )
            # Surface a typed shape error; identifier-shape failures
            # are caller-bug not vault-fail, so don't degrade to
            # CredentialNotFoundError.
            raise ValueError(
                "scope_ref / key must match ``^[A-Z0-9_]+$`` (uppercase, "
                "digits, underscore only); rejected values redacted "
                "(see audit log for the recorded INVALID_IDENTIFIER event)"
            )

        # Audit IDs are stable hashes of the validated identifiers,
        # never the raw caller-supplied strings (codex iter-2 important).
        scope_audit = _hashed_ref(scope_ref)
        key_audit = _hashed_ref(key)

        raw: str | None
        backend_failure_kind: VaultBackendErrorKind | None = None
        unexpected_exception_seen = False
        try:
            raw = self._backend.fetch(scope_ref=scope_ref, key=key)
        except VaultBackendError as exc:
            backend_failure_kind = exc.kind
            raw = None
        except Exception:
            # Codex iter-2 important: any non-VaultBackendError
            # SDK panic must still produce one audit row and surface
            # as the canonical CredentialNotFoundError. Raise outside
            # the except block so ``__context__`` does not chain.
            unexpected_exception_seen = True
            raw = None

        # Compute the post-fetch outcome before any audit attempt
        # so we know what to record + what to raise. The credential
        # is then returned ONLY if the audit write succeeds —
        # codex iter-3 important: "no access without audit" must
        # hold even when the audit writer itself fails.
        outcome: CredentialAccessOutcome
        not_found_message: str | None
        if unexpected_exception_seen:
            outcome = CredentialAccessOutcome.INTERNAL
            not_found_message = (
                "vault backend raised an unexpected exception; "
                "treated as missing (see audit log for INTERNAL outcome)"
            )
        elif backend_failure_kind is not None:
            outcome = _BACKEND_KIND_TO_OUTCOME[backend_failure_kind]
            not_found_message = (
                "vault backend operation failed; treated as missing "
                "(scope_ref / key shapes redacted in this message; "
                "see audit log for the structured outcome)"
            )
        elif raw is None:
            outcome = CredentialAccessOutcome.NOT_FOUND
            not_found_message = (
                "credential not found in vault (scope_ref / key "
                "redacted; see audit log)"
            )
        elif not raw.strip():
            outcome = CredentialAccessOutcome.BLANK_VALUE
            not_found_message = (
                "vault returned a blank credential value; treated as "
                "missing (fail-closed for cooperative crawler)"
            )
        else:
            outcome = CredentialAccessOutcome.SUCCESS
            not_found_message = None

        # Codex iter-3 important: the post-fetch audit write may
        # itself fail (audit adapter network down, queue full,
        # disk full, etc.). If the write fails AND we have a
        # successfully fetched credential, we cannot return it —
        # that would violate "no access without audit". Refuse
        # with CredentialNotFoundError + emit a fallback
        # structured-log event so the operator sees the gap. The
        # fallback log itself does NOT carry the credential.
        post_fetch_ts = self._now()
        audit_failed = False
        try:
            self._audit_record(
                scope_ref_for_audit=scope_audit,
                key_for_audit=key_audit,
                outcome=outcome,
                timestamp=post_fetch_ts,
            )
        except Exception:
            audit_failed = True
        if audit_failed:
            # Raise OUTSIDE the except block so Python does not
            # auto-populate ``__context__`` with the audit-writer's
            # exception (which may carry adapter-specific details
            # a logging handler that walks the chain would surface).
            _logger.error(  # noqa: TRY400 — caller doesn't need our traceback
                "credential_access_audit_failed",
                scope_ref=scope_audit,
                key=key_audit,
                attempted_outcome=outcome.value,
                run_ref=self._run_ref,
                timestamp_iso=post_fetch_ts.isoformat(),
            )
            raise CredentialNotFoundError(
                "credential access audit write failed; refusing "
                "credential return (no access without audit). See "
                "structured-log fallback event ``credential_access_audit_failed``."
            ) from None

        if not_found_message is not None:
            raise CredentialNotFoundError(not_found_message)
        # Mypy: ``not_found_message is None`` implies success branch ran.
        assert raw is not None
        return CredentialValue(value=raw, scope_ref=scope_ref)


__all__ = ["OutboxVaultClient"]
