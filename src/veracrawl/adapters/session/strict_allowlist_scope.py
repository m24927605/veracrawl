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
:class:`CredentialScopeReason` of ``ORIGIN_NOT_ALLOWED`` /
``ROUTE_NOT_ALLOWED`` / ``METHOD_NOT_ALLOWED`` / ``EXPIRED``. The
exception sanitizes its public attributes at the boundary, so
refusal logging / telemetry cannot leak credentials or PII even if
a caller passes a credentialed URL.

What is **out of scope** for 2.2a:

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

from veracrawl.contracts.errors import CredentialScopeReason, CredentialScopeViolation
from veracrawl.contracts.security_privacy import CredentialScope

_DEFAULT_PORTS: Final[dict[str, int]] = {"http": 80, "https": 443}

# Hard cap on the route path length the matcher will run against.
# Combined with the contract-layer nested-quantifier AST guard
# (``_validate_route_pattern``), this bounds the maximum work a
# single ``re.match`` call can do — even a degenerate pattern that
# slipped past the AST guard cannot wedge the matcher on an
# attacker-controlled URL because the input is short.
#
# This is intentionally not a *complete* ReDoS defense: contract-valid
# patterns with ambiguous alternations can still backtrack on much
# shorter inputs. A per-match timeout (re2 engine, regex-module
# ``timeout=`` kwarg, or signal.alarm in a worker) is required to
# fully close that gap and lives in **step 2.2c** of the second-
# reassessment plan split. Pulling it forward into 2.2a was
# considered and rejected because it adds a third-party dependency
# (``re2``/``regex``) or a worker-pool integration that is a meaningful
# scope expansion for an atomic step. The 4 KiB cap + AST guard is
# the floor that ships in 2.2a so the credential gate has *some*
# runtime defense, with step 2.2c upgrading that floor to a hard
# bound. See STATUS.md "v2 phase 2 step 2.2a reservations".
_MAX_ROUTE_LENGTH: Final[int] = 4096


def _safe_urlsplit(
    value: str,
) -> tuple[str, str | None, int | None, str, bool] | None:
    """Defensive ``urlsplit`` that returns
    ``(scheme, host, port, path, has_userinfo)`` or ``None`` if any
    access raises.

    ``urlsplit`` itself rarely raises, but reading ``.port`` raises
    ``ValueError`` for malformed authorities (``host:bad`` port,
    out-of-range ``host:99999``, malformed IPv6 brackets). The
    runtime policy promises every refusal is a typed
    :class:`CredentialScopeViolation` — never a plain
    :class:`ValueError` — so swallow parse failures here and let
    the caller surface them as ``origin_not_allowed``.
    """

    try:
        parts = urlsplit(value)
    except ValueError:
        return None
    try:
        port = parts.port
    except ValueError:
        # Malformed authority (e.g., ``host:bad`` port or
        # ``host:99999`` out-of-range).
        return None
    # Detect userinfo structurally from the authority delimiter
    # rather than truthiness of ``parts.username`` / ``parts.password``.
    # Empty userinfo shapes (``https://@host/...`` and
    # ``https://:@host/...``) carry an ``@`` delimiter but parse to
    # empty strings, so the truthiness check would miss them and let
    # an attacker land at the credential gate with userinfo present
    # in the wire URL. Rsplit so a literal ``@`` inside a path-only
    # value (post ``//``) cannot false-positive.
    netloc = parts.netloc
    has_userinfo = "@" in netloc
    return parts.scheme, parts.hostname, port, parts.path, has_userinfo


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

    parsed = _safe_urlsplit(request_url)
    if parsed is None:
        return None
    scheme, host, port, _path, has_userinfo = parsed
    if scheme not in {"http", "https"}:
        return None
    if not host:
        return None
    if has_userinfo:
        # Refuse credential-bearing URLs at the origin gate. A
        # ``user:pass@host`` URL would otherwise land in the
        # ``Authorization`` builder alongside the vault credential
        # and create ambiguous auth precedence + audit-log
        # surprises. Treat as ``origin_not_allowed``.
        return None
    host = host.lower()
    if port is not None and port == _DEFAULT_PORTS.get(scheme):
        port = None
    if port is None:
        return f"{scheme}://{host}"
    return f"{scheme}://{host}:{port}"


def _normalize_allowed_origin(origin: str) -> str:
    """Normalize an ``allowed_origin`` from the scope.

    The contract layer (``_is_valid_origin``) already validates the
    shape, so a malformed value here would be a contract bug — but
    the parse is defensive anyway so a future contract change cannot
    crash the runtime path.
    """

    parsed = _safe_urlsplit(origin)
    if (
        parsed is None
        or parsed[0] not in {"http", "https"}
        or not parsed[1]
        or parsed[4]  # has_userinfo — must never appear in an allowed origin
    ):
        # Contract layer rejects this shape; reaching here means a
        # ``CredentialScope`` was constructed bypassing
        # validation (e.g., a contract regression or an unsafe
        # ``model_construct``). Fail loudly so the issue surfaces
        # as an internal invariant violation rather than degrading
        # silently into a confusing ``origin_not_allowed`` refusal.
        # Userinfo in an allowed origin is especially bad: the
        # request normalizer would strip it, and the policy would
        # then authorize requests under that origin even though
        # the scope nominally restricted them to a credentialed
        # ``user:pass@host`` (which the contract layer rejects).
        raise RuntimeError(
            "StrictAllowlistScope: scope.allowed_origins contains a value "
            f"that is not a valid bare http(s) origin; len={len(origin)} "
            "(contract layer should have rejected this — looks like a "
            "validation bypass)"
        )
    scheme, host, port, _path, _userinfo = parsed
    assert host is not None  # narrowed by the early-return above
    host = host.lower()
    if port is not None and port == _DEFAULT_PORTS.get(scheme):
        port = None
    if port is None:
        return f"{scheme}://{host}"
    return f"{scheme}://{host}:{port}"


