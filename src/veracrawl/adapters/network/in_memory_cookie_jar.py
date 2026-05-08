"""``InMemoryCookieJar`` — production default for ``CookieJarPort``.

Per-(run_ref, origin) cookie store. Origin matching is exact
(scheme + host + port, lowercased + default-port-normalized).
``Domain=`` cookie attribute is **ignored** for step 1.5; broader
subdomain scope interacts with the credential vault and authorized
session model and lands in Phase 2 / Phase 6. ``Path=`` is honored
per RFC 6265 §5.4.

Thread safety: all reads / writes serialize on a single lock. The
cooperative crawl is not contention-bound, so a finer-grained
scheme is over-engineered for Phase 1.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from email.utils import parsedate_to_datetime
from http.cookies import CookieError, SimpleCookie
from urllib.parse import urlsplit

from veracrawl.ports.cookie_jar import CookieJarSnapshot, CookieRecord
from veracrawl.runtime_support.logging import get_logger

_logger = get_logger(__name__)


def _origin_for(url: str) -> str | None:
    """Return canonical ``scheme://host[:port]`` or ``None`` on bad URL."""

    try:
        parts = urlsplit(url)
    except ValueError:
        return None
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        return None
    host = parts.hostname.lower()
    try:
        port = parts.port
    except ValueError:
        return None
    if port is None:
        return f"{parts.scheme.lower()}://{host}"
    # Drop default ports so http://example.com:80 and
    # http://example.com share an origin.
    if (parts.scheme == "http" and port == 80) or (parts.scheme == "https" and port == 443):
        return f"{parts.scheme.lower()}://{host}"
    return f"{parts.scheme.lower()}://{host}:{port}"


def _path_for(url: str) -> str:
    parts = urlsplit(url)
    path = parts.path or "/"
    return path


def _default_cookie_path(request_url: str) -> str:
    """RFC 6265 §5.1.4 default-path computation.

    Codex iter-1 important #2: when a Set-Cookie omits the
    ``Path`` attribute, the default is the *directory* of the
    request URL, NOT the full request path. So a cookie set by
    ``https://example.test/admin/login`` defaults to ``/admin``
    (not ``/admin/login``), so the cookie matches subsequent
    requests to ``/admin/dashboard``. Algorithm:

    1. Let ``uri-path`` be the path of the request.
    2. If ``uri-path`` is empty or doesn't start with ``/``,
       return ``/``.
    3. If ``uri-path`` contains no ``/`` other than the leading
       one, return ``/``.
    4. Return everything from the start up to (but not
       including) the rightmost ``/`` character.
    """

    parts = urlsplit(request_url)
    path = parts.path or ""
    if not path.startswith("/"):
        return "/"
    last_slash = path.rfind("/")
    if last_slash == 0:
        return "/"
    return path[:last_slash]


def _normalize_cookie_path(path_attr: str | None, request_url: str) -> str:
    """Apply RFC 6265 path validation + fall back to default-path.

    Codex iter-1 important #3: server-supplied ``Path=`` values
    that are empty, missing, or do not start with ``/`` must fall
    back to the default-path computation. Storing the raw value
    verbatim (e.g. ``Path=admin``) creates cookies that never
    match, masking a misconfiguration as a silent failure.
    """

    if path_attr is None or not path_attr or not path_attr.startswith("/"):
        return _default_cookie_path(request_url)
    return path_attr


def _path_matches_cookie_path(request_path: str, cookie_path: str) -> bool:
    """RFC 6265 §5.1.4 path-match: cookie sent if cookie-path is a
    prefix of request-path with a ``/`` separator (or cookie-path
    equals request-path or cookie-path equals ``/``)."""

    if cookie_path == request_path:
        return True
    if cookie_path == "/":
        return True
    if request_path.startswith(cookie_path):
        # Either the next char is ``/`` or the cookie-path itself
        # ended in ``/``.
        if cookie_path.endswith("/"):
            return True
        if len(request_path) > len(cookie_path) and request_path[len(cookie_path)] == "/":
            return True
    return False


