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

# Per-(run_ref, origin) cookie count cap. Above this, oldest
# cookies are evicted in insertion order (codex iter-2 important
# #4). 64 covers all real-world cookie usage; mass-Set-Cookie
# attacks won't exhaust process memory.
_DEFAULT_MAX_COOKIES_PER_BUCKET: int = 64
# Per-cookie value byte cap. RFC 6265 doesn't mandate a max but
# real browsers cap around 4 KiB; we use 8 KiB to leave headroom
# for legitimate signed-token cookies.
_DEFAULT_MAX_COOKIE_VALUE_BYTES: int = 8 * 1024


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
        max_cookies_per_bucket: int = _DEFAULT_MAX_COOKIES_PER_BUCKET,
        max_cookie_value_bytes: int = _DEFAULT_MAX_COOKIE_VALUE_BYTES,
    ) -> None:
        if max_cookies_per_bucket <= 0:
            raise ValueError("max_cookies_per_bucket must be positive")
        if max_cookie_value_bytes <= 0:
            raise ValueError("max_cookie_value_bytes must be positive")
        self._clock = clock_fn
        self._max_cookies_per_bucket = max_cookies_per_bucket
        self._max_cookie_value_bytes = max_cookie_value_bytes
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
        request_secure = origin.startswith("https://")
        for name, morsel in morsels.items():
            value = morsel.value
            path = _normalize_cookie_path(morsel["path"] or None, url)
            secure = bool(morsel["secure"])
            # Codex iter-2 critical: RFC 6265bis §5.6 — ignore a
            # ``Set-Cookie`` with the ``Secure`` attribute when it
            # arrives over an insecure (non-HTTPS) channel.
            # Otherwise an HTTP response can plant a Secure cookie
            # that the jar later ships on HTTPS requests, even
            # though the per-origin scope means the cookies live in
            # different buckets — a Set-Cookie header itself can
            # still be a covert channel into the credential surface.
            if secure and not request_secure:
                _logger.warning(
                    "cookie_jar_ignored_secure_over_insecure",
                    run_ref=run_ref,
                    origin=origin,
                    cookie_name=name,
                )
                continue
            # Codex iter-2 important #4: cap cookie value size so
            # an oversized Set-Cookie cannot exhaust process memory.
            if len(value.encode("utf-8")) > self._max_cookie_value_bytes:
                _logger.warning(
                    "cookie_jar_value_oversize_dropped",
                    run_ref=run_ref,
                    origin=origin,
                    cookie_name=name,
                    value_bytes=len(value.encode("utf-8")),
                )
                continue
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
            # Codex iter-2 important #4: cap per-bucket cookie
            # count. Above the cap, drop oldest (FIFO at the
            # head of the list) so a malicious or runaway server
            # cannot pump unbounded Set-Cookies into one origin.
            if len(replaced) > self._max_cookies_per_bucket:
                overflow = len(replaced) - self._max_cookies_per_bucket
                replaced = replaced[overflow:]
            self._jar[(run_ref, origin)] = replaced

    def cookies_in_jar(self, *, run_ref: str, include_values: bool = False) -> CookieJarSnapshot:
        with self._lock:
            cookies: list[CookieRecord] = []
            for (jar_run, _origin), records in self._jar.items():
                if jar_run == run_ref:
                    cookies.extend(records)
            snapshot = CookieJarSnapshot(cookies=cookies)
        # Default: redact values for safety (codex iter-4 important).
        # ``include_values=True`` is explicit opt-in for tests /
        # debug paths.
        if include_values:
            return snapshot
        return snapshot.redacted()

    def clear_run(self, *, run_ref: str) -> None:
        with self._lock:
            keys_to_drop = [k for k in self._jar if k[0] == run_ref]
            for k in keys_to_drop:
                del self._jar[k]


__all__ = ["InMemoryCookieJar"]