def _route_of(request_url: str) -> str:
    """Return the URL's path (no query / fragment).

    The ``CredentialScope`` route grammar (Phase 0) is
    path-anchored — ``allowed_route_patterns`` always start with
    ``/``. Comparing the bare path keeps the matcher independent of
    query-string ordering and fragment identifiers (which a request
    builder can vary without affecting whether the credential is in
    scope for the resource).
    """

    parsed = _safe_urlsplit(request_url)
    if parsed is None:
        return ""
    return parsed[3] or "/"


def _route_too_long(route: str) -> bool:
    return len(route) > _MAX_ROUTE_LENGTH


# Tokens that make a path ambiguous between what the matcher sees
# and what a downstream client / proxy / server normalizes the path
# to. ``/v1/items/../admin`` would match a regex anchored at
# ``/v1/items`` but reach ``/admin`` after upstream normalization;
# the credential-bearing gate must refuse rather than approve under
# that ambiguity.
_AMBIGUOUS_PATH_TOKENS: Final[tuple[str, ...]] = (
    "%2f",  # encoded slash
    "%2F",
    "%5c",  # encoded backslash
    "%5C",
    "%2e",  # encoded dot — combines with another dot or with `/` to bypass dot-segment refusal
    "%2E",
    "%00",  # NUL — short-circuits some C clients
    "\\",  # raw backslash
)
_DOT_SEGMENTS: Final[frozenset[str]] = frozenset({".", ".."})


def _route_is_ambiguous(route: str) -> bool:
    """Return ``True`` for paths that should be refused before regex
    match because downstream normalization could move them outside
    the matched scope.
    """

    if any(token in route for token in _AMBIGUOUS_PATH_TOKENS):
        return True
    return any(segment in _DOT_SEGMENTS for segment in route.split("/"))


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
                    reason=CredentialScopeReason.EXPIRED,
                )

        normalized_method = method.upper()
        if normalized_method not in scope.allowed_methods:
            self._raise(
                scope=scope,
                request_url=request_url,
                method=method,
                reason=CredentialScopeReason.METHOD_NOT_ALLOWED,
            )

        request_origin = _normalize_origin(request_url)
        allowed_origins = {_normalize_allowed_origin(o) for o in scope.allowed_origins}
        if request_origin is None or request_origin not in allowed_origins:
            self._raise(
                scope=scope,
                request_url=request_url,
                method=method,
                reason=CredentialScopeReason.ORIGIN_NOT_ALLOWED,
            )

        route = _route_of(request_url)
        if _route_is_ambiguous(route):
            # Refuse paths whose runtime form differs from what the
            # regex matches: ``/v1/items/../admin`` would match a
            # ``^/v1/items`` regex literally but reach ``/admin``
            # after the upstream normalizes dot-segments. Same risk
            # for percent-encoded slashes / backslashes / NUL —
            # downstream normalization can move the request outside
            # the matched scope.
            self._raise(
                scope=scope,
                request_url=request_url,
                method=method,
                reason=CredentialScopeReason.ROUTE_NOT_ALLOWED,
            )
        if _route_too_long(route):
            # Bound the worst-case work the regex engine will do on
            # an attacker-controlled URL. The contract-layer AST
            # guard already refuses pathological *patterns*, but
            # combining well-formed patterns with a hostile input
            # of unbounded length is still a runtime concern. Step
            # 2.2c will replace this with a per-match timeout / re2
            # / glob-only DSL.
            self._raise(
                scope=scope,
                request_url=request_url,
                method=method,
                reason=CredentialScopeReason.ROUTE_NOT_ALLOWED,
            )
        for pattern in scope.allowed_route_patterns:
            # ``re.match`` anchors at position 0 — required because
            # ``re.search`` would let ``/v1/items`` match
            # ``/prefix/v1/items``, defeating the contract's
            # path-anchored grammar (``allowed_route_pattern`` must
            # start with ``/`` or ``^/``). Patterns that already
            # carry an explicit ``^`` work identically under
            # ``re.match``.
            if re.match(pattern, route) is not None:
                return None
        self._raise(
            scope=scope,
            request_url=request_url,
            method=method,
            reason=CredentialScopeReason.ROUTE_NOT_ALLOWED,
        )

    @staticmethod
    def _raise(
        *,
        scope: CredentialScope,
        request_url: str,
        method: str,
        reason: CredentialScopeReason,
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
