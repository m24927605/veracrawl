"""``CookieJarPort`` — per-run / per-origin cookie store.

Phase 1 step 1.5 deliverable (design.md §4 Phase 1):

    Cookie jar scoped per-run and per-origin; do not leak between
    runs or across origins.

Surface (caller-facing):

* :meth:`CookieJarPort.cookies_for` returns a ``{name: value}``
  dict suitable for the outgoing ``Cookie`` header for a request
  to ``url`` under ``run_ref``. Empty dict when no cookies apply.
* :meth:`CookieJarPort.accept_set_cookie` parses one ``Set-Cookie``
  header value and stores the cookie under ``(run_ref, origin)``.
  Same call shape regardless of whether the cookie carries
  ``Domain=`` / ``Path=`` / ``Max-Age=`` attributes.
* :meth:`CookieJarPort.cookies_in_jar` returns the in-jar cookies
  as a list (test / observability helper).
* :meth:`CookieJarPort.clear_run` releases all cookies for a run
  on completion — prevents cross-run leakage at the lifecycle
  boundary (the run scope alone is necessary but not sufficient
  if the jar is reused; clearing on completion is the
  belt-and-braces guard).

Scope rules (production default):

1. **Per-run isolation**: cookies set during ``run_a`` are never
   sent to a request under ``run_b``, even when the URL host
   matches. The framework wraps ``cookies_for`` with the active
   ``run_ref``; cross-run reuse is impossible at the port surface.
2. **Per-origin scope**: a cookie set under ``https://a.example``
   is only sent to ``https://a.example`` (and not to
   ``https://b.example``). For step 1.5 we ignore the
   ``Domain=`` cookie attribute — broader subdomain scope is
   Phase 2 / Phase 6 territory because it interacts with the
   credential vault and authorized session model.
3. **Path matching**: a cookie's ``Path=`` attribute is honored
   per RFC 6265 §5.4.

The framework default :class:`NoopCookieJar` always returns an
empty dict and discards every ``accept_set_cookie`` so existing
tests pass without configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class CookieRecord:
    """A stored cookie as observed by the jar.

    Attributes:
        name: Cookie name.
        value: Cookie value.
        origin: Canonical origin (``scheme://host[:port]``) the
            cookie was set under.
        path: Path scope (default ``/``).
        expires_epoch: ``Expires`` / ``Max-Age`` resolved to a
            wall-clock epoch in seconds, or ``None`` for session
            cookies (cleared at run boundary).
        secure: ``Secure`` attribute — when ``True`` the cookie
            only ships on ``https`` requests.
        http_only: ``HttpOnly`` attribute (informational; the jar
            ships cookies on HTTP-API requests too).
    """

    name: str
    value: str
    origin: str
    path: str = "/"
    expires_epoch: float | None = None
    secure: bool = False
    http_only: bool = False


@dataclass
class CookieJarSnapshot:
    """A point-in-time view of the jar's cookies.

    Returned by :meth:`CookieJarPort.cookies_in_jar` for tests /
    observability. Mutating the snapshot does not mutate the jar.

    Codex iter-3 important: cookie values are credentials; the
    snapshot returned to non-test observability surfaces should
    NOT carry raw values. Use :meth:`redacted` to obtain a copy
    where each cookie's ``value`` is replaced with ``<redacted>``.
    Tests that need to assert on raw values use the snapshot as
    returned by the jar (which keeps values for backward
    compatibility with the existing test surface — the burden of
    keeping raw cookie values out of audit / observability sinks
    falls on the integrator, who should call ``redacted()``).
    """

    cookies: list[CookieRecord] = field(default_factory=list)

    def redacted(self) -> CookieJarSnapshot:
        """Return a copy with every cookie's value replaced.

        Use for any non-test observability surface (audit logs,
        operator dashboards, replay records) that should not
        carry credential material.
        """

        redacted_cookies = [
            CookieRecord(
                name=c.name,
                value="<redacted>",
                origin=c.origin,
                path=c.path,
                expires_epoch=c.expires_epoch,
                secure=c.secure,
                http_only=c.http_only,
            )
            for c in self.cookies
        ]
        return CookieJarSnapshot(cookies=redacted_cookies)


@runtime_checkable
class CookieJarPort(Protocol):
    """Hexagonal port for the per-run / per-origin cookie store."""

    def cookies_for(
        self,
        *,
        run_ref: str,
        url: str,
        clock_now: float | None = None,
    ) -> dict[str, str]:
        """Return ``{name: value}`` cookies to attach to the request.

        Excludes expired cookies (per ``clock_now`` if provided, else
        per ``time.time()``). Only cookies whose origin / path / scheme
        match the request URL are returned.
        """

    def accept_set_cookie(
        self,
        *,
        run_ref: str,
        url: str,
        set_cookie_value: str,
        clock_now: float | None = None,
    ) -> None:
        """Parse ``set_cookie_value`` and store the cookie.

        ``url`` is the request URL whose response carried the
        ``Set-Cookie`` header — used to derive the cookie's origin
        and (default) path. Malformed values are dropped silently
        (logged, not raised) — Phase 1's contract is best-effort
        cookie acceptance.
        """

    def cookies_in_jar(self, *, run_ref: str) -> CookieJarSnapshot:
        """Return a snapshot of ``run_ref``'s cookies (test helper)."""

    def clear_run(self, *, run_ref: str) -> None:
        """Release every cookie for ``run_ref``.

        Called at the run-completion boundary so cookies do not
        accumulate across runs in long-lived processes. A subsequent
        :meth:`cookies_for` for the same ``run_ref`` returns an
        empty dict.
        """


class NoopCookieJar:
    """Permissive default — never stores or returns any cookie.

    Used when no jar is configured (Phase 1 boundary acceptance:
    existing tests pass without configuration). Production callers
    inject :class:`InMemoryCookieJar`; leaving the no-op in
    production just means cookies are not echoed back (some sites
    will issue Set-Cookie redirects that never resolve, which is a
    correctness concern — but not a security gate).
    """

    def cookies_for(
        self,
        *,
        run_ref: str,
        url: str,
        clock_now: float | None = None,
    ) -> dict[str, str]:
        del run_ref, url, clock_now
        return {}

    def accept_set_cookie(
        self,
        *,
        run_ref: str,
        url: str,
        set_cookie_value: str,
        clock_now: float | None = None,
    ) -> None:
        del run_ref, url, set_cookie_value, clock_now

    def cookies_in_jar(self, *, run_ref: str) -> CookieJarSnapshot:
        del run_ref
        return CookieJarSnapshot()

    def clear_run(self, *, run_ref: str) -> None:
        del run_ref


__all__ = [
    "CookieJarPort",
    "CookieJarSnapshot",
    "CookieRecord",
    "NoopCookieJar",
]
