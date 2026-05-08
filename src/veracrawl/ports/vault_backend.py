"""``VaultBackendPort`` — outbound interface to the actual vault.

Phase 2 step 2.4a wires the production credential path:
:class:`~veracrawl.adapters.credential_vault.outbox_vault_client.OutboxVaultClient`
implements :class:`~veracrawl.ports.credential_vault.CredentialVaultPort`
and delegates the actual fetch to a backend adapter implementing
this port. Real backends (HashiCorp Vault / AWS Secrets Manager /
customer-supplied) plug in via the wiring layer; Phase 2 ships
only the port + an in-memory fixture for tests.

Failure surface uses a structured enum (``VaultBackendErrorKind``)
rather than free-form text — the same lesson Phase 2 step 2.2b
applied to ``CredentialScopeViolation``: free-form reason fields
on exceptions become leak vectors via ``__dict__`` /
``logging.exception()``.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol, runtime_checkable

from veracrawl.contracts.errors import VeraCrawlError

_SAFE_BACKEND_KIND_VALUES: frozenset[str]  # populated below


class VaultBackendErrorKind(StrEnum):
    """Structured refusal classes for ``VaultBackendError``.

    Producers (vault adapters) MUST classify backend failures as one
    of these. The enum is closed: a backend that returns an
    unanticipated error must classify it as ``INTERNAL`` rather than
    inventing a free-form reason.
    """

    NOT_FOUND = "not_found"
    BACKEND_UNREACHABLE = "backend_unreachable"
    AUTH_FAILED = "auth_failed"
    INTERNAL = "internal"


_SAFE_BACKEND_KIND_VALUES = frozenset(member.value for member in VaultBackendErrorKind)


class VaultBackendError(VeraCrawlError):
    """Raised by a :class:`VaultBackendPort` adapter when fetching a
    credential fails for a non-not-found reason.

    The exception sanitizes its public attributes at the boundary:

    * ``kind`` — :class:`VaultBackendErrorKind` enum (structured).
    * No raw scope_ref / key on the public attribute surface — the
      caller is the orchestrator which already has those in scope;
      storing them on the exception adds nothing for triage and
      creates a ``__dict__`` leak vector for the underlying vault
      adapter that may have classified the keys with confidential
      naming conventions.

    The exception is a :class:`VeraCrawlError` (not a
    :class:`PolicyViolation`) — vault backend failures are
    operational, not policy refusals.
    """

    def __init__(self, *, kind: VaultBackendErrorKind | str) -> None:
        if isinstance(kind, VaultBackendErrorKind):
            self.kind: VaultBackendErrorKind = kind
        else:
            valid = isinstance(kind, str) and kind in _SAFE_BACKEND_KIND_VALUES
            if not valid:
                raise ValueError(
                    "VaultBackendError.kind must be a VaultBackendErrorKind "
                    "enum value (or its string form); got an unknown value (redacted)"
                ) from None
            self.kind = VaultBackendErrorKind(kind)
        super().__init__(f"vault backend operation failed: {self.kind.value}")


@runtime_checkable
class VaultBackendPort(Protocol):
    """Outbound port for the actual credential backend.

    Implementations talk to HashiCorp Vault / AWS Secrets Manager /
    a customer-supplied store. The port surface is intentionally
    narrow — fetch one credential at a time, no streaming, no
    bulk operations.

    ``scope_ref`` and ``key`` shape conform to
    :class:`~veracrawl.ports.credential_vault.CredentialValue`'s
    ``^[A-Z0-9_]+$`` env-var-safe regex (Phase 2 step 2.1
    contract). The port itself does NOT re-validate — the caller
    (``OutboxVaultClient``) validates before delegating, and the
    ``CredentialValue`` constructor revalidates at wrap time.
    """

    def fetch(self, *, scope_ref: str, key: str) -> str | None:
        """Return the credential value, or ``None`` if not found.

        Raises :class:`VaultBackendError` for any non-not-found
        failure (network unreachable, backend auth failed, generic
        backend error). Never raises plain :class:`ValueError` /
        :class:`KeyError` — the caller treats every failure as a
        typed event.
        """


__all__ = [
    "VaultBackendError",
    "VaultBackendErrorKind",
    "VaultBackendPort",
]
