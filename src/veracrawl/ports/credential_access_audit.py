"""``CredentialAccessAuditPort`` — vault-side audit boundary.

Phase 2 step 2.4a writes one audit row per credential fetch attempt
through :class:`~veracrawl.adapters.credential_vault.outbox_vault_client.OutboxVaultClient`.
The audit answers "which scope was retrieved when, and what was
the outcome?" — distinct from :class:`CredentialUseRecord` (Phase 2
step 2.4b), which answers "which HTTP request actually used the
credential". Both are part of the design.md §3.3 audit pipeline;
they fire at different rates (fetch on session start /
token-refresh; use on every authorized HTTP request).

The port is narrow — one ``record`` call per access attempt. The
body takes only non-secret fields; the credential value never
lands on the audit payload. The ``outcome`` field is a structured
enum so operational triage can distinguish ``not_found`` /
``auth_failed`` / ``backend_unreachable`` / ``internal`` /
``invalid_identifier`` without a free-form text path that would be
a leak vector (Phase 2 step 2.2b lesson).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable

from veracrawl.contracts.common import Ref


class CredentialAccessOutcome(StrEnum):
    """Structured outcome classes for a credential vault access.

    Closed enum — adapters that encounter unanticipated failures
    classify them as ``INTERNAL`` rather than inventing free-form
    outcomes. The values overlap intentionally with
    :class:`~veracrawl.ports.vault_backend.VaultBackendErrorKind`
    (NOT_FOUND / BACKEND_UNREACHABLE / AUTH_FAILED / INTERNAL) plus
    two access-side outcomes the backend never sees:

    * ``SUCCESS`` — credential retrieved successfully.
    * ``BLANK_VALUE`` — backend returned an empty / whitespace-only
      value; treated as not-found per the fail-closed policy.
    * ``INVALID_IDENTIFIER`` — caller passed a scope_ref / key
      that failed shape validation; backend never queried.
    """

    SUCCESS = "success"
    NOT_FOUND = "not_found"
    BACKEND_UNREACHABLE = "backend_unreachable"
    AUTH_FAILED = "auth_failed"
    INTERNAL = "internal"
    BLANK_VALUE = "blank_value"
    INVALID_IDENTIFIER = "invalid_identifier"


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

    ``scope_ref`` and ``key`` may be ``"[REDACTED]"`` placeholders
    when the original caller-supplied identifiers failed shape
    validation. The audit pipeline can still correlate by
    ``timestamp`` + ``run_ref`` + ``outcome=INVALID_IDENTIFIER``.

    The credential value is **never** passed to ``record``. The
    audit row exists to count + correlate accesses, not to store
    the secret.
    """

    def record(
        self,
        *,
        scope_ref: str,
        key: str,
        outcome: CredentialAccessOutcome,
        run_ref: Ref,
        timestamp: datetime,
    ) -> None: ...


__all__ = ["CredentialAccessAuditPort", "CredentialAccessOutcome"]
