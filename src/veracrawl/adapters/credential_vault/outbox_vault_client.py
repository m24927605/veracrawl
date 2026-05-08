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

    def get(self, *, scope_ref: str, key: str) -> CredentialValue:
        # Identifier shape validation. Audit the rejection with
        # redacted placeholders BEFORE raising — operators want
        # to count invalid-identifier attempts (security-relevant
        # signal of a misconfiguration / abuse) without leaking
        # the rejected value.
        if not _is_valid_identifier(scope_ref) or not _is_valid_identifier(key):
            self._audit.record(
                scope_ref=_REDACTED_IDENT,
                key=_REDACTED_IDENT,
                outcome=CredentialAccessOutcome.INVALID_IDENTIFIER,
                run_ref=self._run_ref,
                timestamp=self._clock(),
            )
            # Surface a typed shape error; identifier-shape failures
            # are caller-bug not vault-fail, so don't degrade to
            # CredentialNotFoundError.
            raise ValueError(
                "scope_ref / key must match ``^[A-Z0-9_]+$`` (uppercase, "
                "digits, underscore only); rejected values redacted "
                "(see audit log for the recorded INVALID_IDENTIFIER event)"
            )

        raw: str | None
        backend_failure_kind: VaultBackendErrorKind | None = None
        try:
            raw = self._backend.fetch(scope_ref=scope_ref, key=key)
        except VaultBackendError as exc:
            backend_failure_kind = exc.kind
            raw = None
        if backend_failure_kind is not None:
            # Audit + raise OUTSIDE the except block so Python does
            # not auto-populate ``__context__`` with the original
            # VaultBackendError (Phase 2 step 2.2b lesson). The
            # structured backend kind IS preserved on the audit row
            # via the ``outcome`` field; the upstream-visible
            # exception is the canonical CredentialNotFoundError so
            # callers can dispatch uniformly.
            self._audit.record(
                scope_ref=scope_ref,
                key=key,
                outcome=_BACKEND_KIND_TO_OUTCOME[backend_failure_kind],
                run_ref=self._run_ref,
                timestamp=self._clock(),
            )
            raise CredentialNotFoundError(
                "vault backend operation failed; treated as missing "
                "(scope_ref / key shapes redacted in this message; "
                "see audit log for the structured outcome)"
            ) from None

        if raw is None:
            self._audit.record(
                scope_ref=scope_ref,
                key=key,
                outcome=CredentialAccessOutcome.NOT_FOUND,
                run_ref=self._run_ref,
                timestamp=self._clock(),
            )
            raise CredentialNotFoundError(
                "credential not found in vault (scope_ref / key "
                "redacted; see audit log)"
            )
        if not raw.strip():
            self._audit.record(
                scope_ref=scope_ref,
                key=key,
                outcome=CredentialAccessOutcome.BLANK_VALUE,
                run_ref=self._run_ref,
                timestamp=self._clock(),
            )
            raise CredentialNotFoundError(
                "vault returned a blank credential value; treated as "
                "missing (fail-closed for cooperative crawler)"
            )
        self._audit.record(
            scope_ref=scope_ref,
            key=key,
            outcome=CredentialAccessOutcome.SUCCESS,
            run_ref=self._run_ref,
            timestamp=self._clock(),
        )
        return CredentialValue(value=raw, scope_ref=scope_ref)


__all__ = ["OutboxVaultClient"]