def _resolve_expiry(
    morsel_max_age: str | None,
    morsel_expires: str | None,
    *,
    now_epoch: float,
) -> float | None:
    """Compute the cookie's wall-clock expiry epoch, or ``None`` for session."""

    if morsel_max_age:
        try:
            seconds = int(morsel_max_age)
        except ValueError:
            return None
        if seconds <= 0:
            # Per RFC 6265: Max-Age <= 0 means delete immediately.
            return now_epoch - 1.0
        return now_epoch + float(seconds)
    if morsel_expires:
        try:
            when = parsedate_to_datetime(morsel_expires)
        except (TypeError, ValueError):
            return None
        return when.timestamp()
    return None


class InMemoryCookieJar:
    """Per-run / per-origin cookie store."""

    def __init__(
        self,
        *,
        clock_fn: Callable[[], float] = time.time,
    ) -> None:
        self._clock = clock_fn
        self._lock = threading.Lock()
        # (run_ref, origin) → list[CookieRecord]
        self._jar: dict[tuple[str, str], list[CookieRecord]] = {}

    def cookies_for(
        self,
        *,
        run_ref: str,
        url: str,
        clock_now: float | None = None,
    ) -> dict[str, str]:
        origin = _origin_for(url)
        if origin is None:
            return {}
        request_path = _path_for(url)
        request_secure = origin.startswith("https://")
        now = clock_now if clock_now is not None else self._clock()
        out: dict[str, str] = {}
        with self._lock:
            cookies = self._jar.get((run_ref, origin), [])
            kept: list[CookieRecord] = []
            for cookie in cookies:
                if cookie.expires_epoch is not None and cookie.expires_epoch <= now:
                    # Drop expired.
                    continue
                kept.append(cookie)
                if cookie.secure and not request_secure:
                    continue
                if not _path_matches_cookie_path(request_path, cookie.path):
                    continue
                out[cookie.name] = cookie.value
            # Persist the trimmed-of-expired list back.
            if len(kept) != len(cookies):
                self._jar[(run_ref, origin)] = kept
        return out

    def accept_set_cookie(
        self,
        *,
        run_ref: str,
        url: str,
        set_cookie_value: str,
        clock_now: float | None = None,
    ) -> None:
        origin = _origin_for(url)
        if origin is None:
            return
        now = clock_now if clock_now is not None else self._clock()
        try:
            morsels = SimpleCookie()
            morsels.load(set_cookie_value)
        except CookieError:
            _logger.warning(
                "cookie_jar_set_cookie_parse_failed",
                run_ref=run_ref,
                origin=origin,
            )
            return
        new_cookies: list[CookieRecord] = []
        for name, morsel in morsels.items():
            value = morsel.value
            path = _normalize_cookie_path(morsel["path"] or None, url)
            secure = bool(morsel["secure"])
            http_only = bool(morsel["httponly"])
            expires = _resolve_expiry(
                morsel["max-age"] or None,
                morsel["expires"] or None,
                now_epoch=now,
            )
            new_cookies.append(
                CookieRecord(
                    name=name,
                    value=value,
                    origin=origin,
                    path=path,
                    expires_epoch=expires,
                    secure=secure,
                    http_only=http_only,
                )
            )
        if not new_cookies:
            return
        with self._lock:
            existing = self._jar.get((run_ref, origin), [])
            # Replace by (name, path) — RFC 6265 §5.3 step 11.
            replaced: list[CookieRecord] = []
            new_keys = {(c.name, c.path) for c in new_cookies}
            for cookie in existing:
                if (cookie.name, cookie.path) in new_keys:
                    continue
                if cookie.expires_epoch is not None and cookie.expires_epoch <= now:
                    continue
                replaced.append(cookie)
            for cookie in new_cookies:
                # Drop immediately-expired so the jar stays clean.
                if cookie.expires_epoch is not None and cookie.expires_epoch <= now:
                    continue
                replaced.append(cookie)
            self._jar[(run_ref, origin)] = replaced

    def cookies_in_jar(self, *, run_ref: str) -> CookieJarSnapshot:
        with self._lock:
            cookies: list[CookieRecord] = []
            for (jar_run, _origin), records in self._jar.items():
                if jar_run == run_ref:
                    cookies.extend(records)
            return CookieJarSnapshot(cookies=cookies)

    def clear_run(self, *, run_ref: str) -> None:
        with self._lock:
            keys_to_drop = [k for k in self._jar if k[0] == run_ref]
            for k in keys_to_drop:
                del self._jar[k]


__all__ = ["InMemoryCookieJar"]
