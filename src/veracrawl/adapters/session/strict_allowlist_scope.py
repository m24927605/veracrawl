"""``StrictAllowlistScope`` — default ``SessionScopePolicy`` impl.

Phase 2 step 2.2a runtime enforcement of ``CredentialScope``: a
credential-bearing request is allowed iff *all* of the following
hold:

1. ``request_url`` parses to an ``http(s)`` URL whose origin
   (``scheme://host[:port]``, lower-cased host, default ports
   stripped) appears in ``scope.allowed_origins``.
2. The URL's path component (without query / fragment) matches at
   least one regex in ``scope.allowed_route_patterns``.
3. ``method`` (upper-cased) appears in ``scope.allowed_methods``.
4. ``scope.expires_at`` (if set) is strictly later than ``now``.

Any violation raises :class:`CredentialScopeViolation` with a
``reason`` of ``origin_not_allowed`` / ``route_not_allowed`` /
``method_not_allowed`` / ``expired``. The exception sanitizes its
public attributes at the boundary, so refusal logging / telemetry
cannot leak credentials or PII even if a caller passes a
credentialed URL.

What is **out of scope** for 2.2a:

* The refusal ``reason`` is currently free-form text. Step 2.2b
  will replace it with a structured enum so a future caller
  cannot leak by piping raw user input into the field.
* The matcher uses Python's ``re`` engine, which has no per-match
  timeout. The contract layer's nested-quantifier AST guard
  (``_validate_route_pattern``) refuses pathological *patterns*
  before they land in a ``CredentialScope``. Step 2.2c adds a
  runtime ReDoS defense (per-match timeout / ``re2`` / glob-only
  DSL) so even a well-formed pattern cannot be wedged by an
  attacker-controlled URL.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Final
from urllib.parse import urlsplit

from veracrawl.contracts.errors import CredentialScopeViolation
from veracrawl.contracts.security_privacy import CredentialScope

_DEFAULT_PORTS: Final[dict[str, int]] = {"http": 80, "https": 443}


def _normalize_origin(request_url: str) -> str | None:
    """Return ``scheme://host[:port]`` with default ports stripped, or
    ``None`` if the URL cannot be parsed as ``http(s)://host``.

    Used to compare a request URL's origin against
    ``scope.allowed_origins`` (which the contract layer already
    constrained to bare ``http(s)`` origins). A return of ``None``
    surfaces as ``origin_not_allowed`` at the policy boundary —
    the policy never raises ``ValueError`` on a malformed URL
    because the caller treats every refusal as a typed scope event.
    """

    parts = urlsplit(request_url)
    if parts.scheme not in {"http", "https"}:
        return None
    host = parts.hostname
    if not host:
        return None
    host = host.lower()
    port = parts.port
    if port is not None and port == _DEFAULT_PORTS.get(parts.scheme):
        port = None
    if port is None:
        return f"{parts.scheme}://{host}"
    return f"{parts.scheme}://{host}:{port}"


def _normalize_allowed_origin(origin: str) -> str:
    parts = urlsplit(origin)
    host = (parts.hostname or "").lower()
    port = parts.port
    if port is not None and port == _DEFAULT_PORTS.get(parts.scheme):
        port = None
    if port is None:
        return f"{parts.scheme}://{host}"
    return f"{parts.scheme}://{host}:{port}"


def _route_of(request_url: str) -> str:
    """Return the URL's path (no query / fragment).

    The ``CredentialScope`` route grammar (Phase 0) is
    path-anchored — ``allowed_route_patterns`` always start with
    ``/``. Comparing the bare path keeps the matcher independent of
    query-string ordering and fragment identifiers (which a request
    builder can vary without affecting whether the credential is in
    scope for the resource).
    """

    parts = urlsplit(request_url)
    return parts.path or "/"


class StrictAllowlistScope:
    """Default ``SessionScopePolicy``: literal allowlist enforcement.

    Stateless — the same instance is safe to share across runs and
    threads. The class predicates do no I/O and depend only on the
    arguments to :meth:`check` plus an injectable ``now``.
    """

    def check(
        self,
        scope: CredentialScope,
        *,
        request_url: str,
        method: str,
        now: datetime | None = None,
    ) -> None:
        # Expiry first: a stale scope must refuse before any URL
        # comparison so a leaked-after-expiry scope cannot be used
        # against a target that "happens to match" the allowlist.
        if scope.expires_at is not None:
            current = now if now is not None else datetime.now(UTC)
            if current.tzinfo is None:
                # The contract layer pins ``expires_at`` to a tz-aware
                # value; reject a tz-naive ``now`` rather than do an
                # implicit assume-UTC that would silently misread
                # ``aware vs naive`` differences as scope refusals.
                raise ValueError("now must be timezone-aware")
            if current >= scope.expires_at:
                self._raise(
                    scope=scope,
                    request_url=request_url,
                    method=method,
                    reason="expired",
                )

        normalized_method = method.upper()
        if normalized_method not in scope.allowed_methods:
            self._raise(
                scope=scope,
                request_url=request_url,
                method=method,
                reason="method_not_allowed",
            )

        request_origin = _normalize_origin(request_url)
        allowed_origins = {_normalize_allowed_origin(o) for o in scope.allowed_origins}
        if request_origin is None or request_origin not in allowed_origins:
            self._raise(
                scope=scope,
                request_url=request_url,
                method=method,
                reason="origin_not_allowed",
            )

        route = _route_of(request_url)
        for pattern in scope.allowed_route_patterns:
            if re.search(pattern, route) is not None:
                return None
        self._raise(
            scope=scope,
            request_url=request_url,
            method=method,
            reason="route_not_allowed",
        )

    @staticmethod
    def _raise(
        *,
        scope: CredentialScope,
        request_url: str,
        method: str,
        reason: str,
    ) -> None:
        # The exception sanitizes ``scope_ref`` / ``requested_origin``
        # / ``requested_route`` / ``requested_method`` / ``reason``
        # at the boundary (Phase 0 step 0.4): ``_redact_url`` keeps
        # scheme + host + path (drops query / fragment / userinfo),
        # ``_redact_route`` keeps path only. Pass the request URL
        # to ``requested_origin`` so operators get scheme+host+path
        # for triage, and the bare path to ``requested_route`` so
        # the route-only field is path-anchored as the contract
        # documents.
        raise CredentialScopeViolation(
            scope_ref=scope.id,
            requested_origin=request_url,
            requested_route=_route_of(request_url),
            requested_method=method,
            reason=reason,
        )


__all__ = ["StrictAllowlistScope"]
