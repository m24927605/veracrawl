"""Contract tests for Phase 1 step 1.5 — ``CookieJarPort``.

design.md §4 Phase 1 step 1.5 deliverable: cookie jar scoped per-run
and per-origin; do not leak between runs or across origins. The
framework default :class:`NoopCookieJar` is permissive — never
stores or returns any cookie — so existing tests pass without
configuration (Phase 1 boundary acceptance).
"""

from __future__ import annotations

from veracrawl.ports.cookie_jar import (
    CookieJarPort,
    CookieJarSnapshot,
    CookieRecord,
    NoopCookieJar,
)


def test_noop_satisfies_runtime_protocol() -> None:
    jar = NoopCookieJar()
    assert isinstance(jar, CookieJarPort)


def test_noop_cookies_for_returns_empty_dict() -> None:
    jar = NoopCookieJar()
    assert jar.cookies_for(run_ref="run:r", url="https://example.test/") == {}


def test_noop_accept_set_cookie_does_not_change_state() -> None:
    jar = NoopCookieJar()
    jar.accept_set_cookie(
        run_ref="run:r",
        url="https://example.test/",
        set_cookie_value="session=abc; Path=/",
    )
    assert jar.cookies_for(run_ref="run:r", url="https://example.test/") == {}


def test_noop_cookies_in_jar_returns_empty_snapshot() -> None:
    jar = NoopCookieJar()
    snapshot = jar.cookies_in_jar(run_ref="run:r")
    assert isinstance(snapshot, CookieJarSnapshot)
    assert snapshot.cookies == []


def test_cookie_record_immutable() -> None:
    cookie = CookieRecord(
        name="session",
        value="abc",
        origin="https://example.test",
    )
    try:
        cookie.value = "xyz"  # type: ignore[misc]
    except (AttributeError, Exception):  # noqa: BLE001
        return
    raise AssertionError("CookieRecord must be immutable")


def test_cookie_record_default_path_is_root() -> None:
    cookie = CookieRecord(
        name="session",
        value="abc",
        origin="https://example.test",
    )
    assert cookie.path == "/"


def test_clear_run_is_noop_on_default() -> None:
    jar = NoopCookieJar()
    jar.clear_run(run_ref="run:r")
    assert jar.cookies_for(run_ref="run:r", url="https://example.test/") == {}
