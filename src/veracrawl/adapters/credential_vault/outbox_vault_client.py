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
    ) -> None:
        self._audit.record(
            scope_ref=scope_ref_for_audit,
            key=key_for_audit,
            outcome=outcome,
            run_ref=self._run_ref,
            timestamp=self._now(),
        )

    def get(self, *, scope_ref: str, key: str) -> CredentialValue:
        # Identifier shape validation. Audit the rejection with
        # redacted placeholders BEFORE raising — operators want
        # to count invalid-identifier attempts (security-relevant
        # signal of a misconfiguration / abuse) without leaking
        # the rejected value.
        if not _is_valid_identifier(scope_ref) or not _is_valid_identifier(key):
            self._audit_record(
                scope_ref_for_audit=_REDACTED_IDENT,
                key_for_audit=_REDACTED_IDENT,
                outcome=CredentialAccessOutcome.INVALID_IDENTIFIER,
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
        # never the raw caller-supplied strings — even shape-valid
        # uppercase tokens may be secret-shaped (codex iter-2
        # important).
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
            # (e.g., a misbehaving SDK that raises ``RuntimeError``
            # / ``TimeoutError`` / etc. instead of the typed
            # backend exception) must still produce one audit row
            # and surface as the canonical CredentialNotFoundError.
            # Catch + flag here; raise OUTSIDE the except block so
            # ``__context__`` does not chain (defense in depth
            # against logging handlers that walk the chain).
            unexpected_exception_seen = True
            raw = None
        if unexpected_exception_seen:
            self._audit_record(
                scope_ref_for_audit=scope_audit,
                key_for_audit=key_audit,
                outcome=CredentialAccessOutcome.INTERNAL,
            )
            raise CredentialNotFoundError(
                "vault backend raised an unexpected exception; "
                "treated as missing (see audit log for INTERNAL outcome)"
            ) from None
        if backend_failure_kind is not None:
            # Audit + raise OUTSIDE the except block so Python does
            # not auto-populate ``__context__`` with the original
            # VaultBackendError (Phase 2 step 2.2b lesson). The
            # structured backend kind IS preserved on the audit row
            # via the ``outcome`` field; the upstream-visible
            # exception is the canonical CredentialNotFoundError so
            # callers can dispatch uniformly.
            self._audit_record(
                scope_ref_for_audit=scope_audit,
                key_for_audit=key_audit,
                outcome=_BACKEND_KIND_TO_OUTCOME[backend_failure_kind],
            )
            raise CredentialNotFoundError(
                "vault backend operation failed; treated as missing "
                "(scope_ref / key shapes redacted in this message; "
                "see audit log for the structured outcome)"
            ) from None

        if raw is None:
            self._audit_record(
                scope_ref_for_audit=scope_audit,
                key_for_audit=key_audit,
                outcome=CredentialAccessOutcome.NOT_FOUND,
            )
            raise CredentialNotFoundError(
                "credential not found in vault (scope_ref / key "
                "redacted; see audit log)"
            )
        if not raw.strip():
            self._audit_record(
                scope_ref_for_audit=scope_audit,
                key_for_audit=key_audit,
                outcome=CredentialAccessOutcome.BLANK_VALUE,
            )
            raise CredentialNotFoundError(
                "vault returned a blank credential value; treated as "
                "missing (fail-closed for cooperative crawler)"
            )
        self._audit_record(
            scope_ref_for_audit=scope_audit,
            key_for_audit=key_audit,
            outcome=CredentialAccessOutcome.SUCCESS,
        )
        return CredentialValue(value=raw, scope_ref=scope_ref)


__all__ = ["OutboxVaultClient"]
