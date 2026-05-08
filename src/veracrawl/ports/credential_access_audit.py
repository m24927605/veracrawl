"""``CredentialAccessAuditPort`` — vault-side audit boundary.

Phase 2 step 2.4a writes one audit row per credential fetch
through :class:`~veracrawl.adapters.credential_vault.outbox_vault_client.OutboxVaultClient`.
The audit answers "which scope was retrieved when, and did it
succeed?" — distinct from :class:`CredentialUseRecord` (Phase 2
step 2.4b), which answers "which HTTP request actually used the
credential". Both are part of the design.md §3.3 audit pipeline;
they fire at different rates (fetch on session start /
token-refresh; use on every authorized HTTP request).

The port is narrow — one ``record`` call per access. The body
takes only non-secret fields; the credential value never lands
on the audit payload.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from veracrawl.contracts.common import Ref


@runtime_checkable
class CredentialAccessAuditPort(Protocol):
    """Per-access audit writer for credential vault operations.

    Implementations decide where the audit lands (structured-log,
    outbox queue, both). The port itself does not specify the
    persistence shape — the caller (``OutboxVaultClient``) hands
    over fields and lets the adapter decide. Phase 6 wires a
    real outbox-backed implementation; Phase 2 ships only a
    structured-log-backed default.

    ``timestamp`` is required tz-aware (replay determinism, Phase 0
    §3.3 invariant). ``run_ref`` is the run identifier; the
    audit pipeline correlates by run_ref + scope_ref.

    The credential value is **never** passed to ``record`` — only
    the success boolean. The audit row exists to count + correlate
    accesses, not to store the secret.
    """

    def record(
        self,
        *,
        scope_ref: str,
        key: str,
        success: bool,
        run_ref: Ref,
        timestamp: datetime,
    ) -> None: ...


__all__ = ["CredentialAccessAuditPort"]
