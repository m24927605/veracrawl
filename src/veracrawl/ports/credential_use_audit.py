"""``CredentialUseAuditPort`` — HTTP-side credential audit boundary.

Phase 2 step 2.4b writes one :class:`CredentialUseRecord` row per
authorized HTTP request via this port. Distinct from
:class:`CredentialAccessAuditPort` (step 2.4a, vault-side):

* :class:`CredentialAccessAuditPort` answers "which scope was
  retrieved when, and what was the outcome?" — fires on each
  ``CredentialVaultPort.get`` call (session start / token refresh).
* :class:`CredentialUseAuditPort` answers "which HTTP request used
  the credential?" — fires on each authorized request dispatched
  through :class:`AuthorizedSessionAdapter`.

Both are part of the design.md §3.3 audit pipeline; they fire at
different rates. The two audit ports are intentionally separate:
the vault layer doesn't know the request URL / method / response
status that the use record requires.

The port is narrow — one ``record`` call per request. The body
takes a fully-validated :class:`CredentialUseRecord` (Phase 0
contract); the credential value is **never** part of the record
shape, so the port cannot leak the secret by construction.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from veracrawl.contracts.security_privacy import CredentialUseRecord


@runtime_checkable
class CredentialUseAuditPort(Protocol):
    """Per-request audit writer for authorized HTTP credential use.

    Implementations decide where the record lands (structured log,
    outbox queue, both). Phase 2 step 2.4b ships only a structured-
    log-backed default. Phase 6 wires an outbox-backed alternate
    that satisfies the same port; production deployments swap via
    wiring.

    Implementations MAY raise on failure (network down, queue full,
    disk full). The caller (``AuthorizedSessionAdapter``) handles
    failure with a fail-closed policy: if the audit write fails,
    the credential-bearing response is refused (no use without
    audit) — same contract as
    :class:`CredentialAccessAuditPort`.
    """

    def record(self, use_record: CredentialUseRecord) -> None: ...


__all__ = ["CredentialUseAuditPort"]
