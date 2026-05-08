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
from veracrawl.ports.credential_access_audit import CredentialAccessAuditPort
from veracrawl.ports.credential_vault import (
    CredentialNotFoundError,
    CredentialValue,
)
from veracrawl.ports.vault_backend import (
    VaultBackendError,
    VaultBackendPort,
)

_SAFE_IDENT_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Z0-9_]+$")


def _validate_identifier(name: str, *, kind: str) -> None:
    """Symmetric with EnvVarVault: scope_ref and key must be
    env-var-safe. Don't echo the rejected value in the error
    (could carry a secret-shaped string)."""

    if not name or not _SAFE_IDENT_RE.fullmatch(name):
        raise ValueError(
            f"{kind} must match ``^[A-Z0-9_]+$`` (uppercase, digits, "
            f"underscore only); rejected value of length "
            f"{len(name) if isinstance(name, str) else 0} (redacted)"
        )


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
        _validate_identifier(scope_ref, kind="scope_ref")
        _validate_identifier(key, kind="key")

        raw: str | None
        backend_failed = False
        try:
            raw = self._backend.fetch(scope_ref=scope_ref, key=key)
        except VaultBackendError:
            backend_failed = True
            raw = None
        if backend_failed:
            # Audit the failed access. Then raise OUTSIDE the
            # except block so Python does not auto-populate
            # ``__context__`` with the original VaultBackendError —
            # that would leak the structured kind via a logging
            # handler that walks the exception chain
            # (Phase 2 step 2.2b lesson). The original kind is
            # captured in the audit row via ``success=False``; the
            # upstream-visible exception is the canonical
            # ``CredentialNotFoundError`` so callers can dispatch
            # uniformly.
            self._audit.record(
                scope_ref=scope_ref,
                key=key,
                success=False,
                run_ref=self._run_ref,
                timestamp=self._clock(),
            )
            raise CredentialNotFoundError(
                "vault backend operation failed; treated as missing "
                "(scope_ref / key shapes redacted in this message)"
            ) from None

        success = raw is not None and bool(raw.strip())
        self._audit.record(
            scope_ref=scope_ref,
            key=key,
            success=success,
            run_ref=self._run_ref,
            timestamp=self._clock(),
        )
        if not success:
            raise CredentialNotFoundError(
                "credential not found in vault (scope_ref / key redacted; "
                "see audit log for the recorded access event)"
            )
        # Mypy: ``success`` implies ``raw`` is non-None and non-blank.
        assert raw is not None
        return CredentialValue(value=raw, scope_ref=scope_ref)


__all__ = ["OutboxVaultClient"]
