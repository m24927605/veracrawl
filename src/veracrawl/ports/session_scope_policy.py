"""``SessionScopePolicy`` — runtime enforcement of ``CredentialScope``.

Phase 2 step 2.2a introduces the runtime check that every
credential-bearing request runs through before the
``AuthorizedSessionAdapter`` (step 2.4) attaches a credential. The
contract layer (Phase 0 step 0.3 / 0.4) already pinned
``CredentialScope`` shape (origin / route pattern / method / expiry)
and the typed refusal exception ``CredentialScopeViolation``. This
step wires the runtime path:

* :class:`SessionScopePolicy` — Protocol with a single
  :meth:`check` method that returns ``None`` on allow and raises
  :class:`~veracrawl.contracts.errors.CredentialScopeViolation` on
  refuse. The exception itself sanitizes its public attributes
  (Phase 0 step 0.4) so the runtime path doesn't have to
  re-implement redaction at every refusal site.
* :class:`~veracrawl.adapters.session.strict_allowlist_scope.StrictAllowlistScope`
  (step 2.2a) — the default implementation that enforces the
  allowlist literally: origin must appear in
  ``scope.allowed_origins``, request path must regex-match at least
  one ``scope.allowed_route_patterns``, method must appear in
  ``scope.allowed_methods``, and (if set) ``scope.expires_at`` must
  not have lapsed when ``check`` runs.

What lives in step 2.2a vs later sub-steps:

* **2.2a (this step)**: pure-logic matcher + port. No structured
  refusal-reason redesign and no runtime ReDoS hardening — the
  free-form ``reason`` string carries the refusal class
  (``origin_not_allowed`` / ``route_not_allowed`` /
  ``method_not_allowed`` / ``expired``) and ``CredentialScopeViolation``
  redacts it at the exception boundary.
* **2.2b**: replaces the free-form ``reason`` with a structured
  enum so ``CredentialScopeViolation`` cannot leak even if a future
  caller pipes raw user input into the field
  (Phase 0 step 0.4 reservation pull-forward).
* **2.2c**: layers a runtime ReDoS defense (per-match timeout /
  ``re2`` engine / glob-only DSL) over the regex matcher so an
  attacker-controlled URL cannot wedge the matcher even though
  the AST guard already refuses pathological *patterns*
  (Phase 0 step 0.3 reservation pull-forward).
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from veracrawl.contracts.security_privacy import CredentialScope


@runtime_checkable
class SessionScopePolicy(Protocol):
    """Hexagonal port for credential-scope enforcement.

    A single method, ``check``, that consumes a ``CredentialScope``
    plus the request triple ``(request_url, method)`` and either
    returns ``None`` (request is in scope) or raises
    :class:`~veracrawl.contracts.errors.CredentialScopeViolation`
    (request is out of scope). ``now`` is injectable so tests can
    pin the clock; production passes ``datetime.now(UTC)`` (or
    relies on the default ``None``, which the implementation
    resolves via ``datetime.now(UTC)``).
    """

    def check(
        self,
        scope: CredentialScope,
        *,
        request_url: str,
        method: str,
        now: datetime | None = None,
    ) -> None:
        """Allow or refuse the request.

        Allow path is silent (returns ``None``). Refuse path raises
        :class:`~veracrawl.contracts.errors.CredentialScopeViolation`
        with a sanitized ``scope_ref`` / ``requested_origin`` /
        ``requested_route`` / ``requested_method`` / ``reason``.

        ``request_url`` must be a full URL (``http(s)://host[:port]/path``).
        Implementations may reject malformed URLs as ``origin_not_allowed``
        (the canonical refusal class for "could not extract a comparable
        origin from the request"); they must not raise plain
        :class:`ValueError` on a malformed URL because the calling code
        treats every refusal as a typed scope event.
        """


__all__ = ["SessionScopePolicy"]
