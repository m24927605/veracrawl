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

* **2.2a**: pure-logic matcher + port. The matcher emits a
  :class:`~veracrawl.contracts.errors.CredentialScopeReason` enum
  value as the refusal class.
* **2.2b** (now landed): replaced the original free-form ``reason``
  string with a structured ``CredentialScopeReason`` enum so
  ``CredentialScopeViolation`` cannot leak even if a future caller
  pipes raw user input into the field
  (Phase 0 step 0.4 reservation pull-forward). Implementations of
  ``SessionScopePolicy`` that ship after step 2.2b must use the
  enum — free-form strings raise :class:`ValueError` at exception
  construction.
* **2.2c** (now landed): layers a runtime ReDoS defense over the
  regex matcher — the third-party ``regex`` package's per-match
  ``timeout=`` kwarg, combined with a cumulative whole-check
  deadline, bounds worst-case work on attacker-controlled URLs.
  Resolves Phase 0 step 0.3 + step 2.2a runtime-ReDoS reservations.
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
