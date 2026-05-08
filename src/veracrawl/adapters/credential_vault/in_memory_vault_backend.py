"""``InMemoryVaultBackend`` — fixture :class:`VaultBackendPort` impl.

Test / fixture backend that holds credentials in a process-local
dict. Production-mode-gated like Phase 2 step 2.1's ``EnvVarVault``
— under :class:`RuntimeMode.PRODUCTION`, every ``fetch`` call
raises :class:`ProductionRuntimeNotImplemented` so a wiring
regression cannot route production credentials through this
in-memory store.

The fixture supports two failure modes for tests:

* ``fail_with_kind`` (constructor argument): inject a
  :class:`VaultBackendErrorKind` so tests can exercise each
  failure branch of :class:`OutboxVaultClient` deterministically.
* Empty / whitespace-only entries: treated as ``None`` (NOT
  found) — symmetric with Phase 2 step 2.1's ``EnvVarVault``
  fail-closed semantics.
"""

from __future__ import annotations

from collections.abc import Mapping

from veracrawl.ports.vault_backend import (
    VaultBackendError,
    VaultBackendErrorKind,
)
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
    current_mode,
)


class InMemoryVaultBackend:
    """Fixture-only :class:`~veracrawl.ports.vault_backend.VaultBackendPort` impl.

    Construction:

    * ``credentials``: mapping of ``(scope_ref, key)`` to value.
    * ``fail_with_kind``: optional injected failure mode; if set,
      every ``fetch`` raises ``VaultBackendError(kind=fail_with_kind)``
      regardless of the credential dict contents. Used in tests to
      exercise the OutboxVaultClient's error-translation paths.
    """

    def __init__(
        self,
        *,
        credentials: Mapping[tuple[str, str], str] | None = None,
        fail_with_kind: VaultBackendErrorKind | None = None,
    ) -> None:
        self._credentials: dict[tuple[str, str], str] = (
            dict(credentials) if credentials is not None else {}
        )
        self._fail_with_kind = fail_with_kind

    def fetch(self, *, scope_ref: str, key: str) -> str | None:
        if current_mode() is RuntimeMode.PRODUCTION:
            raise ProductionRuntimeNotImplemented(
                backend="in_memory_vault_backend",
                gate="vault_backend",
            )
        if self._fail_with_kind is not None:
            raise VaultBackendError(kind=self._fail_with_kind)
        raw = self._credentials.get((scope_ref, key))
        if raw is None:
            return None
        if not raw.strip():
            # Symmetric with EnvVarVault: empty / whitespace-only
            # entries indistinguishable from misconfiguration; fail-
            # closed by returning None (the caller treats this as
            # not-found).
            return None
        return raw


__all__ = ["InMemoryVaultBackend"]
